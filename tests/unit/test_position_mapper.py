import pytest
from types import SimpleNamespace
from datetime import datetime

from app.mappers.position_mapper import map_mt5_position

def test_map_mt5_position_buy():
    # Simulate a buy position
    pos = SimpleNamespace(
        ticket=1001,
        symbol="EURUSD",
        type=0,
        volume=1.5,
        price_open=1.1000,
        price_current=1.1050,
        sl=1.0900,
        tp=1.1200,
        profit=50.0,
        swap=-1.2,
        time=int(datetime(2023, 10, 1, 12, 0).timestamp()),
        magic=88001,
        comment="test buy"
    )
    
    mapped = map_mt5_position(pos)
    
    assert mapped.ticket == 1001
    assert mapped.symbol == "EURUSD"
    assert mapped.type == "buy"
    assert mapped.volume == 1.5
    assert mapped.price_open == 1.1000
    assert mapped.sl == 1.0900
    assert mapped.tp == 1.1200
    assert mapped.profit == 50.0
    assert mapped.swap == -1.2
    assert mapped.magic == 88001
    assert mapped.comment == "test buy"
    assert mapped.time.endswith("Z")

def test_map_mt5_position_sell_no_sltp():
    # Simulate a sell position with no stop loss or take profit
    pos = SimpleNamespace(
        ticket=1002,
        symbol="GBPUSD",
        type=1,
        volume=2.0,
        price_open=1.3000,
        price_current=1.2950,
        sl=0.0,  # MT5 returns 0.0 when no SL is set
        tp=0.0,
        profit=100.0,
        swap=0.5,
        time=int(datetime(2023, 10, 2, 12, 0).timestamp()),
        magic=88001,
        comment="test sell"
    )
    
    mapped = map_mt5_position(pos)
    
    assert mapped.type == "sell"
    assert mapped.sl is None
    assert mapped.tp is None
