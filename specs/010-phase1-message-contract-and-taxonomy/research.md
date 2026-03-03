# Research: Phase 1 — Message Contract and Taxonomy

**Branch**: `010-phase1-message-contract-and-taxonomy`
**Date**: 2026-03-03
**Purpose**: Resolve all technical unknowns for the canonical message envelope, error taxonomy, tracking ID integration, and dashboard renderer before entering the design phase.

---

## 1. Current Error Shapes (verified from source 2026-03-03)

Three distinct response shapes exist across the backend today:

### 1.1 HTTPException → `{ "detail": string }`

Used in most routes via `raise HTTPException(status_code=..., detail=...)`:

```python
# app/routes/execute.py
raise HTTPException(status_code=404, detail=f"Unknown ticker: {req.ticker}")
# app/routes/close_position.py
raise HTTPException(status_code=503, detail="MT5 terminal not connected")
```

### 1.2 RequestValidationError → `{ "detail": [{loc, msg, type}] }`

Automatic from Pydantic when request body fails validation:

```python
# app/main.py:128-134
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": exc.errors()},
                        headers={"X-Error-Code": "VALIDATION_ERROR"})
```

### 1.3 TradeResponse → `{ "success": false, "error": string }`

Returned in some routes as the body (not an exception), sometimes before raising:

```python
# app/routes/execute.py
TradeResponse(success=False, error=f"order_send returned None: {mt5.last_error()}")
TradeResponse(success=False, error=f"Order rejected (retcode={result.retcode}): {result.comment}")
```

### 1.4 Summary of inconsistency

| Path                | Shape                                                              | Example raw content shown to user |
| ------------------- | ------------------------------------------------------------------ | --------------------------------- |
| Validation failure  | `{ detail: [{loc,msg,type}] }`                                     | Pydantic field array              |
| Trade mode rejected | `{ detail: "Symbol X only allows long (buy) trades..." }`          | Clean but no tracking ID          |
| Order rejected      | `{ success: false, error: "Order rejected (retcode=10030): ..." }` | Raw retcode + comment             |
| MT5 disconnected    | `{ detail: "MT5 terminal not connected" }`                         | Clean but no tracking ID          |
| Unhandled exception | `{ detail: "Internal server error" }`                              | Clean but no tracking ID          |

---

## 2. Existing X-Error-Code Infrastructure

Found in `app/main.py._infer_error_code()` (lines 98–118):

| HTTP Status | Inferred Code               | Condition                               |
| ----------- | --------------------------- | --------------------------------------- |
| 401         | `UNAUTHORIZED_API_KEY`      | Always                                  |
| 403         | `EXECUTION_DISABLED`        | "execution disabled" in detail          |
| 404         | `SYMBOL_NOT_CONFIGURED`     | "ticker" in detail                      |
| 404         | `RESOURCE_NOT_FOUND`        | "not found" in detail                   |
| 409         | `OVERLOAD_OR_SINGLE_FLIGHT` | Always                                  |
| 422         | `VALIDATION_ERROR`          | Always                                  |
| 503         | `MT5_DISCONNECTED`          | "not connected" or "terminal" in detail |
| 503         | `SERVICE_UNAVAILABLE`       | Fallback 503                            |
| 5xx         | `INTERNAL_SERVER_ERROR`     | Fallback 5xx                            |
| other       | `REQUEST_ERROR`             | Catch-all                               |

**Key finding**: The existing `_infer_error_code()` uses heuristic text matching on `detail`. Phase 1 replaces this with deterministic code assignment at the normalization layer, keeping backward compatibility with the same header name.

---

## 3. Dashboard Error Surfacing (verified from source)

19 `alert()` calls found across 4 dashboard JS files:

| File            | Count | Patterns                                                                 |
| --------------- | ----- | ------------------------------------------------------------------------ |
| `execute-v2.js` | 7     | Client-side validation alerts, success/failure alerts, raw `err.message` |
| `positions.js`  | 7     | `alert(parsed.error)`, raw `err.message`, success messages               |
| `orders.js`     | 4     | Success/failure alerts with `err.message`                                |
| `app.js`        | 1     | Execution policy update failure                                          |

**Critical observation**: The dashboard currently passes **raw backend error text directly into `alert()`** calls. There is no centralized error rendering, no severity-based styling, and no tracking ID display.

---

## 4. Phase 0 Baseline Dependencies (verified available)

Phase 1 depends on these Phase 0 deliverables being finalized:

| Dependency           | Status                           | Source                                                   |
| -------------------- | -------------------------------- | -------------------------------------------------------- |
| Terminology glossary | Defined in Phase 0 data-model.md | Terms: error, warning, status, advice, blocker, recovery |
| Severity scale       | Defined                          | 4 levels: low, medium, high, critical                    |
| Tracking ID format   | Decided                          | `brg-<YYYYMMDDTHHMMSS>-<hex4>` (≤ 30 chars)              |
| Error-code namespace | Decided                          | `<DOMAIN>_<CONDITION>` uppercase, 7 domain prefixes      |
| Compatibility window | Decided                          | Legacy `detail` retained until Phase 6                   |

---

## 5. Research Decisions

### 5.1 Where to place the normalization utility

- **Decision**: New module `app/messaging/` containing `envelope.py` (Pydantic model), `codes.py` (taxonomy enum), `tracking.py` (ID generation), and `normalizer.py` (entry point).
- **Rationale**: Isolates the messaging concern from routes. The normalizer acts as a single function that all exception handlers and route error returns delegate to, ensuring one code path for envelope construction.
- **Alternatives considered**: (a) Inline normalization in each route (duplicates logic), (b) Middleware-only approach (cannot normalize TradeResponse-shaped returns without refactoring every route simultaneously).

### 5.2 How to normalize TradeResponse errors

- **Decision**: Route handlers continue to return `TradeResponse` for success cases (backward-compatible). For failure cases that currently return `TradeResponse(success=False, ...)`, the route raises `MessageEnvelopeException` instead — a custom HTTPException subclass that carries the canonical envelope. The exception handler serializes both the canonical envelope and the legacy `detail` field.
- **Rationale**: This avoids changing the `TradeResponse` model (Phase 0 constraint: "Pydantic business models are not redefined for convenience"). It also avoids breaking the TradeResponse response_model contract for successful responses.
- **Alternatives considered**: (a) Adding envelope fields to TradeResponse (violates Phase 0 invariant), (b) Post-processing middleware (cannot reliably detect which responses need normalization).

### 5.3 How to generate tracking IDs

- **Decision**: `app/messaging/tracking.py` implements `generate_tracking_id() → str` using `datetime.now(UTC).strftime("%Y%m%dT%H%M%S")` + `secrets.token_hex(2)`, prefixed with `brg-`. Called once per normalization event.
- **Rationale**: Follows the Phase 0 tracking ID policy exactly. `secrets.token_hex(2)` produces 4 hex chars (65,536 values per second — more than sufficient for single-bridge throughput).
- **Alternatives considered**: UUID (too long at 36 chars), sequential counter (not unique across restarts).

### 5.4 How to integrate with existing exception handlers

- **Decision**: Modify the three existing exception handlers in `main.py` to call the normalizer:
  1. `unhandled_exception_handler` → wraps with `code=INTERNAL_SERVER_ERROR`, generates tracking ID
  2. `http_exception_handler` → wraps with code from `_infer_error_code()` (existing logic preserved), generates tracking ID
  3. `request_validation_exception_handler` → wraps Pydantic errors into `code=VALIDATION_ERROR`, generates tracking ID, produces human-readable title/message/action from the first validation error
- **Rationale**: Centralizes all envelope construction without duplicating logic across routes. The legacy `detail` field is populated alongside the envelope.
- **Alternatives considered**: FastAPI depends/middleware (too late in the lifecycle, misses validation errors).

### 5.5 Dashboard message renderer approach

- **Decision**: New module `dashboard/js/message-renderer.js` providing `renderMessage(envelope)` that creates a styled toast/banner with title, message, action, tracking ID (with copy button), and collapsible Details section. All 19 `alert()` calls in critical paths are replaced with calls to the renderer.
- **Rationale**: The renderer must be a standalone module that can be imported by `execute-v2.js`, `positions.js`, `orders.js`, and `app.js`. A single function ensures consistent rendering across all paths.
- **Alternatives considered**: (a) In-place styling inside each file (duplicates logic), (b) Custom HTML elements / web components (over-engineered for vanilla JS dashboard).

### 5.6 Error code taxonomy — complete initial set

- **Decision**: 14 canonical codes spanning 5 domains (extending the 10 existing codes):

| Code                               | Domain     | Severity | Retryable | HTTP Status |
| ---------------------------------- | ---------- | -------- | --------- | ----------- |
| `VALIDATION_VOLUME_RANGE`          | VALIDATION | medium   | false     | 422         |
| `VALIDATION_VOLUME_STEP`           | VALIDATION | medium   | false     | 422         |
| `VALIDATION_CURRENT_PRICE_GT_ZERO` | VALIDATION | medium   | false     | 422         |
| `VALIDATION_ERROR`                 | VALIDATION | medium   | false     | 422         |
| `MT5_DISCONNECTED`                 | MT5        | critical | true      | 503         |
| `MT5_RUNTIME_UNAVAILABLE`          | MT5        | critical | true      | 503         |
| `WORKER_RECONNECT_EXHAUSTED`       | WORKER     | critical | false     | 503         |
| `EXECUTION_DISABLED`               | EXECUTION  | high     | false     | 403         |
| `SYMBOL_TRADE_MODE_RESTRICTED`     | SYMBOL     | high     | false     | 422         |
| `SYMBOL_NOT_CONFIGURED`            | SYMBOL     | high     | false     | 404         |
| `FILLING_MODE_UNSUPPORTED`         | SYMBOL     | high     | false     | 422         |
| `REQUEST_REJECTED`                 | REQUEST    | high     | false     | 400         |
| `OVERLOAD_OR_SINGLE_FLIGHT`        | REQUEST    | medium   | true      | 409         |
| `INTERNAL_SERVER_ERROR`            | INTERNAL   | critical | true      | 500         |

- Plus `UNAUTHORIZED_API_KEY` (401), `RESOURCE_NOT_FOUND` (404), `SERVICE_UNAVAILABLE` (503), `REQUEST_ERROR` (catch-all) carried forward.
- **Rationale**: Extends the Phase 1 blueprint's minimum required codes while aligning with all 10 existing `_infer_error_code()` values. New codes (`VALIDATION_VOLUME_RANGE`, `VALIDATION_VOLUME_STEP`, `VALIDATION_CURRENT_PRICE_GT_ZERO`, `MT5_RUNTIME_UNAVAILABLE`, `WORKER_RECONNECT_EXHAUSTED`, `SYMBOL_TRADE_MODE_RESTRICTED`, `FILLING_MODE_UNSUPPORTED`) cover the failure scenarios currently producing raw error strings.

---

## 6. Summary of Unknowns Resolved

| Unknown                              | Resolution                                                          | Source                        |
| ------------------------------------ | ------------------------------------------------------------------- | ----------------------------- |
| Where to normalize?                  | New `app/messaging/` module (envelope, codes, tracking, normalizer) | Research decision 5.1         |
| How to handle TradeResponse errors?  | `MessageEnvelopeException` — custom exception carrying envelope     | Research decision 5.2         |
| How to generate tracking IDs?        | `brg-<timestamp>-<hex4>` via `secrets.token_hex(2)`                 | Phase 0 policy + decision 5.3 |
| How to integrate exception handlers? | Modify 3 existing handlers in `main.py` to call normalizer          | Decision 5.4                  |
| Dashboard renderer approach?         | New `message-renderer.js` module, replace 19 `alert()` calls        | Decision 5.5                  |
| Full error code set?                 | 18 codes across 7 domains (14 initial + 4 existing)                 | Decision 5.6                  |
