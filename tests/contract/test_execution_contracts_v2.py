import pytest
from unittest.mock import patch
from app.models.trade import TradeResponse
from app.models.order_check import OrderCheckResponse
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

@pytest.fixture(autouse=True)
def mock_symbol_map(monkeypatch):
    from types import SimpleNamespace
    dummy_symbol = SimpleNamespace(mt5_symbol="V75", precision=2, trade_mode=0)
    monkeypatch.setattr("app.routes.pending_order.symbol_map", {"V75": dummy_symbol})
    monkeypatch.setattr("app.routes.order_check.symbol_map", {"V75": dummy_symbol})

def test_pending_order_contract(client, auth_headers, mock_execution_enabled):
    with patch("app.routes.pending_order.submit") as mock_submit:
        mock_submit.return_value = make_future((TradeResponse(
            success=True,
            filled_price=100.0,
            filled_quantity=0.1,
            ticket_id=301,
            error=None,
        ), None))
        response = client.post("/pending-order", headers=auth_headers, json={
            "ticker": "V75",
            "type": "buy_limit",
            "volume": 0.1,
            "price": 100.0
        })
        assert response.status_code == 200
        TradeResponse.model_validate(response.json())

def test_order_check_contract(client, auth_headers):
    with patch("app.routes.order_check.submit") as mock_submit:
        mock_submit.return_value = make_future(OrderCheckResponse(
            valid=True,
            margin=15.0,
            profit=0.0,
            equity=100.0,
            comment="valid parameters",
            retcode=0
        ))
        response = client.post("/order-check", headers=auth_headers, json={
            "ticker": "V75",
            "type": "buy_limit",
            "volume": 0.1,
            "price": 100.0
        })
        assert response.status_code == 200
        OrderCheckResponse.model_validate(response.json())
