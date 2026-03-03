# Tasks: Phase 0 — Baseline and Constraints

**Branch**: `009-phase0-baseline-and-constraints`
**Input**: Design documents from `specs/009-phase0-baseline-and-constraints/`
**Spec**: `specs/009-phase0-baseline-and-constraints/spec.md`
**Plan**: `specs/009-phase0-baseline-and-constraints/plan.md`
**Date**: 2026-03-03

---

## User Story Map

| Story | FRs        | Priority | Summary                                               |
| ----- | ---------- | -------- | ----------------------------------------------------- |
| US1   | FR-013–014 | P1 🔴    | Existing-state snapshot (endpoint + script inventory) |
| US2   | FR-001–002 | P1 🔴    | Terminology glossary + severity scale                 |
| US3   | FR-003–004 | P1 🔴    | Canonical tracking ID policy                          |
| US4   | FR-005–006 | P1 🔴    | Error-code namespace policy                           |
| US5   | FR-007–008 | P1 🔴    | Compatibility pledge                                  |
| US6   | FR-009–010 | P2 🟠    | Launcher invariants checklist                         |
| US7   | FR-011–012 | P2 🟠    | MT5 parity gap register                               |

> **Note**: US1 (endpoint snapshot) is sequenced first because all other deliverables reference it — the glossary, error namespace, and compatibility pledge need to cite real endpoints as examples.

---

## Phase 1: Setup

- [x] T001 Create directory structure `docs/baseline/` from repository root
- [x] T002 Verify all spec and plan artifacts exist in `specs/009-phase0-baseline-and-constraints/` — confirm `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/document-schemas.md` are present

---

## Phase 2: Foundational — Existing-State Snapshot (US1, P1 🔴)

> **Blocks**: US2 (glossary needs real examples), US4 (error namespace needs existing codes), US5 (pledge needs endpoint list). Complete before all other phases.

**Story Goal**: Produce a comprehensive snapshot of every endpoint and operational script in the bridge as of 2026-03-03, so subsequent phases have a testable regression surface and a "do not remove" list.

**Independent Test Criteria**: Read `docs/baseline/endpoint-snapshot.md` — cross-reference against `app/main.py` router registrations: every registered router must appear in the snapshot. Read `scripts/` directory — every script must appear in the scripts inventory table.

### Implementation

- [x] T003 [US1] Create `docs/baseline/endpoint-snapshot.md` — add header with title, snapshot date (2026-03-03), bridge version (1.2.0), re-snapshot instructions
- [x] T004 [US1] Add "Health and Diagnostics" endpoint table to `docs/baseline/endpoint-snapshot.md` — list `/health`, `/worker/state`, `/metrics`, `/diagnostics/runtime`, `/diagnostics/symbols`, `/logs` with method, module, purpose, response shape summary, auth status
- [x] T005 [US1] Add "Market and Symbol Data" endpoint table to `docs/baseline/endpoint-snapshot.md` — list `/symbols`, `/broker-symbols`, `/broker-capabilities`, `/broker-capabilities/refresh`, `/tick/{ticker}`, `/prices` with full details
- [x] T006 [US1] Add "Trade Operations" endpoint table to `docs/baseline/endpoint-snapshot.md` — list `/execute`, `/pending-order`, `/close-position`, `/order-check`, `/orders`, `/orders/{ticket}` (PUT), `/orders/{ticket}` (DELETE), `/positions`, `/positions/{ticket}/sltp` with full details
- [x] T007 [US1] Add "Account and Terminal" endpoint table to `docs/baseline/endpoint-snapshot.md` — list `/account`, `/terminal`, `/history/deals`, `/history/orders` with full details
- [x] T008 [US1] Add "Configuration" endpoint table to `docs/baseline/endpoint-snapshot.md` — list `/config` with full details
- [x] T009 [US1] Add "Dashboard" static mount entry to `docs/baseline/endpoint-snapshot.md` — document `/dashboard` mount from `dashboard/` directory
- [x] T010 [US1] Add "Operational Scripts Inventory" table to `docs/baseline/endpoint-snapshot.md` — list all 8 scripts in `scripts/` and the PowerShell script in `scripts/windows/`: name, purpose, invocation pattern, Phase 5 relevance assessment

---

## Phase 3: Terminology Glossary (US2, P1 🔴)

> **Requires**: Phase 2 (needs endpoint examples for concrete triggers). **Blocks**: US4 (error codes reference severity from glossary).

**Story Goal**: Produce a team-agreed glossary defining `error`, `warning`, `status`, `advice`, `blocker`, and `recovery` with a 4-level severity scale — so any team member can categorize a new runtime event without ambiguity.

**Independent Test Criteria**: Given a novel runtime event description (e.g., "MT5 login credentials expired"), a reader can assign it to exactly one term + severity using only the glossary — validated by peer-review sign-off.

### Implementation

- [x] T011 [US2] Create `docs/baseline/glossary.md` — add header with title, snapshot date, last-reviewed date placeholder
- [x] T012 [US2] Add "Core Terms" table to `docs/baseline/glossary.md` — define all 6 terms (`error`, `warning`, `status`, `advice`, `blocker`, `recovery`) with columns: Term, Definition, Example Trigger, Dashboard Treatment
  - `error`: An operation failed and cannot complete. Example: `order_send returned None` (close_position.py line 121). Dashboard: red banner.
  - `warning`: A condition exists that may cause problems but does not prevent current operation. Example: `symbol trade_mode=1 (Long Only)`. Dashboard: orange inline alert.
  - `status`: A neutral factual event requiring no action. Example: worker state transition to `AUTHORIZED`. Dashboard: info text.
  - `advice`: A recommended action for the operator to improve outcomes. Example: "Consider restarting bridge — uptime > 72h". Dashboard: blue suggestion.
  - `blocker`: A system-level condition preventing all operations until resolved. Example: worker state `DISCONNECTED` after 5 retries. Dashboard: red lock overlay.
  - `recovery`: A previously failed condition has resolved itself. Example: successful reconnect after `RECONNECTING`. Dashboard: green transient toast.
- [x] T013 [US2] Add "Severity Scale" table to `docs/baseline/glossary.md` — define 4 levels with columns: Level, Criteria, Action Required, Example
  - `critical`: System unavailable or operation unsafe. Immediate attention. Example: MT5 terminal disconnected after all retries.
  - `high`: Operation blocked, operator intervention needed. Example: `EXECUTION_DISABLED` policy prevents all trades.
  - `medium`: Operation blocked but user-correctable. Example: invalid volume step size on close request.
  - `low`: Non-blocking advisory notice. Example: stale tick data older than 5 minutes.
- [x] T014 [US2] Add "Usage Notes" section to `docs/baseline/glossary.md` — document how to apply the glossary when categorizing new events in future phases: (1) identify the scope, (2) match the term, (3) assign severity, (4) note the dashboard treatment

---

## Phase 4: Tracking ID Policy (US3, P1 🔴)

> **Requires**: Phase 2 (propagation path references endpoints). **Can run in parallel with Phase 3** (different document, independent content).

**Story Goal**: Define the `tracking_id` format so any team member can locate the corresponding backend log entry within 60 seconds given a dashboard screenshot.

**Independent Test Criteria**: Generate a sample `tracking_id` following the spec → grep the JSONL log directory for it → confirm it resolves to exactly one log entry.

### Implementation

- [x] T015 [P] [US3] Create `docs/baseline/tracking-id-policy.md` — add header with title, effective date, format version
- [x] T016 [P] [US3] Add "Format Specification" section to `docs/baseline/tracking-id-policy.md` — define pattern `brg-<YYYYMMDDTHHMMSS>-<hex4>`, character constraints (lowercase hex, hyphens, digits), total length ≤ 30 chars, worked example: `brg-20260303T094500-a3f7`
- [x] T017 [P] [US3] Add "Generation Rules" section to `docs/baseline/tracking-id-policy.md` — specify: generated at request entry point (middleware or route handler), uses UTC timestamp at generation time, 4-character random hex from `secrets.token_hex(2)`, one ID per inbound request, stored in request scope
- [x] T018 [P] [US3] Add "Propagation Path" section to `docs/baseline/tracking-id-policy.md` — document the chain: (1) generated in backend → (2) attached to structured JSONL log entry → (3) returned in response header `X-Tracking-ID` → (4) read and displayed by dashboard JS
- [x] T019 [P] [US3] Add "Log Correlation Guide" section to `docs/baseline/tracking-id-policy.md` — step-by-step: (1) copy tracking ID from dashboard screenshot, (2) grep `logs/dashboard/trades.jsonl` or `logs/dashboard/tasks.jsonl` for the ID, (3) read the matching JSON line for full context. Include a worked terminal command example

---

## Phase 5: Error-Code Namespace Policy (US4, P1 🔴)

> **Requires**: Phase 3 (severity scale from glossary). **Can run in parallel with Phase 4** (different document).

**Story Goal**: Define a stable error-code namespace so no two codes have the same semantic meaning — validated by a namespace review sign-off before Phase 1 begins.

**Independent Test Criteria**: Read the initial code registry table — assert every code is unique, every code maps to exactly one domain prefix, and the 5 required failure categories are covered.

### Implementation

- [x] T020 [P] [US4] Create `docs/baseline/error-code-namespace.md` — add header with title, effective date, namespace version
- [x] T021 [P] [US4] Add "Naming Convention" section to `docs/baseline/error-code-namespace.md` — define pattern `<DOMAIN>_<CONDITION>` in uppercase with underscores; allowed domain prefixes: `VALIDATION_`, `MT5_`, `EXECUTION_`, `WORKER_`, `SYMBOL_`, `REQUEST_`, `INTERNAL_`
- [x] T022 [P] [US4] Add "Initial Code Registry" table to `docs/baseline/error-code-namespace.md` — enumerate all existing codes from `app/main.py._infer_error_code()` plus any new codes needed for the 5 required categories:

  **Validation failures**: `VALIDATION_ERROR` (422)
  **Connectivity/runtime failures**: `MT5_DISCONNECTED` (503), `SERVICE_UNAVAILABLE` (503), `INTERNAL_SERVER_ERROR` (500)
  **Policy/capability failures**: `EXECUTION_DISABLED` (403), `OVERLOAD_OR_SINGLE_FLIGHT` (409)
  **Request-compatibility failures**: `SYMBOL_NOT_CONFIGURED` (404), `RESOURCE_NOT_FOUND` (404), `UNAUTHORIZED_API_KEY` (401)
  **Generic fallback**: `REQUEST_ERROR` (4xx)

  Columns: Code, Domain Prefix, Description, HTTP Status, Severity (from glossary), Phase Introduced (all "Phase 0 — initial")

- [x] T023 [P] [US4] Add "Governance Rules" section to `docs/baseline/error-code-namespace.md` — define: (1) new codes must be checked against this registry before adoption — no semantic duplicates, (2) codes are never removed, only deprecated with a successor noted, (3) adding a new code requires updating this document with `phase_introduced` field, (4) domain prefix must be from the allowed set or a new domain must be formally approved
- [x] T024 [P] [US4] Add "Minimum Required Codes" section to `docs/baseline/error-code-namespace.md` — verify coverage of all 5 failure categories with at least one code each; list any gaps

---

## Phase 6: Compatibility Pledge (US5, P1 🔴)

> **Requires**: Phase 2 (endpoint snapshot is the source list). **Can run in parallel with Phases 3–5** (different document).

**Story Goal**: Produce a per-endpoint stability commitment so any developer reviewing a change knows exactly what can and cannot change.

**Independent Test Criteria**: Read the pledge table — assert 100% of endpoints from `endpoint-snapshot.md` appear, each with a stated stability level.

### Implementation

- [x] T025 [P] [US5] Create `docs/baseline/compatibility-pledge.md` — add header with title, effective date, pledge version
- [x] T026 [P] [US5] Add "Pledge Summary" section to `docs/baseline/compatibility-pledge.md` — state the overall policy: endpoint contracts listed as `frozen` will not change their response shape or HTTP semantics across the full phased rollout; `evolving` endpoints may add new response fields but will not remove or rename existing ones; `migrating` endpoints will receive a new canonical response shape alongside the legacy one during a stated compatibility window
- [x] T027 [P] [US5] Add "Endpoint Pledge Table" to `docs/baseline/compatibility-pledge.md` — one row per endpoint family from `endpoint-snapshot.md`:

  | Endpoint Family | Stability Level | Phases That May Change It | Compatibility Window | Migration Notes |

  Category assignments (from plan research):
  - `/health`, `/worker/state`, `/metrics`, `/account`, `/terminal` → `frozen`
  - `/diagnostics/*`, `/logs`, `/config`, `/symbols` → `evolving` (may add fields)
  - `/execute`, `/close-position`, `/pending-order`, `/orders/*`, `/positions/*` → `migrating` (response envelope will change in Phase 1; legacy `detail` shape maintained through Phase 5, removed after Phase 6)
  - `/broker-capabilities`, `/broker-symbols`, `/tick/*`, `/prices` → `evolving`
  - `/order-check`, `/history/*` → `evolving`

- [x] T028 [P] [US5] Add "Legacy Support Window" section to `docs/baseline/compatibility-pledge.md` — explicitly state: legacy `detail`-shaped error responses remain supported through Phases 1–5; they are retired only after Phase 6 (Dashboard Operator Experience) is deployed and validated; consumers must migrate to the canonical `MessageEnvelope` by Phase 6 completion
- [x] T029 [P] [US5] Add "Consumer Migration Guide" section to `docs/baseline/compatibility-pledge.md` — document what consumers must do to adopt the canonical envelope: (1) read `message` instead of `detail`, (2) read `error_code` from response body instead of `X-Error-Code` header, (3) read `tracking_id` from response body instead of computing it. Note: the canonical envelope schema will be defined in Phase 1

---

## Phase 7: Launcher Invariants Checklist (US6, P2 🟠)

> **Requires**: Phase 2 (scripts inventory). **Blocks**: Phase 5 spec (launcher hardening uses this as a gate).

**Story Goal**: Produce an explicit checklist of launcher and script behaviors that must NOT change in any phase — used as a mandatory gate in code review.

**Independent Test Criteria**: The checklist is used as a required gate for the first Phase 5 code review — its presence and use is the acceptance test.

### Implementation

- [x] T030 [P] [US6] Create `docs/baseline/launcher-invariants.md` — add header with title, effective date, checklist version
- [x] T031 [P] [US6] Add "Invariant Registry" table to `docs/baseline/launcher-invariants.md` — one invariant per critical behavior with columns: ID, Category, Description, Current Behavior, Verification Method

  Required invariants (from research.md §3):
  - `LI-001` `script_name`: `start_bridge.sh` name and location must not change
  - `LI-002` `script_name`: `stop_bridge.sh` name and location must not change
  - `LI-003` `script_name`: `restart_bridge.sh` name and location must not change
  - `LI-004` `script_name`: `smoke_bridge.sh` name and location must not change
  - `LI-005` `script_name`: `launch_bridge_dashboard.sh` name and location must not change
  - `LI-006` `script_name`: `launch_bridge_windows.sh` name and location must not change
  - `LI-007` `invocation_pattern`: All scripts accept `MT5_BRIDGE_PORT` and `MT5_BRIDGE_API_KEY` from environment or `.env`
  - `LI-008` `restart_policy`: `launch_bridge_dashboard.sh` attempts exactly 1 auto-restart on unexpected exit
  - `LI-009` `log_structure`: Log bundles are written to `logs/bridge/launcher/<run-id>/` with `launcher.log`, `bridge.stdout.log`, `bridge.stderr.log`, `session.json`
  - `LI-010` `log_structure`: `session.json` contains `run_id`, `started_at_utc`, `ended_at_utc`, `exit_code`, `termination_reason`, `restart_attempted`, `restart_successful`
  - `LI-011` `smoke_test`: `smoke_bridge.sh` probes `GET /health` and returns 0 on 200, non-zero on failure
  - `LI-012` `env_var`: `LAUNCHER_PREFER_WINDOWS` controls WSL→Windows bridge dispatch (default `true`)
  - `LI-013` `invocation_pattern`: `test-fast.sh` and `test-full.sh` names and invocation patterns must not change

- [x] T032 [P] [US6] Add "Review Gate Instructions" section to `docs/baseline/launcher-invariants.md` — instruct code reviewers: (1) for any PR touching `scripts/`, the reviewer must open this checklist, (2) verify every invariant is still satisfied, (3) if an invariant would be violated, the PR must include a formal exception approval comment citing the invariant ID and justification
- [x] T033 [P] [US6] Add "Exception Process" section to `docs/baseline/launcher-invariants.md` — document: (1) request a variance by opening an issue citing the invariant ID, (2) get approval from a second team member, (3) update this document with the exception record and date

---

## Phase 8: MT5 Parity Gap Register (US7, P2 🟠)

> **Requires**: Phase 2 (endpoint snapshot for coverage cross-reference). **Can run in parallel with Phase 7** (different document).

**Story Goal**: Produce a structured inventory of MT5 Python API capability coverage vs. current bridge implementation — sufficient to guide Phase 7 scoping.

**Independent Test Criteria**: Read the register — assert all 7 MT5 capability categories (from research.md §6.5) are present, each with at least one function entry, and `bridge_coverage` fields are populated.

### Implementation

- [x] T034 [P] [US7] Create `docs/baseline/parity-gap-register.md` — add header with title, snapshot date, bridge version
- [x] T035 [P] [US7] Add "Category 1: Connection and Session Lifecycle" table to `docs/baseline/parity-gap-register.md` — cover `mt5.initialize`, `mt5.shutdown`, `mt5.login`, `mt5.last_error` with coverage, constraints, broker variance, fallback, test coverage, operator impact
- [x] T036 [P] [US7] Add "Category 2: Terminal and Account Metadata" table to `docs/baseline/parity-gap-register.md` — cover `mt5.terminal_info`, `mt5.account_info`, `mt5.version`
- [x] T037 [P] [US7] Add "Category 3: Symbol and Market Data" table to `docs/baseline/parity-gap-register.md` — cover `mt5.symbols_get`, `mt5.symbols_total`, `mt5.symbol_info`, `mt5.symbol_info_tick`, `mt5.symbol_select`, `mt5.market_book_add`, `mt5.market_book_get`, `mt5.market_book_release`
- [x] T038 [P] [US7] Add "Category 4: Order Pre-check and Calculations" table to `docs/baseline/parity-gap-register.md` — cover `mt5.order_check`, `mt5.order_calc_margin`, `mt5.order_calc_profit`
- [x] T039 [P] [US7] Add "Category 5: Order Submission and Management" table to `docs/baseline/parity-gap-register.md` — cover `mt5.order_send`, `mt5.positions_get`, `mt5.positions_total`, `mt5.orders_get`, `mt5.orders_total`
- [x] T040 [P] [US7] Add "Category 6: History and Reporting" table to `docs/baseline/parity-gap-register.md` — cover `mt5.history_deals_get`, `mt5.history_deals_total`, `mt5.history_orders_get`, `mt5.history_orders_total`, `mt5.copy_rates_from`, `mt5.copy_rates_from_pos`, `mt5.copy_rates_range`, `mt5.copy_ticks_from`, `mt5.copy_ticks_range`
- [x] T041 [P] [US7] Add "Category 7: Advanced Facilities" table to `docs/baseline/parity-gap-register.md` — cover market book depth (DOM), custom indicator data access. Note: these are explicitly deferred/optional per Phase 7 plan
- [x] T042 [P] [US7] Add "Summary Statistics" section to `docs/baseline/parity-gap-register.md` — count functions per coverage level (full/partial/none), note overall coverage percentage, identify top-3 highest-impact gaps for Phase 7 prioritization

---

## Phase 9: Polish & Cross-Cutting Concerns

> **Requires**: All phases complete. Run as final sweep.

- [x] T043 [P] Cross-reference `docs/baseline/compatibility-pledge.md` endpoint list against `docs/baseline/endpoint-snapshot.md` — verify 100% coverage; fix any mismatches
- [x] T044 [P] Cross-reference `docs/baseline/launcher-invariants.md` script list against `docs/baseline/endpoint-snapshot.md` scripts table — verify all scripts appear; fix any mismatches
- [x] T045 [P] Cross-reference `docs/baseline/error-code-namespace.md` code list against `app/main.py._infer_error_code()` — verify all 10 existing codes are documented; fix any mismatches
- [x] T046 [P] Verify `docs/baseline/parity-gap-register.md` covers all 7 MT5 capability categories — confirm each has at least one function entry
- [x] T047 [P] Review all 7 documents for internal consistency — term usage must match glossary definitions; severity references must match the severity scale table
- [x] T048 Add a `docs/baseline/README.md` index file linking to all 7 documents with one-line descriptions and phase dependency notes

---

## Dependency Graph

```
Phase 2 (US1 — Endpoint Snapshot)
  └──► Phase 3 (US2 — Glossary)
  │       └──► Phase 5 (US4 — Error Namespace)  ← needs severity from glossary
  └──► Phase 4 (US3 — Tracking ID Policy)       ← parallel with Phase 3
  └──► Phase 6 (US5 — Compatibility Pledge)      ← parallel with Phase 3, 4
  └──► Phase 7 (US6 — Launcher Invariants)       ← parallel with Phase 3–6
  └──► Phase 8 (US7 — Parity Gap Register)       ← parallel with Phase 7

Phase 9 (Polish) ← requires all above complete
```

---

## Parallel Execution Examples

### Sprint 1: Foundation (Phase 2 only — must complete first)

```
T003–T010  docs/baseline/endpoint-snapshot.md — all sequential, same file
```

### Sprint 2: Core Documents (Phases 3–6 — mostly parallel, different files)

```
T011–T014  docs/baseline/glossary.md           ← sequential within, blocks Phase 5
T015–T019  [P] docs/baseline/tracking-id-policy.md  ← fully parallel with glossary
T025–T029  [P] docs/baseline/compatibility-pledge.md ← fully parallel with glossary + tracking ID
T020–T024  [P] docs/baseline/error-code-namespace.md ← starts after glossary severity table (T013)
```

### Sprint 3: Remaining Registers (Phases 7–8 — parallel, different files)

```
T030–T033  [P] docs/baseline/launcher-invariants.md  ← parallel
T034–T042  [P] docs/baseline/parity-gap-register.md  ← parallel
```

### Sprint 4: Polish (Phase 9)

```
T043–T047  [P] Cross-reference validation — all parallel (read-only checks on different doc pairs)
T048       docs/baseline/README.md — sequential after validation
```

---

## Implementation Strategy

**MVP Scope** (minimum baseline to unblock Phase 1):

1. Phase 2 (T003–T010) — Endpoint snapshot grounds everything
2. Phase 3 (T011–T014) — Glossary defines shared vocabulary for Phase 1 message contract
3. Phase 5 (T020–T024) — Error namespace enables Phase 1 canonical error codes

**Full Feature**:

- Phase 4 + Phase 6 + Phase 7 + Phase 8 → Phase 9

**Suggested execution sequence**:

1. **Round 1**: Phase 2 (endpoint snapshot) — single file, fast
2. **Round 2**: Phases 3 + 4 + 5 + 6 in parallel (4 documents, 4 different files)
3. **Round 3**: Phases 7 + 8 in parallel (2 documents, 2 different files)
4. **Round 4**: Phase 9 polish (cross-reference + README)

---

## Task Count Summary

| Phase                              | Tasks  | [P] Parallel | Story |
| ---------------------------------- | ------ | ------------ | ----- |
| Phase 1 — Setup                    | 2      | 0            | —     |
| Phase 2 — US1 Endpoint Snapshot    | 8      | 0            | US1   |
| Phase 3 — US2 Glossary             | 4      | 0            | US2   |
| Phase 4 — US3 Tracking ID Policy   | 5      | 5            | US3   |
| Phase 5 — US4 Error Namespace      | 5      | 5            | US4   |
| Phase 6 — US5 Compatibility Pledge | 5      | 5            | US5   |
| Phase 7 — US6 Launcher Invariants  | 4      | 4            | US6   |
| Phase 8 — US7 Parity Gap Register  | 9      | 9            | US7   |
| Phase 9 — Polish                   | 6      | 5            | —     |
| **Total**                          | **48** | **33**       | —     |

---

## Validation Checklist

- [x] All 7 document contracts from `contracts/document-schemas.md` have corresponding task phases
- [x] All 14 functional requirements (FR-001 through FR-014) are covered by at least one task
- [x] Parallel tasks are truly independent (verified by file path — no two [P] tasks modify same file in same sprint)
- [x] Each task specifies exact file path (`docs/baseline/<filename>.md`)
- [x] Dependency graph is acyclic
- [x] MVP scope identified (endpoint snapshot + glossary + error namespace)
- [x] Cross-reference validation tasks exist for all inter-document dependencies
- [x] All phases have independent test criteria defined
