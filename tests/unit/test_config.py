from __future__ import annotations

from pathlib import Path

import pytest

from app.config import get_mt5_timeframe, load_symbol_map


def test_get_mt5_timeframe_valid():
    assert get_mt5_timeframe("D1") == 16408
    assert get_mt5_timeframe("m1") == 1


def test_get_mt5_timeframe_invalid():
    with pytest.raises(ValueError):
        get_mt5_timeframe("BAD")


def test_load_symbol_map_from_yaml(tmp_path):
    cfg = tmp_path / "symbols.yaml"
    cfg.write_text(
        "symbols:\n  ABC:\n    mt5_symbol: ABC.MT5\n    lot_size: 0.1\n    category: forex\n",
        encoding="utf-8",
    )

    loaded = load_symbol_map(cfg)
    assert "ABC" in loaded
    assert loaded["ABC"].mt5_symbol == "ABC.MT5"
    assert loaded["ABC"].lot_size == 0.1


def test_load_symbol_map_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_symbol_map(tmp_path / "missing.yaml")
