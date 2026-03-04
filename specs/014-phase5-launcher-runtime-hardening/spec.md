# Feature Specification: Phase 5 — Launcher and Runtime Hardening

**Feature Branch**: `014-phase5-launcher-runtime-hardening`
**Created**: 2026-03-03
**Status**: Draft
**Plan Reference**: `docs/plans/phased-user-facing-reliability/5-launcher-runtime-hardening.md`
**Phase Dependency**: Phase 0 (baseline and launcher invariants checklist)

---

## Overview

The bridge has experienced recurring runtime startup failures — port conflicts, missing Python dependencies, invalid log-level formats, and failed restart attempts — that operators discover only after the bridge fails to start. Diagnosing these incidents requires opening multiple logs and manually tracing the cause.

This phase adds **additive preflight checks and structured diagnostic output** to the existing launcher scripts: the same commands, same workflow, same restart behavior — but with clear, plain-language startup diagnostics that surface environment issues before the bridge process is spawned, and structured failure guidance when startup fails.

The strict constraint: no launcher script is replaced, no command is renamed, no existing operator workflow is broken.

---

## User Scenarios & Testing _(mandatory)_

### Primary User Story

As an operator running the bridge on a new machine for the first time, when I execute `./scripts/start_bridge.sh`, I want to see a preflight summary that confirms the environment is ready — or clearly lists what is wrong and what to do — before the bridge process starts. I should never have to open a log file to understand why the bridge refused to start.

As an operator investigating a failed restart, I want the launcher to output a plain-language diagnosis: "Port 8000 is already in use by process XYZ — run `./scripts/stop_bridge.sh` first" — not a raw OS error or a blank exit.

As an operator performing smoke tests, I want the smoke test script to output an enriched status summary (version, run ID) while keeping existing pass/fail behavior intact.

As a Windows operator, I want the equivalent structured preflight checks and output parsing on my PowerShell launcher wrapper.

### Acceptance Scenarios

1. **Given** the `MetaTrader5` Python package is not installed in the active runtime environment, **When** the operator runs `./scripts/start_bridge.sh`, **Then** the preflight check detects the missing dependency and prints a human-readable message: "Required dependency 'MetaTrader5' is not installed. Install it with: `pip install MetaTrader5`" — before attempting to start the bridge process.

2. **Given** the bridge's configured port is already bound by another process, **When** the operator runs `./scripts/start_bridge.sh`, **Then** the preflight check detects the port conflict and prints the specific port number and the command to stop the existing listener — before attempting to bind.

3. **Given** the log-level environment variable is set to an invalid value (e.g., "DEBG" instead of "DEBUG"), **When** the operator runs `./scripts/start_bridge.sh`, **Then** the preflight check emits a warning: "Log level 'DEBG' is not valid — defaulting to INFO" — and the bridge starts with the safe default, not an error.

4. **Given** the bridge starts successfully after all preflight checks pass, **When** the operator views the launch output, **Then** the preflight summary is concise (no excessive output), all checks show a pass status, and no additional steps are required.

5. **Given** a bridge session ends in a non-success exit after a failed restart attempt, **When** the operator reads the terminal output, **Then** there is a clear human-readable statement of what the last restart attempt's outcome was and what to do next.

6. **Given** the bridge is running and the operator runs `./scripts/smoke_bridge.sh`, **When** the bridge is healthy, **Then** the smoke output is enriched with a richer status summary (endpoint statuses, bridge version, run ID) — but the existing smoke pass/fail exit code behavior is unchanged.

7. **Given** the dashboard Status tab is open, **When** the bridge is running, **Then** the dashboard shows the current launcher run ID and last termination reason snapshot as an additive informational panel — without changing existing tab layout or navigation.

### Edge Cases

- What if a preflight check itself fails (e.g., the port check command is unavailable)? → The check is skipped with a warning "preflight check unavailable — proceeding with launch" and the bridge start continues. Preflight checks must never prevent a launch attempt unless explicitly classified as a critical blocker.
- What if the operator has a CI script that parses the existing launcher output format? → Log and terminal output additions are additive lines — existing status lines and exit codes remain unchanged. CI scripts that parse specific lines may need a minor update if they do strict text matching, which is documented in the operator runbook update.
- What if the dashboard Status tab cannot reach the run ID endpoint? → The panel shows "Run ID not available" and the rest of the dashboard functions normally.

---

## Requirements _(mandatory)_

### Functional Requirements

**Launcher Script Invariants (must not change)**

- **FR-001**: Script entrypoints (`start_bridge.sh`, `stop_bridge.sh`, `restart_bridge.sh`, `smoke_bridge.sh`, `launch_bridge_dashboard.sh`, `launch_bridge_windows.sh`, `windows/launch_bridge_windows.ps1`) MUST retain their existing names, locations, and basic invocation syntax.
- **FR-002**: The single-automatic-restart policy (one restart attempt on unexpected exit) MUST remain the default behavior — not removed, not changed to multi-attempt.
- **FR-003**: Log bundle files MUST remain in the same `logs/bridge/launcher/<run-id>/` location and structure.
- **FR-004**: The `stop → start → smoke` operational procedure MUST continue to function identically.

**Additive Preflight Checks**

- **FR-005**: `start_bridge.sh` MUST perform a port availability check before spawning the bridge process, reporting the port number and occupying process if blocked, in plain language.
- **FR-006**: `start_bridge.sh` MUST perform a Python/runtime dependency presence check, listing any missing critical packages by name with the corresponding install command.
- **FR-007**: `start_bridge.sh` MUST validate the effective log-level value before process spawn, emitting a warning and substituting a safe default if the value is invalid — without blocking the launch.
- **FR-008**: `start_bridge.sh` MUST perform an environment key sanity check (presence-only, no secret values printed) and warn if required environment variables are absent.
- **FR-009**: All preflight check results MUST be presented as a preflight summary block in the terminal output before the bridge process launch begins.
- **FR-010**: Preflight checks classified as warnings MUST NOT prevent launch — the bridge starts with the warning noted.
- **FR-011**: Preflight checks classified as critical blockers (e.g., port conflict) MUST prevent launch and print the exact corrective command.

**Structured Failure Guidance**

- **FR-012**: When the bridge process fails to start or exits abnormally, the launcher MUST map the failure to a human-readable diagnostic category: dependency missing, port conflict, environment mismatch, auth misconfiguration, or generic unexpected failure.
- **FR-013**: Each diagnostic category MUST include: a plain-language description, the specific command to run next, the log file to inspect first, and any known compatibility flag relevant to the scenario.

**Incident Linkage**

- **FR-014**: Each launcher run MUST generate or preserve a run ID that can be correlated with API `tracking_id` values from the same session.
- **FR-015**: The run ID MUST be emitted in the preflight summary and available in the launcher log bundle.

**Dashboard-Runtime Linkage (additive)**

- **FR-016**: The bridge API MUST expose an endpoint or field (e.g., on `/diagnostics/runtime`) that surfaces the current launcher run ID and last termination reason.
- **FR-017**: The dashboard Status tab MUST display the current launcher run ID and last termination reason as an additive informational panel — without replacing or rearranging any existing tab content.
- **FR-018**: The dashboard MUST provide a quick link or hint to the current log bundle location, without embedding sensitive file paths.

**Backward Compatibility Validation**

- **FR-019**: All existing documented commands MUST continue to function without modification.
- **FR-020**: All existing environment variables used by the launcher MUST continue to be honored.
- **FR-021**: All log bundle files MUST remain in the same location and structure.

### Key Entities

- **PreflightSummary**: The structured terminal output block produced before bridge process launch, listing each check and its result.
- **PreflightCheck**: A single pre-launch validation (port availability, dependency presence, env var presence, log level validity), with a result of pass, warning, or critical-blocker.
- **LauncherRunID**: The unique identifier for a single bridge launch session, correlatable with API `tracking_id` values from that session.
- **StartupFailureDiagnostic**: The mapped human-readable explanation of a bridge startup failure, including next-step commands and log file references.
- **RuntimeSummaryPanel**: The additive dashboard Status tab component showing the current launcher run ID and last termination reason.

---

## Success Criteria _(mandatory)_

1. **Preflight coverage**: The four defined preflight check areas (port conflict, dependency presence, environment key sanity, log-level validity) are all executed before the bridge process launches — confirmed by a test that triggers each condition and observes the correct terminal output.

2. **Plain-language output**: For each of the three most common observed startup failure scenarios (missing `MetaTrader5`, port `10048` already bound, invalid log-level), the terminal output provides the exact corrective command without requiring the operator to read a log file — confirmed by a non-developer reading the output cold.

3. **No workflow regression**: The existing documented runbook (`stop → start → smoke`) produces the same exit codes and operational outcomes as before — confirmed by running the full procedure in a test environment and comparing outputs.

4. **Run ID correlation**: Given a `tracking_id` from a bridge API response and the launcher run ID from the same session, a support engineer can confirm they belong to the same session within 30 seconds.

5. **Dashboard panel non-disruptive**: After the additive runtime summary panel is added to the Status tab, all existing Status tab content remains present and functional — confirmed by a regression check of the existing dashboard tab tests.

---

## Assumptions

- WSL is the primary launcher environment. On Windows, the PowerShell launcher (`launch_bridge_windows.ps1`) receives equivalent improvements but may have platform-specific diagnostics (e.g., `netstat` vs. `ss` for port checking).
- Critical-blocker preflight checks that prevent launch are limited to scenarios where launching would certainly fail immediately or destructively (e.g., port conflict). All other checks are warnings.
- The run ID may be the existing log bundle `<run-id>` that is already generated by the launcher — this phase standardizes its exposure, not necessarily changes its generation.

---

## Out of Scope

- Replacing any launcher script with a new tool.
- Adding new primary command entrypoints (new scripts are allowed only as supporting utilities called from existing scripts, not new top-level commands).
- Dashboard layout redesign (Phase 6).
- API-level readiness preflight (Phase 2).
- MT5 parity expansion (Phase 7).
