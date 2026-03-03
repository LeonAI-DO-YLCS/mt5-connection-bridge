# Endpoint and Script Snapshot — MT5 Connection Bridge

> **Snapshot Date**: 2026-03-03
> **Bridge Version**: 1.2.0
> **Branch at Snapshot**: `main` (commit `468b075`)
> **Re-snapshot Instructions**: Re-run this inventory whenever the bridge adds, removes, or renames an endpoint or script. Update the snapshot date and bridge version accordingly.

---

## 1. Health and Diagnostics

| Endpoint               | Method | Module                  | Purpose                                                         | Response Shape (key fields)                                  | Auth Required |
| ---------------------- | ------ | ----------------------- | --------------------------------------------------------------- | ------------------------------------------------------------ | ------------- |
| `/health`              | GET    | `routes/health.py`      | Liveness/readiness check                                        | `{ "status", "worker_state", "uptime_seconds", "version" }`  | Yes (API key) |
| `/worker/state`        | GET    | `routes/worker.py`      | Current MT5 worker state enum                                   | `{ "state": "<WorkerState>" }`                               | Yes           |
| `/metrics`             | GET    | `routes/metrics.py`     | Rolling request metrics (per-endpoint counts, error rates)      | `{ "total_requests", "endpoints": {...}, "retention_days" }` | Yes           |
| `/diagnostics/runtime` | GET    | `routes/diagnostics.py` | Runtime context: settings, environment, execution policy source | `{ "settings": {...}, "policy_source", "uptime_seconds" }`   | Yes           |
| `/diagnostics/symbols` | GET    | `routes/diagnostics.py` | MT5 symbol introspection: symbol_info for a given ticker        | `{ "symbol", "info": {...} }`                                | Yes           |
| `/logs`                | GET    | `routes/logs.py`        | Trade audit log retrieval (paginated JSONL reader)              | `{ "total", "offset", "limit", "entries": [...] }`           | Yes           |

---

## 2. Market and Symbol Data

| Endpoint                       | Method | Module                          | Purpose                                                                                                                        | Response Shape (key fields)                                                                                                  | Auth Required |
| ------------------------------ | ------ | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- | ------------- |
| `/symbols`                     | GET    | `routes/symbols.py`             | Strategy alias → MT5 symbol map (from `config/symbols.yaml`)                                                                   | `{ "<ticker>": { "mt5_symbol", "lot_size", "category" } }`                                                                   | Yes           |
| `/broker-symbols`              | GET    | `routes/broker_symbols.py`      | Live broker symbol catalog from MT5 `symbols_get()`                                                                            | `{ "count", "symbols": [{ "name", "description", "path", ... }] }`                                                           | Yes           |
| `/broker-capabilities`         | GET    | `routes/broker_capabilities.py` | Full broker capabilities snapshot (symbols with filling modes, trade modes, categories) + account/terminal trade authorization | `{ "account_trade_allowed", "terminal_trade_allowed", "symbol_count", "symbols": [...], "categories": {...}, "fetched_at" }` | Yes           |
| `/broker-capabilities/refresh` | POST   | `routes/broker_capabilities.py` | Force cache clear and re-fetch from MT5                                                                                        | `{ "status": "refreshed", "fetched_at" }`                                                                                    | Yes           |
| `/tick/{ticker}`               | GET    | `routes/tick.py`                | Current tick data for a symbol (bid, ask, last, volume, time)                                                                  | `{ "symbol", "bid", "ask", "last", "volume", "time" }`                                                                       | Yes           |
| `/prices`                      | POST   | `routes/prices.py`              | Historical price bars (OHLCV) for a symbol and timeframe                                                                       | `{ "symbol", "timeframe", "count", "bars": [{ "time", "open", "high", "low", "close", "volume" }] }`                         | Yes           |

---

## 3. Trade Operations

| Endpoint                   | Method | Module                     | Purpose                                            | Response Shape (key fields)                                                                    | Auth Required |
| -------------------------- | ------ | -------------------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------- |
| `/execute`                 | POST   | `routes/execute.py`        | Market order execution (buy/sell)                  | `{ "success", "filled_price", "filled_quantity", "ticket_id", "error" }`                       | Yes           |
| `/pending-order`           | POST   | `routes/pending_order.py`  | Limit/stop order placement                         | `{ "success", "filled_price", "filled_quantity", "ticket_id", "error" }`                       | Yes           |
| `/close-position`          | POST   | `routes/close_position.py` | Close an open position by ticket (full or partial) | `{ "success", "filled_price", "filled_quantity", "ticket_id", "error" }`                       | Yes           |
| `/order-check`             | POST   | `routes/order_check.py`    | MT5 order pre-check (validates without executing)  | `{ "retcode", "balance", "equity", "profit", "margin", "margin_free", "comment" }`             | Yes           |
| `/orders`                  | GET    | `routes/orders.py`         | List all active pending orders                     | `{ "count", "orders": [{ "ticket", "symbol", "type", "volume", "price", ... }] }`              | Yes           |
| `/orders/{ticket}`         | PUT    | `routes/orders.py`         | Modify an active order (price, volume, SL, TP)     | `{ "success", "error" }`                                                                       | Yes           |
| `/orders/{ticket}`         | DELETE | `routes/orders.py`         | Cancel (delete) an active pending order            | `{ "success", "error" }`                                                                       | Yes           |
| `/positions`               | GET    | `routes/positions.py`      | List all open positions                            | `{ "count", "positions": [{ "ticket", "symbol", "type", "volume", "price", "profit", ... }] }` | Yes           |
| `/positions/{ticket}/sltp` | PUT    | `routes/positions.py`      | Modify stop loss / take profit on an open position | `{ "success", "error" }`                                                                       | Yes           |

---

## 4. Account and Terminal

| Endpoint          | Method | Module               | Purpose                                              | Response Shape (key fields)                                                                                       | Auth Required |
| ----------------- | ------ | -------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------- |
| `/account`        | GET    | `routes/account.py`  | MT5 account info (balance, equity, margin, leverage) | `{ "login", "balance", "equity", "margin", "free_margin", "leverage", "currency", "server", "name" }`             | Yes           |
| `/terminal`       | GET    | `routes/terminal.py` | MT5 terminal info (build, connected, trade allowed)  | `{ "connected", "trade_allowed", "build", "name", "path", "company" }`                                            | Yes           |
| `/history/deals`  | GET    | `routes/history.py`  | Historical deals (closed trades) within a date range | `{ "count", "deals": [{ "ticket", "order", "time", "type", "price", "volume", "profit", "symbol", "comment" }] }` | Yes           |
| `/history/orders` | GET    | `routes/history.py`  | Historical orders within a date range                | `{ "count", "orders": [{ "ticket", "time_setup", "type", "state", "price", "volume", "symbol" }] }`               | Yes           |

---

## 5. Configuration

| Endpoint  | Method | Module                  | Purpose                                               | Response Shape (key fields)                                                                 | Auth Required |
| --------- | ------ | ----------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------- |
| `/config` | GET    | `routes/config_info.py` | Runtime configuration snapshot (credentials redacted) | `{ "port", "execution_enabled", "log_level", "symbols_count", "policy_source", "version" }` | Yes           |

---

## 6. Dashboard Static Mount

| Path          | Type         | Source                                   | Purpose                                                                        |
| ------------- | ------------ | ---------------------------------------- | ------------------------------------------------------------------------------ |
| `/dashboard/` | Static mount | `dashboard/` directory (HTML + JS + CSS) | Serves the operator dashboard UI; auto-detected at startup if directory exists |

**Dashboard JS modules**: `app.js`, `chart.js`, `components.js`, `execute-v2.js`, `history.js`, `orders.js`, `positions.js`, `symbols-browser.js`

---

## 7. Operational Scripts Inventory

| Script                                      | Purpose                                                                                              | Invocation                             | Phase 5 Relevance                                                                                                 |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `scripts/start_bridge.sh`                   | Start the bridge uvicorn process                                                                     | `./scripts/start_bridge.sh`            | May gain preflight checks                                                                                         |
| `scripts/stop_bridge.sh`                    | Kill bridge process and port listeners                                                               | `./scripts/stop_bridge.sh`             | Core invariant — name/behavior frozen                                                                             |
| `scripts/restart_bridge.sh`                 | Stop then start (sequential)                                                                         | `./scripts/restart_bridge.sh`          | Core invariant — name/behavior frozen                                                                             |
| `scripts/smoke_bridge.sh`                   | Probe `/health` endpoint for readiness verification                                                  | `./scripts/smoke_bridge.sh`            | Core invariant — may gain additional probes                                                                       |
| `scripts/launch_bridge_dashboard.sh`        | Full-featured launcher with TUI control panel, structured log bundles, auto-restart, signal handling | `./scripts/launch_bridge_dashboard.sh` | Primary target — gains preflight diagnostics, but invariants (restart policy, log structure, env vars) are frozen |
| `scripts/launch_bridge_windows.sh`          | Thin WSL→PowerShell wrapper                                                                          | `./scripts/launch_bridge_windows.sh`   | Core invariant — invocation pattern frozen                                                                        |
| `scripts/windows/launch_bridge_windows.ps1` | Windows-native bridge launcher (called via WSL wrapper)                                              | Called by `launch_bridge_windows.sh`   | May gain equivalent diagnostics                                                                                   |
| `scripts/test-fast.sh`                      | Run fast test subset (`pytest -x`)                                                                   | `./scripts/test-fast.sh`               | Name/behavior frozen                                                                                              |
| `scripts/test-full.sh`                      | Run full test suite (`pytest`)                                                                       | `./scripts/test-full.sh`               | Name/behavior frozen                                                                                              |
