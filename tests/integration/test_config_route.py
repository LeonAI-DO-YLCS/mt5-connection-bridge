from __future__ import annotations


def test_config_endpoint_sanitized(client, auth_headers):
    response = client.get("/config", headers=auth_headers)
    payload = response.json()

    assert response.status_code == 200
    assert "mt5_password" not in payload
    assert "mt5_bridge_api_key" not in payload
    assert payload["metrics_retention_days"] == 90
    assert "multi_trade_overload_queue_threshold" in payload


def test_config_execution_toggle_endpoint(client, auth_headers):
    initial = client.get("/config", headers=auth_headers).json()
    assert initial["execution_enabled"] is False

    enable_resp = client.put(
        "/config/execution",
        headers=auth_headers,
        json={"execution_enabled": True},
    )
    assert enable_resp.status_code == 200
    assert enable_resp.json()["execution_enabled"] is True

    roundtrip = client.get("/config", headers=auth_headers).json()
    assert roundtrip["execution_enabled"] is True

    disable_resp = client.put(
        "/config/execution",
        headers=auth_headers,
        json={"execution_enabled": False},
    )
    assert disable_resp.status_code == 200
    assert disable_resp.json()["execution_enabled"] is False
