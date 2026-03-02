from __future__ import annotations


def test_worker_state_endpoint(client, auth_headers, monkeypatch):
    from app.routes import worker as worker_route

    class _State:
        value = "AUTHORIZED"

    monkeypatch.setattr(worker_route, "get_state", lambda: _State())
    monkeypatch.setattr(worker_route, "get_queue_depth", lambda: 3)

    response = client.get("/worker/state", headers=auth_headers)
    payload = response.json()

    assert response.status_code == 200
    assert payload["state"] == "AUTHORIZED"
    assert payload["queue_depth"] == 3
