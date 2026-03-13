import pytest
from types import SimpleNamespace
from unittest.mock import patch

@pytest.fixture
def mock_get_state():
    with patch("app.routes.history.get_state") as mock_state:
        from app.mt5_worker import WorkerState
        mock_state.return_value = WorkerState.AUTHORIZED
        yield mock_state

@pytest.fixture
def mock_mt5_submit():
    with patch("app.routes.history.submit") as mock_submit:
        yield mock_submit

def test_history_orders_success(client, auth_headers, mock_mt5_submit, mock_get_state, completed_future_factory):
    from app.routes.history import OrdersResponse
    from app.models.historical_order import HistoricalOrder
    
    mock_order = HistoricalOrder(
        ticket=2001,
        symbol="EURUSD",
        type="buy",
        volume=0.1,
        price=1.1000,
        sl=None,
        tp=None,
        state="filled",
        time_setup="2026-03-01T12:00:00Z",
        time_done="2026-03-01T12:00:01Z",
        magic=123
    )
    
    # Same as deals, just dict for OrdersResponse
    mock_submit_ret = OrdersResponse(
        orders=[mock_order],
        count=1
    )
    mock_mt5_submit.return_value = completed_future_factory(mock_submit_ret)

    response = client.get(
        "/history/orders?date_from=2026-02-01T00:00:00Z&date_to=2026-03-01T00:00:00Z",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["orders"][0]["state"] == "filled"

def test_history_orders_empty(client, auth_headers, mock_mt5_submit, mock_get_state, completed_future_factory):
    from app.routes.history import OrdersResponse
    
    mock_submit_ret = OrdersResponse(
        orders=[],
        count=0
    )
    mock_mt5_submit.return_value = completed_future_factory(mock_submit_ret)

    response = client.get(
        "/history/orders?date_from=2026-02-01T00:00:00Z&date_to=2026-03-01T00:00:00Z",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert len(data["orders"]) == 0

def test_history_orders_connection_error(client, auth_headers, mock_mt5_submit, mock_get_state):
    mock_mt5_submit.side_effect = ConnectionError("MT5 disconnected")
    
    response = client.get(
        "/history/orders?date_from=2026-02-01T00:00:00Z&date_to=2026-03-01T00:00:00Z",
        headers=auth_headers
    )
    assert response.status_code == 503
    data = response.json()
    assert data["code"] == "MT5_DISCONNECTED"
    assert "disconnected" in data["message"].lower() or "Not connected" in data["message"]
