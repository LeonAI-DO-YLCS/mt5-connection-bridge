# API Contracts: MT5 Bridge Full Dashboard

**Branch**: `006-mt5-bridge-dashboard` | **Date**: 2026-03-02

> These contracts define the REST API surface added by this feature. All endpoints require `X-API-KEY` header authentication (existing middleware). Write endpoints additionally require `EXECUTION_ENABLED=true`.

---

## Phase 1: Read-Only Endpoints

### `GET /account`

**Purpose**: Retrieve current account financial state.

**Response** `200`:

```json
{
  "login": 12345678,
  "server": "Deriv-Demo",
  "balance": 10000.0,
  "equity": 10250.5,
  "margin": 120.0,
  "free_margin": 10130.5,
  "profit": 250.5,
  "currency": "USD",
  "leverage": 500
}
```

**Errors**: `503` if MT5 terminal not connected.

---

### `GET /positions`

**Purpose**: List all open positions.

**Response** `200`:

```json
{
  "positions": [
    {
      "ticket": 1234567,
      "symbol": "V75",
      "type": "buy",
      "volume": 0.01,
      "price_open": 950.0,
      "price_current": 955.0,
      "sl": 940.0,
      "tp": 970.0,
      "profit": 5.0,
      "swap": -0.12,
      "time": "2026-03-02T10:30:00Z",
      "magic": 88001,
      "comment": "ai-hedge-fund mt5 bridge"
    }
  ],
  "count": 1
}
```

---

### `GET /orders`

**Purpose**: List all active pending orders.

**Response** `200`:

```json
{
  "orders": [
    {
      "ticket": 7654321,
      "symbol": "V75",
      "type": "buy_limit",
      "volume": 0.01,
      "price": 940.0,
      "sl": 930.0,
      "tp": 960.0,
      "time_setup": "2026-03-02T09:00:00Z",
      "magic": 88001
    }
  ],
  "count": 1
}
```

---

### `GET /tick/{ticker}`

**Purpose**: Get current bid/ask for a symbol.

**Response** `200`:

```json
{
  "ticker": "V75",
  "bid": 954.8,
  "ask": 955.2,
  "spread": 0.4,
  "time": "2026-03-02T12:00:00Z"
}
```

**Errors**: `404` if ticker not in symbol map.

---

### `GET /terminal`

**Purpose**: Get MT5 terminal diagnostics.

**Response** `200`:

```json
{
  "build": 4410,
  "name": "MetaTrader 5",
  "path": "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
  "data_path": "C:\\Users\\User\\AppData\\Roaming\\MetaQuotes\\Terminal\\ABC123",
  "connected": true,
  "trade_allowed": true
}
```

---

## Phase 2: Management Endpoints

### `POST /close-position`

**Purpose**: Close an open position (full or partial).

**Request**:

```json
{
  "ticket": 1234567,
  "volume": 0.005
}
```

`volume` is optional — `null` or omitted means full close.

**Response** `200`:

```json
{
  "success": true,
  "filled_price": 955.1,
  "filled_quantity": 0.005,
  "ticket_id": 1234568,
  "error": null
}
```

**Errors**: `404` position not found, `422` invalid volume, `503` terminal not connected.

---

### `DELETE /orders/{ticket}`

**Purpose**: Cancel a pending order.

**Response** `200`:

```json
{
  "success": true,
  "ticket_id": 7654321,
  "error": null
}
```

**Errors**: `404` order not found, `503` terminal not connected.

---

### `PUT /positions/{ticket}/sltp`

**Purpose**: Modify stop-loss and/or take-profit on an open position.

**Request**:

```json
{
  "sl": 935.0,
  "tp": 975.0
}
```

**Response** `200`:

```json
{
  "success": true,
  "ticket_id": 1234567,
  "error": null
}
```

---

### `PUT /orders/{ticket}`

**Purpose**: Modify a pending order's trigger price, SL, or TP.

**Request**:

```json
{
  "price": 938.0,
  "sl": 928.0,
  "tp": 958.0
}
```

**Response** `200`:

```json
{
  "success": true,
  "ticket_id": 7654321,
  "error": null
}
```

---

## Phase 3: Execution Endpoints

### `POST /pending-order`

**Purpose**: Place a new pending order.

**Request**:

```json
{
  "ticker": "V75",
  "type": "buy_limit",
  "volume": 0.01,
  "price": 940.0,
  "sl": 930.0,
  "tp": 960.0,
  "comment": "limit order via dashboard"
}
```

**Response** `200`:

```json
{
  "success": true,
  "filled_price": null,
  "filled_quantity": null,
  "ticket_id": 8888888,
  "error": null
}
```

**Errors**: `404` unknown ticker, `422` invalid order type or volume, `503` terminal not connected.

---

### `POST /order-check`

**Purpose**: Pre-validate an order without executing.

**Request**: Same structure as `POST /pending-order`.

**Response** `200`:

```json
{
  "valid": true,
  "margin": 12.4,
  "profit": 0.0,
  "equity": 10238.1,
  "comment": "Done",
  "retcode": 0
}
```

---

## Phase 4: History & Discovery Endpoints

### `GET /history/deals`

**Purpose**: Retrieve historical deals (fills).

**Query Parameters**: `date_from` (ISO 8601), `date_to` (ISO 8601), `symbol` (optional), `position` (optional int).

**Response** `200`:

```json
{
  "deals": [
    {
      "ticket": 111222,
      "order_ticket": 333444,
      "position_id": 555666,
      "symbol": "V75",
      "type": "buy",
      "entry": "in",
      "volume": 0.01,
      "price": 950.0,
      "profit": 0.0,
      "swap": 0.0,
      "commission": -0.1,
      "fee": 0.0,
      "time": "2026-03-01T14:30:00Z",
      "magic": 88001
    }
  ],
  "count": 1,
  "net_profit": 5.5,
  "total_swap": -0.24,
  "total_commission": -0.2
}
```

---

### `GET /history/orders`

**Purpose**: Retrieve historical orders.

**Query Parameters**: `date_from` (ISO 8601), `date_to` (ISO 8601).

**Response** `200`:

```json
{
  "orders": [
    {
      "ticket": 333444,
      "symbol": "V75",
      "type": "buy",
      "volume": 0.01,
      "price": 950.0,
      "sl": 940.0,
      "tp": 970.0,
      "state": "filled",
      "time_setup": "2026-03-01T14:29:00Z",
      "time_done": "2026-03-01T14:30:00Z",
      "magic": 88001
    }
  ],
  "count": 1
}
```

---

### `GET /broker-symbols`

**Purpose**: Discover all symbols from broker.

**Query Parameters**: `group` (optional, e.g., `"Forex*"`).

**Response** `200`:

```json
{
  "symbols": [
    {
      "name": "EURUSD",
      "description": "Euro vs US Dollar",
      "path": "Forex\\EURUSD",
      "spread": 12,
      "digits": 5,
      "volume_min": 0.01,
      "volume_max": 100.0,
      "trade_mode": "Full",
      "is_configured": false
    }
  ],
  "count": 1
}
```
