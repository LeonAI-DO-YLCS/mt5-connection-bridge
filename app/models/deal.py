from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

class Deal(BaseModel):
    """
    Represents a performed execution/deal in MT5.
    """
    ticket: int = Field(..., description="Unique deal ticket ID")
    order_ticket: int = Field(..., description="Ticket of the order that initiated the deal")
    position_id: int = Field(..., description="ID of the position the deal belongs to")
    symbol: str = Field(..., description="Instrument symbol")
    type: str = Field(..., description="Deal type (e.g., buy, sell)")
    entry: Literal["in", "out", "inout"] = Field(..., description="Deal entry direction")
    volume: float = Field(..., description="Deal volume in lots")
    price: float = Field(..., description="Execution price")
    profit: float = Field(..., description="Realized profit/loss")
    swap: float = Field(..., description="Swap applied on deal")
    commission: float = Field(..., description="Commission charged")
    fee: float = Field(..., description="Additional fee charged")
    time: str = Field(..., description="Time of execution in ISO 8601 format (UTC)")
    magic: int = Field(..., description="Expert Advisor magic number")
