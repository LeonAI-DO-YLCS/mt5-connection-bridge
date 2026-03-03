from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.mappers.trade_mapper import build_order_request
from app.models.trade import TradeRequest


@pytest.mark.parametrize(
    ("bitmask", "expected_filling"),
    [
        (0, 0),  # RETURN
        (1, 1),  # FOK
        (2, 2),  # IOC
        (3, 1),  # FOK wins over IOC
    ],
)
def test_build_order_request_uses_dynamic_filling_mode(bitmask: int, expected_filling: int):
    req = TradeRequest(
        ticker="V75",
        action="buy",
        quantity=0.10,
        current_price=100.0,
    )
    symbol_info = SimpleNamespace(
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        spread=5,
        filling_mode=bitmask,
    )

    payload = build_order_request(req, "Volatility 75 Index", symbol_info)

    assert payload["symbol"] == "Volatility 75 Index"
    assert payload["type_filling"] == expected_filling

