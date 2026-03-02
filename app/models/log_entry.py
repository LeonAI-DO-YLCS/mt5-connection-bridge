from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    timestamp: str
    request: dict[str, Any]
    response: dict[str, Any]
    metadata: dict[str, Any] | None = None


class LogsResponse(BaseModel):
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1)
    entries: list[LogEntry]
