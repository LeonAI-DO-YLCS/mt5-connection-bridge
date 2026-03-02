from __future__ import annotations

import numpy as np

from app.mappers.price_mapper import map_mt5_rates_to_prices


def test_map_mt5_rates_to_prices_empty():
    out = map_mt5_rates_to_prices(None, "V75")
    assert out.ticker == "V75"
    assert out.prices == []


def test_map_mt5_rates_to_prices_rows():
    rates = np.array(
        [
            (1704067200, 10.0, 12.0, 9.0, 11.0, 0, 0, 7),
        ],
        dtype=[
            ("time", "i8"),
            ("open", "f8"),
            ("high", "f8"),
            ("low", "f8"),
            ("close", "f8"),
            ("tick_volume", "i8"),
            ("spread", "i8"),
            ("real_volume", "i8"),
        ],
    )

    out = map_mt5_rates_to_prices(rates, "V75")
    assert out.ticker == "V75"
    assert len(out.prices) == 1
    assert out.prices[0].volume == 7
    assert out.prices[0].time.endswith("Z")
