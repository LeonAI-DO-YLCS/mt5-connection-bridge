import pytest
from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime

@pytest.fixture(autouse=True)
def enable_worker():
    from app.main import settings
    settings.disable_mt5_worker = False
    yield
    settings.disable_mt5_worker = True

@pytest.fixture
def mock_mt5_symbol_info_tick():
    with patch("app.routes.tick.submit") as mock_submit:
        yield mock_submit

@pytest.fixture
def mock_symbol_map():
    with patch("app.routes.tick.symbol_map", {"TEST": SimpleNamespace(mt5_symbol="TEST_MT5")}) as mock_map:
        yield mock_map

def test_tick_route_success(client, auth_headers, mock_mt5_symbol_info_tick, mock_symbol_map, completed_future_factory):
    tick = SimpleNamespace(
        bid=1.1000, ask=1.1005,
        time=int(datetime(2023, 10, 1).timestamp())
    )
    mock_mt5_symbol_info_tick.return_value = completed_future_factory(tick)

    response = client.get("/tick/TEST", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "TEST"
    assert data["bid"] == 1.1000
    assert data["ask"] == 1.1005
    assert data["spread"] == pytest.approx(0.0005)

def test_tick_route_unknown_ticker(client, auth_headers, mock_symbol_map, mock_mt5_symbol_info_tick, completed_future_factory):
    mock_mt5_symbol_info_tick.return_value = completed_future_factory(None)
    response = client.get("/tick/UNKNOWN", headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_tick_route_connection_error(client, auth_headers, mock_mt5_symbol_info_tick, mock_symbol_map, completed_future_factory):
    mock_mt5_symbol_info_tick.side_effect = ConnectionError("MT5 not connected")

    response = client.get("/tick/TEST", headers=auth_headers)
    assert response.status_code == 503
    assert response.json() == {"detail": "Not connected to MT5"}


def test_tick_route_worker_disabled(client, auth_headers, mock_symbol_map):
    from app.main import settings

    settings.disable_mt5_worker = True
    response = client.get("/tick/TEST", headers=auth_headers)
    assert response.status_code == 503
    assert "worker disabled" in response.json()["detail"].lower()
    settings.disable_mt5_worker = False


def test_tick_route_selects_hidden_symbol_and_handles_missing_tick_time(
    client,
    auth_headers,
    monkeypatch,
    fake_mt5,
    completed_future_factory,
):
    from app.routes import tick as tick_route

    calls = {"selected": 0}
    fake_mt5._symbol_info = SimpleNamespace(visible=False)
    fake_mt5._tick = SimpleNamespace(bid=1.10, ask=1.11)  # no "time" attribute

    def _symbol_select(_symbol, _visible):
        calls["selected"] += 1
        return True

    fake_mt5.symbol_select = _symbol_select
    monkeypatch.setattr(tick_route, "submit", lambda fn: completed_future_factory(fn()))

    response = client.get("/tick/UNKNOWN_DIRECT", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "UNKNOWN_DIRECT"
    assert calls["selected"] == 1
    assert isinstance(payload["time"], str)


def test_tick_route_handles_submit_runtime_error(client, auth_headers, mock_symbol_map, mock_mt5_symbol_info_tick):
    mock_mt5_symbol_info_tick.side_effect = RuntimeError("unexpected")
    response = client.get("/tick/TEST", headers=auth_headers)
    assert response.status_code == 500
    assert "unexpected" in response.json()["detail"].lower()
