from __future__ import annotations

from app.mt5_worker import WorkerState


BASE_PAYLOAD = {
    "ticker": "V75",
    "action": "buy",
    "quantity": 0.01,
    "current_price": 100.0,
}


def test_pre_dispatch_slippage_rejection_regression(client, auth_headers, monkeypatch, fake_mt5, immediate_submit):
    from app.main import settings
    from app.routes import execute as execute_route

    settings.execution_enabled = True
    settings.max_pre_dispatch_slippage_pct = 0.01
    settings.max_post_fill_slippage_pct = 99.0
    fake_mt5._tick.ask = 200.0
    monkeypatch.setattr(execute_route, "get_state", lambda: WorkerState.AUTHORIZED)

    response = client.post("/execute", headers=auth_headers, json=BASE_PAYLOAD)
    assert response.status_code == 200
    assert "pre_dispatch_slippage_rejection" in response.json()["error"]


def test_post_fill_slippage_exception_regression(client, auth_headers, monkeypatch, fake_mt5, immediate_submit):
    from app.main import settings
    from app.routes import execute as execute_route

    settings.execution_enabled = True
    settings.max_pre_dispatch_slippage_pct = 99.0
    settings.max_post_fill_slippage_pct = 0.01
    fake_mt5._tick.ask = 100.0
    fake_mt5._order_result.price = 150.0
    monkeypatch.setattr(execute_route, "get_state", lambda: WorkerState.AUTHORIZED)

    response = client.post("/execute", headers=auth_headers, json=BASE_PAYLOAD)
    assert response.status_code == 200
    assert "post_fill_slippage_exception" in response.json()["error"]


def test_fill_confirmed_state_regression(client, auth_headers, monkeypatch, fake_mt5, immediate_submit):
    from app.main import settings
    from app.routes import execute as execute_route

    settings.execution_enabled = True
    settings.max_pre_dispatch_slippage_pct = 99.0
    settings.max_post_fill_slippage_pct = 99.0
    fake_mt5._tick.ask = 100.0
    fake_mt5._order_result.price = 100.0
    monkeypatch.setattr(execute_route, "get_state", lambda: WorkerState.AUTHORIZED)

    response = client.post("/execute", headers=auth_headers, json=BASE_PAYLOAD)
    assert response.status_code == 200
    assert response.json()["success"] is True

    logs_response = client.get("/logs?limit=10&offset=0", headers=auth_headers)
    entries = logs_response.json()["entries"]
    assert entries[-1]["metadata"]["state"] == "fill_confirmed"
