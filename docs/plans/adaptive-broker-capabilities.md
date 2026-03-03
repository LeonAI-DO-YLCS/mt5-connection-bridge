# Adaptive Broker Capabilities Plan

**MT5 Bridge — Dynamic Symbol Discovery, Capability Detection & Dashboard Adaptation**

> Status: PLANNING
> Created: 2026-03-02
> Scope: `app/` (backend bridge) + `dashboard/` (frontend)
> Goal: Zero hardcoded assumptions about broker capabilities, filling modes, or instrument catalogs.

---

## 1. Problem Statement

The current implementation makes four categories of hardcoded assumptions that will silently fail on any broker that deviates from the initial Deriv.com defaults:

| #   | Problem                                        | Location                                       | Symptom                                                                 |
| --- | ---------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------- |
| 1   | **Filling mode is hardcoded to IOC**           | `trade_mapper.py:75,93,142,159`                | `retcode=10030 Unsupported filling mode`                                |
| 2   | **Symbol catalog is static YAML**              | `config/symbols.yaml` + `routes/symbols.py`    | New broker symbols never visible; executions fail on unknown tickers    |
| 3   | **Symbol categories are pattern-matched text** | `dashboard/js/symbols-browser.js:11-16, 44-49` | Filter groups are wrong; Deriv synthetic indices don't fit any category |
| 4   | **Trade mode per symbol not enforced**         | `routes/execute.py`, `routes/pending_order.py` | Users can submit buy orders on sell-only symbols; broker rejects them   |

### Root Cause Architecture Diagram

```
config/symbols.yaml  ──────────────┐
(static, human-maintained)         │
                                   ▼
dashboard Execute tab ──────► /execute endpoint
     uses ticker list             uses IOC filling
     from /symbols                ignores symbol_info.filling_mode
     (only YAML entries)          ignores symbol_info.trade_mode

dashboard Symbols tab ──────► /broker-symbols endpoint
     hardcoded group              returns path but categories
     filter dropdown              are extracted by guessing
```

---

## 2. MT5 Capabilities That Must Be Exploited

The MT5 Python API exposes everything needed. None of these capabilities are currently used:

### 2.1 Filling Mode Bitmask (per symbol)

```
symbol_info.filling_mode  →  int bitmask
  bit 0 (value 1) = ORDER_FILLING_FOK  supported
  bit 1 (value 2) = ORDER_FILLING_IOC  supported
  value 0         = ORDER_FILLING_RETURN only (implicit)

Selection priority: FOK → IOC → RETURN
```

### 2.2 Symbol Path = Broker Category Hierarchy

```
symbol_info.path  →  str
  Examples from Deriv:
    "Volatility Indices\\Continuous Indices\\Volatility 10 Index"
    "Forex\\Majors\\EURUSD"
    "Crypto\\Bitcoin\\BTC/USD"

The path is an actual folder hierarchy in the MT5 Symbols tree.
The top-level folder (first segment before \\) is the true category.
Sub-categories (all segments) give a full breadcrumb.
```

### 2.3 Trade Mode (per symbol)

```
symbol_info.trade_mode  →  int
  0 = SYMBOL_TRADE_MODE_DISABLED   (no trades)
  1 = SYMBOL_TRADE_MODE_LONGONLY   (buy only)
  2 = SYMBOL_TRADE_MODE_SHORTONLY  (sell only)
  3 = SYMBOL_TRADE_MODE_CLOSEONLY  (close existing only)
  4 = SYMBOL_TRADE_MODE_FULL       (all operations allowed)
```

### 2.4 Account Trade Allowed

```
terminal_info.trade_allowed  →  bool
account_info.trade_allowed   →  bool
  Both must be true for any execution to work.
  Currently: terminal_info.trade_allowed is displayed but not enforced.
```

### 2.5 All Broker Symbols (already partially used)

```
mt5.symbols_get()  →  all symbols on broker
mt5.symbols_get(group="Forex\\*")  →  filtered by group
  The 'path' field on each symbol gives its full hierarchy.
```

---

## 3. Proposed Changes — High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              NEW: /broker-capabilities endpoint              │
│                                                              │
│  On startup (and on-demand):                                 │
│   • mt5.symbols_get()                                        │
│   • For each symbol: extract filling_mode, trade_mode, path  │
│   • Derive category tree from path segments                  │
│   • Build: symbol registry + capabilities + category tree    │
│                                                              │
│  Returns:                                                    │
│   { symbols[], categories{}, account_trade_allowed: bool }   │
└──────────────────────┬───────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
┌─────────────────────┐   ┌─────────────────────────────────┐
│  Backend: trade     │   │  Dashboard: Execute Tab          │
│  mapper adapts      │   │                                  │
│  filling mode per   │   │  Ticker list = live broker       │
│  symbol at runtime  │   │  symbols (not YAML)              │
│                     │   │                                  │
│  trade_mode check   │   │  Buy/Sell buttons disabled per   │
│  blocks invalid     │   │  symbol trade_mode               │
│  order directions   │   │                                  │
└─────────────────────┘   │  Category filter = real MT5      │
                           │  hierarchy, dynamically built    │
                           │  from path segments              │
                           └─────────────────────────────────┘
```

---

## 4. Detailed Plan — Backend Changes

### Phase A: Fix Filling Mode (Highest Priority — Unblocks the core bug)

**File:** `app/mappers/trade_mapper.py`

**Change:** Replace the hardcoded `ORDER_FILLING_IOC` with a dynamic selection function that reads `symbol_info.filling_mode`.

**New function to add:**

```
resolve_filling_mode(symbol_info) -> int
  1. Read symbol_info.filling_mode (int bitmask)
  2. If bit 0 set → return ORDER_FILLING_FOK (1)
  3. Elif bit 1 set → return ORDER_FILLING_IOC (2)
  4. Else → return ORDER_FILLING_RETURN (0)   ← fallback, always supported
```

**Affected functions:**

- `build_order_request()` — line 75, 93 → use `resolve_filling_mode(symbol_info)`
- `build_pending_order_request()` — line 142, 159 → same
- `build_close_request()` — currently has no `type_filling` set; add it using `resolve_filling_mode(symbol_info)`

**Note:** `build_close_request()` currently does NOT receive `symbol_info`. The caller in `close_position.py` already fetches it (line 105). It must be passed to `build_close_request()`.

---

### Phase B: New `/broker-capabilities` Endpoint

**New file:** `app/routes/broker_capabilities.py`

**New model:** `app/models/broker_capabilities.py`

This endpoint consolidates everything the dashboard and execution engine need in a single call, cached on the bridge side (refreshed on connect/reconnect).

**Response Schema:**

```json
{
  "account_trade_allowed": true,
  "terminal_trade_allowed": true,
  "symbol_count": 348,
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
      "visible": true
    }
  ],
  "categories": {
    "Forex": ["Majors", "Minors", "Exotics"],
    "Volatility Indices": ["Continuous Indices", "Daily Reset Indices"],
    "Crypto": ["Bitcoin", "Ethereum"]
  }
}
```

**Logic:**

1. Call `mt5.symbols_get()` to get all available symbols
2. Call `mt5.terminal_info()` and `mt5.account_info()` for trade-allowed flags
3. For each symbol:
   - Parse `path` into segments: `path.split("\\")` or `path.split("/")`
   - `category` = segments[0], `subcategory` = segments[1] (if exists)
   - Decode `filling_mode` bitmask into list of supported mode strings
   - Map `trade_mode` int to label string
4. Build `categories` dict: `{category: [unique subcategories]}`
5. Return full payload

**Caching strategy:**

- Cache the result in memory on the bridge (module-level dict)
- Cache TTL: 60 seconds (configurable via env `CAPABILITIES_CACHE_TTL_SECONDS`)
- Automatic invalidation: on MT5 worker reconnect event
- Manual refresh: `POST /broker-capabilities/refresh` endpoint

---

### Phase C: Enforce Trade Mode on Order Submission

**File:** `app/routes/execute.py`

**Where:** Inside `_execute_in_worker()`, after `symbol_info = mt5.symbol_info(mt5_symbol)` is fetched (around line 97).

**New validation block:**

```
trade_mode = int(getattr(symbol_info, "trade_mode", 4))
action = req.action  # "buy", "sell", "short", "cover"

if trade_mode == 0:  # DISABLED
    → reject: "Symbol trading is disabled by broker."

if trade_mode == 1 and action in ("sell", "short"):  # LONGONLY
    → reject: "Symbol only allows long (buy) trades."

if trade_mode == 2 and action in ("buy", "cover"):  # SHORTONLY
    → reject: "Symbol only allows short (sell) trades."

if trade_mode == 3:  # CLOSEONLY
    → reject: "Symbol is in close-only mode. No new positions allowed."
```

**Same validation needed in:** `app/routes/pending_order.py` — apply equivalent direction checks for `buy_limit`/`buy_stop` vs `sell_limit`/`sell_stop`

---

### Phase D: Extend `/broker-capabilities` with Enriched `BrokerSymbol` Model

**File:** `app/models/broker_symbol.py`

**Add fields:**

- `category: str` — extracted from path segment 0
- `subcategory: str` — extracted from path segment 1 (empty string if absent)
- `filling_mode: int` — raw bitmask from MT5
- `supported_filling_modes: list[str]` — human labels ["FOK", "IOC"] or ["RETURN"]
- `trade_mode: int` — raw int from MT5
- `volume_step: float` — step size for volume increments
- `visible: bool` — is symbol currently visible in Market Watch

**Update:** `app/routes/broker_symbols.py` — populate the new fields

---

### Phase E: Settings Extension

**File:** `app/config.py` → `Settings` class

**New env vars:**

```
CAPABILITIES_CACHE_TTL_SECONDS=60    # How long to cache broker catalog
AUTO_SELECT_SYMBOLS=true             # If true, auto-select symbols in Market Watch
```

---

## 5. Detailed Plan — Dashboard Changes

### Phase F: Dynamic Ticker Catalog in Execute Tab

**File:** `dashboard/js/execute-v2.js`

**Current behavior:**

- Calls `GET /symbols` (YAML-based list) + `GET /broker-symbols` (full broker list)
- Ticker dropdown populated only from YAML-configured symbols
- No trade_mode awareness — buy/sell always available

**New behavior:**

1. Call `GET /broker-capabilities` instead (single call replacing both)
2. Populate ticker dropdown from **all symbols** with `trade_mode != 0` (tradeable)
   - Group options by `category` using `<optgroup label="Forex">` etc.
3. On ticker selection:
   - Read `trade_mode` from the cached capabilities response
   - Disable the Buy option if `trade_mode` is `SHORTONLY` or `CLOSEONLY`
   - Disable the Sell option if `trade_mode` is `LONGONLY` or `CLOSEONLY`
   - Show a tooltip/badge explaining why an option is disabled
4. No more dependency on `config/symbols.yaml` for the Execute tab

---

### Phase G: Dynamic Symbol Browser Tab

**File:** `dashboard/js/symbols-browser.js`

**Current behavior:**

- Hardcoded category filter dropdown: `<option value="forex">Forex</option>` etc.
- Group matching done by text-guessing the `path` field
- 100 rows per page with prev/next pagination

**New behavior:**

1. Call `GET /broker-capabilities`
2. Build category filter dropdown **dynamically** from `response.categories` object:
   ```javascript
   // response.categories = {"Forex": ["Majors","Minors"], "Crypto": [...]}
   for (const [cat, subcats] of Object.entries(categories)) {
     // Add <optgroup label="Forex"> with sub-options for each subcategory
   }
   ```
3. Filter table by matching `symbol.category` and `symbol.subcategory` fields
   (exact match, not text guessing)
4. Add new "Subcategory" column to table
5. Add "Trade Mode" badge with color coding:
   - Full → green
   - Long Only → blue
   - Short Only → orange
   - Close Only → yellow
   - Disabled → red (hidden by default — add toggle to show disabled symbols)
6. Add "Filling Modes" column showing `["FOK", "IOC"]` etc.
7. Add toggle: "Show disabled symbols" (trade_mode=0)

---

### Phase H: Status Tab — Account Trade Capability Panel

**File:** `dashboard/js/components.js`

**Current behavior:**

- Shows `terminal.trade_allowed` from `/terminal` endpoint
- Does not show per-account trade permissions

**New behavior:**

- Pull `account_trade_allowed` and `terminal_trade_allowed` from `/broker-capabilities`
- Show a prominent capability badge:
  ```
  ┌─────────────────────────────────────┐
  │  ✅ Terminal Trade Allowed          │
  │  ✅ Account Trade Allowed           │
  │  ⚠️  Execution Policy: BLOCKED     │
  └─────────────────────────────────────┘
  ```
- If either is `false`, show a red warning banner above the Execute tab

---

### Phase I: Execute Tab — Trade Mode Guard in UI

**File:** `dashboard/js/execute-v2.js`

When user selects a symbol that has non-Full trade_mode, display a banner:

```
┌─────────────────────────────────────────────────────┐
│  ⚠️  EURUSD is currently in CLOSE ONLY mode.       │
│      New positions are not allowed by the broker.   │
│      The submit button has been disabled.           │
└─────────────────────────────────────────────────────┘
```

Disable the Submit button for symbols with `trade_mode` of `DISABLED` or `CLOSEONLY`.

---

### Phase J: Prices Tab — Symbol Source Migration

**File:** `dashboard/js/app.js` (the `prices` tab block, line 257-316)

**Current:** Calls `/symbols` (YAML list) to populate the ticker dropdown.

**New:** Calls `/broker-capabilities` and populates ticker dropdown from live MT5 symbols grouped by category. Allows pricing ANY symbol the broker has, not just the ones in YAML.

---

## 6. Dependency Graph (Implementation Order)

```
Phase A (Fix filling mode)
  └─▶ Unblocks current retcode=10030 bug immediately
      No new endpoints needed
      Only trade_mapper.py + close_position.py

Phase D (Extend BrokerSymbol model)
  └─▶ Must precede Phase B

Phase B (New /broker-capabilities endpoint)
  └─▶ Requires Phase D
  └─▶ Enables all dashboard phases

Phase C (Trade mode enforcement)
  └─▶ Can be done in parallel with B
  └─▶ Requires symbol_info already fetched in execute.py (it is)

Phase E (Settings extension)
  └─▶ Can be done in parallel with B, C

Phase F (Dynamic Execute ticker dropdown)
  └─▶ Requires Phase B

Phase G (Dynamic Symbol Browser)
  └─▶ Requires Phase B

Phase H (Status Tab capability panel)
  └─▶ Requires Phase B

Phase I (Execute trade mode guard)
  └─▶ Requires Phase F

Phase J (Prices tab symbol source)
  └─▶ Requires Phase B
```

**Recommended implementation order:**

```
A → D → B → C → E → F → G → H → I → J
```

Or as two parallel tracks after B is done:

```
A (immediate fix)
 ↓
D → B (foundation)
       ↓           ↓           ↓
       C+E         F→I         G→J→H
    (backend)   (execute)   (symbols/prices)
```

---

## 7. New API Endpoints Summary

| Method | Path                           | Description                                                                  |
| ------ | ------------------------------ | ---------------------------------------------------------------------------- |
| `GET`  | `/broker-capabilities`         | Full symbol catalog + categories + account/terminal trade flags. TTL-cached. |
| `POST` | `/broker-capabilities/refresh` | Manually invalidate and re-fetch from MT5                                    |

**Existing endpoints modified:**
| Endpoint | Change |
|----------|--------|
| `POST /execute` | Add trade_mode validation before order construction |
| `POST /pending-order` | Add trade_mode validation + dynamic filling mode |
| `POST /close-position` | Pass symbol_info to build_close_request; add filling mode |
| `GET /broker-symbols` | Add new fields: category, subcategory, filling_mode, supported_filling_modes, trade_mode, volume_step, visible |

**Endpoints that become secondary (but stay):**
| Endpoint | Status |
|----------|--------|
| `GET /symbols` | Keep for backward compatibility (YAML-based, for AI hedge fund strategy use) |

---

## 8. No-Change Decisions

| Item                       | Reason                                                                                                                                                                                             |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config/symbols.yaml`      | Keep as-is. It maps strategy tickers (V75, EURUSD) to MT5 names. Used by the AI hedge fund for `/execute` calls with user-defined tickers. It is a **strategy alias layer**, not a broker catalog. |
| `GET /symbols` endpoint    | Keep for backward compatibility. The AI strategies use it.                                                                                                                                         |
| MT5 worker threading model | No change. All new MT5 calls go through `submit()`.                                                                                                                                                |
| Authentication middleware  | No change.                                                                                                                                                                                         |
| Audit logging              | New endpoint calls should be logged like the others.                                                                                                                                               |

---

## 9. Dashboard UX Changes Summary

```
BEFORE                          AFTER
══════════════════════════════════════════════════════════

Execute Tab:
  Ticker: [YAML dropdown]    →  Ticker: [All MT5 symbols, grouped by MT5 category]
  Buy/Sell: always enabled   →  Buy/Sell: disabled per trade_mode (with tooltip)
  Error at send time         →  Guard shown before submit (preemptive UX)

Symbols Tab:
  Filter: Forex|Crypto|...   →  Filter: [Dynamic from MT5 category tree]
  Category: text-guessed     →  Category: exact from MT5 path
  No filling mode shown       →  Filling modes column: ["FOK", "IOC"]
  No trade mode color         →  Trade mode badge: green/blue/orange/red

Status Tab:
  trade_allowed: text field  →  Capability panel: terminal + account flags

Prices Tab:
  Ticker: [YAML dropdown]    →  Ticker: [All MT5 symbols, grouped by category]
```

---

## 10. Risk Register

| Risk                                                         | Likelihood | Impact | Mitigation                                                             |
| ------------------------------------------------------------ | ---------- | ------ | ---------------------------------------------------------------------- |
| MT5 broker encodes path differently (e.g. `/` vs `\`)        | Medium     | Medium | Normalize path separators during parsing                               |
| Some brokers return empty path for symbols                   | Medium     | Low    | Fallback: use "Other" as category                                      |
| `symbols_get()` returns 1000+ symbols, slow initial load     | Low        | Medium | Cache result, lazy-load on first request                               |
| `filling_mode=0` (RETURN mode) on market order execution     | Low        | High   | RETURN is the implicit fallback but must be verified; test with broker |
| `trade_mode` values may vary by broker (undocumented values) | Low        | Medium | Treat unknown values as "Full" with a warning log                      |
| Breaking change: Execute tab now shows 1000 symbols          | Medium     | Low    | Add a search/filter to ticker dropdown; preserve recent selections     |

---

## 11. Files Affected Summary

### Backend (`app/`)

```
app/
├── mappers/
│   └── trade_mapper.py          MODIFY  — resolve_filling_mode(), update 4 build functions
├── models/
│   ├── broker_symbol.py         MODIFY  — add 6 new fields
│   └── broker_capabilities.py  CREATE  — new response schema
├── routes/
│   ├── broker_symbols.py        MODIFY  — populate new model fields
│   ├── broker_capabilities.py  CREATE  — new endpoint with caching
│   ├── execute.py               MODIFY  — add trade_mode validation
│   ├── pending_order.py         MODIFY  — add trade_mode validation + filling mode
│   └── close_position.py       MODIFY  — pass symbol_info to build_close_request
├── config.py                    MODIFY  — add 2 new env vars
└── main.py                      MODIFY  — register broker_capabilities router
```

### Dashboard (`dashboard/`)

```
dashboard/
└── js/
    ├── app.js                   MODIFY  — prices tab ticker source + capabilities call
    ├── execute-v2.js            MODIFY  — dynamic ticker list, trade mode guard
    ├── symbols-browser.js       MODIFY  — dynamic categories, new columns
    └── components.js            MODIFY  — capability panel in Status tab
```

### Config

```
config/symbols.yaml              NO CHANGE  — keep as strategy alias layer
.env.example                     MODIFY     — document 2 new env vars
```

---

## 12. Testing Plan

### Unit tests (backend)

- `test_resolve_filling_mode`: assert FOK chosen when bit0 set, IOC when bit1 only, RETURN when 0
- `test_trade_mode_validation`: assert rejected payloads for each restricted mode
- `test_broker_capabilities_model`: path parsing into category/subcategory
- `test_capabilities_cache`: TTL expiry and manual refresh invalidation

### Integration tests (backend)

- Mock `mt5.symbols_get()` with realistic symbol list including varied paths
- Assert `/broker-capabilities` returns correctly structured categories
- Assert `/execute` returns 422 with clear message for trade_mode violations

### Manual verification (dashboard)

1. Connect to broker → open Symbols tab → verify groups match MT5 symbol tree
2. Open Execute tab → select a sell-only symbol → Buy button disabled
3. Submit a market order → no more retcode=10030
4. Add new symbol to broker → refresh capabilities → symbol appears in dropdowns without YAML edit

---

_End of plan. This document covers all changes needed for a fully adaptive, broker-agnostic MT5 bridge and dashboard._
