from __future__ import annotations

import sys
from types import SimpleNamespace

from app.mt5_worker import WorkerState


def _fake_symbols():
    return [
        SimpleNamespace(
            name="EURUSD",
            description="Euro vs US Dollar",
            path="Forex\\Majors\\EURUSD",
            trade_mode=4,
            filling_mode=3,
            spread=10,
            digits=5,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            visible=True,
        ),
        SimpleNamespace(
            name="BTCUSD",
            description="Bitcoin",
            path="Crypto",
            trade_mode=2,
            filling_mode=0,
            spread=20,
            digits=2,
            volume_min=0.01,
            volume_max=10.0,
            volume_step=0.01,
            visible=True,
        ),
    ]


def _wire_capabilities_route(monkeypatch, completed_future_factory):
    import app.main  # noqa: F401

    broker_caps_route = sys.modules["app.routes.broker_capabilities"]
    monkeypatch.setattr(broker_caps_route, "get_state", lambda: WorkerState.AUTHORIZED)
    monkeypatch.setattr(
        broker_caps_route,
        "submit",
        lambda fn: completed_future_factory(fn()),
    )
    broker_caps_route.invalidate_capabilities_cache()


def test_broker_capabilities_get_and_refresh_contract(
    client,
    auth_headers,
    monkeypatch,
    fake_mt5,
    completed_future_factory,
):
    import app.main  # noqa: F401

    _wire_capabilities_route(monkeypatch, completed_future_factory)

    fake_mt5.symbols_get = lambda: _fake_symbols()
    fake_mt5.terminal_info = lambda: SimpleNamespace(trade_allowed=True)
    fake_mt5.account_info = lambda: SimpleNamespace(trade_allowed=True)

    get_response = client.get("/broker-capabilities", headers=auth_headers)
    assert get_response.status_code == 200
    payload = get_response.json()
    assert payload["symbol_count"] == 2
    assert "fetched_at" in payload
    assert "categories" in payload
    assert "symbols" in payload
    assert payload["categories"]["Forex"] == ["Majors"]
    assert payload["symbols"][0]["name"] in {"EURUSD", "BTCUSD"}

    refresh_response = client.post("/broker-capabilities/refresh", headers=auth_headers)
    assert refresh_response.status_code == 200
    refresh_payload = refresh_response.json()
    assert refresh_payload["message"] == "Capabilities cache refreshed"
    assert refresh_payload["symbol_count"] == 2
    assert "fetched_at" in refresh_payload


def test_broker_capabilities_refetches_when_cache_is_stale(
    client,
    auth_headers,
    monkeypatch,
    fake_mt5,
    completed_future_factory,
):
    import app.main  # noqa: F401

    from app.main import settings

    _wire_capabilities_route(monkeypatch, completed_future_factory)
    settings.capabilities_cache_ttl_seconds = 0

    calls = {"count": 0}

    def _symbols_get():
        calls["count"] += 1
        return _fake_symbols()

    fake_mt5.symbols_get = _symbols_get
    fake_mt5.terminal_info = lambda: SimpleNamespace(trade_allowed=True)
    fake_mt5.account_info = lambda: SimpleNamespace(trade_allowed=True)

    first = client.get("/broker-capabilities", headers=auth_headers)
    second = client.get("/broker-capabilities", headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert calls["count"] >= 2


def test_broker_capabilities_returns_503_when_worker_disconnected(
    client,
    auth_headers,
    monkeypatch,
):
    import app.main  # noqa: F401

    broker_caps_route = sys.modules["app.routes.broker_capabilities"]
    monkeypatch.setattr(broker_caps_route, "get_state", lambda: WorkerState.DISCONNECTED)

    response = client.get("/broker-capabilities", headers=auth_headers)
    assert response.status_code == 503
