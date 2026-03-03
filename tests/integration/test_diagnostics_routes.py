from __future__ import annotations

from types import SimpleNamespace

from app.mt5_worker import WorkerState


def test_runtime_diagnostics_endpoint(client, auth_headers):
    response = client.get("/diagnostics/runtime", headers=auth_headers)
    payload = response.json()

    assert response.status_code == 200
    assert payload["app_version"]
    assert isinstance(payload["uptime_seconds"], (int, float))
    assert payload["symbol_count"] >= 0
    assert payload["config_fingerprint"]
    assert payload["runtime_state_path"]
    assert payload["worker_state"] in {state.value for state in WorkerState}


def test_symbol_diagnostics_disconnected(client, auth_headers, monkeypatch):
    from app.routes import diagnostics as diagnostics_route

    monkeypatch.setattr(diagnostics_route, "symbol_map", {"AAPL": SimpleNamespace(mt5_symbol="AAPL")})
    monkeypatch.setattr(diagnostics_route, "get_state", lambda: WorkerState.DISCONNECTED)

    response = client.get("/diagnostics/symbols", headers=auth_headers)
    payload = response.json()

    assert response.status_code == 200
    assert payload["worker_state"] == WorkerState.DISCONNECTED.value
    assert payload["checked_count"] == 1
    assert payload["items"][0]["reason_code"] == "MT5_DISCONNECTED"


def test_symbol_diagnostics_connected(client, auth_headers, monkeypatch, fake_mt5, completed_future_factory):
    from app.routes import diagnostics as diagnostics_route

    monkeypatch.setattr(
        diagnostics_route,
        "symbol_map",
        {
            "AAPL": SimpleNamespace(mt5_symbol="AAPL"),
            "BAD": SimpleNamespace(mt5_symbol="NOPE"),
        },
    )
    monkeypatch.setattr(diagnostics_route, "get_state", lambda: WorkerState.AUTHORIZED)
    monkeypatch.setattr(diagnostics_route, "submit", lambda fn: completed_future_factory(fn()))

    fake_mt5.symbols_get = lambda *args, **kwargs: [SimpleNamespace(name="AAPL"), SimpleNamespace(name="AAPLm")]
    fake_mt5.symbol_info = lambda symbol: SimpleNamespace(visible=True) if symbol == "AAPL" else None

    response = client.get("/diagnostics/symbols", headers=auth_headers)
    payload = response.json()

    assert response.status_code == 200
    items = {item["ticker"]: item for item in payload["items"]}
    assert items["AAPL"]["reason_code"] == "OK"
    assert items["BAD"]["reason_code"] in {"SYMBOL_ALIAS_CANDIDATES", "SYMBOL_NOT_IN_BROKER"}

