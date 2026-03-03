import pytest
from types import SimpleNamespace
from unittest.mock import patch

@pytest.fixture(autouse=True)
def enable_worker():
    from app.main import settings
    settings.disable_mt5_worker = False
    yield
    settings.disable_mt5_worker = True

@pytest.fixture
def mock_mt5_terminal_info():
    with patch("app.routes.terminal.submit") as mock_submit:
        yield mock_submit

def test_terminal_route_success(client, auth_headers, mock_mt5_terminal_info, completed_future_factory):
    term_info = SimpleNamespace(
        build=3802,
        name="MetaTrader 5",
        path="C:\\Program Files\\MT5",
        data_path="C:\\Users\\user\\AppData\\Roaming\\MT5",
        connected=True,
        trade_allowed=True
    )
    mock_mt5_terminal_info.return_value = completed_future_factory(term_info)

    response = client.get("/terminal", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["build"] == 3802
    assert data["connected"] is True

def test_terminal_route_connection_error(client, auth_headers, mock_mt5_terminal_info, completed_future_factory):
    mock_mt5_terminal_info.side_effect = ConnectionError("MT5 not connected")

    response = client.get("/terminal", headers=auth_headers)
    assert response.status_code == 503
    assert response.json() == {"detail": "Not connected to MT5"}


def test_terminal_route_worker_disabled(client, auth_headers, monkeypatch):
    from app.main import settings
    monkeypatch.setattr(settings, "disable_mt5_worker", True)
    response = client.get("/terminal", headers=auth_headers)
    assert response.status_code == 503
