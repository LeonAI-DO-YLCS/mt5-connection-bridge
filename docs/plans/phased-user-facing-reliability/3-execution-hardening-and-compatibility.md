# Phase 3: Execution Hardening and Compatibility

> Objective: Make trade-affecting operations deterministic and resilient across broker-specific MT5 behaviors.

---

## 1. Problem This Phase Solves

Even with better messages and readiness, runtime behavior can still be ambiguous due to:

- inconsistent HTTP/business success semantics
- idempotency gaps
- transient MT5 failures without explicit retry classification
- undefined behavior around stale ticks and duplicate clicks

---

## 2. Required Hardening Areas

### 2.1 Deterministic operation lifecycle

Standard operation states for all trade-affecting routes:

- `queued`
- `dispatching`
- `accepted`
- `rejected`
- `recovered`
- `failed_terminal`

Expose state transitions in logs and responses where appropriate.

### 2.2 Idempotency and duplicate protection

1. Add idempotency token support for write operations.
2. Define replay behavior:
   - same request + same token returns previous result envelope.
3. Keep existing single-flight behavior as a complement, not replacement.

### 2.3 Retry classification policy

Define retry behavior by error class:

- retryable transport/runtime interruptions
- non-retryable validation/policy failures
- operation-specific compatibility retries (e.g., comment fallback in Phase 4)

### 2.4 HTTP and business semantics alignment

Unify route behavior to avoid mixed patterns where blocked operations may return HTTP 200 with `success=false`.

---

## 3. Decision Matrix: Business Failure Transport

| Option | Description | Pros | Cons | Recommendation |
|---|---|---|---|---|
| A | Keep mixed model forever | No migration effort | Ambiguous client behavior | No |
| B | Hard flip to strict HTTP semantics immediately | Cleaner | Risky breakage | No |
| C | Migration path with compatibility window and feature flag | Safe transition | Temporary complexity | **Recommended** |

---

## 4. Required Route-Level Alignment

Apply consistent hardening to:

- `POST /execute`
- `POST /pending-order`
- `POST /close-position`
- `PUT /orders/{ticket}`
- `DELETE /orders/{ticket}`
- `PUT /positions/{ticket}/sltp`

For each, define:

1. preflight dependency set
2. idempotency behavior
3. retry policy
4. canonical error codes
5. observability fields

---

## 5. Observability Requirements

Every trade-affecting attempt logs:

- `tracking_id`
- `operation`
- `state_transition`
- `code`
- `retry_count`
- `idempotency_key` (if provided)
- `final_outcome`

---

## 6. Testing Strategy

1. Integration tests for lifecycle/state and idempotency behavior.
2. Negative tests for duplicate submit and race scenarios.
3. Compatibility tests for migration mode vs strict mode.

---

## 7. Exit Criteria

1. All write operations share the same behavioral contract.
2. Duplicate-click/retry ambiguity is eliminated.
3. Route semantics are clear to both dashboard and API consumers.

