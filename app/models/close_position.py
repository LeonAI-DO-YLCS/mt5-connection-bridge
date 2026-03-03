from __future__ import annotations

from pydantic import BaseModel, Field

class ClosePositionRequest(BaseModel):
    """
    Request model for closing an open position.
    """
    ticket: int = Field(..., description="Unique position ticket ID", gt=0)
    volume: float | None = Field(default=None, description="Volume to close. If None, closes full position.")
