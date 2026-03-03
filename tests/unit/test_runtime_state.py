from __future__ import annotations

from types import SimpleNamespace

from app.runtime_state import apply_runtime_overrides, load_runtime_state, persist_execution_policy


def test_runtime_state_roundtrip(tmp_path):
    runtime_file = tmp_path / "runtime_state.json"
    settings = SimpleNamespace(runtime_state_path=str(runtime_file), execution_enabled=False)

    persist_execution_policy(settings, True)
    payload = load_runtime_state(settings)

    assert payload["execution_enabled"] is True
    assert "updated_at" in payload

    settings.execution_enabled = False
    source = apply_runtime_overrides(settings)
    assert source == "runtime_state"
    assert settings.execution_enabled is True


def test_runtime_state_fallback_to_env_when_missing(tmp_path):
    settings = SimpleNamespace(runtime_state_path=str(tmp_path / "missing.json"), execution_enabled=False)
    source = apply_runtime_overrides(settings)
    assert source == "env"
    assert settings.execution_enabled is False

