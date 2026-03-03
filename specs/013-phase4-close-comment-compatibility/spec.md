# Feature Specification: Phase 4 — Close-Order Comment Compatibility

**Feature Branch**: `013-phase4-close-comment-compatibility`
**Created**: 2026-03-03
**Status**: Draft
**Plan Reference**: `docs/plans/phased-user-facing-reliability/4-close-comment-compatibility.md`
**Phase Dependency**: Phase 3 (execution hardening and deterministic lifecycle)

---

## Overview

A confirmed operational failure — `order_send returned None: (-2, 'Invalid "comment" argument')` — occurs in the close-position flow when the broker or terminal rejects the `comment` field on the MT5 order request. The bridge currently sends a static comment string and offers no fallback, leaving operators with a cryptic failure and an unclosed position.

This phase eliminates that failure class through a **sanitize-and-fallback** strategy: the comment is normalized before sending, and if an invalid-comment signature is detected at runtime, the operation is re-attempted once without the comment — transparently to the operator, with full auditability.

---

## User Scenarios & Testing _(mandatory)_

### Primary User Story

As a trading operator, when I close a position, I want the operation to succeed even if my broker's terminal rejects the comment field format — without needing to change any configuration or understand MT5 internals. If the close completes with a compatibility workaround, I want to see a brief informational note, not an error.

As a support engineer, I want every close operation to produce an audit trail that distinguishes three outcomes: (a) closed successfully with the original comment, (b) closed successfully using the compatibility fallback (no comment), or (c) failed to close even after fallback — so I can diagnose broker-specific behavior patterns across environments.

### Acceptance Scenarios

1. **Given** a broker that rejects the MT5 `comment` field during position close, **When** the operator clicks "Close Position" in the dashboard, **Then** the bridge detects the invalid-comment signature, re-attempts the close without a comment, and the position is closed — the dashboard shows a warning-category message: "Closed with compatibility format (note field not supported by this broker)."

2. **Given** a broker that accepts the MT5 `comment` field normally, **When** the operator closes a position, **Then** the first attempt succeeds, no fallback occurs, and the dashboard shows a standard success message — no compatibility warning.

3. **Given** an invalid-comment failure where the fallback attempt also fails for a different reason (e.g., position already closed), **When** both attempts are exhausted, **Then** the dashboard shows a clear error message with the reason the close failed, a `tracking_id`, and the instruction "Contact support with your tracking ID."

4. **Given** a close operation that uses the comment fallback, **When** the structured logs are inspected, **Then** the log entry contains: `tracking_id`, `operation: close_position`, `attempt_variant: with_comment → without_comment`, `mt5_last_error_code`, `mt5_last_error_message`, and `final_outcome: recovered`.

5. **Given** a close operation that fails even after fallback, **When** the logs are inspected, **Then** the log entry contains `attempt_variant: with_comment → without_comment`, `final_outcome: unrecoverable`, and the canonical code `MT5_REQUEST_COMMENT_INVALID`.

6. **Given** a pending order with a user-provided comment that contains disallowed characters, **When** the order is submitted, **Then** the comment is automatically sanitized (disallowed characters removed, length trimmed) before reaching MT5 — and the operator sees no error related to comment formatting.

### Edge Cases

- What if the broker rejects the comment on the fallback attempt as well (different reason)? → The operation fails with `final_outcome: unrecoverable`, code `MT5_REQUEST_COMMENT_INVALID`, and the operator message distinguishes "failed even after removing the note field."
- What if the bridge cannot determine whether the failure was caused by the comment field (ambiguous error signature)? → The failure is treated as non-comment-related and surfaced as a standard operation failure — no fallback is attempted, to avoid silent operation changes on unrelated errors.
- What if the sanitized comment becomes empty after normalization? → An empty comment is treated as "no comment" and the request is sent with an empty string or the field omitted, depending on what the MT5 API accepts.

---

## Requirements _(mandatory)_

### Functional Requirements

**Comment Normalization**

- **FR-001**: Before any MT5 order request that includes a `comment` field, the bridge MUST normalize the comment value by: (a) enforcing a maximum length policy, (b) applying an allowed-character policy that removes or replaces disallowed characters, (c) trimming leading/trailing whitespace, and (d) handling empty values by substituting a safe empty value.
- **FR-002**: The comment normalization MUST apply to: `POST /close-position` (static comment), `POST /pending-order` (user-provided comment), and any future endpoints that pass a `comment` field to `order_send`.
- **FR-003**: Normalization MUST be applied silently — no user-visible warning for routine normalization, only for the fallback scenario.

**Adaptive Comment Fallback (Close Operation)**

- **FR-004**: After sending the normalized comment on a close operation, if `order_send` returns `None` AND `last_error()` matches the invalid-comment error signature (error code `-2` with message matching "Invalid \"comment\" argument" or equivalent), the bridge MUST automatically re-attempt the close once without any comment field.
- **FR-005**: The second attempt MUST use the same `tracking_id` as the first attempt, so both attempts are traceable as a single logical operation.
- **FR-006**: If the second attempt succeeds, the operation MUST be reported as a `warning`-category success with code `MT5_REQUEST_COMMENT_INVALID_RECOVERED`.
- **FR-007**: If the second attempt fails (for any reason), the operation MUST be reported as an `error` with code `MT5_REQUEST_COMMENT_INVALID` and `retryable: false`.
- **FR-008**: The fallback MUST NOT be triggered by any error signature other than the specific invalid-comment pattern — other MT5 errors MUST follow the standard failure path.

**User-Facing Messages**

- **FR-009**: When the close succeeds via fallback, the canonical message MUST use: `category: warning`, sub-context `success`, `code: MT5_REQUEST_COMMENT_INVALID_RECOVERED`, `title: "Broker rejected note format; position closed successfully"`, `action: "No action required."`.
- **FR-010**: When the close fails even after fallback, the canonical message MUST use: `category: error`, `code: MT5_REQUEST_COMMENT_INVALID`, `title: "Could not close position due to broker request-format restrictions"`, and an `action` that references the `tracking_id` and support contact.
- **FR-011**: In both cases, the raw MT5 error tuple MUST NOT appear as primary user-facing copy — it may be included in the `context` field only.

**Observability and Audit**

- **FR-012**: Every close operation affected by comment compatibility handling MUST produce a structured log entry containing: `tracking_id`, `operation`, `code`, `attempt_variant` (values: `with_comment`, `without_comment`), `mt5_last_error_code`, `mt5_last_error_message`, and `final_outcome` (values: `recovered`, `unrecoverable`).
- **FR-013**: Operations that complete on the first attempt (no fallback needed) MUST also log `attempt_variant: with_comment` and `final_outcome: success` so the audit trail is complete for all paths.

### Key Entities

- **CommentNormalizer**: The component that sanitizes and length-limits comment values before they are included in MT5 order requests.
- **InvalidCommentSignature**: The specific MT5 error pattern (error code and message) that triggers the adaptive fallback strategy.
- **CommentFallbackResult**: The recorded outcome of a close operation that went through comment compatibility handling: `recovered` (success on attempt 2) or `unrecoverable` (failed on both attempts).
- **CloseOperationAuditRecord**: The structured log entry capturing full comment-compatibility attempt details for a single close operation.

---

## Success Criteria _(mandatory)_

1. **Confirmed failure eliminated**: In a test environment that simulates the invalid-comment broker rejection, 100% of close-position operations that previously failed with the raw tuple error now either succeed via fallback recovery or fail with a user-readable message (never with the raw tuple as primary copy).

2. **Zero false-positive fallbacks**: In a test environment where the broker accepts comments normally, 100% of close operations succeed on the first attempt — the fallback is never triggered unnecessarily.

3. **Human-readable messages in all paths**: In the recovered path, the dashboard shows a warning-category message with no raw MT5 content. In the unrecoverable path, the dashboard shows an error message with a plain-English explanation and `tracking_id`. Neither path shows a raw error tuple.

4. **Audit trail completeness**: In 100% of tested close operations (recovered, unrecoverable, and normal), the structured log entry contains all required observability fields including `attempt_variant` and `final_outcome`.

5. **Normalization correctness**: A test suite covering at least 5 disallowed character patterns and 3 length-boundary cases confirms that the normalizer produces valid comment values in each case.

---

## Assumptions

- The invalid-comment error signature (error code `-2`, message `Invalid "comment" argument`) is the confirmed pattern from observed operations. If additional broker-specific variations are discovered, the signature matcher is extended — but only verified signatures trigger fallback.
- The maximum number of attempts in the fallback strategy is exactly 2 (original + one retry without comment). A third attempt is never made.
- Comment normalization happens synchronously in the request handler before the MT5 worker call — not inside the MT5 worker itself.
- Phase 3 operation lifecycle and `tracking_id` are prerequisites — the `tracking_id` is reused across both attempts of the same operation.

---

## Out of Scope

- Adaptive fallback for endpoints other than `POST /close-position` in Phase 4 (the pending order comment path gets normalization only, not adaptive fallback, in this phase — fallback expansion is explicitly a Phase 7+ concern).
- Comment field support for raw MT5 endpoints (Phase 7).
- Dashboard UI changes beyond receiving and displaying the Phase 1 canonical message (Phase 6).
- Persistent audit storage of comment-compatibility events (structured logs are sufficient).
