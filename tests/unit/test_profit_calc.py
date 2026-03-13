import pytest
from unittest.mock import patch, MagicMock
from concurrent.futures import Future

from app.mt5_worker import WorkerState

def mock_submit(f):
    fut = Future()
    try:
        fut.set_result(f())
    except Exception as e:
        fut.set_exception(e)
    return fut

def test_profit_calc_success(client, fake_mt5, auth_headers):
    fake_mt5.order_calc_profit = MagicMock(return_value=50.0)

    with patch("app.routes.profit_calc.get_state", return_value=WorkerState.AUTHORIZED), \
         patch("app.routes.profit_calc.submit", side_effect=mock_submit):
         
        payload = {"symbol": "EURUSD", "volume": 1.0, "action": "buy", "price_open": 1.1000, "price_close": 1.1050}
        response = client.post("/profit-calc", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["profit"] == 50.0
        assert data["symbol"] == "EURUSD"
        assert data["volume"] == 1.0
        assert data["price_open"] == 1.1000
        assert data["price_close"] == 1.1050

        fake_mt5.order_calc_profit.assert_called_once_with(fake_mt5.ORDER_TYPE_BUY, "EURUSD", 1.0, 1.1000, 1.1050)

def test_profit_calc_unauthorized(client, fake_mt5, auth_headers):
    with patch("app.routes.profit_calc.get_state", return_value=WorkerState.DISCONNECTED):
         
        payload = {"symbol": "EURUSD", "volume": 1.0, "action": "buy", "price_open": 1.1000, "price_close": 1.1050}
        response = client.post("/profit-calc", json=payload, headers=auth_headers)
        
        assert response.status_code == 503
        data = response.json()
        assert data["code"] == "MT5_DISCONNECTED"
        assert "MT5 terminal not authorized" in data["message"]

def test_profit_calc_failure(client, fake_mt5, auth_headers):
    fake_mt5.order_calc_profit = MagicMock(return_value=None)

    with patch("app.routes.profit_calc.get_state", return_value=WorkerState.AUTHORIZED), \
         patch("app.routes.profit_calc.submit", side_effect=mock_submit):
         
        payload = {"symbol": "EURUSD", "volume": 1.0, "action": "buy", "price_open": 1.1000, "price_close": 1.1050}
        response = client.post("/profit-calc", json=payload, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert data["code"] == "VALIDATION_ERROR"
        assert "Profit calculation failed" in data["message"]
