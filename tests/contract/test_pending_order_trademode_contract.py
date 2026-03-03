from __future__ import annotations

from types import SimpleNamespace

from app.mt5_worker import WorkerState


def test_pending_order_rejects_sell_limit_when_symbol_is_long_only(
    client,
    auth_headers,
    monkeypatch,
    fake_mt5,
    completed_future_factory,
):
    from app.main import settings
    from app.routes import pending_order as pending_order_route

    settings.execution_enabled = True
    fake_mt5._symbol_info = SimpleNamespace(
        name="EURUSD",
        trade_mode=1,  # Long only
        visible=True,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        spread=10,
        filling_mode=3,
    )
    monkeypatch.setattr(pending_order_route, "get_state", lambda: WorkerState.AUTHORIZED)
    monkeypatch.setattr(
        pending_order_route,
        "submit",
        lambda fn: completed_future_factory(fn()),
    )

    response = client.post(
        "/pending-order",
        headers=auth_headers,
        json={
            "ticker": "V75",
            "type": "sell_limit",
            "volume": 0.01,
            "price": 100.0,
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert "detail" in payload
    assert "only allows long" in payload["detail"].lower()

