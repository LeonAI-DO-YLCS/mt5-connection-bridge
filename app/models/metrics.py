from __future__ import annotations

from pydantic import BaseModel, Field


class MetricsSummary(BaseModel):
    uptime_seconds: float = Field(ge=0)
    total_requests: int = Field(ge=0)
    requests_by_endpoint: dict[str, int]
    errors_count: int = Field(ge=0)
    last_request_at: str | None = None
    retention_days: int = Field(ge=1)
