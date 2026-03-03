# Quickstart: Adaptive Broker Capabilities

**Feature**: 008-adaptive-broker-capabilities
**For**: Developers implementing or reviewing this feature

---

## What This Feature Does

Replaces four areas of hardcoded broker assumptions in the MT5 Bridge with runtime-detected values:

1. **Order filling mode** — previously hardcoded to IOC everywhere; now resolved per symbol from the MT5 filling_mode bitmask.
2. **Symbol catalog** — previously only `config/symbols.yaml` entries shown in dashboard; now all broker symbols visible grouped by MT5 category.
3. **Symbol categories** — previously hardcoded dropdown strings; now derived from actual MT5 symbol path hierarchy.
4. **Trade direction enforcement** — previously no check; now broker-enforced constraints (long-only, short-only, close-only, disabled) validated before order submission.

---

## Implementation Sequence

Work in this order (each step unblocks the next):

```
Step 1: resolve_filling_mode()         ← trade_mapper.py (pure Python, no new endpoints)
Step 2: build_close_request() fix      ← trade_mapper.py + close_position.py
Step 3: BrokerSymbol model extension   ← models/broker_symbol.py
Step 4: BrokerCapabilities model       ← models/broker_capabilities.py (new file)
Step 5: broker_capabilities.py route   ← routes/broker_capabilities.py (new file)
Step 6: Register route in main.py
Step 7: Trade mode validation          ← routes/execute.py + routes/pending_order.py
Step 8: TradeRequest mt5_symbol_direct ← models/trade.py + routes/execute.py
Step 9: Settings extension             ← config.py (.env.example)
Step 10: broker_symbols.py extension   ← routes/broker_symbols.py (populate new fields)
Step 11: Dashboard Execute tab         ← dashboard/js/execute-v2.js
Step 12: Dashboard Symbols Browser     ← dashboard/js/symbols-browser.js
Step 13: Dashboard Prices tab          ← dashboard/js/app.js
Step 14: Dashboard Status tab          ← dashboard/js/components.js (or app.js)
Step 15: Tests                         ← tests/unit/, tests/contract/, tests/integration/
```

---

## Key Files at a Glance

### Backend — Modified

| File                           | What changes                                                                                                                     |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| `app/mappers/trade_mapper.py`  | + `resolve_filling_mode()` function; use it in `build_order_request()`, `build_pending_order_request()`, `build_close_request()` |
| `app/models/broker_symbol.py`  | + 7 new fields: category, subcategory, filling_mode, supported_filling_modes, trade_mode_label, volume_step, visible             |
| `app/models/trade.py`          | + `mt5_symbol_direct: str                                                                                                        | None = None` field |
| `app/routes/execute.py`        | + trade_mode validation block inside `_execute_in_worker()`; + `mt5_symbol_direct` bypass                                        |
| `app/routes/pending_order.py`  | + trade_mode validation block inside `_execute_in_worker()`                                                                      |
| `app/routes/close_position.py` | Pass `symbol_info` to `build_close_request()`                                                                                    |
| `app/routes/broker_symbols.py` | Populate new BrokerSymbol fields                                                                                                 |
| `app/config.py`                | + 2 new env vars in Settings                                                                                                     |
| `app/main.py`                  | Register `broker_capabilities` router                                                                                            |

### Backend — New Files

| File                                | What it is                                                       |
| ----------------------------------- | ---------------------------------------------------------------- |
| `app/models/broker_capabilities.py` | `BrokerCapabilities` Pydantic response model                     |
| `app/routes/broker_capabilities.py` | `GET /broker-capabilities` + `POST /broker-capabilities/refresh` |

### Frontend — Modified

| File                                     | What changes                                                                                        |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `dashboard/js/execute-v2.js`             | Fetch from `/broker-capabilities`; `<optgroup>` ticker dropdown; trade_mode guard                   |
| `dashboard/js/symbols-browser.js`        | Dynamic category filter; new table columns (category, subcategory, trade mode badge, filling modes) |
| `dashboard/js/app.js`                    | Prices tab fetches symbols from `/broker-capabilities`                                              |
| `dashboard/js/components.js` (or app.js) | Status tab capability panel                                                                         |

---

## Critical Implementation Details

### 1. `resolve_filling_mode` — The Priority Rule

```
filling_mode bitmask = 0  → use RETURN (ORDER_FILLING_RETURN = 0)
bit 0 set (bitmask & 1)   → use FOK   (ORDER_FILLING_FOK   = 1)   ← highest priority
bit 1 set (bitmask & 2)   → use IOC   (ORDER_FILLING_IOC   = 2)
```

FOK is preferred because it provides cleaner all-or-nothing fill semantics. IOC is the fallback. RETURN is the universal fallback.

### 2. Trade Mode Validation — Actions to Block

```
action strings treated as BUY: "buy", "cover", "buy_limit", "buy_stop"
action strings treated as SELL: "sell", "short", "sell_limit", "sell_stop"

trade_mode 0 (DISABLED)   → block ALL
trade_mode 1 (LONG ONLY)  → block SELL actions
trade_mode 2 (SHORT ONLY) → block BUY actions
trade_mode 3 (CLOSE ONLY) → block ALL (only close_position allowed)
trade_mode 4 (FULL)       → allow ALL
unknown value             → allow ALL (log warning)
```

### 3. Cache Module — Thread Safety

The capabilities cache (`_capabilities_cache`) is read by multiple concurrent async requests. Use `threading.Lock()` around cache reads and writes (consistent with the existing pattern in `close_position.py` and `positions.py`).

### 4. `mt5_symbol_direct` Bypass — Only for Dashboard

When `mt5_symbol_direct` is present in `TradeRequest`, skip the `symbol_map` lookup and use the provided string as `mt5_symbol`. The `ticker` field is still logged in the audit trail.

### 5. Dashboard: Single Source of Truth

After this feature, the dashboard calls `/broker-capabilities` once per tab open (on render) and caches the result in a JS module-level variable. All subsequent UI interactions (dropdown filtering, trade mode checks, category filters) use this in-memory JS object — no additional API calls per user action.

---

## Tests to Write

### Unit (tests/unit/)

```
test_resolve_filling_mode.py
  - bitmask=0    → RETURN
  - bitmask=1    → FOK
  - bitmask=2    → IOC
  - bitmask=3    → FOK (FOK wins over IOC)
  - symbol_info missing filling_mode attr → RETURN (safe default)

test_trade_mode_validation.py
  - trade_mode=0, action="buy"   → error
  - trade_mode=0, action="sell"  → error
  - trade_mode=1, action="sell"  → error
  - trade_mode=1, action="buy"   → pass
  - trade_mode=2, action="buy"   → error
  - trade_mode=2, action="sell"  → pass
  - trade_mode=3, action="buy"   → error
  - trade_mode=3, action="sell"  → error
  - trade_mode=4, action="buy"   → pass
  - trade_mode=4, action="sell"  → pass
  - trade_mode=99 (unknown)      → pass (log warning)

test_parse_symbol_path.py
  - "Forex\\Majors\\EURUSD"        → ("Forex", "Majors")
  - "Forex/Majors/EURUSD"          → ("Forex", "Majors")  ← mixed separator
  - "Crypto"                       → ("Crypto", "")
  - ""                             → ("Other", "")
  - None/missing                   → ("Other", "")

test_broker_capabilities_model.py
  - BrokerCapabilities built from mock symbol list
  - categories dict correctly aggregated and sorted
  - is_configured cross-reference correct
```

### Contract (tests/contract/)

```
test_broker_capabilities_contract.py
  - GET /broker-capabilities returns schema matching BrokerCapabilities model
  - POST /broker-capabilities/refresh returns success response
  - GET /broker-symbols response includes new fields (category, subcategory, etc.)

test_execute_trademode_contract.py
  - POST /execute with long-only symbol + sell action → 422
  - POST /execute with mt5_symbol_direct → resolves symbol correctly
```

### Integration (tests/integration/)

```
test_capabilities_cache.py
  - Cache is populated on first request
  - TTL: second request within TTL returns cached fetched_at (not re-fetched)
  - POST /refresh invalidates cache → next GET re-fetches
  - MT5 worker reconnect event invalidates cache
```

---

## Environment Variables

Add these to `.env.example`:

```bash
# Broker capabilities cache TTL in seconds (default: 60)
CAPABILITIES_CACHE_TTL_SECONDS=60

# Automatically select symbols in MT5 Market Watch when scanning (default: true)
AUTO_SELECT_SYMBOLS=true
```

---

## Dashboard UX Summary

### Execute Tab — After Feature

```
┌─────────────────────────────────────────────────┐
│  Symbol: [search input]                         │
│           ┌────────────────────────────┐        │
│           │ Forex                      │        │
│           │   EURUSD - Euro/US Dollar  │        │
│           │   GBPUSD - Pound/US Dollar │        │
│           │ Volatility Indices         │        │
│           │   Volatility 75 Index      │        │
│           └────────────────────────────┘        │
│                                                 │
│  Direction:   [🟢 BUY]  [⚠️ SELL — Long Only]  │
│  Quantity:    [0.01]                            │
│  [Submit — disabled: close-only mode]           │
│                                                 │
│  ⚠️  This symbol is in CLOSE ONLY mode.         │
│     No new positions allowed.                   │
└─────────────────────────────────────────────────┘
```

### Symbols Browser — After Feature

```
Category: [Forex ▾]  Sub: [Majors ▾]  Search: [___]  [☑ Show disabled]

Name      | Description          | Category | Sub    | Trade Mode  | Filling
--------- |----------------------|----------|--------|-------------|--------
EURUSD    | Euro vs US Dollar    | Forex    | Majors | 🟢 Full     | FOK, IOC
VOLATILITY| Volatility 75 Index  | Vol Idx  | Cont.  | 🟢 Full     | RETURN
XAGUSD    | Silver vs US Dollar  | Metals   | Silver | 🟠 Long Only| FOK
```
