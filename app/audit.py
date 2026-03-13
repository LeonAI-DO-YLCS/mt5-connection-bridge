"""
MT5 Bridge — Audit logging for trading and task execution events.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from .models.log_entry import LogEntry, LogsResponse
from .models.trade import TradeResponse

logger = logging.getLogger("mt5_bridge.audit")

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs" / "dashboard"
_RETENTION_DAYS = 90


def _ensure_log_dir() -> None:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)


def init_audit_logging(retention_days: int = 90) -> None:
    global _RETENTION_DAYS
    _RETENTION_DAYS = max(1, int(retention_days))
    _ensure_log_dir()


def _trade_log_path() -> Path:
    return _LOG_DIR / "trades.jsonl"


def _task_log_path() -> Path:
    return _LOG_DIR / "tasks.jsonl"


def _general_log_path() -> Path:
    return _LOG_DIR / "requests.jsonl"


def _parse_iso_ts(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _prune_jsonl_file(path: Path) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=_RETENTION_DAYS)
    if not path.exists():
        return

    kept: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except Exception:
                    continue
                parsed_ts = _parse_iso_ts(payload.get("timestamp"))
                if parsed_ts is None:
                    continue
                if parsed_ts >= cutoff:
                    kept.append(line)
    except Exception as exc:
        logger.error("Failed to prune %s: %s", path, exc)
        return

    temp = path.with_suffix(path.suffix + ".tmp")
    try:
        with temp.open("w", encoding="utf-8") as fh:
            for line in kept:
                fh.write(line + "\n")
        temp.replace(path)
    except Exception as exc:
        logger.error("Failed to write pruned log file %s: %s", path, exc)
        if temp.exists():
            try:
                temp.unlink()
            except Exception:
                pass


def _append_jsonl(path: Path, entry: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, default=str) + "\n")
    _prune_jsonl_file(path)


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


def log_trade(
    request: Any,
    response: TradeResponse,
    metadata: dict[str, Any] | None = None,
) -> None:
    _ensure_log_dir()

    request_payload = _to_serializable_payload(request)
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": request_payload,
        "response": response.model_dump(),
    }
    if metadata:
        entry["metadata"] = metadata

    try:
        _append_jsonl(_trade_log_path(), entry)
        _append_jsonl(
            _task_log_path(),
            {
                "timestamp": entry["timestamp"],
                "event_type": "trade_event",
                "task_name": request_payload.get("action", "trade_execution"),
                "request": request_payload,
                "response": response.model_dump(),
                "outcome": "success" if response.success else "failed",
                "metadata": metadata or {},
            },
        )
    except Exception as exc:
        logger.error("Failed to write trade audit log: %s", exc)


def log_task_event(
    task_name: str,
    *,
    request: Any | None = None,
    outcome: str = "success",
    status_code: int | None = None,
    details: Any | None = None,
) -> None:
    _ensure_log_dir()

    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "task_event",
        "task_name": task_name,
        "outcome": outcome,
    }
    if request is not None:
        entry["request"] = _to_serializable_payload(request)
    if status_code is not None:
        entry["status_code"] = int(status_code)
    if details is not None:
        entry["details"] = _to_serializable_payload(details)

    try:
        _append_jsonl(_task_log_path(), entry)
    except Exception as exc:
        logger.error("Failed to write task event log: %s", exc)


def log_request(
    endpoint: str,
    method: str,
    status_code: int,
    duration_ms: float,
    metadata: dict[str, Any] | None = None,
) -> None:
    _ensure_log_dir()

    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "api_request",
        "method": method,
        "endpoint": endpoint,
        "status_code": status_code,
        "duration_ms": duration_ms,
    }
    if metadata:
        entry["metadata"] = metadata

    try:
        _append_jsonl(_general_log_path(), entry)
    except Exception as exc:
        logger.error("Failed to write request audit log: %s", exc)


def read_trade_logs(limit: int = 50, offset: int = 0) -> LogsResponse:
    _ensure_log_dir()

    entries: list[LogEntry] = []
    path = _trade_log_path()
    _prune_jsonl_file(path)
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
