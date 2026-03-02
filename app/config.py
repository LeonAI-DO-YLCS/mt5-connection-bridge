"""
MT5 Bridge — Application settings and configuration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# MT5 timeframe constant mapping.
MT5_TIMEFRAME_MAP: dict[str, int] = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 16385,
    "H4": 16388,
    "D1": 16408,
    "W1": 32769,
    "MN1": 49153,
}


class SymbolEntry:
    """Single entry in the symbol mapping table."""

    def __init__(self, mt5_symbol: str, lot_size: float, category: str) -> None:
        self.mt5_symbol = mt5_symbol
        self.lot_size = lot_size
        self.category = category

    def __repr__(self) -> str:
        return f"SymbolEntry({self.mt5_symbol!r}, lot={self.lot_size}, cat={self.category!r})"


class Settings(BaseSettings):
    # Bridge server
    mt5_bridge_port: int = Field(default=8001, alias="MT5_BRIDGE_PORT")
    mt5_bridge_api_key: str = Field(default="change-me", alias="MT5_BRIDGE_API_KEY")

    # MT5 credentials
    mt5_login: int | None = Field(default=None, alias="MT5_LOGIN")
    mt5_password: str | None = Field(default=None, alias="MT5_PASSWORD")
    mt5_server: str = Field(default="Deriv-Demo", alias="MT5_SERVER")
    mt5_path: str | None = Field(default=None, alias="MT5_PATH")

    # Runtime policy
    execution_enabled: bool = Field(default=False, alias="EXECUTION_ENABLED")
    metrics_retention_days: int = Field(default=90, alias="METRICS_RETENTION_DAYS")
    multi_trade_overload_queue_threshold: int = Field(
        default=100, alias="MULTI_TRADE_OVERLOAD_QUEUE_THRESHOLD"
    )
    max_pre_dispatch_slippage_pct: float = Field(default=1.0, alias="MAX_PRE_DISPATCH_SLIPPAGE_PCT")
    max_post_fill_slippage_pct: float = Field(default=1.0, alias="MAX_POST_FILL_SLIPPAGE_PCT")

    # Paths / logging
    symbols_config_path: str = Field(default="config/symbols.yaml", alias="SYMBOLS_CONFIG_PATH")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Test support
    disable_mt5_worker: bool = Field(default=False, alias="DISABLE_MT5_WORKER")

    model_config = {"env_file": ".env", "extra": "ignore"}


def load_symbol_map(config_path: str | Path | None = None) -> dict[str, SymbolEntry]:
    if config_path is None:
        settings = Settings()
        config_path = settings.symbols_config_path

    cfg = Path(config_path)
    if not cfg.is_absolute():
        cfg = PROJECT_ROOT / cfg

    if not cfg.exists():
        raise FileNotFoundError(f"Symbol map not found at {cfg}")

    with cfg.open("r", encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh) or {}

    entries: dict[str, SymbolEntry] = {}
    for ticker, info in raw.get("symbols", {}).items():
        entries[ticker] = SymbolEntry(
            mt5_symbol=info["mt5_symbol"],
            lot_size=float(info.get("lot_size", 0.01)),
            category=str(info.get("category", "unknown")),
        )
    return entries


def get_mt5_timeframe(tf_string: str) -> int:
    tf_upper = tf_string.upper()
    if tf_upper not in MT5_TIMEFRAME_MAP:
        valid = ", ".join(sorted(MT5_TIMEFRAME_MAP.keys()))
        raise ValueError(f"Unknown timeframe '{tf_string}'. Valid: {valid}")
    return MT5_TIMEFRAME_MAP[tf_upper]
