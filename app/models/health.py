"""
MT5 Bridge — Health status response model.
"""

from __future__ import annotations

from pydantic import BaseModel


class HealthStatus(BaseModel):
    """Diagnostic report of the bridge's operational state."""

    connected: bool = False
    authorized: bool = False
    broker: str | None = None
    account_id: int | None = None
    balance: float | None = None
    server_time_offset: int | None = None
    latency_ms: int | None = None
