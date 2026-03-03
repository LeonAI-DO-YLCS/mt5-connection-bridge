"""Unit tests for symbol path parsing logic used in broker_capabilities — T031."""
from __future__ import annotations

import sys


def parse_symbol_path(path: str | None) -> tuple[str, str]:
    import app.main  # noqa: F401

    broker_caps_route = sys.modules["app.routes.broker_capabilities"]
    return broker_caps_route._parse_symbol_path(path)


class TestParseSymbolPath:
    """Tests for MT5 symbol path → (category, subcategory) extraction."""

    def test_backslash_separator(self):
        """Standard MT5 Windows format: Forex\\Majors\\EURUSD."""
        assert parse_symbol_path("Forex\\Majors\\EURUSD") == ("Forex", "Majors")

    def test_forward_slash_separator(self):
        """Some brokers use forward slash: Forex/Majors/EURUSD."""
        assert parse_symbol_path("Forex/Majors/EURUSD") == ("Forex", "Majors")

    def test_mixed_separators(self):
        """Mix of separators — normalize to forward slash first."""
        assert parse_symbol_path("Forex\\Majors/EURUSD") == ("Forex", "Majors")

    def test_category_only_no_subcategory(self):
        """Single segment path — subcategory is empty string."""
        assert parse_symbol_path("Crypto") == ("Crypto", "")

    def test_empty_string_returns_other(self):
        """Empty path → ('Other', '')."""
        assert parse_symbol_path("") == ("Other", "")

    def test_none_returns_other(self):
        """None path → ('Other', '')."""
        assert parse_symbol_path(None) == ("Other", "")

    def test_deep_path_uses_only_first_two_segments(self):
        """Deep path — only first two segments are used."""
        result = parse_symbol_path("Forex\\Majors\\EURUSD\\Spot")
        assert result == ("Forex", "Majors")

    def test_volatility_index_path(self):
        """Deriv-style path example."""
        result = parse_symbol_path("Volatility Indices\\Continuous Indices\\Volatility 75 Index")
        assert result == ("Volatility Indices", "Continuous Indices")

    def test_whitespace_path_segments_preserved(self):
        """Spaces in segment names are preserved (broker may include them)."""
        cat, sub = parse_symbol_path("Forex Majors\\Top Pairs")
        assert cat == "Forex Majors"
        assert sub == "Top Pairs"
