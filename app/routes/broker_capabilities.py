"""MT5 Bridge — GET /broker-capabilities and POST /broker-capabilities/refresh.

Provides a single, cached endpoint that exposes the full broker symbol catalog
with category/trade-mode/filling-mode metadata and account/terminal trade flags.

Cache strategy:
  - In-memory module-level dict with configurable TTL (CAPABILITIES_CACHE_TTL_SECONDS)
  - Invalidated on MT5 worker reconnect via invalidate_capabilities_cache()
  - Manually refreshable via POST /broker-capabilities/refresh
"""

from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status

from ..main import settings, symbol_map
from ..models.broker_capabilities import BrokerCapabilitiesResponse
from ..models.broker_symbol import BrokerSymbol
from ..mt5_worker import WorkerState, get_state, submit

logger = logging.getLogger("mt5_bridge.broker_capabilities")
router = APIRouter(tags=["broker_capabilities"])

# ---------------------------------------------------------------------------
# Module-level cache (T023)
# ---------------------------------------------------------------------------
_cache_lock = threading.Lock()
_capabilities_cache: BrokerCapabilitiesResponse | None = None
_cache_fetched_at: datetime | None = None


# ---------------------------------------------------------------------------
# Cache invalidation hook (T030) — called by mt5_worker on reconnect
# ---------------------------------------------------------------------------
def invalidate_capabilities_cache() -> None:
    """Clear the capabilities cache so the next request re-fetches from MT5.

    Called by the MT5 worker when the connection transitions to AUTHORIZED
    (i.e., after a reconnect). This ensures stale symbol data is not served
    after a broker session change.
    """
    global _capabilities_cache, _cache_fetched_at
    with _cache_lock:
        _capabilities_cache = None
        _cache_fetched_at = None
    logger.info("Broker capabilities cache invalidated.")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
_TRADE_MODE_LABELS: dict[int, str] = {
    0: "Disabled",
    1: "Long Only",
    2: "Short Only",
    3: "Close Only",
    4: "Full",
}


def _decode_filling_modes(bitmask: int) -> list[str]:
    """Decode filling_mode bitmask into human-readable list."""
    if bitmask & 1:  # bit 0 = FOK
        modes = ["FOK"]
        if bitmask & 2:
            modes.append("IOC")
        return modes
    if bitmask & 2:  # bit 1 = IOC only
        return ["IOC"]
    return ["RETURN"]  # neither bit → RETURN only


def _parse_symbol_path(path: str | None) -> tuple[str, str]:
    """Parse MT5 symbol path into (category, subcategory).

    Normalizes both \\ and / separators. Returns ("Other", "") for empty paths.
    """
    if not path:
        return ("Other", "")
    segments = [s for s in path.replace("\\", "/").split("/") if s]
    category = segments[0] if segments else "Other"
    subcategory = segments[1] if len(segments) > 1 else ""
    return (category, subcategory)


def _build_capabilities(symbols_mt5: Any, terminal_info: Any, account_info: Any) -> BrokerCapabilitiesResponse:
    """Build BrokerCapabilitiesResponse from raw MT5 data."""
    configured_mt5_symbols = {s.mt5_symbol for s in symbol_map.values()}
    fetched_at = datetime.now(timezone.utc).isoformat()

    symbols: list[BrokerSymbol] = []
    categories: dict[str, set[str]] = {}

    for s in symbols_mt5:
        name = getattr(s, "name", "")
        raw_path = getattr(s, "path", "")
        category, subcategory = _parse_symbol_path(raw_path)

        # Build category tree
        if category not in categories:
            categories[category] = set()
        if subcategory:
            categories[category].add(subcategory)

        raw_trade_mode = getattr(s, "trade_mode", 4)
        try:
            trade_mode_int = int(raw_trade_mode)
        except (TypeError, ValueError):
            trade_mode_int = 4

        raw_filling = getattr(s, "filling_mode", 0)
        try:
            filling_bitmask = int(raw_filling or 0)
        except (TypeError, ValueError):
            filling_bitmask = 0

        symbols.append(
            BrokerSymbol(
                name=name,
                description=getattr(s, "description", ""),
                path=raw_path,
                category=category,
                subcategory=subcategory,
                spread=int(getattr(s, "spread", 0) or 0),
                digits=int(getattr(s, "digits", 0) or 0),
                volume_min=float(getattr(s, "volume_min", 0.0) or 0.0),
                volume_max=float(getattr(s, "volume_max", 0.0) or 0.0),
                volume_step=float(getattr(s, "volume_step", 0.01) or 0.01),
                trade_mode=trade_mode_int,
                trade_mode_label=_TRADE_MODE_LABELS.get(trade_mode_int, "Full"),
                filling_mode=filling_bitmask,
                supported_filling_modes=_decode_filling_modes(filling_bitmask),
                visible=bool(getattr(s, "visible", True)),
                is_configured=name in configured_mt5_symbols,
            )
        )

    # Build clean category tree dict: {category: sorted_subcategories}
    clean_categories = {cat: sorted(list(subs)) for cat, subs in categories.items()}

    account_trade_allowed = bool(getattr(account_info, "trade_allowed", True)) if account_info else True
    terminal_trade_allowed = bool(getattr(terminal_info, "trade_allowed", True)) if terminal_info else True

    return BrokerCapabilitiesResponse(
        account_trade_allowed=account_trade_allowed,
        terminal_trade_allowed=terminal_trade_allowed,
        symbol_count=len(symbols),
        symbols=symbols,
        categories=clean_categories,
        fetched_at=fetched_at,
    )


# ---------------------------------------------------------------------------
# MT5 fetch function (T024)
# ---------------------------------------------------------------------------
def _fetch_capabilities_from_mt5() -> BrokerCapabilitiesResponse:
    """Fetch full broker capabilities from MT5. Runs inside MT5 worker thread."""
    import MetaTrader5 as mt5  # type: ignore[import-untyped]

    symbols_mt5 = mt5.symbols_get()
    if symbols_mt5 is None:
        err = mt5.last_error()
        if err[0] == 1:  # No symbols — treat as empty
            symbols_mt5 = []
        else:
            raise RuntimeError(f"Failed to fetch symbols from MT5: {err}")

    terminal_info = mt5.terminal_info()
    account_info = mt5.account_info()

    return _build_capabilities(symbols_mt5, terminal_info, account_info)


def _get_or_refresh_cache() -> BrokerCapabilitiesResponse:
    """Return cached capabilities or fetch fresh data if TTL expired. Thread-safe."""
    global _capabilities_cache, _cache_fetched_at

    with _cache_lock:
        now = datetime.now(timezone.utc)
        ttl_seconds = getattr(settings, "capabilities_cache_ttl_seconds", 60)

        if (
            _capabilities_cache is not None
            and _cache_fetched_at is not None
            and (now - _cache_fetched_at).total_seconds() < ttl_seconds
        ):
            return _capabilities_cache

    # Cache miss — fetch outside lock to avoid blocking other requests
    result = _fetch_capabilities_from_mt5()

    with _cache_lock:
        _capabilities_cache = result
        _cache_fetched_at = datetime.now(timezone.utc)

    return result


def _refresh_cache_from_mt5() -> BrokerCapabilitiesResponse:
    """Force-refresh cache from MT5 while preserving previous cache on failure."""
    global _capabilities_cache, _cache_fetched_at

    result = _fetch_capabilities_from_mt5()
    with _cache_lock:
        _capabilities_cache = result
        _cache_fetched_at = datetime.now(timezone.utc)
    return result


# ---------------------------------------------------------------------------
# Routes (T025, T026)
# ---------------------------------------------------------------------------
@router.get(
    "/broker-capabilities",
    response_model=BrokerCapabilitiesResponse,
    summary="Get full broker symbol catalog with capabilities",
    description=(
        "Returns the complete live broker symbol catalog — derived from MT5 directly — "
        "with category hierarchy, trade mode, filling mode, and account/terminal trade flags. "
        "Response is served from an in-memory cache (TTL=CAPABILITIES_CACHE_TTL_SECONDS, default 60s)."
    ),
)
async def get_broker_capabilities() -> BrokerCapabilitiesResponse:
    if get_state() not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MT5 terminal not connected",
        )

    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wrap_future(submit(_get_or_refresh_cache), loop=loop)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Not connected to MT5")
    except Exception as exc:
        logger.exception("Failed to fetch broker capabilities: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/broker-capabilities/refresh",
    summary="Force-refresh the broker capabilities cache",
    description="Clears the in-memory capabilities cache and immediately re-fetches from MT5.",
)
async def refresh_broker_capabilities() -> dict:
    if get_state() not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MT5 terminal not connected — cache not cleared",
        )

    loop = asyncio.get_running_loop()
    try:
        result = await asyncio.wrap_future(submit(_refresh_cache_from_mt5), loop=loop)
        return {
            "message": "Capabilities cache refreshed",
            "symbol_count": result.symbol_count,
            "fetched_at": result.fetched_at,
        }
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Not connected to MT5")
    except Exception as exc:
        logger.exception("Failed to refresh broker capabilities: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
