"""Unit tests for the readiness service (app.services.readiness)."""

from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.models.readiness import OverallStatus, ReadinessStatus
from app.mt5_worker import WorkerState


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_settings(**overrides):
    defaults = {
        "execution_enabled": True,
        "multi_trade_overload_queue_threshold": 100,
        "tick_freshness_threshold_seconds": 30,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_symbol_info(**overrides):
    defaults = {
        "name": "EURUSD",
        "visible": True,
        "volume_min": 0.01,
        "volume_max": 100.0,
        "volume_step": 0.01,
        "trade_mode": 4,
        "filling_mode": 3,      # FOK + IOC
        "spread": 10,
        "trade_freeze_level": 0,
        "trade_stops_level": 0,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_tick(age_seconds: int = 5):
    return SimpleNamespace(
        bid=1.1000,
        ask=1.1002,
        time=int(time.time()) - age_seconds,
    )


# ── Tests ────────────────────────────────────────────────────────────────────

class TestGlobalChecks:
    """Tests for global readiness checks."""

    @pytest.mark.asyncio
    async def test_all_global_pass(self, monkeypatch):
        """When worker connected, MT5 available, exec enabled → ready."""
        from app.services import readiness as svc

        monkeypatch.setattr(svc, "get_state", lambda: WorkerState.AUTHORIZED)
        monkeypatch.setattr(svc, "get_queue_depth", lambda: 0)
        monkeypatch.setattr(svc, "get_settings", _make_settings)

        # Mock _inflight_requests as 0
        with patch("app.routes.execute._inflight_requests", 0):
            # Mock MT5 global checks
            async def _mock_mt5_global():
                return [
                    svc.ReadinessCheck(
                        check_id="global.mt5_terminal_connected",
                        status=ReadinessStatus.PASS, blocking=True,
                        user_message="MT5 terminal connection is active.", action="",
                    ),
                    svc.ReadinessCheck(
                        check_id="global.terminal_trade_allowed",
                        status=ReadinessStatus.PASS, blocking=True,
                        user_message="Terminal trading is enabled.", action="",
                        details={"trade_allowed": True},
                    ),
                    svc.ReadinessCheck(
                        check_id="global.account_trade_allowed",
                        status=ReadinessStatus.PASS, blocking=True,
                        user_message="Account trading is enabled.", action="",
                        details={"trade_allowed": True},
                    ),
                ]

            monkeypatch.setattr(svc, "_run_mt5_global_checks", _mock_mt5_global)
            result = await svc.evaluate_readiness()

        assert result.overall_status == OverallStatus.READY
        assert len(result.blockers) == 0

    @pytest.mark.asyncio
    async def test_worker_disconnected_gives_blocked(self, monkeypatch):
        """When worker is disconnected → blocked, MT5 checks are unknown."""
        from app.services import readiness as svc

        monkeypatch.setattr(svc, "get_state", lambda: WorkerState.DISCONNECTED)
        monkeypatch.setattr(svc, "get_queue_depth", lambda: 0)
        monkeypatch.setattr(svc, "get_settings", _make_settings)

        with patch("app.routes.execute._inflight_requests", 0):
            result = await svc.evaluate_readiness()

        assert result.overall_status == OverallStatus.BLOCKED
        worker_check = next(c for c in result.checks if c.check_id == "global.worker_connected")
        assert worker_check.status == ReadinessStatus.FAIL

        # MT5-dependent checks should be UNKNOWN
        mt5_checks = [c for c in result.checks if c.check_id.startswith("global.mt5_")]
        assert all(c.status == ReadinessStatus.UNKNOWN for c in mt5_checks)

    @pytest.mark.asyncio
    async def test_execution_disabled_gives_blocked(self, monkeypatch):
        """When EXECUTION_ENABLED=false → blocked."""
        from app.services import readiness as svc

        monkeypatch.setattr(svc, "get_state", lambda: WorkerState.AUTHORIZED)
        monkeypatch.setattr(svc, "get_queue_depth", lambda: 0)
        monkeypatch.setattr(svc, "get_settings", lambda: _make_settings(execution_enabled=False))

        async def _mock_mt5_global():
            return [
                svc.ReadinessCheck(
                    check_id="global.mt5_terminal_connected",
                    status=ReadinessStatus.PASS, blocking=True,
                    user_message="OK", action="",
                ),
                svc.ReadinessCheck(
                    check_id="global.terminal_trade_allowed",
                    status=ReadinessStatus.PASS, blocking=True,
                    user_message="OK", action="", details={"trade_allowed": True},
                ),
                svc.ReadinessCheck(
                    check_id="global.account_trade_allowed",
                    status=ReadinessStatus.PASS, blocking=True,
                    user_message="OK", action="", details={"trade_allowed": True},
                ),
            ]

        monkeypatch.setattr(svc, "_run_mt5_global_checks", _mock_mt5_global)

        with patch("app.routes.execute._inflight_requests", 0):
            result = await svc.evaluate_readiness()

        assert result.overall_status == OverallStatus.BLOCKED
        exec_check = next(c for c in result.checks if c.check_id == "global.execution_policy")
        assert exec_check.status == ReadinessStatus.FAIL

    @pytest.mark.asyncio
    async def test_queue_overloaded_gives_blocked(self, monkeypatch):
        """When queue depth exceeds threshold → blocked."""
        from app.services import readiness as svc

        monkeypatch.setattr(svc, "get_state", lambda: WorkerState.AUTHORIZED)
        monkeypatch.setattr(svc, "get_queue_depth", lambda: 95)
        monkeypatch.setattr(svc, "get_settings", _make_settings)

        async def _mock_mt5_global():
            return [
                svc.ReadinessCheck(
                    check_id="global.mt5_terminal_connected",
                    status=ReadinessStatus.PASS, blocking=True,
                    user_message="OK", action="",
                ),
                svc.ReadinessCheck(
                    check_id="global.terminal_trade_allowed",
                    status=ReadinessStatus.PASS, blocking=True,
                    user_message="OK", action="", details={"trade_allowed": True},
                ),
                svc.ReadinessCheck(
                    check_id="global.account_trade_allowed",
                    status=ReadinessStatus.PASS, blocking=True,
                    user_message="OK", action="", details={"trade_allowed": True},
                ),
            ]

        monkeypatch.setattr(svc, "_run_mt5_global_checks", _mock_mt5_global)

        with patch("app.routes.execute._inflight_requests", 10):
            result = await svc.evaluate_readiness()

        assert result.overall_status == OverallStatus.BLOCKED
        queue_check = next(c for c in result.checks if c.check_id == "global.queue_capacity")
        assert queue_check.status == ReadinessStatus.FAIL


class TestSymbolChecks:
    """Tests for symbol-specific readiness checks."""

    @pytest.mark.asyncio
    async def test_symbol_not_found_gives_blocked(self, monkeypatch):
        """Symbol not recognized by MT5 → blocked + sub-checks unknown."""
        from app.services import readiness as svc
        from concurrent.futures import Future

        monkeypatch.setattr(svc, "get_state", lambda: WorkerState.AUTHORIZED)
        monkeypatch.setattr(svc, "get_queue_depth", lambda: 0)
        monkeypatch.setattr(svc, "get_settings", _make_settings)

        async def _mock_mt5_global():
            return [
                svc.ReadinessCheck(
                    check_id="global.mt5_terminal_connected",
                    status=ReadinessStatus.PASS, blocking=True,
                    user_message="OK", action="",
                ),
                svc.ReadinessCheck(
                    check_id="global.terminal_trade_allowed",
                    status=ReadinessStatus.PASS, blocking=True,
                    user_message="OK", action="", details={"trade_allowed": True},
                ),
                svc.ReadinessCheck(
                    check_id="global.account_trade_allowed",
                    status=ReadinessStatus.PASS, blocking=True,
                    user_message="OK", action="", details={"trade_allowed": True},
                ),
            ]

        monkeypatch.setattr(svc, "_run_mt5_global_checks", _mock_mt5_global)

        # Mock submit to return None for symbol_info
        def _mock_submit(fn):
            fut = Future()
            # The fn will call mt5.symbol_info which returns None
            import sys
            mt5_module = sys.modules.get("MetaTrader5")
            if mt5_module:
                orig_si = mt5_module.symbol_info
                mt5_module.symbol_info = lambda s: None
                try:
                    result = fn()
                except Exception as e:
                    fut.set_exception(e)
                else:
                    fut.set_result(result)
                finally:
                    mt5_module.symbol_info = orig_si
            else:
                fut.set_result((None, None))
            return fut

        monkeypatch.setattr(svc, "submit", _mock_submit)

        with patch("app.routes.execute._inflight_requests", 0):
            result = await svc.evaluate_readiness(symbol="NONEXIST")

        assert result.overall_status == OverallStatus.BLOCKED
        exists_check = next(c for c in result.checks if c.check_id == "symbol.exists")
        assert exists_check.status == ReadinessStatus.FAIL

        unknown_checks = [c for c in result.checks if c.check_id.startswith("symbol.") and c.check_id != "symbol.exists"]
        assert all(c.status == ReadinessStatus.UNKNOWN for c in unknown_checks)

    @pytest.mark.asyncio
    async def test_trade_mode_restricted_gives_blocked(self, monkeypatch, fake_mt5):
        """Symbol in LONG_ONLY mode + sell direction → blocked."""
        from app.services import readiness as svc
        from concurrent.futures import Future

        monkeypatch.setattr(svc, "get_state", lambda: WorkerState.AUTHORIZED)
        monkeypatch.setattr(svc, "get_queue_depth", lambda: 0)
        monkeypatch.setattr(svc, "get_settings", _make_settings)

        async def _mock_mt5_global():
            return [
                svc.ReadinessCheck(check_id="global.mt5_terminal_connected", status=ReadinessStatus.PASS, blocking=True, user_message="OK", action=""),
                svc.ReadinessCheck(check_id="global.terminal_trade_allowed", status=ReadinessStatus.PASS, blocking=True, user_message="OK", action="", details={"trade_allowed": True}),
                svc.ReadinessCheck(check_id="global.account_trade_allowed", status=ReadinessStatus.PASS, blocking=True, user_message="OK", action="", details={"trade_allowed": True}),
            ]

        monkeypatch.setattr(svc, "_run_mt5_global_checks", _mock_mt5_global)

        # Set symbol to LONG_ONLY mode (1)
        si = _make_symbol_info(trade_mode=1)
        fake_mt5.symbol_info = lambda s: si
        fake_mt5.symbol_info_tick = lambda s: _make_tick(5)

        def _mock_submit(fn):
            fut = Future()
            try:
                fut.set_result(fn())
            except Exception as e:
                fut.set_exception(e)
            return fut

        monkeypatch.setattr(svc, "submit", _mock_submit)

        with patch("app.routes.execute._inflight_requests", 0):
            result = await svc.evaluate_readiness(symbol="EURUSD", direction="sell")

        assert result.overall_status == OverallStatus.BLOCKED
        tm_check = next(c for c in result.checks if c.check_id == "symbol.trade_mode")
        assert tm_check.status == ReadinessStatus.FAIL

    @pytest.mark.asyncio
    async def test_tick_stale_gives_degraded(self, monkeypatch, fake_mt5):
        """Tick data older than threshold → degraded (warning, not blocking)."""
        from app.services import readiness as svc
        from concurrent.futures import Future

        monkeypatch.setattr(svc, "get_state", lambda: WorkerState.AUTHORIZED)
        monkeypatch.setattr(svc, "get_queue_depth", lambda: 0)
        monkeypatch.setattr(svc, "get_settings", _make_settings)

        async def _mock_mt5_global():
            return [
                svc.ReadinessCheck(check_id="global.mt5_terminal_connected", status=ReadinessStatus.PASS, blocking=True, user_message="OK", action=""),
                svc.ReadinessCheck(check_id="global.terminal_trade_allowed", status=ReadinessStatus.PASS, blocking=True, user_message="OK", action="", details={"trade_allowed": True}),
                svc.ReadinessCheck(check_id="global.account_trade_allowed", status=ReadinessStatus.PASS, blocking=True, user_message="OK", action="", details={"trade_allowed": True}),
            ]

        monkeypatch.setattr(svc, "_run_mt5_global_checks", _mock_mt5_global)

        si = _make_symbol_info()
        fake_mt5.symbol_info = lambda s: si
        fake_mt5.symbol_info_tick = lambda s: _make_tick(age_seconds=60)  # 60s > 30s threshold

        def _mock_submit(fn):
            fut = Future()
            try:
                fut.set_result(fn())
            except Exception as e:
                fut.set_exception(e)
            return fut

        monkeypatch.setattr(svc, "submit", _mock_submit)

        with patch("app.routes.execute._inflight_requests", 0):
            result = await svc.evaluate_readiness(symbol="EURUSD", direction="buy")

        assert result.overall_status == OverallStatus.DEGRADED
        tick_check = next(c for c in result.checks if c.check_id == "symbol.tick_freshness")
        assert tick_check.status == ReadinessStatus.WARN
        assert tick_check.blocking is False

    @pytest.mark.asyncio
    async def test_volume_out_of_range_gives_blocked(self, monkeypatch, fake_mt5):
        """Volume below minimum → blocked."""
        from app.services import readiness as svc
        from concurrent.futures import Future

        monkeypatch.setattr(svc, "get_state", lambda: WorkerState.AUTHORIZED)
        monkeypatch.setattr(svc, "get_queue_depth", lambda: 0)
        monkeypatch.setattr(svc, "get_settings", _make_settings)

        async def _mock_mt5_global():
            return [
                svc.ReadinessCheck(check_id="global.mt5_terminal_connected", status=ReadinessStatus.PASS, blocking=True, user_message="OK", action=""),
                svc.ReadinessCheck(check_id="global.terminal_trade_allowed", status=ReadinessStatus.PASS, blocking=True, user_message="OK", action="", details={"trade_allowed": True}),
                svc.ReadinessCheck(check_id="global.account_trade_allowed", status=ReadinessStatus.PASS, blocking=True, user_message="OK", action="", details={"trade_allowed": True}),
            ]

        monkeypatch.setattr(svc, "_run_mt5_global_checks", _mock_mt5_global)

        si = _make_symbol_info(volume_min=0.01)
        fake_mt5.symbol_info = lambda s: si
        fake_mt5.symbol_info_tick = lambda s: _make_tick(5)

        def _mock_submit(fn):
            fut = Future()
            try:
                fut.set_result(fn())
            except Exception as e:
                fut.set_exception(e)
            return fut

        monkeypatch.setattr(svc, "submit", _mock_submit)

        with patch("app.routes.execute._inflight_requests", 0):
            result = await svc.evaluate_readiness(symbol="EURUSD", direction="buy", volume=0.001)

        assert result.overall_status == OverallStatus.BLOCKED
        vol_check = next(c for c in result.checks if c.check_id == "symbol.volume_valid")
        assert vol_check.status == ReadinessStatus.FAIL


class TestNoSymbol:
    """Tests for readiness without symbol parameters."""

    @pytest.mark.asyncio
    async def test_no_symbol_returns_global_checks_only(self, monkeypatch):
        """When no symbol is provided, only global checks are returned."""
        from app.services import readiness as svc

        monkeypatch.setattr(svc, "get_state", lambda: WorkerState.AUTHORIZED)
        monkeypatch.setattr(svc, "get_queue_depth", lambda: 0)
        monkeypatch.setattr(svc, "get_settings", _make_settings)

        async def _mock_mt5_global():
            return [
                svc.ReadinessCheck(check_id="global.mt5_terminal_connected", status=ReadinessStatus.PASS, blocking=True, user_message="OK", action=""),
                svc.ReadinessCheck(check_id="global.terminal_trade_allowed", status=ReadinessStatus.PASS, blocking=True, user_message="OK", action="", details={"trade_allowed": True}),
                svc.ReadinessCheck(check_id="global.account_trade_allowed", status=ReadinessStatus.PASS, blocking=True, user_message="OK", action="", details={"trade_allowed": True}),
            ]

        monkeypatch.setattr(svc, "_run_mt5_global_checks", _mock_mt5_global)

        with patch("app.routes.execute._inflight_requests", 0):
            result = await svc.evaluate_readiness()

        symbol_checks = [c for c in result.checks if c.check_id.startswith("symbol.")]
        assert len(symbol_checks) == 0

    @pytest.mark.asyncio
    async def test_context_echoed(self, monkeypatch):
        """Request context fields are echoed back."""
        from app.services import readiness as svc

        monkeypatch.setattr(svc, "get_state", lambda: WorkerState.DISCONNECTED)
        monkeypatch.setattr(svc, "get_queue_depth", lambda: 0)
        monkeypatch.setattr(svc, "get_settings", _make_settings)

        with patch("app.routes.execute._inflight_requests", 0):
            result = await svc.evaluate_readiness(
                operation="buy", symbol="EURUSD", direction="buy", volume=0.1,
            )

        assert result.request_context.operation == "buy"
        assert result.request_context.symbol == "EURUSD"
        assert result.request_context.direction == "buy"
        assert result.request_context.volume == 0.1
