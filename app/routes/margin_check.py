import asyncio
import logging
from fastapi import APIRouter, status

from ..messaging.codes import ErrorCode
from ..messaging.envelope import MessageEnvelopeException
from ..audit import log_task_event
from ..main import symbol_map
from ..models.margin import MarginCheckRequest, MarginCheckResponse
from ..mt5_worker import WorkerState, get_state, submit

logger = logging.getLogger("mt5_bridge.margin_check")
router = APIRouter(tags=["calculations"])

@router.post("/margin-check", response_model=MarginCheckResponse, summary="Calculate required margin")
async def margin_check(req: MarginCheckRequest) -> MarginCheckResponse:
    mt5_symbol = req.symbol.strip()
    if mt5_symbol in symbol_map:
        mt5_symbol = symbol_map[mt5_symbol].mt5_symbol

    if get_state() != WorkerState.AUTHORIZED:
        raise MessageEnvelopeException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=ErrorCode.MT5_DISCONNECTED,
            message="MT5 terminal not authorized or connected",
        )

    def _calc_margin() -> MarginCheckResponse:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        
        symbol_info = mt5.symbol_info(mt5_symbol)
        if symbol_info is None:
            raise MessageEnvelopeException(
                status_code=404,
                code=ErrorCode.SYMBOL_NOT_CONFIGURED,
                message=f"Symbol info unavailable for {mt5_symbol}",
            )

        tick = mt5.symbol_info_tick(mt5_symbol)
        if tick is None:
            raise MessageEnvelopeException(
                status_code=503,
                code=ErrorCode.SERVICE_UNAVAILABLE,
                message=f"No tick data available for {mt5_symbol}",
            )

        mt5_action = mt5.ORDER_TYPE_BUY if req.action.lower() == "buy" else mt5.ORDER_TYPE_SELL
        price = tick.ask if mt5_action == mt5.ORDER_TYPE_BUY else tick.bid

        margin = mt5.order_calc_margin(mt5_action, mt5_symbol, float(req.volume), price)
        if margin is None:
            err = mt5.last_error()
            raise MessageEnvelopeException(
                status_code=422,
                code=ErrorCode.VALIDATION_ERROR,
                message=f"Margin calculation failed: {err}",
            )

        account = mt5.account_info()
        free_margin = account.margin_free if account else 0.0
        
        return MarginCheckResponse(
            margin=float(margin),
            free_margin=float(free_margin),
            margin_rate=1.0, # Rate is informational, MT5 API directly gives absolute margin
            symbol=mt5_symbol,
            volume=req.volume
        )

    loop = asyncio.get_running_loop()
    try:
        response = await asyncio.wrap_future(submit(_calc_margin), loop=loop)
        log_task_event(
            "margin_check",
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
            "margin_check",
            request=req,
            outcome="failed",
            status_code=500,
            details={"reason": str(e)},
        )
        raise MessageEnvelopeException(
            status_code=500,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Internal error during margin calculation: {str(e)}"
        )
