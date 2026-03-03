# MT5 Bridge Runtime Runbook

## Rules

1. Never source `.env` directly in shell scripts.
2. Change execution policy only through `PUT /config/execution`.
3. After restart, always run `./scripts/smoke_bridge.sh`.
4. Use diagnostics endpoints for RCA before editing symbol configs.
5. Treat `X-Error-Code` as the primary automation signal for error handling.

## Standard Procedure

1. `./scripts/stop_bridge.sh`
2. `./scripts/start_bridge.sh --background`
3. `./scripts/smoke_bridge.sh`
4. Open dashboard `/dashboard` and verify `Status` + `Execution Policy`.
5. If symbol issues appear, call `GET /diagnostics/symbols`.

## Inspector Mode (Launcher)

1. Run:
   - `./scripts/launch_bridge_windows.sh` from WSL2 (preferred), or
   - `./scripts/launch_bridge_dashboard.sh` for local shell runtime mode.
   - If Windows dependencies are missing, the launcher auto-bootstraps `.venv-win` when `LAUNCHER_AUTO_SETUP_WINDOWS_VENV=true`.
2. Confirm startup output includes:
   - bridge endpoint URL
   - dashboard URL
   - run log bundle path
   - live TUI status panel with color-coded process/runtime health (unless `LAUNCHER_TUI_MODE=false`)
   - fixed panel output (logs remain in files under the run bundle)
3. Inspect run artifacts under `logs/bridge/launcher/<run-id>/`:
   - `launcher.log` (lifecycle + session events)
   - `bridge.stdout.log` (runtime stdout stream)
   - `bridge.stderr.log` (runtime stderr stream)
   - `session.json` (run metadata and retention window)
4. Inspect dashboard task/trade telemetry under `logs/dashboard/`:
   - `tasks.jsonl` (task execution events)
   - `trades.jsonl` (trade execution audit)
   - `metrics.jsonl` (request telemetry)

Expected behavior:
- Runtime crash triggers one automatic restart attempt.
- If restart fails, launcher exits non-success and records both failure events.
- Failed authentication attempts are logged for inspection; no lockout is applied by launcher policy.
- Run-scoped bundles are retained for 90 days before cleanup eligibility.

## Mistakes To Avoid

- Killing random PIDs without checking listener port ownership.
- Assuming runtime toggles survive restart without persisted state.
- Treating all 404 errors equally; inspect `X-Error-Code`.
- Running the full test suite for every small check; use fast profile first.
