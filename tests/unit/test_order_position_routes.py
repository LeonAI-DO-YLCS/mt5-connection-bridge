from __future__ import annotations

from concurrent.futures import Future
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.messaging.codes import ErrorCode
from app.messaging.envelope import MessageEnvelopeException
from app.models.modify_order import ModifyOrderRequest
from app.models.modify_sltp import ModifySLTPRequest


def _result_future(value=None, error: Exception | None = None) -> Future:
    fut = Future()
    if error is not None:
        fut.set_exception(error)
    else:
        fut.set_result(value)
    return fut


def _immediate_submit(fn):
    fut = Future()
    try:
        fut.set_result(fn())
    except Exception as exc:  # pragma: no cover - safety net for route tests
        fut.set_exception(exc)
    return fut


@pytest.fixture
def route_settings():
    from app.main import settings

    original = {
        "disable_mt5_worker": settings.disable_mt5_worker,
        "execution_enabled": settings.execution_enabled,
        "multi_trade_overload_queue_threshold": settings.multi_trade_overload_queue_threshold,
    }
    settings.disable_mt5_worker = False
    settings.execution_enabled = True
    settings.multi_trade_overload_queue_threshold = 100
    yield settings
    settings.disable_mt5_worker = original["disable_mt5_worker"]
    settings.execution_enabled = original["execution_enabled"]
    settings.multi_trade_overload_queue_threshold = original["multi_trade_overload_queue_threshold"]


@pytest.mark.asyncio
async def test_get_orders_returns_empty_when_mt5_returns_none(monkeypatch, route_settings):
    from app.routes import orders as orders_route

    monkeypatch.setattr(orders_route, "submit", lambda fn: _result_future(None))

    payload = await orders_route.get_orders()

    assert payload == {"orders": [], "count": 0}


@pytest.mark.asyncio
async def test_get_orders_raises_service_unavailable_on_connection_error(monkeypatch, route_settings):
    from app.routes import orders as orders_route

    monkeypatch.setattr(
        orders_route,
        "submit",
        lambda fn: _result_future(error=ConnectionError("mt5 offline")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await orders_route.get_orders()

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Not connected to MT5"


@pytest.mark.asyncio
async def test_modify_order_rejects_when_execution_disabled(monkeypatch, route_settings):
    from app.routes import orders as orders_route

    route_settings.execution_enabled = False

    with pytest.raises(MessageEnvelopeException) as exc_info:
        await orders_route.modify_order(
            ModifyOrderRequest(price=100.0),
            ticket=12345,
            idempotency_key=None,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.envelope.code == ErrorCode.EXECUTION_DISABLED.name


@pytest.mark.asyncio
async def test_modify_order_returns_not_found_for_missing_order(monkeypatch, route_settings, fake_mt5):
    from app.routes import orders as orders_route

    fake_mt5._order_result = SimpleNamespace(retcode=10021, comment="Order not found")
    monkeypatch.setattr(orders_route, "submit", _immediate_submit)

    with pytest.raises(MessageEnvelopeException) as exc_info:
        await orders_route.modify_order(
            ModifyOrderRequest(price=99.5, sl=98.0, tp=105.0),
            ticket=54321,
            idempotency_key=None,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.envelope.code == ErrorCode.RESOURCE_NOT_FOUND.name


@pytest.mark.asyncio
async def test_modify_order_returns_success_payload(monkeypatch, route_settings, fake_mt5):
    from app.routes import orders as orders_route

    fake_mt5._order_result = SimpleNamespace(retcode=10009, comment="done")
    monkeypatch.setattr(orders_route, "submit", _immediate_submit)

    payload = await orders_route.modify_order(
        ModifyOrderRequest(price=101.0, sl=99.0, tp=110.0),
        ticket=67890,
        idempotency_key=None,
    )

    assert payload == {"success": True, "ticket_id": 67890, "error": None}


@pytest.mark.asyncio
async def test_get_positions_returns_empty_when_mt5_returns_none(monkeypatch, route_settings):
    from app.routes import positions as positions_route

    monkeypatch.setattr(positions_route, "submit", lambda fn: _result_future(None))

    payload = await positions_route.get_positions()

    assert payload == {"positions": [], "count": 0}


@pytest.mark.asyncio
async def test_modify_sltp_rejects_when_position_missing(monkeypatch, route_settings, fake_mt5):
    from app.routes import positions as positions_route

    fake_mt5._order_result = SimpleNamespace(retcode=10021, comment="Position not found")
    monkeypatch.setattr(positions_route, "submit", _immediate_submit)

    with pytest.raises(MessageEnvelopeException) as exc_info:
        await positions_route.modify_sltp(
            ModifySLTPRequest(sl=95.0, tp=120.0),
            ticket=45678,
            idempotency_key=None,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.envelope.code == ErrorCode.RESOURCE_NOT_FOUND.name


@pytest.mark.asyncio
async def test_modify_sltp_returns_success_payload(monkeypatch, route_settings, fake_mt5):
    from app.routes import positions as positions_route

    fake_mt5._order_result = SimpleNamespace(retcode=10009, comment="done")
    monkeypatch.setattr(positions_route, "submit", _immediate_submit)

    payload = await positions_route.modify_sltp(
        ModifySLTPRequest(sl=94.0, tp=121.0),
        ticket=22222,
        idempotency_key=None,
    )

    assert payload == {"success": True, "ticket_id": 22222, "error": None}
