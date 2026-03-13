"""
MT5 Bridge — Trade request and response models.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TradeRequest(BaseModel):
    ticker: str = Field(
        ..., description="User-facing ticker name (must exist in symbol map)"
    )
    action: Literal["buy", "sell", "short", "cover"] = Field(
        ..., description="Trade action"
    )
    quantity: float = Field(
        ..., gt=0, description="Desired quantity (will be normalized to lot size)"
    )
    current_price: float = Field(
        ..., gt=0, description="Current market price for slippage protection"
    )
    multi_trade_mode: bool = Field(
        default=False, description="Allow parallel execution submissions"
    )
    sl: float | None = Field(default=None, description="Optional stop loss price")
    tp: float | None = Field(default=None, description="Optional take profit price")
    mt5_symbol_direct: str | None = Field(
        default=None,
        description=(
            "Optional raw MT5 symbol name. When set, bypasses the YAML symbol_map lookup. "
            "For use by the dashboard to trade symbols not configured in symbols.yaml. "
            "The 'ticker' field is still required for audit logging."
        ),
    )


class TradeResponse(BaseModel):
    success: bool = False
    status: str = "failed"
    requested_quantity: float | None = None
    requested_price: float | None = None
    filled_price: float | None = None
    filled_quantity: float | None = None
    unfilled_quantity: float | None = None
    ticket_id: int | None = None
    error: str | None = None
