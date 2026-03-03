# Data Model: MT5 Bridge Full Dashboard

**Branch**: `006-mt5-bridge-dashboard` | **Date**: 2026-03-02

---

## 1. New Entities

### 1.1 Position

Represents an open trade on the MT5 terminal.

| Field           | Type                    | Required | Validation                          | Source                    |
| :-------------- | :---------------------- | :------- | :---------------------------------- | :------------------------ | ----- |
| `ticket`        | `int`                   | Yes      | > 0                                 | `mt5.positions_get()`     |
| `symbol`        | `str`                   | Yes      | Non-empty                           | `.symbol`                 |
| `type`          | `Literal["buy","sell"]` | Yes      | Mapped from MT5 int (0=buy, 1=sell) | `.type`                   |
| `volume`        | `float`                 | Yes      | > 0                                 | `.volume`                 |
| `price_open`    | `float`                 | Yes      | > 0                                 | `.price_open`             |
| `price_current` | `float`                 | Yes      | ≥ 0                                 | `.price_current`          |
| `sl`            | `float                  | None`    | No                                  | None if 0.0               | `.sl` |
| `tp`            | `float                  | None`    | No                                  | None if 0.0               | `.tp` |
| `profit`        | `float`                 | Yes      | —                                   | `.profit`                 |
| `swap`          | `float`                 | Yes      | —                                   | `.swap`                   |
| `time`          | `str`                   | Yes      | ISO 8601 UTC                        | `utcfromtimestamp(.time)` |
| `magic`         | `int`                   | Yes      | —                                   | `.magic`                  |
| `comment`       | `str`                   | Yes      | —                                   | `.comment`                |

**File**: `app/models/position.py`

### 1.2 Order (Pending)

Represents an active pending order.

| Field        | Type                                                       | Required | Validation          | Source             |
| :----------- | :--------------------------------------------------------- | :------- | :------------------ | :----------------- | ----- |
| `ticket`     | `int`                                                      | Yes      | > 0                 | `mt5.orders_get()` |
| `symbol`     | `str`                                                      | Yes      | Non-empty           | `.symbol`          |
| `type`       | `Literal["buy_limit","sell_limit","buy_stop","sell_stop"]` | Yes      | Mapped from MT5 int | `.type`            |
| `volume`     | `float`                                                    | Yes      | > 0                 | `.volume`          |
| `price`      | `float`                                                    | Yes      | > 0                 | `.price_open`      |
| `sl`         | `float                                                     | None`    | No                  | None if 0.0        | `.sl` |
| `tp`         | `float                                                     | None`    | No                  | None if 0.0        | `.tp` |
| `time_setup` | `str`                                                      | Yes      | ISO 8601 UTC        | `.time_setup`      |
| `magic`      | `int`                                                      | Yes      | —                   | `.magic`           |

**File**: `app/models/order.py`

### 1.3 AccountInfo

Represents the trader's account financial state.

| Field         | Type    | Required | Validation | Source               |
| :------------ | :------ | :------- | :--------- | :------------------- |
| `login`       | `int`   | Yes      | > 0        | `mt5.account_info()` |
| `server`      | `str`   | Yes      | Non-empty  | `.server`            |
| `balance`     | `float` | Yes      | ≥ 0        | `.balance`           |
| `equity`      | `float` | Yes      | —          | `.equity`            |
| `margin`      | `float` | Yes      | ≥ 0        | `.margin`            |
| `free_margin` | `float` | Yes      | —          | `.free_margin`       |
| `profit`      | `float` | Yes      | —          | `.profit`            |
| `currency`    | `str`   | Yes      | Non-empty  | `.currency`          |
| `leverage`    | `int`   | Yes      | > 0        | `.leverage`          |

**File**: `app/models/account.py`

### 1.4 TickPrice

A single price snapshot for a symbol.

| Field    | Type    | Required | Validation | Source                       |
| :------- | :------ | :------- | :--------- | :--------------------------- |
| `ticker` | `str`   | Yes      | Non-empty  | User-facing ticker           |
| `bid`    | `float` | Yes      | > 0        | `mt5.symbol_info_tick().bid` |
| `ask`    | `float` | Yes      | > 0        | `mt5.symbol_info_tick().ask` |
| `spread` | `float` | Yes      | ≥ 0        | Computed `ask - bid`         |
| `time`   | `str`   | Yes      | ISO 8601   | `utcfromtimestamp(.time)`    |

**File**: `app/models/tick.py`

### 1.5 TerminalInfo

MT5 terminal diagnostic information.

| Field           | Type   | Required | Validation | Source                |
| :-------------- | :----- | :------- | :--------- | :-------------------- |
| `build`         | `int`  | Yes      | > 0        | `mt5.terminal_info()` |
| `name`          | `str`  | Yes      | Non-empty  | `.name`               |
| `path`          | `str`  | Yes      | Non-empty  | `.path`               |
| `data_path`     | `str`  | Yes      | Non-empty  | `.data_path`          |
| `connected`     | `bool` | Yes      | —          | `.connected`          |
| `trade_allowed` | `bool` | Yes      | —          | `.trade_allowed`      |

**File**: `app/models/terminal.py`

### 1.6 Deal (Historical Fill)

Represents a completed transaction in trade history.

| Field          | Type                          | Required | Validation | Source                    |
| :------------- | :---------------------------- | :------- | :--------- | :------------------------ |
| `ticket`       | `int`                         | Yes      | > 0        | `mt5.history_deals_get()` |
| `order_ticket` | `int`                         | Yes      | ≥ 0        | `.order`                  |
| `position_id`  | `int`                         | Yes      | ≥ 0        | `.position_id`            |
| `symbol`       | `str`                         | Yes      | Non-empty  | `.symbol`                 |
| `type`         | `str`                         | Yes      | Mapped     | `.type`                   |
| `entry`        | `Literal["in","out","inout"]` | Yes      | Mapped     | `.entry`                  |
| `volume`       | `float`                       | Yes      | > 0        | `.volume`                 |
| `price`        | `float`                       | Yes      | ≥ 0        | `.price`                  |
| `profit`       | `float`                       | Yes      | —          | `.profit`                 |
| `swap`         | `float`                       | Yes      | —          | `.swap`                   |
| `commission`   | `float`                       | Yes      | —          | `.commission`             |
| `fee`          | `float`                       | Yes      | —          | `.fee`                    |
| `time`         | `str`                         | Yes      | ISO 8601   | `utcfromtimestamp(.time)` |
| `magic`        | `int`                         | Yes      | —          | `.magic`                  |

**File**: `app/models/deal.py`

### 1.7 HistoricalOrder

An order that has reached a terminal state.

| Field        | Type                                                 | Required | Validation | Source                     |
| :----------- | :--------------------------------------------------- | :------- | :--------- | :------------------------- | ----- |
| `ticket`     | `int`                                                | Yes      | > 0        | `mt5.history_orders_get()` |
| `symbol`     | `str`                                                | Yes      | Non-empty  | `.symbol`                  |
| `type`       | `str`                                                | Yes      | Mapped     | `.type`                    |
| `volume`     | `float`                                              | Yes      | > 0        | `.volume_current`          |
| `price`      | `float`                                              | Yes      | ≥ 0        | `.price_open`              |
| `sl`         | `float                                               | None`    | No         | None if 0                  | `.sl` |
| `tp`         | `float                                               | None`    | No         | None if 0                  | `.tp` |
| `state`      | `Literal["filled","cancelled","expired","rejected"]` | Yes      | Mapped     | `.state`                   |
| `time_setup` | `str`                                                | Yes      | ISO 8601   | `.time_setup`              |
| `time_done`  | `str`                                                | Yes      | ISO 8601   | `.time_done`               |
| `magic`      | `int`                                                | Yes      | —          | `.magic`                   |

**File**: `app/models/historical_order.py`

### 1.8 BrokerSymbol

A tradable instrument from the broker's catalog.

| Field           | Type    | Required | Validation | Source                    |
| :-------------- | :------ | :------- | :--------- | :------------------------ |
| `name`          | `str`   | Yes      | Non-empty  | `mt5.symbols_get()`       |
| `description`   | `str`   | Yes      | —          | `.description`            |
| `path`          | `str`   | Yes      | —          | `.path`                   |
| `spread`        | `int`   | Yes      | ≥ 0        | `.spread`                 |
| `digits`        | `int`   | Yes      | ≥ 0        | `.digits`                 |
| `volume_min`    | `float` | Yes      | > 0        | `.volume_min`             |
| `volume_max`    | `float` | Yes      | > 0        | `.volume_max`             |
| `trade_mode`    | `str`   | Yes      | —          | Mapped from `.trade_mode` |
| `is_configured` | `bool`  | Yes      | —          | Cross-ref `symbol_map`    |

**File**: `app/models/broker_symbol.py`

---

## 2. Modified Entities

### 2.1 TradeRequest (Enhanced)

Add two optional fields for stop-loss/take-profit on market orders.

| New Field | Type   | Default | Validation |
| :-------- | :----- | :------ | :--------- | ----------- |
| `sl`      | `float | None`   | `None`     | If set, > 0 |
| `tp`      | `float | None`   | `None`     | If set, > 0 |

**File**: `app/models/trade.py` (modify existing)

---

## 3. Request/Response Models (Write Operations)

### 3.1 ClosePositionRequest

| Field    | Type   | Required | Validation |
| :------- | :----- | :------- | :--------- | ------------------------------ |
| `ticket` | `int`  | Yes      | > 0        |
| `volume` | `float | None`    | No         | If set, > 0; None = full close |

**File**: `app/models/close_position.py`

### 3.2 ModifySLTPRequest

| Field | Type   | Required | Validation |
| :---- | :----- | :------- | :--------- | ----------- |
| `sl`  | `float | None`    | No         | If set, > 0 |
| `tp`  | `float | None`    | No         | If set, > 0 |

**File**: `app/models/modify_sltp.py`

### 3.3 ModifyOrderRequest

| Field   | Type   | Required | Validation |
| :------ | :----- | :------- | :--------- | ----------- |
| `price` | `float | None`    | No         | If set, > 0 |
| `sl`    | `float | None`    | No         | If set, > 0 |
| `tp`    | `float | None`    | No         | If set, > 0 |

**File**: `app/models/modify_order.py`

### 3.4 PendingOrderRequest

| Field     | Type                                                       | Required | Validation    |
| :-------- | :--------------------------------------------------------- | :------- | :------------ | ----------- |
| `ticker`  | `str`                                                      | Yes      | In symbol map |
| `type`    | `Literal["buy_limit","sell_limit","buy_stop","sell_stop"]` | Yes      | Valid enum    |
| `volume`  | `float`                                                    | Yes      | > 0           |
| `price`   | `float`                                                    | Yes      | > 0           |
| `sl`      | `float                                                     | None`    | No            | If set, > 0 |
| `tp`      | `float                                                     | None`    | No            | If set, > 0 |
| `comment` | `str`                                                      | No       | Max 255 chars |

**File**: `app/models/pending_order.py`

### 3.5 OrderCheckRequest / OrderCheckResponse

**Request**: Reuses `PendingOrderRequest` fields.

**Response**:

| Field     | Type    | Required | Notes                        |
| :-------- | :------ | :------- | :--------------------------- |
| `valid`   | `bool`  | Yes      | Whether `order_check` passes |
| `margin`  | `float` | Yes      | Required margin              |
| `profit`  | `float` | Yes      | Estimated profit             |
| `equity`  | `float` | Yes      | Post-trade equity projection |
| `comment` | `str`   | Yes      | MT5 comment                  |
| `retcode` | `int`   | Yes      | MT5 return code              |

**File**: `app/models/order_check.py`

---

## 4. Entity Relationships

```
Account ──1:N──▶ Position ──history──▶ Deal
                 Position ──modify──▶ ModifySLTPRequest
                 Position ──close──▶ ClosePositionRequest

Account ──1:N──▶ Order ──history──▶ HistoricalOrder
                 Order ──modify──▶ ModifyOrderRequest
                 Order ──cancel──▶ (DELETE by ticket)

BrokerSymbol ──config──▶ SymbolInfo (existing, from symbols.yaml)

PendingOrderRequest ──validates──▶ OrderCheckResponse
PendingOrderRequest ──places──▶ Order
```

---

## 5. New Mapper Functions

### 5.1 Position Mapper (`app/mappers/position_mapper.py`)

- `map_mt5_position(pos) → Position` — Convert MT5 position tuple to Pydantic model.

### 5.2 Order Mapper (`app/mappers/order_mapper.py`)

- `map_mt5_order(ord) → Order` — Convert MT5 order tuple to Pydantic model.
- `pending_type_to_mt5_const(type_str) → int` — Map string type to MT5 order type constant.

### 5.3 Account Mapper (`app/mappers/account_mapper.py`)

- `map_mt5_account(acc) → AccountInfo` — Convert MT5 account info to Pydantic model.

### 5.4 History Mapper (`app/mappers/history_mapper.py`)

- `map_mt5_deal(deal) → Deal` — Convert MT5 deal to Pydantic model.
- `map_mt5_historical_order(ord) → HistoricalOrder` — Convert MT5 historical order to Pydantic model.

### 5.5 Trade Mapper Enhancement (`app/mappers/trade_mapper.py`)

- `build_close_request(position, volume, symbol_info) → dict` — Build `TRADE_ACTION_DEAL` counter-order.
- `build_modify_sltp_request(ticket, sl, tp) → dict` — Build `TRADE_ACTION_SLTP` request.
- `build_pending_order_request(req, mt5_symbol, symbol_info) → dict` — Build `TRADE_ACTION_PENDING` request.
- `build_modify_order_request(ticket, price, sl, tp) → dict` — Build `TRADE_ACTION_MODIFY` request.
- `build_cancel_order_request(ticket) → dict` — Build `TRADE_ACTION_REMOVE` request.
