# Quickstart: Phase 1 — Message Contract and Taxonomy

**Branch**: `010-phase1-message-contract-and-taxonomy`
**Date**: 2026-03-03
**Purpose**: Concise developer guide for implementing, testing, and verifying Phase 1 artifacts.

---

## 1. What Changes

### Backend (Python)

- **New module**: `app/messaging/` containing:
  - `envelope.py` — `MessageEnvelope` Pydantic model + `MessageEnvelopeException`
  - `codes.py` — `ErrorCode` enum with metadata (title, message, action, severity, retryable, http_status)
  - `tracking.py` — `generate_tracking_id()` function
  - `normalizer.py` — `normalize_error()` and `normalize_success()` factory functions
- **Modified files**:
  - `app/main.py` — Update 3 exception handlers to produce canonical envelopes
  - `app/routes/execute.py` — Replace `TradeResponse(success=False, ...)` returns with `MessageEnvelopeException`
  - `app/routes/close_position.py` — Same pattern
  - `app/routes/pending_order.py` — Same pattern
  - `app/routes/order_check.py` — Same pattern
  - `app/routes/orders.py` — Same pattern
  - `app/routes/positions.py` — Same pattern

### Dashboard (JavaScript)

- **New file**: `dashboard/js/message-renderer.js` — Centralized renderer with severity styling, tracking ID copy, and details toggle
- **New file**: `dashboard/css/messages.css` — Message styling
- **Modified files**:
  - `dashboard/js/execute-v2.js` — Replace `alert()` calls with `renderMessage()`
  - `dashboard/js/positions.js` — Same pattern
  - `dashboard/js/orders.js` — Same pattern
  - `dashboard/js/app.js` — Same pattern
  - `dashboard/index.html` — Add `<script>` and `<link>` tags for new files

---

## 2. Implementation Order

```
Step 1: app/messaging/codes.py          ← ErrorCode enum (no dependencies)
Step 2: app/messaging/tracking.py       ← generate_tracking_id() (no dependencies)
Step 3: app/messaging/envelope.py       ← MessageEnvelope model + exception (depends on 1, 2)
Step 4: app/messaging/normalizer.py     ← normalize_error/success (depends on 1, 2, 3)
Step 5: app/main.py                     ← Wire exception handlers (depends on 4)
Step 6: app/routes/execute.py           ← Replace error returns with exceptions (depends on 3)
Step 7: app/routes/close_position.py    ← Same pattern
Step 8: app/routes/pending_order.py     ← Same pattern
Step 9: app/routes/order_check.py       ← Same pattern
Step 10: app/routes/orders.py           ← Same pattern
Step 11: app/routes/positions.py        ← Same pattern
Step 12: dashboard/js/message-renderer.js + css  ← Renderer (no backend dependency)
Step 13: dashboard/js/execute-v2.js     ← Replace alert() calls (depends on 12)
Step 14: dashboard/js/positions.js      ← Same pattern
Step 15: dashboard/js/orders.js         ← Same pattern
Step 16: dashboard/js/app.js            ← Same pattern
```

---

## 3. Key Patterns

### Creating a canonical error (in a route)

```python
from app.messaging.envelope import MessageEnvelopeException
from app.messaging.codes import ErrorCode

raise MessageEnvelopeException(
    status_code=422,
    code=ErrorCode.SYMBOL_TRADE_MODE_RESTRICTED,
    message=f"Symbol {symbol} only allows long (buy) trades.",
    action="Change to a buy action or select a different symbol.",
    context={"symbol": symbol, "trade_mode": 1},
)
```

### Creating a canonical success (in a route)

```python
from app.messaging.normalizer import normalize_success

envelope = normalize_success(
    title="Trade executed successfully",
    message=f"Buy order for {qty} lots of {symbol} filled at {price}.",
    data={"filled_price": price, "filled_quantity": qty, "ticket_id": ticket},
)
return envelope
```

### Rendering a message (dashboard)

```javascript
import { renderMessage } from './message-renderer.js';

try {
    const res = await fetch('/execute', ...);
    const data = await res.json();
    renderMessage(data, document.getElementById('message-area'));
} catch (err) {
    renderMessage({
        ok: false, category: 'error', code: 'REQUEST_ERROR',
        title: 'Request failed', message: err.message,
        action: 'Check your network connection and try again.',
        severity: 'high', retryable: true, tracking_id: '',
    }, document.getElementById('message-area'));
}
```

---

## 4. Testing

### Run existing tests (should still pass — backward compatibility)

```bash
cd /home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge
.venv/bin/python -m pytest tests/ -v
```

### New tests to add

| Test file                                  | Scope    | What it verifies                                                           |
| ------------------------------------------ | -------- | -------------------------------------------------------------------------- |
| `tests/unit/test_envelope.py`              | Unit     | `MessageEnvelope` serialization, field constraints, `context` sanitization |
| `tests/unit/test_codes.py`                 | Unit     | All `ErrorCode` members have required metadata, no duplicate codes         |
| `tests/unit/test_tracking.py`              | Unit     | `generate_tracking_id()` format, uniqueness within a second, ≤ 30 chars    |
| `tests/unit/test_normalizer.py`            | Unit     | `normalize_error()` and `normalize_success()` produce valid envelopes      |
| `tests/contract/test_envelope_contract.py` | Contract | All trade-affecting endpoints return canonical envelope fields             |
| `tests/contract/test_backward_compat.py`   | Contract | All error responses contain legacy `detail` field                          |

### Run new tests

```bash
.venv/bin/python -m pytest tests/unit/test_envelope.py tests/unit/test_codes.py tests/unit/test_tracking.py tests/unit/test_normalizer.py -v
.venv/bin/python -m pytest tests/contract/test_envelope_contract.py tests/contract/test_backward_compat.py -v
```

---

## 5. Verification Checklist

- [ ] All trade-affecting endpoints return `ok`, `category`, `code`, `tracking_id`, `title`, `message`, `action`, `severity`, `retryable`, `context`
- [ ] All error responses also contain `detail` (legacy compatibility)
- [ ] `X-Error-Code` header maps to canonical `code`
- [ ] `X-Tracking-ID` header populated on every response
- [ ] Structured logs contain `tracking_id` and `code` as searchable fields
- [ ] Dashboard shows human-readable title/message/action — no raw JSON or MT5 tuples
- [ ] Dashboard displays `tracking_id` with copy button on failures
- [ ] Dashboard shows collapsible Details section for `context`
- [ ] No `alert()` calls remain in critical operation paths
- [ ] Existing API consumers (reading `detail`) still work
