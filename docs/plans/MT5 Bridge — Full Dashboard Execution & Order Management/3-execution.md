# Phase 3: Execution — Full Order Panel & Pre-Validation

**Goal**: Enable full order placement (market + pending) and add pre-execution validation to ensure margin sufficiency and trade feasibility.

---

## 1. Backend Endpoints (Execution)

### 1.1 `POST /pending-order` — Place a Pending Order

- **Model**: `ticker`, `type` (buy_limit, sell_limit, buy_stop, sell_stop), `volume`, `price`, `sl`, `tp`, `comment`.
- **Implementation**: Map type to MT5 constants → build `TRADE_ACTION_PENDING` request → submit via worker.

### 1.2 `POST /order-check` — Pre-Validate an Order

- **Purpose**: Call `mt5.order_check()` before submission to verify margin and validity without executing.
- **Model**: Reuses execution parameters.
- **Response**: `valid` (bool), `margin`, `profit`, `equity`, `comment`, `retcode`.

---

## 2. Dashboard: Rebuilt Execute Tab

### 2.1 Rebuilt UI Components

- **Order Type Selector**: Radio group for Market, Buy Limit, Sell Limit, Buy Stop, Sell Stop.
- **Dynamic Fields**: "Trigger Price" field only shown for pending orders.
- **Automated Price Fetching**: Call `GET /tick/{ticker}` when ticker changes to populate bid/ask.
- **Lots Stepper**: Constrained by brokerage `volume_min`, `volume_max`, `volume_step`.

### 2.2 Pre-Validation Panel

- Debounced (500ms) call to `POST /order-check` as the user fills out the form.
- Live display of:
  - ✅/❌ Validity status.
  - Required Margin (e.g., "$12.40").
  - Estimated Profit (if TP price is set).
  - Post-trade equity projection.

---

## 3. Worker Implementation (Mappers)

### 3.1 Pending Order Mapper

```python
# app/mappers/trade_mapper.py
def build_pending_order_request(req, mt5_symbol, symbol_info):
    return {
        "action": TRADE_ACTION_PENDING,
        "symbol": mt5_symbol,
        "volume": normalize_lot_size(req.volume, symbol_info),
        "type": PENDING_ORDER_TYPE_MAP[req.type],
        "price": float(req.price),
        "sl": float(req.sl) if req.sl else 0.0,
        "tp": float(req.tp) if req.tp else 0.0,
        "deviation": 20,
        "magic": 88001,
        "comment": req.comment,
        "type_time": ORDER_TIME_GTC,
        "type_filling": ORDER_FILLING_IOC,
    }
```

---

## 4. Deliverable

Complete order placement functionality (market + pending) with live pre-validation showing required margin and feasibility.
