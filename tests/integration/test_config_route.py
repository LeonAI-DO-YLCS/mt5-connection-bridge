from __future__ import annotations


def test_config_endpoint_sanitized(client, auth_headers):
    response = client.get("/config", headers=auth_headers)
    payload = response.json()

    assert response.status_code == 200
    assert "mt5_password" not in payload
    assert "mt5_bridge_api_key" not in payload
    assert payload["metrics_retention_days"] == 90
    assert "multi_trade_overload_queue_threshold" in payload
