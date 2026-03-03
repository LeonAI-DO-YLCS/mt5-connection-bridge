from __future__ import annotations

from pydantic import BaseModel, Field


class BrokerSymbol(BaseModel):
    """Represents a symbol available on the connected broker."""

    name: str = Field(..., description="Symbol name (e.g. EURUSD)")
    description: str = Field(..., description="Symbol description")
    path: str = Field(..., description="Symbol path in broker catalog (e.g. Forex\\Majors\\EURUSD)")
    spread: int = Field(..., description="Current spread in points")
    digits: int = Field(..., description="Number of decimal digits")
    volume_min: float = Field(..., description="Minimum allowed volume")
    volume_max: float = Field(..., description="Maximum allowed volume")
    trade_mode: int = Field(default=4, description="Trade mode integer (0=Disabled,1=LongOnly,2=ShortOnly,3=CloseOnly,4=Full)")
    trade_mode_label: str = Field(default="Full", description="Human-readable trade mode label")
    is_configured: bool = Field(..., description="Whether this symbol is mapped in the bridge config")
    # --- New fields added by feature 008-adaptive-broker-capabilities ---
    category: str = Field(default="Other", description="Top-level category derived from symbol path segment[0]")
    subcategory: str = Field(default="", description="Subcategory derived from symbol path segment[1]")
    filling_mode: int = Field(default=0, description="Filling mode bitmask from symbol_info.filling_mode")
    supported_filling_modes: list[str] = Field(
        default_factory=list,
        description="Human-readable list of supported filling modes decoded from bitmask (e.g. ['FOK', 'IOC'])",
    )
    volume_step: float = Field(default=0.01, description="Volume step size for lot sizing")
    visible: bool = Field(default=True, description="Whether symbol is visible in Market Watch")
