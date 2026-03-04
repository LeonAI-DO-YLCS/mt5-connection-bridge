import asyncio
import logging
import threading
import math

from fastapi import APIRouter, Header, status

from ..execution.idempotency import compute_request_hash, idempotency_store
from ..execution.lifecycle import OperationState, create_context, transition
from ..execution.observability import emit_operation_log
from ..execution.comment import matches_invalid_comment_signature

from ..messaging.codes import ErrorCode
from ..messaging.envelope import MessageEnvelopeException

from ..audit import log_trade
from ..main import settings
from ..mappers.trade_mapper import build_close_request
from ..models.close_position import ClosePositionRequest
from ..models.trade import TradeResponse
from ..mt5_worker import WorkerState, get_queue_depth, get_state, submit

logger = logging.getLogger("mt5_bridge.close_position")
router = APIRouter(tags=["management"])

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


def _is_valid_step(value: float, min_value: float, step: float) -> bool:
    if step <= 0:
        return True
    ratio = (value - min_value) / step
    return math.isclose(ratio, round(ratio), rel_tol=0.0, abs_tol=1e-9)


def _validate_close_volume(
    requested_volume: float | None,
    position_volume: float,
    symbol_info: object,
) -> str | None:
    if requested_volume is None:
        return None

    volume = float(requested_volume)
    if volume <= 0:
        return "Volume must be greater than 0."
    if volume > float(position_volume):
        return "Volume to close cannot exceed current position volume."

    volume_min = float(getattr(symbol_info, "volume_min", 0.0) or 0.0)
    volume_step = float(getattr(symbol_info, "volume_step", 0.0) or 0.0)

    if volume_min > 0 and volume < volume_min:
        return f"Volume must be >= minimum lot size ({volume_min})."
    if not _is_valid_step(volume, volume_min if volume_min > 0 else 0.0, volume_step):
        return (
            f"Invalid volume step for symbol. Volume must follow step size {volume_step}"
            + (f" from min {volume_min}." if volume_min > 0 else ".")
        )
    return None


@router.post("/close-position", response_model=TradeResponse, summary="Close an open position")
async def close_position(
    req: ClosePositionRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> TradeResponse:
    # ── Phase 3: Lifecycle + Idempotency setup ──────────────────────────
    request_hash = compute_request_hash(req.model_dump()) if idempotency_key else None
    ctx = create_context("close_position", idempotency_key=idempotency_key, request_hash=request_hash)

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

        def _execute_in_worker() -> tuple[TradeResponse, str]:
            import MetaTrader5 as mt5  # type: ignore[import-untyped]

            positions = mt5.positions_get(ticket=req.ticket)
            if positions is None or len(positions) == 0:
                return TradeResponse(success=False, error=f"Position {req.ticket} not found"), "position_not_found", "none", None, None
            
            position = positions[0]
            mt5_symbol = position.symbol
            
            symbol_info = mt5.symbol_info(mt5_symbol)
            if symbol_info is None:
                return TradeResponse(success=False, error=f"Symbol info unavailable for {mt5_symbol}"), "symbol_missing", "none", None, None

            volume_error = _validate_close_volume(req.volume, float(position.volume), symbol_info)
            if volume_error:
                return TradeResponse(success=False, error=volume_error), "invalid_volume", "none", None, None

            try:
                close_request = build_close_request(position, req.volume, symbol_info)
            except ValueError as exc:
                return TradeResponse(success=False, error=str(exc)), "invalid_volume", "none", None, None
            logger.info("Submitting MT5 close order: %s", close_request)

            # ── Attempt 1: with normalized comment ──
            result = mt5.order_send(close_request)
            attempt_variant = "with_comment"

            if result is None:
                last_err = mt5.last_error()
                err_code = last_err[0] if last_err else 0
                err_msg = last_err[1] if last_err and len(last_err) > 1 else ""

                if matches_invalid_comment_signature(err_code, err_msg):
                    # ── Attempt 2: without comment (adaptive fallback) ──
                    close_request.pop("comment", None)
                    result = mt5.order_send(close_request)
                    attempt_variant = "with_comment → without_comment"

                    if result is None:
                        return (
                            TradeResponse(success=False, error="Could not close position due to broker request-format restrictions"),
                            "unrecoverable",
                            attempt_variant,
                            err_code,
                            err_msg,
                        )
                else:
                    return (
                        TradeResponse(success=False, error=f"order_send returned None: {mt5.last_error()}"),
                        "order_send_none",
                        attempt_variant,
                        None,
                        None,
                    )

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
                    attempt_variant,
                    None,
                    None,
                )

            trade_state = "comment_recovered" if "→" in attempt_variant else "fill_confirmed"
            return (
                TradeResponse(
                    success=True,
                    filled_price=float(getattr(result, "price", 0.0) or 0.0),
                    filled_quantity=float(getattr(result, "volume", close_request["volume"]) or close_request["volume"]),
                    ticket_id=int(getattr(result, "order", 0) or 0),
                    error=None,
                ),
                trade_state,
                attempt_variant,
                None,
                None,
            )

        loop = asyncio.get_running_loop()
        try:
            response, trade_state, attempt_variant, mt5_err_code, mt5_err_msg = await asyncio.wrap_future(submit(_execute_in_worker), loop=loop)
            log_trade(req, response, metadata={"state": trade_state})
            logger.info("MT5 close order result: %s", response.model_dump())

            if trade_state == "comment_recovered":
                transition(ctx, OperationState.RECOVERED)
                emit_operation_log(
                    ctx,
                    code="MT5_REQUEST_COMMENT_INVALID_RECOVERED",
                    final_outcome="recovered",
                    attempt_variant=attempt_variant,
                    mt5_last_error_code=mt5_err_code,
                    mt5_last_error_message=mt5_err_msg
                )
            elif trade_state == "unrecoverable":
                transition(ctx, OperationState.FAILED_TERMINAL)
                emit_operation_log(
                    ctx, 
                    code="MT5_REQUEST_COMMENT_INVALID", 
                    final_outcome="unrecoverable",
                    attempt_variant=attempt_variant,
                    mt5_last_error_code=mt5_err_code,
                    mt5_last_error_message=mt5_err_msg
                )
            else:
                if response.success:
                    transition(ctx, OperationState.ACCEPTED)
                else:
                    transition(ctx, OperationState.REJECTED)
                emit_operation_log(
                    ctx, 
                    code="REQUEST_OK" if response.success else "REQUEST_REJECTED", 
                    final_outcome=trade_state,
                    attempt_variant=attempt_variant
                )

            if idempotency_key and request_hash:
                idempotency_store.store(idempotency_key, request_hash, response.model_dump(), "close_position")

            if response.success:
                return response

            if trade_state == "unrecoverable":
                raise MessageEnvelopeException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    code=ErrorCode.MT5_REQUEST_COMMENT_INVALID,
                    message=response.error or "Could not close position due to broker request-format restrictions",
                    context={
                        "ticket": req.ticket,
                        "attempt_variant": attempt_variant,
                        "mt5_last_error_code": mt5_err_code,
                        "mt5_last_error_message": mt5_err_msg
                    },
                )

            if trade_state == "position_not_found":
                raise MessageEnvelopeException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ErrorCode.RESOURCE_NOT_FOUND,
                    message=response.error or f"Position {req.ticket} not found",
                    context={"ticket": req.ticket},
                )
            if trade_state == "invalid_volume":
                raise MessageEnvelopeException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code=ErrorCode.VALIDATION_VOLUME_RANGE,
                    message=response.error or "Invalid close volume",
                    context={"ticket": req.ticket},
                )
            if trade_state == "symbol_missing":
                raise MessageEnvelopeException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ErrorCode.SYMBOL_NOT_CONFIGURED,
                    message=response.error or "Symbol info unavailable",
                )
            raise MessageEnvelopeException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code=ErrorCode.REQUEST_REJECTED,
                message=response.error or "Close request failed",
                context={"ticket": req.ticket},
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
