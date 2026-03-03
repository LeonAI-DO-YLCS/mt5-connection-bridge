import pytest
from types import SimpleNamespace
from unittest.mock import patch

@pytest.fixture
def mock_get_state():
    with patch("app.routes.broker_symbols.get_state") as mock_state:
        from app.mt5_worker import WorkerState
        mock_state.return_value = WorkerState.AUTHORIZED
        yield mock_state

@pytest.fixture
def mock_mt5_submit():
    with patch("app.routes.broker_symbols.submit") as mock_submit:
        yield mock_submit

@pytest.fixture(autouse=True)
def mock_symbol_map(monkeypatch):
    from types import SimpleNamespace
    dummy_symbol = SimpleNamespace(mt5_symbol="AAPL", precision=2, trade_mode=0)
    monkeypatch.setattr("app.routes.broker_symbols.symbol_map", {"AAPL": dummy_symbol})
    yield

def test_broker_symbols_success(client, auth_headers, mock_mt5_submit, mock_get_state, completed_future_factory):
    from app.routes.broker_symbols import BrokerSymbolsResponse
    from app.models.broker_symbol import BrokerSymbol
    
    # One configured, one unconfigured
    s1 = BrokerSymbol(
        name="AAPL",
        description="Apple Inc.",
        path="Stocks/US",
        spread=3,
        digits=2,
        volume_min=0.01,
        volume_max=100.0,
        trade_mode=4,
        is_configured=True
    )
    s2 = BrokerSymbol(
        name="EURUSD",
        description="Euro vs US Dollar",
        path="Forex/Majors",
        spread=10,
        digits=5,
        volume_min=0.01,
        volume_max=100.0,
        trade_mode=0,
        is_configured=False
    )
    
    mock_submit_ret = BrokerSymbolsResponse(
        symbols=[s1, s2],
        count=2
    )
    mock_mt5_submit.return_value = completed_future_factory(mock_submit_ret)

    response = client.get("/broker-symbols", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    symbols = {s["name"]: s for s in data["symbols"]}
    assert symbols["AAPL"]["is_configured"] is True
    assert symbols["EURUSD"]["is_configured"] is False

def test_broker_symbols_group_filter(client, auth_headers, mock_mt5_submit, mock_get_state, completed_future_factory):
    from app.routes.broker_symbols import BrokerSymbolsResponse
    from app.models.broker_symbol import BrokerSymbol
    
    s = BrokerSymbol(
        name="EURUSD",
        description="Euro vs US Dollar",
        path="Forex/Majors",
        spread=10,
        digits=5,
        volume_min=0.01,
        volume_max=100.0,
        trade_mode=0,
        is_configured=False
    )
    
    mock_submit_ret = BrokerSymbolsResponse(
        symbols=[s],
        count=1
    )
    mock_mt5_submit.return_value = completed_future_factory(mock_submit_ret)

    response = client.get("/broker-symbols?group=*USD*", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["count"] == 1

def test_broker_symbols_connection_error(client, auth_headers, mock_mt5_submit, mock_get_state):
    mock_mt5_submit.side_effect = ConnectionError("MT5 disconnected")
    
    response = client.get("/broker-symbols", headers=auth_headers)
    assert response.status_code == 503
    assert "Not connected to MT5" in response.json()["detail"]


def test_broker_symbols_maps_trade_mode_to_human_label(
    client,
    auth_headers,
    mock_get_state,
    completed_future_factory,
):
    with patch("MetaTrader5.symbols_get", create=True) as mock_symbols_get, patch("MetaTrader5.last_error", create=True) as mock_last_error:
        with patch("app.routes.broker_symbols.submit") as mock_submit:
            mock_symbols_get.return_value = [
                SimpleNamespace(
                    name="EURUSD",
                    description="Euro vs US Dollar",
                    path="Forex/Majors",
                    spread=10,
                    digits=5,
                    volume_min=0.01,
                    volume_max=100.0,
                    trade_mode=4,
                )
            ]
            mock_last_error.return_value = (1, "OK")
            mock_submit.side_effect = lambda fn: completed_future_factory(fn())

            response = client.get("/broker-symbols", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 1
            assert data["symbols"][0]["trade_mode"] == 4  # int (Full)
            assert data["symbols"][0]["trade_mode_label"] == "Full"
