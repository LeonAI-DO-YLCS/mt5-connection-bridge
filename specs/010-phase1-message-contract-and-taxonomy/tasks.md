# Tasks: Phase 1 — Message Contract and Taxonomy

**Input**: Design documents from `/specs/010-phase1-message-contract-and-taxonomy/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Yes — spec.md testing strategy requires contract tests for envelope fields and backward compatibility.

**Organization**: Tasks grouped by user story. US1 (canonical envelope) is the MVP. US2 (tracking ID correlation) and US3 (backward compatibility) build on it.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `app/` at repository root
- **Dashboard**: `dashboard/` at repository root
- **Tests**: `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the messaging module package and shared dependencies

- [x] T001 Create messaging module package with `app/messaging/__init__.py`
- [x] T002 [P] Define `ErrorCode` enum with all 18 codes and metadata (domain, default_title, default_message, default_action, default_severity, default_retryable, default_http_status, category) in `app/messaging/codes.py`
- [x] T003 [P] Implement `generate_tracking_id()` returning `brg-<YYYYMMDDTHHMMSS>-<hex4>` format string using `datetime.now(UTC)` + `secrets.token_hex(2)` in `app/messaging/tracking.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core MessageEnvelope model and normalizer that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create `MessageEnvelope` Pydantic v2 model with fields: `ok`, `category`, `code`, `tracking_id`, `title`, `message`, `action`, `severity`, `retryable`, `context`, `detail` (legacy compat), and optional `data` dict for trade-specific fields — in `app/messaging/envelope.py`
- [x] T005 Create `MessageEnvelopeException` as HTTPException subclass carrying a pre-built `MessageEnvelope`, with convenience constructor accepting `status_code`, `code` (ErrorCode enum), `message`, `action`, `context` — in `app/messaging/envelope.py`
- [x] T006 Implement `normalize_error(code, message, action, context, detail)` factory that builds a `MessageEnvelope` with `ok=False`, auto-generated `tracking_id`, and metadata defaults from the `ErrorCode` enum — in `app/messaging/normalizer.py`
- [x] T007 Implement `normalize_success(title, message, data)` factory that builds a `MessageEnvelope` with `ok=True`, `category=success`, `code=REQUEST_OK`, auto-generated `tracking_id` — in `app/messaging/normalizer.py`

**Checkpoint**: Foundation ready — MessageEnvelope model, exception class, and normalizer are available for route integration

---

## Phase 3: User Story 1 — Canonical Envelope for All Trade Operations (Priority: P1) 🎯 MVP

**Goal**: Every user-facing response from trade-affecting endpoints uses the canonical `MessageEnvelope` — operators see human-readable title, message, and action instead of raw MT5 tuples, Pydantic arrays, or technical error strings.

**Independent Test**: Submit an execute trade with invalid volume → response contains `ok`, `category`, `code`, `tracking_id`, `title`, `message`, `action`, `severity`, `retryable`, `context` fields. No raw retcode or Pydantic array visible in response body.

### Tests for User Story 1

- [x] T008 [P] [US1] Create unit tests for `MessageEnvelope` serialization, field constraints (title ≤ 80 chars), and `context` sanitization (rejects keys containing "password", "secret", "token") in `tests/unit/test_envelope.py`
- [x] T009 [P] [US1] Create unit tests for `ErrorCode` enum — all 18 members have required metadata, no duplicate codes, all domain prefixes valid — in `tests/unit/test_codes.py`
- [x] T010 [P] [US1] Create unit tests for `generate_tracking_id()` — format matches `brg-\d{8}T\d{6}-[0-9a-f]{4}`, length ≤ 30 chars, 100 consecutive calls produce unique values — in `tests/unit/test_tracking.py`
- [x] T011 [P] [US1] Create unit tests for `normalize_error()` and `normalize_success()` — produce valid envelopes with all required fields populated, correct defaults from ErrorCode — in `tests/unit/test_normalizer.py`

### Implementation for User Story 1

- [x] T012 [US1] Register `MessageEnvelopeException` handler in `app/main.py` — serialize the carried envelope to JSON, set `X-Error-Code` header from `envelope.code`, set `X-Tracking-ID` header from `envelope.tracking_id`, log `tracking_id` and `code` as structured fields
- [x] T013 [US1] Modify `unhandled_exception_handler` in `app/main.py` to wrap the error with `normalize_error(code=INTERNAL_SERVER_ERROR, ...)` and return the canonical envelope JSON alongside legacy `detail` field
- [x] T014 [US1] Modify `http_exception_handler` in `app/main.py` to wrap errors with `normalize_error()` using the code from existing `_infer_error_code()`, set `X-Tracking-ID` header, and include both canonical envelope and legacy `detail` in response body
- [x] T015 [US1] Modify `request_validation_exception_handler` in `app/main.py` to wrap Pydantic errors with `normalize_error(code=VALIDATION_ERROR, ...)`, generating a human-readable `title` and `message` from the first validation error, preserving the Pydantic array in `detail`
- [x] T016 [US1] Refactor `/execute` endpoint in `app/routes/execute.py` — replace all `TradeResponse(success=False, error=...)` failure returns with `raise MessageEnvelopeException(...)` using the appropriate `ErrorCode` for each case: `SYMBOL_NOT_CONFIGURED` (unknown ticker), `VALIDATION_ERROR` (invalid action), `SYMBOL_TRADE_MODE_RESTRICTED` (trade mode rejected), `REQUEST_REJECTED` (order rejected, slippage), `MT5_DISCONNECTED` (not connected), `INTERNAL_SERVER_ERROR` (unhandled). Keep success `TradeResponse` unchanged.
- [x] T017 [US1] Refactor `/close-position` endpoint in `app/routes/close_position.py` — replace all `TradeResponse(success=False, ...)` failure returns and inline `HTTPException` raises with `raise MessageEnvelopeException(...)` using: `RESOURCE_NOT_FOUND` (position not found), `SYMBOL_NOT_CONFIGURED` (symbol missing), `VALIDATION_VOLUME_RANGE`/`VALIDATION_VOLUME_STEP` (invalid volume), `REQUEST_REJECTED` (order rejected), `MT5_DISCONNECTED` (not connected), `EXECUTION_DISABLED` (execution disabled), `OVERLOAD_OR_SINGLE_FLIGHT` (queue overload)
- [x] T018 [US1] Refactor `/pending-order` endpoint in `app/routes/pending_order.py` — replace failure returns/raises with `raise MessageEnvelopeException(...)` using appropriate codes. Inspect the file first to identify all error paths, then apply the same pattern as T016/T017.
- [x] T019 [US1] Refactor `/order-check` endpoint in `app/routes/order_check.py` — replace failure returns/raises with `raise MessageEnvelopeException(...)`. Inspect the file first to identify all error paths.
- [x] T020 [US1] Refactor `/orders` endpoints (GET, PUT /{ticket}, DELETE /{ticket}) in `app/routes/orders.py` — replace `HTTPException` raises with `raise MessageEnvelopeException(...)` using appropriate codes for each error path
- [x] T021 [US1] Refactor `/positions` endpoints (GET, PUT /{ticket}/sltp) in `app/routes/positions.py` — replace `HTTPException` raises with `raise MessageEnvelopeException(...)` using appropriate codes for each error path

**Checkpoint**: All trade-affecting endpoints return canonical envelope on errors. Success responses retain `TradeResponse` shape. Unit tests pass.

---

## Phase 4: User Story 2 — Dashboard Message Renderer (Priority: P2)

**Goal**: The dashboard displays canonical envelope messages with severity-based styling, tracking ID with copy-to-clipboard, and a collapsible Details section — replacing all raw `alert()` calls in critical operation paths.

**Independent Test**: Trigger a trade failure from the dashboard → styled message banner appears with title, message, action text, tracking ID copy button, and expandable Details section. No `alert()` popup.

### Implementation for User Story 2

- [x] T022 [P] [US2] Create message severity CSS styles in `dashboard/css/messages.css` — define `.msg-envelope` container, severity variants (`.msg-critical` red, `.msg-high` orange, `.msg-medium` yellow, `.msg-low` blue, `.msg-success` green), `.msg-title`, `.msg-body`, `.msg-action`, `.msg-tracking-id`, `.msg-details-toggle`, `.msg-details-content`, `.msg-copy-btn` classes, and fade-in/auto-dismiss animations
- [x] T023 [US2] Create centralized message renderer module in `dashboard/js/message-renderer.js` — export `renderMessage(envelope, containerEl)` that: creates styled message banner from envelope fields, displays title (bold, severity-colored), message body, action text (highlighted), tracking ID in monospace with copy-to-clipboard button, collapsible "Details" toggle showing `context` as formatted key-value pairs. Auto-dismiss success/info messages after 5 seconds. Support stacking multiple messages.
- [x] T024 [US2] Add `<link>` for `css/messages.css` and `<script>` for `js/message-renderer.js` in `dashboard/index.html`. Add a `<div id="message-area">` container positioned for message display.
- [x] T025 [US2] Replace all `alert()` calls in `dashboard/js/execute-v2.js` (7 occurrences) with calls to `renderMessage()` — parse the API response as envelope when available, construct a minimal envelope for client-side validation errors (select symbol, volume > 0, missing price). Preserve success message for filled trades.
- [x] T026 [US2] Replace all `alert()` calls in `dashboard/js/positions.js` (7 occurrences) with calls to `renderMessage()` — handle close position success/failure, close-all completion, modify position success/failure
- [x] T027 [US2] Replace all `alert()` calls in `dashboard/js/orders.js` (4 occurrences) with calls to `renderMessage()` — handle cancel order, cancel-all, modify order success/failure
- [x] T028 [US2] Replace the `alert()` call in `dashboard/js/app.js` (1 occurrence) with `renderMessage()` — handle execution policy update failure

**Checkpoint**: Dashboard shows styled message banners for all trade operation outcomes. No `alert()` calls remain in critical paths. Tracking IDs are copyable.

---

## Phase 5: User Story 3 — Backward Compatibility and Structured Logging (Priority: P3)

**Goal**: Existing API consumers that read the `detail` field continue to work. Every operation event is logged with `tracking_id` and `code` as searchable structured fields.

**Independent Test**: Send a failing request to `/execute` with an API consumer that reads `response.json()["detail"]` → the `detail` field is present and matches the pre-Phase-1 format. Grep structured logs by `tracking_id` → find the exact log entry.

### Tests for User Story 3

- [x] T029 [P] [US3] Create contract tests verifying backward compatibility in `tests/contract/test_backward_compat.py` — for each of the 6 trade-affecting endpoints, assert that error responses contain `detail` field with the same type/content as pre-Phase-1 (string for HTTPException, list for validation errors). Assert `X-Error-Code` header is still populated.
- [x] T030 [P] [US3] Create contract tests verifying canonical envelope fields in `tests/contract/test_envelope_contract.py` — for each of the 6 trade-affecting endpoints, assert error responses contain all 11 canonical envelope fields (`ok`, `category`, `code`, `tracking_id`, `title`, `message`, `action`, `severity`, `retryable`, `context`, `detail`)

### Implementation for User Story 3

- [x] T031 [US3] Verify and harden legacy `detail` field population in all 3 exception handlers in `app/main.py` — ensure `detail` is always present alongside the canonical envelope, matching the pre-Phase-1 content type (string for HTTP exceptions, list for validation errors)
- [x] T032 [US3] Add structured logging of `tracking_id` and `code` to all 3 exception handlers in `app/main.py` and to `MessageEnvelopeException` handler — use `logger.info()` or `logger.error()` with explicit `tracking_id=` and `code=` kwargs so the fields are grep-searchable in log output
- [x] T033 [US3] Verify `X-Error-Code` header maps correctly to canonical `code` value across all exception handlers — the `_infer_error_code()` function output must match the `ErrorCode` enum member used in the envelope. Add a cross-reference assertion in the `MessageEnvelopeException` handler.
- [x] T034 [US3] Add `X-Tracking-ID` response header to all exception handlers and to the `MessageEnvelopeException` handler in `app/main.py` — set value from `envelope.tracking_id`

**Checkpoint**: Legacy `detail` field present in all error responses. Structured logs searchable by `tracking_id` and `code`. `X-Error-Code` and `X-Tracking-ID` headers present.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validation, documentation, and final cleanup

- [x] T035 [P] Run existing test suite (`tests/contract/` and `tests/integration/`) to verify no regressions — command: `.venv/bin/python -m pytest tests/ -v`
- [x] T036 [P] Run new unit tests — command: `.venv/bin/python -m pytest tests/unit/test_envelope.py tests/unit/test_codes.py tests/unit/test_tracking.py tests/unit/test_normalizer.py -v`
- [x] T037 [P] Run new contract tests — command: `.venv/bin/python -m pytest tests/contract/test_envelope_contract.py tests/contract/test_backward_compat.py -v`
- [x] T038 Run lint check — command: `.venv/bin/python -m ruff check app tests`
- [x] T039 Validate quickstart.md verification checklist — walk through all 10 items and confirm each passes
- [x] T040 Update `app/messaging/__init__.py` with public API exports: `MessageEnvelope`, `MessageEnvelopeException`, `ErrorCode`, `generate_tracking_id`, `normalize_error`, `normalize_success`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001, T002, T003 can start immediately. T002 and T003 are parallel.
- **Foundational (Phase 2)**: T004 depends on T002 (ErrorCode enum). T005 depends on T004. T006 depends on T002, T003, T004. T007 depends on T002, T003, T004.
- **US1 (Phase 3)**: Depends on Phase 2 completion. T008–T011 tests are parallel. T012–T015 (main.py handlers) are sequential. T016–T021 (route refactors) are parallel with each other.
- **US2 (Phase 4)**: Depends on Phase 3 completion (routes must produce envelope responses). T022–T023 are parallel. T025–T028 depend on T023+T024.
- **US3 (Phase 5)**: Can start after Phase 3 (needs envelope in responses). T029–T030 tests are parallel. T031–T034 are sequential.
- **Polish (Phase 6)**: Depends on all user stories completion. T035–T037 are parallel.

### User Story Dependencies

- **US1 (P1)**: MVP — depends only on Foundational (Phase 2)
- **US2 (P2)**: Depends on US1 (backend must produce envelope responses for the renderer to consume)
- **US3 (P3)**: Depends on US1 (needs canonical envelope in responses to verify backward compat alongside it)

### Within Each User Story

- Tests FIRST (should FAIL before implementation)
- Models/infra before services
- Services before routes
- Core implementation before integration

### Parallel Opportunities

- **Phase 1**: T002 ‖ T003 (different files, no dependencies)
- **Phase 2**: T006 ‖ T007 (both depend on T004 but write to same file — execute sequentially)
- **Phase 3 tests**: T008 ‖ T009 ‖ T010 ‖ T011 (different test files)
- **Phase 3 routes**: T016 ‖ T017 ‖ T018 ‖ T019 ‖ T020 ‖ T021 (different route files, after T012–T015)
- **Phase 4**: T022 ‖ T023 (CSS and JS); then T025 ‖ T026 ‖ T027 ‖ T028 (different dashboard files)
- **Phase 5 tests**: T029 ‖ T030 (different test files)
- **Phase 6**: T035 ‖ T036 ‖ T037 (independent test runs)

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests in parallel:
Task T008: "Unit tests for MessageEnvelope in tests/unit/test_envelope.py"
Task T009: "Unit tests for ErrorCode in tests/unit/test_codes.py"
Task T010: "Unit tests for tracking ID in tests/unit/test_tracking.py"
Task T011: "Unit tests for normalizer in tests/unit/test_normalizer.py"

# After T012-T015 (main.py handlers), launch all route refactors in parallel:
Task T016: "Refactor /execute in app/routes/execute.py"
Task T017: "Refactor /close-position in app/routes/close_position.py"
Task T018: "Refactor /pending-order in app/routes/pending_order.py"
Task T019: "Refactor /order-check in app/routes/order_check.py"
Task T020: "Refactor /orders in app/routes/orders.py"
Task T021: "Refactor /positions in app/routes/positions.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T007)
3. Complete Phase 3: User Story 1 (T008–T021)
4. **STOP and VALIDATE**: Run `pytest tests/` — all existing + new tests pass
5. Every trade-affecting endpoint returns canonical envelopes on error

### Incremental Delivery

1. Setup + Foundational → Core messaging module ready
2. Add US1 → Backend produces canonical envelopes → Test independently → **MVP!**
3. Add US2 → Dashboard renders envelopes → Human-readable messages visible
4. Add US3 → Legacy compat + logging verified → Full Phase 1 complete
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (route refactors T016–T021)
   - Developer B: US2 (dashboard renderer T022–T028) — can start CSS/JS before US1 completes
3. US3 follows after US1 is merged

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total tasks: 40
