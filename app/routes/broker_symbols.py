import asyncio
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from ..main import symbol_map
from ..models.broker_symbol import BrokerSymbol
from ..mt5_worker import WorkerState, get_state, submit

router = APIRouter(tags=["broker_symbols"])


class BrokerSymbolsResponse(BaseModel):
    symbols: List[BrokerSymbol]
    count: int


_TRADE_MODE_LABELS: dict[int, str] = {
    0: "Disabled",
    1: "Long Only",
    2: "Short Only",
    3: "Close Only",
    4: "Full",
}


def _safe_int_trade_mode(value: object) -> int:
    """Convert MT5 trade_mode to int, defaulting to 4 (Full) on error."""
    try:
        return int(value)  # type: ignore[arg-type]
    except Exception:
        return 4


def _decode_filling_modes(bitmask: int) -> list[str]:
    """Decode filling_mode bitmask into human-readable list."""
    if bitmask & 1:
        modes = ["FOK"]
        if bitmask & 2:
            modes.append("IOC")
        return modes
    if bitmask & 2:
        return ["IOC"]
    return ["RETURN"]


def _parse_symbol_path(path: str | None) -> tuple[str, str]:
    """Parse MT5 symbol path into (category, subcategory)."""
    if not path:
        return ("Other", "")
    segments = [s for s in path.replace("\\", "/").split("/") if s]
    category = segments[0] if segments else "Other"
    subcategory = segments[1] if len(segments) > 1 else ""
    return (category, subcategory)


@router.get("/broker-symbols", response_model=BrokerSymbolsResponse, summary="Get all broker symbols")
async def get_broker_symbols(
    group: Optional[str] = Query(None, description="Optional group filter (e.g. '*USD*')")
) -> BrokerSymbolsResponse:
    if get_state() not in (WorkerState.AUTHORIZED, WorkerState.PROCESSING):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MT5 terminal not connected",
        )

    def _fetch_symbols() -> BrokerSymbolsResponse:
        import MetaTrader5 as mt5 # type: ignore[import-untyped]

        if group:
            symbols_mt5 = mt5.symbols_get(group)
        else:
            symbols_mt5 = mt5.symbols_get()

        if symbols_mt5 is None:
            err = mt5.last_error()
            if err[0] == 1:
                return BrokerSymbolsResponse(symbols=[], count=0)
            raise Exception(f"Failed to fetch symbols: {err}")

        configured_mt5_symbols = {s.mt5_symbol for s in symbol_map.values()}

        symbols: List[BrokerSymbol] = []
        for s in symbols_mt5:
            name = getattr(s, "name", "")
            raw_path = getattr(s, "path", "")
            category, subcategory = _parse_symbol_path(raw_path)

            trade_mode_int = _safe_int_trade_mode(getattr(s, "trade_mode", 4))
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

        return BrokerSymbolsResponse(symbols=symbols, count=len(symbols))

    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wrap_future(submit(_fetch_symbols), loop=loop)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Not connected to MT5")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
