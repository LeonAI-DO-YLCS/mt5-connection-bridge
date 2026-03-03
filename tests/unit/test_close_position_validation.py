from types import SimpleNamespace

import app.main  # noqa: F401 - ensures route imports are initialized for tests
from app.routes.close_position import _is_valid_step, _validate_close_volume


def test_validate_close_volume_accepts_valid_step():
    symbol_info = SimpleNamespace(volume_min=0.01, volume_step=0.01)
    err = _validate_close_volume(0.05, position_volume=0.10, symbol_info=symbol_info)
    assert err is None


def test_validate_close_volume_none_is_allowed_for_full_close():
    symbol_info = SimpleNamespace(volume_min=0.01, volume_step=0.01)
    err = _validate_close_volume(None, position_volume=0.10, symbol_info=symbol_info)
    assert err is None


def test_is_valid_step_with_non_positive_step_is_permitted():
    assert _is_valid_step(0.1, min_value=0.01, step=0.0) is True


def test_validate_close_volume_rejects_invalid_step():
    symbol_info = SimpleNamespace(volume_min=0.01, volume_step=0.01)
    err = _validate_close_volume(0.055, position_volume=0.10, symbol_info=symbol_info)
    assert err is not None
    assert "step size" in err


def test_validate_close_volume_rejects_above_position_volume():
    symbol_info = SimpleNamespace(volume_min=0.01, volume_step=0.01)
    err = _validate_close_volume(0.20, position_volume=0.10, symbol_info=symbol_info)
    assert err is not None
    assert "cannot exceed" in err
