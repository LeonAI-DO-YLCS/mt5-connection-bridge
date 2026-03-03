from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone

from fastapi import APIRouter

from ..main import app_started_at, app_version, get_runtime_policy_source, settings, symbol_map
from ..models.diagnostics import RuntimeDiagnostics, SymbolDiagnostic, SymbolsDiagnosticsResponse
from ..mt5_worker import WorkerState, get_queue_depth, get_state, submit
from ..runtime_state import resolve_runtime_state_path

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


def _fingerprint() -> str:
    payload = {
        "mt5_bridge_port": settings.mt5_bridge_port,
        "mt5_server": settings.mt5_server,
        "log_level": settings.log_level,
        "execution_enabled": settings.execution_enabled,
        "metrics_retention_days": settings.metrics_retention_days,
        "multi_trade_overload_queue_threshold": settings.multi_trade_overload_queue_threshold,
        "symbol_count": len(symbol_map),
        "symbols_config_path": str(settings.symbols_config_path),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@router.get("/runtime", response_model=RuntimeDiagnostics, summary="Runtime diagnostics snapshot")
async def diagnostics_runtime() -> RuntimeDiagnostics:
    now = datetime.now(timezone.utc)
    runtime_path = resolve_runtime_state_path(settings)
    state = get_state()
    return RuntimeDiagnostics(
        app_version=app_version,
        started_at=app_started_at.isoformat(),
        uptime_seconds=max((now - app_started_at).total_seconds(), 0.0),
        worker_state=state.value,
        queue_depth=get_queue_depth(),
        mt5_connected=state in (WorkerState.AUTHORIZED, WorkerState.PROCESSING),
        execution_enabled=settings.execution_enabled,
        execution_policy_source=get_runtime_policy_source(),
        symbol_count=len(symbol_map),
        symbols_config_path=str(settings.symbols_config_path),
        runtime_state_path=str(runtime_path),
        runtime_state_exists=runtime_path.exists(),
        config_fingerprint=_fingerprint(),
    )


def _build_disconnected_diagnostics(state: WorkerState) -> SymbolsDiagnosticsResponse:
    generated_at = datetime.now(timezone.utc).isoformat()
    items = [
        SymbolDiagnostic(
            ticker=ticker,
            configured_mt5_symbol=entry.mt5_symbol,
            broker_symbol_found=False,
            symbol_info_available=False,
            visible=None,
            reason_code="MT5_DISCONNECTED",
            reason=f"Worker state is {state.value}; broker symbol checks unavailable.",
            suggested_matches=[],
        )
        for ticker, entry in sorted(symbol_map.items())
    ]
    return SymbolsDiagnosticsResponse(
        generated_at=generated_at,
        worker_state=state.value,
        configured_symbols=len(symbol_map),
        checked_count=len(items),
        items=items,
    )


@router.get("/symbols", response_model=SymbolsDiagnosticsResponse, summary="Symbol resolution diagnostics")
async def diagnostics_symbols() -> SymbolsDiagnosticsResponse:
    state = get_state()
    if state not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
        return _build_disconnected_diagnostics(state)

    def _collect() -> list[SymbolDiagnostic]:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]

        broker_symbols = mt5.symbols_get() or []
        broker_names = [str(getattr(sym, "name", "")) for sym in broker_symbols if getattr(sym, "name", None)]
        broker_name_set = set(broker_names)
        broker_name_lower = {name.lower(): name for name in broker_names}
        items: list[SymbolDiagnostic] = []

        for ticker, entry in sorted(symbol_map.items()):
            configured = entry.mt5_symbol
            info = mt5.symbol_info(configured)
            exact_found = configured in broker_name_set
            lower_match = broker_name_lower.get(configured.lower())
            suggested = sorted(
                [
                    name
                    for name in broker_names
                    if configured.lower() in name.lower() or name.lower() in configured.lower()
                ]
            )[:5]

            if info is not None:
                visible = bool(getattr(info, "visible", False))
                items.append(
                    SymbolDiagnostic(
                        ticker=ticker,
                        configured_mt5_symbol=configured,
                        broker_symbol_found=True,
                        symbol_info_available=True,
                        visible=visible,
                        reason_code="OK" if visible else "SYMBOL_NOT_VISIBLE",
                        reason="Symbol resolved and visible in Market Watch."
                        if visible
                        else "Symbol resolved but is not visible in Market Watch.",
                        suggested_matches=[],
                    )
                )
                continue

            if exact_found:
                items.append(
                    SymbolDiagnostic(
                        ticker=ticker,
                        configured_mt5_symbol=configured,
                        broker_symbol_found=True,
                        symbol_info_available=False,
                        visible=None,
                        reason_code="BROKER_SYMBOL_UNAVAILABLE",
                        reason="Broker lists the symbol but symbol_info lookup failed.",
                        suggested_matches=[],
                    )
                )
                continue

            if lower_match is not None:
                items.append(
                    SymbolDiagnostic(
                        ticker=ticker,
                        configured_mt5_symbol=configured,
                        broker_symbol_found=True,
                        symbol_info_available=False,
                        visible=None,
                        reason_code="SYMBOL_CASE_MISMATCH",
                        reason=f"Case mismatch. Broker symbol is '{lower_match}'.",
                        suggested_matches=[lower_match],
                    )
                )
                continue

            if suggested:
                items.append(
                    SymbolDiagnostic(
                        ticker=ticker,
                        configured_mt5_symbol=configured,
                        broker_symbol_found=False,
                        symbol_info_available=False,
                        visible=None,
                        reason_code="SYMBOL_ALIAS_CANDIDATES",
                        reason="Configured symbol was not found exactly. Possible aliases detected.",
                        suggested_matches=suggested,
                    )
                )
                continue

            items.append(
                SymbolDiagnostic(
                    ticker=ticker,
                    configured_mt5_symbol=configured,
                    broker_symbol_found=False,
                    symbol_info_available=False,
                    visible=None,
                    reason_code="SYMBOL_NOT_IN_BROKER",
                    reason="Configured symbol does not exist in broker symbol list.",
                    suggested_matches=[],
                )
            )

        return items

    try:
        loop = asyncio.get_running_loop()
        items = await asyncio.wrap_future(submit(_collect), loop=loop)
    except Exception:
        return _build_disconnected_diagnostics(get_state())

    return SymbolsDiagnosticsResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        worker_state=get_state().value,
        configured_symbols=len(symbol_map),
        checked_count=len(items),
        items=items,
    )
