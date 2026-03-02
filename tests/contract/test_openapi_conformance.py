from __future__ import annotations

from pathlib import Path

import yaml


def test_openapi_schema_has_required_sections():
    contract = Path("specs/001-mt5-bridge-dashboard/contracts/openapi.yaml")
    doc = yaml.safe_load(contract.read_text(encoding="utf-8"))

    assert doc["openapi"].startswith("3.")
    assert "components" in doc
    assert "schemas" in doc["components"]


def test_response_payloads_include_required_keys(client, auth_headers):
    health = client.get("/health", headers=auth_headers).json()
    symbols = client.get("/symbols", headers=auth_headers).json()
    config = client.get("/config", headers=auth_headers).json()

    assert {"connected", "authorized"}.issubset(health.keys())
    assert "symbols" in symbols
    assert {"execution_enabled", "metrics_retention_days", "multi_trade_overload_queue_threshold"}.issubset(
        config.keys()
    )
