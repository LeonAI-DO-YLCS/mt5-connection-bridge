import pytest
from unittest.mock import patch
from app.models.trade import TradeResponse
import asyncio

def make_future(val):
    fut = asyncio.Future()
    fut.set_result(val)
    return fut

@pytest.fixture(autouse=True)
def enable_worker():
    from app.main import settings
    settings.disable_mt5_worker = False
    yield
    settings.disable_mt5_worker = True

@pytest.fixture
def mock_execution_enabled(monkeypatch):
    monkeypatch.setattr("app.main.settings.execution_enabled", True)

def test_close_position_contract(client, auth_headers, mock_execution_enabled):
    with patch("app.routes.close_position.submit") as mock_submit:
        mock_submit.return_value = make_future((TradeResponse(
            success=True,
            filled_price=1.05,
            filled_quantity=0.1,
            ticket_id=101,
            error=None,
        ), "close"))
        response = client.post("/close-position", headers=auth_headers, json={"ticket": 1, "volume": 0.1})
        assert response.status_code == 200
        TradeResponse.model_validate(response.json())

def test_delete_order_contract(client, auth_headers, mock_execution_enabled):
    with patch("app.routes.orders.submit") as mock_submit:
        mock_submit.return_value = make_future((TradeResponse(success=True, ticket_id=201, error=None), "cancelled"))
        response = client.delete("/orders/201", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True

def test_put_order_contract(client, auth_headers, mock_execution_enabled):
    with patch("app.routes.orders.submit") as mock_submit:
        mock_submit.return_value = make_future((TradeResponse(success=True, ticket_id=201, error=None), "modified"))
        response = client.put("/orders/201", headers=auth_headers, json={"price": 105.0, "sl": 90.0, "tp": 120.0})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


def test_put_position_sltp_contract(client, auth_headers, mock_execution_enabled):
    with patch("app.routes.positions.submit") as mock_submit:
        mock_submit.return_value = make_future((TradeResponse(success=True, ticket_id=1, error=None), "modified"))
        response = client.put("/positions/1/sltp", headers=auth_headers, json={"sl": 90.0, "tp": 110.0})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
