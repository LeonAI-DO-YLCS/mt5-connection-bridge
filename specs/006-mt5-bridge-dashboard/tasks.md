# Tasks: MT5 Bridge Full Dashboard

**Input**: Design documents from `specs/006-mt5-bridge-dashboard/`
**Prerequisites**: plan.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅ | quickstart.md ✅

---

## User Story Map

| Story | Phase                         | Goal                                                         | Priority      |
| :---- | :---------------------------- | :----------------------------------------------------------- | :------------ |
| US1   | Phase 0 — Foundations         | Shared models, mappers, enhanced TradeRequest, safety layers | P1 (blocking) |
| US2   | Phase 1 — Visibility          | Read-only: account, positions, orders, tick, terminal        | P1            |
| US3   | Phase 2 — Management          | Close, cancel, modify positions/orders                       | P2            |
| US4   | Phase 3 — Execution           | Pending orders, pre-validation, rebuilt Execute tab          | P2            |
| US5   | Phase 4 — History & Discovery | Deal/order history, broker symbol browser                    | P3            |

---

## Phase 1: Setup

> **Goal**: Prepare the project structure for all new files. No logic yet — just empty directories and skeleton files so subsequent tasks have clear targets.

- [x] T001 Create new model files as empty modules: `app/models/position.py`, `app/models/order.py`, `app/models/account.py`, `app/models/tick.py`, `app/models/terminal.py`, `app/models/deal.py`, `app/models/historical_order.py`, `app/models/broker_symbol.py`, `app/models/close_position.py`, `app/models/modify_sltp.py`, `app/models/modify_order.py`, `app/models/pending_order.py`, `app/models/order_check.py`
- [x] T002 Create new mapper files as empty modules: `app/mappers/position_mapper.py`, `app/mappers/order_mapper.py`, `app/mappers/account_mapper.py`, `app/mappers/history_mapper.py`
- [x] T003 Create new route files as empty modules: `app/routes/account.py`, `app/routes/positions.py`, `app/routes/orders.py`, `app/routes/tick.py`, `app/routes/terminal.py`, `app/routes/close_position.py`, `app/routes/pending_order.py`, `app/routes/order_check.py`, `app/routes/history.py`, `app/routes/broker_symbols.py`

---

## Phase 2: Foundational — US1 (Foundations)

> **Goal**: Build all shared Pydantic models and mapper functions that every subsequent phase depends on. Nothing works without these.
> **Test Criteria**: `pytest tests/unit/test_position_mapper.py tests/unit/test_order_mapper.py tests/unit/test_account_mapper.py tests/unit/test_trade_mapper_v2.py` — all pass.

### Models (all parallelizable — different files, no dependencies)

- [x] T004 [P] [US1] Create `Position` Pydantic model in `app/models/position.py`. Fields: `ticket` (int, >0), `symbol` (str), `type` (Literal["buy","sell"]), `volume` (float, >0), `price_open` (float), `price_current` (float), `sl` (float|None), `tp` (float|None), `profit` (float), `swap` (float), `time` (str, ISO 8601), `magic` (int), `comment` (str). Follow the exact pattern from `app/models/health.py` — docstring, `from __future__ import annotations`, `BaseModel` import.
- [x] T005 [P] [US1] Create `Order` Pydantic model in `app/models/order.py`. Fields: `ticket` (int, >0), `symbol` (str), `type` (Literal["buy_limit","sell_limit","buy_stop","sell_stop"]), `volume` (float, >0), `price` (float, >0), `sl` (float|None), `tp` (float|None), `time_setup` (str, ISO 8601), `magic` (int).
- [x] T006 [P] [US1] Create `AccountInfo` Pydantic model in `app/models/account.py`. Fields: `login` (int), `server` (str), `balance` (float), `equity` (float), `margin` (float), `free_margin` (float), `profit` (float), `currency` (str), `leverage` (int).
- [x] T007 [P] [US1] Create `TickPrice` Pydantic model in `app/models/tick.py`. Fields: `ticker` (str), `bid` (float), `ask` (float), `spread` (float), `time` (str).
- [x] T008 [P] [US1] Create `TerminalInfo` Pydantic model in `app/models/terminal.py`. Fields: `build` (int), `name` (str), `path` (str), `data_path` (str), `connected` (bool), `trade_allowed` (bool).
- [x] T009 [P] [US1] Create `Deal` Pydantic model in `app/models/deal.py`. Fields: `ticket` (int), `order_ticket` (int), `position_id` (int), `symbol` (str), `type` (str), `entry` (Literal["in","out","inout"]), `volume` (float), `price` (float), `profit` (float), `swap` (float), `commission` (float), `fee` (float), `time` (str), `magic` (int).
- [x] T010 [P] [US1] Create `HistoricalOrder` Pydantic model in `app/models/historical_order.py`. Fields: `ticket` (int), `symbol` (str), `type` (str), `volume` (float), `price` (float), `sl` (float|None), `tp` (float|None), `state` (Literal["filled","cancelled","expired","rejected"]), `time_setup` (str), `time_done` (str), `magic` (int).
- [x] T011 [P] [US1] Create `BrokerSymbol` Pydantic model in `app/models/broker_symbol.py`. Fields: `name` (str), `description` (str), `path` (str), `spread` (int), `digits` (int), `volume_min` (float), `volume_max` (float), `trade_mode` (str), `is_configured` (bool).
- [x] T012 [P] [US1] Create `ClosePositionRequest` Pydantic model in `app/models/close_position.py`. Fields: `ticket` (int, >0), `volume` (float|None, default None — None means full close).
- [x] T013 [P] [US1] Create `ModifySLTPRequest` Pydantic model in `app/models/modify_sltp.py`. Fields: `sl` (float|None), `tp` (float|None).
- [x] T014 [P] [US1] Create `ModifyOrderRequest` Pydantic model in `app/models/modify_order.py`. Fields: `price` (float|None), `sl` (float|None), `tp` (float|None).
- [x] T015 [P] [US1] Create `PendingOrderRequest` Pydantic model in `app/models/pending_order.py`. Fields: `ticker` (str), `type` (Literal["buy_limit","sell_limit","buy_stop","sell_stop"]), `volume` (float, >0), `price` (float, >0), `sl` (float|None), `tp` (float|None), `comment` (str, default "").
- [x] T016 [P] [US1] Create `OrderCheckResponse` Pydantic model in `app/models/order_check.py`. Fields: `valid` (bool), `margin` (float), `profit` (float), `equity` (float), `comment` (str), `retcode` (int).

### Enhanced TradeRequest

- [x] T017 [US1] Add `sl: float | None = Field(default=None, description="Optional stop loss price")` and `tp: float | None = Field(default=None, description="Optional take profit price")` to the existing `TradeRequest` class in `app/models/trade.py`. Insert them after the `multi_trade_mode` field. This is a non-breaking change since both default to `None`.

### Update Model Exports

- [x] T018 [US1] Update `app/models/__init__.py` to import and export all 13 new models. Add each new model to the `from .xxx import Xxx` imports and to the `__all__` list. Keep existing imports unchanged. Follow the alphabetical ordering already used in the file.

### Mappers (parallelizable — different files)

- [x] T019 [P] [US1] Create `map_mt5_position(pos) → Position` function in `app/mappers/position_mapper.py`. Convert MT5 position tuple fields: `pos.ticket` → int, `pos.symbol` → str, `pos.type` → "buy" if 0 else "sell", `pos.volume/price_open/price_current/profit/swap` → float, `pos.sl/tp` → float|None (None if value is 0.0), `pos.time` → ISO 8601 via `datetime.utcfromtimestamp(pos.time).isoformat() + "Z"`, `pos.magic` → int, `pos.comment` → str. Import the `Position` model from `..models.position`.
- [x] T020 [P] [US1] Create `map_mt5_order(ord) → Order` function in `app/mappers/order_mapper.py`. Map `ord.type` integer to string using lookup: `{2: "buy_limit", 3: "sell_limit", 4: "buy_stop", 5: "sell_stop"}`. Also create helper `pending_type_to_mt5_const(type_str: str) → int` that does the reverse mapping. Use `_mt5_const()` pattern from `app/mappers/trade_mapper.py` for safe constant resolution.
- [x] T021 [P] [US1] Create `map_mt5_account(acc) → AccountInfo` function in `app/mappers/account_mapper.py`. Straightforward field-to-field mapping from `mt5.account_info()` result: `acc.login`, `acc.server`, `acc.balance`, `acc.equity`, `acc.margin`, `acc.free_margin`, `acc.profit`, `acc.currency`, `acc.leverage`.
- [x] T022 [P] [US1] Create `map_mt5_deal(deal) → Deal` and `map_mt5_historical_order(ord) → HistoricalOrder` functions in `app/mappers/history_mapper.py`. For deals: map `deal.entry` int to Literal["in","out","inout"] (0=in, 1=out, 2=inout). For historical orders: map `ord.state` int to Literal["filled","cancelled","expired","rejected"].

### Enhance Trade Mapper (new builder functions)

- [x] T023 [US1] Add `build_close_request(position, volume: float | None, symbol_info) → dict` to `app/mappers/trade_mapper.py`. Build a `TRADE_ACTION_DEAL` counter-order: if position.type is "buy", counter is ORDER_TYPE_SELL and vice versa. If `volume` is None, use `position.volume` (full close). Normalize volume via existing `normalize_lot_size()`. Use `_mt5_const()` for constants.
- [x] T024 [US1] Add `build_modify_sltp_request(ticket: int, sl: float | None, tp: float | None) → dict` to `app/mappers/trade_mapper.py`. Build `TRADE_ACTION_SLTP` payload with `action`, `position` (ticket), `sl` (or 0.0), `tp` (or 0.0).
- [x] T025 [US1] Add `build_pending_order_request(req: PendingOrderRequest, mt5_symbol: str, symbol_info) → dict` to `app/mappers/trade_mapper.py`. Build `TRADE_ACTION_PENDING` payload. Use the `pending_type_to_mt5_const()` from `order_mapper.py` to map type strings. Normalize volume. Set magic=88001, type_time=GTC, type_filling=IOC.
- [x] T026 [US1] Add `build_modify_order_request(ticket: int, price: float | None, sl: float | None, tp: float | None) → dict` to `app/mappers/trade_mapper.py`. Build `TRADE_ACTION_MODIFY` payload.
- [x] T027 [US1] Add `build_cancel_order_request(ticket: int) → dict` to `app/mappers/trade_mapper.py`. Build `TRADE_ACTION_REMOVE` payload with `action` and `order` (ticket).
- [x] T028 [US1] Update existing `build_order_request()` in `app/mappers/trade_mapper.py` to pass `trade_req.sl` and `trade_req.tp` into the order dict (as `float(trade_req.sl) if trade_req.sl else 0.0` for each). This wires the new SL/TP fields from T017 into market orders.

### Unit Tests for Mappers

- [x] T029 [P] [US1] Create unit tests for `position_mapper` in `tests/unit/test_position_mapper.py`. Test: (1) basic mapping with all fields, (2) sl/tp=0.0 maps to None, (3) type=0 maps to "buy", type=1 maps to "sell", (4) time converts to ISO 8601 with "Z" suffix. Use a mock namedtuple or SimpleNamespace to simulate MT5 position objects.
- [x] T030 [P] [US1] Create unit tests for `order_mapper` in `tests/unit/test_order_mapper.py`. Test: (1) each order type int maps to correct string, (2) `pending_type_to_mt5_const()` reverse mapping, (3) sl/tp=0.0 maps to None.
- [x] T031 [P] [US1] Create unit tests for `account_mapper` in `tests/unit/test_account_mapper.py`. Test: (1) all fields map correctly, (2) leverage is int, (3) currency is str.
- [x] T032 [P] [US1] Create unit tests for `history_mapper` in `tests/unit/test_history_mapper.py`. Test: (1) deal entry mapping (0→"in", 1→"out", 2→"inout"), (2) historical order state mapping, (3) time conversion.
- [x] T033 [P] [US1] Create unit tests for the new trade_mapper builder functions in `tests/unit/test_trade_mapper_v2.py`. Test: (1) `build_close_request` counter-order type logic (buy→sell, sell→buy), (2) `build_close_request` with None volume = full close, (3) `build_modify_sltp_request` with sl/tp as None→0.0, (4) `build_pending_order_request` maps each type correctly, (5) `build_cancel_order_request` returns correct action, (6) `build_order_request` now includes sl/tp.

---

## Phase 3: Visibility — US2

> **Goal**: Add all read-only endpoints and dashboard tabs so the trader can see positions, orders, account info, tick prices, and terminal diagnostics.
> **Test Criteria**: `pytest tests/integration/test_account_route.py tests/integration/test_positions_route.py tests/integration/test_orders_route.py tests/integration/test_tick_route.py tests/integration/test_terminal_route.py` — all pass. Dashboard loads with Positions, Orders, and Status tabs showing data.
> **Depends on**: Phase 2 (US1 models and mappers must be complete)

### Routes (parallelizable — different files)

- [x] T034 [P] [US2] Create `GET /account` route in `app/routes/account.py`. Create an `APIRouter(tags=["account"])`. The handler submits a lambda calling `mt5.account_info()` via `submit()` from `mt5_worker`, awaits the future with `asyncio.wrap_future()`, maps the result using `map_mt5_account()`, and returns it. Handle `ConnectionError` → 503. Import `settings` and `submit` following the pattern in `app/routes/execute.py`.
- [x] T035 [P] [US2] Create `GET /positions` route in `app/routes/positions.py`. Submit `mt5.positions_get()` via worker, map each result with `map_mt5_position()`, return `{"positions": [...], "count": N}`. If `positions_get()` returns None, return empty list.
- [x] T036 [P] [US2] Create `GET /orders` route in `app/routes/orders.py`. Submit `mt5.orders_get()` via worker, map each with `map_mt5_order()`, return `{"orders": [...], "count": N}`. If `orders_get()` returns None, return empty list.
- [x] T037 [P] [US2] Create `GET /tick/{ticker}` route in `app/routes/tick.py`. Validate ticker is in `symbol_map` (404 if not). Resolve to `mt5_symbol`. Submit `mt5.symbol_info_tick(mt5_symbol)` via worker. Return `TickPrice` with `ticker` (user-facing), `bid`, `ask`, `spread` (ask-bid), `time` (ISO 8601).
- [x] T038 [P] [US2] Create `GET /terminal` route in `app/routes/terminal.py`. Submit `mt5.terminal_info()` via worker. Map to `TerminalInfo` model. Return directly.

### Register Routes

- [x] T039 [US2] Register all 5 new routers in `app/main.py`. Add imports at the bottom of the import block (following the existing `# noqa: E402` pattern): `from .routes.account import router as account_router`, etc. Then add `app.include_router(...)` for each. Keep existing routers unchanged.

### Integration Tests (parallelizable — different files)

- [x] T040 [P] [US2] Create integration test for `GET /account` in `tests/integration/test_account_route.py`. Mock the MT5 worker to return a fake account_info result. Assert 200 response with correct field structure. Assert 503 when worker raises ConnectionError. Follow the mocking pattern used in `tests/integration/test_health_route.py`.
- [x] T041 [P] [US2] Create integration test for `GET /positions` in `tests/integration/test_positions_route.py`. Test: (1) empty positions list → `{"positions": [], "count": 0}`, (2) two positions → correct mapping, (3) 503 on ConnectionError.
- [x] T042 [P] [US2] Create integration test for `GET /orders` in `tests/integration/test_orders_route.py`. Test: (1) empty orders → `{"orders": [], "count": 0}`, (2) pending order with correct type mapping, (3) 503 on ConnectionError.
- [x] T043 [P] [US2] Create integration test for `GET /tick/{ticker}` in `tests/integration/test_tick_route.py`. Test: (1) valid ticker → 200 with bid/ask/spread, (2) unknown ticker → 404, (3) 503 on ConnectionError.
- [x] T044 [P] [US2] Create integration test for `GET /terminal` in `tests/integration/test_terminal_route.py`. Test: (1) 200 with correct fields, (2) 503 on ConnectionError.

### Dashboard UI

- [x] T045 [US2] Add "Positions" and "Orders" tab buttons to the navigation in `dashboard/index.html`. Add two new `<button>` elements inside the existing tab bar. Add corresponding `<div>` containers for each tab's content area. Follow the existing tab structure.
- [x] T046 [P] [US2] Create `dashboard/js/positions.js`. Fetch `GET /positions` from the bridge. Render each position as a card showing: symbol, type (color-coded: green=buy, red=sell), volume, entry price, current price, P&L (color-coded), SL, TP, swap. Add a summary bar at the top with total unrealized P&L (fetched from `GET /account`). Set up 5-second auto-refresh with `setInterval`.
- [x] T047 [P] [US2] Create `dashboard/js/orders.js`. Fetch `GET /orders`. Render each pending order as a card showing: symbol, type, volume, trigger price, SL, TP, setup time. Set up 10-second auto-refresh.
- [x] T048 [US2] Update the Status tab section in the dashboard to add an Account Summary panel (from `GET /account`: balance, equity, margin, free margin, leverage) and a Terminal Diagnostics panel (from `GET /terminal`). Modify the relevant section in `dashboard/index.html` and the existing JS to fetch and display this data.

---

## Phase 4: Management — US3

> **Goal**: Add write endpoints for closing positions, cancelling orders, and modifying SL/TP or order parameters. Dashboard gets action buttons.
> **Test Criteria**: `pytest tests/integration/test_close_position.py tests/integration/test_cancel_order.py tests/integration/test_modify_sltp.py tests/integration/test_modify_order.py` — all pass.
> **Depends on**: Phase 3 (US2 read endpoints must work for verification)

### Routes

- [x] T049 [US3] Create `POST /close-position` route in `app/routes/close_position.py`. Accept `ClosePositionRequest`. Gate with `execution_enabled` check (return error if false). Use single-flight pattern from `execute.py` (copy `_acquire_single_flight`/`_release_single_flight` or refactor into shared utility). In the worker: (1) fetch the position via `mt5.positions_get(ticket=req.ticket)`, (2) if not found → 404, (3) build close request via `build_close_request()`, (4) call `mt5.order_send()`, (5) check retcode, (6) log via `log_trade()`. Return `TradeResponse`.
- [x] T050 [US3] Create `DELETE /orders/{ticket}` route in `app/routes/orders.py` (add to the existing orders router from T036). Gate with `execution_enabled`. In the worker: build cancel request via `build_cancel_order_request(ticket)`, call `mt5.order_send()`, check retcode. Return `{"success": true/false, "ticket_id": ticket, "error": ...}`.
- [x] T051 [US3] Create `PUT /positions/{ticket}/sltp` route in `app/routes/positions.py` (add to the existing positions router from T035). Accept `ModifySLTPRequest`. Gate with `execution_enabled`. In the worker: build modify request via `build_modify_sltp_request(ticket, req.sl, req.tp)`, call `mt5.order_send()`, check retcode. Return `{"success": true/false, "ticket_id": ticket, "error": ...}`.
- [x] T052 [US3] Create `PUT /orders/{ticket}` route in `app/routes/orders.py` (add to the existing orders router). Accept `ModifyOrderRequest`. Gate with `execution_enabled`. Build modify order request via `build_modify_order_request()`, submit, check retcode.

### Integration Tests

- [x] T053 [P] [US3] Create integration test for `POST /close-position` in `tests/integration/test_close_position.py`. Test: (1) successful full close → success=true, (2) execution_disabled → error message, (3) unknown ticket → 404, (4) 503 on ConnectionError. Mock MT5 worker to return fake position and order_send result.
- [x] T054 [P] [US3] Create integration test for `DELETE /orders/{ticket}` in `tests/integration/test_cancel_order.py`. Test: (1) successful cancel, (2) execution_disabled, (3) 503 on ConnectionError.
- [x] T055 [P] [US3] Create integration test for `PUT /positions/{ticket}/sltp` in `tests/integration/test_modify_sltp.py`. Test: (1) successful modify, (2) execution_disabled, (3) 503 on ConnectionError.
- [x] T056 [P] [US3] Create integration test for `PUT /orders/{ticket}` in `tests/integration/test_modify_order.py`. Test: (1) successful modify, (2) execution_disabled, (3) 503 on ConnectionError.

### Dashboard Actions

- [x] T057 [US3] Add "Close" button to each position card in `dashboard/js/positions.js`. On click: show a confirmation modal ("Close BUY 0.01 V75? This is irreversible."). On confirm: POST to `/close-position` with the ticket. On success: refresh positions list. On error: show error message.
- [x] T058 [US3] Add "Modify SL/TP" inline form to each position card in `dashboard/js/positions.js`. Add an expandable section below each card. On click "Modify": show two input fields (SL, TP) pre-filled with current values. On submit: PUT to `/positions/{ticket}/sltp`. On success: refresh.
- [x] T059 [US3] Add "Cancel" button to each order card in `dashboard/js/orders.js`. On click: show confirmation modal ("Cancel BUY LIMIT 0.01 V75 @ 940.00?"). On confirm: DELETE `/orders/{ticket}`. On success: refresh orders list.
- [x] T060 [US3] Add "Modify" inline form to each order card in `dashboard/js/orders.js`. Expandable section with fields for price, SL, TP (showing old → new comparison). On submit: PUT `/orders/{ticket}`.
- [x] T061 [US3] Add dashboard CSS for confirmation modals and inline forms in `dashboard/css/style.css`. Style: modal overlay, modal box, confirm/cancel buttons (red/gray), inline form inputs, expand/collapse animation.

---

## Phase 5: Execution — US4

> **Goal**: Enable full order placement (market + pending) with pre-validation. Rebuild the Execute tab.
> **Test Criteria**: `pytest tests/integration/test_pending_order.py tests/integration/test_order_check.py` — all pass. Execute tab shows order type selector and live pre-validation.
> **Depends on**: Phase 4 (US3 — management patterns reused)

### Routes

- [x] T062 [US4] Create `POST /pending-order` route in `app/routes/pending_order.py`. Accept `PendingOrderRequest`. Gate with `execution_enabled`. Validate ticker in `symbol_map`. In the worker: (1) get `symbol_info`, (2) build pending order via `build_pending_order_request()`, (3) `mt5.order_send()`, (4) check retcode. Use single-flight pattern. Log via `log_trade()`. Return `TradeResponse`.
- [x] T063 [US4] Create `POST /order-check` route in `app/routes/order_check.py`. Accept `PendingOrderRequest`. In the worker: (1) build the same pending order dict, (2) call `mt5.order_check()` instead of `order_send()`, (3) map result to `OrderCheckResponse` (valid=retcode==0, margin, profit, equity, comment, retcode). No execution gate needed (read-only check).

### Register Routes

- [x] T064 [US4] Register `pending_order_router` and `order_check_router` in `app/main.py`. Add imports and `app.include_router(...)` calls.

### Integration Tests

- [x] T065 [P] [US4] Create integration test for `POST /pending-order` in `tests/integration/test_pending_order.py`. Test: (1) successful placement, (2) unknown ticker → 404, (3) execution_disabled, (4) 503 on ConnectionError.
- [x] T066 [P] [US4] Create integration test for `POST /order-check` in `tests/integration/test_order_check.py`. Test: (1) valid order → valid=true with margin/equity, (2) invalid order → valid=false with retcode, (3) unknown ticker → 404.

### Dashboard: Rebuilt Execute Tab

- [x] T067 [US4] Create `dashboard/js/execute-v2.js` — the rebuilt Execute tab. Components: (1) Order type radio group (Market, Buy Limit, Sell Limit, Buy Stop, Sell Stop), (2) Ticker dropdown (from existing symbols list), (3) Volume stepper input, (4) "Trigger Price" field (shown only when a pending type is selected, hidden for Market), (5) SL and TP input fields, (6) Comment textarea, (7) Submit button.
- [x] T068 [US4] Add auto-price fetching to `dashboard/js/execute-v2.js`. When the ticker dropdown changes: call `GET /tick/{ticker}` and display current bid/ask next to the price fields.
- [x] T069 [US4] Add live pre-validation panel to `dashboard/js/execute-v2.js`. On any form field change (debounced 500ms): call `POST /order-check` with current form values. Display: ✅/❌ validity status, required margin (e.g., "$12.40"), estimated profit (if TP set), post-trade equity projection. Style the panel green for valid, red for invalid.
- [x] T070 [US4] Wire the Submit button in `dashboard/js/execute-v2.js`. On click: show confirmation modal. On confirm: if Market type → POST `/execute`, if pending type → POST `/pending-order`. On success: show success toast and reset form. On error: show error message.
- [x] T071 [US4] Update `dashboard/index.html` to replace the old Execute tab JS with `execute-v2.js`. Add a `<script>` tag for the new file. Remove or comment out the old execute tab logic.

---

## Phase 6: History & Discovery — US5

> **Goal**: Provide trade history audit trail and broker symbol discovery.
> **Test Criteria**: `pytest tests/integration/test_history_deals.py tests/integration/test_history_orders.py tests/integration/test_broker_symbols.py` — all pass. Trade History tab displays deals and orders. Broker Symbols browser shows catalog.
> **Depends on**: Phase 3 (US2 — follows same read-only patterns)

### Routes

- [x] T072 [US5] Create `GET /history/deals` and `GET /history/orders` routes in `app/routes/history.py`. Create `APIRouter(tags=["history"])`. For deals: accept query params `date_from` (str, ISO 8601), `date_to` (str, ISO 8601), `symbol` (str, optional), `position` (int, optional). Convert ISO dates to UTC timestamps via `datetime.fromisoformat(...).timestamp()`. Submit `mt5.history_deals_get(date_from_ts, date_to_ts)` via worker. Filter by symbol/position if provided. Map each deal with `map_mt5_deal()`. Return `{"deals": [...], "count": N, "net_profit": sum, "total_swap": sum, "total_commission": sum}`. For orders: similar pattern with `mt5.history_orders_get()` and `map_mt5_historical_order()`.
- [x] T073 [US5] Create `GET /broker-symbols` route in `app/routes/broker_symbols.py`. Accept optional `group` query param (str). Submit `mt5.symbols_get(group)` via worker (or `mt5.symbols_get()` if no group). Map each to `BrokerSymbol`, setting `is_configured = symbol.name in symbol_map_values` (cross-reference with the bridge's loaded `symbol_map`). Return `{"symbols": [...], "count": N}`.

### Register Routes

- [x] T074 [US5] Register `history_router` and `broker_symbols_router` in `app/main.py`.

### Integration Tests

- [x] T075 [P] [US5] Create integration test for `GET /history/deals` in `tests/integration/test_history_deals.py`. Test: (1) valid date range → deals list with summary stats, (2) empty result → `{"deals": [], "count": 0, "net_profit": 0, ...}`, (3) 503 on ConnectionError.
- [x] T076 [P] [US5] Create integration test for `GET /history/orders` in `tests/integration/test_history_orders.py`. Test: (1) valid range → orders list, (2) empty result, (3) 503. Ensure state field is correctly mapped (filled/cancelled/etc.).
- [x] T077 [P] [US5] Create integration test for `GET /broker-symbols` in `tests/integration/test_broker_symbols.py`. Test: (1) no filter → all symbols, (2) group filter → filtered set, (3) `is_configured` flag correctly reflects `symbol_map`.

### Dashboard UI

- [x] T078 [US5] Add "Trade History" tab to `dashboard/index.html`. Add tab button and content area.
- [x] T079 [US5] Create `dashboard/js/history.js`. Components: (1) Date range picker (two date inputs: from/to), (2) Sub-tab toggle: "Deals" vs "Orders", (3) Summary header (Net Profit, Total Swap, Total Commission, Trade Count), (4) Table showing deal/order records, (5) "Export to CSV" button. On load: default to last 7 days. On date change or sub-tab toggle: re-fetch and re-render.
- [x] T080 [US5] Implement CSV export in `dashboard/js/history.js`. On click "Export to CSV": convert current table data to CSV string, create a Blob, trigger browser download as `trade-history-YYYY-MM-DD.csv`.
- [x] T081 [US5] Create `dashboard/js/symbols-browser.js`. Fetch `GET /broker-symbols`. Render as a searchable table with columns: Name, Description, Spread, Digits, Volume Range, Trade Mode, Configured (badge). Add a text search input that filters by name/description. Add group filter dropdown (Forex, Indices, Crypto, etc.).
- [x] T082 [US5] Integrate the symbols browser into the existing Symbols tab in the dashboard. Add a section or sub-tab in `dashboard/index.html` for the broker symbols browser. Add a `<script>` tag for `symbols-browser.js`.

---

## Phase 7: Polish & Cross-Cutting

> **Goal**: Contract tests, final cleanup, and verification.

- [x] T083 Create contract tests for visibility endpoints in `tests/contract/test_visibility_contracts.py`. For each of `GET /account`, `/positions`, `/orders`, `/tick/{ticker}`, `/terminal`: assert response matches the Pydantic model schema (all required fields present, correct types). Use `TestClient` and mock MT5 worker.
- [x] T084 [P] Create contract tests for management endpoints in `tests/contract/test_management_contracts.py`. For `/close-position`, `/orders/{ticket}` (DELETE and PUT), `/positions/{ticket}/sltp`: assert request validation and response schema.
- [x] T085 [P] Create contract tests for execution endpoints in `tests/contract/test_execution_contracts_v2.py`. For `/pending-order` and `/order-check`: assert request/response schemas.
- [x] T086 [P] Create contract tests for history endpoints in `tests/contract/test_history_contracts.py`. For `/history/deals`, `/history/orders`, `/broker-symbols`: assert response schemas.
- [x] T087 Run full test suite `pytest` from repo root and fix any failures. Ensure all existing tests still pass (no regressions). Document test results.
- [x] T088 Run `quickstart.md` verification commands (curl commands for each phase) against a live bridge instance (or document the expected results for manual verification).

---

## Dependencies

```
Phase 1 (Setup) ──────► Phase 2 (US1: Foundations)
                              │
                              ▼
                        Phase 3 (US2: Visibility) ──► Phase 4 (US3: Management) ──► Phase 5 (US4: Execution)
                              │
                              └──────────────────────► Phase 6 (US5: History & Discovery)
                                                                │
                                                                ▼
                                                          Phase 7 (Polish)
```

- **US1** blocks everything (models and mappers are shared)
- **US2** blocks US3 (management needs visibility to verify results)
- **US3** blocks US4 (execution reuses management patterns like single-flight)
- **US5** is independent of US3/US4 (can run in parallel with Phase 4/5 after US2)
- **Phase 7** runs after all story phases complete

---

## Parallel Execution Examples

### Phase 2 (US1) — Maximum Parallelism

```
# Launch T004–T016 together (13 model files, all independent):
T004: Position model          T005: Order model
T006: AccountInfo model       T007: TickPrice model
T008: TerminalInfo model      T009: Deal model
T010: HistoricalOrder model   T011: BrokerSymbol model
T012: ClosePositionRequest    T013: ModifySLTPRequest
T014: ModifyOrderRequest      T015: PendingOrderRequest
T016: OrderCheckResponse

# Then T017–T018 (sequential, modify existing files)

# Then T019–T022 together (4 mapper files):
T019: position_mapper    T020: order_mapper
T021: account_mapper     T022: history_mapper

# Then T023–T028 (sequential, same file: trade_mapper.py)

# Then T029–T033 together (5 test files):
T029: test_position_mapper   T030: test_order_mapper
T031: test_account_mapper    T032: test_history_mapper
T033: test_trade_mapper_v2
```

### Phase 3 (US2) — Route Parallelism

```
# T034–T038 together (5 route files):
T034: account route    T035: positions route
T036: orders route     T037: tick route
T038: terminal route

# Then T039 (register in main.py)

# Then T040–T044 together (5 test files):
T040: test_account    T041: test_positions
T042: test_orders     T043: test_tick
T044: test_terminal
```

---

## Implementation Strategy

1. **MVP = Phase 2 + Phase 3 (US1 + US2)**: Deliver all models, mappers, and read-only visibility first. This alone provides major value — traders can see positions, orders, and account info.
2. **Increment 2 = Phase 4 (US3)**: Add trade management. Traders can now act on what they see.
3. **Increment 3 = Phase 5 (US4)**: Full order placement with pre-validation.
4. **Increment 4 = Phase 6 (US5)**: Analytics and discovery (can be developed in parallel with Phase 4/5).
5. **Final = Phase 7**: Polish, contract tests, full verification.

---

## Summary

| Metric                     | Value                                    |
| :------------------------- | :--------------------------------------- |
| **Total tasks**            | 88                                       |
| **US1 (Foundations)**      | 30 tasks (T004–T033)                     |
| **US2 (Visibility)**       | 15 tasks (T034–T048)                     |
| **US3 (Management)**       | 13 tasks (T049–T061)                     |
| **US4 (Execution)**        | 10 tasks (T062–T071)                     |
| **US5 (History)**          | 11 tasks (T072–T082)                     |
| **Setup**                  | 3 tasks (T001–T003)                      |
| **Polish**                 | 6 tasks (T083–T088)                      |
| **Parallel opportunities** | 35+ tasks marked [P]                     |
| **Suggested MVP**          | Phase 2 + Phase 3 (US1 + US2) = 45 tasks |

---

## Validation Checklist

- [x] All contracts have corresponding integration tests
- [x] All entities have model tasks
- [x] Parallel tasks are truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] All user stories have independent test criteria
- [x] Dependencies are clearly documented
