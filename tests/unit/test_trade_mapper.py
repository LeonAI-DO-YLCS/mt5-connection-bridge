from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.mappers.trade_mapper import action_to_mt5_order_type, build_order_request, normalize_lot_size
from app.models.trade import TradeRequest


def test_action_to_mt5_order_type_known():
    assert action_to_mt5_order_type("buy") in (0, 1)
    assert action_to_mt5_order_type("sell") in (0, 1)


def test_action_to_mt5_order_type_invalid():
    with pytest.raises(ValueError):
        action_to_mt5_order_type("hold")


def test_normalize_lot_size_rounding():
    symbol = SimpleNamespace(volume_min=0.01, volume_max=1.0, volume_step=0.01)
    assert normalize_lot_size(0.014, symbol) == 0.01
    assert normalize_lot_size(0.016, symbol) == 0.02


def test_build_order_request_contains_expected_fields():
    symbol = SimpleNamespace(volume_min=0.01, volume_max=1.0, volume_step=0.01, spread=5)
    req = TradeRequest(ticker="V75", action="buy", quantity=0.1, current_price=100.0)

    payload = build_order_request(req, "Volatility 75 Index", symbol)
    assert payload["symbol"] == "Volatility 75 Index"
    assert payload["price"] == 100.0
    assert payload["volume"] == 0.1
