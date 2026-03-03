import pytest
from types import SimpleNamespace
from datetime import datetime

from app.mappers.order_mapper import map_mt5_order, pending_type_to_mt5_const
from app.mappers.trade_mapper import _mt5_const

def test_map_mt5_order_buy_limit():
    ord = SimpleNamespace(
        ticket=2001,
        symbol="USDJPY",
        type=_mt5_const("ORDER_TYPE_BUY_LIMIT", 2),
        volume_initial=0.5,
        price_open=149.00,
        sl=148.00,
        tp=151.00,
        time_setup=int(datetime(2023, 10, 1, 10, 0).timestamp()),
        magic=88002
    )
    
    mapped = map_mt5_order(ord)
    
    assert mapped.ticket == 2001
    assert mapped.symbol == "USDJPY"
    assert mapped.type == "buy_limit"
    assert mapped.volume == 0.5
    assert mapped.price == 149.00
    assert mapped.sl == 148.00
    assert mapped.tp == 151.00
    assert mapped.magic == 88002
    assert mapped.time_setup.endswith("Z")

def test_map_mt5_order_sell_stop_no_sltp():
    ord = SimpleNamespace(
        ticket=2002,
        symbol="AUDUSD",
        type=_mt5_const("ORDER_TYPE_SELL_STOP", 5),
        volume_initial=1.0,
        price_open=0.6500,
        sl=0.0,
        tp=0.0,
        time_setup=int(datetime(2023, 10, 1, 11, 0).timestamp()),
        magic=0
    )
    
    mapped = map_mt5_order(ord)
    
    assert mapped.type == "sell_stop"
    assert mapped.volume == 1.0
    assert mapped.sl is None
    assert mapped.tp is None

def test_pending_type_to_mt5_const():
    assert pending_type_to_mt5_const("buy_limit") == _mt5_const("ORDER_TYPE_BUY_LIMIT", 2)
    assert pending_type_to_mt5_const("sell_limit") == _mt5_const("ORDER_TYPE_SELL_LIMIT", 3)
    assert pending_type_to_mt5_const("buy_stop") == _mt5_const("ORDER_TYPE_BUY_STOP", 4)
    assert pending_type_to_mt5_const("sell_stop") == _mt5_const("ORDER_TYPE_SELL_STOP", 5)
