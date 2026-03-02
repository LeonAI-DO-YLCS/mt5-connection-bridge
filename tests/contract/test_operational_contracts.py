from __future__ import annotations

from pathlib import Path

import yaml


def test_operational_paths_present_in_openapi():
    contract = Path("specs/001-mt5-bridge-dashboard/contracts/openapi.yaml")
    doc = yaml.safe_load(contract.read_text(encoding="utf-8"))

    assert "/symbols" in doc["paths"]
    assert "/worker/state" in doc["paths"]
    assert "/metrics" in doc["paths"]


def test_operational_runtime_contracts(client, auth_headers):
    symbols = client.get("/symbols", headers=auth_headers)
    worker = client.get("/worker/state", headers=auth_headers)
    metrics = client.get("/metrics", headers=auth_headers)

    assert symbols.status_code == 200
    assert worker.status_code == 200
    assert metrics.status_code == 200
