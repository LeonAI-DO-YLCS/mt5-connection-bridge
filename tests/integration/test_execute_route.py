from __future__ import annotations

from app.mt5_worker import WorkerState


BASE_PAYLOAD = {
    "ticker": "V75",
    "action": "buy",
    "quantity": 0.01,
    "current_price": 100.0,
}


def test_execute_blocked_when_disabled(client, auth_headers, monkeypatch, immediate_submit):
    from app.main import settings
    from app.routes import execute as execute_route

    settings.execution_enabled = False
    monkeypatch.setattr(execute_route, "get_state", lambda: WorkerState.AUTHORIZED)

    response = client.post("/execute", headers=auth_headers, json=BASE_PAYLOAD)
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is False
    assert "disabled" in payload["error"].lower()


def test_execute_pre_dispatch_slippage_rejection(client, auth_headers, monkeypatch, fake_mt5, immediate_submit):
    from app.main import settings
    from app.routes import execute as execute_route

    settings.execution_enabled = True
    settings.max_pre_dispatch_slippage_pct = 0.05
    fake_mt5._tick.ask = 150.0

    monkeypatch.setattr(execute_route, "get_state", lambda: WorkerState.AUTHORIZED)

    response = client.post("/execute", headers=auth_headers, json=BASE_PAYLOAD)
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is False
    assert "pre_dispatch_slippage_rejection" in payload["error"]


def test_execute_post_fill_slippage_exception(client, auth_headers, monkeypatch, fake_mt5, immediate_submit):
    from app.main import settings
    from app.routes import execute as execute_route

    settings.execution_enabled = True
    settings.max_pre_dispatch_slippage_pct = 99.0
    settings.max_post_fill_slippage_pct = 0.01
    fake_mt5._tick.ask = 100.0
    fake_mt5._order_result.price = 120.0

    monkeypatch.setattr(execute_route, "get_state", lambda: WorkerState.AUTHORIZED)

    response = client.post("/execute", headers=auth_headers, json=BASE_PAYLOAD)
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is False
    assert "post_fill_slippage_exception" in payload["error"]


def test_execute_fill_confirmed_success(client, auth_headers, monkeypatch, fake_mt5, immediate_submit):
    from app.main import settings
    from app.routes import execute as execute_route

    settings.execution_enabled = True
    settings.max_pre_dispatch_slippage_pct = 99.0
    settings.max_post_fill_slippage_pct = 99.0
    fake_mt5._tick.ask = 100.0
    fake_mt5._order_result.price = 100.01
    fake_mt5._order_result.volume = 0.01

    monkeypatch.setattr(execute_route, "get_state", lambda: WorkerState.AUTHORIZED)

    response = client.post("/execute", headers=auth_headers, json=BASE_PAYLOAD)
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["ticket_id"] is not None


def test_execute_overload_threshold_rejection(client, auth_headers, monkeypatch, immediate_submit):
    from app.main import settings
    from app.routes import execute as execute_route

    settings.execution_enabled = True
    settings.multi_trade_overload_queue_threshold = 1

    monkeypatch.setattr(execute_route, "get_queue_depth", lambda: 10)

    response = client.post("/execute", headers=auth_headers, json=BASE_PAYLOAD)
    payload = response.json()

    assert response.status_code == 200
    assert payload["success"] is False
    assert "overload" in payload["error"].lower()


def test_execute_parallel_submission_behavior(client, auth_headers, monkeypatch, immediate_submit):
    from app.main import settings
    from app.routes import execute as execute_route

    settings.execution_enabled = True
    monkeypatch.setattr(execute_route, "get_state", lambda: WorkerState.AUTHORIZED)

    execute_route._inflight_requests = 1

    blocked = client.post("/execute", headers=auth_headers, json=BASE_PAYLOAD)
    assert blocked.json()["success"] is False

    allowed_payload = dict(BASE_PAYLOAD)
    allowed_payload["multi_trade_mode"] = True
    allowed = client.post("/execute", headers=auth_headers, json=allowed_payload)
    assert allowed.status_code == 200
