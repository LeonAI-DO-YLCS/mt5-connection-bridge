"""
MT5 Bridge — Price data mapper.

Converts the numpy structured array returned by ``mt5.copy_rates_range()``
into a ``PriceResponse`` that matches the main project's Pydantic schema.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np

from ..models.price import Price, PriceResponse


def map_mt5_rates_to_prices(
    rates: np.ndarray | None,
    ticker: str,
) -> PriceResponse:
    """Transform MT5 rates into a schema-compatible ``PriceResponse``.

    Parameters
    ----------
    rates:
        Numpy structured array from ``mt5.copy_rates_range()`` with
        fields: ``time``, ``open``, ``high``, ``low``, ``close``,
        ``tick_volume``, ``real_volume``, ``spread``.
        May be *None* if MT5 returned no data.
    ticker:
        The user-facing ticker name (passed through as-is).

    Returns
    -------
    PriceResponse
        Always a valid response — returns empty ``prices`` list when
        *rates* is None or empty.
    """
    if rates is None or len(rates) == 0:
        return PriceResponse(ticker=ticker, prices=[])

    prices: list[Price] = []
    for row in rates:
        # Volume mapping: tick_volume primary, real_volume fallback (FR-013)
        tick_vol = int(row["tick_volume"])
        real_vol = int(row["real_volume"]) if "real_volume" in rates.dtype.names else 0
        volume = tick_vol if tick_vol > 0 else real_vol

        # Timestamp: Unix epoch → ISO 8601 with Z suffix
        ts = datetime.fromtimestamp(int(row["time"]), tz=timezone.utc)
        time_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ")

        prices.append(
            Price(
                open=float(row["open"]),
                close=float(row["close"]),
                high=float(row["high"]),
                low=float(row["low"]),
                volume=volume,
                time=time_str,
            )
        )

    return PriceResponse(ticker=ticker, prices=prices)
