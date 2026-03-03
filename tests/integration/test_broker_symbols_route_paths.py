from __future__ import annotations

from types import SimpleNamespace

from app.mt5_worker import WorkerState


def _wire_connected(route_module, monkeypatch, completed_future_factory):
    monkeypatch.setattr(route_module, "get_state", lambda: WorkerState.AUTHORIZED)
    monkeypatch.setattr(route_module, "submit", lambda fn: completed_future_factory(fn()))


def test_broker_symbols_returns_empty_when_mt5_has_no_symbols(
    client,
    auth_headers,
    monkeypatch,
    fake_mt5,
    completed_future_factory,
):
    from app.routes import broker_symbols as broker_symbols_route

    _wire_connected(broker_symbols_route, monkeypatch, completed_future_factory)
    fake_mt5.symbols_get = lambda *args, **kwargs: None
    fake_mt5.last_error = lambda: (1, "no symbols")

    response = client.get("/broker-symbols", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 0
    assert payload["symbols"] == []


def test_broker_symbols_returns_500_for_mt5_symbol_fetch_failure(
    client,
    auth_headers,
    monkeypatch,
    fake_mt5,
    completed_future_factory,
):
    from app.routes import broker_symbols as broker_symbols_route

    _wire_connected(broker_symbols_route, monkeypatch, completed_future_factory)
    fake_mt5.symbols_get = lambda *args, **kwargs: None
    fake_mt5.last_error = lambda: (500, "fatal")

    response = client.get("/broker-symbols", headers=auth_headers)
    assert response.status_code == 500
    assert "failed to fetch symbols" in response.json()["detail"].lower()


def test_broker_symbols_handles_invalid_trade_mode_and_filling_mode_values(
    client,
    auth_headers,
    monkeypatch,
    fake_mt5,
    completed_future_factory,
):
    from app.routes import broker_symbols as broker_symbols_route

    _wire_connected(broker_symbols_route, monkeypatch, completed_future_factory)
    fake_mt5.symbols_get = lambda *args, **kwargs: [
        SimpleNamespace(
            name="BROKEN",
            description="Bad metadata",
            path="Weird\\Path",
            spread=1,
            digits=5,
            volume_min=0.01,
            volume_max=1.0,
            volume_step=0.01,
            trade_mode="bad-int",
            filling_mode="bad-int",
            visible=True,
        )
    ]

    response = client.get("/broker-symbols", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    symbol = payload["symbols"][0]
    assert symbol["trade_mode"] == 4
    assert symbol["trade_mode_label"] == "Full"
    assert symbol["filling_mode"] == 0
    assert symbol["supported_filling_modes"] == ["RETURN"]


def test_broker_symbols_rejects_when_worker_disconnected(client, auth_headers, monkeypatch):
    from app.routes import broker_symbols as broker_symbols_route

    monkeypatch.setattr(broker_symbols_route, "get_state", lambda: WorkerState.DISCONNECTED)

    response = client.get("/broker-symbols", headers=auth_headers)
    assert response.status_code == 503
    assert "not connected" in response.json()["detail"].lower()


def test_broker_symbols_group_query_and_filling_mode_decoding(
    client,
    auth_headers,
    monkeypatch,
    fake_mt5,
    completed_future_factory,
):
    from app.routes import broker_symbols as broker_symbols_route

    _wire_connected(broker_symbols_route, monkeypatch, completed_future_factory)

    def _symbols_get(group=None):
        assert group == "*USD*"
        return [
            SimpleNamespace(
                name="EURUSD",
                description="EUR/USD",
                path="Forex/Majors",
                spread=1,
                digits=5,
                volume_min=0.01,
                volume_max=1.0,
                volume_step=0.01,
                trade_mode=4,
                filling_mode=1,
                visible=True,
            ),
            SimpleNamespace(
                name="BTCUSD",
                description="BTC/USD",
                path="Crypto",
                spread=2,
                digits=2,
                volume_min=0.01,
                volume_max=1.0,
                volume_step=0.01,
                trade_mode=4,
                filling_mode=2,
                visible=True,
            ),
            SimpleNamespace(
                name="XAUUSD",
                description="Gold",
                path="Metals",
                spread=3,
                digits=2,
                volume_min=0.01,
                volume_max=1.0,
                volume_step=0.01,
                trade_mode=4,
                filling_mode=3,
                visible=True,
            ),
        ]

    fake_mt5.symbols_get = _symbols_get

    response = client.get("/broker-symbols?group=*USD*", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    by_name = {symbol["name"]: symbol for symbol in payload["symbols"]}
    assert by_name["EURUSD"]["supported_filling_modes"] == ["FOK"]
    assert by_name["BTCUSD"]["supported_filling_modes"] == ["IOC"]
    assert by_name["XAUUSD"]["supported_filling_modes"] == ["FOK", "IOC"]
