import asyncio
import logging

from fastapi import APIRouter, HTTPException, status

from ..audit import log_task_event
from ..main import symbol_map
from ..mappers.trade_mapper import build_pending_order_request
from ..models.order_check import OrderCheckResponse
from ..models.pending_order import PendingOrderRequest
from ..mt5_worker import WorkerState, get_state, submit

logger = logging.getLogger("mt5_bridge.order_check")
router = APIRouter(tags=["execution"])

@router.post("/order-check", response_model=OrderCheckResponse, summary="Pre-validate a pending order")
async def order_check(req: PendingOrderRequest) -> OrderCheckResponse:
    if req.ticker not in symbol_map:
        log_task_event(
            "order_check",
            request=req,
            outcome="failed",
            status_code=404,
            details={"reason": "unknown_ticker"},
        )
        raise HTTPException(status_code=404, detail=f"Unknown ticker '{req.ticker}'")

    mt5_symbol = symbol_map[req.ticker].mt5_symbol

    if get_state() not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
        log_task_event(
            "order_check",
            request=req,
            outcome="failed",
            status_code=503,
            details={"reason": "mt5_disconnected"},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MT5 terminal not connected",
        )

    def _execute_check() -> OrderCheckResponse:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        
        symbol_info = mt5.symbol_info(mt5_symbol)
        if symbol_info is None:
            return OrderCheckResponse(
                valid=False,
                margin=0.0,
                profit=0.0,
                equity=0.0,
                comment=f"Symbol info unavailable for {mt5_symbol}",
                retcode=-1,
            )

        try:
            request_dict = build_pending_order_request(req, mt5_symbol, symbol_info)
        except Exception as e:
            return OrderCheckResponse(
                valid=False,
                margin=0.0,
                profit=0.0,
                equity=0.0,
                comment=f"Invalid parameters: {str(e)}",
                retcode=-1,
            )

        result = mt5.order_check(request_dict)
        if result is None:
            return OrderCheckResponse(
                valid=False,
                margin=0.0,
                profit=0.0,
                equity=0.0,
                comment=f"order_check returned None: {mt5.last_error()}",
                retcode=-1,
            )

        retcode = int(getattr(result, "retcode", -1))
        retcode_done = int(getattr(mt5, "TRADE_RETCODE_DONE", 10009))
        is_valid = retcode in {0, retcode_done}

        return OrderCheckResponse(
            valid=is_valid,
            margin=float(getattr(result, "margin", 0.0) or 0.0),
            profit=float(getattr(result, "profit", 0.0) or 0.0),
            equity=float(
                getattr(result, "equity", None)
                or getattr(result, "margin_free", 0.0)
                or 0.0
            ),
            comment=getattr(result, "comment", ""),
            retcode=retcode,
        )

    loop = asyncio.get_running_loop()
    try:
        response = await asyncio.wrap_future(submit(_execute_check), loop=loop)
        log_task_event(
            "order_check",
            request=req,
            outcome="success" if response.valid else "failed",
            status_code=200 if response.valid else 422,
            details=response.model_dump(),
        )
        return response
    except ConnectionError:
        log_task_event(
            "order_check",
            request=req,
            outcome="failed",
            status_code=503,
            details={"reason": "connection_error"},
        )
        raise HTTPException(status_code=503, detail="Not connected to MT5")
    except Exception as e:
        log_task_event(
            "order_check",
            request=req,
            outcome="failed",
            status_code=500,
            details={"reason": str(e)},
        )
        raise HTTPException(status_code=500, detail=str(e))
