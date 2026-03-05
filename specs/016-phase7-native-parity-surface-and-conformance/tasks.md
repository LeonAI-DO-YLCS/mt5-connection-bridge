# Tasks: Phase 7 — Native Parity Surface and Conformance

**Input**: Design documents from `/specs/016-phase7-native-parity-surface-and-conformance/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md

**Organization**: Tasks grouped by user story. Each phase is independently dispatchable to one Jules agent.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- All file paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new directories, config files, and shared models that all stories depend on.

- [ ] T001 Create `app/conformance/` directory with empty `__init__.py` at `app/conformance/__init__.py`
- [ ] T002 [P] Create `config/` directory and empty `config/governance-checklist.yaml` scaffold (YAML with top-level `endpoints: {}` key)
- [ ] T003 [P] Create `config/compatibility-profiles.yaml` with the three named profiles (`strict_safe`, `balanced`, `max_compat`) and their four dimensions per research.md §4 profile matrix
- [ ] T004 [P] Create `CompatibilityProfile` Pydantic model in `app/models/compatibility.py` per data-model.md (fields: `name`, `retry_aggressiveness`, `optional_field_handling`, `gating_strictness`, `warning_verbosity`)
- [ ] T005 [P] Create `ConformanceResult` and `ConformanceReport` Pydantic models in `app/models/conformance.py` per data-model.md
- [ ] T006 Add `COMPATIBILITY_PROFILE` setting to `app/config.py` (`str`, default `"strict_safe"`, alias `COMPATIBILITY_PROFILE`). Add helper `get_compatibility_profile()` that loads the YAML and returns the matching `CompatibilityProfile` instance.

**Checkpoint**: Directory structure exists, shared models importable, profiles YAML loadable.

---

## Phase 2: US1 — Safe Domain Extensions (Priority: P1) 🎯 MVP

**Goal**: Add `POST /margin-check` and `POST /profit-calc` to the safe domain API — the two calculation endpoints missing from the parity matrix. Wrapped in canonical envelope, readiness-gated.

**Independent Test**: `curl -X POST /margin-check -d '{"symbol":"EURUSD","volume":1.0,"action":"buy"}'` returns canonical envelope with `margin`, `free_margin`, `margin_rate`.

- [ ] T007 [P] [US1] Create `MarginCheckRequest` and `MarginCheckResponse` Pydantic models in `app/models/margin.py` per data-model.md
- [ ] T008 [P] [US1] Create `ProfitCalcRequest` and `ProfitCalcResponse` Pydantic models in `app/models/margin.py` (same file, co-located)
- [ ] T009 [US1] Implement `POST /margin-check` route in `app/routes/margin_check.py`: validate request, resolve symbol via `symbol_map`, call `mt5.order_calc_margin()` through worker `submit()`, wrap in canonical envelope, gate on readiness (worker state must be `AUTHORIZED`)
- [ ] T010 [US1] Implement `POST /profit-calc` route in `app/routes/profit_calc.py`: validate request, call `mt5.order_calc_profit()` through worker `submit()`, wrap in canonical envelope, readiness-gated
- [ ] T011 [US1] Register `margin_check_router` and `profit_calc_router` in `app/routes/__init__.py` and mount in the FastAPI app
- [ ] T012 [US1] Write unit tests for margin-check and profit-calc in `tests/unit/test_margin_check.py` and `tests/unit/test_profit_calc.py` — mock `mt5.order_calc_margin` and `mt5.order_calc_profit`, verify canonical envelope shape, error codes, readiness gating

**Checkpoint**: Safe domain calculation endpoints operational. Standard operators can calculate margin/profit without expert namespace.

---

## Phase 3: US2 — Expert/Advanced Namespace (Priority: P2)

**Goal**: Introduce the `/mt5/raw/` expert namespace with read-heavy endpoints: margin-check, profit-calc, market-book, terminal-info, account-info, last-error. Every response includes `namespace: "advanced"` and `safety_disclaimer`.

**Independent Test**: `curl /mt5/raw/margin-check?symbol=EURUSD&volume=1&action=buy` returns response with `namespace`, `safety_disclaimer`, and raw data.

- [ ] T013 [P] [US2] Create `MarketBookEntry` Pydantic model in `app/models/market_book.py` per data-model.md
- [ ] T014 [US2] Create expert namespace router in `app/routes/raw_namespace.py`:
  - FastAPI `APIRouter(prefix="/mt5/raw", tags=["advanced"])` with `api_key_dependency`
  - `GET /margin-check` — query params `symbol`, `volume`, `action`; calls `mt5.order_calc_margin()` via worker; response includes `namespace`, `safety_disclaimer`
  - `GET /profit-calc` — query params `symbol`, `volume`, `action`, `price_open`, `price_close`; calls `mt5.order_calc_profit()` via worker
  - `GET /market-book` — query param `symbol`; calls `mt5.market_book_add()`, `mt5.market_book_get()`, `mt5.market_book_release()` via worker; returns list of `MarketBookEntry`
  - `GET /terminal-info` — calls `mt5.terminal_info()` via worker; returns all fields (not curated)
  - `GET /account-info` — calls `mt5.account_info()` via worker; returns all fields
  - `GET /last-error` — calls `mt5.last_error()` via worker; returns raw error tuple
- [ ] T015 [US2] Register `raw_namespace_router` in `app/routes/__init__.py` and mount in the FastAPI app
- [ ] T016 [US2] Write unit tests for raw namespace in `tests/unit/test_raw_namespace.py` — mock MT5 functions, verify `namespace` and `safety_disclaimer` fields present in all responses, verify auth required, verify market-book lifecycle

**Checkpoint**: Expert namespace endpoints accessible to advanced users via API key. Safe domain unaffected.

---

## Phase 4: US3 — Compatibility Profiles (Priority: P3)

**Goal**: Support three named operational profiles (`strict_safe`, `balanced`, `max_compat`) that control bridge behavior. Switchable at runtime via env var, exposed in `/diagnostics/runtime`, change logged.

**Independent Test**: Set `COMPATIBILITY_PROFILE=balanced`, call `GET /diagnostics/runtime`, verify profile appears in response with all four dimensions.

- [ ] T017 [US3] Modify `app/routes/diagnostics.py` to include `compatibility_profile` object in the `/diagnostics/runtime` response — read from `get_compatibility_profile()` helper in config
- [ ] T018 [US3] Implement profile-change audit logging in `app/config.py`: when `get_compatibility_profile()` detects a different profile than last loaded, emit a structured log entry `{ event: "compatibility_profile_changed", old_profile: "...", new_profile: "...", timestamp: "..." }`
- [ ] T019 [US3] Write unit tests for compatibility profiles in `tests/unit/test_compatibility.py` — test profile loading from YAML, default profile, invalid profile handling, diagnostics response shape, audit log emission

**Checkpoint**: Operator can switch profiles via env var without restart, observe in runtime diagnostics, and see audit log.

---

## Phase 5: US4 — Conformance Harness (Priority: P4)

**Goal**: Build a CLI-runnable conformance suite (`python -m app.conformance`) that exercises the bridge API against a connected broker and produces JSON + Markdown reports with a production compatibility mode recommendation.

**Independent Test**: `python -m app.conformance --base-url http://localhost:8001 --api-key test --output-json /tmp/conformance.json` produces a valid ConformanceReport JSON.

- [ ] T020 [P] [US4] Create conformance CLI entry point at `app/conformance/__main__.py` — argparse with `--base-url`, `--api-key`, `--include-write-tests`, `--output-json`, `--output-md`
- [ ] T021 [P] [US4] Create conformance test runner at `app/conformance/runner.py` — orchestrates probe execution by category, collects `ConformanceResult` list, builds `ConformanceReport`
- [ ] T022 [P] [US4] Create connection probe at `app/conformance/probes/connection.py` — tests `/health`, `/diagnostics/runtime`, `/readiness`; returns list of `ConformanceResult`
- [ ] T023 [P] [US4] Create symbols probe at `app/conformance/probes/symbols.py` — tests `/broker-capabilities`, symbol resolution; returns `ConformanceResult` list
- [ ] T024 [P] [US4] Create pricing probe at `app/conformance/probes/pricing.py` — tests `/tick/{symbol}`, price data availability; returns `ConformanceResult` list
- [ ] T025 [P] [US4] Create calculations probe at `app/conformance/probes/calculations.py` — tests `/margin-check`, `/profit-calc`, `/mt5/raw/margin-check`, `/mt5/raw/profit-calc`; returns `ConformanceResult` list
- [ ] T026 [P] [US4] Create market-book probe at `app/conformance/probes/market_book.py` — tests `/mt5/raw/market-book`; handles `not_supported` gracefully; returns `ConformanceResult` list
- [ ] T027 [P] [US4] Create write-tests probe at `app/conformance/probes/write_tests.py` — opt-in only (skipped unless `--include-write-tests`); tests order send + immediate cancel on test account; returns `ConformanceResult` list
- [ ] T028 [US4] Create report generator at `app/conformance/reporter.py` — takes `ConformanceReport`, writes JSON to stdout or file, generates Markdown summary with pass/warn/fail table, recommendation section per contracts/api-contracts.md §Conformance CLI
- [ ] T029 [US4] Create `app/conformance/probes/__init__.py` that exports all probe modules
- [ ] T030 [US4] Wire runner to discover and execute all probes, compute summary stats, generate recommendation based on pass/warn/fail ratios, output via reporter
- [ ] T031 [US4] Write integration test for conformance harness in `tests/integration/test_conformance.py` — mock bridge API responses, verify report structure matches `ConformanceReport` model, verify JSON and Markdown output

**Checkpoint**: Operator can run conformance suite against any broker environment and receive a structured report with compatibility recommendation.

---

## Phase 6: US5 — Governance & Coverage Matrix (Priority: P5)

**Goal**: Establish a machine-readable governance checklist for all raw endpoints and a parity coverage matrix tracking MT5 capability coverage.

**Independent Test**: Parse `config/governance-checklist.yaml` — every `/mt5/raw/*` endpoint has `safety_class`, `auth_required`, `logging_policy`, `readiness_gated`, `approved_by`, `approved_date`.

- [ ] T032 [P] [US5] Create `GovernanceEntry` Pydantic model in `app/models/conformance.py` (append to existing file) per data-model.md
- [ ] T033 [P] [US5] Create `ParityCoverageEntry` Pydantic model in `app/models/conformance.py` (append to existing file) per data-model.md
- [ ] T034 [US5] Populate `config/governance-checklist.yaml` with governance entries for all 6 raw endpoints: `/mt5/raw/margin-check`, `/mt5/raw/profit-calc`, `/mt5/raw/market-book`, `/mt5/raw/terminal-info`, `/mt5/raw/account-info`, `/mt5/raw/last-error` — each with `safety_class`, `auth_required`, `logging_policy`, `readiness_gated`
- [ ] T035 [US5] Create `config/parity-coverage-matrix.yaml` with the 7 MT5 capability categories from research.md §1 — fill `implemented`, `safe_domain_endpoint`, `raw_endpoint`, `constraints`, `known_broker_variance`, `test_coverage` for each capability
- [ ] T036 [US5] Create a governance validation script at `scripts/validate_governance.py` that loads the YAML and validates all raw endpoints have complete governance entries — exit non-zero if any field is missing

**Checkpoint**: Full governance and coverage documentation in place. Machine-readable and validatable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, documentation, and validation.

- [ ] T037 Update `specs/016-phase7-native-parity-surface-and-conformance/quickstart.md` with actual CLI commands for all new endpoints and conformance harness
- [ ] T038 Verify no existing safe domain endpoints are affected — run full `pytest` suite and confirm all prior tests pass
- [ ] T039 Run governance validation script: `python scripts/validate_governance.py`
- [ ] T040 Run conformance suite dry-run (if MT5 available): `python -m app.conformance --base-url http://localhost:8001 --api-key test --output-json /tmp/conformance.json`
- [ ] T041 Code cleanup — ensure all new files have module docstrings, type hints, and follow project conventions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (US1 — Safe Domain)**: Depends on T004, T006 from Phase 1
- **Phase 3 (US2 — Expert Namespace)**: Depends on Phase 1 complete; can run in parallel with Phase 2
- **Phase 4 (US3 — Compatibility)**: Depends on T004, T006 from Phase 1; can run in parallel with Phases 2/3
- **Phase 5 (US4 — Conformance)**: Depends on Phases 2 + 3 (needs endpoints to test)
- **Phase 6 (US5 — Governance)**: Depends on Phase 3 (needs raw endpoint list); can run in parallel with Phase 5
- **Phase 7 (Polish)**: Depends on all prior phases

### Parallel Dispatch Strategy (Jules Agents)

```text
Agent 1: Phase 1 (Setup)        ← runs first, blocks others
Agent 2: Phase 2 (US1)          ← after Phase 1
Agent 3: Phase 3 (US2)          ← after Phase 1, parallel with Agent 2
Agent 4: Phase 4 (US3)          ← after Phase 1, parallel with Agents 2/3
Agent 5: Phase 5 (US4)          ← after Agents 2+3 complete
Agent 6: Phase 6 (US5)          ← after Agent 3, parallel with Agent 5
Agent 7: Phase 7 (Polish)       ← after all agents complete
```

### Within Each Phase

- Tasks marked `[P]` within a phase can run in parallel
- Models before services/routes
- Implementation before tests
- Registration (T011, T015) after route implementation

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: US1 — Safe Domain Extensions
3. **STOP and VALIDATE**: Margin-check + profit-calc working with canonical envelope
4. This alone closes the primary parity gap

### Incremental Delivery

1. Phase 1 (Setup) → shared infrastructure ready
2. Phase 2 (US1) → margin/profit calcs in safe domain (MVP)
3. Phase 3 (US2) → expert namespace deployed
4. Phase 4 (US3) → compatibility profiles active
5. Phase 5 (US4) → conformance harness runnable
6. Phase 6 (US5) → governance + coverage matrix complete
7. Phase 7 (Polish) → documentation, validation, cleanup

---

## Notes

- All new routes follow existing patterns: `APIRouter`, `api_key_dependency`, canonical envelope wrapping
- Expert namespace (`/mt5/raw/`) is read-heavy initially per spec assumptions — no raw `order_send`
- Conformance harness uses bridge API (not direct MT5 calls) per spec
- Dashboard is NOT modified this phase (per plan.md)
- Total: 41 tasks across 7 phases
