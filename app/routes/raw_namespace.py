import asyncio
import logging
from typing import Literal, Dict, Any

from fastapi import APIRouter, status, Query

from ..messaging.codes import ErrorCode
from ..messaging.envelope import MessageEnvelopeException
from ..audit import log_task_event
from ..main import symbol_map
from ..models.market_book import MarketBookEntry
from ..mt5_worker import WorkerState, get_state, submit

logger = logging.getLogger("mt5_bridge.raw_namespace")
router = APIRouter(prefix="/mt5/raw", tags=["advanced"])

def _raw_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Wraps raw data with namespace and safety disclaimer."""
    return {
        "namespace": "advanced",
        "safety_disclaimer": "RAW_NAMESPACE_UNVALIDATED",
        "data": data
    }

def _resolve_symbol(symbol: str) -> str:
    mt5_symbol = symbol.strip()
    if mt5_symbol in symbol_map:
        return symbol_map[mt5_symbol].mt5_symbol
    return mt5_symbol

def _check_worker():
    if get_state() != WorkerState.AUTHORIZED:
        raise MessageEnvelopeException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=ErrorCode.MT5_DISCONNECTED,
            message="MT5 terminal not authorized or connected",
        )

@router.get("/margin-check", summary="Raw margin check (Expert Namespace)")
async def raw_margin_check(
    symbol: str = Query(..., description="Trading symbol"),
    volume: float = Query(..., gt=0, description="Trade volume"),
    action: Literal["buy", "sell"] = Query(..., description="Trade action")
):
    _check_worker()
    mt5_symbol = _resolve_symbol(symbol)

    def _calc() -> Dict[str, Any]:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        
        mt5_action = mt5.ORDER_TYPE_BUY if action.lower() == "buy" else mt5.ORDER_TYPE_SELL
        
        tick = mt5.symbol_info_tick(mt5_symbol)
        if tick is None:
            raise MessageEnvelopeException(
                status_code=503,
                code=ErrorCode.SERVICE_UNAVAILABLE,
                message=f"No tick data available for {mt5_symbol}",
            )

        price = tick.ask if mt5_action == mt5.ORDER_TYPE_BUY else tick.bid
        margin = mt5.order_calc_margin(mt5_action, mt5_symbol, float(volume), price)
        
        return {
            "margin": margin,
            "last_error": mt5.last_error() if margin is None else None
        }

    loop = asyncio.get_running_loop()
    result = await asyncio.wrap_future(submit(_calc), loop=loop)
    return _raw_response(result)


@router.get("/profit-calc", summary="Raw profit calc (Expert Namespace)")
async def raw_profit_calc(
    symbol: str = Query(..., description="Trading symbol"),
    volume: float = Query(..., gt=0, description="Trade volume"),
    action: Literal["buy", "sell"] = Query(..., description="Trade action"),
    price_open: float = Query(..., gt=0, description="Entry price"),
    price_close: float = Query(..., gt=0, description="Exit price")
):
    _check_worker()
    mt5_symbol = _resolve_symbol(symbol)

    def _calc() -> Dict[str, Any]:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        
        mt5_action = mt5.ORDER_TYPE_BUY if action.lower() == "buy" else mt5.ORDER_TYPE_SELL
        profit = mt5.order_calc_profit(mt5_action, mt5_symbol, float(volume), float(price_open), float(price_close))
        
        return {
            "profit": profit,
            "last_error": mt5.last_error() if profit is None else None
        }

    loop = asyncio.get_running_loop()
    result = await asyncio.wrap_future(submit(_calc), loop=loop)
    return _raw_response(result)


@router.get("/market-book", summary="Raw market book (Expert Namespace)")
async def raw_market_book(
    symbol: str = Query(..., description="Trading symbol")
):
    _check_worker()
    mt5_symbol = _resolve_symbol(symbol)

    def _calc() -> Dict[str, Any]:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        
        if not mt5.market_book_add(mt5_symbol):
            return {"error": f"Failed to add market book for {mt5_symbol}", "last_error": mt5.last_error()}
            
        try:
            depth_data = mt5.market_book_get(mt5_symbol)
            if depth_data is None:
                return {"error": "No market depth data", "last_error": mt5.last_error()}
            
            entries = []
            for d in depth_data:
                # MT5 market_book_get returns BookInfo objects
                etype = "buy"  # fallback default
                if getattr(d, "type", 0) == getattr(mt5, "BOOK_TYPE_BUY", 1):
                    etype = "buy"
                elif getattr(d, "type", 0) == getattr(mt5, "BOOK_TYPE_SELL", 2):
                    etype = "sell"
                elif getattr(d, "type", 0) == getattr(mt5, "BOOK_TYPE_BUY_MARKET", 3):
                    etype = "buy_market"
                elif getattr(d, "type", 0) == getattr(mt5, "BOOK_TYPE_SELL_MARKET", 4):
                    etype = "sell_market"
                
                entry = MarketBookEntry(
                    type=etype, # type: ignore
                    price=float(getattr(d, "price", 0.0)),
                    volume=float(getattr(d, "volume", 0.0)),
                    volume_real=float(getattr(d, "volume_double", 0.0)) if hasattr(d, "volume_double") else None
                )
                entries.append(entry.model_dump())
            
            return {"entries": entries}
        finally:
            mt5.market_book_release(mt5_symbol)

    loop = asyncio.get_running_loop()
    result = await asyncio.wrap_future(submit(_calc), loop=loop)
    if "error" in result:
        raise MessageEnvelopeException(
            status_code=400,
            code=ErrorCode.VALIDATION_ERROR,
            message=result["error"],
            details={"mt5_error": result["last_error"]}
        )
    return _raw_response(result)


@router.get("/terminal-info", summary="Raw terminal info (Expert Namespace)")
async def raw_terminal_info():
    _check_worker()
    def _calc() -> Dict[str, Any]:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        info = mt5.terminal_info()
        return info._asdict() if info else {"error": "Could not get terminal info", "last_error": mt5.last_error()}

    loop = asyncio.get_running_loop()
    result = await asyncio.wrap_future(submit(_calc), loop=loop)
    return _raw_response(result)


@router.get("/account-info", summary="Raw account info (Expert Namespace)")
async def raw_account_info():
    _check_worker()
    def _calc() -> Dict[str, Any]:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        info = mt5.account_info()
        return info._asdict() if info else {"error": "Could not get account info", "last_error": mt5.last_error()}

    loop = asyncio.get_running_loop()
    result = await asyncio.wrap_future(submit(_calc), loop=loop)
    return _raw_response(result)


@router.get("/last-error", summary="Raw last error (Expert Namespace)")
async def raw_last_error():
    _check_worker()
    def _calc() -> Dict[str, Any]:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        err = mt5.last_error()
        return {"code": err[0], "message": err[1]} if err else {"code": 0, "message": "No error"}

    loop = asyncio.get_running_loop()
    result = await asyncio.wrap_future(submit(_calc), loop=loop)
    return _raw_response(result)
