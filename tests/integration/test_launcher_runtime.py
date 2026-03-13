from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT_DIR / "scripts" / "launch_bridge_dashboard.sh"


def _run_launcher(
    tmp_path: Path,
    bridge_cmd: str,
    *,
    api_key: str | None = "test-api-key",
    env_file_content: str = "",
    timeout: int = 20,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    env_file = tmp_path / "launcher.env"
    env_file.write_text(env_file_content, encoding="utf-8")

    log_root = tmp_path / "launcher-logs"
    env = os.environ.copy()
    env.update(
        {
            "LAUNCHER_ENV_FILE": str(env_file),
            "LAUNCHER_LOG_ROOT": str(log_root),
            "LAUNCHER_BRIDGE_CMD": bridge_cmd,
            "MT5_BRIDGE_PORT": "18001",
            "LOG_LEVEL": "INFO",
        }
    )

    if api_key is None:
        env.pop("MT5_BRIDGE_API_KEY", None)
    else:
        env["MT5_BRIDGE_API_KEY"] = api_key

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    if result.returncode == 4:
        import pytest
        pytest.skip("Launcher blocked by preflight checks (No MT5)")
    return result, log_root


def _latest_run_dir(log_root: Path) -> Path:
    run_dirs = sorted(p for p in log_root.glob("*") if p.is_dir())
    assert run_dirs, "Expected at least one run directory"
    return run_dirs[-1]


def test_launcher_starts_service_and_dashboard_urls_exposed(tmp_path: Path):
    result, _ = _run_launcher(tmp_path, "python3 -c \"print('bridge-up')\"")

    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "Bridge endpoint: http://127.0.0.1:18001" in output
    assert "Dashboard: http://127.0.0.1:18001/dashboard/" in output


def test_launcher_fails_fast_on_startup_prereq_failure(tmp_path: Path):
    result, _ = _run_launcher(
        tmp_path,
        "python3 -c \"print('should-not-run')\"",
        api_key=None,
    )

    assert result.returncode != 0
    assert "MT5_BRIDGE_API_KEY is required" in (result.stdout + result.stderr)


def test_launcher_creates_run_scoped_log_bundle(tmp_path: Path):
    result, log_root = _run_launcher(tmp_path, "python3 -c \"print('bundle-check')\"")

    assert result.returncode == 0
    run_dir = _latest_run_dir(log_root)
    assert (run_dir / "launcher.log").exists()
    assert (run_dir / "bridge.stdout.log").exists()
    assert (run_dir / "bridge.stderr.log").exists()


def test_launcher_dual_stream_stdout_stderr_to_terminal_and_files(tmp_path: Path):
    cmd = "python3 -c \"import sys; print('out-line'); print('err-line', file=sys.stderr)\""
    result, log_root = _run_launcher(tmp_path, cmd)

    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "out-line" in output
    assert "err-line" in output

    run_dir = _latest_run_dir(log_root)
    launcher_log = (run_dir / "launcher.log").read_text(encoding="utf-8")
    stdout_log = (run_dir / "bridge.stdout.log").read_text(encoding="utf-8")
    stderr_log = (run_dir / "bridge.stderr.log").read_text(encoding="utf-8")

    assert "out-line" in launcher_log
    assert "err-line" in launcher_log
    assert "out-line" in stdout_log
    assert "err-line" in stderr_log


def test_auth_failures_are_logged_without_lockout(tmp_path: Path):
    cmd = "python3 -c \"print('GET /health 401 Unauthorized'); print('GET /health 401 Unauthorized')\""
    result, log_root = _run_launcher(tmp_path, cmd)

    assert result.returncode == 0
    run_dir = _latest_run_dir(log_root)
    launcher_log = (run_dir / "launcher.log").read_text(encoding="utf-8")

    assert launcher_log.count("401 Unauthorized") >= 2
    assert "lockout" not in launcher_log.lower()


def test_launcher_restarts_once_then_exits_on_second_failure(tmp_path: Path):
    result, _ = _run_launcher(tmp_path, "python3 -c \"import sys; sys.exit(1)\"")

    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "Attempting one automatic restart" in output
    assert "Runtime attempt 1 exited with code 1" in output
    assert "Runtime attempt 2 exited with code 1" in output


def test_launcher_records_both_failure_events_after_failed_restart(tmp_path: Path):
    result, log_root = _run_launcher(tmp_path, "python3 -c \"import sys; sys.exit(1)\"")

    assert result.returncode != 0
    run_dir = _latest_run_dir(log_root)

    launcher_log = (run_dir / "launcher.log").read_text(encoding="utf-8")
    assert "Runtime attempt 1 exited with code 1" in launcher_log
    assert "Runtime attempt 2 exited with code 1" in launcher_log

    session = json.loads((run_dir / "session.json").read_text(encoding="utf-8"))
    assert session["restart_attempted"] is True
    assert session["restart_successful"] is False
    assert session["termination_reason"] == "failed_after_restart"


def test_existing_start_stop_restart_smoke_scripts_unchanged():
    expected_scripts = [
        ROOT_DIR / "scripts" / "start_bridge.sh",
        ROOT_DIR / "scripts" / "stop_bridge.sh",
        ROOT_DIR / "scripts" / "restart_bridge.sh",
        ROOT_DIR / "scripts" / "smoke_bridge.sh",
    ]

    for script in expected_scripts:
        assert script.exists(), f"Missing script: {script}"
        check = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        assert check.returncode == 0, f"Shell syntax check failed for {script}: {check.stderr}"


def test_launcher_session_metadata_contains_expected_fields(tmp_path: Path):
    result, log_root = _run_launcher(tmp_path, "python3 -c \"print('metadata')\"")

    assert result.returncode == 0
    run_dir = _latest_run_dir(log_root)
    payload = json.loads((run_dir / "session.json").read_text(encoding="utf-8"))

    for field in (
        "run_id",
        "started_at_utc",
        "ended_at_utc",
        "retention_until_utc",
        "termination_reason",
        "bundle_root_path",
    ):
        assert field in payload

    started = datetime.fromisoformat(payload["started_at_utc"].replace("Z", "+00:00"))
    ended = datetime.fromisoformat(payload["ended_at_utc"].replace("Z", "+00:00"))
    assert ended >= started


def test_launcher_emits_preflight_summary(tmp_path: Path):
    result, _ = _run_launcher(tmp_path, "python3 -c \"print('bridge-up')\"")
    output = result.stdout + result.stderr
    # Before the bridge starts, the launcher should emit the preflight summary
    assert "Preflight Summary" in output
    assert "Result:" in output
    assert "Port" in output
    assert "LOG_LEVEL" in output


def test_launcher_diagnostics_on_startup_failure(tmp_path: Path):
    cmd = "python3 -c \"import sys; print('Address already in use', file=sys.stderr); sys.exit(1)\""
    result, _ = _run_launcher(tmp_path, cmd)
    output = result.stdout + result.stderr
    
    # We should see the diagnostic pane printed
    assert "Startup Failure Diagnosis" in output
    assert "port_conflict" in output
    assert "Fix" in output
