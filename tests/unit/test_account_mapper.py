import pytest
from types import SimpleNamespace

from app.mappers.account_mapper import map_mt5_account

def test_map_mt5_account():
    acc = SimpleNamespace(
        login=1234567,
        server="MetaQuotes-Demo",
        balance=10000.50,
        equity=10500.25,
        margin=500.0,
        margin_free=10000.25,
        profit=499.75,
        currency="USD",
        leverage=100
    )
    
    mapped = map_mt5_account(acc)
    
    assert mapped.login == 1234567
    assert mapped.server == "MetaQuotes-Demo"
    assert mapped.balance == 10000.50
    assert mapped.equity == 10500.25
    assert mapped.margin == 500.0
    assert mapped.free_margin == 10000.25
    assert mapped.profit == 499.75
    assert mapped.currency == "USD"
    assert mapped.leverage == 100
    assert isinstance(mapped.leverage, int)
    assert isinstance(mapped.currency, str)
