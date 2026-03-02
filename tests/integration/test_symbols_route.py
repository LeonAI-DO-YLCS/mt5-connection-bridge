from __future__ import annotations


def test_symbols_returns_configured_catalog(client, auth_headers):
    response = client.get("/symbols", headers=auth_headers)
    assert response.status_code == 200

    payload = response.json()
    assert "symbols" in payload
    assert any(item["ticker"] == "V75" for item in payload["symbols"])
