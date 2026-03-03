from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

class Order(BaseModel):
    """
    Represents a pending order in MT5.
    """
    ticket: int = Field(..., description="Unique order ticket ID", gt=0)
    symbol: str = Field(..., description="Instrument symbol")
    type: Literal["buy_limit", "sell_limit", "buy_stop", "sell_stop"] = Field(..., description="Pending order type")
    volume: float = Field(..., description="Requested volume in lots", gt=0)
    price: float = Field(..., description="Trigger price", gt=0)
    sl: float | None = Field(default=None, description="Stop loss price")
    tp: float | None = Field(default=None, description="Take profit price")
    time_setup: str = Field(..., description="Order setup time in ISO 8601 format (UTC)")
    magic: int = Field(..., description="Expert Advisor magic number")
