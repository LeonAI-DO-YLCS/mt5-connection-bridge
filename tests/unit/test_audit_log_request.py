"""
Tests for audit.log_request — T005 bridge-side observability.
Verifies that request logging creates structured entries in requests.jsonl
separate from the trade journal.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def test_log_request_creates_entry(tmp_path):
    """Verify log_request produces a well-formed JSONL line in requests.jsonl."""
    import importlib
    from app import audit

    # Patch _LOG_DIR to use temp dir
    with patch.object(audit, "_LOG_DIR", tmp_path):
        audit.log_request(
            endpoint="/prices",
            method="GET",
            status_code=200,
            duration_ms=12.5,
            metadata={"ticker": "V75"},
        )

    log_file = tmp_path / "requests.jsonl"
    assert log_file.exists(), "requests.jsonl should have been created"

    lines = [l.strip() for l in log_file.read_text().splitlines() if l.strip()]
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["event_type"] == "api_request"
    assert entry["method"] == "GET"
    assert entry["endpoint"] == "/prices"
    assert entry["status_code"] == 200
    assert entry["duration_ms"] == 12.5
    assert entry["metadata"]["ticker"] == "V75"
    assert "timestamp" in entry


def test_log_request_separate_from_trades(tmp_path):
    """Verify log_request writes to requests.jsonl, not trades.jsonl."""
    from app import audit

    with patch.object(audit, "_LOG_DIR", tmp_path):
        audit.log_request("/execute", "POST", 200, 55.0)

    trade_file = tmp_path / "trades.jsonl"
    request_file = tmp_path / "requests.jsonl"

    assert request_file.exists()
    # trades.jsonl should NOT exist from a log_request call
    assert not trade_file.exists()
