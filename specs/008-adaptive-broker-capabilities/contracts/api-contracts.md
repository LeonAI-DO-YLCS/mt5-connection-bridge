# API Contracts: Adaptive Broker Capabilities

**Feature**: 008-adaptive-broker-capabilities
**Date**: 2026-03-02

---

## New Endpoints

### `GET /broker-capabilities`

Returns the complete broker symbol catalog, category tree, and account/terminal trade authorization flags. Response is served from a TTL-cached in-memory store.

**Authentication**: Required (existing API key mechanism)

**Request**: No body, no query parameters.

**Response `200 OK`**:

```json
{
  "account_trade_allowed": true,
  "terminal_trade_allowed": true,
  "symbol_count": 348,
  "fetched_at": "2026-03-02T23:30:00Z",
  "categories": {
    "Forex": ["Majors", "Minors", "Exotics"],
    "Volatility Indices": ["Continuous Indices", "Daily Reset Indices"],
    "Crypto": ["Bitcoin", "Ethereum"],
    "Other": [""]
  },
  "symbols": [
    {
      "name": "EURUSD",
      "description": "Euro vs US Dollar",
      "path": "Forex\\Majors\\EURUSD",
      "category": "Forex",
      "subcategory": "Majors",
      "trade_mode": 4,
      "trade_mode_label": "Full",
      "filling_mode": 3,
      "supported_filling_modes": ["FOK", "IOC"],
      "digits": 5,
      "volume_min": 0.01,
      "volume_max": 500.0,
      "volume_step": 0.01,
      "spread": 12,
      "visible": true,
      "is_configured": true
    }
  ]
}
```

**Response `503 Service Unavailable`**: MT5 terminal not connected.

**Response `500 Internal Server Error`**: MT5 call failed.

**Caching behaviour**:

- Cache TTL: `CAPABILITIES_CACHE_TTL_SECONDS` (default 60)
- Cache is refreshed lazily on first request after TTL expires
- A `fetched_at` field in the response shows cache age

---

### `POST /broker-capabilities/refresh`

Manually invalidates the capabilities cache and immediately re-fetches from MT5.

**Authentication**: Required

**Request**: No body.

**Response `200 OK`**:

```json
{
  "message": "Capabilities cache refreshed",
  "symbol_count": 348,
  "fetched_at": "2026-03-02T23:31:00Z"
}
```

**Response `503 Service Unavailable`**: MT5 terminal not connected — cache NOT cleared.

---

## Modified Endpoints

### `POST /execute` — Extended

**Change**: New optional field `mt5_symbol_direct` in request body. When provided, bypasses the YAML `symbol_map` lookup and uses the MT5 symbol name directly. `ticker` field is still required for audit logging.

**New request body field**:

```json
{
  "ticker": "EURUSD",
  "action": "buy",
  "quantity": 0.1,
  "current_price": 1.0865,
  "mt5_symbol_direct": "EURUSD"
}
```

**New error responses**:

`422 Unprocessable Entity` — Trade mode violation:

```json
{
  "detail": "Symbol EURUSD only allows long (buy) trades. Sell orders are not permitted."
}
```

`422 Unprocessable Entity` — Close-only mode:

```json
{
  "detail": "Symbol GBPUSD is in close-only mode. No new positions allowed."
}
```

`422 Unprocessable Entity` — Symbol disabled:

```json
{
  "detail": "Symbol XAUUSD trading is currently disabled by the broker."
}
```

**Unchanged**: All existing error codes (symbol not found in YAML without `mt5_symbol_direct`, position size validation, queue overload, etc.) remain as-is.

---

### `POST /pending-order` — Extended

**Change**: New optional field `mt5_symbol_direct` (same semantics as `/execute`). Trade mode validation applied before building the pending order request.

**New error responses** (same HTTP/body structure as `/execute` above):

- Trade mode violation for `buy_limit`, `buy_stop` vs `sell_limit`, `sell_stop`

---

### `GET /broker-symbols` — Extended Fields

Existing endpoint extended with new fields. All previous fields preserved. No breaking changes.

**New fields added to each symbol in response**:

```json
{
  "category": "Forex",
  "subcategory": "Majors",
  "filling_mode": 3,
  "supported_filling_modes": ["FOK", "IOC"],
  "volume_step": 0.01,
  "visible": true
}
```

**Note**: `trade_mode` was already present. The `trade_mode_label` human-readable string is also added.

---

## Unchanged Endpoints

These endpoints are **not modified** by this feature:

| Endpoint                   | Reason                                                            |
| -------------------------- | ----------------------------------------------------------------- |
| `GET /symbols`             | YAML-based strategy alias layer; intentionally static             |
| `POST /close-position`     | Only receives filling mode fix internally; no API contract change |
| `GET /positions`           | Read-only, no changes                                             |
| `GET /orders`              | Read-only, no changes                                             |
| `GET /account`             | Read-only, no changes                                             |
| `GET /terminal`            | Read-only, no changes                                             |
| `GET /diagnostics/symbols` | Read-only diagnostic; unchanged                                   |
| `GET /tick/{ticker}`       | Price feed; unchanged                                             |
| `GET /health`              | Health check; unchanged                                           |

---

## Dashboard API Consumption Map

| Dashboard Tab   | Currently calls                       | Will call (after feature)                                      |
| --------------- | ------------------------------------- | -------------------------------------------------------------- |
| Execute         | `GET /symbols`, `GET /broker-symbols` | `GET /broker-capabilities`                                     |
| Symbols Browser | `GET /broker-symbols`                 | `GET /broker-capabilities`                                     |
| Prices          | `GET /symbols`                        | `GET /broker-capabilities`                                     |
| Status          | `GET /terminal`                       | `GET /terminal` + `GET /broker-capabilities` (for trade flags) |
| Others          | unchanged                             | unchanged                                                      |
