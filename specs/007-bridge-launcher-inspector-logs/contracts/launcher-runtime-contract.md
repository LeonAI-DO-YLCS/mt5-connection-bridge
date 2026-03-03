# Contract: Launcher Runtime Interface

**Feature**: Bridge Launcher Inspector Logging  
**Branch**: `007-bridge-launcher-inspector-logs`  
**Date**: 2026-03-02

## 1. Command Contract

### 1.1 Primary Command

- Command path: `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/scripts/launch_bridge_dashboard.sh`
- Invocation type: foreground process
- Contracted outcome:
  - Starts bridge runtime session that serves API and `/dashboard/`
  - Streams runtime output to terminal
  - Persists run-scoped log bundle for each launch attempt

### 1.2 Environment Contract

- Consumes runtime configuration from environment / `.env` values (port, api key, log level).
- Must fail with clear non-success outcome if mandatory runtime prerequisites are missing.
- Must preserve existing operational scripts and not alter their invocation contract.

## 2. Runtime Output Contract

For each launch attempt, startup output must include:
- service endpoint URL
- dashboard URL
- run log bundle file paths
- launch lifecycle status (start, stop, error)

For failure conditions, output must include:
- failure category (startup, crash, restart failure, auth failure)
- associated run identifier or correlation context

## 3. Log Artifact Contract

### 3.1 Bundle Structure

A unique run-scoped bundle must be created per launch attempt:

```text
logs/launcher/<run-id>/
├── launcher.log
├── bridge.stdout.log
└── bridge.stderr.log
```

### 3.2 Retention Contract

- Run-scoped log bundles remain retrievable for 90 days.
- Bundles become cleanup-eligible after 90 days.

## 4. Reliability Contract

- Unexpected runtime crash triggers exactly one automatic restart attempt.
- If restart fails, launcher exits non-success and records both failure events.
- Graceful termination records explicit termination reason and exit code.

## 5. Security Contract

- Network-access-enabled sessions require authentication for all operational requests.
- Failed authentication attempts are logged with request context.
- No throttling/lockout behavior is introduced by this feature.

## 6. Compatibility Contract

These scripts must remain behavior-compatible:
- `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/scripts/start_bridge.sh`
- `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/scripts/stop_bridge.sh`
- `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/scripts/restart_bridge.sh`
- `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/scripts/smoke_bridge.sh`

## 7. Non-Change Contract

- Existing API endpoint contracts remain unchanged by this feature.
- This feature introduces an operational launcher interface and logging behavior, not new API routes.

## 8. Requirement Traceability Notes

| Requirement / Success Criteria | Validation Coverage |
|---|---|
| FR-001, FR-002, FR-007, SC-001 | `tests/integration/test_launcher_runtime.py::test_launcher_starts_service_and_dashboard_urls_exposed`; `tests/contract/test_launcher_contract.py::test_launcher_output_contains_required_startup_fields` |
| FR-003, FR-004, FR-005, FR-006, SC-002, SC-003 | `tests/integration/test_launcher_runtime.py::test_launcher_dual_stream_stdout_stderr_to_terminal_and_files`; `tests/integration/test_launcher_runtime.py::test_launcher_creates_run_scoped_log_bundle`; `tests/contract/test_launcher_contract.py::test_log_bundle_contains_required_files` |
| FR-008, FR-009 | `tests/integration/test_launcher_runtime.py::test_launcher_fails_fast_on_startup_prereq_failure`; `tests/integration/test_launcher_runtime.py::test_launcher_session_metadata_contains_expected_fields` |
| FR-010, SC-004 | `tests/integration/test_launcher_runtime.py::test_existing_start_stop_restart_smoke_scripts_unchanged`; operational regression check command in tasks (`T040`) |
| FR-011, FR-012, FR-013, FR-014, FR-015 | Quickstart validation (`401` unauthenticated, `200` authenticated) and `tests/integration/test_launcher_runtime.py::test_auth_failures_are_logged_without_lockout` |
| FR-016, FR-017, SC-006 | `tests/integration/test_launcher_runtime.py::test_launcher_restarts_once_then_exits_on_second_failure`; `tests/integration/test_launcher_runtime.py::test_launcher_records_both_failure_events_after_failed_restart` |
| FR-018 | Contracted in auth/access section and validated via authenticated quickstart flow |
| FR-019, SC-007 | `tests/contract/test_launcher_contract.py::test_retention_window_metadata_is_90_days` |
| SC-005 | Operationally supported through run-scoped logs + audit records; verified via quickstart and runbook inspector workflow |
