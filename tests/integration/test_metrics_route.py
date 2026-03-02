from __future__ import annotations


def test_metrics_endpoint_returns_summary(client, auth_headers):
    client.get("/health", headers=auth_headers)

    response = client.get("/metrics", headers=auth_headers)
    payload = response.json()

    assert response.status_code == 200
    assert payload["retention_days"] == 90
    assert payload["total_requests"] >= 1
