from __future__ import annotations

from pydantic import BaseModel, Field


class WorkerInfo(BaseModel):
    state: str
    queue_depth: int = Field(ge=0)
    max_reconnect_retries: int = Field(ge=1)
    reconnect_base_delay: float = Field(ge=0)
