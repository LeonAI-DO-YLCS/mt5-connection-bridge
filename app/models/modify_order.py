from __future__ import annotations

from pydantic import BaseModel, Field

class ModifyOrderRequest(BaseModel):
    """
    Request model for modifying a pending order.
    """
    price: float | None = Field(default=None, description="New trigger price. None leaves unchanged.")
    sl: float | None = Field(default=None, description="New stop loss price. None removes it.")
    tp: float | None = Field(default=None, description="New take profit price. None removes it.")
