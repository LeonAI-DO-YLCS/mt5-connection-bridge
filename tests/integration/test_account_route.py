import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def enable_worker():
    from app.main import settings
    settings.disable_mt5_worker = False
    yield
    settings.disable_mt5_worker = True

@pytest.fixture
def mock_mt5_account_info():
    with patch("app.routes.account.submit") as mock_submit:
        yield mock_submit

def test_account_route_success(client, auth_headers, mock_mt5_account_info, completed_future_factory):
    mock_acc_info = SimpleNamespace(
        login=1234567,
        server="TestServer",
        balance=10000.0,
        equity=10500.0,
        margin=500.0,
        margin_free=10000.0,
        profit=500.0,
        currency="USD",
        leverage=100
    )
    mock_mt5_account_info.return_value = completed_future_factory(mock_acc_info)

    response = client.get("/account", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["login"] == 1234567
    assert data["server"] == "TestServer"
    assert data["balance"] == 10000.0
    assert data["equity"] == 10500.0

def test_account_route_connection_error(client, auth_headers, mock_mt5_account_info, completed_future_factory):
    mock_mt5_account_info.side_effect = ConnectionError("MT5 not connected")

    response = client.get("/account", headers=auth_headers)
    assert response.status_code == 503
    data = response.json()
    assert data["code"] == "MT5_DISCONNECTED"
    assert data["category"] == "error"
    assert "Not connected to MT5" in data["message"]


def test_account_route_worker_disabled(client, auth_headers, monkeypatch):
    from app.main import settings
    monkeypatch.setattr(settings, "disable_mt5_worker", True)
    response = client.get("/account", headers=auth_headers)
    assert response.status_code == 503
