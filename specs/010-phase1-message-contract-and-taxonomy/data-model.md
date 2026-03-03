# Data Model: Phase 1 — Message Contract and Taxonomy

**Branch**: `010-phase1-message-contract-and-taxonomy`
**Date**: 2026-03-03
**Source**: [spec.md](./spec.md) key entities, grounded by [research.md](./research.md)

---

## Entity Definitions

Phase 1 introduces runtime data structures (Pydantic models and JS rendering logic) that are used in every API response and dashboard interaction.

---

### 1. MessageEnvelope

The canonical response shape for all user-facing messages from trade-affecting endpoints.

| Field         | Type    | Required | Description                                                                             |
| ------------- | ------- | -------- | --------------------------------------------------------------------------------------- |
| `ok`          | boolean | yes      | `true` for success, `false` for any failure                                             |
| `category`    | enum    | yes      | One of: `error`, `warning`, `status`, `advice`, `success`, `info`                       |
| `code`        | string  | yes      | Stable semantic code from `ErrorCodeTaxonomy` (e.g., `VALIDATION_VOLUME_RANGE`)         |
| `tracking_id` | string  | yes      | Unique per-event ID in format `brg-<YYYYMMDDTHHMMSS>-<hex4>`                            |
| `title`       | string  | yes      | Concise human summary (≤ 80 chars). No raw field names or MT5 internals                 |
| `message`     | string  | yes      | Plain-English explanation of what happened                                              |
| `action`      | string  | yes      | Concrete next step the operator should take                                             |
| `severity`    | enum    | yes      | One of: `low`, `medium`, `high`, `critical`                                             |
| `retryable`   | boolean | yes      | Whether the same operation can be retried without changes                               |
| `context`     | dict    | no       | Sanitized technical hints (no credentials, no file paths). Not shown as primary UI copy |

**Implementation**: Pydantic v2 `BaseModel` in `app/messaging/envelope.py`.

**Serialization rule**: When serialized to JSON, `context` defaults to `{}` if not provided.

---

### 2. ErrorCodeTaxonomy

Enumerated map of all semantic error codes with their default metadata.

| Field                 | Type                 | Description                                                                                |
| --------------------- | -------------------- | ------------------------------------------------------------------------------------------ |
| `code`                | string (enum member) | The stable code name (e.g., `VALIDATION_VOLUME_RANGE`)                                     |
| `domain`              | string               | Domain prefix: `VALIDATION`, `MT5`, `EXECUTION`, `WORKER`, `SYMBOL`, `REQUEST`, `INTERNAL` |
| `default_title`       | string               | Default human-readable title template                                                      |
| `default_message`     | string               | Default plain-English explanation template                                                 |
| `default_action`      | string               | Default next-step text                                                                     |
| `default_severity`    | enum                 | Default severity: `low`, `medium`, `high`, `critical`                                      |
| `default_retryable`   | boolean              | Default retryable flag                                                                     |
| `default_http_status` | int                  | Typical HTTP status code                                                                   |
| `category`            | enum                 | Default message category: `error`, `warning`, etc.                                         |

**Implementation**: Python `enum.Enum` subclass in `app/messaging/codes.py`. Each member carries its metadata as attributes.

#### Initial Code Registry

| Code                               | Domain     | Title                           | Severity | Retryable | HTTP | Category |
| ---------------------------------- | ---------- | ------------------------------- | -------- | --------- | ---- | -------- |
| `VALIDATION_VOLUME_RANGE`          | VALIDATION | Invalid trade volume            | medium   | false     | 422  | error    |
| `VALIDATION_VOLUME_STEP`           | VALIDATION | Invalid volume step             | medium   | false     | 422  | error    |
| `VALIDATION_CURRENT_PRICE_GT_ZERO` | VALIDATION | Price must be positive          | medium   | false     | 422  | error    |
| `VALIDATION_ERROR`                 | VALIDATION | Input validation failed         | medium   | false     | 422  | error    |
| `MT5_DISCONNECTED`                 | MT5        | MT5 terminal disconnected       | critical | true      | 503  | error    |
| `MT5_RUNTIME_UNAVAILABLE`          | MT5        | MT5 runtime unavailable         | critical | true      | 503  | error    |
| `WORKER_RECONNECT_EXHAUSTED`       | WORKER     | Reconnection attempts exhausted | critical | false     | 503  | error    |
| `EXECUTION_DISABLED`               | EXECUTION  | Execution disabled by policy    | high     | false     | 403  | error    |
| `SYMBOL_TRADE_MODE_RESTRICTED`     | SYMBOL     | Symbol trade mode restricted    | high     | false     | 422  | error    |
| `SYMBOL_NOT_CONFIGURED`            | SYMBOL     | Symbol not configured           | high     | false     | 404  | error    |
| `FILLING_MODE_UNSUPPORTED`         | SYMBOL     | Filling mode not supported      | high     | false     | 422  | error    |
| `REQUEST_REJECTED`                 | REQUEST    | Trade request rejected          | high     | false     | 400  | error    |
| `OVERLOAD_OR_SINGLE_FLIGHT`        | REQUEST    | Execution queue busy            | medium   | true      | 409  | warning  |
| `INTERNAL_SERVER_ERROR`            | INTERNAL   | Internal server error           | critical | true      | 500  | error    |
| `UNAUTHORIZED_API_KEY`             | INTERNAL   | Authentication required         | high     | false     | 401  | error    |
| `RESOURCE_NOT_FOUND`               | REQUEST    | Resource not found              | medium   | false     | 404  | error    |
| `SERVICE_UNAVAILABLE`              | MT5        | Service temporarily unavailable | critical | true      | 503  | error    |
| `REQUEST_ERROR`                    | REQUEST    | Request error                   | medium   | false     | 400  | error    |

---

### 3. TrackingID

A unique event identifier generated per operation event.

| Field              | Type     | Description                                             |
| ------------------ | -------- | ------------------------------------------------------- |
| `value`            | string   | Full tracking ID string: `brg-<YYYYMMDDTHHMMSS>-<hex4>` |
| `timestamp`        | datetime | UTC timestamp embedded in the ID                        |
| `random_component` | string   | 4-character hex suffix for uniqueness within a second   |

**Implementation**: Not a Pydantic model — a factory function `generate_tracking_id()` in `app/messaging/tracking.py` that returns a plain string.

**Propagation path**:

1. Generated in normalizer → included in `MessageEnvelope.tracking_id`
2. Written to structured log entry (searchable field)
3. Sent in HTTP response body (inside envelope)
4. Sent in `X-Tracking-ID` response header
5. Displayed in dashboard message renderer with copy-to-clipboard affordance

---

### 4. MessageEnvelopeException

Custom exception class that carries a pre-built `MessageEnvelope` for route-level failures.

| Field         | Type            | Description                        |
| ------------- | --------------- | ---------------------------------- |
| `status_code` | int             | HTTP status code to return         |
| `envelope`    | MessageEnvelope | Pre-constructed canonical envelope |

**Implementation**: Subclass of `HTTPException` in `app/messaging/envelope.py`. Registered as a FastAPI exception handler in `main.py`.

**Usage pattern**:

```python
raise MessageEnvelopeException(
    status_code=422,
    code=ErrorCode.SYMBOL_TRADE_MODE_RESTRICTED,
    message="Symbol EURUSD only allows long (buy) trades.",
    action="Change to a buy action or select a different symbol.",
    context={"symbol": "EURUSD", "trade_mode": 1},
)
```

---

### 5. MessageRenderer (dashboard)

The dashboard component responsible for rendering `MessageEnvelope` objects.

| Property     | Type        | Description                                                      |
| ------------ | ----------- | ---------------------------------------------------------------- |
| `envelope`   | object      | The parsed MessageEnvelope JSON from the API response            |
| `container`  | HTMLElement | DOM element where the message renders                            |
| `autoHideMs` | number      | Auto-dismiss timeout for success/info messages (default: 5000ms) |

**Rendering rules**:

- **Title**: Bold, styled by severity color
- **Message**: Body text below title
- **Action**: Highlighted next-step text
- **Tracking ID**: Monospace, with clipboard copy button. Always shown for `error` and `warning` categories
- **Details toggle**: Collapsible section showing `context` as formatted key-value pairs
- **Severity styling**: `critical` → red border/icon, `high` → orange, `medium` → yellow, `low` → blue, `success` → green

**Implementation**: `dashboard/js/message-renderer.js` exporting `renderMessage(envelope, container)`.

---

## Relationships

```
MessageEnvelope.code → ErrorCodeTaxonomy (must be a valid code member)
MessageEnvelope.tracking_id → TrackingID (generated by tracking.py)
MessageEnvelopeException.envelope → MessageEnvelope (carries pre-built envelope)
MessageRenderer.envelope → MessageEnvelope (parsed from API response)
ErrorCodeTaxonomy.severity → TerminologyGlossary.severity_scale (Phase 0 reference)
ErrorCodeTaxonomy.category → TerminologyGlossary.core_terms (Phase 0 reference)
```

## State Transitions

N/A — Phase 1 entities are request-scoped. No persistent state transitions.

## Validation Rules

1. Every `MessageEnvelope.code` must be a member of `ErrorCodeTaxonomy`.
2. Every `MessageEnvelope.category` must be one of the 6 defined values.
3. Every `MessageEnvelope.severity` must be one of the 4 defined levels.
4. `tracking_id` must match the pattern `brg-\d{8}T\d{6}-[0-9a-f]{4}`.
5. `title` must not exceed 80 characters.
6. `context` must not contain keys named `password`, `secret`, `key`, `token`, or `credential`.
