# API Contracts: Phase 1 — Message Contract and Taxonomy

**Branch**: `010-phase1-message-contract-and-taxonomy`
**Date**: 2026-03-03
**Purpose**: Define the canonical envelope schema, error code registry, and response contracts for all trade-affecting endpoints.

---

## 1. Canonical Envelope Schema

### 1.1 Response body (all trade-affecting endpoints)

All user-facing responses — success and failure — from trade-affecting endpoints MUST include these fields:

```json
{
  "ok": true,
  "category": "success",
  "code": "REQUEST_OK",
  "tracking_id": "brg-20260303T094500-a3f7",
  "title": "Trade executed successfully",
  "message": "Your buy order for 0.01 lots of EURUSD was filled at 1.08350.",
  "action": "No action required.",
  "severity": "low",
  "retryable": false,
  "context": {},
  "detail": "Trade executed successfully"
}
```

#### Field definitions

| Field         | Type            | Required | Constraints                                                                                 |
| ------------- | --------------- | -------- | ------------------------------------------------------------------------------------------- |
| `ok`          | boolean         | yes      | `true` iff the operation succeeded                                                          |
| `category`    | string          | yes      | Enum: `error`, `warning`, `status`, `advice`, `success`, `info`                             |
| `code`        | string          | yes      | Must be a member of the Error Code Registry (§2)                                            |
| `tracking_id` | string          | yes      | Format: `brg-<YYYYMMDDTHHMMSS>-<hex4>`, ≤ 30 chars                                          |
| `title`       | string          | yes      | ≤ 80 chars. No raw field names, MT5 internals, or retcodes                                  |
| `message`     | string          | yes      | Plain English explanation                                                                   |
| `action`      | string          | yes      | Concrete next step for the operator                                                         |
| `severity`    | string          | yes      | Enum: `low`, `medium`, `high`, `critical`                                                   |
| `retryable`   | boolean         | yes      | Whether the same request can be retried without changes                                     |
| `context`     | object          | yes      | Sanitized technical hints. Defaults to `{}`. Must not contain credentials                   |
| `detail`      | string \| array | yes      | **Legacy compatibility**: populated with the same content as the pre-Phase-1 `detail` field |

### 1.2 Response headers

| Header          | Value                  | Notes                                |
| --------------- | ---------------------- | ------------------------------------ |
| `X-Error-Code`  | Canonical `code` value | Preserved for backward compatibility |
| `X-Tracking-ID` | `tracking_id` value    | New in Phase 1                       |

### 1.3 HTTP status codes

HTTP status code semantics are **unchanged** from the current behavior. The canonical envelope is carried in the body; HTTP status codes are not modified in Phase 1 (deferred to Phase 3).

---

## 2. Error Code Registry

### 2.1 Validation domain

| Code                               | HTTP | Severity | Retryable | Default Title           | Default Action                                             |
| ---------------------------------- | ---- | -------- | --------- | ----------------------- | ---------------------------------------------------------- |
| `VALIDATION_VOLUME_RANGE`          | 422  | medium   | false     | Invalid trade volume    | Adjust the volume to be within the symbol's allowed range. |
| `VALIDATION_VOLUME_STEP`           | 422  | medium   | false     | Invalid volume step     | Round the volume to the nearest valid step size.           |
| `VALIDATION_CURRENT_PRICE_GT_ZERO` | 422  | medium   | false     | Price must be positive  | Provide a current price greater than zero.                 |
| `VALIDATION_ERROR`                 | 422  | medium   | false     | Input validation failed | Check the highlighted fields and correct the input.        |

### 2.2 Connectivity / runtime domain

| Code                         | HTTP | Severity | Retryable | Default Title                   | Default Action                                   |
| ---------------------------- | ---- | -------- | --------- | ------------------------------- | ------------------------------------------------ |
| `MT5_DISCONNECTED`           | 503  | critical | true      | MT5 terminal disconnected       | Wait for automatic reconnect, then retry.        |
| `MT5_RUNTIME_UNAVAILABLE`    | 503  | critical | true      | MT5 runtime unavailable         | Check that the MetaTrader 5 terminal is running. |
| `WORKER_RECONNECT_EXHAUSTED` | 503  | critical | false     | Reconnection failed             | Restart the bridge manually.                     |
| `SERVICE_UNAVAILABLE`        | 503  | critical | true      | Service temporarily unavailable | Wait a moment and retry the operation.           |

### 2.3 Policy / capability domain

| Code                           | HTTP | Severity | Retryable | Default Title                | Default Action                                                            |
| ------------------------------ | ---- | -------- | --------- | ---------------------------- | ------------------------------------------------------------------------- |
| `EXECUTION_DISABLED`           | 403  | high     | false     | Execution disabled by policy | Enable execution via environment config or the dashboard toggle.          |
| `SYMBOL_TRADE_MODE_RESTRICTED` | 422  | high     | false     | Symbol trade mode restricted | Select a different action or choose a symbol that allows this trade type. |
| `SYMBOL_NOT_CONFIGURED`        | 404  | high     | false     | Symbol not configured        | Add the symbol to `symbols.yaml` or use the direct symbol field.          |
| `FILLING_MODE_UNSUPPORTED`     | 422  | high     | false     | Filling mode not supported   | Contact support with the tracking ID.                                     |

### 2.4 Request compatibility domain

| Code                        | HTTP | Severity | Retryable | Default Title          | Default Action                                      |
| --------------------------- | ---- | -------- | --------- | ---------------------- | --------------------------------------------------- |
| `REQUEST_REJECTED`          | 400  | high     | false     | Trade request rejected | Review the order parameters and try again.          |
| `OVERLOAD_OR_SINGLE_FLIGHT` | 409  | medium   | true      | Execution queue busy   | Wait for the current trade to complete, then retry. |
| `RESOURCE_NOT_FOUND`        | 404  | medium   | false     | Resource not found     | Verify the ticket or resource identifier.           |
| `REQUEST_ERROR`             | 400  | medium   | false     | Request error          | Review the request and try again.                   |

### 2.5 Generic / internal domain

| Code                    | HTTP | Severity | Retryable | Default Title           | Default Action                                    |
| ----------------------- | ---- | -------- | --------- | ----------------------- | ------------------------------------------------- |
| `INTERNAL_SERVER_ERROR` | 500  | critical | true      | Internal server error   | Contact support with the tracking ID shown above. |
| `UNAUTHORIZED_API_KEY`  | 401  | high     | false     | Authentication required | Provide a valid API key in the request header.    |

### 2.6 Success codes

| Code         | HTTP | Category | Title                            |
| ------------ | ---- | -------- | -------------------------------- |
| `REQUEST_OK` | 200  | success  | Operation completed successfully |

### 2.7 Governance rules

1. **Naming**: `<DOMAIN>_<SPECIFIC_CONDITION>`, uppercase with underscores
2. **Domains**: `VALIDATION`, `MT5`, `EXECUTION`, `WORKER`, `SYMBOL`, `REQUEST`, `INTERNAL`
3. **Collisions**: New codes must be checked against this registry before adoption
4. **Deprecation**: Codes are never removed; they can be deprecated with a successor noted
5. **Unmapped fallback**: Any unrecognized failure maps to `REQUEST_REJECTED` with the raw detail preserved in `context`

---

## 3. Endpoint Normalization Scope

### 3.1 Trade-affecting endpoints (full normalization in Phase 1)

| Endpoint                   | Method      | Current shapes                    | Phase 1 output     |
| -------------------------- | ----------- | --------------------------------- | ------------------ |
| `/execute`                 | POST        | `TradeResponse` + `HTTPException` | Canonical envelope |
| `/close-position`          | POST        | `TradeResponse` + `HTTPException` | Canonical envelope |
| `/pending-order`           | POST        | `TradeResponse` + `HTTPException` | Canonical envelope |
| `/order-check`             | POST        | `TradeResponse` + `HTTPException` | Canonical envelope |
| `/orders/{ticket}`         | PUT, DELETE | `HTTPException`                   | Canonical envelope |
| `/positions/{ticket}/sltp` | PUT         | `HTTPException`                   | Canonical envelope |

### 3.2 Non-trade endpoints (normalization deferred)

Health, diagnostics, market data, account, and terminal endpoints retain their current shapes. These are read-only and do not present the same user-confusion risks.

---

## 4. Backward Compatibility Contract

### 4.1 Legacy `detail` field

- The `detail` field MUST be populated alongside the canonical envelope in every response
- For `HTTPException`-originated errors: `detail` contains the same string as pre-Phase-1
- For `RequestValidationError`: `detail` contains the Pydantic error array
- For `TradeResponse`-originated errors: `detail` contains the `error` string

### 4.2 Legacy `TradeResponse` for success

- Success responses from `/execute` and `/close-position` continue to return `TradeResponse` fields (`success`, `filled_price`, `filled_quantity`, `ticket_id`) alongside the canonical envelope
- The `data` field in the envelope wraps the trade-specific fields

### 4.3 Migration window

- Legacy support continues until Phase 6 (Dashboard Operator Experience) is deployed
- No API consumer breaks during Phases 1–5

---

## 5. Structured Logging Contract

Every operation event MUST produce a structured log entry containing:

| Field         | Source                         | Searchable                |
| ------------- | ------------------------------ | ------------------------- |
| `tracking_id` | MessageEnvelope                | yes — grep by exact value |
| `code`        | MessageEnvelope                | yes — grep by exact value |
| `category`    | MessageEnvelope                | yes                       |
| `severity`    | MessageEnvelope                | yes                       |
| `endpoint`    | Request path                   | yes                       |
| `timestamp`   | UTC ISO-8601                   | yes                       |
| `detail`      | Raw error text (for debugging) | yes                       |
