"""MT5 Bridge — Readiness evaluation service (Phase 2).

Aggregates all global and symbol-specific trade prerequisites into a
structured ``ReadinessResponse``.  The route delegates here; all check
logic is independently testable.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

from ..config import get_settings
from ..models.readiness import (
    OverallStatus,
    ReadinessCheck,
    ReadinessRequestContext,
    ReadinessResponse,
    ReadinessStatus,
)
from ..mt5_worker import WorkerState, get_queue_depth, get_state, submit

logger = logging.getLogger("mt5_bridge.readiness")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def evaluate_readiness(
    operation: str | None = None,
    symbol: str | None = None,
    direction: str | None = None,
    volume: float | None = None,
) -> ReadinessResponse:
    """Run all readiness checks and return a structured response."""

    checks: list[ReadinessCheck] = []
    settings = get_settings()

    # ── Phase 1: Global checks (always run) ──────────────────────────────

    worker_state = get_state()
    worker_ok = worker_state in (WorkerState.AUTHORIZED, WorkerState.PROCESSING)

    checks.append(_check_worker_connected(worker_state))

    # MT5-dependent global checks — run inside worker thread if connected
    if worker_ok:
        try:
            mt5_global = await _run_mt5_global_checks()
            checks.extend(mt5_global)
        except Exception:
            logger.exception("Failed to run MT5 global checks")
            checks.extend(_unknown_mt5_global_checks())
    else:
        checks.extend(_unknown_mt5_global_checks())

    checks.append(_check_execution_policy(settings))
    checks.append(_check_queue_capacity(settings))

    # ── Phase 2: Symbol checks (when symbol provided) ────────────────────

    if symbol:
        if worker_ok:
            try:
                symbol_checks = await _run_mt5_symbol_checks(
                    symbol, direction, volume, operation, settings,
                )
                checks.extend(symbol_checks)
            except Exception:
                logger.exception("Failed to run MT5 symbol checks for %s", symbol)
                checks.extend(_unknown_symbol_checks())
        else:
            checks.extend(_unknown_symbol_checks())

    # ── Aggregate ────────────────────────────────────────────────────────

    blockers = [c for c in checks if c.status == ReadinessStatus.FAIL and c.blocking]
    warnings = [c for c in checks if c.status == ReadinessStatus.WARN]
    advice = [c for c in checks if c.status == ReadinessStatus.PASS and c.action]

    if blockers:
        overall = OverallStatus.BLOCKED
    elif warnings:
        overall = OverallStatus.DEGRADED
    else:
        overall = OverallStatus.READY

    return ReadinessResponse(
        overall_status=overall,
        checks=checks,
        blockers=blockers,
        warnings=warnings,
        advice=advice,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
        request_context=ReadinessRequestContext(
            operation=operation,
            symbol=symbol,
            direction=direction,
            volume=volume,
        ),
    )


# ---------------------------------------------------------------------------
# Global checks
# ---------------------------------------------------------------------------

def _check_worker_connected(state: WorkerState) -> ReadinessCheck:
    ok = state in (WorkerState.AUTHORIZED, WorkerState.PROCESSING)
    if ok:
        return ReadinessCheck(
            check_id="global.worker_connected",
            status=ReadinessStatus.PASS,
            blocking=True,
            user_message="Bridge worker is connected and authorized.",
            action="",
            details={"worker_state": state.value},
        )
    return ReadinessCheck(
        check_id="global.worker_connected",
        status=ReadinessStatus.FAIL,
        blocking=True,
        user_message="Bridge worker is not connected — start or restart the bridge to proceed.",
        action="Start the MT5 bridge worker or restart the bridge service.",
        details={"worker_state": state.value},
    )


def _check_execution_policy(settings: Any) -> ReadinessCheck:
    if settings.execution_enabled:
        return ReadinessCheck(
            check_id="global.execution_policy",
            status=ReadinessStatus.PASS,
            blocking=True,
            user_message="Execution policy is enabled.",
            action="",
            details={"execution_enabled": True},
        )
    return ReadinessCheck(
        check_id="global.execution_policy",
        status=ReadinessStatus.FAIL,
        blocking=True,
        user_message="Execution disabled by policy (EXECUTION_ENABLED=false).",
        action="Enable execution via environment config or the dashboard toggle.",
        details={"execution_enabled": False},
    )


def _check_queue_capacity(settings: Any) -> ReadinessCheck:
    from ..routes.execute import _inflight_requests

    pending = _inflight_requests + get_queue_depth()
    threshold = settings.multi_trade_overload_queue_threshold
    if pending < threshold:
        return ReadinessCheck(
            check_id="global.queue_capacity",
            status=ReadinessStatus.PASS,
            blocking=True,
            user_message="Execution queue has capacity.",
            action="",
            details={"pending": pending, "threshold": threshold},
        )
    return ReadinessCheck(
        check_id="global.queue_capacity",
        status=ReadinessStatus.FAIL,
        blocking=True,
        user_message="Execution queue is overloaded. Wait for current trades to complete.",
        action="Wait for the current trade(s) to finish before submitting more.",
        details={"pending": pending, "threshold": threshold},
    )


def _unknown_mt5_global_checks() -> list[ReadinessCheck]:
    """Return unknown-status checks when the worker is unavailable."""
    return [
        ReadinessCheck(
            check_id="global.mt5_terminal_connected",
            status=ReadinessStatus.UNKNOWN,
            blocking=True,
            user_message="Cannot determine MT5 terminal status — worker is not connected.",
            action="Connect the bridge worker first.",
        ),
        ReadinessCheck(
            check_id="global.account_trade_allowed",
            status=ReadinessStatus.UNKNOWN,
            blocking=True,
            user_message="Cannot determine account trade permission — worker is not connected.",
            action="Connect the bridge worker first.",
        ),
        ReadinessCheck(
            check_id="global.terminal_trade_allowed",
            status=ReadinessStatus.UNKNOWN,
            blocking=True,
            user_message="Cannot determine terminal trade permission — worker is not connected.",
            action="Connect the bridge worker first.",
        ),
    ]


async def _run_mt5_global_checks() -> list[ReadinessCheck]:
    """Fetch terminal_info and account_info via the MT5 worker thread."""

    def _fetch() -> tuple[Any, Any]:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]

        return mt5.terminal_info(), mt5.account_info()

    loop = asyncio.get_running_loop()
    terminal_info, account_info = await asyncio.wrap_future(submit(_fetch), loop=loop)

    checks: list[ReadinessCheck] = []

    # Terminal connection
    if terminal_info is not None:
        checks.append(ReadinessCheck(
            check_id="global.mt5_terminal_connected",
            status=ReadinessStatus.PASS,
            blocking=True,
            user_message="MT5 terminal connection is active.",
            action="",
        ))
        # Terminal trade allowed
        trade_allowed = bool(getattr(terminal_info, "trade_allowed", False))
        if trade_allowed:
            checks.append(ReadinessCheck(
                check_id="global.terminal_trade_allowed",
                status=ReadinessStatus.PASS,
                blocking=True,
                user_message="Terminal trading is enabled.",
                action="",
                details={"trade_allowed": True},
            ))
        else:
            checks.append(ReadinessCheck(
                check_id="global.terminal_trade_allowed",
                status=ReadinessStatus.FAIL,
                blocking=True,
                user_message="Terminal trading is disabled. Enable it in MT5 terminal settings.",
                action="Open MT5 → Tools → Options → Expert Advisors → Allow Algorithmic Trading.",
                details={"trade_allowed": False},
            ))
    else:
        checks.append(ReadinessCheck(
            check_id="global.mt5_terminal_connected",
            status=ReadinessStatus.FAIL,
            blocking=True,
            user_message="MT5 terminal is not responding. Check that the terminal is running.",
            action="Launch the MetaTrader 5 terminal or restart it.",
        ))
        checks.append(ReadinessCheck(
            check_id="global.terminal_trade_allowed",
            status=ReadinessStatus.UNKNOWN,
            blocking=True,
            user_message="Cannot determine terminal trade permission — terminal not responding.",
            action="Launch the MetaTrader 5 terminal first.",
        ))

    # Account trade allowed
    if account_info is not None:
        trade_allowed = bool(getattr(account_info, "trade_allowed", False))
        if trade_allowed:
            checks.append(ReadinessCheck(
                check_id="global.account_trade_allowed",
                status=ReadinessStatus.PASS,
                blocking=True,
                user_message="Account trading is enabled.",
                action="",
                details={"trade_allowed": True},
            ))
        else:
            checks.append(ReadinessCheck(
                check_id="global.account_trade_allowed",
                status=ReadinessStatus.FAIL,
                blocking=True,
                user_message="Account trading is disabled by the broker.",
                action="Contact your broker to enable trading on this account.",
                details={"trade_allowed": False},
            ))
    else:
        checks.append(ReadinessCheck(
            check_id="global.account_trade_allowed",
            status=ReadinessStatus.UNKNOWN,
            blocking=True,
            user_message="Cannot determine account trade permission — account info unavailable.",
            action="Check MT5 terminal connection.",
        ))

    return checks


# ---------------------------------------------------------------------------
# Symbol checks
# ---------------------------------------------------------------------------

def _unknown_symbol_checks() -> list[ReadinessCheck]:
    """Return unknown-status checks when symbol evaluation is impossible."""
    return [
        ReadinessCheck(
            check_id="symbol.exists",
            status=ReadinessStatus.UNKNOWN,
            blocking=True,
            user_message="Cannot evaluate symbol — worker is not connected.",
            action="Connect the bridge worker first.",
        ),
    ]


async def _run_mt5_symbol_checks(
    symbol: str,
    direction: str | None,
    volume: float | None,
    operation: str | None,
    settings: Any,
) -> list[ReadinessCheck]:
    """Run all symbol-specific checks inside the MT5 worker thread."""

    def _fetch() -> tuple[Any, Any]:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]

        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol) if info is not None else None
        return info, tick

    loop = asyncio.get_running_loop()
    symbol_info, tick_info = await asyncio.wrap_future(submit(_fetch), loop=loop)

    checks: list[ReadinessCheck] = []

    # ── symbol.exists ────────────────────────────────────────────────────
    if symbol_info is None:
        checks.append(ReadinessCheck(
            check_id="symbol.exists",
            status=ReadinessStatus.FAIL,
            blocking=True,
            user_message=f"Symbol '{symbol}' is not recognized by MT5.",
            action="Verify the symbol name or check the broker's symbol catalog.",
            details={"symbol": symbol},
        ))
        # Short-circuit: remaining symbol checks cannot proceed
        for cid in ("symbol.selectable", "symbol.trade_mode", "symbol.filling_mode",
                     "symbol.tick_freshness", "symbol.volume_valid"):
            checks.append(ReadinessCheck(
                check_id=cid,
                status=ReadinessStatus.UNKNOWN,
                blocking=True if cid != "symbol.tick_freshness" else False,
                user_message=f"Not evaluated — symbol '{symbol}' not found.",
                action="Fix the symbol.exists check first.",
            ))
        return checks

    checks.append(ReadinessCheck(
        check_id="symbol.exists",
        status=ReadinessStatus.PASS,
        blocking=True,
        user_message=f"Symbol '{symbol}' is available.",
        action="",
        details={"symbol": symbol},
    ))

    # ── symbol.selectable ────────────────────────────────────────────────
    visible = bool(getattr(symbol_info, "visible", True))
    if visible:
        checks.append(ReadinessCheck(
            check_id="symbol.selectable",
            status=ReadinessStatus.PASS,
            blocking=True,
            user_message=f"Symbol '{symbol}' is visible in Market Watch.",
            action="",
        ))
    else:
        checks.append(ReadinessCheck(
            check_id="symbol.selectable",
            status=ReadinessStatus.WARN,
            blocking=False,
            user_message=f"Symbol '{symbol}' is not in Market Watch — will be auto-selected.",
            action="The bridge will attempt to select it automatically.",
            details={"visible": False},
        ))

    # ── symbol.trade_mode ────────────────────────────────────────────────
    from ..mappers.trade_mapper import validate_trade_mode

    effective_direction = direction or operation
    if effective_direction:
        trade_mode_error = validate_trade_mode(symbol_info, effective_direction)
        if trade_mode_error is None:
            checks.append(ReadinessCheck(
                check_id="symbol.trade_mode",
                status=ReadinessStatus.PASS,
                blocking=True,
                user_message=f"Trade mode allows '{effective_direction}' for {symbol}.",
                action="",
                details={"trade_mode": int(getattr(symbol_info, "trade_mode", 4))},
            ))
        else:
            checks.append(ReadinessCheck(
                check_id="symbol.trade_mode",
                status=ReadinessStatus.FAIL,
                blocking=True,
                user_message=trade_mode_error,
                action="Select a different action or choose a symbol that allows this trade type.",
                details={"trade_mode": int(getattr(symbol_info, "trade_mode", 4))},
            ))
    else:
        checks.append(ReadinessCheck(
            check_id="symbol.trade_mode",
            status=ReadinessStatus.UNKNOWN,
            blocking=False,
            user_message="Trade mode not evaluated — no direction specified.",
            action="Provide a direction (buy/sell) to evaluate trade mode compatibility.",
        ))

    # ── symbol.filling_mode ──────────────────────────────────────────────
    filling_bitmask = int(getattr(symbol_info, "filling_mode", 0) or 0)
    supported: list[str] = []
    if filling_bitmask & 1:
        supported.append("FOK")
    if filling_bitmask & 2:
        supported.append("IOC")
    if not supported:
        supported.append("RETURN")

    checks.append(ReadinessCheck(
        check_id="symbol.filling_mode",
        status=ReadinessStatus.PASS,
        blocking=True,
        user_message=f"Supported filling modes: {', '.join(supported)}.",
        action="",
        details={"filling_mode": filling_bitmask, "supported": supported},
    ))

    # ── symbol.tick_freshness ────────────────────────────────────────────
    is_market_order = operation in ("buy", "sell", "cover", "short", None)
    if tick_info is not None and is_market_order:
        last_tick_time = int(getattr(tick_info, "time", 0) or 0)
        now = int(time.time())
        age_seconds = now - last_tick_time
        threshold = settings.tick_freshness_threshold_seconds

        if age_seconds <= threshold:
            checks.append(ReadinessCheck(
                check_id="symbol.tick_freshness",
                status=ReadinessStatus.PASS,
                blocking=False,
                user_message=f"Tick data for {symbol} is {age_seconds}s old (within {threshold}s threshold).",
                action="",
                details={"last_tick_age_seconds": age_seconds, "threshold_seconds": threshold},
            ))
        else:
            checks.append(ReadinessCheck(
                check_id="symbol.tick_freshness",
                status=ReadinessStatus.WARN,
                blocking=False,
                user_message=f"Tick data for {symbol} is {age_seconds} seconds old. Market price may be stale.",
                action="Acknowledge stale price or wait for a fresh tick before submitting.",
                details={"last_tick_age_seconds": age_seconds, "threshold_seconds": threshold},
            ))
    elif tick_info is None and is_market_order:
        checks.append(ReadinessCheck(
            check_id="symbol.tick_freshness",
            status=ReadinessStatus.WARN,
            blocking=False,
            user_message=f"No tick data available for {symbol}. Market price is unknown.",
            action="Wait for the market to open or check the symbol in MT5.",
            details={"last_tick_age_seconds": None, "threshold_seconds": settings.tick_freshness_threshold_seconds},
        ))

    # ── symbol.volume_valid ──────────────────────────────────────────────
    if volume is not None:
        vol_min = float(getattr(symbol_info, "volume_min", 0.0) or 0.0)
        vol_max = float(getattr(symbol_info, "volume_max", 0.0) or 0.0)
        vol_step = float(getattr(symbol_info, "volume_step", 0.0) or 0.0)

        volume_ok = True
        volume_msg_parts: list[str] = []

        if volume < vol_min:
            volume_ok = False
            volume_msg_parts.append(f"Volume {volume} is below minimum {vol_min}.")
        elif vol_max > 0 and volume > vol_max:
            volume_ok = False
            volume_msg_parts.append(f"Volume {volume} exceeds maximum {vol_max}.")

        if vol_step > 0:
            from decimal import Decimal
            remainder = float((Decimal(str(volume)) - Decimal(str(vol_min))) % Decimal(str(vol_step)))
            if abs(remainder) > 1e-10:
                volume_ok = False
                volume_msg_parts.append(f"Volume {volume} does not align with step size {vol_step}.")

        if volume_ok:
            checks.append(ReadinessCheck(
                check_id="symbol.volume_valid",
                status=ReadinessStatus.PASS,
                blocking=True,
                user_message=f"Volume {volume} is valid for {symbol}.",
                action="",
                details={"volume": volume, "min": vol_min, "max": vol_max, "step": vol_step},
            ))
        else:
            checks.append(ReadinessCheck(
                check_id="symbol.volume_valid",
                status=ReadinessStatus.FAIL,
                blocking=True,
                user_message=" ".join(volume_msg_parts),
                action=f"Adjust volume to be between {vol_min} and {vol_max} in steps of {vol_step}.",
                details={"volume": volume, "min": vol_min, "max": vol_max, "step": vol_step},
            ))

    return checks
