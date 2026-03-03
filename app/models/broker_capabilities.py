"""MT5 Bridge — BrokerCapabilities aggregate response model."""
from __future__ import annotations

from pydantic import BaseModel, Field

from .broker_symbol import BrokerSymbol


class BrokerCapabilitiesResponse(BaseModel):
    """Full broker capability snapshot — symbol catalog + account/terminal flags.

    Returned by ``GET /broker-capabilities``. Served from a TTL-cached
    in-memory store. Use ``fetched_at`` to determine freshness.
    """

    account_trade_allowed: bool = Field(
        ...,
        description="Whether the account has trading enabled (account_info.trade_allowed)",
    )
    terminal_trade_allowed: bool = Field(
        ...,
        description="Whether the terminal has trading enabled (terminal_info.trade_allowed)",
    )
    symbol_count: int = Field(..., description="Total number of symbols in the broker catalog")
    symbols: list[BrokerSymbol] = Field(..., description="Complete broker symbol catalog")
    categories: dict[str, list[str]] = Field(
        ...,
        description=(
            "Symbol category tree derived from MT5 symbol paths. "
            "Keys are top-level categories, values are sorted subcategory lists."
        ),
    )
    fetched_at: str = Field(
        ...,
        description="ISO-8601 UTC timestamp when this snapshot was fetched from MT5",
    )
