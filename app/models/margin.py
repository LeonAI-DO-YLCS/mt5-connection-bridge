from pydantic import BaseModel, Field
from typing import Literal

class MarginCheckRequest(BaseModel):
    """Request model for safe-domain margin calculation."""
    symbol: str = Field(description="Trading symbol (ticker or mt5_symbol)")
    volume: float = Field(gt=0, description="Trade volume in lots")
    action: Literal["buy", "sell"] = Field(description="Trade direction")

class MarginCheckResponse(BaseModel):
    """Response model for margin calculation (wrapped in canonical envelope)."""
    margin: float = Field(description="Required margin for the trade")
    free_margin: float = Field(description="Available free margin after trade")
    margin_rate: float = Field(description="Margin rate applied")
    symbol: str = Field(description="Resolved MT5 symbol")
    volume: float = Field(description="Requested volume")

class ProfitCalcRequest(BaseModel):
    """Request model for profit calculation."""
    symbol: str = Field(description="Trading symbol")
    volume: float = Field(gt=0, description="Trade volume in lots")
    action: Literal["buy", "sell"] = Field(description="Trade direction")
    price_open: float = Field(gt=0, description="Entry price")
    price_close: float = Field(gt=0, description="Exit price")

class ProfitCalcResponse(BaseModel):
    """Response model for profit calculation (wrapped in canonical envelope)."""
    profit: float = Field(description="Calculated profit/loss in account currency")
    symbol: str = Field(description="Resolved MT5 symbol")
    volume: float = Field(description="Requested volume")
    price_open: float = Field(description="Entry price used")
    price_close: float = Field(description="Exit price used")
