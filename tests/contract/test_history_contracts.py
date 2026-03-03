import pytest
import app.main  # Pre-loads the module properly to avoid circular imports during testing
from unittest.mock import patch
from app.routes.history import DealsResponse, OrdersResponse
from app.models.deal import Deal
from app.models.historical_order import HistoricalOrder
from app.routes.broker_symbols import BrokerSymbolsResponse
from app.models.broker_symbol import BrokerSymbol
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

def test_history_deals_contract(client, auth_headers):
    with patch("app.routes.history.submit") as mock_submit:
        mock_submit.return_value = make_future(DealsResponse(
            deals=[Deal(
                ticket=1001, order_ticket=2001, position_id=3001,
                symbol="V75", type="buy", entry="in", volume=0.1,
                price=100.0, profit=5.0, swap=0.0, commission=0.0,
                fee=0.0, time="2026-03-01T00:00:00Z", magic=0
            )],
            count=1, net_profit=5.0, total_swap=0.0, total_commission=0.0
        ))
        response = client.get("/history/deals?date_from=2026-02-01T00:00:00Z&date_to=2026-03-01T00:00:00Z", headers=auth_headers)
        assert response.status_code == 200
        DealsResponse.model_validate(response.json())

def test_history_orders_contract(client, auth_headers):
    with patch("app.routes.history.submit") as mock_submit:
        mock_submit.return_value = make_future(OrdersResponse(
            orders=[HistoricalOrder(
                ticket=2001, symbol="V75", type="buy", volume=0.1, price=100.0,
                sl=None, tp=None, state="filled",
                time_setup="2026-03-01T00:00:00Z", time_done="2026-03-01T00:00:01Z",
                magic=0
            )],
            count=1
        ))
        response = client.get("/history/orders?date_from=2026-02-01T00:00:00Z&date_to=2026-03-01T00:00:00Z", headers=auth_headers)
        assert response.status_code == 200
        OrdersResponse.model_validate(response.json())

def test_broker_symbols_contract(client, auth_headers):
    with patch("app.routes.broker_symbols.submit") as mock_submit:
        mock_submit.return_value = make_future(BrokerSymbolsResponse(
            symbols=[BrokerSymbol(
                name="V75", description="Volatility 75 Index", path="Synthetic/Volatility",
                spread=100, digits=2, volume_min=0.001, volume_max=100.0,
                trade_mode="4", is_configured=True
            )],
            count=1
        ))
        response = client.get("/broker-symbols", headers=auth_headers)
        assert response.status_code == 200
        BrokerSymbolsResponse.model_validate(response.json())
