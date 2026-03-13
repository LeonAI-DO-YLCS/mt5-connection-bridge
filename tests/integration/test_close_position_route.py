import pytest
from types import SimpleNamespace
from unittest.mock import patch

@pytest.fixture(autouse=True)
def enable_worker(monkeypatch):
    from app.main import settings
    monkeypatch.setattr(settings, "disable_mt5_worker", False)
    monkeypatch.setenv("STRICT_HTTP_SEMANTICS", "true")
    yield

@pytest.fixture
def mock_get_state():
    with patch("app.routes.close_position.get_state") as mock_state:
        from app.mt5_worker import WorkerState
        mock_state.return_value = WorkerState.AUTHORIZED
        yield mock_state

@pytest.fixture
def mock_mt5_submit():
    with patch("app.routes.close_position.submit") as mock_submit:
        yield mock_submit

@pytest.fixture
def mock_mt5_positions_get():
    with patch("MetaTrader5.positions_get") as mock_get:
        yield mock_get

@pytest.fixture
def mock_mt5_symbol_info():
    with patch("MetaTrader5.symbol_info") as mock_info:
        yield mock_info

@pytest.fixture
def mock_mt5_order_send():
    with patch("MetaTrader5.order_send") as mock_send:
        yield mock_send

def test_close_position_success(client, auth_headers, mock_mt5_submit, mock_get_state, completed_future_factory):
    # Need to mock the execution inside the worker if we use `submit`
    mock_response = {
        "success": True,
        "filled_price": 100.0,
        "filled_quantity": 0.01,
        "ticket_id": 123456,
        "error": None
    }
    
    # Actually `submit` returns what `_execute_in_worker` returns which is a 5-tuple!
    from app.models.trade import TradeResponse
    from app.main import settings
    settings.execution_enabled = True

    mock_tuple = (TradeResponse(**mock_response), "fill_confirmed", "with_comment", None, None)
    mock_mt5_submit.return_value = completed_future_factory(mock_tuple)

    response = client.post(
        "/close-position",
        headers=auth_headers,
        json={"ticket": 12345}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["ticket_id"] == 123456

def test_close_position_execution_disabled(client, auth_headers, monkeypatch):
    from app.main import settings
    monkeypatch.setattr(settings, "execution_enabled", False)

    response = client.post(
        "/close-position",
        headers=auth_headers,
        json={"ticket": 12345}
    )
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "EXECUTION_DISABLED"
    assert "disabled" in data["message"].lower()


def test_close_position_unknown_ticket_returns_404(client, auth_headers, mock_mt5_submit, mock_get_state, completed_future_factory):
    from app.models.trade import TradeResponse
    from app.main import settings

    settings.execution_enabled = True
    mock_mt5_submit.return_value = completed_future_factory(
        (TradeResponse(success=False, error="Position 999 not found"), "position_not_found", "none", None, None)
    )

    response = client.post(
        "/close-position",
        headers=auth_headers,
        json={"ticket": 999}
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "RESOURCE_NOT_FOUND"
    assert "not found" in data["message"].lower()

def test_close_position_connection_error(client, auth_headers, mock_mt5_submit, mock_get_state):
    from app.main import settings
    settings.execution_enabled = True
    mock_mt5_submit.side_effect = ConnectionError("MT5 not connected")

    response = client.post(
        "/close-position",
        headers=auth_headers,
        json={"ticket": 12345}
    )
    assert response.status_code == 503
    data = response.json()
    assert data["code"] == "MT5_DISCONNECTED"
    assert "Not connected to MT5" in data["message"]
