from __future__ import annotations

from pydantic import BaseModel, Field

class BrokerSymbol(BaseModel):
    """
    Represents a symbol available on the broker.
    """
    name: str = Field(..., description="Symbol name (e.g. EURUSD)")
    description: str = Field(..., description="Symbol description")
    path: str = Field(..., description="Symbol path in broker catalog")
    spread: int = Field(..., description="Current spread in points")
    digits: int = Field(..., description="Number of decimal digits")
    volume_min: float = Field(..., description="Minimum allowed volume")
    volume_max: float = Field(..., description="Maximum allowed volume")
    trade_mode: str = Field(..., description="Trading mode for the symbol")
    is_configured: bool = Field(..., description="Whether this symbol is mapped in the bridge config")
