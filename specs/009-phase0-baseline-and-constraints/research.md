# Research: Phase 0 — Baseline and Constraints

**Branch**: `009-phase0-baseline-and-constraints`
**Date**: 2026-03-03
**Purpose**: Resolve all technical unknowns and ground every Phase 0 deliverable in verified codebase evidence.

---

## 1. Existing Endpoint Families (codebase snapshot 2026-03-03)

Verified by inspecting `app/main.py` router registrations and `app/routes/` directory contents.

### 1.1 Health and Diagnostics

| Endpoint               | Method | Module                  | Purpose                                 |
| ---------------------- | ------ | ----------------------- | --------------------------------------- |
| `/health`              | GET    | `routes/health.py`      | Liveness/readiness check                |
| `/worker/state`        | GET    | `routes/worker.py`      | Current MT5 worker state enum           |
| `/metrics`             | GET    | `routes/metrics.py`     | Rolling request metrics                 |
| `/diagnostics/runtime` | GET    | `routes/diagnostics.py` | Runtime context (settings, env, policy) |
| `/diagnostics/symbols` | GET    | `routes/diagnostics.py` | MT5 symbol introspection                |
| `/logs`                | GET    | `routes/logs.py`        | Trade audit logs                        |

### 1.2 Market and Symbol Data

| Endpoint                       | Method | Module                          | Purpose                                     |
| ------------------------------ | ------ | ------------------------------- | ------------------------------------------- |
| `/symbols`                     | GET    | `routes/symbols.py`             | Strategy alias → MT5 symbol map (from YAML) |
| `/broker-symbols`              | GET    | `routes/broker_symbols.py`      | Live broker symbol catalog from MT5         |
| `/broker-capabilities`         | GET    | `routes/broker_capabilities.py` | Full broker capabilities snapshot           |
| `/broker-capabilities/refresh` | POST   | `routes/broker_capabilities.py` | Force re-fetch from MT5                     |
| `/tick/{ticker}`               | GET    | `routes/tick.py`                | Current tick data                           |
| `/prices`                      | POST   | `routes/prices.py`              | Historical price bars                       |

### 1.3 Trade Operations

| Endpoint                   | Method | Module                     | Purpose                            |
| -------------------------- | ------ | -------------------------- | ---------------------------------- |
| `/execute`                 | POST   | `routes/execute.py`        | Market order execution             |
| `/pending-order`           | POST   | `routes/pending_order.py`  | Limit/stop order placement         |
| `/close-position`          | POST   | `routes/close_position.py` | Close open position (by ticket)    |
| `/order-check`             | POST   | `routes/order_check.py`    | MT5 order pre-check (no execution) |
| `/orders`                  | GET    | `routes/orders.py`         | List active orders                 |
| `/orders/{ticket}`         | PUT    | `routes/orders.py`         | Modify active order                |
| `/orders/{ticket}`         | DELETE | `routes/orders.py`         | Cancel active order                |
| `/positions`               | GET    | `routes/positions.py`      | List open positions                |
| `/positions/{ticket}/sltp` | PUT    | `routes/positions.py`      | Modify SL/TP                       |

### 1.4 Account and Terminal

| Endpoint          | Method | Module               | Purpose           |
| ----------------- | ------ | -------------------- | ----------------- |
| `/account`        | GET    | `routes/account.py`  | MT5 account info  |
| `/terminal`       | GET    | `routes/terminal.py` | MT5 terminal info |
| `/history/deals`  | GET    | `routes/history.py`  | Historical deals  |
| `/history/orders` | GET    | `routes/history.py`  | Historical orders |

### 1.5 Configuration

| Endpoint  | Method | Module                  | Purpose                            |
| --------- | ------ | ----------------------- | ---------------------------------- |
| `/config` | GET    | `routes/config_info.py` | Runtime config snapshot (redacted) |

---

## 2. Existing Error Handling Patterns (verified from source)

### 2.1 Backend error shapes

Three distinct forms are currently returned by the bridge:

1. **HTTPException with `detail` string** — used in most routes:

   ```python
   raise HTTPException(status_code=403, detail="Execution disabled by policy")
   ```

2. **HTTPException with `detail` list** — from Pydantic validation:

   ```python
   # Automatic: RequestValidationError → {"detail": [{"loc":..., "msg":...}]}
   ```

3. **TradeResponse with `success=false`** — returned in some routes before raising:
   ```python
   TradeResponse(success=False, error=f"order_send returned None: {mt5.last_error()}")
   ```

### 2.2 X-Error-Code header system (already exists)

Found in `app/main.py._infer_error_code()`:

| HTTP Status | Error Code                  | Condition                                    |
| ----------- | --------------------------- | -------------------------------------------- |
| 401         | `UNAUTHORIZED_API_KEY`      | Always                                       |
| 403         | `EXECUTION_DISABLED`        | When "execution disabled" in detail text     |
| 404         | `SYMBOL_NOT_CONFIGURED`     | When "ticker" in detail text                 |
| 404         | `RESOURCE_NOT_FOUND`        | When "not found" in detail text              |
| 409         | `OVERLOAD_OR_SINGLE_FLIGHT` | Always                                       |
| 422         | `VALIDATION_ERROR`          | Always                                       |
| 503         | `MT5_DISCONNECTED`          | When "not connected" or "terminal" in detail |
| 503         | `SERVICE_UNAVAILABLE`       | Fallback 503                                 |
| 5xx         | `INTERNAL_SERVER_ERROR`     | Fallback 5xx                                 |
| other       | `REQUEST_ERROR`             | Catch-all                                    |

### 2.3 Dashboard error surfacing

From `dashboard/js/app.js` — the `apiHelper` function currently throws the raw JSON payload as a string when errors occur, which the dashboard catches and passes to `alert()`:

```javascript
// Pattern from app.js apiHelper:
alert(`Error: ${error.message || JSON.stringify(error.detail)}`);
```

---

## 3. Existing Operationaal Scripts Inventory

Verified from `scripts/` directory:

| Script                              | Purpose                                                   | Invocation                             |
| ----------------------------------- | --------------------------------------------------------- | -------------------------------------- |
| `start_bridge.sh`                   | Start the bridge process                                  | `./scripts/start_bridge.sh`            |
| `stop_bridge.sh`                    | Kill bridge/listeners on configured port                  | `./scripts/stop_bridge.sh`             |
| `restart_bridge.sh`                 | Stop then start                                           | `./scripts/restart_bridge.sh`          |
| `smoke_bridge.sh`                   | Probe health endpoint for readiness verification          | `./scripts/smoke_bridge.sh`            |
| `launch_bridge_dashboard.sh`        | Full-featured launcher with TUI, log bundle, auto-restart | `./scripts/launch_bridge_dashboard.sh` |
| `launch_bridge_windows.sh`          | Thin WSL→PowerShell wrapper                               | `./scripts/launch_bridge_windows.sh`   |
| `windows/launch_bridge_windows.ps1` | Windows-native bridge launcher (called from WSL)          | via `launch_bridge_windows.sh`         |
| `test-fast.sh`                      | Fast test subset                                          | `./scripts/test-fast.sh`               |
| `test-full.sh`                      | Full test suite                                           | `./scripts/test-full.sh`               |

### 3.1 Launcher behavior profile (from `launch_bridge_dashboard.sh` source)

- **Single auto-restart**: On unexpected exit, attempts exactly 1 restart. If both fail → exits non-success.
- **Log bundle**: `logs/bridge/launcher/<run-id>/` containing `launcher.log`, `bridge.stdout.log`, `bridge.stderr.log`, `session.json`.
- **Session metadata**: JSON capturing `run_id`, timestamps, host/port, exit code, termination reason, restart info, retention policy.
- **TUI control panel**: Alternate-screen dashboard with process PIDs, endpoint probe status, and diagnostics.
- **Preflight port cleanup**: Stops existing listeners on target port before launch.
- **Run ID generation**: `YYYYMMDD-HHMMSS-$$` format.

---

## 4. Worker State Machine (from `app/mt5_worker.py`)

Existing states (enum):

- `DISCONNECTED` → `CONNECTING` → `CONNECTED` → `AUTHORIZED` → `PROCESSING` → (back to `AUTHORIZED`)
- Error recovery: `AUTHORIZED`/`PROCESSING` → `ERROR` → `RECONNECTING` → `AUTHORIZED` (or `DISCONNECTED` after 5 retries)

Key constants:

- `MAX_RECONNECT_RETRIES = 5`
- `RECONNECT_BASE_DELAY = 1.0s`
- `MAX_RECONNECT_DELAY = 30.0s` (exponential backoff)

---

## 5. Existing Model Constraints (from `app/models/`)

Pydantic models enforce:

- **Trade execution**: `quantity > 0`, `current_price > 0`, valid `action` (buy/sell), optional SL/TP
- **Close position**: `ticket` required, optional `volume` for partial close
- **Pending order**: `quantity > 0`, `current_price > 0`, `limit_price`, optional `comment`, optional SL/TP
- **Modify order**: `ticket`, optional `price`, `quantity`, `sl`, `tp`
- **Modify SL/TP**: `ticket`, optional `sl`, `tp`

---

## 6. Research Decisions for Phase 0 Deliverables

### 6.1 Tracking ID format

- **Decision**: `brg-<ISO8601-compact>-<random-hex>`
  - Example: `brg-20260303T094500-a3f7`
  - Prefix `brg-` distinguishes bridge events from any other system event.
  - ISO8601 compact timestamp gives approximate time context.
  - 4-character random hex (65,536 values) ensures uniqueness within a second.
  - Scoped per bridge runtime session (not globally unique across restarts).
- **Rationale**: Must be human-readable in screenshots, copyable, and searchable in structured logs. UUIDv4 is too long for screenshot usability. Timestamp-prefixed format allows time-based log correlation.
- **Alternatives considered**: UUIDv4 (too long, 36 chars), sequential counters (not unique after restart), pure random (no time context).

### 6.2 Error-code namespace conventions

- **Decision**: `<DOMAIN>_<SPECIFIC_CONDITION>` with uppercase underscored names.
  - Domains: `VALIDATION_`, `MT5_`, `EXECUTION_`, `WORKER_`, `SYMBOL_`, `REQUEST_`, `INTERNAL_`
  - This aligns with the 10 codes already in `_infer_error_code()`.
- **Rationale**: The existing `X-Error-Code` header system already uses this pattern. Aligning the canonical namespace with the existing implementation minimizes migration churn.
- **Alternatives considered**: Numeric codes (not human-readable), dot-separated namespaces (inconsistent with existing pattern).

### 6.3 Severity scale criteria

- **Decision**: Four levels with clear criteria:
  - `critical`: System unavailable or operation unsafe. Requires immediate attention.
  - `high`: Operation blocked, operator intervention needed. Cannot proceed without corrective action.
  - `medium`: Operation blocked but user-correctable. Input change resolves issue.
  - `low`: Non-blocking advisory or informational notice. No action required to proceed.
- **Rationale**: Maps to observed failure classes — MT5 disconnected (critical), execution disabled (high), invalid volume (medium), stale tick warning (low).
- **Alternatives considered**: 5-level (adds confusion), 3-level (insufficient granularity for readiness panel in Phase 2).

### 6.4 Compatibility window policy

- **Decision**: Legacy `detail`-shaped responses remain available during Phases 1–5. They are removed only after Phase 6 (Dashboard Operator Experience) is deployed and validated.
- **Rationale**: The dashboard `apiHelper` currently reads `response.detail`, and no other external consumers are known. Phase 6 rewrites the dashboard error rendering. Removing legacy support before Phase 6 would break the only known consumer.
- **Alternatives considered**: Remove immediately (breaks dashboard), keep forever (permanent tech debt).

### 6.5 MT5 Python API capability categories for parity register

- **Decision**: Seven categories based on the MT5 Python library structure:
  1. Connection and session lifecycle (`initialize`, `shutdown`, `login`, `last_error`)
  2. Terminal and account metadata (`terminal_info`, `account_info`, `version`)
  3. Symbol and market data (`symbols_get`, `symbol_info`, `symbol_select`, `market_book_*`)
  4. Order pre-check and calculations (`order_check`, `order_calc_margin`, `order_calc_profit`)
  5. Order submission and management (`order_send`, `positions_get`, `orders_get`)
  6. History and reporting (`history_deals_get`, `history_orders_get`, `copy_rates_*`, `copy_ticks_*`)
  7. Advanced facilities (market book depth, custom indicator data — optional/future)
- **Rationale**: Directly derived from the MT5 Python library's function groups, matching the Phase 7 plan's 7-category model.
- **Alternatives considered**: Fewer categories (loses granularity for tracking), more categories (over-fine for initial gap assessment).

---

## 7. Summary of Unknowns Resolved

| Unknown                             | Resolution                                         | Source                                                     |
| ----------------------------------- | -------------------------------------------------- | ---------------------------------------------------------- |
| What endpoints exist?               | 28 endpoints across 20 route modules               | `app/main.py` router registrations                         |
| What error shapes exist?            | 3 forms: string detail, list detail, TradeResponse | Code inspection across routes                              |
| What error codes exist?             | 10 codes via `_infer_error_code()`                 | `app/main.py`                                              |
| What launcher behaviors are frozen? | 8 scripts, auto-restart policy, log bundle layout  | `scripts/` directory + `launch_bridge_dashboard.sh` source |
| What worker states exist?           | 7 states with defined transitions                  | `app/mt5_worker.py`                                        |
| What model constraints exist?       | Pydantic-enforced fields across 5 model families   | `app/models/` directory                                    |
| What tracking ID format to use?     | `brg-<timestamp>-<hex4>`                           | Research decision (see 6.1)                                |
| What error-code naming to use?      | `DOMAIN_CONDITION` uppercase                       | Existing pattern alignment (see 6.2)                       |
