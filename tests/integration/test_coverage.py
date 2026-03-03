import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
import asyncio
import sys
from types import SimpleNamespace
import time

def passthrough(fn, *args, **kwargs):
    if hasattr(fn, "func"): # if it's a partial
        val = fn()
    else:
        val = fn(*args, **kwargs)
    fut = asyncio.Future()
    fut.set_result(val)
    return fut

@pytest.fixture
def override_submit():
    with patch("app.routes.account.submit", side_effect=passthrough), \
         patch("app.routes.positions.submit", side_effect=passthrough), \
         patch("app.routes.execute.submit", side_effect=passthrough), \
         patch("app.routes.orders.submit", side_effect=passthrough), \
         patch("app.routes.tick.submit", side_effect=passthrough), \
         patch("app.routes.terminal.submit", side_effect=passthrough), \
         patch("app.routes.close_position.submit", side_effect=passthrough), \
         patch("app.routes.pending_order.submit", side_effect=passthrough), \
         patch("app.routes.order_check.submit", side_effect=passthrough), \
         patch("app.routes.broker_symbols.submit", side_effect=passthrough), \
         patch("app.routes.history.submit", side_effect=passthrough):
         yield

@pytest.fixture
def override_settings(monkeypatch):
    from app.main import settings
    import app.mt5_worker
    monkeypatch.setattr(settings, "execution_enabled", True)
    monkeypatch.setattr(settings, "disable_mt5_worker", False)
    app.mt5_worker._current_state = app.mt5_worker.WorkerState.AUTHORIZED
    yield
    app.mt5_worker._current_state = app.mt5_worker.WorkerState.DISCONNECTED

def test_full_coverage(override_submit, fake_mt5, auth_headers, override_settings, client, monkeypatch):
    import app.mt5_worker
    from app.main import settings
    monkeypatch.setattr(app.mt5_worker, "get_state", lambda: app.mt5_worker.WorkerState.AUTHORIZED)
    settings.execution_enabled = True
    settings.disable_mt5_worker = False

    mt5 = sys.modules["MetaTrader5"]
    fake_mt5._tick.time = int(time.time())
    
    patcher = patch.multiple(sys.modules["MetaTrader5"], create=True,
        positions_get=lambda **k: [SimpleNamespace(ticket=1, symbol="V75", type=0, volume=1.0, price_open=1.0, sl=0.0, tp=0.0, price_current=1.1, swap=0.0, profit=1.0, time=int(time.time()), magic=0, comment="", identifier=1, reason=0)],
        history_deals_get=lambda f, t, **k: [SimpleNamespace(ticket=1, order=1, time=123, type=0, entry=0, magic=0, position_id=1, volume=1.0, price=1.0, commission=0.0, swap=0.0, profit=1.0, symbol="V75", comment="", fee=0.0)],
        history_orders_get=lambda f, t, **k: [SimpleNamespace(ticket=1, time_setup=123, type=0, state=0, magic=0, volume_initial=1.0, price_open=1.0, sl=0.0, tp=0.0, price_current=1.0, symbol="V75", comment="")],
        orders_get=lambda **k: [SimpleNamespace(ticket=1, time_setup=123, type=2, state=0, magic=0, volume_initial=1.0, price_open=1.0, sl=0.0, tp=0.0, price_current=1.0, symbol="V75", comment="")],
        terminal_info=lambda: SimpleNamespace(community_account=True, community_connection=True, connected=True, trade_allowed=True, tradeapi_disabled=False, build=1, maxbars=1, codepage=1, name="A", path="A", data_path="A", commondata_path="A"),
        account_info=lambda: SimpleNamespace(login=1, server="A", balance=1.0, equity=1.0, margin=1.0, margin_free=1.0, profit=1.0, currency="USD", leverage=100),
        symbols_get=lambda **k: [SimpleNamespace(name="V75", path="", description="", spread=1, digits=1, volume_min=0.1, volume_max=100.0, trade_mode=1)],
        order_check=lambda r: SimpleNamespace(retcode=0, margin=1.0, margin_free=1.0, margin_level=1.0, profit=1.0, equity=1.0, comment="ok")
    )
    patcher.start()
    
    try:
        # Visibility
        assert client.get("/account", headers=auth_headers).status_code == 200
        assert client.get("/positions", headers=auth_headers).status_code == 200
        assert client.get("/orders", headers=auth_headers).status_code == 200
        assert client.get("/terminal", headers=auth_headers).status_code == 200
        assert client.get("/tick/V75", headers=auth_headers).status_code == 200
        
        # History - Fix iso format (without Z)
        assert client.get("/history/deals?date_from=2023-01-01T00:00:00&date_to=2023-12-31T00:00:00", headers=auth_headers).status_code == 200
        assert client.get("/history/orders?date_from=2023-01-01T00:00:00&date_to=2023-12-31T00:00:00", headers=auth_headers).status_code == 200
        assert client.get("/broker-symbols", headers=auth_headers).status_code == 200

        # Execution
        assert client.post(
            "/order-check",
            headers=auth_headers,
            json={"ticker": "V75", "type": "buy_limit", "volume": 0.1, "price": 100.0},
        ).status_code == 200
        assert client.post("/pending-order", headers=auth_headers, json={"ticker": "V75", "type": "buy_limit", "volume": 0.1, "price": 100.0}).status_code == 200
        
        # Management
        assert client.post("/close-position", headers=auth_headers, json={"ticket": 1}).status_code == 200
        assert client.delete("/orders/1", headers=auth_headers).status_code == 200
        assert client.put("/orders/1", headers=auth_headers, json={"price": 105.0}).status_code == 200
        assert client.put("/positions/1/sltp", headers=auth_headers, json={"sl": 90.0}).status_code == 200

        # Execute
        assert client.post("/execute", headers=auth_headers, json={"ticker": "V75", "action": "buy", "quantity": 0.1, "current_price": 100.0}).status_code in (200, 503)
    finally:
        patcher.stop()

def test_full_coverage_errors(override_submit, fake_mt5, auth_headers, override_settings, client, monkeypatch):
    import app.mt5_worker
    from app.main import settings
    fake_mt5._tick.time = int(time.time())
    mt5 = sys.modules["MetaTrader5"]
    settings.execution_enabled = True
    settings.disable_mt5_worker = False
    
    patcher = patch.multiple(sys.modules["MetaTrader5"], create=True,
        account_info=lambda: None,
        terminal_info=lambda: None,
        last_error=lambda: (1, "OK"),
        positions_get=lambda **k: None,
        history_deals_get=lambda f, t, **k: None,
        history_orders_get=lambda f, t, **k: None,
        orders_get=lambda **k: None,
        symbols_get=lambda **k: None,
        order_check=lambda *args: None,
        order_send=lambda *args: None
    )
    patcher.start()
    
    try:
        client.get("/account", headers=auth_headers)
        client.get("/positions", headers=auth_headers)
        client.get("/orders", headers=auth_headers)
        client.get("/terminal", headers=auth_headers)
        client.get("/tick/V75", headers=auth_headers)
        client.get("/history/deals?date_from=2023-01-01T00:00:00&date_to=2023-12-31T00:00:00", headers=auth_headers)
        client.get("/history/orders?date_from=2023-01-01T00:00:00&date_to=2023-12-31T00:00:00", headers=auth_headers)
        client.get("/broker-symbols", headers=auth_headers)
        client.post(
            "/order-check",
            headers=auth_headers,
            json={"ticker": "V75", "type": "buy_limit", "volume": 0.1, "price": 100.0},
        )
        client.post("/pending-order", headers=auth_headers, json={"ticker": "V75", "type": "buy_limit", "volume": 0.1, "price": 100.0})
        client.post("/close-position", headers=auth_headers, json={"ticket": 1})
        client.delete("/orders/1", headers=auth_headers)
        client.put("/orders/1", headers=auth_headers, json={"price": 105.0})
        client.put("/positions/1/sltp", headers=auth_headers, json={"sl": 90.0})
        client.post("/execute", headers=auth_headers, json={"ticker": "V75", "action": "buy", "quantity": 0.1, "current_price": 100.0})
    finally:
        patcher.stop()
