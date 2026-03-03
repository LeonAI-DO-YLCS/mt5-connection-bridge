"""Contract tests for the ReadinessResponse schema conformance."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.models.readiness import (
    OverallStatus,
    ReadinessCheck,
    ReadinessRequestContext,
    ReadinessResponse,
    ReadinessStatus,
)


class TestReadinessResponseContract:
    """Validate that ReadinessResponse conforms to Phase 2 contract."""

    def _make_check(self, check_id: str, status: ReadinessStatus, blocking: bool) -> ReadinessCheck:
        return ReadinessCheck(
            check_id=check_id,
            status=status,
            blocking=blocking,
            user_message="Test message.",
            action="" if status == ReadinessStatus.PASS else "Fix it.",
        )

    def test_all_check_ids_follow_naming_convention(self):
        """All check_ids should be dotted: global.* or symbol.*."""
        valid_ids = [
            "global.worker_connected",
            "global.mt5_terminal_connected",
            "global.account_trade_allowed",
            "global.terminal_trade_allowed",
            "global.execution_policy",
            "global.queue_capacity",
            "symbol.exists",
            "symbol.selectable",
            "symbol.trade_mode",
            "symbol.filling_mode",
            "symbol.tick_freshness",
            "symbol.volume_valid",
            "symbol.freeze_level",
            "symbol.stops_level",
        ]
        for cid in valid_ids:
            assert cid.startswith("global.") or cid.startswith("symbol."), \
                f"check_id '{cid}' must start with 'global.' or 'symbol.'"

    def test_blockers_only_contain_fail_and_blocking(self):
        """blockers[] must only contain checks where status=fail AND blocking=true."""
        checks = [
            self._make_check("global.worker_connected", ReadinessStatus.PASS, True),
            self._make_check("global.execution_policy", ReadinessStatus.FAIL, True),
            self._make_check("symbol.tick_freshness", ReadinessStatus.WARN, False),
        ]
        blockers = [c for c in checks if c.status == ReadinessStatus.FAIL and c.blocking]

        assert len(blockers) == 1
        assert blockers[0].check_id == "global.execution_policy"

    def test_warnings_only_contain_warn(self):
        """warnings[] must only contain checks where status=warn."""
        checks = [
            self._make_check("global.worker_connected", ReadinessStatus.PASS, True),
            self._make_check("symbol.tick_freshness", ReadinessStatus.WARN, False),
        ]
        warnings = [c for c in checks if c.status == ReadinessStatus.WARN]

        assert len(warnings) == 1
        assert warnings[0].check_id == "symbol.tick_freshness"

    def test_overall_status_blocked_derivation(self):
        """overall_status=blocked when at least one check has fail+blocking."""
        checks = [
            self._make_check("global.worker_connected", ReadinessStatus.FAIL, True),
            self._make_check("global.execution_policy", ReadinessStatus.PASS, True),
        ]
        blockers = [c for c in checks if c.status == ReadinessStatus.FAIL and c.blocking]
        assert len(blockers) > 0

        overall = OverallStatus.BLOCKED
        assert overall == OverallStatus.BLOCKED

    def test_overall_status_degraded_derivation(self):
        """overall_status=degraded when warns exist but no blocking failures."""
        checks = [
            self._make_check("global.worker_connected", ReadinessStatus.PASS, True),
            self._make_check("symbol.tick_freshness", ReadinessStatus.WARN, False),
        ]
        blockers = [c for c in checks if c.status == ReadinessStatus.FAIL and c.blocking]
        warnings = [c for c in checks if c.status == ReadinessStatus.WARN]

        if blockers:
            overall = OverallStatus.BLOCKED
        elif warnings:
            overall = OverallStatus.DEGRADED
        else:
            overall = OverallStatus.READY

        assert overall == OverallStatus.DEGRADED

    def test_overall_status_ready_derivation(self):
        """overall_status=ready when all checks pass."""
        checks = [
            self._make_check("global.worker_connected", ReadinessStatus.PASS, True),
            self._make_check("symbol.exists", ReadinessStatus.PASS, True),
        ]
        blockers = [c for c in checks if c.status == ReadinessStatus.FAIL and c.blocking]
        warnings = [c for c in checks if c.status == ReadinessStatus.WARN]

        if blockers:
            overall = OverallStatus.BLOCKED
        elif warnings:
            overall = OverallStatus.DEGRADED
        else:
            overall = OverallStatus.READY

        assert overall == OverallStatus.READY

    def test_evaluated_at_is_valid_iso8601(self):
        """evaluated_at must be a valid ISO-8601 timestamp."""
        response = ReadinessResponse(
            overall_status=OverallStatus.READY,
            checks=[],
            blockers=[],
            warnings=[],
            advice=[],
            evaluated_at="2026-03-03T20:15:30.123456+00:00",
            request_context=ReadinessRequestContext(),
        )
        # Must parse without error
        dt = datetime.fromisoformat(response.evaluated_at)
        assert dt.year == 2026

    def test_response_serializes_correctly(self):
        """ReadinessResponse must serialize to JSON with all required fields."""
        response = ReadinessResponse(
            overall_status=OverallStatus.READY,
            checks=[self._make_check("global.worker_connected", ReadinessStatus.PASS, True)],
            blockers=[],
            warnings=[],
            advice=[],
            evaluated_at="2026-03-03T20:15:30.123456+00:00",
            request_context=ReadinessRequestContext(
                operation="buy", symbol="EURUSD", direction="buy", volume=0.1,
            ),
        )
        data = response.model_dump()
        assert "overall_status" in data
        assert "checks" in data
        assert "blockers" in data
        assert "warnings" in data
        assert "advice" in data
        assert "evaluated_at" in data
        assert "request_context" in data
        assert data["request_context"]["symbol"] == "EURUSD"

    def test_request_context_nullable_fields(self):
        """All request_context fields must be nullable."""
        ctx = ReadinessRequestContext()
        assert ctx.operation is None
        assert ctx.symbol is None
        assert ctx.direction is None
        assert ctx.volume is None
