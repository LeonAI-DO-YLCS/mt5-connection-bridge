# Phase 1: Visibility — Read-Only Account & Market Exposure

**Goal**: Add read-only visibility to the dashboard — see what's happening on the account (positions, pending orders, balance, terminal status) and fetch interactive prices.

---

## 1. Backend Endpoints (Read-Only)

### 1.1 `GET /account` — Account Info

- **Model**: `login`, `server`, `balance`, `equity`, `margin`, `free_margin`, `profit`, `currency`, `leverage`.
- **Implementation**: Submit `mt5.account_info()` via worker queue.

### 1.2 `GET /positions` — List Open Positions

- **Model**: `ticket`, `symbol`, `type` (buy/sell), `volume`, `price_open`, `price_current`, `sl`, `tp`, `profit`, `swap`, `time`, `magic`, `comment`.
- **Implementation**: Submit `mt5.positions_get()` via worker queue.

### 1.3 `GET /orders` — List Pending Orders

- **Model**: `ticket`, `symbol`, `type` (limit/stop), `volume`, `price`, `sl`, `tp`, `time_setup`, `magic`.
- **Implementation**: Submit `mt5.orders_get()` via worker.

### 1.4 `GET /tick/{ticker}` — Get Current Tick Price

- **Model**: `ticker`, `bid`, `ask`, `spread`, `time`.
- **Implementation**: Submit `mt5.symbol_info_tick(mt5_symbol)` via worker. Used for auto-filling prices in Execute tab.

### 1.5 `GET /terminal` — Terminal Info

- **Model**: `build`, `name`, `path`, `data_path`, `connected`, `trade_allowed`.
- **Implementation**: Submit `mt5.terminal_info()` via worker. Useful for diagnostics.

---

## 2. Dashboard Enhancements (Read-Only)

### 2.1 Positions Tab (Initial View)

- Displays open positions as cards.
- Show balance, equity, margin, and total unrealized P&L in a top summary bar.
- Auto-refresh every 5 seconds.

### 2.2 Orders Tab (Initial View)

- Displays active pending orders as cards.
- Auto-refresh every 10 seconds.

### 2.3 Status Tab Enhancements

- Add Account Summary panel using `GET /account`.
- Add Terminal Diagnostics panel using `GET /terminal`.

### 2.4 Prices Tab Enhancements

- Replace hardcoded query with interactive ticker dropdown.
- Auto-populate dropdown from `GET /symbols`.

---

## 3. Auto-Refresh Strategy

- **Status/Positions**: 5s intervals.
- **Orders**: 10s intervals.
- **Prices**: Manual fetch only.

---

## 4. Deliverable

A dashboard that shows all positions, pending orders, account balance, terminal info, and has interactive price fetching.
