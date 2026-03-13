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

def test_raw_margin_check(client, fake_mt5, auth_headers):
    fake_mt5.order_calc_margin = MagicMock(return_value=123.45)
    
    with patch("app.routes.raw_namespace.get_state", return_value=WorkerState.AUTHORIZED), \
         patch("app.routes.raw_namespace.submit", side_effect=mock_submit):
         
        response = client.get("/mt5/raw/margin-check?symbol=EURUSD&volume=1.0&action=buy", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["namespace"] == "advanced"
        assert data["safety_disclaimer"] == "RAW_NAMESPACE_UNVALIDATED"
        assert data["data"]["margin"] == 123.45

def test_raw_profit_calc(client, fake_mt5, auth_headers):
    fake_mt5.order_calc_profit = MagicMock(return_value=50.0)
    
    with patch("app.routes.raw_namespace.get_state", return_value=WorkerState.AUTHORIZED), \
         patch("app.routes.raw_namespace.submit", side_effect=mock_submit):
         
        response = client.get("/mt5/raw/profit-calc?symbol=EURUSD&volume=1.0&action=buy&price_open=1.1&price_close=1.2", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["profit"] == 50.0

def test_raw_market_book(client, fake_mt5, auth_headers):
    fake_mt5.market_book_add = MagicMock(return_value=True)
    fake_mt5.market_book_get = MagicMock(return_value=[
        MagicMock(type=1, price=1.1001, volume=10.0, volume_double=10.0),
        MagicMock(type=2, price=1.1002, volume=5.0, volume_double=5.0)
    ])
    fake_mt5.market_book_release = MagicMock(return_value=True)
    
    with patch("app.routes.raw_namespace.get_state", return_value=WorkerState.AUTHORIZED), \
         patch("app.routes.raw_namespace.submit", side_effect=mock_submit):
         
        response = client.get("/mt5/raw/market-book?symbol=EURUSD", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["namespace"] == "advanced"
        entries = data["data"]["entries"]
        assert len(entries) == 2
        assert entries[0]["type"] == "buy"
        assert entries[0]["price"] == 1.1001
        assert entries[1]["type"] == "sell"

def test_raw_terminal_info(client, fake_mt5, auth_headers):
    fake_mt5.terminal_info = MagicMock(return_value=MagicMock(_asdict=lambda: {"connected": True}))
    
    with patch("app.routes.raw_namespace.get_state", return_value=WorkerState.AUTHORIZED), \
         patch("app.routes.raw_namespace.submit", side_effect=mock_submit):
         
        response = client.get("/mt5/raw/terminal-info", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["connected"] is True

def test_raw_account_info(client, fake_mt5, auth_headers):
    fake_mt5.account_info = MagicMock(return_value=MagicMock(_asdict=lambda: {"balance": 1000.0}))
    
    with patch("app.routes.raw_namespace.get_state", return_value=WorkerState.AUTHORIZED), \
         patch("app.routes.raw_namespace.submit", side_effect=mock_submit):
         
        response = client.get("/mt5/raw/account-info", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["balance"] == 1000.0

def test_raw_last_error(client, fake_mt5, auth_headers):
    fake_mt5.last_error = MagicMock(return_value=(1, "Success"))
    
    with patch("app.routes.raw_namespace.get_state", return_value=WorkerState.AUTHORIZED), \
         patch("app.routes.raw_namespace.submit", side_effect=mock_submit):
         
        response = client.get("/mt5/raw/last-error", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["code"] == 1
        assert data["data"]["message"] == "Success"
