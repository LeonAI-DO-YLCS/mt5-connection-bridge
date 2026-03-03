# One-Command Bridge + Dashboard Launcher With Full Inspector Logging (mt5-connection-bridge)

## Summary
Create a single launcher script that starts the MT5 bridge (which already serves `/dashboard`) in one command, streams all runtime errors/logs live to terminal for inspector visibility, and persists per-run logs for debugging and auditability, without changing architecture or touching anything outside `mt5-connection-bridge`.

## Objective
Implement a simple, reliable launch workflow for `mt5-connection-bridge` that:
1. Starts bridge + dashboard together with one command.
2. Prints all errors live in terminal.
3. Saves full process logs for post-mortem tracking of failures and successful dashboard-triggered operations.

## Architectural Impact
1. Preserve existing architecture: dashboard remains embedded at `/dashboard` via FastAPI static mount in the same Uvicorn process.
2. No MT5/Linux stack changes, no schema changes, no backtester/frontend changes outside bridge.
3. Additive only inside bridge scripts/docs, with optional small test additions for launcher behavior.

## Decision Matrix
| Decision | Options | Selected | Why |
|---|---|---|---|
| Process model | Embedded `/dashboard` vs separate dashboard server | Embedded `/dashboard` | Matches current bridge architecture and avoids unnecessary second process/port complexity. |
| Log scope | Process+access logs vs UI-action event instrumentation | Process+access logs | Meets inspector requirement with minimal risk: terminal visibility + persisted logs + existing `trades.jsonl` and `metrics.jsonl`. |
| Run mode | Foreground, background, dual | Foreground | Best for live AI inspection: immediate stdout/stderr/error visibility while still writing files. |

## Public Interfaces / Types / APIs
1. No API endpoint contract changes.
2. No Pydantic model changes.
3. New script interface:
   - Command: `./scripts/launch_bridge_dashboard.sh`
   - Behavior: foreground runtime with live log streaming and persisted log files.
4. Log artifact convention (new):
   - Run-scoped launcher log.
   - Run-scoped bridge stdout log.
   - Run-scoped bridge stderr log.
   - Existing application logs remain: `logs/trades.jsonl`, `logs/metrics.jsonl`.

## Step-by-Step Plan
1. Add launcher script at [scripts/launch_bridge_dashboard.sh](/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/scripts/launch_bridge_dashboard.sh).
2. Implement strict shell safety in launcher:
   - `set -Eeuo pipefail`
   - trap `ERR`, `INT`, `TERM`, `EXIT` to print clear failure/shutdown diagnostics.
3. Reuse existing `.env` parsing pattern from bridge scripts (no `source .env`), resolve:
   - `MT5_BRIDGE_PORT` (default `8001`)
   - `MT5_BRIDGE_API_KEY` (if present for optional startup checks and hints)
   - `LOG_LEVEL` (default `INFO`)
4. Add run-scoped log folder creation:
   - Example: `logs/launcher/YYYYMMDD-HHMMSS/`
   - Files:
     - `launcher.log` (script lifecycle + startup diagnostics)
     - `bridge.stdout.log`
     - `bridge.stderr.log`
5. Start bridge in foreground (single process serves API + dashboard):
   - Launch `uvicorn app.main:app --host 0.0.0.0 --port <PORT> --no-use-colors --log-level <LOG_LEVEL>`.
   - Ensure access logs remain enabled so dashboard interactions are visible via HTTP status lines.
6. Stream and persist logs simultaneously:
   - stdout to terminal + `bridge.stdout.log` + `launcher.log`
   - stderr to terminal + `bridge.stderr.log` + `launcher.log`
   - This guarantees inspector AI sees live failures while retaining full history.
7. Add startup summary output with explicit URLs and log paths:
   - `Bridge API: http://127.0.0.1:<PORT>`
   - `Dashboard: http://127.0.0.1:<PORT>/dashboard/`
   - Exact log file locations.
8. Add graceful shutdown behavior:
   - On Ctrl+C or termination, print final status and stop bridge cleanly.
   - Write exit code and termination reason to `launcher.log`.
9. Keep existing operational scripts intact:
   - Do not break `start_bridge.sh`, `stop_bridge.sh`, `restart_bridge.sh`, `smoke_bridge.sh`.
   - Launcher is additive for inspector-first interactive runs.
10. Update bridge docs only (scoped):
   - [README.md](/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/README.md): add new one-command launch section.
   - [docs/operations/runtime-runbook.md](/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/docs/operations/runtime-runbook.md): add “Inspector mode” workflow and log locations.

## Verification
1. Happy path:
   - Run `./scripts/launch_bridge_dashboard.sh`.
   - Confirm terminal shows startup and request logs.
   - Open `/dashboard/` and exercise tabs; verify access logs appear live.
2. Error visibility:
   - Force a known error (bad API key request, invalid payload).
   - Confirm error appears in terminal and in `bridge.stderr.log`/`launcher.log`.
3. Persistence:
   - Confirm per-run log directory exists with all expected files.
   - Confirm existing `logs/trades.jsonl` updates on execute attempts and `logs/metrics.jsonl` updates on requests.
4. Robustness:
   - Simulate port conflict and verify clear terminal failure + persisted error record + non-zero exit.
5. Shutdown:
   - Stop with Ctrl+C.
   - Confirm clean process exit and shutdown marker in `launcher.log`.

## Test Cases and Scenarios
1. `test_launch_script_starts_uvicorn_with_expected_port_and_log_level`
2. `test_launch_script_creates_run_scoped_log_directory`
3. `test_launch_script_streams_stdout_and_stderr_to_terminal_and_files`
4. `test_launch_script_emits_nonzero_exit_and_error_log_on_port_conflict`
5. `test_dashboard_requests_generate_access_logs_and_metrics_entries`
6. `test_execute_flow_writes_trade_audit_entries_for_success_and_failure`

## Assumptions and Defaults
1. Default mode is foreground-only (no daemon mode) per your selection.
2. Dashboard is served by bridge at `/dashboard/` (no separate dashboard server).
3. “Successful tasks inside dashboard” are tracked through:
   - HTTP access/status logs (success/error per request),
   - `metrics.jsonl` request telemetry,
   - `trades.jsonl` execution audit trail.
4. Scope remains strictly within `mt5-connection-bridge`.
