from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.mappers.trade_mapper import build_close_request


@pytest.mark.parametrize(
    ("position_type", "bitmask", "expected_order_type", "expected_filling"),
    [
        (0, 0, 1, 0),  # close BUY with SELL + RETURN
        (0, 1, 1, 1),  # close BUY with SELL + FOK
        (1, 2, 0, 2),  # close SELL with BUY + IOC
        (1, 3, 0, 1),  # close SELL with BUY + FOK
    ],
)
def test_build_close_request_sets_dynamic_filling(
    position_type: int,
    bitmask: int,
    expected_order_type: int,
    expected_filling: int,
):
    position = SimpleNamespace(
        ticket=12345,
        symbol="EURUSD",
        type=position_type,
        volume=0.50,
    )
    symbol_info = SimpleNamespace(
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        filling_mode=bitmask,
    )

    payload = build_close_request(position, None, symbol_info)

    assert payload["position"] == 12345
    assert payload["type"] == expected_order_type
    assert payload["type_filling"] == expected_filling

