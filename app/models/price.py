"""
MT5 Bridge — Price data response models.

These models EXACTLY mirror the ``Price`` and ``PriceResponse`` Pydantic
models defined in the main project's ``src/data/models.py`` to ensure
schema compatibility.
"""

from __future__ import annotations

from pydantic import BaseModel


class Price(BaseModel):
    """Single OHLCV candle."""

    open: float
    close: float
    high: float
    low: float
    volume: int
    time: str


class PriceResponse(BaseModel):
    """Container returned by the ``GET /prices`` endpoint."""

    ticker: str
    prices: list[Price]
