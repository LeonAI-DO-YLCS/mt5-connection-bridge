from __future__ import annotations

from types import SimpleNamespace

from app.mt5_worker import WorkerState


def test_health_requires_api_key(client):
    response = client.get("/health")
    assert response.status_code == 401


def test_health_disconnected(client, auth_headers, monkeypatch):
    from app.routes import health as health_route

    monkeypatch.setattr(health_route, "get_state", lambda: WorkerState.DISCONNECTED)

    response = client.get("/health", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["connected"] is False


def test_health_authorized(client, auth_headers, monkeypatch):
    from app.routes import health as health_route

    async def fake_account_info():
        return SimpleNamespace(company="Deriv", login=111, balance=222.5, server_time=1704067200)

    monkeypatch.setattr(health_route, "get_state", lambda: WorkerState.AUTHORIZED)
    monkeypatch.setattr(health_route, "_get_account_info", fake_account_info)

    response = client.get("/health", headers=auth_headers)
    payload = response.json()

    assert response.status_code == 200
    assert payload["connected"] is True
    assert payload["authorized"] is True
    assert payload["broker"] == "Deriv"
