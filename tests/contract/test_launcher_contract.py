from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT_DIR / "scripts" / "launch_bridge_dashboard.sh"


def _run_launcher(tmp_path: Path, bridge_cmd: str) -> tuple[subprocess.CompletedProcess[str], Path]:
    env_file = tmp_path / "contract.env"
    env_file.write_text("", encoding="utf-8")

    log_root = tmp_path / "contract-logs"
    env = os.environ.copy()
    env.update(
        {
            "LAUNCHER_ENV_FILE": str(env_file),
            "LAUNCHER_LOG_ROOT": str(log_root),
            "LAUNCHER_BRIDGE_CMD": bridge_cmd,
            "MT5_BRIDGE_API_KEY": "contract-key",
            "MT5_BRIDGE_PORT": "19001",
            "LOG_LEVEL": "INFO",
        }
    )

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        timeout=20,
        env=env,
    )
    return result, log_root


def _latest_run_dir(log_root: Path) -> Path:
    run_dirs = sorted(p for p in log_root.glob("*") if p.is_dir())
    assert run_dirs, "Expected run directory"
    return run_dirs[-1]


def test_launcher_output_contains_required_startup_fields(tmp_path: Path):
    result, _ = _run_launcher(tmp_path, "python3 -c \"print('contract-start')\"")

    if result.returncode == 4:
        import pytest
        pytest.skip("Launcher pre-flight checks blocked (no MT5 terminal available)")

    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "Bridge endpoint:" in output
    assert "Dashboard:" in output
    assert "Log bundle:" in output


def test_log_bundle_contains_required_files(tmp_path: Path):
    result, log_root = _run_launcher(tmp_path, "python3 -c \"print('contract-bundle')\"")

    if result.returncode == 4:
        import pytest
        pytest.skip("Launcher pre-flight checks blocked (no MT5 terminal available)")

    assert result.returncode == 0
    run_dir = _latest_run_dir(log_root)

    for expected in ("launcher.log", "bridge.stdout.log", "bridge.stderr.log", "session.json"):
        assert (run_dir / expected).exists(), f"Missing {expected}"


def test_retention_window_metadata_is_90_days(tmp_path: Path):
    result, log_root = _run_launcher(tmp_path, "python3 -c \"print('retention')\"")

    if result.returncode == 4:
        import pytest
        pytest.skip("Launcher pre-flight checks blocked (no MT5 terminal available)")

    assert result.returncode == 0
    run_dir = _latest_run_dir(log_root)
    payload = json.loads((run_dir / "session.json").read_text(encoding="utf-8"))

    started = datetime.fromisoformat(payload["started_at_utc"].replace("Z", "+00:00"))
    retention_until = datetime.fromisoformat(payload["retention_until_utc"].replace("Z", "+00:00"))
    delta_days = (retention_until - started).days

    assert 89 <= delta_days <= 90


def test_compatibility_contract_for_existing_operational_scripts():
    expected_scripts = [
        ROOT_DIR / "scripts" / "start_bridge.sh",
        ROOT_DIR / "scripts" / "stop_bridge.sh",
        ROOT_DIR / "scripts" / "restart_bridge.sh",
        ROOT_DIR / "scripts" / "smoke_bridge.sh",
    ]

    for script in expected_scripts:
        assert script.exists(), f"Missing script: {script}"
        lint_result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        assert lint_result.returncode == 0, lint_result.stderr


def test_diagnostics_runtime_contains_launcher_fields(monkeypatch):
    from app.main import app, settings
    from fastapi.testclient import TestClient
    
    run_id = "test-contract-999"
    monkeypatch.setattr(settings, "launcher_run_id", run_id)
    
    current_key = settings.mt5_bridge_api_key
    
    with TestClient(app) as client:
        response = client.get("/diagnostics/runtime", headers={"X-API-Key": current_key})
        assert response.status_code == 200
        data = response.json()
        
        assert "launcher_run_id" in data
        assert data["launcher_run_id"] == run_id
        assert "last_termination_reason" in data
        assert "log_bundle_hint" in data


def test_smoke_bridge_outputs_explicit_pass_fail(tmp_path: Path):
    smoke_script = ROOT_DIR / "scripts" / "smoke_bridge.sh"
    
    # We can invoke it directly without a server running to see the [FAIL] response.
    env = os.environ.copy()
    env["MT5_BRIDGE_API_KEY"] = "contract-key"
    env["MT5_BRIDGE_PORT"] = "19002"  # Ensure no active server
    
    result = subprocess.run(
        ["bash", str(smoke_script)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    
    assert "[FAIL] /health -> Connection Error:" in result.stdout
    assert "Connection refused" in result.stdout or "Failed to connect" in result.stdout
    # Test for no stdout/stderr bleeding in mysterious ways
    assert result.stderr == ""
