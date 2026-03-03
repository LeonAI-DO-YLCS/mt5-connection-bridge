# Feature Specification: Phase 1 — Message Contract and Taxonomy

**Feature Branch**: `010-phase1-message-contract-and-taxonomy`
**Created**: 2026-03-03
**Status**: Draft
**Plan Reference**: `docs/plans/phased-user-facing-reliability/1-message-contract-and-taxonomy.md`
**Phase Dependency**: Phase 0 (baseline and invariants must be agreed upon first)

---

## Overview

The MT5 Bridge currently exposes raw technical failure details directly to operators: MT5 error tuples, Pydantic validation arrays, and mixed response shapes (some with `detail: string`, others with `success: false`, others with raw error tuples). Operators cannot reliably distinguish a typo in their input from a broker restriction from a transient MT5 connectivity drop.

This phase replaces all user-facing technical leak-through with a **canonical message envelope** that is consistent, human-readable, and actionable — while maintaining full backward compatibility so existing API consumers continue to work during the migration window.

---

## User Scenarios & Testing _(mandatory)_

### Primary User Story

As a trading operator using the dashboard, when any operation fails I want to see a clear title, a plain-English explanation, and a specific next step — never raw JSON, never MT5 tuples, never Pydantic error arrays — so that I can immediately understand what happened and what to do next without needing to read backend logs.

As a support engineer handling an operator-reported incident, I want every failure event to carry a unique `tracking_id` and a stable semantic `code` — so that I can locate the exact backend log entry from the operator's dashboard screenshot within seconds.

### Acceptance Scenarios

1. **Given** an operator submits a trade with an invalid quantity, **When** the request is rejected, **Then** the dashboard shows a human-readable title (e.g. "Invalid trade volume"), a plain-English explanation, the next corrective step, and a `tracking_id` — and no Pydantic array or technical field name is shown as primary message copy.

2. **Given** the MT5 worker loses connection mid-operation, **When** the failure reaches the dashboard, **Then** the dashboard shows a message in the `error` category, severity `critical`, with `retryable: true`, a clear next step ("Wait for reconnect, then retry"), and a `tracking_id`.

3. **Given** a broker rejects a fill mode, **When** the rejection reaches the dashboard, **Then** the message category is `error`, the code is `FILLING_MODE_UNSUPPORTED`, and the action text names the specific corrective step — not a raw MT5 retcode number.

4. **Given** an existing API consumer that reads the `detail` field from error responses, **When** the backend is migrated to the canonical envelope, **Then** the `detail` field continues to be populated with a backward-compatible string during the migration window so the consumer is not broken.

5. **Given** a structured log entry for any operation failure, **When** the log is inspected, **Then** it contains both the canonical `code` and the `tracking_id`, so log searches by either field work immediately.

6. **Given** a success response from any trade-affecting endpoint, **When** the response is inspected, **Then** it also uses the canonical envelope shape (`ok: true`, `category: success`) — not a different ad-hoc success shape.

### Edge Cases

- What if an unknown MT5 retcode arrives that has no mapping in the taxonomy? → It is mapped to `REQUEST_REJECTED` with `severity: high`, the raw retcode is preserved in the `context` field (sanitized, not shown by default), and the action text instructs the operator to contact support with the `tracking_id`.
- What if two concurrent requests fail at the millisecond boundary with the same timestamp? → Each gets a unique `tracking_id` regardless of timestamp because the ID includes a random component.
- What if the backend fails before it can construct the canonical envelope (e.g., unhandled exception)? → A last-resort envelope is returned with `code: INTERNAL_SERVER_ERROR`, a generic human-readable title, and a generated `tracking_id`, so the operator is never shown a raw 500 stack trace.

---

## Requirements _(mandatory)_

### Functional Requirements

**Canonical Message Envelope**

- **FR-001**: Every user-facing response — success and failure — from trade-affecting endpoints MUST be normalized to a canonical envelope containing: `ok`, `category`, `code`, `tracking_id`, `title`, `message`, `action`, `severity`, `retryable`, and `context`.
- **FR-002**: The `category` field MUST use one of: `error`, `warning`, `status`, `advice`, `success`, `info` — as defined in the Phase 0 glossary.
- **FR-003**: The `code` field MUST use a stable semantic code from the namespace defined in Phase 0.
- **FR-004**: The `tracking_id` field MUST be a unique identifier generated per event according to the format policy defined in Phase 0.
- **FR-005**: The `title` field MUST be a concise human summary (no raw field names, no MT5 internals).
- **FR-006**: The `message` field MUST be a plain-English explanation of what happened.
- **FR-007**: The `action` field MUST state the concrete next step the operator should take.
- **FR-008**: The `severity` field MUST be one of: `low`, `medium`, `high`, `critical` — mapped from the failure class per the Phase 0 severity scale.
- **FR-009**: The `retryable` field MUST be a boolean indicating whether the same operation can be retried without changes.
- **FR-010**: The `context` field MUST contain sanitized technical hints (no credentials, no file paths) and MUST NOT be shown as primary UI copy.

**Error and Warning Taxonomy**

- **FR-011**: The backend MUST implement the minimum required error code namespaces: validation, connectivity/runtime, policy/capability, request-compatibility, and generic fallback — as defined in the Phase 0 namespace policy.
- **FR-012**: Every known MT5 `retcode` and `last_error()` pattern that is observed in operations MUST have a mapped canonical code — unmapped codes fall back to `REQUEST_REJECTED`.

**Backend Normalization**

- **FR-013**: The backend MUST introduce a message-normalization utility that wraps Pydantic validation errors, HTTP exceptions, and MT5-mapped errors into the canonical envelope before the response leaves the server.
- **FR-014**: The `tracking_id` MUST be generated in the normalization layer and included in the structured log entry for the same event.
- **FR-015**: The `code` and `tracking_id` MUST be included in structured log output so they are searchable without parsing raw message text.

**Dashboard Rendering**

- **FR-016**: The dashboard MUST introduce a centralized message renderer that reads the canonical envelope and displays `title`, `message`, and `action` as primary content.
- **FR-017**: The dashboard MUST replace direct `alert()`, `confirm()`, and `prompt()` usage in critical operation paths with the centralized renderer.
- **FR-018**: The dashboard MUST display the `tracking_id` in every rendered failure message, with a one-click copy shortcut.
- **FR-019**: The dashboard MUST provide a collapsible "Details" section in the message renderer that exposes the `context` field for advanced troubleshooting.
- **FR-020**: The dashboard renderer MUST apply consistent visual styling by `category` and `severity` (e.g., `critical/error` shown differently from `low/advice`).

**Backward Compatibility**

- **FR-021**: During the migration window, the backend MUST continue to populate the legacy `detail` field alongside the canonical envelope so existing API consumers are not broken.
- **FR-022**: The HTTP status code behavior MUST remain unchanged in this phase unless explicitly moved in Phase 3.
- **FR-023**: The `X-Error-Code` response header MUST be preserved and mapped to the canonical `code` value.

### Key Entities

- **MessageEnvelope**: The canonical response shape carrying `ok`, `category`, `code`, `tracking_id`, `title`, `message`, `action`, `severity`, `retryable`, and `context`.
- **ErrorCodeTaxonomy**: The enumerated map of semantic codes to their human-readable titles, message templates, severity defaults, and retryable defaults.
- **TrackingID**: A unique event identifier generated per failure or success, included in both the API response and the structured log.
- **MessageRenderer**: The dashboard component responsible for converting a `MessageEnvelope` into displayed UI copy, styling, and copy-to-clipboard affordances.

---

## Success Criteria _(mandatory)_

1. **No raw technical content as primary copy**: On a random sample of 10 different failure scenarios across the dashboard, zero raw MT5 tuples, Pydantic field arrays, or JSON keys appear as the primary user-visible error text.

2. **Tracking ID searchability**: Given any `tracking_id` from a dashboard message, a support engineer can locate the corresponding structured log entry in under 60 seconds.

3. **Taxonomy coverage**: 100% of observed failure classes from the Phase 0 baseline (MT5 `last_error()` tuples, broker `retcode` patterns, Pydantic validation arrays) have a mapped canonical code.

4. **Backward compatibility intact**: Existing API consumers that read the `detail` field from error responses continue to function without modification during the migration window.

5. **Dashboard renderer adoption**: All critical operation paths (execute, close, pending order, order check) use the centralized renderer — no lingering direct `alert()` calls in those paths.

6. **Log correlation**: 100% of structured log entries for operation failures contain both `code` and `tracking_id` as searchable fields.

---

## Assumptions

- The Phase 0 glossary and error-code namespace are finalized before this phase begins — this spec does not re-define those; it relies on them.
- The migration window for legacy `detail` field support extends until Phase 6 (Dashboard Operator Experience) is complete, or until no known legacy consumers remain — whichever comes first.
- The `context` field is not shown as primary UI copy but must be available for advanced users in "Details" expand. Hiding it by default is a dashboard implementation detail.
- `tracking_id` uniqueness is scoped to a single bridge runtime session (not globally unique across restarts); support workflows are expected to also capture the bridge run ID for cross-session disambiguation.

---

## Out of Scope

- Changes to HTTP status code semantics (those belong to Phase 3).
- Idempotency or retry logic (Phase 3).
- Preflight/readiness gating (Phase 2).
- Close-order comment compatibility (Phase 4).
- Dashboard layout redesign beyond message rendering (Phase 6).
- MT5 parity expansion (Phase 7).
