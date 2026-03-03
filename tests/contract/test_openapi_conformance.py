from __future__ import annotations

from pathlib import Path

def test_feature_contract_document_exists_and_lists_006_endpoints():
    contract = Path("specs/006-mt5-bridge-dashboard/contracts/api-contracts.md")
    body = contract.read_text(encoding="utf-8")

    required_paths = [
        "GET /account",
        "GET /positions",
        "GET /orders",
        "GET /tick/{ticker}",
        "GET /terminal",
        "POST /close-position",
        "DELETE /orders/{ticket}",
        "PUT /positions/{ticket}/sltp",
        "PUT /orders/{ticket}",
        "POST /pending-order",
        "POST /order-check",
        "GET /history/deals",
        "GET /history/orders",
        "GET /broker-symbols",
    ]
    for path in required_paths:
        assert path in body


def test_response_payloads_include_required_keys(client, auth_headers):
    health = client.get("/health", headers=auth_headers).json()
    symbols = client.get("/symbols", headers=auth_headers).json()
    config = client.get("/config", headers=auth_headers).json()

    assert {"connected", "authorized"}.issubset(health.keys())
    assert "symbols" in symbols
    assert {"execution_enabled", "metrics_retention_days", "multi_trade_overload_queue_threshold"}.issubset(
        config.keys()
    )
