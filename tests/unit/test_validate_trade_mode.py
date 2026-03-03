"""Unit tests for validate_trade_mode() in trade_mapper.py — T018."""
from __future__ import annotations

from types import SimpleNamespace

from app.mappers.trade_mapper import validate_trade_mode


def _sym(trade_mode: int, name: str = "EURUSD") -> SimpleNamespace:
    return SimpleNamespace(trade_mode=trade_mode, name=name)


class TestValidateTradeModeDisabled:
    """trade_mode=0: DISABLED — all actions blocked."""

    def test_buy_blocked(self):
        err = validate_trade_mode(_sym(0), "buy")
        assert err is not None
        assert "disabled" in err.lower()

    def test_sell_blocked(self):
        err = validate_trade_mode(_sym(0), "sell")
        assert err is not None

    def test_short_blocked(self):
        err = validate_trade_mode(_sym(0), "short")
        assert err is not None

    def test_cover_blocked(self):
        err = validate_trade_mode(_sym(0), "cover")
        assert err is not None


class TestValidateTradeModeLongOnly:
    """trade_mode=1: LONG ONLY — buy allowed, sell blocked."""

    def test_buy_allowed(self):
        assert validate_trade_mode(_sym(1), "buy") is None

    def test_cover_allowed(self):
        assert validate_trade_mode(_sym(1), "cover") is None

    def test_buy_limit_allowed(self):
        assert validate_trade_mode(_sym(1), "buy_limit") is None

    def test_buy_stop_allowed(self):
        assert validate_trade_mode(_sym(1), "buy_stop") is None

    def test_sell_blocked(self):
        err = validate_trade_mode(_sym(1), "sell")
        assert err is not None
        assert "long" in err.lower()

    def test_short_blocked(self):
        err = validate_trade_mode(_sym(1), "short")
        assert err is not None

    def test_sell_limit_blocked(self):
        err = validate_trade_mode(_sym(1), "sell_limit")
        assert err is not None

    def test_sell_stop_blocked(self):
        err = validate_trade_mode(_sym(1), "sell_stop")
        assert err is not None


class TestValidateTradeModeShortOnly:
    """trade_mode=2: SHORT ONLY — sell allowed, buy blocked."""

    def test_sell_allowed(self):
        assert validate_trade_mode(_sym(2), "sell") is None

    def test_short_allowed(self):
        assert validate_trade_mode(_sym(2), "short") is None

    def test_sell_limit_allowed(self):
        assert validate_trade_mode(_sym(2), "sell_limit") is None

    def test_sell_stop_allowed(self):
        assert validate_trade_mode(_sym(2), "sell_stop") is None

    def test_buy_blocked(self):
        err = validate_trade_mode(_sym(2), "buy")
        assert err is not None
        assert "short" in err.lower()

    def test_cover_blocked(self):
        err = validate_trade_mode(_sym(2), "cover")
        assert err is not None

    def test_buy_limit_blocked(self):
        err = validate_trade_mode(_sym(2), "buy_limit")
        assert err is not None


class TestValidateTradeModeCloseOnly:
    """trade_mode=3: CLOSE ONLY — no new positions at all."""

    def test_buy_blocked(self):
        err = validate_trade_mode(_sym(3), "buy")
        assert err is not None
        assert "close-only" in err.lower()

    def test_sell_blocked(self):
        err = validate_trade_mode(_sym(3), "sell")
        assert err is not None

    def test_short_blocked(self):
        err = validate_trade_mode(_sym(3), "short")
        assert err is not None

    def test_cover_blocked(self):
        err = validate_trade_mode(_sym(3), "cover")
        assert err is not None


class TestValidateTradeModeFull:
    """trade_mode=4: FULL — all actions allowed."""

    def test_buy_allowed(self):
        assert validate_trade_mode(_sym(4), "buy") is None

    def test_sell_allowed(self):
        assert validate_trade_mode(_sym(4), "sell") is None

    def test_short_allowed(self):
        assert validate_trade_mode(_sym(4), "short") is None

    def test_cover_allowed(self):
        assert validate_trade_mode(_sym(4), "cover") is None


class TestValidateTradeModeEdgeCases:
    """Edge cases: unknown mode, invalid type, symbol name in error."""

    def test_unknown_mode_allows_all(self):
        """Unknown trade_mode values default to FULL (allow all)."""
        assert validate_trade_mode(_sym(99), "buy") is None
        assert validate_trade_mode(_sym(99), "sell") is None

    def test_symbol_name_in_error_message(self):
        err = validate_trade_mode(_sym(0, name="V75"), "buy")
        assert "V75" in err

    def test_case_insensitive_action(self):
        """Action matching is case-insensitive."""
        assert validate_trade_mode(_sym(1), "BUY") is None
        err = validate_trade_mode(_sym(1), "SELL")
        assert err is not None
