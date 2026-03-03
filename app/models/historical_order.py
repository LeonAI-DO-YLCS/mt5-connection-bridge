from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

class HistoricalOrder(BaseModel):
    """
    Represents an order from trading history in MT5.
    """
    ticket: int = Field(..., description="Unique order ticket ID")
    symbol: str = Field(..., description="Instrument symbol")
    type: str = Field(..., description="Order type (e.g., buy, sell, buy_limit)")
    volume: float = Field(..., description="Order volume in lots")
    price: float = Field(..., description="Requested price")
    sl: float | None = Field(default=None, description="Stop loss")
    tp: float | None = Field(default=None, description="Take profit")
    state: Literal["filled", "cancelled", "expired", "rejected"] = Field(..., description="Final order state")
    time_setup: str = Field(..., description="Order setup time in ISO 8601 format (UTC)")
    time_done: str = Field(..., description="Order completion time in ISO 8601 format (UTC)")
    magic: int = Field(..., description="Expert Advisor magic number")
