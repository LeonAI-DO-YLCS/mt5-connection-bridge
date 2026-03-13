from __future__ import annotations

from pydantic import BaseModel, Field

from .compatibility import CompatibilityProfile

class RuntimeDiagnostics(BaseModel):
    app_version: str
    started_at: str
    uptime_seconds: float = Field(ge=0.0)
    worker_state: str
    queue_depth: int = Field(ge=0)
    mt5_connected: bool
    execution_enabled: bool
    execution_policy_source: str
    symbol_count: int = Field(ge=0)
    symbols_config_path: str
    runtime_state_path: str
    runtime_state_exists: bool
    launcher_run_id: str | None = None
    last_termination_reason: str | None = None
    log_bundle_hint: str | None = None
    config_fingerprint: str
    compatibility_profile: CompatibilityProfile


class SymbolDiagnostic(BaseModel):
    ticker: str
    configured_mt5_symbol: str
    broker_symbol_found: bool
    symbol_info_available: bool
    visible: bool | None = None
    reason_code: str
    reason: str
    suggested_matches: list[str] = Field(default_factory=list)


class SymbolsDiagnosticsResponse(BaseModel):
    generated_at: str
    worker_state: str
    configured_symbols: int = Field(ge=0)
    checked_count: int = Field(ge=0)
    items: list[SymbolDiagnostic]

