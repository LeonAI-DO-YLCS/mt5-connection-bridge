"""
MT5 Bridge — Audit logging for trade executions.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .models.log_entry import LogEntry, LogsResponse
from .models.trade import TradeResponse

logger = logging.getLogger("mt5_bridge.audit")

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def _ensure_log_dir() -> None:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)


def init_audit_logging() -> None:
    _ensure_log_dir()


def _trade_log_path() -> Path:
    return _LOG_DIR / "trades.jsonl"


def log_trade(
    request: Any,
    response: TradeResponse,
    metadata: dict[str, Any] | None = None,
) -> None:
    _ensure_log_dir()

    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": _to_serializable_payload(request),
        "response": response.model_dump(),
    }
    if metadata:
        entry["metadata"] = metadata

    try:
        with _trade_log_path().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")
    except Exception as exc:
        logger.error("Failed to write trade audit log: %s", exc)


def _to_serializable_payload(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {}
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    if isinstance(payload, Mapping):
        return dict(payload)
    if hasattr(payload, "__dict__"):
        return dict(vars(payload))
    return {"value": str(payload)}


def read_trade_logs(limit: int = 50, offset: int = 0) -> LogsResponse:
    _ensure_log_dir()

    entries: list[LogEntry] = []
    path = _trade_log_path()
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                    entries.append(LogEntry(**raw))
                except Exception:
                    continue

    total = len(entries)
    page = entries[offset : offset + limit]
    return LogsResponse(total=total, offset=offset, limit=limit, entries=page)
