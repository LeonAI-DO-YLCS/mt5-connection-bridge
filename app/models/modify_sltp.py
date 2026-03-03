from __future__ import annotations

from pydantic import BaseModel, Field

class ModifySLTPRequest(BaseModel):
    """
    Request model for modifying Stop Loss and Take Profit.
    """
    sl: float | None = Field(default=None, description="New stop loss price. None removes it.")
    tp: float | None = Field(default=None, description="New take profit price. None removes it.")
