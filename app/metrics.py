from __future__ import annotations

import json
import threading
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models.metrics import MetricsSummary


class RollingMetrics:
    def __init__(self, retention_days: int = 90, log_path: Path | None = None) -> None:
        self.retention_days = retention_days
        self.log_path = log_path or (Path(__file__).resolve().parent.parent / "logs" / "dashboard" / "metrics.jsonl")
        self._lock = threading.Lock()
        self._start = datetime.now(timezone.utc)
        self._total_requests = 0
        self._requests_by_endpoint: dict[str, int] = defaultdict(int)
        self._errors_count = 0
        self._last_request_at: str | None = None
        self._ensure_parent()

    def _ensure_parent(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def reset(self) -> None:
        with self._lock:
            self._start = datetime.now(timezone.utc)
            self._total_requests = 0
            self._requests_by_endpoint = defaultdict(int)
            self._errors_count = 0
            self._last_request_at = None

    def record_request(self, endpoint: str, status_code: int) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._total_requests += 1
            self._requests_by_endpoint[endpoint] += 1
            if status_code >= 400:
                self._errors_count += 1
            self._last_request_at = now.isoformat()
            entry = {
                "timestamp": now.isoformat(),
                "endpoint": endpoint,
                "status_code": status_code,
            }
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
        self._prune_old_entries()

    def _prune_old_entries(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        if not self.log_path.exists():
            return

        kept: list[str] = []
        with self.log_path.open("r", encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                    ts = datetime.fromisoformat(payload["timestamp"])
                except Exception:
                    continue
                if ts >= cutoff:
                    kept.append(line)

        with self.log_path.open("w", encoding="utf-8") as fh:
            for line in kept:
                fh.write(line + "\n")

    def get_summary(self) -> MetricsSummary:
        with self._lock:
            uptime = (datetime.now(timezone.utc) - self._start).total_seconds()
            return MetricsSummary(
                uptime_seconds=uptime,
                total_requests=self._total_requests,
                requests_by_endpoint=dict(self._requests_by_endpoint),
                errors_count=self._errors_count,
                last_request_at=self._last_request_at,
                retention_days=self.retention_days,
            )
