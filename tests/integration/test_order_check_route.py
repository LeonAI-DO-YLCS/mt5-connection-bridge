import pytest
from types import SimpleNamespace
from unittest.mock import patch

@pytest.fixture
def mock_get_state():
    with patch("app.routes.order_check.get_state") as mock_state:
        from app.mt5_worker import WorkerState
        mock_state.return_value = WorkerState.AUTHORIZED
        yield mock_state

@pytest.fixture(autouse=True)
def mock_symbol_map(monkeypatch):
    from types import SimpleNamespace
    dummy_symbol = SimpleNamespace(mt5_symbol="AAPL", precision=2, trade_mode=0)
    monkeypatch.setattr("app.routes.order_check.symbol_map", {"AAPL": dummy_symbol})
    yield

@pytest.fixture
def mock_mt5_submit():
    with patch("app.routes.order_check.submit") as mock_submit:
        yield mock_submit

def test_order_check_success(client, auth_headers, mock_mt5_submit, mock_get_state, completed_future_factory):
    from app.routes.order_check import OrderCheckResponse
    
    # We mock submit to return what _execute_check returns in order-check
    mock_submit_ret = OrderCheckResponse(
        valid=True,
        margin=10.5,
        profit=5.0,
        equity=1000.0,
        comment="Check OK",
        retcode=0
    )
    mock_mt5_submit.return_value = completed_future_factory(mock_submit_ret)

    response = client.post(
        "/order-check",
        headers=auth_headers,
        json={
            "ticker": "AAPL",
            "type": "buy_limit",
            "volume": 0.01,
            "price": 105.0
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["margin"] == 10.5
    assert data["comment"] == "Check OK"

def test_order_check_invalid_mt5_rejection(client, auth_headers, mock_mt5_submit, mock_get_state, completed_future_factory):
    from app.routes.order_check import OrderCheckResponse
    
    mock_submit_ret = OrderCheckResponse(
        valid=False,
        margin=0.0,
        profit=0.0,
        equity=0.0,
        comment="Invalid volume",
        retcode=10014
    )
    mock_mt5_submit.return_value = completed_future_factory(mock_submit_ret)

    response = client.post(
        "/order-check",
        headers=auth_headers,
        json={
            "ticker": "AAPL",
            "type": "buy_limit",
            "volume": 0.0000001, # Invalid volume
            "price": 105.0
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "Invalid volume" in data["comment"]

def test_order_check_execution_enabled_not_required(client, auth_headers, mock_mt5_submit, mock_get_state, completed_future_factory):
    from app.main import settings
    # Specifically set it to False to prove check works and doesn't bounce it
    settings.execution_enabled = False
    
    from app.routes.order_check import OrderCheckResponse
    mock_submit_ret = OrderCheckResponse(
        valid=True,
        margin=1.0,
        profit=0.0,
        equity=1000.0,
        comment="ok",
        retcode=0,
    )
    mock_mt5_submit.return_value = completed_future_factory(mock_submit_ret)

    response = client.post(
        "/order-check",
        headers=auth_headers,
        json={
            "ticker": "AAPL",
            "type": "buy_limit",
            "volume": 0.01,
            "price": 105.0
        }
    )
    
    assert response.status_code == 200
    assert response.json()["valid"] is True

def test_order_check_unknown_ticker(client, auth_headers):
    response = client.post(
        "/order-check",
        headers=auth_headers,
        json={
            "ticker": "UNKNOWN_TICKER",
            "type": "buy_limit",
            "volume": 0.01,
            "price": 105.0
        }
    )
    assert response.status_code == 404
    assert "Unknown ticker" in response.json()["detail"]


def test_order_check_connection_error(client, auth_headers, mock_mt5_submit, mock_get_state):
    mock_mt5_submit.side_effect = ConnectionError("MT5 disconnected")
    response = client.post(
        "/order-check",
        headers=auth_headers,
        json={
            "ticker": "AAPL",
            "type": "buy_limit",
            "volume": 0.01,
            "price": 105.0
        }
    )
    assert response.status_code == 503


def test_order_check_unexpected_error(client, auth_headers, mock_mt5_submit, mock_get_state):
    mock_mt5_submit.side_effect = RuntimeError("boom")
    response = client.post(
        "/order-check",
        headers=auth_headers,
        json={
            "ticker": "AAPL",
            "type": "buy_limit",
            "volume": 0.01,
            "price": 105.0
        }
    )
    assert response.status_code == 500
