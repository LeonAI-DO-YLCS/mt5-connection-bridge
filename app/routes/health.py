"""
MT5 Bridge — GET /health endpoint.

Returns the terminal connection status, broker session validity, and latency.
"""

from __future__ import annotations

import time

from fastapi import APIRouter

from ..models.health import HealthStatus
from ..mt5_worker import WorkerState, get_state, submit

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """Report MT5 terminal connection status.

    Always returns 200 — even if the terminal is disconnected —
    so that upstream readiness probes can differentiate between
    "bridge is up but MT5 is down" vs "bridge is down".
    """
    state = get_state()

    if state not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
        return HealthStatus(connected=False)

    try:
        start = time.perf_counter()
        account_info = await _get_account_info()
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        if account_info is None:
            return HealthStatus(connected=True, authorized=False)

        return HealthStatus(
            connected=True,
            authorized=True,
            broker=getattr(account_info, "company", None),
            account_id=getattr(account_info, "login", None),
            balance=getattr(account_info, "balance", None),
            server_time_offset=getattr(account_info, "server_time", None),
            latency_ms=elapsed_ms,
        )
    except Exception:
        return HealthStatus(connected=False)


async def _get_account_info():
    """Submit ``mt5.account_info()`` to the worker queue."""
    import asyncio

    def _call():
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
        return mt5.account_info()

    loop = asyncio.get_running_loop()
    fut = submit(_call)
    return await asyncio.wrap_future(fut, loop=loop)
