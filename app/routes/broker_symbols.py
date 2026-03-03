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


def _map_trade_mode(value: object) -> str:
    mapping = {
        0: "Disabled",
        1: "Long Only",
        2: "Short Only",
        3: "Close Only",
        4: "Full",
    }
    try:
        return mapping.get(int(value), str(value))
    except Exception:
        return str(value)


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
            symbols.append(
                BrokerSymbol(
                    name=name,
                    description=getattr(s, "description", ""),
                    path=getattr(s, "path", ""),
                    spread=getattr(s, "spread", 0),
                    digits=getattr(s, "digits", 0),
                    volume_min=getattr(s, "volume_min", 0.0),
                    volume_max=getattr(s, "volume_max", 0.0),
                    trade_mode=_map_trade_mode(getattr(s, "trade_mode", "")),
                    is_configured=name in configured_mt5_symbols
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
