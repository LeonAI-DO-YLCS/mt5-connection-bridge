from __future__ import annotations

import sys

from app.mt5_worker import WorkerState


def _route_module():
    import app.main  # noqa: F401

    return sys.modules["app.routes.broker_capabilities"]


def test_broker_capabilities_get_handles_connection_error(client, auth_headers, monkeypatch):
    route = _route_module()
    monkeypatch.setattr(route, "get_state", lambda: WorkerState.AUTHORIZED)

    def _submit(_fn):
        raise ConnectionError("mt5 disconnected")

    monkeypatch.setattr(route, "submit", _submit)

    response = client.get("/broker-capabilities", headers=auth_headers)
    assert response.status_code == 503
    assert "not connected" in response.json()["detail"].lower()


def test_broker_capabilities_get_handles_unexpected_error(client, auth_headers, monkeypatch):
    route = _route_module()
    monkeypatch.setattr(route, "get_state", lambda: WorkerState.AUTHORIZED)

    def _submit(_fn):
        raise RuntimeError("boom")

    monkeypatch.setattr(route, "submit", _submit)

    response = client.get("/broker-capabilities", headers=auth_headers)
    assert response.status_code == 500
    assert "boom" in response.json()["detail"].lower()


def test_broker_capabilities_refresh_rejects_disconnected_worker(client, auth_headers, monkeypatch):
    route = _route_module()
    monkeypatch.setattr(route, "get_state", lambda: WorkerState.DISCONNECTED)

    response = client.post("/broker-capabilities/refresh", headers=auth_headers)
    assert response.status_code == 503
    assert "cache not cleared" in response.json()["detail"].lower()


def test_broker_capabilities_refresh_handles_connection_and_runtime_errors(client, auth_headers, monkeypatch):
    route = _route_module()
    monkeypatch.setattr(route, "get_state", lambda: WorkerState.AUTHORIZED)

    def _submit_conn(_fn):
        raise ConnectionError("lost")

    monkeypatch.setattr(route, "submit", _submit_conn)
    conn_response = client.post("/broker-capabilities/refresh", headers=auth_headers)
    assert conn_response.status_code == 503

    def _submit_runtime(_fn):
        raise RuntimeError("refresh failed")

    monkeypatch.setattr(route, "submit", _submit_runtime)
    runtime_response = client.post("/broker-capabilities/refresh", headers=auth_headers)
    assert runtime_response.status_code == 500
    assert "refresh failed" in runtime_response.json()["detail"].lower()

