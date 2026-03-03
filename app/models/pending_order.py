from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

class PendingOrderRequest(BaseModel):
    """
    Request model for placing a pending order.
    """
    ticker: str = Field(..., description="Instrument ticker symbol (bridge mapping)")
    type: Literal["buy_limit", "sell_limit", "buy_stop", "sell_stop"] = Field(..., description="Pending order type")
    volume: float = Field(..., description="Requested volume in lots", gt=0)
    price: float = Field(..., description="Trigger price", gt=0)
    sl: float | None = Field(default=None, description="Optional stop loss price")
    tp: float | None = Field(default=None, description="Optional take profit price")
    comment: str = Field(default="", description="Optional comment for the order")
    mt5_symbol_direct: str | None = Field(
        default=None,
        description=(
            "Optional raw MT5 symbol name. When set, bypasses the YAML symbol_map lookup. "
            "Used by dashboard workflows for symbols not present in symbols.yaml."
        ),
    )
