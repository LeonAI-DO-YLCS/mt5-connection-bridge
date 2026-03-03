import pytest
from types import SimpleNamespace
from unittest.mock import patch

@pytest.fixture
def mock_get_state():
    with patch("app.routes.pending_order.get_state") as mock_state:
        from app.mt5_worker import WorkerState
        mock_state.return_value = WorkerState.AUTHORIZED
        yield mock_state

@pytest.fixture(autouse=True)
def mock_symbol_map(monkeypatch):
    from types import SimpleNamespace
    dummy_symbol = SimpleNamespace(mt5_symbol="AAPL", precision=2, trade_mode=0)
    monkeypatch.setattr("app.routes.pending_order.symbol_map", {"AAPL": dummy_symbol})
    yield

@pytest.fixture
def mock_mt5_submit():
    with patch("app.routes.pending_order.submit") as mock_submit:
        yield mock_submit

def test_pending_order_success(client, auth_headers, mock_mt5_submit, mock_get_state, completed_future_factory):
    from app.main import settings
    settings.execution_enabled = True

    mock_response = {
        "success": True,
        "filled_price": 0.0,
        "filled_quantity": 0.01,
        "ticket_id": 98765,
        "error": None
    }
    
    from app.models.trade import TradeResponse
    mock_tuple = (TradeResponse(**mock_response), "fill_confirmed")
    mock_mt5_submit.return_value = completed_future_factory(mock_tuple)

    response = client.post(
        "/pending-order",
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
    assert data["success"] is True
    assert data["ticket_id"] == 98765

def test_pending_order_execution_disabled(client, auth_headers):
    from app.main import settings
    settings.execution_enabled = False

    response = client.post(
        "/pending-order",
        headers=auth_headers,
        json={
            "ticker": "AAPL",
            "type": "buy_limit",
            "volume": 0.01,
            "price": 105.0
        }
    )
    assert response.status_code == 403
    assert "Execution disabled" in response.json()["detail"]

def test_pending_order_unknown_ticker(client, auth_headers):
    from app.main import settings
    settings.execution_enabled = True

    response = client.post(
        "/pending-order",
        headers=auth_headers,
        json={
            "ticker": "UNKNOWN",
            "type": "buy_limit",
            "volume": 0.01,
            "price": 105.0
        }
    )
    assert response.status_code == 404
    assert "Unknown ticker" in response.json()["detail"]
