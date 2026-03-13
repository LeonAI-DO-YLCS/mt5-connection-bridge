import pytest
from types import SimpleNamespace
from unittest.mock import patch

@pytest.fixture(autouse=True)
def enable_worker(monkeypatch):
    from app.main import settings
    monkeypatch.setattr(settings, "disable_mt5_worker", False)
    yield

@pytest.fixture
def mock_mt5_submit():
    with patch("app.routes.orders.submit") as mock_submit:
        yield mock_submit

def test_modify_order_success(client, auth_headers, mock_mt5_submit, completed_future_factory):
    from app.models.trade import TradeResponse
    from app.main import settings
    settings.execution_enabled = True
    mock_mt5_submit.return_value = completed_future_factory((TradeResponse(success=True, ticket_id=12345, error=None), "modified"))

    response = client.put(
        "/orders/12345", 
        headers=auth_headers,
        json={"price": 105.0, "sl": 100.0, "tp": 110.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["ticket_id"] == 12345

def test_modify_order_execution_disabled(client, auth_headers, monkeypatch):
    from app.main import settings
    monkeypatch.setattr(settings, "execution_enabled", False)

    response = client.put(
        "/orders/12345", 
        headers=auth_headers,
        json={"price": 105.0, "sl": 100.0, "tp": 110.0}
    )
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "EXECUTION_DISABLED"
    assert "disabled" in data["message"].lower()

def test_modify_order_connection_error(client, auth_headers, mock_mt5_submit):
    from app.main import settings
    settings.execution_enabled = True
    mock_mt5_submit.side_effect = ConnectionError("MT5 not connected")

    response = client.put(
        "/orders/12345", 
        headers=auth_headers,
        json={"price": 105.0, "sl": 100.0, "tp": 110.0}
    )
    assert response.status_code == 503
    data = response.json()
    assert data["code"] == "MT5_DISCONNECTED"
    assert "Not connected to MT5" in data["message"]
