import pytest
from types import SimpleNamespace
from unittest.mock import patch

@pytest.fixture
def mock_get_state():
    with patch("app.routes.history.get_state") as mock_state:
        from app.mt5_worker import WorkerState
        mock_state.return_value = WorkerState.AUTHORIZED
        yield mock_state

@pytest.fixture
def mock_mt5_submit():
    with patch("app.routes.history.submit") as mock_submit:
        yield mock_submit

def test_history_deals_success(client, auth_headers, mock_mt5_submit, mock_get_state, completed_future_factory):
    from app.routes.history import DealsResponse
    from app.models.deal import Deal
    
    mock_deal = Deal(
        ticket=1001,
        order_ticket=2001,
        position_id=3001,
        symbol="EURUSD",
        type="buy",
        entry="in",
        volume=0.1,
        price=1.1000,
        profit=5.50,
        swap=-0.10,
        commission=-0.50,
        fee=0.0,
        time="2026-03-01T12:00:00Z",
        magic=123
    )
    
    # The endpoint now directly completes and returns DealsResponse because the mock wrapped logic is abstracted out via _fetch_deals
    # So we should just make the submit mock return DealsResponse
    mock_submit_ret = DealsResponse(
        deals=[mock_deal],
        count=1,
        net_profit=5.50,
        total_swap=-0.10,
        total_commission=-0.50
    )
    mock_mt5_submit.return_value = completed_future_factory(mock_submit_ret)

    response = client.get(
        "/history/deals?date_from=2026-02-01T00:00:00Z&date_to=2026-03-01T00:00:00Z",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["deals"][0]["ticket"] == 1001
    assert data["net_profit"] == 5.50

def test_history_deals_empty(client, auth_headers, mock_mt5_submit, mock_get_state, completed_future_factory):
    from app.routes.history import DealsResponse
    
    mock_submit_ret = DealsResponse(
        deals=[],
        count=0,
        net_profit=0.0,
        total_swap=0.0,
        total_commission=0.0
    )
    mock_mt5_submit.return_value = completed_future_factory(mock_submit_ret)

    response = client.get(
        "/history/deals?date_from=2026-02-01T00:00:00Z&date_to=2026-03-01T00:00:00Z",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["net_profit"] == 0.0
    assert len(data["deals"]) == 0

def test_history_deals_connection_error(client, auth_headers, mock_mt5_submit, mock_get_state):
    mock_mt5_submit.side_effect = ConnectionError("MT5 disconnected")
    
    response = client.get(
        "/history/deals?date_from=2026-02-01T00:00:00Z&date_to=2026-03-01T00:00:00Z",
        headers=auth_headers
    )
    assert response.status_code == 503
    assert "Not connected to MT5" in response.json()["detail"]
