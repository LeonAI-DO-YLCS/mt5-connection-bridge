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

def test_margin_check_success(client, fake_mt5, auth_headers):
    fake_mt5.order_calc_margin = MagicMock(return_value=123.45)
    
    acc_mock = MagicMock()
    acc_mock.margin_free = 1000.0
    fake_mt5.account_info = MagicMock(return_value=acc_mock)
    
    with patch("app.routes.margin_check.get_state", return_value=WorkerState.AUTHORIZED), \
         patch("app.routes.margin_check.submit", side_effect=mock_submit):
         
        payload = {"symbol": "EURUSD", "volume": 1.0, "action": "buy"}
        response = client.post("/margin-check", json=payload, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["margin"] == 123.45
        assert data["free_margin"] == 1000.0
        assert data["margin_rate"] == 1.0
        assert data["symbol"] == "EURUSD"
        assert data["volume"] == 1.0

        fake_mt5.order_calc_margin.assert_called_once_with(fake_mt5.ORDER_TYPE_BUY, "EURUSD", 1.0, 100.1)

def test_margin_check_unauthorized(client, fake_mt5, auth_headers):
    with patch("app.routes.margin_check.get_state", return_value=WorkerState.DISCONNECTED):
         
        payload = {"symbol": "EURUSD", "volume": 1.0, "action": "buy"}
        response = client.post("/margin-check", json=payload, headers=auth_headers)
        
        assert response.status_code == 503
        data = response.json()
        assert data["code"] == "MT5_DISCONNECTED"
        assert "MT5 terminal not authorized" in data["message"]

def test_margin_check_calculation_failure(client, fake_mt5, auth_headers):
    fake_mt5.order_calc_margin = MagicMock(return_value=None)

    with patch("app.routes.margin_check.get_state", return_value=WorkerState.AUTHORIZED), \
         patch("app.routes.margin_check.submit", side_effect=mock_submit):
         
        payload = {"symbol": "EURUSD", "volume": 1.0, "action": "buy"}
        response = client.post("/margin-check", json=payload, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert data["code"] == "VALIDATION_ERROR"
        assert "Margin calculation failed" in data["message"]
