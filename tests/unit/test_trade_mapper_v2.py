import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from app.models.trade import TradeRequest
from app.models.pending_order import PendingOrderRequest
from app.mappers.trade_mapper import (
    build_close_request,
    build_modify_sltp_request,
    build_pending_order_request,
    build_modify_order_request,
    build_cancel_order_request,
    build_order_request,
    _mt5_const
)

def test_build_close_request_full():
    position = SimpleNamespace(
        ticket=1001,
        symbol="EURUSD",
        type=0, # BUY
        volume=1.5
    )
    symbol_info = SimpleNamespace()
    
    # 0 is BUY, so counter is 1 (SELL)
    req = build_close_request(position, None, symbol_info)
    
    assert req["action"] == _mt5_const("TRADE_ACTION_DEAL", 1)
    assert req["type"] == _mt5_const("ORDER_TYPE_SELL", 1)
    assert req["volume"] == 1.5
    assert req["position"] == 1001

def test_build_close_request_partial():
    position = SimpleNamespace(
        ticket=1002,
        symbol="GBPUSD",
        type=1, # SELL
        volume=2.0
    )
    symbol_info = SimpleNamespace()
    
    # 1 is SELL, so counter is 0 (BUY)
    req = build_close_request(position, 1.0, symbol_info)
    
    assert req["type"] == _mt5_const("ORDER_TYPE_BUY", 0)
    assert req["volume"] == 1.0

def test_build_modify_sltp_request():
    req = build_modify_sltp_request(1001, 1.0900, 1.1200)
    assert req["action"] == _mt5_const("TRADE_ACTION_SLTP", 6)
    assert req["position"] == 1001
    assert req["sl"] == 1.0900
    assert req["tp"] == 1.1200

def test_build_modify_sltp_request_none():
    req = build_modify_sltp_request(1001, None, None)
    assert req["sl"] == 0.0
    assert req["tp"] == 0.0

def test_build_pending_order_request():
    pending_req = PendingOrderRequest(
        ticker="EURUSD",
        type="buy_limit",
        volume=1.5,
        price=1.0900,
        sl=1.0800,
        tp=1.1100,
        comment="test pending"
    )
    symbol_info = SimpleNamespace()
    
    req = build_pending_order_request(pending_req, "EURUSD", symbol_info)
    
    assert req["action"] == _mt5_const("TRADE_ACTION_PENDING", 5)
    assert req["type"] == _mt5_const("ORDER_TYPE_BUY_LIMIT", 2)
    assert req["volume"] == 1.5
    assert req["price"] == 1.0900
    assert req["sl"] == 1.0800
    assert req["tp"] == 1.1100
    assert req["magic"] == 88001
    assert req["comment"] == "test pending"
    assert req["type_time"] == _mt5_const("ORDER_TIME_GTC", 0)
    assert req["type_filling"] == _mt5_const("ORDER_FILLING_IOC", 2)

def test_build_modify_order_request():
    req = build_modify_order_request(2001, 1.1000, 1.0900, 1.1200)
    assert req["action"] == _mt5_const("TRADE_ACTION_MODIFY", 7)
    assert req["order"] == 2001
    assert req["price"] == 1.1000
    assert req["sl"] == 1.0900
    assert req["tp"] == 1.1200

def test_build_cancel_order_request():
    req = build_cancel_order_request(2001)
    assert req["action"] == _mt5_const("TRADE_ACTION_REMOVE", 8)
    assert req["order"] == 2001

def test_build_order_request_with_sltp():
    trade_req = TradeRequest(
        ticker="EURUSD",
        action="buy",
        quantity=1.5,
        current_price=1.1000,
        sl=1.0900,
        tp=1.1200
    )
    symbol_info = SimpleNamespace()
    
    req = build_order_request(trade_req, "EURUSD", symbol_info)
    
    assert req["action"] == _mt5_const("TRADE_ACTION_DEAL", 1)
    assert req["price"] == 1.1000
    assert req["sl"] == 1.0900
    assert req["tp"] == 1.1200
