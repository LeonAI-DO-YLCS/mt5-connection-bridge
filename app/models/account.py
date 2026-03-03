from __future__ import annotations

from pydantic import BaseModel, Field

class AccountInfo(BaseModel):
    """
    Represents overall MT5 account status and metrics.
    """
    login: int = Field(..., description="Account number")
    server: str = Field(..., description="Broker server name")
    balance: float = Field(..., description="Account balance")
    equity: float = Field(..., description="Account equity")
    margin: float = Field(..., description="Used margin")
    free_margin: float = Field(..., description="Free margin")
    profit: float = Field(..., description="Total floating profit")
    currency: str = Field(..., description="Account base currency")
    leverage: int = Field(..., description="Account leverage")
