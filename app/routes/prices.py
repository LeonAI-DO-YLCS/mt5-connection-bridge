"""
MT5 Bridge — GET /prices endpoint.

Returns OHLCV candle data for a given ticker and date range,
mapped to the ``PriceResponse`` schema.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from ..config import get_mt5_timeframe
from ..main import symbol_map
from ..mappers.price_mapper import map_mt5_rates_to_prices
from ..mt5_worker import WorkerState, get_state, submit

logger = logging.getLogger("mt5_bridge.prices")

router = APIRouter(tags=["prices"])


@router.get("/prices")
async def get_prices(
    ticker: str = Query(..., description="User-facing ticker name (must exist in symbol map)"),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    timeframe: str = Query("D1", description="MT5 timeframe: M1, M5, M15, M30, H1, H4, D1, W1, MN1"),
):
    """Fetch historical price data from the MT5 terminal.

    The response conforms to the ``PriceResponse`` schema defined in
    ``src/data/models.py`` of the main AI Hedge Fund project.
    """
    # Validate ticker
    if ticker not in symbol_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown ticker: {ticker}",
        )

    # Validate timeframe
    try:
        tf_const = get_mt5_timeframe(timeframe)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # Validate dates
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dates must be in YYYY-MM-DD format.",
        )

    # Check worker state
    if get_state() not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MT5 terminal not connected",
        )

    # Resolve MT5 symbol
    mt5_symbol = symbol_map[ticker].mt5_symbol

    # Submit MT5 call to worker queue
    def _fetch():
        import MetaTrader5 as mt5  # type: ignore[import-untyped]

        rates = mt5.copy_rates_range(mt5_symbol, tf_const, start_dt, end_dt)
        if rates is None:
            err = mt5.last_error()
            logger.warning("copy_rates_range returned None for %s: %s", mt5_symbol, err)
        return rates

    try:
        loop = asyncio.get_running_loop()
        fut = submit(_fetch)
        rates = await asyncio.wrap_future(fut, loop=loop)
    except ConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MT5 error: {exc}",
        )

    return map_mt5_rates_to_prices(rates, ticker)
