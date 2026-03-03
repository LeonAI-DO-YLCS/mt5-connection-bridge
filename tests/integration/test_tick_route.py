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

def test_tick_route_unknown_ticker(client, auth_headers, mock_symbol_map):
    response = client.get("/tick/UNKNOWN", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Ticker not found in mapped symbols"}

def test_tick_route_connection_error(client, auth_headers, mock_mt5_symbol_info_tick, mock_symbol_map, completed_future_factory):
    mock_mt5_symbol_info_tick.side_effect = ConnectionError("MT5 not connected")

    response = client.get("/tick/TEST", headers=auth_headers)
    assert response.status_code == 503
    assert response.json() == {"detail": "Not connected to MT5"}
