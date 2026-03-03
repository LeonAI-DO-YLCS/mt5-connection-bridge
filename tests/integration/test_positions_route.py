import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from datetime import datetime

@pytest.fixture(autouse=True)
def enable_worker():
    from app.main import settings
    settings.disable_mt5_worker = False
    yield
    settings.disable_mt5_worker = True

@pytest.fixture
def mock_mt5_positions_get():
    with patch("app.routes.positions.submit") as mock_submit:
        yield mock_submit

def test_positions_route_empty(client, auth_headers, mock_mt5_positions_get, completed_future_factory):
    mock_mt5_positions_get.return_value = completed_future_factory(None)

    response = client.get("/positions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["positions"] == []
    assert data["count"] == 0

def test_positions_route_success(client, auth_headers, mock_mt5_positions_get, completed_future_factory):
    pos1 = SimpleNamespace(
        ticket=1001, symbol="EURUSD", type=0, volume=1.0,
        price_open=1.1000, price_current=1.1050, sl=0.0, tp=0.0,
        profit=50.0, swap=0.0, time=int(datetime(2023, 10, 1).timestamp()),
        magic=123, comment="test1"
    )
    pos2 = SimpleNamespace(
        ticket=1002, symbol="GBPUSD", type=1, volume=2.0,
        price_open=1.3000, price_current=1.2950, sl=0.0, tp=0.0,
        profit=100.0, swap=0.0, time=int(datetime(2023, 10, 2).timestamp()),
        magic=124, comment="test2"
    )
    mock_mt5_positions_get.return_value = completed_future_factory((pos1, pos2))

    response = client.get("/positions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["positions"]) == 2
    assert data["positions"][0]["ticket"] == 1001
    assert data["positions"][0]["type"] == "buy"
    assert data["positions"][1]["ticket"] == 1002
    assert data["positions"][1]["type"] == "sell"

def test_positions_route_connection_error(client, auth_headers, mock_mt5_positions_get, completed_future_factory):
    mock_mt5_positions_get.side_effect = ConnectionError("MT5 not connected")

    response = client.get("/positions", headers=auth_headers)
    assert response.status_code == 503
    assert response.json() == {"detail": "Not connected to MT5"}
