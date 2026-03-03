# Tasks: Adaptive Broker Capabilities

**Branch**: `008-adaptive-broker-capabilities`
**Input**: Design documents from `specs/008-adaptive-broker-capabilities/`
**Spec**: `specs/008-adaptive-broker-capabilities/spec.md`
**Plan**: `specs/008-adaptive-broker-capabilities/plan.md`
**Date**: 2026-03-02

---

## User Story Map

| Story | FRs        | Priority | Summary                                                 |
| ----- | ---------- | -------- | ------------------------------------------------------- |
| US1   | FR-001–003 | P1 🔴    | Dynamic filling mode — fixes retcode=10030              |
| US2   | FR-004–007 | P1 🔴    | Trade mode enforcement before order dispatch            |
| US3   | FR-008–013 | P1 🔴    | `/broker-capabilities` endpoint with TTL cache          |
| US4   | FR-014–017 | P2 🟠    | Execute tab: live symbol dropdown + trade mode guard UI |
| US5   | FR-018–020 | P2 🟠    | Symbols browser: dynamic categories + new columns       |
| US6   | FR-021     | P3 🟡    | Prices tab: symbol source from live broker catalog      |
| US7   | FR-022–023 | P3 🟡    | Status tab: account/terminal capability panel           |
| US8   | FR-024–027 | P2 🟠    | Backward compat, `mt5_symbol_direct`, env config        |

---

## Phase 1: Setup

- [x] T001 Copy `tasks-template.md` structure is already consumed — verify `specs/008-adaptive-broker-capabilities/` contains `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/api-contracts.md`
- [x] T002 Create new file `app/models/broker_capabilities.py` (empty module placeholder so import references resolve)
- [x] T003 Create new file `app/routes/broker_capabilities.py` (empty module placeholder)
- [x] T004 Add two new env vars to `.env.example`: `CAPABILITIES_CACHE_TTL_SECONDS=60` and `AUTO_SELECT_SYMBOLS=true`

---

## Phase 2: Foundational — Filling Mode Fix (US1, P1 🔴)

> **Blocks**: US2 (trade mode validation shares `symbol_info` fetch path), US3 (fills mode must be resolved when caching capabilities). Complete before any other phase.

**Story Goal**: Every market order, pending order, and position close uses a broker-compatible filling mode — derived at runtime from `symbol_info.filling_mode` — never hardcoded IOC.

**Independent Test Criteria**: Submit a market order against a RETURN-only symbol mock; verify `type_filling=0` (RETURN) in the request dict. Verify retcode=10030 is not possible from the bridge layer.

### Implementation

- [x] T005 Add `resolve_filling_mode(symbol_info: Any) -> int` function to `app/mappers/trade_mapper.py` — reads `symbol_info.filling_mode` bitmask; priority: FOK (bit 0) → IOC (bit 1) → RETURN (default)
- [x] T006 Replace hardcoded `order_filling_ioc` on line 75 of `app/mappers/trade_mapper.py` in `build_order_request()` with `resolve_filling_mode(symbol_info)` call
- [x] T007 Replace hardcoded `order_filling_ioc` on line 93 of `app/mappers/trade_mapper.py` in `build_order_request()` (second occurrence, sell path) with `resolve_filling_mode(symbol_info)` call
- [x] T008 Replace hardcoded `order_filling_ioc` on line 142 of `app/mappers/trade_mapper.py` in `build_pending_order_request()` with `resolve_filling_mode(symbol_info)` call
- [x] T009 Replace hardcoded `order_filling_ioc` on line 159 of `app/mappers/trade_mapper.py` in `build_pending_order_request()` (second occurrence) with `resolve_filling_mode(symbol_info)` call
- [x] T010 Update `build_close_request()` signature in `app/mappers/trade_mapper.py` to accept `symbol_info: Any` parameter and set `type_filling` using `resolve_filling_mode(symbol_info)`
- [x] T011 Update `app/routes/close_position.py` line 114 — pass `symbol_info` to `build_close_request(position, req.volume, symbol_info)` call

### Tests

- [x] T012 [P] Create `tests/unit/test_resolve_filling_mode.py` — test bitmask=0→RETURN, bitmask=1→FOK, bitmask=2→IOC, bitmask=3→FOK, missing attr→RETURN
- [x] T013 [P] Create `tests/unit/test_build_order_request_filling.py` — assert `build_order_request()` embeds correct `type_filling` values with various mock `symbol_info.filling_mode` values
- [x] T014 [P] Create `tests/unit/test_build_close_request_filling.py` — assert `build_close_request()` accepts `symbol_info` and sets `type_filling` correctly

---

## Phase 3: Trade Mode Enforcement (US2, P1 🔴)

> **Requires**: Phase 2 complete (symbol_info already fetched in worker). **Blocks**: US4 dashboard trade mode guard (FR-016, FR-017).

**Story Goal**: The bridge rejects orders that violate a symbol's broker-enforced trade direction before sending anything to MT5. Users receive a human-readable error, not a broker retcode.

**Independent Test Criteria**: Mock `symbol_info.trade_mode=1` (Long Only) and submit a "sell" action → expect `TradeResponse(success=False, error="Symbol … only allows long (buy) trades.")` with HTTP 422. Repeat for each restricted mode.

### Implementation

- [x] T015 Add `validate_trade_mode(symbol_info: Any, action: str) -> str | None` helper function to `app/mappers/trade_mapper.py` — returns error string or None; handles trade_mode 0 (disabled), 1 (long only), 2 (short only), 3 (close only), 4/unknown (pass)
- [x] T016 Add trade mode validation block to `app/routes/execute.py` inside `_execute_in_worker()`, immediately after `symbol_info` is fetched — call `validate_trade_mode(symbol_info, req.action)`, return HTTP 422 TradeResponse if error
- [x] T017 Add trade mode validation block to `app/routes/pending_order.py` inside `_execute_in_worker()`, immediately after `symbol_info` is fetched — map pending order type ("buy_limit", "buy_stop" → "buy"; "sell_limit", "sell_stop" → "sell") then call `validate_trade_mode()`

### Tests

- [x] T018 [P] Create `tests/unit/test_validate_trade_mode.py` — test all 5 trade_mode values × buy/sell actions; verify correct error strings; verify unknown mode returns None (allow)
- [x] T019 [P] Create `tests/contract/test_execute_trademode_contract.py` — use httpx TestClient; mock `mt5.symbol_info` to return trade_mode=1 (Long Only); POST /execute with action=sell → assert 422 with detail containing "only allows long"
- [x] T020 [P] Create `tests/contract/test_pending_order_trademode_contract.py` — same pattern for pending orders; test sell_limit on Long Only symbol → 422

---

## Phase 4: Broker Capabilities Endpoint (US3, P1 🔴)

> **Requires**: Phase 2 (filling mode logic needed to decode `filling_mode` into `supported_filling_modes`). **Blocks**: All dashboard phases (US4–US7) which consume `/broker-capabilities`.

**Story Goal**: A single `GET /broker-capabilities` endpoint returns the full live broker symbol catalog — with category tree, filling mode, trade mode, and account/terminal trade authorization — served from a TTL-cached in-memory store.

**Independent Test Criteria**: Call `GET /broker-capabilities` with MT5 mocked to return 3 symbols with different paths → assert response contains correctly derived `categories` dict, correct `category`/`subcategory` per symbol, correct `supported_filling_modes` per symbol.

### Models

- [x] T021 Extend `app/models/broker_symbol.py` — add 7 new fields: `category: str = "Other"`, `subcategory: str = ""`, `filling_mode: int = 0`, `supported_filling_modes: list[str] = []`, `trade_mode_label: str = "Full"`, `volume_step: float = 0.01`, `visible: bool = True`
- [x] T022 Create `app/models/broker_capabilities.py` — define `BrokerCapabilitiesResponse` Pydantic model with fields: `account_trade_allowed`, `terminal_trade_allowed`, `symbol_count`, `symbols: list[BrokerSymbol]`, `categories: dict[str, list[str]]`, `fetched_at: str`

### Route

- [x] T023 Create `app/routes/broker_capabilities.py` with module-level cache vars: `_capabilities_cache: BrokerCapabilitiesResponse | None = None`, `_cache_fetched_at: datetime | None = None`, `_cache_lock: threading.Lock`
- [x] T024 Add `_fetch_capabilities_from_mt5() -> BrokerCapabilitiesResponse` internal function in `app/routes/broker_capabilities.py` — calls `mt5.symbols_get()`, `mt5.terminal_info()`, `mt5.account_info()`, builds `BrokerCapabilitiesResponse`; parses path with `path.replace("\\", "/").split("/")` for category/subcategory; decodes filling_mode bitmask to `supported_filling_modes`; maps trade_mode int to label; builds `categories` dict
- [x] T025 Add `GET /broker-capabilities` endpoint in `app/routes/broker_capabilities.py` — checks cache freshness against `settings.capabilities_cache_ttl_seconds`, returns cached response if fresh, else calls `_fetch_capabilities_from_mt5()` and updates cache; uses `submit()` for MT5 calls
- [x] T026 Add `POST /broker-capabilities/refresh` endpoint in `app/routes/broker_capabilities.py` — clears `_capabilities_cache` and `_cache_fetched_at`, calls `_fetch_capabilities_from_mt5()`, returns refresh confirmation JSON
- [x] T027 Register `broker_capabilities.router` in `app/main.py` — add import and `app.include_router(broker_capabilities.router)` alongside existing routers
- [x] T028 Add `capabilities_cache_ttl_seconds: int = 60` and `auto_select_symbols: bool = True` to `Settings` class in `app/config.py` with `validation_alias` / env var names `CAPABILITIES_CACHE_TTL_SECONDS` and `AUTO_SELECT_SYMBOLS`

### Broker Symbols Route Extension

- [x] T029 Update `app/routes/broker_symbols.py` `_fetch_symbols()` function — populate new `BrokerSymbol` fields: `category`, `subcategory` (from path parse), `filling_mode` (raw int), `supported_filling_modes` (decoded list), `trade_mode_label` (mapped string), `volume_step`, `visible`

### Cache Invalidation Hook

- [x] T030 Add `invalidate_capabilities_cache()` public function in `app/routes/broker_capabilities.py` — sets `_capabilities_cache = None` and `_cache_fetched_at = None`; import and call this from the MT5 worker reconnect event in `app/mt5_worker.py` when state transitions to `AUTHORIZED`

### Tests

- [x] T031 [P] Create `tests/unit/test_parse_symbol_path.py` — test `"Forex\\Majors\\EURUSD"` → `("Forex", "Majors")`, `"Forex/Majors/EURUSD"` → `("Forex", "Majors")`, `"Crypto"` → `("Crypto", "")`, `""` → `("Other", "")`, `None` → `("Other", "")`
- [x] T032 [P] Create `tests/unit/test_broker_capabilities_model.py` — mock symbols_get with 4 symbols of varying paths and filling_modes; assert `categories` dict correct; assert `is_configured` cross-reference correct; assert `supported_filling_modes` encoding correct
- [x] T033 [P] Create `tests/contract/test_broker_capabilities_contract.py` — TestClient GET /broker-capabilities → 200, validate full response schema; POST /broker-capabilities/refresh → 200; assert stale cache triggers re-fetch; assert 503 when worker not connected
- [x] T034 [P] Create `tests/integration/test_capabilities_cache.py` — assert second GET within TTL returns same `fetched_at`; assert POST /refresh causes new `fetched_at`; assert `invalidate_capabilities_cache()` clears cache

---

## Phase 5: Execute Tab — Dynamic Symbols & Trade Mode Guard (US4, P2 🟠)

> **Requires**: Phase 4 (`/broker-capabilities` endpoint). **Blocks**: None.

**Story Goal**: The dashboard Execute tab populates its ticker dropdown from the live broker catalog grouped by MT5 categories, and disables Buy/Sell based on symbol trade mode — shown before submission, not after a broker rejection.

**Independent Test Criteria**: Manually open Execute tab → ticker dropdown contains symbols not in `symbols.yaml` grouped by real MT5 categories; select a Long Only symbol → Sell option is disabled with tooltip; select a Disabled/Close Only symbol → Submit button is greyed out with warning banner.

### Implementation

- [x] T035 Update `dashboard/js/execute-v2.js` — replace `fetch('/symbols')` call with `fetch('/broker-capabilities')` to load symbol catalog; store response in module-level `_capabilitiesCache` JS object
- [x] T036 Update `dashboard/js/execute-v2.js` — rewrite `populateTickerDropdown()` function to build `<select>` with `<optgroup label="CategoryName">` groups from `_capabilitiesCache.categories`; include all symbols where `trade_mode !== 0`; add text search `<input id="symbolSearch">` above the select
- [x] T037 Update `dashboard/js/execute-v2.js` — add `filterSymbolDropdown(query)` function that hides/shows `<option>` elements matching the search input value (case-insensitive on name + description)
- [x] T038 Update `dashboard/js/execute-v2.js` — add `onSymbolSelect(symbolName)` handler: read `trade_mode` from `_capabilitiesCache.symbols`; disable Buy button if `trade_mode` is 2 (Short Only) or 3 (Close Only); disable Sell button if `trade_mode` is 1 (Long Only) or 3 (Close Only); add `title` attribute explaining why
- [x] T039 Update `dashboard/js/execute-v2.js` — add `renderTradeModeWarning(symbol)` function: show warning banner `⚠️ [symbol] is in [trade_mode_label] mode. [explanation].` for trade_mode 0 or 3; disable Submit button in these cases
- [x] T040 Update `dashboard/js/execute-v2.js` — update `buildExecutePayload()` to include `mt5_symbol_direct: symbolName` in POST /execute body so the bridge resolves the symbol without needing a YAML alias

---

## Phase 6: Symbols Browser — Dynamic Categories & New Columns (US5, P2 🟠)

> **Requires**: Phase 4. **Can run in parallel with Phase 5** (different file: `symbols-browser.js`).

**Story Goal**: The Symbols Browser category filter is built dynamically from the live MT5 path hierarchy. The table shows category, subcategory, trade mode badge, and supported filling modes for every symbol.

**Independent Test Criteria**: Open Symbols tab → category dropdown lists exactly the categories from MT5, not hardcoded strings; selecting "Forex > Majors" filters correctly; a Long Only symbol shows an orange badge; RETURN-only symbols show "RETURN" in Filling column.

### Implementation

- [x] T041 [P] Update `dashboard/js/symbols-browser.js` — replace `fetch('/broker-symbols')` with `fetch('/broker-capabilities')` and store in module-level `_capabilitiesData`
- [x] T042 Update `dashboard/js/symbols-browser.js` — replace hardcoded category `<option>` elements in the filter dropdown with dynamic build from `_capabilitiesData.categories`: outer loop on category keys (add `<optgroup>` or `<option value="Cat">Cat</option>`), inner loop on subcategory values (add indented sub-options)
- [x] T043 Update `dashboard/js/symbols-browser.js` — update `filterSymbols()` function to match `symbol.category` and `symbol.subcategory` against the selected dropdown values (exact string match, not path text guess)
- [x] T044 Update `dashboard/js/symbols-browser.js` — add "Category" and "Subcategory" columns to the symbol table header and data rows; populate from `symbol.category` and `symbol.subcategory`
- [x] T045 Update `dashboard/js/symbols-browser.js` — add "Trade Mode" column with color-coded badge: `trade_mode_label` with CSS classes `badge-full` (green), `badge-longonly` (blue), `badge-shortonly` (orange), `badge-closeonly` (yellow), `badge-disabled` (red)
- [x] T046 Update `dashboard/js/symbols-browser.js` — add "Filling Modes" column showing `symbol.supported_filling_modes.join(", ")` (e.g., "FOK, IOC" or "RETURN")
- [x] T047 Update `dashboard/js/symbols-browser.js` — add "Show disabled symbols" `<input type="checkbox">` toggle; when unchecked (default), filter out symbols where `trade_mode === 0`; when checked, show all

---

## Phase 7: Prices Tab — Live Symbol Source (US6, P3 🟡)

> **Requires**: Phase 4. **Can run in parallel with Phase 5 and Phase 6** (different file: `app.js`).

**Story Goal**: The Prices tab ticker dropdown contains every symbol the broker offers — not only YAML-configured ones — grouped by MT5 category.

**Independent Test Criteria**: Open Prices tab → ticker dropdown contains symbols not in `symbols.yaml`; selecting any broker symbol and clicking "Get Price" loads a valid tick.

### Implementation

- [x] T048 [P] Update `dashboard/js/app.js` prices tab render block — replace `fetch('/symbols')` call with `fetch('/broker-capabilities')` to source the ticker list
- [x] T049 Update `dashboard/js/app.js` prices tab — rebuild the ticker `<select>` to use `<optgroup>` elements from `response.categories`, iterating `response.symbols` grouped by category; use `symbol.name` as both value and label (appending description)

---

## Phase 8: Status Tab — Capability Panel (US7, P3 🟡)

> **Requires**: Phase 4. **Can run in parallel with Phase 7**.

**Story Goal**: The Status tab shows a clear visual panel with terminal trade-allowed status, account trade-allowed status, and execution policy — with green/red indicators and a prominent warning if either flag is false.

**Independent Test Criteria**: Open Status tab when `account_trade_allowed=false` → red warning banner "Account trading is not allowed" is visible above the terminal info section.

### Implementation

- [x] T050 [P] Update `dashboard/js/app.js` (or `dashboard/js/components.js`) status tab render — add `fetch('/broker-capabilities')` call alongside existing `fetch('/terminal')` call; store capabilities response
- [x] T051 Update status tab render — build `renderCapabilityPanel(capabilities)` function that returns an HTML block showing: `✅/❌ Terminal Trade Allowed`, `✅/❌ Account Trade Allowed`, `✅/❌ Execution Policy Active`; use green/red CSS classes
- [x] T052 Update status tab render — show a full-width red alert `<div class="warning-banner">` at top of status content if `capabilities.terminal_trade_allowed === false` OR `capabilities.account_trade_allowed === false`

---

## Phase 9: Backward Compatibility & `mt5_symbol_direct` (US8, P2 🟠)

> **Requires**: Phase 2 (filling mode). **Can start alongside Phase 3/4**. Completes the API contract extension.

**Story Goal**: The `POST /execute` endpoint accepts an optional `mt5_symbol_direct` field that bypasses the YAML symbol lookup, enabling the dashboard to trade any broker symbol. Existing AI strategy calls using YAML tickers continue unchanged.

**Independent Test Criteria**: POST /execute with `{"ticker": "DIRECT", "action": "buy", ..., "mt5_symbol_direct": "EURUSD"}` → bridge resolves to EURUSD and submits successfully (no "Unknown ticker" error). POST /execute without `mt5_symbol_direct` using a YAML ticker → unchanged behavior.

### Implementation

- [x] T053 Add `mt5_symbol_direct: str | None = None` field to `TradeRequest` in `app/models/trade.py`
- [x] T054 Update `app/routes/execute.py` — add bypass logic after the `symbol_map` lookup: if `req.mt5_symbol_direct` is set and not empty, use it as `mt5_symbol` directly (skip the YAML check that raises 404); preserve `req.ticker` for audit logging
- [x] T055 Update `app/routes/pending_order.py` — add same `mt5_symbol_direct` bypass logic for pending order submissions

### Tests

- [x] T056 [P] Create `tests/contract/test_execute_mt5_symbol_direct_contract.py` — TestClient POST /execute with `mt5_symbol_direct="EURUSD"` and unknown `ticker="DIRECT"` → assert executes without 404; assert ticker value appears in audit log mock

---

## Phase 10: Polish & Cross-Cutting Concerns

> **Requires**: All phases complete. Run as final sweep.

- [x] T057 [P] Update `.env.example` with documented new env vars: `CAPABILITIES_CACHE_TTL_SECONDS=60` (with comment) and `AUTO_SELECT_SYMBOLS=true` (with comment)
- [x] T058 [P] Update `GEMINI.md` `## Active Technologies` section — update entry for this feature `008-adaptive-broker-capabilities` to reflect all changes (already bootstrapped by `update-agent-context.sh`)
- [x] T059 Run `pytest tests/ -x -v` from `src/` to confirm all new and existing tests pass
- [x] T060 Run `ruff check .` from `src/` and fix any new lint errors introduced by this feature
- [ ] T061 Manually test the full dashboard flow: connect MT5 → open Symbols tab → verify categories match MT5 tree → open Execute tab → select a symbol → verify trade mode guard → submit a market order → verify no retcode=10030
- [x] T062 Update `README.md` (or `docs/`) to document the new `GET /broker-capabilities` and `POST /broker-capabilities/refresh` endpoints

---

## Dependency Graph

```
Phase 2 (US1 — Filling Mode Fix)
  └──► Phase 3 (US2 — Trade Mode Enforcement)
  └──► Phase 4 (US3 — Broker Capabilities Endpoint)
          └──► Phase 5 (US4 — Execute Tab)
          └──► Phase 6 (US5 — Symbols Browser)    ← parallel with Phase 5
          └──► Phase 7 (US6 — Prices Tab)         ← parallel with Phase 5, 6
          └──► Phase 8 (US7 — Status Tab)         ← parallel with Phase 7

Phase 9 (US8 — mt5_symbol_direct) ← can start after Phase 2, runs parallel to Phase 4

Phase 10 (Polish) ← requires all above complete
```

---

## Parallel Execution Examples

### Sprint 1: Backend Core (Phases 2 + 3 + 9 — all backend, no UI)

Run these together (different files, no conflicts):

```
T005–T011  trade_mapper.py — filling mode (sequential, same file)
T015       trade_mapper.py — validate_trade_mode (sequential after T011)
T053       models/trade.py — mt5_symbol_direct field
T028       config.py — new settings fields
T002–T004  setup — empty modules + .env.example
```

After completing T005–T015:

```
T012 [P] tests/unit/test_resolve_filling_mode.py
T013 [P] tests/unit/test_build_order_request_filling.py
T014 [P] tests/unit/test_build_close_request_filling.py
T018 [P] tests/unit/test_validate_trade_mode.py
T019 [P] tests/contract/test_execute_trademode_contract.py
```

### Sprint 2: Capabilities Endpoint (Phase 4)

```
T021  models/broker_symbol.py — extend fields
T022  models/broker_capabilities.py — new model
  ↓
T023–T026  routes/broker_capabilities.py — cache + endpoints (sequential, same file)
T027  main.py — register router
T029  routes/broker_symbols.py — populate new fields
T030  mt5_worker.py — hook cache invalidation
  ↓
T031 [P] tests/unit/test_parse_symbol_path.py
T032 [P] tests/unit/test_broker_capabilities_model.py
T033 [P] tests/contract/test_broker_capabilities_contract.py
T034 [P] tests/integration/test_capabilities_cache.py
```

### Sprint 3: Dashboard (Phases 5 + 6 + 7 + 8 — all different files, fully parallel)

```
T035–T040  [execute-v2.js]    Execute tab
T041–T047  [symbols-browser.js] Symbols Browser   ← parallel
T048–T049  [app.js prices]    Prices tab           ← parallel
T050–T052  [app.js status]    Status tab           ← parallel (different functions in app.js)
```

---

## Implementation Strategy

**MVP Scope** (minimum to fix the live bug and deliver business value):

1. Phase 2 (T005–T014) — Unblocks retcode=10030 immediately ← **deploy first**
2. Phase 3 (T015–T020) — Prevents incorrect order direction errors
3. Phase 9 (T053–T056) — Enables dashboard to trade any broker symbol

**Full Feature**:

- Phase 4 → Phase 5–8 → Phase 10

**Suggested PR sequence**:

1. PR #1: Phase 2 only (filling mode fix) — smallest, safest, fixes live bug
2. PR #2: Phase 3 + Phase 9 (trade mode + mt5_symbol_direct)
3. PR #3: Phase 4 (broker capabilities endpoint — new endpoint, additive)
4. PR #4: Phase 5–8 (all dashboard changes together)
5. PR #5: Phase 10 (polish)

---

## Task Count Summary

| Phase                         | Tasks  | [P] Parallel | Story |
| ----------------------------- | ------ | ------------ | ----- |
| Phase 1 — Setup               | 4      | 0            | —     |
| Phase 2 — US1 Filling Mode    | 10     | 3            | US1   |
| Phase 3 — US2 Trade Mode      | 6      | 3            | US2   |
| Phase 4 — US3 Capabilities    | 14     | 4            | US3   |
| Phase 5 — US4 Execute Tab     | 6      | 0            | US4   |
| Phase 6 — US5 Symbols Browser | 7      | 1            | US5   |
| Phase 7 — US6 Prices Tab      | 2      | 1            | US6   |
| Phase 8 — US7 Status Tab      | 3      | 1            | US7   |
| Phase 9 — US8 Compat          | 4      | 1            | US8   |
| Phase 10 — Polish             | 6      | 2            | —     |
| **Total**                     | **62** | **16**       | —     |

---

## Validation Checklist

- [x] All contracts have corresponding tests (T033 covers both new endpoints; T019/T020 cover modified endpoints)
- [x] All entities have model tasks (BrokerSymbol T021, BrokerCapabilities T022, TradeRequest T053)
- [x] Parallel tasks are truly independent (verified by file path — no two [P] tasks modify same file)
- [x] Each task specifies exact file path
- [x] No task modifies the same file as another concurrent [P] task
- [x] All phases have independent test criteria defined
- [x] Dependency graph is acyclic
- [x] MVP scope identified and justifiable for immediate deployment
