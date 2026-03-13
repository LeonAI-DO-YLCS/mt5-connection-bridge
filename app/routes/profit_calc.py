import asyncio
import logging
from fastapi import APIRouter, status

from ..messaging.codes import ErrorCode
from ..messaging.envelope import MessageEnvelopeException
from ..audit import log_task_event
from ..main import symbol_map
from ..models.margin import ProfitCalcRequest, ProfitCalcResponse
from ..mt5_worker import WorkerState, get_state, submit

logger = logging.getLogger("mt5_bridge.profit_calc")
router = APIRouter(tags=["calculations"])

@router.post("/profit-calc", response_model=ProfitCalcResponse, summary="Calculate estimated profit")
async def profit_calc(req: ProfitCalcRequest) -> ProfitCalcResponse:
    mt5_symbol = req.symbol.strip()
    if mt5_symbol in symbol_map:
        mt5_symbol = symbol_map[mt5_symbol].mt5_symbol

    if get_state() != WorkerState.AUTHORIZED:
        raise MessageEnvelopeException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=ErrorCode.MT5_DISCONNECTED,
            message="MT5 terminal not authorized or connected",
        )

    def _calc_profit() -> ProfitCalcResponse:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        
        mt5_action = mt5.ORDER_TYPE_BUY if req.action.lower() == "buy" else mt5.ORDER_TYPE_SELL

        profit = mt5.order_calc_profit(mt5_action, mt5_symbol, float(req.volume), float(req.price_open), float(req.price_close))
        if profit is None:
            err = mt5.last_error()
            raise MessageEnvelopeException(
                status_code=422,
                code=ErrorCode.VALIDATION_ERROR,
                message=f"Profit calculation failed: {err}",
            )

        return ProfitCalcResponse(
            profit=float(profit),
            symbol=mt5_symbol,
            volume=req.volume,
            price_open=req.price_open,
            price_close=req.price_close
        )

    loop = asyncio.get_running_loop()
    try:
        response = await asyncio.wrap_future(submit(_calc_profit), loop=loop)
        log_task_event(
            "profit_calc",
            request=req,
            outcome="success",
            status_code=200,
            details=response.model_dump(),
        )
        return response
    except MessageEnvelopeException:
        raise
    except Exception as e:
        log_task_event(
            "profit_calc",
            request=req,
            outcome="failed",
            status_code=500,
            details={"reason": str(e)},
        )
        raise MessageEnvelopeException(
            status_code=500,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Internal error during profit calculation: {str(e)}"
        )
