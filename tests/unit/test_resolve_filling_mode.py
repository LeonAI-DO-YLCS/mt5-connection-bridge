"""Unit tests for resolve_filling_mode() in trade_mapper.py — T012."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.mappers.trade_mapper import resolve_filling_mode


def _sym(filling_mode: int) -> SimpleNamespace:
    return SimpleNamespace(filling_mode=filling_mode)


class TestResolveFillingMode:
    """Tests for the priority cascade: FOK (bit 0) > IOC (bit 1) > RETURN (default)."""

    def test_bitmask_zero_returns_return_mode(self):
        """bitmask=0 → no FOK, no IOC → RETURN (constant value 0)."""
        result = resolve_filling_mode(_sym(0))
        # ORDER_FILLING_RETURN = 0 (fallback constant)
        assert result == 0

    def test_bitmask_one_returns_fok(self):
        """bitmask=1 (bit 0 set) → FOK supported → select FOK (constant 1)."""
        result = resolve_filling_mode(_sym(1))
        assert result == 1  # ORDER_FILLING_FOK = 1

    def test_bitmask_two_returns_ioc(self):
        """bitmask=2 (bit 1 set only) → IOC supported → select IOC (constant 2)."""
        result = resolve_filling_mode(_sym(2))
        assert result == 2  # ORDER_FILLING_IOC = 2

    def test_bitmask_three_returns_fok(self):
        """bitmask=3 (both bits set) → FOK wins over IOC (FOK is preferred)."""
        result = resolve_filling_mode(_sym(3))
        assert result == 1  # ORDER_FILLING_FOK = 1 wins

    def test_missing_filling_mode_attr_returns_return(self):
        """symbol_info without filling_mode attribute → safe default RETURN."""
        sym = SimpleNamespace()  # no filling_mode attr
        result = resolve_filling_mode(sym)
        assert result == 0  # RETURN

    def test_none_filling_mode_returns_return(self):
        """symbol_info.filling_mode = None → treated as 0 → RETURN."""
        sym = SimpleNamespace(filling_mode=None)
        result = resolve_filling_mode(sym)
        assert result == 0

    def test_large_bitmask_bit0_set(self):
        """bitmask with bit 0 set among higher bits → FOK still selected."""
        result = resolve_filling_mode(_sym(0xFF))  # bit 0 set
        assert result == 1  # FOK
