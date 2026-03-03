# Feature Specification: Phase 3 — Execution Hardening and Compatibility

**Feature Branch**: `012-phase3-execution-hardening-and-compatibility`
**Created**: 2026-03-03
**Status**: Draft
**Plan Reference**: `docs/plans/phased-user-facing-reliability/3-execution-hardening-and-compatibility.md`
**Phase Dependency**: Phase 0 (baseline), Phase 1 (message contract), Phase 2 (readiness)

---

## Overview

Even with improved error messages (Phase 1) and upfront readiness gating (Phase 2), trade-affecting operations can still produce ambiguous outcomes at runtime. The bridge currently has no uniform operation lifecycle model: some routes return HTTP 200 with `success: false` for business failures, there is no protection against duplicate-click scenarios, and there is no explicit classification of which failures can be safely retried vs. which must not.

This phase introduces a **deterministic execution model** for all trade-affecting operations: a shared operation lifecycle with named states, idempotency token support, a classified retry policy, and aligned HTTP/business semantics — making every write operation's outcome unambiguous for both the dashboard and any API consumer.

---

## User Scenarios & Testing _(mandatory)_

### Primary User Story

As a trading operator, when I click "Execute Trade" and the dashboard appears to hang or returns an unexpected result, I want to know precisely whether my trade was queued, was accepted by the broker, was rejected, or failed — without ambiguity about whether clicking again would duplicate the order.

As an API consumer integrating with the bridge programmatically, I want each trade-affecting request to behave predictably: business failures return the appropriate error HTTP status (not 200 with a failure body), retryable errors are labeled as such, and I can submit an idempotency key to prevent duplicate orders on retry.

### Acceptance Scenarios

1. **Given** an operator rapidly double-clicks the "Execute" button before the first response arrives, **When** the second request reaches the bridge, **Then** the bridge detects the idempotency key collision and returns the result of the first request — no duplicate order is sent to MT5.

2. **Given** a transient MT5 connectivity interruption during a trade operation, **When** the response is returned, **Then** the `retryable` field in the canonical envelope is `true`, the operation state is `failed_terminal` or `rejected` (with a clear state label), and the operator is told it is safe to retry.

3. **Given** a validation failure (e.g., zero volume), **When** the request is rejected, **Then** the HTTP response status is not 200, the canonical envelope `retryable` is `false`, and the message clearly explains the operator must correct their input.

4. **Given** any trade-affecting request, **When** the operation proceeds through the bridge, **Then** the structured log contains: `tracking_id`, `operation`, `state_transition`, `code`, `retry_count`, and `final_outcome` — making the full lifecycle readable from logs alone.

5. **Given** a legacy API consumer that expects HTTP 200 for all responses (even business failures), **When** the phase is deployed with the compatibility migration window active, **Then** the consumer continues to receive HTTP 200 during the window, and a deprecation header signals the upcoming change.

6. **Given** an operation that passes from `queued` → `dispatching` → `rejected`, **When** the response is returned, **Then** the `state_transition` field in the response and log accurately reflects that sequence.

### Edge Cases

- What if the idempotency key was used in a previous bridge session (after a restart)? → Idempotency keys are scoped to the current bridge runtime session; a restart clears the idempotency store, and the same key from a new session is treated as a fresh request.
- What if two different requests are submitted with the same idempotency key but different parameters? → The bridge returns an error (`IDEMPOTENCY_KEY_CONFLICT`) with a clear explanation that the same key was already used with different parameters.
- What if the operation state machine reaches an unexpected internal state? → The state is logged as `state: unknown`, a `INTERNAL_SERVER_ERROR` canonical code is returned, and the operator is told to contact support with the `tracking_id`.

---

## Requirements _(mandatory)_

### Functional Requirements

**Deterministic Operation Lifecycle**

- **FR-001**: Every trade-affecting route MUST use a shared set of operation states: `queued`, `dispatching`, `accepted`, `rejected`, `recovered`, `failed_terminal`.
- **FR-002**: The operation state MUST be logged at each transition and MUST be included in the final response where the state is meaningful to the operator.
- **FR-003**: The final `state` MUST be unambiguous: an `accepted` state means the broker confirmed the order; `rejected` means the broker or bridge denied it; `failed_terminal` means a non-recoverable system failure prevented completion.

**Idempotency**

- **FR-004**: All write operations (`POST /execute`, `POST /pending-order`, `POST /close-position`, `PUT /orders/{ticket}`, `DELETE /orders/{ticket}`, `PUT /positions/{ticket}/sltp`) MUST accept an optional `Idempotency-Key` header.
- **FR-005**: If the same `Idempotency-Key` is submitted more than once within the same bridge session, the bridge MUST return the result of the first request without re-executing the operation.
- **FR-006**: If the same `Idempotency-Key` is submitted with different request parameters, the bridge MUST return a canonical error (`IDEMPOTENCY_KEY_CONFLICT`) with `retryable: false`.
- **FR-007**: The idempotency key scope MUST be per bridge runtime session; session restart clears the idempotency store.
- **FR-008**: The existing single-flight behavior (preventing concurrent duplicate submissions of the same operation type without an idempotency key) MUST remain active as a complementary mechanism.

**Retry Classification**

- **FR-009**: Every failure response MUST include a `retryable` field (boolean) in the canonical envelope.
- **FR-010**: Retryable classes MUST include: transient MT5 transport errors, worker queue overload conditions.
- **FR-011**: Non-retryable classes MUST include: business validation failures, policy/capability rejections, permanent broker rejections (e.g., invalid symbol, insufficient margin).
- **FR-012**: Operation-specific compatibility retries (e.g., comment fallback defined in Phase 4) are handled internally and do not expose a `retryable` signal to the caller — they appear as a single atomic outcome.

**HTTP and Business Semantics Alignment**

- **FR-013**: Business failures (broker rejection, validation failure, policy block) MUST return an appropriate non-200 HTTP status code (4xx for client-correctable failures, 503 for transient unavailability).
- **FR-014**: During the migration window, a compatibility mode MUST maintain HTTP 200 for business failures for consumers that require it, activated by a feature flag.
- **FR-015**: The feature flag transition MUST be reversible — switching back to compatibility mode must not require a code change or restart of the bridge.
- **FR-016**: A deprecation signal (e.g., a response header) MUST be included in compatibility-mode responses to notify consumers that the behavior will change.

**Route-Level Hardening (all trade-affecting routes)**

- **FR-017**: For each of `POST /execute`, `POST /pending-order`, `POST /close-position`, `PUT /orders/{ticket}`, `DELETE /orders/{ticket}`, `PUT /positions/{ticket}/sltp`, the implementation MUST explicitly define: preflight dependency set, idempotency behavior, retry policy, canonical error codes, and observability fields.

**Observability**

- **FR-018**: Every trade-affecting operation attempt MUST produce a structured log entry containing: `tracking_id`, `operation`, `state_transition`, `code`, `retry_count`, `idempotency_key` (if provided), and `final_outcome`.

### Key Entities

- **OperationLifecycle**: The shared set of named states (`queued`, `dispatching`, `accepted`, `rejected`, `recovered`, `failed_terminal`) that every trade-affecting operation transitions through.
- **IdempotencyKey**: An operator-supplied key that prevents duplicate execution of the same write operation within a bridge session.
- **RetryClassification**: The policy that determines whether a given failure class is safe to retry without operator intervention.
- **CompatibilityWindow**: The period during which the bridge supports both legacy HTTP-200-for-failures behavior and the new strict HTTP semantics, controlled by a feature flag.
- **ExecutionObservabilityRecord**: The structured log entry that captures the full lifecycle of a single trade-affecting operation attempt.

---

## Success Criteria _(mandatory)_

1. **No ambiguous outcomes**: In a test suite covering all six trade-affecting routes, every operation reaches one of the defined terminal states (`accepted`, `rejected`, `failed_terminal`) — no operation ends with an undefined or unlogged state.

2. **Duplicate-click protection**: In a controlled test simulating rapid double-submit on execute/close operations with an idempotency key, zero duplicate MT5 orders are created.

3. **Retry signal correctness**: For at least 10 distinct failure scenarios, the `retryable` field in the response correctly predicts whether retrying the same request will produce a different (success) outcome.

4. **Log completeness**: In 100% of tested trade-affecting operations, the structured log entry contains all required observability fields (`tracking_id`, `operation`, `state_transition`, `code`, `retry_count`, `final_outcome`).

5. **Migration window safety**: With the compatibility flag active, existing API consumers that read HTTP status codes and response bodies continue to function identically to before this phase was deployed.

6. **Semantics alignment**: After the migration migration window, operators and API consumers receive appropriate 4xx/5xx HTTP status codes for all business failures — confirmed by contract tests on each route.

---

## Assumptions

- The idempotency store is in-memory (not persisted to disk). Bridge restarts clear it. This is acceptable because idempotency is primarily a guard against fast duplicate requests, not a long-term deduplication mechanism.
- The feature flag controlling the compatibility/strict HTTP semantics mode is an environment variable readable at runtime without restart.
- The "single-flight" mechanism (preventing concurrent identical operations) already exists in the bridge and is preserved as-is; idempotency keys are an additional layer, not a replacement.
- Phase 1 canonical envelope and tracking ID are prerequisites — this phase assumes they are already in place.

---

## Out of Scope

- Comment-field compatibility fallback logic (Phase 4).
- Dashboard UI changes beyond displaying `state` and `retryable` in message responses (Phase 6).
- Launcher or runtime script changes (Phase 5).
- MT5 parity expansion (Phase 7).
- Cross-session idempotency (persistent across restarts).
