from __future__ import annotations

from pydantic import BaseModel


class SymbolInfo(BaseModel):
    ticker: str
    mt5_symbol: str
    lot_size: float
    category: str


class SymbolsResponse(BaseModel):
    symbols: list[SymbolInfo]
