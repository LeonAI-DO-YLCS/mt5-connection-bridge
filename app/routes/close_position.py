import asyncio
import logging
import threading
import math

from fastapi import APIRouter, HTTPException, status

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
async def close_position(req: ClosePositionRequest) -> TradeResponse:
    if not settings.execution_enabled:
        response = TradeResponse(success=False, error="Execution disabled by policy (EXECUTION_ENABLED=false).")
        log_trade(req, response, metadata={"state": "blocked_execution_disabled"})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=response.error)

    gate_error = _acquire_single_flight()
    if gate_error:
        response = TradeResponse(success=False, error=gate_error)
        log_trade(req, response, metadata={"state": "blocked_overload_or_single_flight"})
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=response.error)

    try:
        if get_state() not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MT5 terminal not connected",
            )

        def _execute_in_worker() -> tuple[TradeResponse, str]:
            import MetaTrader5 as mt5  # type: ignore[import-untyped]

            positions = mt5.positions_get(ticket=req.ticket)
            if positions is None or len(positions) == 0:
                return TradeResponse(success=False, error=f"Position {req.ticket} not found"), "position_not_found"
            
            position = positions[0]
            mt5_symbol = position.symbol
            
            symbol_info = mt5.symbol_info(mt5_symbol)
            if symbol_info is None:
                return TradeResponse(success=False, error=f"Symbol info unavailable for {mt5_symbol}"), "symbol_missing"

            volume_error = _validate_close_volume(req.volume, float(position.volume), symbol_info)
            if volume_error:
                return TradeResponse(success=False, error=volume_error), "invalid_volume"

            try:
                close_request = build_close_request(position, req.volume, symbol_info)
            except ValueError as exc:
                return TradeResponse(success=False, error=str(exc)), "invalid_volume"
            logger.info("Submitting MT5 close order: %s", close_request)

            result = mt5.order_send(close_request)
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
                    filled_quantity=float(getattr(result, "volume", close_request["volume"]) or close_request["volume"]),
                    ticket_id=int(getattr(result, "order", 0) or 0),
                    error=None,
                ),
                "fill_confirmed",
            )

        loop = asyncio.get_running_loop()
        try:
            response, trade_state = await asyncio.wrap_future(submit(_execute_in_worker), loop=loop)
            log_trade(req, response, metadata={"state": trade_state})
            logger.info("MT5 close order result: %s", response.model_dump())
            if response.success:
                return response
            if trade_state == "position_not_found":
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.error)
            if trade_state == "invalid_volume":
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=response.error)
            if trade_state == "symbol_missing":
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.error)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.error or "Close request failed")
        except ConnectionError:
            raise HTTPException(status_code=503, detail="Not connected to MT5")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    finally:
        _release_single_flight()
