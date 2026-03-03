from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.models.trade import TradeResponse
from app.mt5_worker import WorkerState


@pytest.fixture(autouse=True)
def enable_worker_and_execution(monkeypatch):
    from app.main import settings

    monkeypatch.setattr(settings, "disable_mt5_worker", False)
    monkeypatch.setattr(settings, "execution_enabled", True)
    monkeypatch.setattr(settings, "multi_trade_overload_queue_threshold", 100)
    yield


@pytest.fixture(autouse=True)
def reset_inflight_state():
    from app.routes import close_position as close_route
    from app.routes import orders as orders_route
    from app.routes import pending_order as pending_route
    from app.routes import positions as positions_route

    close_route._inflight_requests = 0
    orders_route._inflight_requests = 0
    pending_route._inflight_requests = 0
    positions_route._inflight_requests = 0
    yield
    close_route._inflight_requests = 0
    orders_route._inflight_requests = 0
    pending_route._inflight_requests = 0
    positions_route._inflight_requests = 0


def test_cancel_order_overload_returns_409(client, auth_headers, monkeypatch):
    from app.main import settings
    from app.routes import orders as orders_route

    settings.execution_enabled = True
    settings.multi_trade_overload_queue_threshold = 1
    monkeypatch.setattr(orders_route, "get_queue_depth", lambda: 5)

    response = client.delete("/orders/100", headers=auth_headers)
    assert response.status_code == 409
    assert "overload" in response.json()["detail"].lower()


def test_cancel_order_not_found_maps_404(client, auth_headers, completed_future_factory):
    from app.main import settings
    settings.execution_enabled = True
    with patch("app.routes.orders.submit") as mock_submit:
        mock_submit.return_value = completed_future_factory(
            (TradeResponse(success=False, error="Order not found"), "order_not_found")
        )
        response = client.delete("/orders/100", headers=auth_headers)
        assert response.status_code == 404


def test_modify_sltp_not_found_maps_404(client, auth_headers, completed_future_factory):
    from app.main import settings
    settings.execution_enabled = True
    with patch("app.routes.positions.submit") as mock_submit:
        mock_submit.return_value = completed_future_factory(
            (TradeResponse(success=False, error="Position not found"), "position_not_found")
        )
        response = client.put("/positions/101/sltp", headers=auth_headers, json={"sl": 1.0, "tp": 2.0})
        assert response.status_code == 404


def test_close_position_invalid_volume_maps_422(client, auth_headers, completed_future_factory):
    from app.main import settings
    settings.execution_enabled = True
    with patch("app.routes.close_position.get_state") as mock_state, patch("app.routes.close_position.submit") as mock_submit:
        mock_state.return_value = WorkerState.AUTHORIZED
        mock_submit.return_value = completed_future_factory(
            (TradeResponse(success=False, error="quantity must be greater than 0"), "invalid_volume")
        )
        response = client.post("/close-position", headers=auth_headers, json={"ticket": 100, "volume": 0.0})
        assert response.status_code == 422


def test_pending_order_invalid_params_maps_422(client, auth_headers, completed_future_factory, monkeypatch):
    from app.main import settings
    settings.execution_enabled = True
    with patch("app.routes.pending_order.get_state") as mock_state, patch("app.routes.pending_order.submit") as mock_submit:
        mock_state.return_value = WorkerState.AUTHORIZED
        monkeypatch.setattr(
            "app.routes.pending_order.symbol_map",
            {"AAPL": SimpleNamespace(mt5_symbol="AAPL")},
        )
        mock_submit.return_value = completed_future_factory(
            (TradeResponse(success=False, error="Invalid order parameters"), "invalid_params")
        )
        response = client.post(
            "/pending-order",
            headers=auth_headers,
            json={"ticker": "AAPL", "type": "buy_limit", "volume": 0.01, "price": 100.0},
        )
        assert response.status_code == 422


def test_pending_order_overload_returns_409(client, auth_headers, monkeypatch):
    from app.main import settings
    from app.routes import pending_order as pending_route

    settings.execution_enabled = True
    settings.multi_trade_overload_queue_threshold = 1
    monkeypatch.setattr(pending_route, "get_queue_depth", lambda: 10)
    monkeypatch.setattr(
        "app.routes.pending_order.symbol_map",
        {"AAPL": SimpleNamespace(mt5_symbol="AAPL")},
    )

    response = client.post(
        "/pending-order",
        headers=auth_headers,
        json={"ticker": "AAPL", "type": "buy_limit", "volume": 0.01, "price": 100.0},
    )
    assert response.status_code == 409
