from __future__ import annotations

from pydantic import BaseModel, Field


class ConfigInfo(BaseModel):
    mt5_bridge_port: int
    mt5_server: str
    mt5_login: int | None
    mt5_path: str | None
    log_level: str
    symbol_count: int = Field(ge=0)
    symbols_config_path: str
    execution_enabled: bool
    metrics_retention_days: int = Field(ge=1)
    multi_trade_overload_queue_threshold: int = Field(ge=1)
