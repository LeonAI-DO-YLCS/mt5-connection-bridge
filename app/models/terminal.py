from __future__ import annotations

from pydantic import BaseModel, Field

class TerminalInfo(BaseModel):
    """
    Represents MT5 terminal state and connection.
    """
    build: int = Field(..., description="Terminal build version")
    name: str = Field(..., description="Terminal application name")
    path: str = Field(..., description="Terminal installation path")
    data_path: str = Field(..., description="Terminal data path")
    connected: bool = Field(..., description="Connection to broker server status")
    trade_allowed: bool = Field(..., description="Trading allowed for current account")
