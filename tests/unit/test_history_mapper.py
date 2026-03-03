import pytest
from types import SimpleNamespace
from datetime import datetime

from app.mappers.history_mapper import map_mt5_deal, map_mt5_historical_order

def test_map_mt5_deal():
    deal = SimpleNamespace(
        ticket=3001,
        order=2001,
        position_id=1001,
        symbol="EURUSD",
        type=0,
        entry=0,
        volume=1.5,
        price=1.1000,
        profit=0.0,
        swap=0.0,
        commission=-3.0,
        fee=0.0,
        time=int(datetime(2023, 10, 1, 12, 0).timestamp()),
        magic=88001
    )
    
    mapped = map_mt5_deal(deal)
    
    assert mapped.ticket == 3001
    assert mapped.order_ticket == 2001
    assert mapped.position_id == 1001
    assert mapped.symbol == "EURUSD"
    assert mapped.type == "buy"
    assert mapped.entry == "in"
    assert mapped.volume == 1.5
    assert mapped.price == 1.1000
    assert mapped.commission == -3.0
    assert mapped.time.endswith("Z")

def test_map_mt5_deal_out():
    deal = SimpleNamespace(
        ticket=3002,
        order=2002,
        position_id=1001,
        symbol="EURUSD",
        type=1,
        entry=1,
        volume=1.5,
        price=1.1050,
        profit=75.0,
        swap=-1.2,
        commission=-3.0,
        fee=0.0,
        time=int(datetime(2023, 10, 2, 12, 0).timestamp()),
        magic=88001
    )
    
    mapped = map_mt5_deal(deal)
    
    assert mapped.type == "sell"
    assert mapped.entry == "out"
    assert mapped.profit == 75.0

def test_map_mt5_historical_order():
    ord = SimpleNamespace(
        ticket=2001,
        symbol="EURUSD",
        type=0,
        volume_initial=1.5,
        price_open=1.1000,
        sl=1.0900,
        tp=1.1200,
        state=4,
        time_setup=int(datetime(2023, 10, 1, 11, 59).timestamp()),
        time_done=int(datetime(2023, 10, 1, 12, 0).timestamp()),
        magic=88001
    )
    
    mapped = map_mt5_historical_order(ord)
    
    assert mapped.ticket == 2001
    assert mapped.type == "buy"
    assert mapped.volume == 1.5
    assert mapped.state == "filled"
    assert mapped.time_setup.endswith("Z")
    assert mapped.time_done.endswith("Z")

def test_map_mt5_historical_order_cancelled():
    ord = SimpleNamespace(
        ticket=2003,
        symbol="GBPUSD",
        type=2, # buy_limit
        volume_initial=2.0,
        price_open=1.3000,
        sl=0.0,
        tp=0.0,
        state=2,
        time_setup=int(datetime(2023, 10, 1, 11, 59).timestamp()),
        time_done=int(datetime(2023, 10, 2, 12, 0).timestamp()),
        magic=88001
    )
    
    mapped = map_mt5_historical_order(ord)
    
    assert mapped.type == "pending"
    assert mapped.state == "cancelled"
    assert mapped.sl is None
    assert mapped.tp is None
