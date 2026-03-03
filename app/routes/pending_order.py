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
from ..mappers.trade_mapper import build_pending_order_request, validate_trade_mode
from ..models.pending_order import PendingOrderRequest
from ..models.trade import TradeResponse
from ..mt5_worker import WorkerState, get_queue_depth, get_state, submit

logger = logging.getLogger("mt5_bridge.pending_order")
router = APIRouter(tags=["execution"])

_inflight_lock = threading.Lock()
_inflight_requests = 0

def _acquire_single_flight() -> str | None:
    global _inflight_requests
    with _inflight_lock:
        if _inflight_requests > 0:
            return "Single-flight mode active: wait for current submission to finish."
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

@router.post("/pending-order", response_model=TradeResponse, summary="Submit a pending order")
async def pending_order(
    req: PendingOrderRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> TradeResponse:
    # ── Phase 3: Lifecycle + Idempotency setup ──────────────────────────
    request_hash = compute_request_hash(req.model_dump()) if idempotency_key else None
    ctx = create_context("pending_order", idempotency_key=idempotency_key, request_hash=request_hash)

    if idempotency_key and request_hash:
        cached = idempotency_store.check(idempotency_key, request_hash)
        if cached is not None:
            emit_operation_log(ctx, code="IDEMPOTENCY_KEY_REPLAYED", final_outcome="cache_hit")
            return TradeResponse(**cached.response)
        if idempotency_store.check_conflict(idempotency_key, request_hash):
            raise MessageEnvelopeException(
                code=ErrorCode.IDEMPOTENCY_KEY_CONFLICT,
                message="Idempotency key already used with different parameters.",
            )
    if not settings.execution_enabled:
        transition(ctx, OperationState.REJECTED)
        emit_operation_log(ctx, code="EXECUTION_DISABLED", final_outcome="execution_disabled")
        response = TradeResponse(success=False, error="Execution disabled by policy (EXECUTION_ENABLED=false).")
        log_trade(req, response, metadata={"state": "blocked_execution_disabled"})
        raise MessageEnvelopeException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.EXECUTION_DISABLED,
            message="Execution disabled by policy (EXECUTION_ENABLED=false).",
        )

    # Resolve MT5 symbol — either via YAML alias or direct name (dashboard bypass)
    if req.mt5_symbol_direct:
        mt5_symbol = req.mt5_symbol_direct.strip()
    elif req.ticker in symbol_map:
        mt5_symbol = symbol_map[req.ticker].mt5_symbol
    else:
        response = TradeResponse(success=False, error=f"Unknown ticker '{req.ticker}'")
        log_trade(req, response, metadata={"state": "blocked_unknown_symbol"})
        raise MessageEnvelopeException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.SYMBOL_NOT_CONFIGURED,
            message=f"Unknown ticker '{req.ticker}'",
            context={"ticker": req.ticker},
        )

    gate_error = _acquire_single_flight()
    if gate_error:
        response = TradeResponse(success=False, error=gate_error)
        log_trade(req, response, metadata={"state": "blocked_overload_or_single_flight"})
        raise MessageEnvelopeException(
            status_code=status.HTTP_409_CONFLICT,
            code=ErrorCode.OVERLOAD_OR_SINGLE_FLIGHT,
            message=gate_error,
        )

    try:
        if get_state() not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
            transition(ctx, OperationState.REJECTED)
            emit_operation_log(ctx, code="MT5_DISCONNECTED", final_outcome="not_connected")
            raise MessageEnvelopeException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                code=ErrorCode.MT5_DISCONNECTED,
                message="MT5 terminal not connected",
            )

        transition(ctx, OperationState.DISPATCHING)

        mt5_symbol_resolved = mt5_symbol

        def _execute_in_worker() -> tuple[TradeResponse, str]:
            import MetaTrader5 as mt5  # type: ignore[import-untyped]

            symbol_info = mt5.symbol_info(mt5_symbol_resolved)
            if symbol_info is None:
                return TradeResponse(success=False, error=f"Symbol info unavailable for {mt5_symbol_resolved}"), "symbol_missing"

            # T017: Trade mode enforcement for pending orders
            # Map pending order type to buy/sell direction for validation
            pending_direction = "buy" if req.type in ("buy_limit", "buy_stop") else "sell"
            trade_mode_error = validate_trade_mode(symbol_info, pending_direction)
            if trade_mode_error:
                return TradeResponse(success=False, error=trade_mode_error), "trade_mode_rejected"

            try:
                request_dict = build_pending_order_request(req, mt5_symbol_resolved, symbol_info)
            except Exception as e:
                return TradeResponse(success=False, error=f"Invalid order parameters: {str(e)}"), "invalid_params"

            logger.info("Submitting MT5 pending order: %s", request_dict)

            result = mt5.order_send(request_dict)
            if result is None:
                return TradeResponse(success=False, error=f"order_send returned None: {mt5.last_error()}"), "order_send_none"

            retcode_done = int(getattr(mt5, "TRADE_RETCODE_DONE", 10009))
            if int(getattr(result, "retcode", -1)) != retcode_done:
                return (
                    TradeResponse(
                        success=False,
                        error=(
                            f"Order rejected (retcode={result.retcode}): "
                            f"{getattr(result, 'comment', '')}"
                        ),
                    ),
                    "order_rejected",
                )

            return (
                TradeResponse(
                    success=True,
                    filled_price=float(getattr(result, "price", 0.0) or 0.0),
                    filled_quantity=float(getattr(result, "volume", request_dict["volume"]) or request_dict["volume"]),
                    ticket_id=int(getattr(result, "order", 0) or 0),
                    error=None,
                ),
                "fill_confirmed",
            )

        loop = asyncio.get_running_loop()
        try:
            response, trade_state = await asyncio.wrap_future(submit(_execute_in_worker), loop=loop)
            log_trade(req, response, metadata={"state": trade_state})
            logger.info("MT5 pending order result: %s", response.model_dump())

            if response.success:
                transition(ctx, OperationState.ACCEPTED)
            else:
                transition(ctx, OperationState.REJECTED)
            emit_operation_log(ctx, code="REQUEST_OK" if response.success else "REQUEST_REJECTED", final_outcome=trade_state)

            if idempotency_key and request_hash:
                idempotency_store.store(idempotency_key, request_hash, response.model_dump(), "pending_order")

            if response.success:
                return response
            if trade_state == "trade_mode_rejected":
                raise MessageEnvelopeException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code=ErrorCode.SYMBOL_TRADE_MODE_RESTRICTED,
                    message=response.error or "Trade mode restriction",
                )
            if trade_state in {"invalid_params"}:
                raise MessageEnvelopeException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code=ErrorCode.VALIDATION_ERROR,
                    message=response.error or "Invalid order parameters",
                )
            if trade_state in {"symbol_missing"}:
                raise MessageEnvelopeException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ErrorCode.SYMBOL_NOT_CONFIGURED,
                    message=response.error or "Symbol info unavailable",
                )
            raise MessageEnvelopeException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code=ErrorCode.REQUEST_REJECTED,
                message=response.error or "Pending order request failed",
            )
        except ConnectionError:
            transition(ctx, OperationState.FAILED_TERMINAL)
            emit_operation_log(ctx, code="MT5_DISCONNECTED", final_outcome="connection_error")
            response = TradeResponse(success=False, error="Not connected to MT5")
            log_trade(req, response, metadata={"state": "connection_error"})
            raise MessageEnvelopeException(
                status_code=503,
                code=ErrorCode.MT5_DISCONNECTED,
                message="Not connected to MT5",
            )
        except MessageEnvelopeException:
            raise
        except Exception as e:
            transition(ctx, OperationState.FAILED_TERMINAL)
            emit_operation_log(ctx, code="INTERNAL_SERVER_ERROR", final_outcome="internal_error")
            response = TradeResponse(success=False, error=str(e))
            log_trade(req, response, metadata={"state": "internal_error"})
            raise
    finally:
        _release_single_flight()
