from __future__ import annotations

import sys
from types import SimpleNamespace

from app.mt5_worker import WorkerState


def _wire_connected(monkeypatch, completed_future_factory):
    import app.main  # noqa: F401

    broker_caps_route = sys.modules["app.routes.broker_capabilities"]
    monkeypatch.setattr(broker_caps_route, "get_state", lambda: WorkerState.AUTHORIZED)
    monkeypatch.setattr(
        broker_caps_route,
        "submit",
        lambda fn: completed_future_factory(fn()),
    )
    broker_caps_route.invalidate_capabilities_cache()


def _mock_mt5_capabilities(fake_mt5):
    fake_mt5.symbols_get = lambda: [
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
        )
    ]
    fake_mt5.terminal_info = lambda: SimpleNamespace(trade_allowed=True)
    fake_mt5.account_info = lambda: SimpleNamespace(trade_allowed=True)


def test_capabilities_cache_reuses_snapshot_within_ttl(
    client,
    auth_headers,
    monkeypatch,
    fake_mt5,
    completed_future_factory,
):
    from app.main import settings

    _wire_connected(monkeypatch, completed_future_factory)
    _mock_mt5_capabilities(fake_mt5)
    settings.capabilities_cache_ttl_seconds = 300

    first = client.get("/broker-capabilities", headers=auth_headers)
    second = client.get("/broker-capabilities", headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["fetched_at"] == second.json()["fetched_at"]


def test_capabilities_refresh_endpoint_forces_new_snapshot(
    client,
    auth_headers,
    monkeypatch,
    fake_mt5,
    completed_future_factory,
):
    from app.main import settings

    _wire_connected(monkeypatch, completed_future_factory)
    _mock_mt5_capabilities(fake_mt5)
    settings.capabilities_cache_ttl_seconds = 300

    first = client.get("/broker-capabilities", headers=auth_headers)
    refreshed = client.post("/broker-capabilities/refresh", headers=auth_headers)
    second = client.get("/broker-capabilities", headers=auth_headers)

    assert first.status_code == 200
    assert refreshed.status_code == 200
    assert second.status_code == 200
    assert first.json()["fetched_at"] != second.json()["fetched_at"]


def test_invalidate_capabilities_cache_clears_module_cache(
    monkeypatch,
    fake_mt5,
):
    import app.main  # noqa: F401

    broker_caps_route = sys.modules["app.routes.broker_capabilities"]
    # Build one snapshot directly so module-level cache is populated.
    broker_caps_route.invalidate_capabilities_cache()
    _mock_mt5_capabilities(fake_mt5)
    snapshot = broker_caps_route._get_or_refresh_cache()
    assert snapshot.symbol_count == 1
    assert broker_caps_route._capabilities_cache is not None

    broker_caps_route.invalidate_capabilities_cache()
    assert broker_caps_route._capabilities_cache is None
