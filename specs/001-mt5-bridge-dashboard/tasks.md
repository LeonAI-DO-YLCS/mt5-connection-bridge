# Tasks: MT5 Bridge Verification Dashboard

**Input**: Design documents from `/specs/001-mt5-bridge-dashboard/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Automated tests are required by the specification (FR-013, FR-014), so test tasks are included per story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization for test/dev tooling and dashboard scaffolding.

- [X] T001 Create test dependency manifest in `mt5-connection-bridge/requirements-dev.txt`
- [X] T002 Create pytest configuration in `mt5-connection-bridge/pytest.ini`
- [X] T003 [P] Add feature env flags (`EXECUTION_ENABLED`, `METRICS_RETENTION_DAYS`) in `mt5-connection-bridge/.env.example`
- [X] T004 [P] Create dashboard root markup in `mt5-connection-bridge/dashboard/index.html`
- [X] T005 [P] Create dashboard styles baseline in `mt5-connection-bridge/dashboard/css/dashboard.css`
- [X] T006 [P] Create dashboard script modules in `mt5-connection-bridge/dashboard/js/app.js`, `mt5-connection-bridge/dashboard/js/components.js`, and `mt5-connection-bridge/dashboard/js/chart.js`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend structures and shared models required before user-story implementation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T007 Create symbols response models in `mt5-connection-bridge/app/models/symbol.py`
- [X] T008 Create logs response models in `mt5-connection-bridge/app/models/log_entry.py`
- [X] T009 Create config response model including `multi_trade_overload_queue_threshold` in `mt5-connection-bridge/app/models/config_info.py`
- [X] T010 Create worker response model in `mt5-connection-bridge/app/models/worker_info.py`
- [X] T011 Create metrics response model in `mt5-connection-bridge/app/models/metrics.py`
- [X] T012 Implement rolling metrics service (90-day retention) in `mt5-connection-bridge/app/metrics.py`
- [X] T013 Extend runtime settings for execution/retention/overload policy (`MULTI_TRADE_OVERLOAD_QUEUE_THRESHOLD` default 100) in `mt5-connection-bridge/app/config.py`
- [X] T014 Register shared routers, middleware, and dashboard static mount in `mt5-connection-bridge/app/main.py`

**Checkpoint**: Foundation ready; story phases can begin.

---

## Phase 3: User Story 1 - Verify Bridge Operations (Priority: P1) 🎯 MVP

**Goal**: Deliver end-to-end verification for health, symbols, price retrieval, and status observability via dashboard and additive operational endpoints.

**Independent Test**: Authenticate in dashboard, load status/symbols, fetch prices and chart data, verify worker/metrics visibility and actionable errors.

### Tests for User Story 1

- [X] T015 [P] [US1] Add contract checks for `/symbols`, `/worker/state`, and `/metrics` in `mt5-connection-bridge/tests/contract/test_operational_contracts.py`
- [X] T016 [P] [US1] Add integration tests for status and prices journeys in `mt5-connection-bridge/tests/integration/test_health_route.py` and `mt5-connection-bridge/tests/integration/test_prices_route.py`
- [X] T017 [P] [US1] Add integration tests for symbols endpoint in `mt5-connection-bridge/tests/integration/test_symbols_route.py`
- [X] T018 [P] [US1] Add integration tests for worker and metrics endpoints in `mt5-connection-bridge/tests/integration/test_worker_route.py` and `mt5-connection-bridge/tests/integration/test_metrics_route.py`

### Implementation for User Story 1

- [X] T019 [US1] Implement configured symbol listing endpoint in `mt5-connection-bridge/app/routes/symbols.py`
- [X] T020 [US1] Implement worker state endpoint in `mt5-connection-bridge/app/routes/worker.py`
- [X] T021 [US1] Implement metrics endpoint wiring in `mt5-connection-bridge/app/routes/metrics.py`
- [X] T022 [US1] Include new operational routers in `mt5-connection-bridge/app/main.py`
- [X] T023 [US1] Implement dashboard auth/session flow and tab router in `mt5-connection-bridge/dashboard/js/app.js`
- [X] T024 [P] [US1] Implement Status and Symbols tab renderers in `mt5-connection-bridge/dashboard/js/components.js`
- [X] T025 [P] [US1] Implement Prices tab data table, export flow, and no-data/error states in `mt5-connection-bridge/dashboard/js/components.js`
- [X] T026 [US1] Implement candlestick chart rendering integration in `mt5-connection-bridge/dashboard/js/chart.js`

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Safely Validate Trade Execution Flow (Priority: P2)

**Goal**: Deliver guarded live-execution verification with default-off execution policy, multi-trade control behavior, logs, and sanitized config visibility.

**Independent Test**: Validate execute-tab safety controls, confirm blocked/allowed execution paths by policy/toggle state, and verify result traceability via logs/config views.

### Tests for User Story 2

- [X] T027 [P] [US2] Add contract checks for `/config` and `/logs` in `mt5-connection-bridge/tests/contract/test_execution_contracts.py`
- [X] T028 [P] [US2] Add integration tests for execute safety, pre-dispatch slippage rejection, post-fill slippage exception classification, fill-confirmed state transitions, overload-threshold rejection behavior, and parallel submission behavior in `mt5-connection-bridge/tests/integration/test_execute_route.py`
- [X] T029 [P] [US2] Add integration tests for config and logs endpoints in `mt5-connection-bridge/tests/integration/test_config_route.py` and `mt5-connection-bridge/tests/integration/test_logs_route.py`

### Implementation for User Story 2

- [X] T030 [US2] Implement sanitized runtime config endpoint with policy fields including `multi_trade_overload_queue_threshold` in `mt5-connection-bridge/app/routes/config_info.py`
- [X] T031 [US2] Implement paginated trade log endpoint in `mt5-connection-bridge/app/routes/logs.py`
- [X] T032 [US2] Enforce execution enablement gate, pre-dispatch slippage rejection, post-fill slippage exception classification, fill-confirmed state persistence, and overload-threshold rejection in `mt5-connection-bridge/app/routes/execute.py`
- [X] T033 [US2] Add multi-trade mode concurrency behavior with overload-threshold rejection handling in `mt5-connection-bridge/dashboard/js/app.js`
- [X] T034 [US2] Add execute-tab controls (environment badge, enablement state, checkbox, modal) in `mt5-connection-bridge/dashboard/js/components.js`
- [X] T035 [US2] Add multi-trade risk warning and stateful UI behavior in `mt5-connection-bridge/dashboard/js/components.js`
- [X] T036 [P] [US2] Implement Logs tab UI with pagination and refresh in `mt5-connection-bridge/dashboard/js/components.js`
- [X] T037 [P] [US2] Implement Config tab UI including `execution_enabled`, `metrics_retention_days`, and `multi_trade_overload_queue_threshold` in `mt5-connection-bridge/dashboard/js/components.js`

**Checkpoint**: User Stories 1 and 2 are independently functional and testable.

---

## Phase 5: User Story 3 - Regression-Safe Bridge Validation (Priority: P3)

**Goal**: Deliver complete automated regression safety net for bridge models, mappers, worker, routes, and compatibility contracts without native MT5 dependency.

**Independent Test**: Run full test suite in Linux/CI with MT5 mocked and verify regressions are detected across all required behaviors.

### Tests for User Story 3

- [X] T038 [P] [US3] Build shared MT5 mock fixtures and deterministic app fixtures in `mt5-connection-bridge/tests/conftest.py`
- [X] T039 [P] [US3] Add unit tests for config/symbol/timeframe handling in `mt5-connection-bridge/tests/unit/test_config.py`
- [X] T040 [P] [US3] Add unit tests for API key auth dependency in `mt5-connection-bridge/tests/unit/test_auth.py`
- [X] T041 [P] [US3] Add unit tests for price mapping behavior in `mt5-connection-bridge/tests/unit/test_price_mapper.py`
- [X] T042 [P] [US3] Add unit tests for trade mapping and lot normalization in `mt5-connection-bridge/tests/unit/test_trade_mapper.py`
- [X] T043 [P] [US3] Add unit tests for worker queue/state/reconnect behavior in `mt5-connection-bridge/tests/unit/test_mt5_worker.py`
- [X] T044 [P] [US3] Add route compatibility regression tests for existing endpoints in `mt5-connection-bridge/tests/integration/test_health_route.py`, `mt5-connection-bridge/tests/integration/test_prices_route.py`, and `mt5-connection-bridge/tests/integration/test_execute_route.py`
- [X] T045 [P] [US3] Add integration tests for all additive endpoints in `mt5-connection-bridge/tests/integration/test_symbols_route.py`, `mt5-connection-bridge/tests/integration/test_logs_route.py`, `mt5-connection-bridge/tests/integration/test_config_route.py`, `mt5-connection-bridge/tests/integration/test_worker_route.py`, and `mt5-connection-bridge/tests/integration/test_metrics_route.py`
- [X] T046 [P] [US3] Add contract conformance checks against OpenAPI schemas in `mt5-connection-bridge/tests/contract/test_openapi_conformance.py`

### Implementation for User Story 3

- [X] T047 [US3] Add test package structure initializers in `mt5-connection-bridge/tests/unit/__init__.py`, `mt5-connection-bridge/tests/integration/__init__.py`, and `mt5-connection-bridge/tests/contract/__init__.py`
- [X] T048 [US3] Add test execution, coverage-threshold, and benchmark command documentation in `mt5-connection-bridge/README.md`
- [X] T049 [US3] Align quickstart verification sequence with automated regression flow in `mt5-connection-bridge/specs/001-mt5-bridge-dashboard/quickstart.md`
- [X] T050 [P] [US3] Add MT5 tick/bar streaming non-regression tests in `mt5-connection-bridge/tests/integration/test_mt5_streaming_capability.py`
- [X] T051 [P] [US3] Add dashboard session policy tests (no inactivity timeout, tab close, credential invalidation) in `mt5-connection-bridge/tests/integration/test_dashboard_session_policy.py`
- [X] T052 [P] [US3] Enforce `>=90%` statement coverage gate in `mt5-connection-bridge/pytest.ini`
- [X] T053 [P] [US3] Add dashboard interaction latency benchmark tests for SC-003 in `mt5-connection-bridge/tests/performance/test_dashboard_latency.py`
- [X] T054 [P] [US3] Add log pagination benchmark test for 1,000 entries and median<=2s target in `mt5-connection-bridge/tests/performance/test_logs_pagination_performance.py`
- [X] T055 [US3] Add operator readiness timing validation protocol for SC-001 in `mt5-connection-bridge/specs/001-mt5-bridge-dashboard/quickstart.md`
- [X] T056 [P] [US3] Add metrics retention continuity tests validating review of at least 90 consecutive days in `mt5-connection-bridge/tests/integration/test_metrics_retention_window.py`
- [X] T057 [P] [US3] Add dedicated pre-dispatch slippage rejection, post-fill slippage exception, and MT5 fill-confirmation regression tests in `mt5-connection-bridge/tests/integration/test_execute_slippage_fill_state.py`
- [X] T058 [US3] Define and document SC-003 normal-load benchmark profile and SC-007 verification procedure in `mt5-connection-bridge/specs/001-mt5-bridge-dashboard/quickstart.md`

**Checkpoint**: All user stories are independently functional with regression safeguards.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, consistency validation, and release readiness.

- [X] T059 [P] Refresh bridge endpoint and dashboard documentation (traceability for FR-012 and SC-006) in `mt5-connection-bridge/README.md`
- [X] T060 [P] Finalize dashboard responsive styling and visual consistency (supporting FR-005 and FR-006 usability outcomes) in `mt5-connection-bridge/dashboard/css/dashboard.css`
- [X] T061 Validate API error handling consistency (`401/404/422/503`), reason+action messaging, and slippage/fill-confirmation outcome semantics across routes in `mt5-connection-bridge/app/routes/health.py`, `mt5-connection-bridge/app/routes/prices.py`, `mt5-connection-bridge/app/routes/execute.py`, `mt5-connection-bridge/app/routes/symbols.py`, `mt5-connection-bridge/app/routes/logs.py`, `mt5-connection-bridge/app/routes/config_info.py`, `mt5-connection-bridge/app/routes/worker.py`, and `mt5-connection-bridge/app/routes/metrics.py`
- [X] T062 Run and document quickstart smoke validation results with a consolidated execution-safety acceptance report (SC-001, SC-003, SC-005, SC-007, SC-009) in `mt5-connection-bridge/specs/001-mt5-bridge-dashboard/quickstart.md`
- [X] T063 Run full test suite and capture completion notes in `mt5-connection-bridge/specs/001-mt5-bridge-dashboard/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: starts immediately.
- **Phase 2 (Foundational)**: depends on Phase 1 and blocks all stories.
- **Phase 3 (US1)**: depends on Phase 2 completion.
- **Phase 4 (US2)**: depends on Phase 2 completion; may proceed after US1 core operational paths are stable.
- **Phase 5 (US3)**: depends on Phase 2 and should execute after US1/US2 implementation is materially complete for full regression scope.
- **Phase 6 (Polish)**: depends on target stories completed.

### User Story Dependencies

- **US1 (P1)**: no dependency on other stories after foundational phase.
- **US2 (P2)**: depends on foundational phase and integrates with execution paths established by existing bridge.
- **US3 (P3)**: depends on foundational phase and targets full regression across US1 and US2 deliverables.

### Story Completion Order

1. US1 (MVP)
2. US2
3. US3

### Parallel Opportunities

- Setup: `T003`, `T004`, `T005`, `T006` can run in parallel after `T001`/`T002` kickoff.
- Foundational: model tasks `T007`-`T011` can run in parallel.
- US1: tests `T015`-`T018` parallel; UI tasks `T024` and `T025` parallel.
- US2: tests `T027`-`T029` parallel; UI tasks `T036` and `T037` parallel.
- US3: tests `T038`-`T057` heavily parallelized across unit/integration/contract/performance files.

---

## Parallel Example: User Story 1

```bash
# Run US1 test authoring in parallel:
T015, T016, T017, T018

# Run independent UI implementations in parallel:
T024, T025
```

## Parallel Example: User Story 2

```bash
# Run US2 test authoring in parallel:
T027, T028, T029

# Run Logs/Config tab UI implementations in parallel:
T036, T037
```

## Parallel Example: User Story 3

```bash
# Run unit/integration/contract/performance test implementation in parallel:
T039, T040, T041, T042, T043, T044, T045, T046, T050, T051, T052, T053, T054, T056, T057
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 independent test criteria end-to-end.
4. Demo operational verification dashboard as MVP.

### Incremental Delivery

1. Deliver US1 for operational verification.
2. Deliver US2 for safe execution validation and traceability.
3. Deliver US3 for full regression safety and CI confidence.
4. Complete polish phase for documentation and hardening.

### Parallel Team Strategy

1. Team completes Setup + Foundational together.
2. Developer A executes backend endpoint tasks, Developer B executes dashboard UI tasks, Developer C executes test suite tasks where dependencies allow.
3. Merge by story checkpoints (US1 → US2 → US3).

---

## Notes

- All tasks follow required checklist format: `- [X] T### [P?] [US?] Description with file path`.
- Story labels are present on all user-story tasks and omitted in setup/foundational/polish phases.
- Test tasks are included because the specification explicitly requires automated testing.
- Suggested MVP scope: **User Story 1 only**.

## Completion Notes

- Date: 2026-03-02
- Full suite executed: `.venv/bin/python -m pytest`
- Result: `49 passed`
- Coverage gate: `90.13%` (threshold `>=90%`)
- Scope validated: setup, foundational, US1, US2, US3, and polish tasks completed.
