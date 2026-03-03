import asyncio
import logging
import threading

from fastapi import APIRouter, HTTPException, status

from ..audit import log_trade
from ..main import settings, symbol_map
from ..mappers.trade_mapper import build_pending_order_request
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
async def pending_order(req: PendingOrderRequest) -> TradeResponse:
    if not settings.execution_enabled:
        response = TradeResponse(success=False, error="Execution disabled by policy (EXECUTION_ENABLED=false).")
        log_trade(req, response, metadata={"state": "blocked_execution_disabled"})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=response.error)

    if req.ticker not in symbol_map:
        response = TradeResponse(success=False, error=f"Unknown ticker '{req.ticker}'")
        log_trade(req, response, metadata={"state": "blocked_unknown_symbol"})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.error)

    mt5_symbol = symbol_map[req.ticker].mt5_symbol

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
            
            symbol_info = mt5.symbol_info(mt5_symbol)
            if symbol_info is None:
                return TradeResponse(success=False, error=f"Symbol info unavailable for {mt5_symbol}"), "symbol_missing"

            try:
                request_dict = build_pending_order_request(req, mt5_symbol, symbol_info)
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
                return response
            if trade_state in {"invalid_params"}:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=response.error)
            if trade_state in {"symbol_missing"}:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.error)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.error or "Pending order request failed",
            )
        except ConnectionError:
            raise HTTPException(status_code=503, detail="Not connected to MT5")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    finally:
        _release_single_flight()
