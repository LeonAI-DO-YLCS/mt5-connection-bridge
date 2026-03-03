from __future__ import annotations

from pydantic import BaseModel, Field

class OrderCheckResponse(BaseModel):
    """
    Response model for pre-validating an order without executing.
    """
    valid: bool = Field(..., description="Whether the order is valid for execution")
    margin: float = Field(..., description="Estimated margin required")
    profit: float = Field(..., description="Estimated profit/loss")
    equity: float = Field(..., description="Projected post-trade equity")
    comment: str = Field(..., description="Explanation matching MT5 retcode")
    retcode: int = Field(..., description="MT5 internal retcode")
