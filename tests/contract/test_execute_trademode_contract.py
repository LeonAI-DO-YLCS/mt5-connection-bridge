from __future__ import annotations

from types import SimpleNamespace

from app.mt5_worker import WorkerState


def test_execute_rejects_sell_when_symbol_is_long_only(
    client,
    auth_headers,
    monkeypatch,
    fake_mt5,
    immediate_submit,
):
    from app.main import settings
    from app.routes import execute as execute_route

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
    monkeypatch.setattr(execute_route, "get_state", lambda: WorkerState.AUTHORIZED)

    response = client.post(
        "/execute",
        headers=auth_headers,
        json={
            "ticker": "V75",
            "action": "sell",
            "quantity": 0.01,
            "current_price": 100.0,
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert "detail" in payload
    assert "only allows long" in payload["detail"].lower()

