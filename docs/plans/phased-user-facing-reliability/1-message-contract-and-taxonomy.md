# Phase 1: Message Contract and Taxonomy

> Objective: Replace technical leak-through with a canonical user-facing message contract while preserving backward compatibility.

---

## 1. Problem This Phase Solves

Current behavior mixes multiple error shapes and exposes technical detail directly in dashboard alerts.  
Operators cannot reliably distinguish:

- user input mistake
- broker restriction
- transient MT5 transport issue
- bridge internal error

---

## 2. Contract Definition

### 2.1 Canonical envelope

All user-facing messages should normalize to:

- `ok` (boolean)
- `category` (`error|warning|status|advice|success|info`)
- `code` (stable semantic code)
- `tracking_id` (unique per event)
- `title` (human summary)
- `message` (plain-English explanation)
- `action` (next operator step)
- `severity` (`low|medium|high|critical`)
- `retryable` (boolean)
- `context` (sanitized technical hints)

### 2.2 Compatibility rules

1. Keep HTTP status behavior unless phase-specific migration says otherwise.
2. Keep `X-Error-Code` header; map it to canonical `code`.
3. Continue supporting legacy `detail` consumers during migration.

---

## 3. Error and Warning Taxonomy

### 3.1 Minimum required namespaces

- Validation:
  - `VALIDATION_CURRENT_PRICE_GT_ZERO`
  - `VALIDATION_VOLUME_RANGE`
  - `VALIDATION_VOLUME_STEP`
- Connectivity/runtime:
  - `MT5_DISCONNECTED`
  - `MT5_RUNTIME_UNAVAILABLE`
  - `WORKER_RECONNECT_EXHAUSTED`
- Policy/capability:
  - `EXECUTION_DISABLED`
  - `SYMBOL_TRADE_MODE_RESTRICTED`
  - `FILLING_MODE_UNSUPPORTED`
- Request-compatibility:
  - `MT5_REQUEST_COMMENT_INVALID`
  - `MT5_REQUEST_SYMBOL_NOT_SELECTABLE`
- Generic:
  - `REQUEST_REJECTED`
  - `INTERNAL_SERVER_ERROR`

### 3.2 Severity model

- `critical`: operation unsafe or system unavailable.
- `high`: operation blocked and operator intervention needed.
- `medium`: operation blocked but user-correctable.
- `low`: non-blocking warning/advice.

---

## 4. Decision Matrix: Where To Normalize

| Option | Description | Pros | Cons | Recommendation |
|---|---|---|---|---|
| A | Normalize only in dashboard | Fast | API consumers still fragmented | No |
| B | Normalize only backend | Better API | UI still inconsistent if not updated | Partial |
| C | Backend canonicalization + dashboard renderer | Complete and durable | More work | **Recommended** |

---

## 5. Implementation Plan (Phase 1 Scope)

1. Backend:
   - Introduce message-normalization utility module.
   - Wrap validation, HTTP exceptions, and MT5 mapped errors into canonical envelope.
   - Add tracking ID generation and propagation.
2. Dashboard:
   - Introduce centralized message center renderer.
   - Replace direct `alert` calls in critical paths with renderer.
   - Keep collapsible “Details” section for technical context.
3. Logging:
   - Include `code` and `tracking_id` in structured logs.

---

## 6. Testing Strategy

1. Contract tests:
   - canonical envelope fields present for representative failures.
2. Integration tests:
   - `/execute`, `/close-position`, `/pending-order`, `/order-check` error cases.
3. UI behavior tests:
   - user sees human-readable title/message/action and tracking ID.

---

## 7. Exit Criteria

1. No raw MT5 tuple/validation arrays shown as primary user message.
2. Every blocked operation includes canonical `code` + `tracking_id`.
3. Legacy clients still function during compatibility window.

