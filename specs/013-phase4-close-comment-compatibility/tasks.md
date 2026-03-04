# Tasks: Phase 4 — Close-Order Comment Compatibility

**Input**: Design documents from `/specs/013-phase4-close-comment-compatibility/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/, research.md, quickstart.md

**Tests**: Included — spec explicitly requires test coverage (Success Criteria §5: "A test suite covering at least 5 disallowed character patterns and 3 length-boundary cases").

**Organization**: Tasks are grouped by user story. Each task is explicit enough for a junior developer to implement without additional context.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create new files and scaffolding needed by all user stories.

- [x] T001 Create the new file `app/execution/comment.py` with the module docstring, `from __future__ import annotations`, and `import re`. Add two empty placeholders: (1) a class stub `class CommentNormalizer:` with `pass` body, and (2) a function stub `def matches_invalid_comment_signature(error_code: int, error_message: str) -> bool:` that returns `False`. This file must be importable without errors.

- [x] T002 Create the new file `tests/unit/test_comment_normalizer.py` with `import pytest` and `from app.execution.comment import CommentNormalizer`. Add a single placeholder test: `def test_placeholder(): assert True`. Verify the file runs with `python -m pytest tests/unit/test_comment_normalizer.py -v` and passes.

- [x] T003 [P] Create the new file `tests/unit/test_comment_signature.py` with `import pytest` and `from app.execution.comment import matches_invalid_comment_signature`. Add a single placeholder test: `def test_placeholder(): assert True`. Verify the file runs with `python -m pytest tests/unit/test_comment_signature.py -v` and passes.

- [x] T004 [P] Create the new file `tests/integration/test_close_comment_fallback.py` with `import pytest` and an import of `from unittest.mock import patch, MagicMock`. Add a single placeholder test: `def test_placeholder(): assert True`. Verify the file runs with `python -m pytest tests/integration/test_close_comment_fallback.py -v` and passes.

**Checkpoint**: All 4 new files exist and are importable. `python -m pytest tests/unit/test_comment_normalizer.py tests/unit/test_comment_signature.py tests/integration/test_close_comment_fallback.py -v` passes with 3 placeholder tests.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the two new `ErrorCode` members and extend `emit_operation_log()` — both are needed by every user story.

**⚠️ CRITICAL**: US1, US2, and US3 cannot begin until this phase is complete.

- [x] T005 Add the `MT5_REQUEST_COMMENT_INVALID_RECOVERED` member to the `ErrorCode` enum in `app/messaging/codes.py`. Insert it in the "Request compatibility domain" section (after `REQUEST_REJECTED`, before `OVERLOAD_OR_SINGLE_FLIGHT`). Use exactly these values: `domain="MT5"`, `default_title="Broker rejected note format; position closed successfully"`, `default_message="The broker's terminal rejected the comment field on the close request. The position was closed successfully using a compatibility format without the comment."`, `default_action="No action required."`, `default_severity="low"`, `default_retryable=False`, `default_http_status=200`, `category="warning"`. Verify the app still imports without errors: `python -c "from app.messaging.codes import ErrorCode; print(ErrorCode.MT5_REQUEST_COMMENT_INVALID_RECOVERED.name)"`.

- [x] T006 Add the `MT5_REQUEST_COMMENT_INVALID` member to the `ErrorCode` enum in `app/messaging/codes.py`. Insert it immediately after `MT5_REQUEST_COMMENT_INVALID_RECOVERED`. Use exactly these values: `domain="MT5"`, `default_title="Could not close position due to broker request-format restrictions"`, `default_message="The close request failed even after removing the comment field. The broker may have additional restrictions on the order format."`, `default_action="Contact support with the tracking ID shown above."`, `default_severity="high"`, `default_retryable=False`, `default_http_status=400`, `category="error"`. Verify: `python -c "from app.messaging.codes import ErrorCode; print(ErrorCode.MT5_REQUEST_COMMENT_INVALID.name)"`.

- [x] T007 Extend the `emit_operation_log()` function in `app/execution/observability.py` to accept optional extra fields. Change the signature from `def emit_operation_log(ctx: OperationContext, code: str, final_outcome: str) -> None:` to `def emit_operation_log(ctx: OperationContext, code: str, final_outcome: str, **extra: Any) -> None:`. Add `from typing import Any` to the imports. Inside the function body, after building the `log_data` dict, add the line `log_data.update(extra)` just before the `logger.info(...)` call. Verify existing callers are unaffected by running `python -m pytest -v --tb=short -q 2>&1 | tail -5`.

- [x] T008 Update `app/execution/__init__.py` to re-export `CommentNormalizer` and `matches_invalid_comment_signature` from `app.execution.comment`. Add the import line: `from .comment import CommentNormalizer, matches_invalid_comment_signature`. Add both names to the `__all__` list. Verify: `python -c "from app.execution import CommentNormalizer, matches_invalid_comment_signature; print('OK')"`.

**Checkpoint**: Two new `ErrorCode` members are importable, `emit_operation_log()` accepts `**extra`, and `app.execution` re-exports comment utilities. Full test suite still passes.

---

## Phase 3: User Story 1 — Comment Normalization (Priority: P1) 🎯 MVP

**Goal**: Implement the `CommentNormalizer` class so that all comment values are sanitized before reaching `order_send`. This eliminates the root cause — invalid characters and overlength comments — in all order-building paths.

**Independent Test**: Run `python -m pytest tests/unit/test_comment_normalizer.py -v` — all normalizer tests pass. Import `CommentNormalizer` and call `normalize()` with various inputs to see sanitized outputs.

**Spec Requirements**: FR-001 (normalize), FR-002 (apply to close + pending + execute), FR-003 (silent normalization).

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T009 [P] [US1] In `tests/unit/test_comment_normalizer.py`, remove the placeholder test. Write a test `test_normalize_none_returns_empty_string` that asserts `CommentNormalizer().normalize(None) == ""`. This test should FAIL because the stub returns `pass` / is not implemented yet.

- [x] T010 [P] [US1] In `tests/unit/test_comment_normalizer.py`, write a test `test_normalize_empty_string_returns_empty` that asserts `CommentNormalizer().normalize("") == ""`.

- [x] T011 [P] [US1] In `tests/unit/test_comment_normalizer.py`, write a test `test_normalize_whitespace_only_returns_empty` that asserts `CommentNormalizer().normalize("   ") == ""`.

- [x] T012 [P] [US1] In `tests/unit/test_comment_normalizer.py`, write a parametrized test `test_normalize_strips_disallowed_characters` using `@pytest.mark.parametrize` with at least these 6 cases (input, expected*output): `("hello@world", "helloworld")`, `("test! (value)", "test value")`, `("αβγ unicode", " unicode")`, `('quote "test"', "quote test")`, `("special#$%^&*chars", "specialchars")`, `("pipe|and<angle>brackets", "pipeandanglebrackets")`. Each case verifies that non-`[A-Za-z0-9 .*-]` characters are removed.

- [x] T013 [P] [US1] In `tests/unit/test_comment_normalizer.py`, write a parametrized test `test_normalize_enforces_max_length` with at least these 3 boundary cases: (1) a 26-char string → unchanged, (2) a 27-char string → truncated to 26 chars, (3) a 50-char string → truncated to 26 chars. Use `CommentNormalizer.MAX_LENGTH` as the reference constant.

- [x] T014 [P] [US1] In `tests/unit/test_comment_normalizer.py`, write a test `test_normalize_preserves_valid_characters` that asserts `CommentNormalizer().normalize("valid.comment-123_ok") == "valid.comment-123_ok"` — all allowed characters (`[A-Za-z0-9 ._-]`) are preserved untouched.

- [x] T015 [P] [US1] In `tests/unit/test_comment_normalizer.py`, write a test `test_normalize_strips_trailing_whitespace_after_truncation` — create a 30-char string where char 26 would be a space (e.g. `"abcdefghijklmnopqrstuvwxy zzzz"`), normalize it, and assert the result has no trailing whitespace and is ≤ 26 chars.

- [x] T016 [P] [US1] In `tests/unit/test_comment_normalizer.py`, write a test `test_normalize_full_pipeline_combined` that takes a string with disallowed chars AND overlength AND leading/trailing whitespace (e.g. `"  ai-hedge-fund@mt5! bridge close order   "`), normalizes it, and asserts: (a) result has no disallowed chars, (b) len ≤ 26, (c) no leading/trailing whitespace.

### Implementation for User Story 1

- [x] T017 [US1] Implement the `CommentNormalizer` class in `app/execution/comment.py`. Replace the `pass` stub with the real implementation. Add these class-level constants: `MAX_LENGTH: int = 26` and `ALLOWED_PATTERN: re.Pattern = re.compile(r"[^A-Za-z0-9 ._-]")`. Implement the `normalize(self, value: str | None) -> str` method following this exact pipeline: (1) if `value is None`, return `""`. (2) Call `self.ALLOWED_PATTERN.sub("", value)` to remove disallowed chars. (3) Call `.strip()` to trim whitespace. (4) Slice to `[:self.MAX_LENGTH]`. (5) Call `.rstrip()` to trim any trailing whitespace produced by truncation. (6) Return the result. Run `python -m pytest tests/unit/test_comment_normalizer.py -v` — all tests from T009–T016 should now pass.

**Checkpoint**: `CommentNormalizer` is fully implemented and tested. `python -m pytest tests/unit/test_comment_normalizer.py -v` passes with ≥8 tests.

---

## Phase 4: User Story 2 — Adaptive Close Fallback (Priority: P2)

**Goal**: Implement the `matches_invalid_comment_signature()` function and modify the close-position worker to retry without comment when the signature matcher fires.

**Independent Test**: Run `python -m pytest tests/unit/test_comment_signature.py tests/integration/test_close_comment_fallback.py -v` — all fallback tests pass.

**Spec Requirements**: FR-004 (adaptive retry), FR-005 (same tracking_id), FR-006 (recovered response), FR-007 (unrecoverable response), FR-008 (no false-positive fallback), FR-009 (warning message), FR-010 (error message), FR-011 (no raw tuple in user-facing copy).

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T018 [P] [US2] In `tests/unit/test_comment_signature.py`, remove the placeholder test. Write a parametrized test `test_matches_invalid_comment_signature` with these 6 cases from the contract: `(-2, 'Invalid "comment" argument') → True`, `(-2, 'INVALID "COMMENT" ARGUMENT') → True` (case-insensitive), `(-2, 'Invalid "volume" argument') → False`, `(-1, 'Invalid "comment" argument') → False` (wrong code), `(-2, 'Something else') → False`, `(-2, '') → False` (empty message).

- [x] T019 [P] [US2] In `tests/integration/test_close_comment_fallback.py`, remove the placeholder test. Write a test `test_close_position_normal_success_no_fallback` that: (1) mocks `mt5.positions_get` to return a fake position, (2) mocks `mt5.symbol_info` to return a fake symbol_info, (3) mocks `mt5.order_send` to return a successful result object (retcode=10009, price=1.085, volume=0.1, order=9999) on the FIRST call, (4) calls the `POST /close-position` endpoint with `{"ticket": 12345}` via `TestClient`, (5) asserts the response is successful, and (6) asserts `mt5.order_send` was called exactly **once** (no fallback triggered). Use `from unittest.mock import patch, MagicMock, PropertyMock` and `from types import SimpleNamespace`.

- [x] T020 [P] [US2] In `tests/integration/test_close_comment_fallback.py`, write a test `test_close_position_comment_rejected_then_recovered` that: (1) mocks `mt5.order_send` to return `None` on the first call AND a successful result on the second call, (2) mocks `mt5.last_error` to return `(-2, 'Invalid "comment" argument')`, (3) calls `POST /close-position` with `{"ticket": 12345}`, (4) asserts the response `ok` is `True`, (5) asserts the response `code` is `"MT5_REQUEST_COMMENT_INVALID_RECOVERED"`, (6) asserts `mt5.order_send` was called exactly **twice**, (7) asserts the second `order_send` call's dict argument does NOT contain the key `"comment"`.

- [x] T021 [P] [US2] In `tests/integration/test_close_comment_fallback.py`, write a test `test_close_position_comment_rejected_then_unrecoverable` that: (1) mocks `mt5.order_send` to return `None` on BOTH calls, (2) mocks `mt5.last_error` to return `(-2, 'Invalid "comment" argument')` on the first call and `(-2, 'Some other error')` on the second call, (3) calls `POST /close-position` with `{"ticket": 12345}`, (4) asserts the response `ok` is `False`, (5) asserts the response `code` is `"MT5_REQUEST_COMMENT_INVALID"`, (6) asserts `mt5.order_send` was called exactly **twice**.

- [x] T022 [P] [US2] In `tests/integration/test_close_comment_fallback.py`, write a test `test_close_position_non_comment_failure_no_fallback` that: (1) mocks `mt5.order_send` to return `None`, (2) mocks `mt5.last_error` to return `(-2, 'Invalid "volume" argument')` (NOT comment-related), (3) calls `POST /close-position` with `{"ticket": 12345}`, (4) asserts `mt5.order_send` was called exactly **once** (no fallback triggered), (5) asserts the response code is NOT `MT5_REQUEST_COMMENT_INVALID_RECOVERED` and NOT `MT5_REQUEST_COMMENT_INVALID`.

### Implementation for User Story 2

- [x] T023 [US2] Implement the `matches_invalid_comment_signature()` function in `app/execution/comment.py`. Replace the `return False` stub with: `return error_code == -2 and "invalid" in error_message.lower() and "comment" in error_message.lower()`. Run `python -m pytest tests/unit/test_comment_signature.py -v` — all 6 parametrized cases should pass.

- [x] T024 [US2] Modify the `_execute_in_worker()` function inside `app/routes/close_position.py` to implement the adaptive comment fallback. This is the most critical task. Make these exact changes inside `_execute_in_worker()`:

  **Step 1**: Add a new import at the top of the file: `from ..execution.comment import matches_invalid_comment_signature`.

  **Step 2**: Find the line `result = mt5.order_send(close_request)` (line ~159). Replace the block from that line through the return statement (lines ~159–185) with this logic:

  ```
  # ── Attempt 1: with normalized comment ──
  result = mt5.order_send(close_request)
  attempt_variant = "with_comment"

  if result is None:
      last_err = mt5.last_error()
      err_code = last_err[0] if last_err else 0
      err_msg = last_err[1] if last_err and len(last_err) > 1 else ""

      if matches_invalid_comment_signature(err_code, err_msg):
          # ── Attempt 2: without comment (adaptive fallback) ──
          close_request.pop("comment", None)
          result = mt5.order_send(close_request)
          attempt_variant = "with_comment → without_comment"

          if result is None:
              return (
                  TradeResponse(success=False, error="Could not close position due to broker request-format restrictions"),
                  "unrecoverable",
                  attempt_variant,
                  err_code,
                  err_msg,
              )
      else:
          return (
              TradeResponse(success=False, error=f"order_send returned None: {mt5.last_error()}"),
              "order_send_none",
              attempt_variant,
              None,
              None,
          )
  ```

  **Step 3**: Update the retcode check and the two return statements to include the 5-tuple format `(TradeResponse, trade_state, attempt_variant, mt5_err_code, mt5_err_msg)`:
  - For retcode failure: `return (TradeResponse(success=False, ...), "order_rejected", attempt_variant, None, None)`
  - For success when `attempt_variant` contains `"→"` (fallback happened): return with `trade_state = "comment_recovered"`
  - For normal success: `return (TradeResponse(success=True, ...), "fill_confirmed", attempt_variant, None, None)`

  **Step 4**: Update the caller of `_execute_in_worker()` (line ~189) from `response, trade_state = await ...` to `response, trade_state, attempt_variant, mt5_err_code, mt5_err_msg = await ...`.

  Run `python -m pytest tests/integration/test_close_comment_fallback.py -v` after this change.

- [x] T025 [US2] Update the response-handling logic after the `await` call in `app/routes/close_position.py`. After getting the 5-tuple, add handling for the two new trade states:

  **For `trade_state == "comment_recovered"`**: Transition to `OperationState.RECOVERED`. Emit a `MessageEnvelopeException` with `status_code=200`, `code=ErrorCode.MT5_REQUEST_COMMENT_INVALID_RECOVERED`, and `context={"ticket": req.ticket, "attempt_variant": attempt_variant, "mt5_last_error_code": mt5_err_code, "mt5_last_error_message": mt5_err_msg}`. But since this is a SUCCESS response (not an exception), instead return a `TradeResponse(success=True, ...)` and use the normalizer's warning-category envelope. The simplest approach: return the successful `TradeResponse` as-is, since the `MessageEnvelope` is constructed by the exception handler and this is NOT an error. Log with `emit_operation_log(ctx, code="MT5_REQUEST_COMMENT_INVALID_RECOVERED", final_outcome="recovered", attempt_variant=attempt_variant, mt5_last_error_code=mt5_err_code, mt5_last_error_message=mt5_err_msg)`.

  **For `trade_state == "unrecoverable"`**: Transition to `OperationState.FAILED_TERMINAL`. Emit log with `emit_operation_log(ctx, code="MT5_REQUEST_COMMENT_INVALID", final_outcome="unrecoverable", ...)`. Raise `MessageEnvelopeException` with `status_code=400`, `code=ErrorCode.MT5_REQUEST_COMMENT_INVALID`, `message=response.error`, `context={"ticket": req.ticket, "attempt_variant": attempt_variant, "mt5_last_error_code": mt5_err_code, "mt5_last_error_message": mt5_err_msg}`.

  For all other existing states (`"fill_confirmed"`, `"order_rejected"`, `"position_not_found"`, etc.), pass through the `attempt_variant` to the observability call: change `emit_operation_log(ctx, code=..., final_outcome=trade_state)` to `emit_operation_log(ctx, code=..., final_outcome=trade_state, attempt_variant=attempt_variant)`.

  Run `python -m pytest tests/integration/test_close_comment_fallback.py -v` — all 4 integration tests should now pass.

**Checkpoint**: `matches_invalid_comment_signature()` works correctly across all 6 test cases. The close-position route handles normal, recovered, and unrecoverable paths. `python -m pytest tests/unit/test_comment_signature.py tests/integration/test_close_comment_fallback.py -v` passes.

---

## Phase 5: User Story 3 — Comment Normalization Integration into Mappers (Priority: P3)

**Goal**: Wire `CommentNormalizer.normalize()` into all three mapper functions so that no un-normalized comment ever reaches `order_send`.

**Independent Test**: Manually verify that `build_close_request()`, `build_pending_order_request()`, and `build_order_request()` all produce normalized comment values. Existing tests continue to pass.

**Spec Requirements**: FR-002 (normalization applies to close, pending, and execute), FR-003 (silent normalization).

### Implementation for User Story 3

- [x] T026 [US3] Add the import `from ..execution.comment import CommentNormalizer` at the top of `app/mappers/trade_mapper.py` (after the existing imports, around line 10). Also add a module-level normalizer instance: `_comment_normalizer = CommentNormalizer()` immediately after the import. Verify import works: `python -c "from app.mappers.trade_mapper import _comment_normalizer; print(type(_comment_normalizer))"`.

- [x] T027 [US3] In `app/mappers/trade_mapper.py`, update the `build_order_request()` function (around line 173). Change the line `"comment": "ai-hedge-fund mt5 bridge",` to `"comment": _comment_normalizer.normalize("ai-hedge-fund mt5 bridge"),`. The static string `"ai-hedge-fund mt5 bridge"` is 23 chars (under the 26-char limit), so this is a no-op for this specific value — but it ensures any future changes to the default string are automatically sanitized.

- [x] T028 [US3] In `app/mappers/trade_mapper.py`, update the `build_close_request()` function (around line 205). Change the line `"comment": "ai-hedge-fund mt5 bridge close",` to `"comment": _comment_normalizer.normalize("ai-hedge-fund mt5 bridge close"),`. Note: the original string `"ai-hedge-fund mt5 bridge close"` is 30 chars — this WILL be truncated to 26 chars (`"ai-hedge-fund mt5 bridge c"` then rstripped → `"ai-hedge-fund mt5 bridge c"`). Verify: `python -c "from app.execution.comment import CommentNormalizer; print(repr(CommentNormalizer().normalize('ai-hedge-fund mt5 bridge close')))"` should print `'ai-hedge-fund mt5 bridge c'`.

- [x] T029 [US3] In `app/mappers/trade_mapper.py`, update the `build_pending_order_request()` function (around line 239). Change the line `"comment": req.comment or "ai-hedge-fund pending order",` to `"comment": _comment_normalizer.normalize(req.comment or "ai-hedge-fund pending order"),`. This ensures user-provided comments on pending orders are also sanitized (FR-002). Verify existing pending order tests still pass: `python -m pytest tests/ -k "pending" -v --tb=short`.

**Checkpoint**: All three mapper functions normalize comments. `python -m pytest -v --tb=short` — full test suite passes with no regressions.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Ensure full audit trail compliance, no raw tuples in user-facing copy, and final regression check.

- [x] T030 Run the complete test suite with verbose output: `python -m pytest -v`. Verify: (a) all Phase 4 tests pass (normalizer ≥8 tests, signature 6 cases, integration 4 tests), (b) no existing tests are broken, (c) no raw MT5 error tuples appear in any response `message` or `title` field (grep the test outputs for patterns like `(-2,` or `last_error()`). Fix any failures found.

- [x] T031 [P] Run `python -m ruff check app/execution/comment.py app/routes/close_position.py app/mappers/trade_mapper.py app/messaging/codes.py app/execution/observability.py app/execution/__init__.py` and fix any linting issues found. All files must pass with zero warnings.

- [x] T032 [P] Verify the quickstart.md validation steps manually. Ensure the three close-position paths (normal, recovered, unrecoverable) are exercised by the integration tests. Add a comment at the top of `tests/integration/test_close_comment_fallback.py` documenting which acceptance scenarios (from spec.md §Acceptance Scenarios) each test covers: test 1 → Scenario 2 (normal), test 2 → Scenario 1 (recovered), test 3 → Scenario 3 (unrecoverable), test 4 → Scenario edge case (non-comment failure).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 - Normalization (Phase 3)**: Depends on Phase 2. No dependency on US2 or US3.
- **US2 - Adaptive Fallback (Phase 4)**: Depends on Phase 2 AND Phase 3 (US2 imports `matches_invalid_comment_signature` from the same module as US1's `CommentNormalizer`). Must complete after US1.
- **US3 - Mapper Integration (Phase 5)**: Depends on Phase 3 (uses `CommentNormalizer` from US1). Can run in parallel with US2.
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1 - Normalization)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (P2 - Adaptive Fallback)**: Depends on US1 completion (shares `app/execution/comment.py`)
- **US3 (P3 - Mapper Integration)**: Depends on US1 completion (imports `CommentNormalizer`)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Implementation tasks execute sequentially within a story
- Story complete before moving to next priority

### Parallel Opportunities

**Within Phase 1** (all [P]):

```
T002, T003, T004 — three test files can be created simultaneously
```

**Within Phase 2**:

```
T005 + T006 — both ErrorCode additions (same file, but sequential lines)
T007 + T008 — different files, can run in parallel
```

**Within Phase 3 (US1)** — all test tasks [P]:

```
T009, T010, T011, T012, T013, T014, T015, T016 — all test tasks in the same file,
  but each adds an independent test function. Can be written simultaneously if
  one developer writes all of them in a single pass.
```

**US2 + US3** — limited parallelism:

```
US3 (T026–T029) can start as soon as US1 is complete, even while US2 is in progress.
```

**Within Phase 6** (all [P]):

```
T031 + T032 — linting and quickstart validation can run in parallel
```

---

## Parallel Example: User Story 1

```bash
# Write ALL normalizer tests in one pass (they're all in the same file):
# T009–T016: 8 test functions in tests/unit/test_comment_normalizer.py

# Then implement:
# T017: CommentNormalizer class in app/execution/comment.py

# Validate:
python -m pytest tests/unit/test_comment_normalizer.py -v
# Expected: 8+ tests pass
```

## Parallel Example: After US1 completes

```bash
# Developer A works on US2 (adaptive fallback):
# T018–T022 (tests) → T023–T025 (implementation)

# Developer B works on US3 (mapper integration) simultaneously:
# T026–T029 (implementation, no separate tests needed)

# Both can proceed in parallel since they modify different files:
# US2: app/routes/close_position.py + tests/
# US3: app/mappers/trade_mapper.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T008)
3. Complete Phase 3: US1 — Normalization (T009–T017)
4. **STOP and VALIDATE**: Run `python -m pytest tests/unit/test_comment_normalizer.py -v` — 8+ tests pass
5. At this point, all comments are sanitized before reaching MT5 — the root cause is mitigated

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Normalization) → Root cause mitigated (MVP!) → Commit
3. Add US2 (Adaptive Fallback) → Graceful recovery for residual failures → Commit
4. Add US3 (Mapper Integration) → All mappers wired → Commit
5. Polish → Full regression + lint clean → Final commit

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD)
- Commit after each phase or logical group
- Stop at any checkpoint to validate independently
- Total tasks: **32** (T001–T032)
- Tasks per story: US1 = 9 tasks (8 test + 1 impl), US2 = 8 tasks (5 test + 3 impl), US3 = 4 tasks (impl only)
- Foundational: 4 tasks, Setup: 4 tasks, Polish: 3 tasks
