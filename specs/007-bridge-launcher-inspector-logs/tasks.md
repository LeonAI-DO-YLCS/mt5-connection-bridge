# Tasks: Bridge Launcher Inspector Logging

**Input**: Design documents from `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/007-bridge-launcher-inspector-logs/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- `[P]` means task can run in parallel (different files, no direct dependency).
- `[Story]` maps each task to one user story (`US1`, `US2`, `US3`).

## Phase 1: Setup (Shared Foundations)

**Purpose**: Prepare launcher feature scaffolding and baseline guardrails.

- [x] T001 Create launcher script file `scripts/launch_bridge_dashboard.sh` with executable mode and placeholder structure aligned with existing script conventions.
- [x] T002 [P] Create integration test scaffold `tests/integration/test_launcher_runtime.py` with baseline fixture imports and placeholder cases.
- [x] T003 [P] Create contract test scaffold `tests/contract/test_launcher_contract.py` validating launcher artifact shape and lifecycle outputs.
- [x] T004 [P] Add a dedicated launcher log root convention note in `docs/operations/runtime-runbook.md` (section stub for inspector mode).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement core launcher lifecycle and reusable behaviors needed by all stories.

**CRITICAL**: No user-story completion is possible before this phase.

- [x] T005 Implement strict shell safety and lifecycle traps (`ERR`, `INT`, `TERM`, `EXIT`) in `scripts/launch_bridge_dashboard.sh`.
- [x] T006 Implement safe `.env` key reader (no `source .env`) in `scripts/launch_bridge_dashboard.sh`, matching existing script parsing behavior.
- [x] T007 Implement runtime config resolution in `scripts/launch_bridge_dashboard.sh` for port, API key presence checks, and log level defaults.
- [x] T008 Implement run ID generation and run-scoped bundle path creation in `scripts/launch_bridge_dashboard.sh` under `logs/launcher/<run-id>/`.
- [x] T009 Implement mandatory log file creation contract (`launcher.log`, `bridge.stdout.log`, `bridge.stderr.log`) in `scripts/launch_bridge_dashboard.sh`.
- [x] T010 Implement startup summary output in `scripts/launch_bridge_dashboard.sh` with service endpoint URL, dashboard URL, and concrete log paths.
- [x] T011 Implement foreground runtime spawn in `scripts/launch_bridge_dashboard.sh` using existing bridge runtime entrypoint and preserving `/dashboard/` model.
- [x] T012 Implement stream fan-out in `scripts/launch_bridge_dashboard.sh` so stdout/stderr are both terminal-visible and file-persisted.
- [x] T013 Implement termination-reason and exit-code persistence in `scripts/launch_bridge_dashboard.sh` to `launcher.log`.

**Checkpoint**: Foundation complete. User stories can now be completed independently.

---

## Phase 3: User Story 1 - One-Command Runtime Launch (Priority: P1)

**Goal**: Operator launches bridge + dashboard in one command and receives actionable startup guidance.

**Independent Test**: Run launcher from clean shell and confirm both service endpoint and dashboard become reachable from a single process invocation with clear startup output.

### Tests (US1)

- [x] T014 [P] [US1] Add integration test `test_launcher_starts_service_and_dashboard_urls_exposed` in `tests/integration/test_launcher_runtime.py`.
- [x] T015 [P] [US1] Add integration test `test_launcher_fails_fast_on_startup_prereq_failure` in `tests/integration/test_launcher_runtime.py`.
- [x] T016 [P] [US1] Add contract test `test_launcher_output_contains_required_startup_fields` in `tests/contract/test_launcher_contract.py`.

### Implementation (US1)

- [x] T017 [US1] Finalize single-command startup path in `scripts/launch_bridge_dashboard.sh` to bring up existing runtime process serving both API and dashboard.
- [x] T018 [US1] Implement startup prerequisite validation messaging in `scripts/launch_bridge_dashboard.sh` with non-success exits for invalid prerequisites.
- [x] T019 [US1] Add explicit startup guidance section to `README.md` documenting launcher invocation and expected runtime output.
- [x] T020 [US1] Add inspector-mode operational flow to `docs/operations/runtime-runbook.md` for one-command launch and immediate validation.

**Checkpoint**: US1 is independently functional and testable.

---

## Phase 4: User Story 2 - Live and Persisted Inspector Logging (Priority: P2)

**Goal**: Operator sees runtime output live and can review complete per-run artifacts later.

**Independent Test**: Trigger successful and failing requests during launcher run, verify terminal visibility and complete persisted run-scoped logs including lifecycle events.

### Tests (US2)

- [x] T021 [P] [US2] Add integration test `test_launcher_creates_run_scoped_log_bundle` in `tests/integration/test_launcher_runtime.py`.
- [x] T022 [P] [US2] Add integration test `test_launcher_dual_stream_stdout_stderr_to_terminal_and_files` in `tests/integration/test_launcher_runtime.py`.
- [x] T023 [P] [US2] Add integration test `test_auth_failures_are_logged_without_lockout` in `tests/integration/test_launcher_runtime.py`.
- [x] T024 [P] [US2] Add contract test `test_log_bundle_contains_required_files` in `tests/contract/test_launcher_contract.py`.
- [x] T025 [P] [US2] Add contract test `test_retention_window_metadata_is_90_days` in `tests/contract/test_launcher_contract.py`.

### Implementation (US2)

- [x] T026 [US2] Implement lifecycle log writer in `scripts/launch_bridge_dashboard.sh` for start/restart/stop/failure events with UTC timestamps.
- [x] T027 [US2] Implement run bundle retention tagging in `scripts/launch_bridge_dashboard.sh` sufficient to validate 90-day retrievability policy.
- [x] T028 [US2] Implement auth-failure visibility path in launcher session logs by ensuring failed authenticated requests are surfaced in runtime output and persisted files.
- [x] T029 [US2] Update `docs/operations/runtime-runbook.md` with run-log bundle interpretation guidance and troubleshooting mapping.
- [x] T030 [US2] Update `README.md` with run-scoped log bundle structure and retention expectations.

**Checkpoint**: US2 is independently functional and testable.

---

## Phase 5: User Story 3 - Compatibility and Reliability Guardrails (Priority: P3)

**Goal**: Existing operations workflows remain intact while launcher adds restart-once reliability and explicit failure diagnostics.

**Independent Test**: Validate existing scripts continue to behave as before and verify launcher performs one restart attempt on unexpected crash before failing safely.

### Tests (US3)

- [x] T031 [P] [US3] Add integration test `test_launcher_restarts_once_then_exits_on_second_failure` in `tests/integration/test_launcher_runtime.py`.
- [x] T032 [P] [US3] Add integration test `test_launcher_records_both_failure_events_after_failed_restart` in `tests/integration/test_launcher_runtime.py`.
- [x] T033 [P] [US3] Add integration regression test `test_existing_start_stop_restart_smoke_scripts_unchanged` in `tests/integration/test_launcher_runtime.py`.
- [x] T034 [P] [US3] Add contract test `test_compatibility_contract_for_existing_operational_scripts` in `tests/contract/test_launcher_contract.py`.

### Implementation (US3)

- [x] T035 [US3] Implement crash detection and single automatic restart attempt in `scripts/launch_bridge_dashboard.sh`.
- [x] T036 [US3] Implement restart failure safe-halt path in `scripts/launch_bridge_dashboard.sh` with non-success exit and dual-failure diagnostics.
- [x] T037 [US3] Ensure launcher does not alter behavior of `scripts/start_bridge.sh`, `scripts/stop_bridge.sh`, `scripts/restart_bridge.sh`, `scripts/smoke_bridge.sh`.
- [x] T038 [US3] Extend `docs/operations/runtime-runbook.md` with restart-once expectations and escalation steps after second failure.

**Checkpoint**: US3 is independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: Final quality gates, documentation consistency, and verification against spec outcomes.

- [x] T039 [P] Run targeted launcher test suite: `pytest tests/integration/test_launcher_runtime.py tests/contract/test_launcher_contract.py`.
- [x] T040 [P] Run existing operational regression checks: `./scripts/start_bridge.sh --background && ./scripts/smoke_bridge.sh && ./scripts/stop_bridge.sh`.
- [x] T041 Validate quickstart workflow from `specs/007-bridge-launcher-inspector-logs/quickstart.md` and capture any command/output mismatches.
- [x] T042 Update `specs/007-bridge-launcher-inspector-logs/quickstart.md` only if verification reveals drift from implemented behavior.
- [x] T043 Confirm plan/spec alignment by verifying FR-001 through FR-019 and SC-001 through SC-007 traceability in test coverage notes.

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 -> Phase 2 -> Phase 3/4/5 -> Phase 6.
- User stories depend on foundational phase completion.
- US2 depends on US1 startup mechanics.
- US3 depends on US1/US2 lifecycle and logging infrastructure.

### Story Dependencies

- US1 (P1): first deliverable, MVP anchor.
- US2 (P2): builds on US1 runtime lifecycle and log artifacts.
- US3 (P3): extends reliability and compatibility guardrails over US1/US2.

### Parallel Opportunities

- Tasks marked `[P]` can be executed in parallel across independent files.
- US2 and US3 test authoring can partially proceed in parallel once foundational behaviors are implemented.

---

## Parallel Example

```bash
# Parallel test authoring after foundational phase:
T021 + T022 + T023 + T024 + T025

# Parallel US3 test and contract prep:
T031 + T032 + T033 + T034
```

---

## Implementation Strategy

1. Deliver US1 first to establish reliable one-command launch behavior.
2. Add US2 logging and retention behavior without changing existing API contracts.
3. Add US3 restart-once and compatibility safeguards.
4. Execute polish verification and traceability checks before implementation sign-off.

