from __future__ import annotations

from pathlib import Path

import yaml


def test_execution_paths_present_in_openapi():
    contract = Path("specs/001-mt5-bridge-dashboard/contracts/openapi.yaml")
    doc = yaml.safe_load(contract.read_text(encoding="utf-8"))

    assert "/config" in doc["paths"]
    assert "/logs" in doc["paths"]


def test_config_logs_runtime_contracts(client, auth_headers):
    config = client.get("/config", headers=auth_headers)
    logs = client.get("/logs", headers=auth_headers)

    assert config.status_code == 200
    assert logs.status_code == 200
