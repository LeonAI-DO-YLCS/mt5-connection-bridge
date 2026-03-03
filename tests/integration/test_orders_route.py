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
def mock_mt5_orders_get():
    with patch("app.routes.orders.submit") as mock_submit:
        yield mock_submit

def test_orders_route_empty(client, auth_headers, mock_mt5_orders_get, completed_future_factory):
    mock_mt5_orders_get.return_value = completed_future_factory(None)

    response = client.get("/orders", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["orders"] == []
    assert data["count"] == 0

def test_orders_route_success(client, auth_headers, mock_mt5_orders_get, completed_future_factory):
    # type 2 is ORDER_TYPE_BUY_LIMIT
    ord1 = SimpleNamespace(
        ticket=2001, symbol="EURUSD", type=2, volume_initial=1.0,
        price_open=1.1000, sl=0.0, tp=0.0,
        time_setup=int(datetime(2023, 10, 1).timestamp()), magic=123
    )
    mock_mt5_orders_get.return_value = completed_future_factory((ord1,))

    response = client.get("/orders", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert len(data["orders"]) == 1
    assert data["orders"][0]["ticket"] == 2001
    assert data["orders"][0]["type"] == "buy_limit"

def test_orders_route_connection_error(client, auth_headers, mock_mt5_orders_get, completed_future_factory):
    mock_mt5_orders_get.side_effect = ConnectionError("MT5 not connected")

    response = client.get("/orders", headers=auth_headers)
    assert response.status_code == 503
    assert response.json() == {"detail": "Not connected to MT5"}
