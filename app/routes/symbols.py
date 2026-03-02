from __future__ import annotations

from fastapi import APIRouter

from ..main import symbol_map
from ..models.symbol import SymbolInfo, SymbolsResponse

router = APIRouter(tags=["symbols"])


@router.get("/symbols", response_model=SymbolsResponse)
async def get_symbols() -> SymbolsResponse:
    symbols = [
        SymbolInfo(
            ticker=ticker,
            mt5_symbol=entry.mt5_symbol,
            lot_size=entry.lot_size,
            category=entry.category,
        )
        for ticker, entry in sorted(symbol_map.items())
    ]
    return SymbolsResponse(symbols=symbols)
