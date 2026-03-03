from __future__ import annotations

from types import SimpleNamespace

from app.mt5_worker import WorkerState


def test_execute_accepts_mt5_symbol_direct_without_yaml_mapping(
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
        trade_mode=4,
        visible=True,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        spread=10,
        filling_mode=3,
    )
    monkeypatch.setattr(execute_route, "get_state", lambda: WorkerState.AUTHORIZED)

    captured_tickers: list[str] = []

    def _capture_log_trade(req, response, metadata=None):
        captured_tickers.append(req.ticker)

    monkeypatch.setattr(execute_route, "log_trade", _capture_log_trade)

    response = client.post(
        "/execute",
        headers=auth_headers,
        json={
            "ticker": "DIRECT",
            "action": "buy",
            "quantity": 0.01,
            "current_price": 100.0,
            "mt5_symbol_direct": "EURUSD",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["ticket_id"] is not None
    assert "DIRECT" in captured_tickers

