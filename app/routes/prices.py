"""
MT5 Bridge — GET /prices endpoint.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from ..config import get_mt5_timeframe
from ..main import symbol_map
from ..mappers.price_mapper import map_mt5_rates_to_prices
from ..models.price import PriceResponse
from ..mt5_worker import WorkerState, get_state, submit

logger = logging.getLogger("mt5_bridge.prices")

router = APIRouter(tags=["prices"])


@router.get("/prices", response_model=PriceResponse)
async def get_prices(
    ticker: str = Query(..., description="User-facing ticker name (must exist in symbol map)"),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    timeframe: str = Query("D1", description="MT5 timeframe: M1, M5, M15, M30, H1, H4, D1, W1, MN1"),
):
    if ticker not in symbol_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown ticker: {ticker}",
        )

    try:
        tf_const = get_mt5_timeframe(timeframe)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dates must be in YYYY-MM-DD format.",
        )

    if get_state() not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MT5 terminal not connected",
        )

    mt5_symbol = symbol_map[ticker].mt5_symbol

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
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MT5 error: {exc}",
        ) from exc

    return map_mt5_rates_to_prices(rates, ticker)
