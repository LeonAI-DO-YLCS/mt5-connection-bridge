# MT5 Connection Bridge — Verification UI & Testing Blueprint

> **Status**: Exploration artifact — no code execution  
> **Scope**: Additive only — zero changes to existing endpoints, models, or main project integration  
> **Goal**: A self-contained dashboard UI for verifying bridge connectivity, data fetching, and trade execution + a comprehensive test suite covering all bridge components  
> **Date**: 2026-03-02

---

## Table of Contents

1. [Current Architecture Summary](#1-current-architecture-summary)
2. [Gap Analysis](#2-gap-analysis)
3. [Architecture Decisions](#3-architecture-decisions)
4. [Resolved Design Decisions](#4-resolved-design-decisions)
5. [New API Endpoints](#5-new-api-endpoints-backend)
6. [Dashboard UI Specification](#6-dashboard-ui-specification)
7. [Testing Strategy](#7-testing-strategy)
8. [File-by-File Implementation Plan](#8-file-by-file-implementation-plan)
9. [Phased Delivery Plan](#9-phased-delivery-plan)
10. [Risk Assessment](#10-risk-assessment)

---

## 1. Current Architecture Summary

### Bridge Structure (`mt5-connection-bridge/`)

```
app/
├── main.py           ← FastAPI app, lifespan (worker start/stop), router mounting
├── config.py         ← Settings (pydantic-settings), symbol YAML loader, timeframe map
├── auth.py           ← X-API-KEY header validation middleware
├── audit.py          ← JSONL trade audit logger (logs/trades.jsonl)
├── mt5_worker.py     ← Single-threaded worker daemon, queue, state machine, reconnect
├── models/
│   ├── price.py      ← Price, PriceResponse (mirrors src/data/models.py)
│   ├── trade.py      ← TradeRequest, TradeResponse
│   └── health.py     ← HealthStatus
├── mappers/
│   ├── price_mapper.py  ← numpy structured array → PriceResponse
│   └── trade_mapper.py  ← action→MT5 order type, lot normalization, order building
└── routes/
    ├── health.py     ← GET /health
    ├── prices.py     ← GET /prices
    └── execute.py    ← POST /execute
```

### Main Project Integration Points

| File                           | Role                                              |
| :----------------------------- | :------------------------------------------------ |
| `src/tools/mt5_client.py`      | `MT5BridgeClient` — HTTP wrapper with retry logic |
| `src/tools/provider_config.py` | `is_mt5_provider()`, `get_instrument_category()`  |
| `src/tools/api.py`             | `get_prices()` — MT5 fallback routing             |

### Current API Surface

| Endpoint   | Method | Auth         | Purpose                                          |
| :--------- | :----- | :----------- | :----------------------------------------------- |
| `/health`  | GET    | ✅ X-API-KEY | Terminal connection status, broker info, latency |
| `/prices`  | GET    | ✅ X-API-KEY | Historical OHLCV candle data                     |
| `/execute` | POST   | ✅ X-API-KEY | Live trade execution                             |
| `/docs`    | GET    | ❌ None      | Auto-generated Swagger UI (FastAPI default)      |

---

## 2. Gap Analysis

### 🔴 Critical Gaps

| Gap                    | Impact                                                                           | Resolution                           |
| :--------------------- | :------------------------------------------------------------------------------- | :----------------------------------- |
| **Zero tests**         | No CI safety net, no regression detection, can't verify mapper logic without MT5 | Full test suite (unit + integration) |
| **No verification UI** | Manual curl/Swagger only, no visual feedback, no at-a-glance status              | Dashboard UI served from the bridge  |

### 🟡 Secondary Gaps (addressable alongside UI)

| Gap                         | Impact                                                             | Resolution                             |
| :-------------------------- | :----------------------------------------------------------------- | :------------------------------------- |
| No symbol listing endpoint  | UI can't populate dropdowns, external tools can't discover symbols | New `GET /symbols` endpoint            |
| No audit log viewer         | Must SSH/read files to see trade history                           | New `GET /logs` endpoint               |
| No config introspection     | Can't verify runtime settings without reading .env                 | New `GET /config` endpoint (sanitized) |
| No worker state granularity | `/health` mixes MT5 state with account info                        | New `GET /worker/state` endpoint       |
| No request metrics          | Can't see throughput or error rates                                | Metrics model + endpoint               |

### ✅ What Stays Untouched

- All existing Pydantic models (`Price`, `PriceResponse`, `TradeRequest`, `TradeResponse`, `HealthStatus`)
- All existing route handlers (health, prices, execute)
- Auth middleware logic
- MT5 worker internals
- Main project files (`mt5_client.py`, `provider_config.py`, `api.py`)
- `config/symbols.yaml` format
- `.env` / `.env.example` structure

---

## 3. Architecture Decisions

### Decision 1: UI Hosting Strategy

**Selected: Embedded static files served by FastAPI**

```
mt5-connection-bridge/
└── dashboard/              ← NEW directory
    ├── index.html          ← Single-page dashboard
    ├── css/
    │   └── dashboard.css   ← All styles
    └── js/
        ├── app.js          ← Main app logic (tab routing, API client, state)
        ├── components.js   ← UI component renderers (status card, table, form)
        └── chart.js        ← Optional candlestick chart (lightweight-charts)
```

**Rationale**:

- No build step, no framework dependency, no second process
- FastAPI's `StaticFiles` mount serves the directory at `/dashboard`
- JavaScript `fetch()` calls the bridge's own API — zero CORS issues
- The bridge remains a single deployable unit
- No changes to the existing FastAPI app structure beyond adding a mount

**In `main.py`** (additive only):

```python
from fastapi.staticfiles import StaticFiles
app.mount("/dashboard", StaticFiles(directory="dashboard", html=True), name="dashboard")
```

### Decision 2: UI Authentication

**Selected: Client-side API key input stored in `sessionStorage`**

- On load, the dashboard checks `sessionStorage` for a stored API key
- If absent, renders a key input screen
- Once entered, the key is stored in `sessionStorage` (cleared when tab closes)
- No inactivity timeout is enforced while the tab stays open; session ends when the tab/browser session ends or credentials are invalid
- All `fetch()` calls include `X-API-KEY` header
- **No backend auth changes needed**

### Decision 3: New Endpoints Are Purely Additive

All new endpoints follow the existing pattern:

- Same `APIRouter` pattern
- Same `X-API-KEY` auth (inherited from app-level `dependencies`)
- Same response model approach (Pydantic models)
- Separate route files: `routes/symbols.py`, `routes/logs.py`, `routes/config_info.py`, `routes/worker.py`

### Decision 4: Testing Without MetaTrader5

The `MetaTrader5` package only works on Windows. All tests must:

- **Mock** the `MetaTrader5` module entirely using `unittest.mock.patch` or `pytest-mock`
- Use **fixture-generated numpy arrays** that mimic `mt5.copy_rates_range()` output
- Use **mock objects** with matching attributes for `mt5.account_info()` and `mt5.symbol_info()`
- Run cleanly on Linux/CI without any Windows dependency

---

## 4. Resolved Design Decisions

> All exploratory questions and interview follow-ups have been resolved based on the project's scope as a **universal MT5 bridge** that will serve the current ai-hedge-fund and any future trading tools.

### Decision 5: Candlestick Charting — ✅ YES, Include

**Verdict**: Include a TradingView `lightweight-charts` candlestick chart in the Prices tab.

**Reasoning**:

- **Verification value**: Seeing candle shapes, wicks, and gaps instantly reveals data quality issues (wrong OHLCV mapping, timezone misalignment, missing candles) that a raw table can't catch at a glance. A single out-of-order timestamp or inverted high/low is visible in 1 second on a chart vs. scrolling through hundreds of rows.
- **Universal bridge utility**: Any project connecting to this bridge (not just ai-hedge-fund) will need to visually verify price feeds. A built-in chart eliminates the need for external tools like TradingView or Excel to spot-check data.
- **Cost is minimal**: `lightweight-charts` by TradingView is a single `<script>` tag (~45KB gzipped), no build process, MIT-licensed. It renders professional candlestick charts with zoom/pan built-in. It's purpose-built for exactly this use case.
- **Implementation**: Bundle `lightweight-charts.standalone.production.mjs` locally in `dashboard/js/vendor/` (not CDN) so the bridge works in air-gapped / offline environments. The chart module (`chart.js`) wraps the library with a single `renderCandlestickChart(containerId, priceData)` function.

### Decision 6: Execute Tab Safety — ✅ YES, Multi-Layer Safety

**Verdict**: Implement five layers of trade execution protection, including environment-level execution enablement and multi-trade controls.

**Reasoning**:

- This bridge handles **real money** on live accounts. An accidental click in a verification UI must not cost real funds. Since MT5 has no native "dry-run" mode, we must add every reasonable guardrail at the UI level.
- The bridge is universal — different teams and tools will connect, and we can't assume everyone understands the risk.

**Five safety layers**:

| Layer                        | Mechanism            | Details                                                                                                                                                                                                                                                                                                      |
| :--------------------------- | :------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Execution enablement gate** | Environment policy | Execute tab is locked by default unless environment-level execution enablement is turned on. UI reads this from `GET /config` and blocks submit actions when disabled. |
| **2. Environment badge**     | Persistent banner    | Large, color-coded banner at top of Execute tab: **"LIVE ACCOUNT"** (red, pulsing border) or **"DEMO ACCOUNT"** (green, solid). Derived from `GET /config` → `mt5_server` containing "Demo" (case-insensitive). Always visible, cannot be dismissed.                                                         |
| **3. Confirmation checkbox** | Required interaction | Checkbox: _"I confirm this will execute a REAL trade on [account_id] at [broker]"_. Dynamically populated from `/health` response. Submit button remains disabled (greyed out) until checked. Checkbox resets after each trade submission.                                                                   |
| **4. Confirmation modal**    | Final gate           | After clicking Submit with checkbox checked, a modal appears: _"You are about to [BUY/SELL] [quantity] lots of [ticker]. This is irreversible. Proceed?"_ with **Cancel** (primary/blue, left) and **Confirm Trade** (red, right). The destructive action is intentionally styled as the non-default button. |
| **5. Multi-trade mode control** | Operator toggle + warning | Execute tab includes a toggle for multi-trade mode. Default is OFF. When ON, a risk-management warning is shown and parallel submissions are allowed with no fixed UI cap. When OFF, only one in-flight submission is allowed at a time. |

### Decision 7: Universal Scope — ❌ NO Multi-Config, Single Instance Only

**Verdict**: The UI verifies one bridge instance. No project-switching or multi-config capability.

**Reasoning**:

- The bridge itself is already universal — any tool can call its REST API. The **UI** is a verification/debugging companion, not a management console.
- Multi-project switching implies routing traffic between different MT5 terminals, which is an entirely different architecture (service mesh, registry, config store). That's premature complexity with no current use case.
- If someone deploys multiple bridge instances (e.g., one per broker account), each instance already has its own URL and API key. They'd each have their own `/dashboard`.
- **If needed later**: This can be added as a separate `/bridge-manager` service that aggregates multiple bridges. It's a different concern from the bridge itself.

### Decision 8: WebSocket Streaming — ❌ NOT This Phase, Architectural Prep Only

**Verdict**: REST-only for this phase. But prepare the architecture for a future `GET /ws/ticks` endpoint.

**Reasoning**:

- **Current need is verification**, not live monitoring. REST request/response is sufficient to prove the bridge fetches data correctly and executes trades.
- Adding WebSocket streaming requires:
  1. A new MT5 worker pattern (polling `symbol_info_tick()` in a loop or subscription model)
  2. WebSocket connection management (multiple clients, heartbeats, disconnect handling)
  3. New UI state management for streaming data
  4. Additional auth considerations (WebSocket doesn't support custom headers in the same way)
  - This is a full feature, not a bolt-on. It deserves its own design → tasks → implementation cycle.
- **Architectural prep**: In the worker module, ensure the `submit()` function pattern is flexible enough that a future "tick poller" can coexist without refactoring. The current design (dedicated thread + queue) already supports this — a second daemon thread for tick polling could be added alongside the request worker.
- **Placeholder in UI**: The Prices tab could include a disabled "Live Ticks" toggle with tooltip "Coming soon — requires WebSocket endpoint" to signal the intention.

### Decision 9: Test Dependencies — `requirements-dev.txt` (Separate File)

**Verdict**: Create a separate `requirements-dev.txt` for test/dev dependencies. Keep `requirements.txt` as production-only.

**Reasoning**:

- The bridge runs on Windows in production. Mixing test deps into the production requirements adds unnecessary packages to the runtime environment.
- A separate `requirements-dev.txt` is the standard Python pattern for this. It can `--requirement requirements.txt` to inherit production deps, then add test-specific packages.
- This matches the ai-hedge-fund main project's pattern and common convention.

### Decision 10: Metrics Retention Window — ✅ 90 Days

**Verdict**: Retain operational metrics history for 90 days.

**Reasoning**:

- 90 days provides enough data for trend and incident review without creating excessive storage overhead.
- Shorter windows reduce diagnostic value; longer windows increase maintenance burden for a verification-focused service.
- Retention will be enforced by rolling pruning to keep operational behavior deterministic.

### Decision 11: Dashboard Session Lifetime — ✅ No Inactivity Timeout

**Verdict**: No inactivity timeout while the browser tab session remains open.

**Reasoning**:

- Verification sessions are often intermittent; forced inactivity expiry adds friction during investigation.
- Session still ends on tab/browser close because the API key is kept in `sessionStorage`.
- This preserves existing auth model and avoids backend session-state complexity.

---

## 5. New API Endpoints (Backend)

### 4.1 `GET /symbols`

**File**: `app/routes/symbols.py`

**Purpose**: List all configured symbols from `symbols.yaml` for UI dropdowns and external discovery.

**Response Model** (new file `app/models/symbol.py`):

```
SymbolInfo:
    ticker: str                    # User-facing name (e.g., "V75")
    mt5_symbol: str               # Broker symbol (e.g., "Volatility 75 Index")
    lot_size: float               # Default lot size
    category: str                 # "synthetic", "forex", "equity"
```

**Response**:

```json
{
    "symbols": [
        {"ticker": "V75", "mt5_symbol": "Volatility 75 Index", "lot_size": 0.01, "category": "synthetic"},
        ...
    ]
}
```

**Implementation**:

- Import `symbol_map` from `app.main`
- Iterate entries, convert `SymbolEntry` → `SymbolInfo`
- Return as list

---

### 4.2 `GET /logs`

**File**: `app/routes/logs.py`

**Purpose**: Paginated view of trade audit log entries.

**Query Parameters**:

- `limit` (int, default 50, max 500)
- `offset` (int, default 0)

**Response Model** (new file `app/models/log_entry.py`):

```
LogEntry:
    timestamp: str
    request: dict
    response: dict

LogsResponse:
    total: int
    offset: int
    limit: int
    entries: list[LogEntry]
```

**Implementation**:

- Read `logs/trades.jsonl` in reverse order (most recent first)
- Parse each line as JSON
- Apply offset/limit pagination
- Count total lines for `total` field
- Return empty list if file doesn't exist

---

### 4.3 `GET /config`

**File**: `app/routes/config_info.py`

**Purpose**: Expose current runtime settings (sanitized — no passwords or API keys).

**Response Model** (new file `app/models/config_info.py`):

```
ConfigInfo:
    mt5_bridge_port: int
    mt5_server: str
    mt5_login: int | None          # Account number (not sensitive)
    mt5_path: str | None
    log_level: str
    symbol_count: int
    symbols_config_path: str
    execution_enabled: bool
    metrics_retention_days: int
```

**Implementation**:

- Read from the existing `settings` singleton
- Explicitly exclude `mt5_bridge_api_key` and `mt5_password`
- Include `len(symbol_map)` as `symbol_count`
- Include `execution_enabled` and `metrics_retention_days` for dashboard policy rendering

---

### 4.4 `GET /worker/state`

**File**: `app/routes/worker.py`

**Purpose**: Granular worker state for debugging (more detail than `/health`).

**Response Model** (new file `app/models/worker_info.py`):

```
WorkerInfo:
    state: str                     # Current WorkerState enum value
    queue_depth: int              # Current items in request queue
    max_reconnect_retries: int
    reconnect_base_delay: float
```

**Implementation**:

- Import `get_state`, `_request_queue` from `mt5_worker`
- Read `_request_queue.qsize()` for queue depth
- Expose constants for reconnect configuration

---

### 4.5 Metrics Tracking (Internal)

**File**: `app/metrics.py`

**Purpose**: Request metrics service with a rolling 90-day retention window for dashboard status and troubleshooting.

**Data tracked**:

```
MetricsSummary:
    uptime_seconds: float
    total_requests: int
    requests_by_endpoint: dict[str, int]  # {"/health": 42, "/prices": 120, ...}
    errors_count: int
    last_request_at: str | None
    retention_days: int
```

**Implementation**:

- Module-level counters for fast reads + persisted metrics history in `logs/metrics.jsonl`
- FastAPI middleware (`@app.middleware("http")`) increments counters
- New endpoint `GET /metrics` returns the summary
- Apply rolling cleanup to prune metrics records older than 90 days
- Middleware is additive — does not modify request/response flow

---

## 6. Dashboard UI Specification

### 5.1 Layout Structure

```
┌──────────────────────────────────────────────────────────────────┐
│  HEADER: "MT5 Bridge Dashboard"    [●/○ status]   [latency]    │
├──────────────────────────────────────────────────────────────────┤
│  TAB BAR:  Status | Symbols | Prices | Execute | Logs | Config │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CONTENT AREA (renders based on active tab)                      │
│                                                                  │
│                                                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
│  FOOTER: Bridge v1.0  |  API docs: /docs  |  Session: active    │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 Auth Screen (shown first if no key in sessionStorage)

- Centered card with title "MT5 Bridge Dashboard"
- Single input field: "API Key"
- "Connect" button
- On submit: stores key in `sessionStorage`, calls `GET /health` to validate
- If 401: shows error, clears key
- If success: renders dashboard
- No inactivity timeout countdown is displayed; session persists while the tab is open

### 5.3 Tab: Status

**Auto-refreshes every 5 seconds.**

| Section           | Data Source                       | Display                                                        |
| :---------------- | :-------------------------------- | :------------------------------------------------------------- |
| Connection Status | `GET /health`                     | Green/red badge: "Connected" / "Disconnected"                  |
| Authorization     | `GET /health`                     | Green/yellow badge: "Authorized" / "Not Authorized"            |
| Broker            | `GET /health` → `broker`          | Text display                                                   |
| Account ID        | `GET /health` → `account_id`      | Text display                                                   |
| Balance           | `GET /health` → `balance`         | Formatted currency                                             |
| Latency           | `GET /health` → `latency_ms`      | Badge with color coding (<50ms green, <200ms yellow, else red) |
| Worker State      | `GET /worker/state`               | State badge + queue depth                                      |
| Uptime            | `GET /metrics` → `uptime_seconds` | Formatted duration                                             |
| Request Count     | `GET /metrics` → `total_requests` | Numeric display                                                |

### 5.4 Tab: Symbols

**Static data, loaded once.**

| Element         | Behavior                                        |
| :-------------- | :---------------------------------------------- |
| Symbol table    | Columns: Ticker, MT5 Symbol, Lot Size, Category |
| Category filter | Dropdown: All / Synthetic / Forex / Equity      |
| Search          | Text filter across ticker and MT5 symbol name   |
| Row count       | "Showing X of Y symbols"                        |

Data source: `GET /symbols`

### 5.5 Tab: Prices

**Interactive form + results.**

| Element       | Type       | Details                                                                  |
| :------------ | :--------- | :----------------------------------------------------------------------- |
| Ticker        | Dropdown   | Populated from `GET /symbols`                                            |
| Start Date    | Date input | Default: 30 days ago                                                     |
| End Date      | Date input | Default: today                                                           |
| Timeframe     | Dropdown   | Options: M1, M5, M15, M30, H1, H4, D1, W1, MN1. Default: D1              |
| Fetch button  | Button     | Calls `GET /prices?ticker=...&start_date=...&end_date=...&timeframe=...` |
| Results count | Text       | "Returned X candles"                                                     |
| Data table    | Table      | Columns: Time, Open, High, Low, Close, Volume                            |
| Chart area    | Canvas     | Candlestick chart (lightweight-charts) — shown below table               |
| Export        | Button     | Download results as JSON                                                 |

**Error states**:

- Unknown ticker → show API error message
- Empty results → "No data available for this range"
- 503 → "MT5 terminal not connected"

### 5.6 Tab: Execute

**Interactive form with safety guards.**

> [!CAUTION]
> This tab sends **real orders** to the MT5 terminal. Must include explicit safety mechanisms.

| Element                         | Type         | Details                                                                                                                               |
| :------------------------------ | :----------- | :------------------------------------------------------------------------------------------------------------------------------------ |
| **Execution enabled status**    | Banner       | Derived from `GET /config` → `execution_enabled`. If `false`, execute controls are locked and submit actions are blocked.           |
| **Environment badge**           | Banner       | Shows "LIVE" (red) or "DEMO" (green) based on `/config` → `mt5_server` containing "Demo"                                            |
| Ticker                          | Dropdown     | Populated from `GET /symbols`                                                                                                         |
| Action                          | Dropdown     | buy, sell, short, cover                                                                                                               |
| Quantity                        | Number input | Default: minimum lot size for selected symbol                                                                                         |
| Current Price                   | Number input | Manual entry (bridge doesn't have a tick endpoint yet)                                                                                |
| **Multi-trade mode**            | Toggle       | OFF by default. When ON, allow multiple submissions in parallel with no fixed UI cap.                                                |
| **Multi-trade risk warning**    | Alert panel  | Visible when multi-trade mode is ON. States risk implications before submission is allowed.                                           |
| **Confirmation checkbox**       | Checkbox     | "I understand this will execute a REAL trade"                                                                                         |
| Submit button                   | Button       | Disabled until checkbox is checked and execution is enabled. Calls `POST /execute`. When multi-trade OFF, only one in-flight submit. |
| Result area                     | Card         | Shows success/failure, filled price, quantity, ticket ID                                                                              |

**Execution-specific states**:

- `execution_enabled = false` → "Execution is disabled for this environment"
- Multi-trade ON with rapid submissions → keep all submissions allowed, each with independent result cards

### 5.7 Tab: Logs

**Paginated trade history.**

| Element     | Type     | Details                                                                               |
| :---------- | :------- | :------------------------------------------------------------------------------------ |
| Log table   | Table    | Columns: Timestamp, Ticker, Action, Quantity, Success, Filled Price, Ticket ID, Error |
| Pagination  | Buttons  | Previous / Next, showing page X of Y                                                  |
| Page size   | Dropdown | 25, 50, 100                                                                           |
| Empty state | Message  | "No trades recorded yet"                                                              |
| Refresh     | Button   | Re-fetch current page                                                                 |

Data source: `GET /logs?limit=...&offset=...`

### 5.8 Tab: Config

**Read-only display.**

| Element      | Display                       |
| :----------- | :---------------------------- |
| Bridge Port  | `mt5_bridge_port`             |
| MT5 Server   | `mt5_server`                  |
| MT5 Login    | `mt5_login` (account number)  |
| MT5 Path     | `mt5_path` or "Auto-detected" |
| Log Level    | `log_level`                   |
| Symbol Count | `symbol_count`                |
| Config Path  | `symbols_config_path`         |
| Execution Enabled | `execution_enabled`       |
| Metrics Retention | `metrics_retention_days`   |

Data source: `GET /config`

### 5.9 Design Tokens (CSS)

```
--color-bg:          #0f1117        (dark background)
--color-surface:     #1a1d27        (card/panel background)
--color-border:      #2a2d3a        (subtle borders)
--color-text:        #e1e4ea        (primary text)
--color-text-muted:  #6b7280        (secondary text)
--color-accent:      #3b82f6        (primary blue)
--color-success:     #10b981        (green — connected, success)
--color-warning:     #f59e0b        (yellow — warnings)
--color-danger:      #ef4444        (red — errors, disconnected, LIVE)
--font-family:       'Inter', system-ui, sans-serif
--font-mono:         'JetBrains Mono', 'Fira Code', monospace
--radius:            8px
--transition:        150ms ease
```

---

## 7. Testing Strategy

### 6.1 Test Infrastructure

**New files in `mt5-connection-bridge/`**:

| File                                           | Purpose                                                      |
| :--------------------------------------------- | :----------------------------------------------------------- |
| `pyproject.toml` or update `requirements.txt`  | Add test dependencies                                        |
| `pytest.ini` or `pyproject.toml [tool.pytest]` | Pytest configuration                                         |
| `tests/conftest.py`                            | Shared fixtures: mock MT5 module, test client, test settings |

**Test dependencies to add**:

```
pytest>=7.4.0
pytest-asyncio>=0.23.0
pytest-mock>=3.12.0
httpx>=0.25.0                     # For async TestClient
coverage>=7.3.0
```

### 6.2 Core Fixture: Mock MetaTrader5 Module

In `tests/conftest.py`, create a comprehensive mock that:

1. **Patches `MetaTrader5` as a sys.modules entry** so all `import MetaTrader5 as mt5` calls resolve
2. Provides mock implementations for:
   - `mt5.initialize()` → returns `True`
   - `mt5.login()` → returns `True`
   - `mt5.shutdown()` → no-op
   - `mt5.last_error()` → returns `(0, "OK")`
   - `mt5.account_info()` → returns mock object with `company`, `login`, `balance`, `server_time`
   - `mt5.copy_rates_range()` → returns a numpy structured array with OHLCV fields
   - `mt5.symbol_info()` → returns mock object with `visible`, `volume_min`, `volume_max`, `volume_step`, `spread`
   - `mt5.symbol_select()` → returns `True`
   - `mt5.order_send()` → returns mock result with `retcode`, `price`, `volume`, `order`
   - Constants: `ORDER_TYPE_BUY=0`, `ORDER_TYPE_SELL=1`, `TRADE_ACTION_DEAL=1`, `ORDER_TIME_GTC=0`, `ORDER_FILLING_IOC=2`, `TRADE_RETCODE_DONE=10009`

3. **A `TestClient` fixture** using FastAPI's `TestClient` with the API key header pre-set

4. **A test `Settings` fixture** with deterministic values

5. **A numpy rates fixture** that generates realistic OHLCV data for price mapper tests

### 6.3 Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py                       ← Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_config.py                ← 8-10 tests
│   ├── test_auth.py                  ← 4-5 tests
│   ├── test_price_mapper.py          ← 6-8 tests
│   ├── test_trade_mapper.py          ← 10-12 tests
│   └── test_mt5_worker.py            ← 6-8 tests
└── integration/
    ├── __init__.py
    ├── test_health_route.py          ← 4-5 tests
    ├── test_prices_route.py          ← 6-8 tests
    ├── test_execute_route.py         ← 6-8 tests
    ├── test_symbols_route.py         ← 3-4 tests
    ├── test_logs_route.py            ← 4-5 tests
    ├── test_config_route.py          ← 2-3 tests
    └── test_worker_route.py          ← 2-3 tests
```

### 6.4 Unit Test Specifications

#### `test_config.py`

| Test                                      | Description                                           |
| :---------------------------------------- | :---------------------------------------------------- |
| `test_settings_defaults`                  | Verify default values when no env vars set            |
| `test_settings_from_env`                  | Set env vars, verify Settings picks them up           |
| `test_load_symbol_map_valid`              | Load the actual `config/symbols.yaml`, verify entries |
| `test_load_symbol_map_missing_file`       | Nonexistent path raises `FileNotFoundError`           |
| `test_load_symbol_map_empty`              | YAML with no `symbols` key returns empty dict         |
| `test_load_symbol_map_custom_path`        | Explicit path parameter works                         |
| `test_get_mt5_timeframe_valid`            | All 9 valid timeframes resolve correctly              |
| `test_get_mt5_timeframe_invalid`          | Unknown timeframe raises `ValueError`                 |
| `test_get_mt5_timeframe_case_insensitive` | "d1" and "D1" both work                               |
| `test_symbol_entry_repr`                  | SymbolEntry `__repr__` is well-formed                 |

#### `test_auth.py`

| Test                   | Description              |
| :--------------------- | :----------------------- |
| `test_valid_api_key`   | Correct key returns 200  |
| `test_missing_api_key` | No header returns 401    |
| `test_wrong_api_key`   | Wrong key returns 401    |
| `test_empty_api_key`   | Empty string returns 401 |

#### `test_price_mapper.py`

| Test                               | Description                                             |
| :--------------------------------- | :------------------------------------------------------ |
| `test_map_valid_rates`             | Normal numpy array maps correctly to PriceResponse      |
| `test_map_none_rates`              | `None` input returns empty prices list                  |
| `test_map_empty_array`             | Zero-length array returns empty prices list             |
| `test_map_volume_tick_priority`    | `tick_volume > 0` is used over `real_volume`            |
| `test_map_volume_fallback_to_real` | `tick_volume == 0` falls back to `real_volume`          |
| `test_map_timestamp_format`        | Unix epoch correctly converts to ISO 8601 with Z suffix |
| `test_map_preserves_ticker`        | Ticker passthrough is exact                             |
| `test_map_large_dataset`           | 10,000 rows process without error                       |

#### `test_trade_mapper.py`

| Test                                          | Description                                 |
| :-------------------------------------------- | :------------------------------------------ |
| `test_action_buy`                             | "buy" maps to ORDER_TYPE_BUY (0)            |
| `test_action_sell`                            | "sell" maps to ORDER_TYPE_SELL (1)          |
| `test_action_short`                           | "short" maps to ORDER_TYPE_SELL (1)         |
| `test_action_cover`                           | "cover" maps to ORDER_TYPE_BUY (0)          |
| `test_action_invalid`                         | Unknown action raises ValueError            |
| `test_action_case_insensitive`                | "BUY", "Buy" both work                      |
| `test_normalize_lot_basic`                    | 0.05 with step 0.01 → 0.05                  |
| `test_normalize_lot_rounding`                 | 0.015 with step 0.01 → 0.02 (round half up) |
| `test_normalize_lot_clamp_min`                | Below min → clamped to min                  |
| `test_normalize_lot_clamp_max`                | Above max → clamped to max                  |
| `test_normalize_lot_zero_step`                | step=0 → simple clamp                       |
| `test_normalize_lot_zero_quantity`            | quantity ≤ 0 raises ValueError              |
| `test_build_order_request_fields`             | All fields present with correct values      |
| `test_build_order_request_deviation_fallback` | spread=0 → deviation defaults to 20         |

#### `test_mt5_worker.py`

| Test                               | Description                                                  |
| :--------------------------------- | :----------------------------------------------------------- |
| `test_initial_state_disconnected`  | Worker starts in DISCONNECTED before `start_worker`          |
| `test_start_worker_creates_thread` | `start_worker()` spawns daemon thread                        |
| `test_submit_returns_future`       | `submit(fn)` returns a `Future`                              |
| `test_worker_processes_request`    | Submitted callable is executed and result is set on future   |
| `test_worker_handles_exception`    | Exception in callable is caught and set on future            |
| `test_stop_worker_sends_sentinel`  | `stop_worker()` drains queue and joins thread                |
| `test_disconnect_detection`        | `_is_disconnect_error` correctly identifies disconnect codes |
| `test_reconnect_backoff`           | Reconnect delays follow exponential backoff pattern          |

### 6.5 Integration Test Specifications

All integration tests use `httpx.AsyncClient` (or `TestClient`) with `app` directly. The MT5 module is mocked at the `conftest.py` level.

#### `test_health_route.py`

| Test                              | Description                                              |
| :-------------------------------- | :------------------------------------------------------- |
| `test_health_connected`           | Worker AUTHORIZED → returns full health with broker info |
| `test_health_disconnected`        | Worker DISCONNECTED → returns `connected: false`         |
| `test_health_unauthorized_no_key` | Missing API key → 401                                    |
| `test_health_returns_latency`     | Response includes `latency_ms` field                     |

#### `test_prices_route.py`

| Test                               | Description                                     |
| :--------------------------------- | :---------------------------------------------- |
| `test_prices_valid_request`        | Known ticker, valid dates → returns candle data |
| `test_prices_unknown_ticker`       | Unknown ticker → 404                            |
| `test_prices_invalid_timeframe`    | Bad timeframe → 422                             |
| `test_prices_invalid_date_format`  | Non-YYYY-MM-DD → 422                            |
| `test_prices_mt5_disconnected`     | Worker not ready → 503                          |
| `test_prices_mt5_returns_none`     | MT5 returned no data → empty prices list        |
| `test_prices_schema_compatibility` | Response matches `PriceResponse` schema exactly |

#### `test_execute_route.py`

| Test                                | Description                                     |
| :---------------------------------- | :---------------------------------------------- |
| `test_execute_buy_success`          | Valid buy → success with ticket ID              |
| `test_execute_sell_success`         | Valid sell → success                            |
| `test_execute_unknown_ticker`       | Unknown ticker → 404                            |
| `test_execute_invalid_action`       | Bad action → 422                                |
| `test_execute_mt5_disconnected`     | Worker not ready → 503                          |
| `test_execute_order_rejected`       | MT5 retcode ≠ DONE → success=false with error   |
| `test_execute_creates_audit_log`    | After trade, `trades.jsonl` contains entry      |
| `test_execute_schema_compatibility` | Response matches `TradeResponse` schema exactly |
| `test_execute_parallel_submissions` | Multiple concurrent execute calls return independent responses |

#### `test_symbols_route.py` (new endpoint)

| Test                          | Description                                           |
| :---------------------------- | :---------------------------------------------------- |
| `test_symbols_returns_all`    | Returns all entries from symbols.yaml                 |
| `test_symbols_fields_present` | Each entry has ticker, mt5_symbol, lot_size, category |
| `test_symbols_unauthorized`   | Missing API key → 401                                 |

#### `test_logs_route.py` (new endpoint)

| Test                      | Description                      |
| :------------------------ | :------------------------------- |
| `test_logs_empty`         | No log file → empty entries list |
| `test_logs_with_data`     | Populated log → returns entries  |
| `test_logs_pagination`    | offset/limit work correctly      |
| `test_logs_reverse_order` | Most recent entries first        |

#### `test_metrics_route.py` (new endpoint)

| Test                             | Description                                              |
| :------------------------------- | :------------------------------------------------------- |
| `test_metrics_summary_fields`    | Returns uptime/request/error fields and retention window |
| `test_metrics_retention_days_90` | Response retention window is 90 days                     |
| `test_metrics_unauthorized`      | Missing API key → 401                                    |

---

## 8. File-by-File Implementation Plan

### Phase 1: Test Infrastructure + Unit Tests

| #   | Action | File                              | Details                                                                                        |
| :-- | :----- | :-------------------------------- | :--------------------------------------------------------------------------------------------- |
| 1   | CREATE | `tests/conftest.py`               | Mock MT5 module, test client, settings fixtures, numpy rates factory                           |
| 2   | CREATE | `tests/unit/__init__.py`          | Empty init                                                                                     |
| 3   | CREATE | `tests/unit/test_config.py`       | 8-10 tests for Settings, symbol map, timeframe map                                             |
| 4   | CREATE | `tests/unit/test_auth.py`         | 4-5 tests for API key validation                                                               |
| 5   | CREATE | `tests/unit/test_price_mapper.py` | 6-8 tests for numpy → PriceResponse mapping                                                    |
| 6   | CREATE | `tests/unit/test_trade_mapper.py` | 10-12 tests for action mapping, lot normalization, order building                              |
| 7   | CREATE | `tests/unit/test_mt5_worker.py`   | 6-8 tests for state machine, queue, reconnect                                                  |
| 8   | MODIFY | `requirements.txt`                | Add `pytest`, `pytest-asyncio`, `pytest-mock`, `httpx`, `coverage` under a `# Testing` section |
| 9   | CREATE | `pytest.ini`                      | Configure `asyncio_mode = auto`, test paths, markers                                           |

### Phase 2: New API Endpoints

| #   | Action | File                        | Details                                                                |
| :-- | :----- | :-------------------------- | :--------------------------------------------------------------------- |
| 10  | CREATE | `app/models/symbol.py`      | `SymbolInfo`, `SymbolsResponse` models                                 |
| 11  | CREATE | `app/models/log_entry.py`   | `LogEntry`, `LogsResponse` models                                      |
| 12  | CREATE | `app/models/config_info.py` | `ConfigInfo` model                                                     |
| 13  | CREATE | `app/models/worker_info.py` | `WorkerInfo` model                                                     |
| 14  | CREATE | `app/models/metrics.py`     | `MetricsSummary` model                                                 |
| 15  | CREATE | `app/routes/symbols.py`     | `GET /symbols` — list configured symbols                               |
| 16  | CREATE | `app/routes/logs.py`        | `GET /logs` — paginated trade audit log                                |
| 17  | CREATE | `app/routes/config_info.py` | `GET /config` — sanitized settings + execution/retention policy        |
| 18  | CREATE | `app/routes/worker.py`      | `GET /worker/state` — granular worker state                            |
| 19  | CREATE | `app/metrics.py`            | Rolling metrics service + `GET /metrics` endpoint (90-day retention)   |
| 20  | MODIFY | `app/main.py`               | Import and include new routers (4 lines total), add metrics middleware |

### Phase 3: Dashboard UI

| #   | Action | File                          | Details                                                                 |
| :-- | :----- | :---------------------------- | :---------------------------------------------------------------------- |
| 21  | CREATE | `dashboard/index.html`        | Single HTML page: header, tab bar, content area, footer. Loads CSS + JS |
| 22  | CREATE | `dashboard/css/dashboard.css` | Dark theme design system, responsive layout, component styles           |
| 23  | CREATE | `dashboard/js/app.js`         | API client class, tab router, auth flow, auto-refresh logic             |
| 24  | CREATE | `dashboard/js/components.js`  | Render functions: status cards, data tables, forms, badges, pagination  |
| 25  | CREATE | `dashboard/js/chart.js`       | Candlestick chart using locally bundled lightweight-charts vendor module |
| 26  | MODIFY | `app/main.py`                 | Add `StaticFiles` mount for `/dashboard` (1 import + 1 line)            |

### Phase 4: Integration Tests for New Endpoints

| #   | Action | File                                      | Details               |
| :-- | :----- | :---------------------------------------- | :-------------------- |
| 27  | CREATE | `tests/integration/__init__.py`           | Empty init            |
| 28  | CREATE | `tests/integration/test_health_route.py`  | 4-5 integration tests |
| 29  | CREATE | `tests/integration/test_prices_route.py`  | 6-8 integration tests |
| 30  | CREATE | `tests/integration/test_execute_route.py` | 7-9 integration tests |
| 31  | CREATE | `tests/integration/test_symbols_route.py` | 3-4 integration tests |
| 32  | CREATE | `tests/integration/test_logs_route.py`    | 4-5 integration tests |
| 33  | CREATE | `tests/integration/test_config_route.py`  | 2-3 integration tests |
| 34  | CREATE | `tests/integration/test_worker_route.py`  | 2-3 integration tests |
| 35  | CREATE | `tests/integration/test_metrics_route.py` | 2-3 integration tests |

### Phase 5: Documentation + Finalization

| #   | Action | File           | Details                                                   |
| :-- | :----- | :------------- | :-------------------------------------------------------- |
| 36  | MODIFY | `README.md`    | Add Dashboard section, testing section, new endpoint docs |
| 37  | MODIFY | `.env.example` | Add `EXECUTION_ENABLED` and `METRICS_RETENTION_DAYS` examples |

---

## 9. Phased Delivery Plan

```
Phase 1 ─── Test Infrastructure ──────── ~35 tests, 9 files
   │        (can run immediately, validates existing code)
   ▼
Phase 2 ─── New API Endpoints ────────── 5 endpoints, 11 files
   │        (purely additive, no existing code changes)
   ▼
Phase 3 ─── Dashboard UI ────────────── 5 files, ~1000 lines
   │        (static files, 2-line change to main.py)
   ▼
Phase 4 ─── Integration Tests ────────── ~33 tests, 8 files
   │        (covers all routes including new ones)
   ▼
Phase 5 ─── Documentation ───────────── 2 file updates
            (README + `.env.example`)
```

**Total new files**: ~31  
**Total modified files**: 3 (`main.py`, `README.md`, `.env.example`)  
**Estimated test count**: ~68 tests  
**Existing code changes**: Additive updates to router wiring, config policy exposure, metrics retention handling, and dashboard execution controls.

---

## 10. Risk Assessment

| Risk                                                            | Likelihood         | Mitigation                                                                                         |
| :-------------------------------------------------------------- | :----------------- | :------------------------------------------------------------------------------------------------- |
| MT5 mock doesn't match real API behavior                        | Medium             | Use real MT5 docs for mock fixture shapes; add integration test markers for future Windows testing |
| UI JS fetch calls fail due to FastAPI CORS                      | None               | UI is served from same origin — no CORS needed                                                     |
| Adding routers changes import order in `main.py`                | Low                | New routers are appended after existing ones; tested via integration tests                         |
| `StaticFiles` mount conflicts with existing routes              | None               | `/dashboard` path doesn't conflict with `/health`, `/prices`, `/execute`                           |
| Trade audit log file grows unbounded                            | Medium (long-term) | Out of scope for this change but flag for future: add log rotation                                 |
| `lightweight-charts` vendor bundle missing or outdated          | Low                | Pin and ship local vendor asset in `dashboard/js/vendor/` with release checks                      |
| No explicit cap in multi-trade mode can cause burst load        | Medium             | Default multi-trade toggle OFF, show risk warning when ON, rely on broker/MT5 safeguards           |
| Long-lived tab sessions increase exposure if workstation is shared | Medium          | Keep key in `sessionStorage`, require explicit reconnect on tab close, document workstation hygiene |

---

> **Next Step**: Blueprint is aligned with the interview decisions and ready for implementation artifact generation (`/opsx:new` or `/opsx:ff`).
