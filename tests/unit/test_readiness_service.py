from __future__ import annotations

import time
from concurrent.futures import Future
from types import SimpleNamespace

import pytest

from app.models.readiness import OverallStatus, ReadinessStatus
from app.mt5_worker import WorkerState


def _immediate_submit(fn):
    fut = Future()
    try:
        fut.set_result(fn())
    except Exception as exc:  # pragma: no cover - safety net for readiness tests
        fut.set_exception(exc)
    return fut


def _checks_by_id(response):
    return {check.check_id: check for check in response.checks}


@pytest.fixture
def readiness_settings(monkeypatch):
    from app.services import readiness as readiness_service

    settings = readiness_service.get_settings()
    original = {
        "execution_enabled": settings.execution_enabled,
        "multi_trade_overload_queue_threshold": settings.multi_trade_overload_queue_threshold,
        "tick_freshness_threshold_seconds": settings.tick_freshness_threshold_seconds,
    }
    settings.execution_enabled = True
    settings.multi_trade_overload_queue_threshold = 10
    settings.tick_freshness_threshold_seconds = 30
    monkeypatch.setattr(readiness_service, "submit", _immediate_submit)
    yield settings
    settings.execution_enabled = original["execution_enabled"]
    settings.multi_trade_overload_queue_threshold = original["multi_trade_overload_queue_threshold"]
    settings.tick_freshness_threshold_seconds = original["tick_freshness_threshold_seconds"]


@pytest.mark.asyncio
async def test_evaluate_readiness_marks_disconnected_worker_and_unknown_mt5_checks(monkeypatch, readiness_settings):
    from app.services import readiness as readiness_service

    monkeypatch.setattr(readiness_service, "get_state", lambda: WorkerState.DISCONNECTED)
    readiness_settings.execution_enabled = False

    response = await readiness_service.evaluate_readiness(operation="buy", symbol="V75", direction="buy", volume=0.01)
    checks = _checks_by_id(response)

    assert response.overall_status == OverallStatus.BLOCKED
    assert checks["global.worker_connected"].status == ReadinessStatus.FAIL
    assert checks["global.execution_policy"].status == ReadinessStatus.FAIL
    assert checks["global.mt5_terminal_connected"].status == ReadinessStatus.UNKNOWN
    assert checks["symbol.exists"].status == ReadinessStatus.UNKNOWN


@pytest.mark.asyncio
async def test_evaluate_readiness_short_circuits_when_symbol_is_missing(monkeypatch, readiness_settings, fake_mt5):
    from app.services import readiness as readiness_service

    fake_mt5.terminal_info = lambda: SimpleNamespace(trade_allowed=True)
    fake_mt5.account_info = lambda: SimpleNamespace(trade_allowed=True)
    fake_mt5.symbol_info = lambda symbol: None
    monkeypatch.setattr(readiness_service, "get_state", lambda: WorkerState.AUTHORIZED)

    response = await readiness_service.evaluate_readiness(operation="buy", symbol="UNKNOWN", direction="buy", volume=0.01)
    checks = _checks_by_id(response)

    assert response.overall_status == OverallStatus.BLOCKED
    assert checks["symbol.exists"].status == ReadinessStatus.FAIL
    assert checks["symbol.selectable"].status == ReadinessStatus.UNKNOWN
    assert checks["symbol.trade_mode"].status == ReadinessStatus.UNKNOWN
    assert checks["symbol.volume_valid"].status == ReadinessStatus.UNKNOWN


@pytest.mark.asyncio
async def test_evaluate_readiness_flags_stale_tick_and_invalid_volume(monkeypatch, readiness_settings, fake_mt5):
    from app.services import readiness as readiness_service

    fake_mt5.terminal_info = lambda: SimpleNamespace(trade_allowed=True)
    fake_mt5.account_info = lambda: SimpleNamespace(trade_allowed=True)
    fake_mt5.symbol_info = lambda symbol: SimpleNamespace(
        visible=False,
        trade_mode=4,
        filling_mode=3,
        volume_min=0.01,
        volume_max=1.0,
        volume_step=0.01,
    )
    fake_mt5.symbol_info_tick = lambda symbol: SimpleNamespace(time=int(time.time()) - 120)

    monkeypatch.setattr(readiness_service, "get_state", lambda: WorkerState.AUTHORIZED)

    response = await readiness_service.evaluate_readiness(
        operation="buy",
        symbol="V75",
        direction="buy",
        volume=0.015,
    )
    checks = _checks_by_id(response)

    assert response.overall_status == OverallStatus.BLOCKED
    assert checks["symbol.selectable"].status == ReadinessStatus.WARN
    assert checks["symbol.tick_freshness"].status == ReadinessStatus.WARN
    assert checks["symbol.volume_valid"].status == ReadinessStatus.FAIL
    assert "step size 0.01" in checks["symbol.volume_valid"].user_message


@pytest.mark.asyncio
async def test_evaluate_readiness_surfaces_trade_mode_restriction(monkeypatch, readiness_settings, fake_mt5):
    from app.services import readiness as readiness_service

    fake_mt5.terminal_info = lambda: SimpleNamespace(trade_allowed=True)
    fake_mt5.account_info = lambda: SimpleNamespace(trade_allowed=True)
    fake_mt5.symbol_info = lambda symbol: SimpleNamespace(
        visible=True,
        trade_mode=1,
        filling_mode=2,
        volume_min=0.01,
        volume_max=1.0,
        volume_step=0.01,
    )
    fake_mt5.symbol_info_tick = lambda symbol: SimpleNamespace(time=int(time.time()))

    monkeypatch.setattr(readiness_service, "get_state", lambda: WorkerState.AUTHORIZED)

    response = await readiness_service.evaluate_readiness(
        operation="sell",
        symbol="V75",
        direction="sell",
        volume=0.01,
    )
    checks = _checks_by_id(response)

    assert response.overall_status == OverallStatus.BLOCKED
    assert checks["symbol.trade_mode"].status == ReadinessStatus.FAIL
    assert "sell" in checks["symbol.trade_mode"].user_message.lower()
