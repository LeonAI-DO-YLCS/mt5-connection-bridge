import pytest
from unittest.mock import patch
from app.models.account import AccountInfo
from app.models.position import Position
from app.models.order import Order
from app.models.tick import TickPrice
from app.models.terminal import TerminalInfo
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



def test_account_contract(client, auth_headers):
    with patch("app.routes.account.submit") as mock_submit:
        from types import SimpleNamespace
        mock_submit.return_value = make_future(SimpleNamespace(
            login=123,
            server="DemoServer",
            balance=10000.0,
            equity=10000.0,
            margin=1000.0,
            margin_free=9000.0,
            profit=0.0,
            currency="USD",
            leverage=100
        ))
        response = client.get("/account", headers=auth_headers)
        assert response.status_code == 200
        # Validate schema
        AccountInfo.model_validate(response.json())

def test_positions_contract(client, auth_headers):
    with patch("app.routes.positions.submit") as mock_submit:
        from types import SimpleNamespace
        import time
        mock_submit.return_value = make_future([SimpleNamespace(
            ticket=1, time=int(time.time()), type=0, magic=0, identifier=1, reason=0,
            volume=0.1, price_open=100.0, sl=90.0, tp=110.0,
            price_current=105.0, profit=5.0, swap=0.0,
            symbol="V75", comment="test", external_id=""
        )])
        response = client.get("/positions", headers=auth_headers)
        assert response.status_code == 200
        for p in response.json()["positions"]:
            Position.model_validate(p)

def test_orders_contract(client, auth_headers):
    with patch("app.routes.orders.submit") as mock_submit:
        from types import SimpleNamespace
        import time
        mock_submit.return_value = make_future([SimpleNamespace(
            ticket=1, time_setup=int(time.time()), type=2,
            magic=0,
            volume_initial=0.1, price_open=100.0, sl=90.0, tp=110.0,
            symbol="V75"
        )])
        response = client.get("/orders", headers=auth_headers)
        assert response.status_code == 200
        for o in response.json()["orders"]:
            Order.model_validate(o)

def test_tick_contract(client, auth_headers, monkeypatch):
    from types import SimpleNamespace
    dummy_symbol = SimpleNamespace(mt5_symbol="V75", precision=2, trade_mode=0)
    monkeypatch.setattr("app.routes.tick.symbol_map", {"V75": dummy_symbol})
    with patch("app.routes.tick.submit") as mock_submit:
        import time
        mock_submit.return_value = make_future(SimpleNamespace(
            bid=1.0, ask=1.1, time=int(time.time())
        ))
        response = client.get("/tick/V75", headers=auth_headers)
        assert response.status_code == 200
        TickPrice.model_validate(response.json())

def test_terminal_contract(client, auth_headers):
    with patch("app.routes.terminal.submit") as mock_submit:
        from types import SimpleNamespace
        mock_submit.return_value = make_future(SimpleNamespace(
            community_account=True, community_connection=True, connected=True,
            trade_allowed=True, tradeapi_disabled=False,
            build=4000, maxbars=100000, codepage=0, name="MT5", path="", data_path="", commondata_path=""
        ))
        response = client.get("/terminal", headers=auth_headers)
        assert response.status_code == 200
        TerminalInfo.model_validate(response.json())
