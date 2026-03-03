from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

class Position(BaseModel):
    """
    Represents an open holding (position) in MT5.
    """
    ticket: int = Field(..., description="Unique position ticket ID", gt=0)
    symbol: str = Field(..., description="Instrument symbol")
    type: Literal["buy", "sell"] = Field(..., description="Position direction")
    volume: float = Field(..., description="Position size in lots", gt=0)
    price_open: float = Field(..., description="Entry price")
    price_current: float = Field(..., description="Current market price")
    sl: float | None = Field(default=None, description="Stop loss price")
    tp: float | None = Field(default=None, description="Take profit price")
    profit: float = Field(..., description="Unrealized profit/loss")
    swap: float = Field(..., description="Accumulated swap")
    time: str = Field(..., description="Position open time in ISO 8601 format (UTC)")
    magic: int = Field(..., description="Expert Advisor magic number")
    comment: str = Field(..., description="Position comment")
