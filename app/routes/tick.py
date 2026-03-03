from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

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
    if ticker not in symbol_map:
        raise HTTPException(status_code=404, detail="Ticker not found in mapped symbols")
    
    mt5_symbol = symbol_map[ticker].mt5_symbol

    if settings.disable_mt5_worker:
        raise HTTPException(status_code=503, detail="MT5 worker disabled")

    def _get_tick():
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        return mt5.symbol_info_tick(mt5_symbol)

    try:
        tick_info = await asyncio.wrap_future(submit(_get_tick))
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Not connected to MT5")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not tick_info:
        raise HTTPException(status_code=404, detail=f"Tick data for {mt5_symbol} not found")

    return TickPrice(
        ticker=ticker,
        bid=float(tick_info.bid),
        ask=float(tick_info.ask),
        spread=float(tick_info.ask - tick_info.bid), # Spread formula (ask-bid)
        time=datetime.fromtimestamp(tick_info.time, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    )
