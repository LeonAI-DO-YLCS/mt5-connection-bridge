"""
MT5 Bridge — Trade request and response models.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TradeRequest(BaseModel):
    """Incoming trade execution request."""

    ticker: str = Field(..., description="User-facing ticker name (must exist in symbol map)")
    action: Literal["buy", "sell", "short", "cover"] = Field(..., description="Trade action")
    quantity: float = Field(..., gt=0, description="Desired quantity (will be normalized to lot size)")
    current_price: float = Field(..., gt=0, description="Current market price for slippage protection")


class TradeResponse(BaseModel):
    """Trade execution result."""

    success: bool = False
    filled_price: float | None = None
    filled_quantity: float | None = None
    ticket_id: int | None = None
    error: str | None = None
