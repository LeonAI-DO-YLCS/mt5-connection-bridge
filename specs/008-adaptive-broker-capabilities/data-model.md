# Data Model: Adaptive Broker Capabilities

**Feature**: 008-adaptive-broker-capabilities
**Date**: 2026-03-02
**Source**: `specs/008-adaptive-broker-capabilities/spec.md` + `research.md`

---

## Entity Overview

```
┌───────────────────────────┐
│      BrokerCapabilities   │◄─── Cached in memory on bridge
│  account_trade_allowed    │
│  terminal_trade_allowed   │
│  symbol_count             │
│  fetched_at               │
│  symbols[]                │──── 1..* ──► BrokerSymbol
│  categories{}             │──── 1..* ──► CategoryTree
└───────────────────────────┘

┌───────────────────────────┐
│         BrokerSymbol      │
│  name                     │
│  description              │
│  path (raw MT5)           │
│  category                 │◄── derived from path segment[0]
│  subcategory              │◄── derived from path segment[1]
│  trade_mode (int)         │
│  trade_mode_label (str)   │◄── mapped from trade_mode int
│  filling_mode (int bitmask│
│  supported_filling_modes[]│◄── decoded from bitmask
│  digits                   │
│  volume_min               │
│  volume_max               │
│  volume_step              │
│  spread                   │
│  visible                  │
│  is_configured            │◄── cross-referenced with symbol_map
└───────────────────────────┘

┌───────────────────────────┐
│       CategoryTree        │
│  {category: [subcategory]}│◄── Dict built from all symbol paths
└───────────────────────────┘

┌───────────────────────────┐
│       TradeRequest        │  (EXISTING — extended)
│  ticker                   │◄── YAML alias (existing)
│  action                   │
│  quantity                 │
│  current_price            │
│  multi_trade_mode         │
│  sl                       │
│  tp                       │
│  mt5_symbol_direct (NEW)  │◄── Optional: bypasses YAML lookup
└───────────────────────────┘
```

---

## Pydantic Models (Backend)

### `BrokerSymbol` (extend existing `app/models/broker_symbol.py`)

| Field                     | Type        | Validation        | Source                          |
| ------------------------- | ----------- | ----------------- | ------------------------------- |
| `name`                    | `str`       | non-empty         | `symbol_info.name`              |
| `description`             | `str`       | —                 | `symbol_info.description`       |
| `path`                    | `str`       | —                 | `symbol_info.path`              |
| `category`                | `str`       | default `"Other"` | `path.split("\\")[0]`           |
| `subcategory`             | `str`       | default `""`      | `path.split("\\")[1]` if exists |
| `trade_mode`              | `int`       | 0–4               | `symbol_info.trade_mode`        |
| `trade_mode_label`        | `str`       | —                 | mapped from `trade_mode`        |
| `filling_mode`            | `int`       | ≥0                | `symbol_info.filling_mode`      |
| `supported_filling_modes` | `list[str]` | —                 | decoded from bitmask            |
| `digits`                  | `int`       | ≥0                | `symbol_info.digits`            |
| `volume_min`              | `float`     | ≥0                | `symbol_info.volume_min`        |
| `volume_max`              | `float`     | ≥volume_min       | `symbol_info.volume_max`        |
| `volume_step`             | `float`     | ≥0                | `symbol_info.volume_step`       |
| `spread`                  | `int`       | ≥0                | `symbol_info.spread`            |
| `visible`                 | `bool`      | —                 | `symbol_info.visible`           |
| `is_configured`           | `bool`      | —                 | `name in symbol_map`            |

### `BrokerCapabilities` (new `app/models/broker_capabilities.py`)

| Field                    | Type                   | Description                             |
| ------------------------ | ---------------------- | --------------------------------------- |
| `account_trade_allowed`  | `bool`                 | From `account_info.trade_allowed`       |
| `terminal_trade_allowed` | `bool`                 | From `terminal_info.trade_allowed`      |
| `symbol_count`           | `int`                  | Total symbols returned                  |
| `symbols`                | `list[BrokerSymbol]`   | Full symbol catalog                     |
| `categories`             | `dict[str, list[str]]` | `{category: [subcategory, ...]}` sorted |
| `fetched_at`             | `str`                  | ISO-8601 UTC timestamp of last fetch    |

### `TradeRequest` (extend existing `app/models/trade.py`)

| Field               | Type           | Default  | Description                                          |
| ------------------- | -------------- | -------- | ---------------------------------------------------- |
| `ticker`            | `str`          | required | YAML alias (existing behavior)                       |
| `action`            | `Literal[...]` | required | buy/sell/short/cover                                 |
| `quantity`          | `float`        | required | Volume                                               |
| `current_price`     | `float`        | required | Slippage protection price                            |
| `multi_trade_mode`  | `bool`         | `False`  | Allow parallel submissions                           |
| `sl`                | `float\|None`  | `None`   | Stop loss                                            |
| `tp`                | `float\|None`  | `None`   | Take profit                                          |
| `mt5_symbol_direct` | `str\|None`    | `None`   | **NEW**: Bypass YAML lookup; use raw MT5 symbol name |

### `Settings` (extend existing `app/config.py`)

| Env Var                          | Type   | Default | Description                                  |
| -------------------------------- | ------ | ------- | -------------------------------------------- |
| `CAPABILITIES_CACHE_TTL_SECONDS` | `int`  | `60`    | How long broker catalog is cached            |
| `AUTO_SELECT_SYMBOLS`            | `bool` | `True`  | Auto-add symbols to MT5 Market Watch on scan |

---

## Trade Mode Mapping Table

| MT5 Value | Label          | Buy Allowed | Sell Allowed | Close Allowed |
| --------- | -------------- | ----------- | ------------ | ------------- |
| 0         | Disabled       | ❌          | ❌           | ❌            |
| 1         | Long Only      | ✅          | ❌           | ✅            |
| 2         | Short Only     | ❌          | ✅           | ✅            |
| 3         | Close Only     | ❌          | ❌           | ✅            |
| 4         | Full           | ✅          | ✅           | ✅            |
| unknown   | Full (assumed) | ✅          | ✅           | ✅            |

---

## Filling Mode Bitmask Decoding

| Bitmask  | FOK supported | IOC supported | Selected mode |
| -------- | ------------- | ------------- | ------------- |
| 0b00 (0) | ❌            | ❌            | RETURN (0)    |
| 0b01 (1) | ✅            | ❌            | FOK (1)       |
| 0b10 (2) | ❌            | ✅            | IOC (2)       |
| 0b11 (3) | ✅            | ✅            | FOK (1)       |

`supported_filling_modes` field decodes the bitmask to human labels:

- Bit 0 set → include `"FOK"`
- Bit 1 set → include `"IOC"`
- Neither → include `"RETURN"`

---

## State Transitions — Capabilities Cache

```
            bridge startup / MT5 reconnect
                         │
                         ▼
                ┌────────────────┐
                │    EMPTY       │
                └───────┬────────┘
                        │ first request or POST /broker-capabilities/refresh
                        ▼
                ┌────────────────┐
                │    FETCHING    │  (blocks concurrent requests until done)
                └───────┬────────┘
                        │ symbols_get() + terminal_info() + account_info()
                        ▼
                ┌────────────────┐
                │    FRESH       │  TTL = CAPABILITIES_CACHE_TTL_SECONDS
                └───────┬────────┘
                        │ TTL elapsed
                        ▼
                ┌────────────────┐
                │    STALE       │  Still served but next request triggers refresh
                └───────┬────────┘
                        │ MT5 worker reconnect event OR POST /refresh
                        ▼
                ┌────────────────┐
                │    EMPTY       │  → FETCHING on next request
                └────────────────┘
```

---

## Validation Rules

### Trade Mode Validation (executed inside MT5 worker)

```python
# action: "buy" | "sell" | "short" | "cover"
# pending type: "buy_limit" | "buy_stop" | "sell_limit" | "sell_stop"

BUY_ACTIONS    = {"buy", "cover", "buy_limit", "buy_stop"}
SELL_ACTIONS   = {"sell", "short", "sell_limit", "sell_stop"}

if trade_mode == 0:   # DISABLED
    error = "Symbol trading is disabled by the broker."
elif trade_mode == 1 and action in SELL_ACTIONS:   # LONG ONLY
    error = f"Symbol {symbol} only allows long (buy) trades."
elif trade_mode == 2 and action in BUY_ACTIONS:    # SHORT ONLY
    error = f"Symbol {symbol} only allows short (sell) trades."
elif trade_mode == 3:  # CLOSE ONLY
    error = f"Symbol {symbol} is in close-only mode. No new positions allowed."
```

### Filling Mode Resolution

```python
def resolve_filling_mode(symbol_info) -> int:
    bitmask = int(getattr(symbol_info, "filling_mode", 0) or 0)
    FOK    = mt5_const("ORDER_FILLING_FOK", 1)
    IOC    = mt5_const("ORDER_FILLING_IOC", 2)
    RETURN = mt5_const("ORDER_FILLING_RETURN", 0)
    if bitmask & 1:   return FOK
    if bitmask & 2:   return IOC
    return RETURN
```

### Path Parsing

```python
def parse_symbol_path(path: str) -> tuple[str, str]:
    """Returns (category, subcategory). Normalizes \ and / separators."""
    if not path:
        return ("Other", "")
    segments = path.replace("\\", "/").split("/")
    category    = segments[0] if len(segments) > 0 else "Other"
    subcategory = segments[1] if len(segments) > 1 else ""
    return (category, subcategory)
```
