"""
MT5 Bridge — Application settings and configuration.

Loads environment variables and parses the symbol mapping YAML file.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


# MT5 timeframe constant mapping.
# The actual `MetaTrader5` library will only be available at runtime
# on Windows, so we define string-to-int mappings here and resolve
# them lazily via ``get_mt5_timeframe()``.
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
    """Application-wide settings loaded from environment variables."""

    # Bridge server
    mt5_bridge_port: int = Field(default=8001, alias="MT5_BRIDGE_PORT")
    mt5_bridge_api_key: str = Field(default="change-me", alias="MT5_BRIDGE_API_KEY")

    # MT5 credentials
    mt5_login: int | None = Field(default=None, alias="MT5_LOGIN")
    mt5_password: str | None = Field(default=None, alias="MT5_PASSWORD")
    mt5_server: str = Field(default="Deriv-Demo", alias="MT5_SERVER")
    mt5_path: str | None = Field(default=None, alias="MT5_PATH")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = {"env_file": ".env", "extra": "ignore"}


def load_symbol_map(config_path: str | Path | None = None) -> dict[str, SymbolEntry]:
    """Load the symbol mapping table from a YAML file.

    Parameters
    ----------
    config_path:
        Absolute or relative path to ``symbols.yaml``.  When *None*, the
        path defaults to ``config/symbols.yaml`` relative to **this
        package's parent directory** (i.e. the ``mt5-connection-bridge/``
        root).

    Returns
    -------
    dict[str, SymbolEntry]
        Mapping from user-facing ticker name to its MT5 details.
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "config" / "symbols.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Symbol map not found at {config_path}")

    with open(config_path, "r") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh)

    entries: dict[str, SymbolEntry] = {}
    for ticker, info in raw.get("symbols", {}).items():
        entries[ticker] = SymbolEntry(
            mt5_symbol=info["mt5_symbol"],
            lot_size=float(info.get("lot_size", 0.01)),
            category=info.get("category", "unknown"),
        )
    return entries


def get_mt5_timeframe(tf_string: str) -> int:
    """Resolve a human-readable timeframe string to its MT5 constant.

    Raises ``ValueError`` for unknown timeframes.
    """
    tf_upper = tf_string.upper()
    if tf_upper not in MT5_TIMEFRAME_MAP:
        valid = ", ".join(sorted(MT5_TIMEFRAME_MAP.keys()))
        raise ValueError(f"Unknown timeframe '{tf_string}'. Valid: {valid}")
    return MT5_TIMEFRAME_MAP[tf_upper]
