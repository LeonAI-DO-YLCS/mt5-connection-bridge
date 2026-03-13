from pydantic import BaseModel, Field
from typing import Literal, Optional

class MarketBookEntry(BaseModel):
    """Single entry in the market depth book."""
    type: Literal["buy", "sell", "buy_market", "sell_market"] = Field(description="Book entry type")
    price: float = Field(description="Price level")
    volume: float = Field(description="Volume at price level")
    volume_real: Optional[float] = Field(default=None, description="Extended volume (MT5-specific)")
