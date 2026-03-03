from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Path

from ..main import settings, symbol_map
from ..models.tick import TickPrice
from ..mt5_worker import submit

router = APIRouter(tags=["tick"])

@router.get("/tick/{ticker}", response_model=TickPrice, summary="Get latest tick price")
async def get_tick(ticker: str = Path(..., description="Instrument ticker symbol (bridge mapping)")):
    """
    Retrieve the current bid/ask and spread for a specific symbol.
    """
    if ticker in symbol_map:
        mt5_symbol = symbol_map[ticker].mt5_symbol
    else:
        # Allow direct broker symbol lookup for dashboard live-catalog flows.
        mt5_symbol = ticker

    if settings.disable_mt5_worker:
        raise HTTPException(status_code=503, detail="MT5 worker disabled")

    def _get_tick():
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        symbol_info = mt5.symbol_info(mt5_symbol)
        if symbol_info is None:
            return None
        if not bool(getattr(symbol_info, "visible", True)) and settings.auto_select_symbols:
            mt5.symbol_select(mt5_symbol, True)
        return mt5.symbol_info_tick(mt5_symbol)

    try:
        tick_info = await asyncio.wrap_future(submit(_get_tick))
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Not connected to MT5")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not tick_info:
        raise HTTPException(status_code=404, detail=f"Tick data for {mt5_symbol} not found")

    tick_ts = int(getattr(tick_info, "time", 0) or 0)
    if tick_ts > 0:
        tick_time = datetime.fromtimestamp(tick_ts, tz=timezone.utc)
    else:
        tick_time = datetime.now(timezone.utc)

    return TickPrice(
        ticker=ticker,
        bid=float(tick_info.bid),
        ask=float(tick_info.ask),
        spread=float(tick_info.ask - tick_info.bid), # Spread formula (ask-bid)
        time=tick_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z",
    )
