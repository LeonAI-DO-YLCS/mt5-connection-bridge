from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest


def test_build_capabilities_maps_categories_and_filling_modes(monkeypatch):
    import app.main  # noqa: F401

    broker_caps_route = sys.modules["app.routes.broker_capabilities"]

    monkeypatch.setattr(
        broker_caps_route,
        "symbol_map",
        {
            "EURUSD": SimpleNamespace(mt5_symbol="EURUSD"),
            "XAUUSD": SimpleNamespace(mt5_symbol="XAUUSD"),
        },
    )

    symbols_mt5 = [
        SimpleNamespace(
            name="EURUSD",
            description="Euro vs US Dollar",
            path="Forex\\Majors\\EURUSD",
            trade_mode=4,
            filling_mode=3,
            spread=12,
            digits=5,
            volume_min=0.01,
            volume_max=500.0,
            volume_step=0.01,
            visible=True,
        ),
        SimpleNamespace(
            name="GBPUSD",
            description="Pound vs US Dollar",
            path="Forex/Majors/GBPUSD",
            trade_mode=1,
            filling_mode=1,
            spread=11,
            digits=5,
            volume_min=0.01,
            volume_max=500.0,
            volume_step=0.01,
            visible=True,
        ),
        SimpleNamespace(
            name="BTCUSD",
            description="Bitcoin",
            path="Crypto",
            trade_mode=2,
            filling_mode=0,
            spread=30,
            digits=2,
            volume_min=0.01,
            volume_max=50.0,
            volume_step=0.01,
            visible=False,
        ),
        SimpleNamespace(
            name="VIX75",
            description="Volatility Index",
            path="Volatility Indices\\Continuous",
            trade_mode=3,
            filling_mode=2,
            spread=8,
            digits=2,
            volume_min=0.1,
            volume_max=100.0,
            volume_step=0.1,
            visible=True,
        ),
    ]

    capabilities = broker_caps_route._build_capabilities(
        symbols_mt5=symbols_mt5,
        terminal_info=SimpleNamespace(trade_allowed=True),
        account_info=SimpleNamespace(trade_allowed=False),
    )

    assert capabilities.account_trade_allowed is False
    assert capabilities.terminal_trade_allowed is True
    assert capabilities.symbol_count == 4

    assert capabilities.categories["Forex"] == ["Majors"]
    assert capabilities.categories["Volatility Indices"] == ["Continuous"]
    assert capabilities.categories["Crypto"] == []

    by_name = {sym.name: sym for sym in capabilities.symbols}
    assert by_name["EURUSD"].is_configured is True
    assert by_name["GBPUSD"].is_configured is False
    assert by_name["EURUSD"].supported_filling_modes == ["FOK", "IOC"]
    assert by_name["GBPUSD"].supported_filling_modes == ["FOK"]
    assert by_name["BTCUSD"].supported_filling_modes == ["RETURN"]
    assert by_name["VIX75"].supported_filling_modes == ["IOC"]


def test_build_capabilities_falls_back_for_invalid_trade_mode_and_filling_mode(monkeypatch):
    import app.main  # noqa: F401

    broker_caps_route = sys.modules["app.routes.broker_capabilities"]

    monkeypatch.setattr(
        broker_caps_route,
        "symbol_map",
        {"EURUSD": SimpleNamespace(mt5_symbol="EURUSD")},
    )

    capabilities = broker_caps_route._build_capabilities(
        symbols_mt5=[
            SimpleNamespace(
                name="EURUSD",
                description="Euro vs US Dollar",
                path="Forex\\Majors\\EURUSD",
                trade_mode="invalid-int",
                filling_mode="invalid-int",
                spread=1,
                digits=5,
                volume_min=0.01,
                volume_max=1.0,
                volume_step=0.01,
                visible=True,
            )
        ],
        terminal_info=SimpleNamespace(trade_allowed=True),
        account_info=SimpleNamespace(trade_allowed=True),
    )

    symbol = capabilities.symbols[0]
    assert symbol.trade_mode == 4
    assert symbol.trade_mode_label == "Full"
    assert symbol.filling_mode == 0
    assert symbol.supported_filling_modes == ["RETURN"]


def test_fetch_capabilities_handles_mt5_no_symbols(monkeypatch, fake_mt5):
    import app.main  # noqa: F401

    broker_caps_route = sys.modules["app.routes.broker_capabilities"]

    monkeypatch.setattr(broker_caps_route, "symbol_map", {})
    fake_mt5.symbols_get = lambda: None
    fake_mt5.last_error = lambda: (1, "no symbols")
    fake_mt5.terminal_info = lambda: SimpleNamespace(trade_allowed=True)
    fake_mt5.account_info = lambda: SimpleNamespace(trade_allowed=True)

    response = broker_caps_route._fetch_capabilities_from_mt5()
    assert response.symbol_count == 0
    assert response.symbols == []


def test_fetch_capabilities_raises_when_mt5_symbols_get_fails(monkeypatch, fake_mt5):
    import app.main  # noqa: F401

    broker_caps_route = sys.modules["app.routes.broker_capabilities"]

    monkeypatch.setattr(broker_caps_route, "symbol_map", {})
    fake_mt5.symbols_get = lambda: None
    fake_mt5.last_error = lambda: (500, "fatal")
    fake_mt5.terminal_info = lambda: SimpleNamespace(trade_allowed=True)
    fake_mt5.account_info = lambda: SimpleNamespace(trade_allowed=True)

    with pytest.raises(RuntimeError):
        broker_caps_route._fetch_capabilities_from_mt5()
