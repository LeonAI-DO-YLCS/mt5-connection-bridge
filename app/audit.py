"""
MT5 Bridge — Audit logging for trade executions.

Appends JSON-lines entries to ``logs/trades.jsonl`` for every trade
request and response pair (FR-009).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models.trade import TradeRequest, TradeResponse

logger = logging.getLogger("mt5_bridge.audit")

# Resolve log directory relative to the bridge project root
_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


def _ensure_log_dir() -> None:
    """Create the logs directory if it doesn't exist."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)


def init_audit_logging() -> None:
    """Initialize audit log storage directory at application startup."""
    _ensure_log_dir()


def log_trade(request: TradeRequest, response: TradeResponse) -> None:
    """Append a trade audit record to ``logs/trades.jsonl``.

    Each line is a self-contained JSON object with timestamp, request,
    and response fields.
    """
    _ensure_log_dir()

    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": request.model_dump(),
        "response": response.model_dump(),
    }

    log_path = _LOG_DIR / "trades.jsonl"
    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")
    except Exception as exc:
        logger.error("Failed to write trade audit log: %s", exc)
