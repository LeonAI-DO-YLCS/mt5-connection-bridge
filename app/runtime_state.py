from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT


def resolve_runtime_state_path(settings: Any) -> Path:
    raw = Path(str(settings.runtime_state_path))
    if raw.is_absolute():
        return raw
    return PROJECT_ROOT / raw


def load_runtime_state(settings: Any) -> dict[str, Any]:
    path = resolve_runtime_state_path(settings)
    if not path.exists():
        return {}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if not isinstance(payload, dict):
        return {}
    return payload


def apply_runtime_overrides(settings: Any) -> str:
    """
    Apply persisted runtime policy overrides.

    Returns a source label used by diagnostics.
    """
    payload = load_runtime_state(settings)
    if "execution_enabled" not in payload:
        return "env"

    settings.execution_enabled = bool(payload["execution_enabled"])
    return "runtime_state"


def persist_execution_policy(settings: Any, enabled: bool) -> None:
    path = resolve_runtime_state_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = load_runtime_state(settings)
    payload["execution_enabled"] = bool(enabled)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()

    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temp.replace(path)

