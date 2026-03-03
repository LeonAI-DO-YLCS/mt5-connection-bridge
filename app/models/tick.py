from __future__ import annotations

from pydantic import BaseModel, Field

class TickPrice(BaseModel):
    """
    Represents the latest tick price for a symbol.
    """
    ticker: str = Field(..., description="Instrument symbol")
    bid: float = Field(..., description="Current bid price")
    ask: float = Field(..., description="Current ask price")
    spread: float = Field(..., description="Current spread (ask - bid)")
    time: str = Field(..., description="Time of the tick in ISO 8601 format (UTC)")
