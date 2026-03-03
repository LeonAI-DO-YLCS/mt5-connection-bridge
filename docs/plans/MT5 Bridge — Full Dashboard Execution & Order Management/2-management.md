# Phase 2: Management — Controlling Open Risk

**Goal**: Add the ability to manage existing trades from the dashboard. This includes closing positions (full/partial), cancelling pending orders, and modifying SL/TP or order prices.

---

## 1. Backend Endpoints (Actions)

### 1.1 `POST /close-position` — Close an Open Position

- **Request**: `ticket` (int), `volume` (float | None for full close).
- **Implementation**: Fetch position → determine counter-order types → submit counter-deal via worker.
- **Safety**: Inherits slippage protection and execution gates.

### 1.2 `DELETE /orders/{ticket}` — Cancel Pending Order

- **Implementation**: Build `TRADE_ACTION_REMOVE` request with order ticket → submit via worker.

### 1.3 `PUT /positions/{ticket}/sltp` — Modify Position SL/TP

- **Request**: `sl` (float | None), `tp` (float | None).
- **Implementation**: Build `TRADE_ACTION_SLTP` request → submit via worker.

### 1.4 `PUT /orders/{ticket}` — Modify Pending Order

- **Request**: `price` (float | None), `sl` (float | None), `tp` (float | None).
- **Implementation**: Build `TRADE_ACTION_MODIFY` request → submit via worker. Updates price or risk levels.

---

## 2. Dashboard Actions & UI

### 2.1 Positions Tab Actions

- **Close Button**: Triggers confirmation modal: _"Close BUY 0.01 V75? This is irreversible."_
- **Partial Close Dropdown**: Constrained by symbol `volume_step`.
- **Modify SL/TP Inline Form**: Expands to allow numeric entry of new levels.

### 2.2 Orders Tab Actions

- **Cancel Button**: Confirmation modal: _"Cancel BUY LIMIT 0.01 V75 @ 970.00?"_
- **Modify Order Inline Form**: Allows editing trigger price, SL, or TP. Shows old → new comparison.

---

## 3. Safety & Constraints

### Execution Safety

- All actions gated by `execution_enabled` ENV policy.
- Single-flight concurrency control prevents double-clicking submitting twice.
- API Key authentication required for all calls.

### UI Guardrails

- Confirmation modals for all destructive operations.
- "Cancel All" and "Close All" buttons require an extra checkbox confirmation.

---

## 4. Deliverable

Full position & order lifecycle control — close, partial close, modify SL/TP, modify pending orders, and cancel orders from the dashboard.
