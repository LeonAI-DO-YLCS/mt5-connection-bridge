"""MT5 Bridge — POST `/execute` endpoint."""

from __future__ import annotations

import asyncio
import logging
import threading

from fastapi import APIRouter, Header, status

from ..execution.idempotency import compute_request_hash, idempotency_store
from ..execution.lifecycle import OperationState, create_context, transition
from ..execution.observability import emit_operation_log
from ..messaging.codes import ErrorCode
from ..messaging.envelope import MessageEnvelopeException

from ..audit import log_trade
from ..main import settings, symbol_map
from ..mappers.trade_mapper import (
    action_to_mt5_order_type,
    build_order_request,
    normalize_lot_size,
    validate_trade_mode,
)
from ..models.trade import TradeRequest, TradeResponse
from ..mt5_worker import WorkerState, get_queue_depth, get_state, submit

logger = logging.getLogger("mt5_bridge.execute")

router = APIRouter(tags=["execution"])

_inflight_lock = threading.Lock()
_inflight_requests = 0


def _safe_pct_delta(a: float, b: float) -> float:
    if b <= 0:
        return 0.0
    return abs(a - b) / b * 100.0


def _build_trade_response(
    req: TradeRequest,
    *,
    success: bool,
    status_name: str,
    filled_price: float | None = None,
    filled_quantity: float | None = None,
    ticket_id: int | None = None,
    error: str | None = None,
) -> TradeResponse:
    actual_quantity = float(filled_quantity or 0.0)
    requested_quantity = float(req.quantity)
    return TradeResponse(
        success=success,
        status=status_name,
        requested_quantity=requested_quantity,
        requested_price=float(req.current_price),
        filled_price=filled_price,
        filled_quantity=actual_quantity,
        unfilled_quantity=max(requested_quantity - actual_quantity, 0.0),
        ticket_id=ticket_id,
        error=error,
    )


def _acquire_single_flight(req: TradeRequest) -> str | None:
    global _inflight_requests

    with _inflight_lock:
        if not req.multi_trade_mode and _inflight_requests > 0:
            return "Single-flight mode active: wait for current submission to finish or enable multi-trade mode."

        pending = _inflight_requests + get_queue_depth()
        if pending >= settings.multi_trade_overload_queue_threshold:
            return (
                "Execution queue overload protection triggered. "
                f"Pending={pending}, threshold={settings.multi_trade_overload_queue_threshold}."
            )
        _inflight_requests += 1
    return None


def _release_single_flight() -> None:
    global _inflight_requests
    with _inflight_lock:
        _inflight_requests = max(_inflight_requests - 1, 0)


@router.post("/execute", response_model=TradeResponse)
async def execute_trade(
    req: TradeRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> TradeResponse:
    # ── Phase 3: Lifecycle + Idempotency setup ──────────────────────────
    request_hash = compute_request_hash(req.model_dump()) if idempotency_key else None
    ctx = create_context(
        "execute_trade",
        idempotency_key=idempotency_key,
        request_hash=request_hash,
    )

    # Idempotency check (FR-004 through FR-006)
    if idempotency_key and request_hash:
        cached = idempotency_store.check(idempotency_key, request_hash)
        if cached is not None:
            emit_operation_log(
                ctx, code="IDEMPOTENCY_KEY_REPLAYED", final_outcome="cache_hit"
            )
            return TradeResponse(**cached.response)
        if idempotency_store.check_conflict(idempotency_key, request_hash):
            raise MessageEnvelopeException(
                code=ErrorCode.IDEMPOTENCY_KEY_CONFLICT,
                message="Idempotency key already used with different parameters.",
            )

    # ── Symbol resolution ───────────────────────────────────────────────
    if req.mt5_symbol_direct:
        mt5_symbol = req.mt5_symbol_direct.strip()
    elif req.ticker in symbol_map:
        mt5_symbol = symbol_map[req.ticker].mt5_symbol
    else:
        transition(ctx, OperationState.REJECTED)
        emit_operation_log(
            ctx, code="SYMBOL_NOT_CONFIGURED", final_outcome="unknown_ticker"
        )
        response = TradeResponse(success=False, error=f"Unknown ticker: {req.ticker}")
        log_trade(req, response, metadata={"state": "blocked_unknown_ticker"})
        raise MessageEnvelopeException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.SYMBOL_NOT_CONFIGURED,
            message=f"Unknown ticker: {req.ticker}",
            action="Add the symbol to symbols.yaml or use mt5_symbol_direct.",
            context={"ticker": req.ticker},
        )

    try:
        action_to_mt5_order_type(req.action)
    except ValueError as exc:
        transition(ctx, OperationState.REJECTED)
        emit_operation_log(ctx, code="VALIDATION_ERROR", final_outcome="invalid_action")
        response = TradeResponse(success=False, error=str(exc))
        log_trade(req, response, metadata={"state": "blocked_invalid_action"})
        raise MessageEnvelopeException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ErrorCode.VALIDATION_ERROR,
            message=str(exc),
            action="Use a valid action: buy, sell, long, short.",
            context={"action": req.action},
        ) from exc

    if not settings.execution_enabled:
        transition(ctx, OperationState.REJECTED)
        emit_operation_log(
            ctx, code="EXECUTION_DISABLED", final_outcome="execution_disabled"
        )
        response = TradeResponse(
            success=False,
            error="Execution disabled by policy (EXECUTION_ENABLED=false).",
        )
        log_trade(req, response, metadata={"state": "blocked_execution_disabled"})
        raise MessageEnvelopeException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.EXECUTION_DISABLED,
            message="Execution disabled by policy (EXECUTION_ENABLED=false).",
        )

    gate_error = _acquire_single_flight(req)
    if gate_error:
        transition(ctx, OperationState.REJECTED)
        emit_operation_log(
            ctx,
            code="OVERLOAD_OR_SINGLE_FLIGHT",
            final_outcome="overload_or_single_flight",
        )
        response = TradeResponse(success=False, error=gate_error)
        log_trade(
            req, response, metadata={"state": "blocked_overload_or_single_flight"}
        )
        raise MessageEnvelopeException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.OVERLOAD_OR_SINGLE_FLIGHT,
            message=gate_error,
        )

    try:
        if get_state() not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
            transition(ctx, OperationState.REJECTED)
            emit_operation_log(
                ctx, code="MT5_DISCONNECTED", final_outcome="not_connected"
            )
            raise MessageEnvelopeException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                code=ErrorCode.MT5_DISCONNECTED,
                message="MT5 terminal not connected",
            )

        # ── Transition to DISPATCHING ───────────────────────────────────
        transition(ctx, OperationState.DISPATCHING)

        mt5_symbol_resolved = (
            mt5_symbol  # resolved above (YAML alias or mt5_symbol_direct)
        )

        def _execute_in_worker() -> tuple[TradeResponse, str]:
            import MetaTrader5 as mt5  # type: ignore[import-untyped]

            symbol_info = mt5.symbol_info(mt5_symbol_resolved)
            if symbol_info is None:
                return _build_trade_response(
                    req,
                    success=False,
                    status_name="failed",
                    error=f"Symbol info unavailable for {mt5_symbol_resolved}",
                ), "symbol_missing"

            # T016: Trade mode enforcement — validate BEFORE touching the broker
            trade_mode_error = validate_trade_mode(symbol_info, req.action)
            if trade_mode_error:
                return _build_trade_response(
                    req,
                    success=False,
                    status_name="rejected",
                    error=trade_mode_error,
                ), "trade_mode_rejected"

            if not symbol_info.visible and not mt5.symbol_select(
                mt5_symbol_resolved, True
            ):
                return (
                    _build_trade_response(
                        req,
                        success=False,
                        status_name="failed",
                        error=f"Failed to select symbol {mt5_symbol_resolved} in Market Watch",
                    ),
                    "symbol_not_selectable",
                )

            tick = mt5.symbol_info_tick(mt5_symbol_resolved)
            if tick is not None:
                market_price = float(getattr(tick, "ask", 0.0) or 0.0)
                if req.action in ("sell", "short"):
                    market_price = float(
                        getattr(tick, "bid", market_price) or market_price
                    )
                if market_price > 0:
                    pre_dispatch_delta = _safe_pct_delta(
                        market_price, req.current_price
                    )
                    if pre_dispatch_delta > settings.max_pre_dispatch_slippage_pct:
                        return (
                            _build_trade_response(
                                req,
                                success=False,
                                status_name="rejected",
                                error=(
                                    "pre_dispatch_slippage_rejection: "
                                    f"delta_pct={pre_dispatch_delta:.4f} exceeds {settings.max_pre_dispatch_slippage_pct:.4f}"
                                ),
                            ),
                            "pre_dispatch_slippage_rejected",
                        )

            try:
                normalized_qty = normalize_lot_size(req.quantity, symbol_info)
            except ValueError as exc:
                return _build_trade_response(
                    req,
                    success=False,
                    status_name="failed",
                    error=str(exc),
                ), "invalid_lot"

            order_request = build_order_request(req, mt5_symbol_resolved, symbol_info)
            order_request["volume"] = normalized_qty
            logger.info("Submitting MT5 order: %s", order_request)

            result = mt5.order_send(order_request)
            if result is None:
                return _build_trade_response(
                    req,
                    success=False,
                    status_name="failed",
                    error=f"order_send returned None: {mt5.last_error()}",
                ), "order_send_none"

            retcode_done = int(getattr(mt5, "TRADE_RETCODE_DONE", 10009))
            if int(getattr(result, "retcode", -1)) != retcode_done:
                return (
                    _build_trade_response(
                        req,
                        success=False,
                        status_name="rejected",
                        error=(
                            f"Order rejected (retcode={result.retcode}): "
                            f"{getattr(result, 'comment', '')}"
                        ),
                    ),
                    "order_rejected",
                )

            filled_price = float(getattr(result, "price", req.current_price))
            filled_quantity = float(getattr(result, "volume", normalized_qty))
            ticket_id = int(getattr(result, "deal", 0) or 0)
            if not ticket_id:
                ticket_id = int(getattr(result, "order", 0) or 0)
            post_fill_delta = _safe_pct_delta(filled_price, req.current_price)
            if post_fill_delta > settings.max_post_fill_slippage_pct:
                return (
                    _build_trade_response(
                        req,
                        success=False,
                        status_name="rejected",
                        filled_price=filled_price,
                        filled_quantity=filled_quantity,
                        ticket_id=ticket_id,
                        error=(
                            "post_fill_slippage_exception: "
                            f"delta_pct={post_fill_delta:.4f} exceeds {settings.max_post_fill_slippage_pct:.4f}"
                        ),
                    ),
                    "post_fill_slippage_exception",
                )

            status_name = (
                "partial_fill" if 0 < filled_quantity < normalized_qty else "filled"
            )
            return (
                _build_trade_response(
                    req,
                    success=filled_quantity > 0,
                    status_name=status_name if filled_quantity > 0 else "failed",
                    filled_price=filled_price,
                    filled_quantity=filled_quantity,
                    ticket_id=ticket_id,
                    error=None
                    if filled_quantity > 0
                    else "Broker returned zero filled quantity",
                ),
                "fill_confirmed",
            )

        loop = asyncio.get_running_loop()
        response, trade_state = await asyncio.wrap_future(
            submit(_execute_in_worker), loop=loop
        )
        log_trade(req, response, metadata={"state": trade_state})
        logger.info("MT5 order result: %s", response.model_dump())

        # ── Lifecycle terminal state ────────────────────────────────────
        if response.success:
            transition(ctx, OperationState.ACCEPTED)
        else:
            transition(ctx, OperationState.REJECTED)

        emit_operation_log(
            ctx,
            code="REQUEST_OK" if response.success else "REQUEST_REJECTED",
            final_outcome=trade_state,
        )

        # Cache for idempotency replay (FR-005)
        if idempotency_key and request_hash:
            idempotency_store.store(
                idempotency_key, request_hash, response.model_dump(), "execute_trade"
            )

        if not response.success and trade_state == "trade_mode_rejected":
            raise MessageEnvelopeException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code=ErrorCode.SYMBOL_TRADE_MODE_RESTRICTED,
                message=response.error or "Trade mode restriction",
                action="Select a different action or choose a symbol that allows this trade type.",
            )
        return response
    except ConnectionError as exc:
        transition(ctx, OperationState.FAILED_TERMINAL)
        emit_operation_log(
            ctx, code="MT5_DISCONNECTED", final_outcome="connection_error"
        )
        response = TradeResponse(success=False, error=str(exc))
        log_trade(req, response, metadata={"state": "connection_error"})
        raise MessageEnvelopeException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=ErrorCode.MT5_DISCONNECTED,
            message=str(exc),
        ) from exc
    except MessageEnvelopeException:
        raise
    except Exception as exc:
        transition(ctx, OperationState.FAILED_TERMINAL)
        emit_operation_log(
            ctx, code="INTERNAL_SERVER_ERROR", final_outcome="internal_error"
        )
        response = TradeResponse(success=False, error=str(exc))
        log_trade(req, response, metadata={"state": "internal_error"})
        raise
    finally:
        _release_single_flight()
