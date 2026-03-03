# MT5 Parity Gap Register — MT5 Connection Bridge

> **Snapshot Date**: 2026-03-03
> **Bridge Version**: 1.2.0
> **MT5 Python Library**: MetaTrader5 ≥ 5.0.5640
> **Purpose**: Inventory of MT5 Python API coverage vs. current bridge implementation

---

## Category 1: Connection and Session Lifecycle

| MT5 Function       | Bridge Coverage | Coverage Notes                                                             | Constraints                                                                        | Known Broker Variance                                                                         | Fallback Behavior                                                   | Test Coverage                    | Operator Readiness Impact                                    |
| ------------------ | --------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------ |
| `mt5.initialize()` | **full**        | Called in `mt5_worker._connect()` at worker startup and on every reconnect | Must specify `path` kwarg for non-default MT5 terminal installs                    | Some brokers require specific terminal builds; path varies by installation                    | Worker enters `DISCONNECTED` state → bridge returns 503             | automated (mock in worker tests) | Critical — if `initialize` fails, all operations are blocked |
| `mt5.shutdown()`   | **full**        | Called in `mt5_worker._disconnect()` on graceful close and before retry    | Must be called from the same thread as `initialize`                                | None known                                                                                    | Worker enters `DISCONNECTED` state                                  | automated                        | Low — only impacts clean shutdown                            |
| `mt5.login()`      | **full**        | Called in `mt5_worker._authorize()` after successful `initialize`          | Credentials from environment variables (`MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`) | Login may fail with "Authorization failed" for some broker servers during maintenance windows | Worker enters `ERROR` state → reconnect loop                        | automated (mock)                 | Critical — login failure prevents all operations             |
| `mt5.last_error()` | **full**        | Called throughout worker and route handlers to capture error context       | Returns `(code, message)` tuple; code semantics vary between terminal versions     | None known — standardized by MetaQuotes                                                       | Error details logged to JSONL; generic message returned to consumer | automated                        | Medium — error context quality affects debugging             |

---

## Category 2: Terminal and Account Metadata

| MT5 Function          | Bridge Coverage | Coverage Notes                                                                              | Constraints                                       | Known Broker Variance                                                          | Fallback Behavior                                           | Test Coverage    | Operator Readiness Impact                                      |
| --------------------- | --------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------ | ----------------------------------------------------------- | ---------------- | -------------------------------------------------------------- |
| `mt5.terminal_info()` | **full**        | Exposed via `GET /terminal` and used in `/broker-capabilities` for `terminal_trade_allowed` | Returns `TerminalInfo` named tuple                | Some fields (e.g., `community_balance`) may be zero depending on broker        | Returns cached or None; endpoint returns 503 if unavailable | automated (mock) | High — `trade_allowed=false` should block trading              |
| `mt5.account_info()`  | **full**        | Exposed via `GET /account` and used in `/broker-capabilities` for `account_trade_allowed`   | Returns `AccountInfo` named tuple                 | Leverage, margin calculation mode, and trade mode vary significantly by broker | Returns cached or None; endpoint returns 503                | automated (mock) | High — `trade_allowed=false` should block trading              |
| `mt5.version()`       | **partial**     | Not exposed as a dedicated endpoint; terminal build available via `terminal_info().build`   | Returns `(build, release_date, build_date)` tuple | None known                                                                     | Not called; terminal_info provides sufficient version data  | none             | Low — version info is available through `/terminal` indirectly |

---

## Category 3: Symbol and Market Data

| MT5 Function                | Bridge Coverage | Coverage Notes                                                                                                                           | Constraints                                                          | Known Broker Variance                                                                  | Fallback Behavior                                    | Test Coverage    | Operator Readiness Impact                                        |
| --------------------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------- | ---------------- | ---------------------------------------------------------------- |
| `mt5.symbols_get()`         | **full**        | Used in `/broker-symbols` and `/broker-capabilities` to fetch all visible symbols                                                        | Can filter by `group` parameter — bridge does not currently use this | Symbol count varies 100–5000+ by broker; large catalogs may cause slow first fetch     | Cache miss → fresh MT5 call; failure → 503           | automated (mock) | Medium — supports symbol catalog                                 |
| `mt5.symbols_total()`       | **none**        | Not called; `len(symbols_get())` used instead                                                                                            | N/A                                                                  | N/A                                                                                    | Bridge uses `len(symbols_get())` result              | none             | Low — count available through symbols_get                        |
| `mt5.symbol_info()`         | **full**        | Called in trade routes (`execute`, `pending-order`, `close-position`) to get symbol specs (filling mode, trade mode, volume constraints) | String symbol name required                                          | `filling_mode` bitmask interpretation varies; some brokers only support RETURN filling | Failure → trade rejected with descriptive error      | automated (mock) | Critical — incorrect symbol info leads to order rejections       |
| `mt5.symbol_info_tick()`    | **full**        | Exposed via `GET /tick/{ticker}` — returns current tick (bid, ask, last, volume, time)                                                   | Symbol must be visible in MarketWatch                                | Some brokers don't populate `last` field for certain instruments                       | Returns None → 503 with "tick unavailable" error     | automated (mock) | Medium — tick data drives dashboard displays                     |
| `mt5.symbol_select()`       | **partial**     | Called implicitly by some MT5 functions; not explicitly exposed or called in trade setup                                                 | Adds/removes symbol from MarketWatch panel                           | Some symbols require manual selection before data becomes available                    | Not called → relies on broker's auto-select behavior | none             | Medium — could cause silent tick failures for unselected symbols |
| `mt5.market_book_add()`     | **none**        | Not implemented — market depth (DOM) not exposed                                                                                         | Requires `symbol_select` first; subscription-based                   | Not all brokers provide depth of market data                                           | N/A — market depth not available through bridge      | none             | Low — advanced feature, not required for basic trading           |
| `mt5.market_book_get()`     | **none**        | Not implemented — market depth queries not available                                                                                     | Requires prior `market_book_add` subscription                        | Depth levels and update frequency vary by broker                                       | N/A                                                  | none             | Low — deferred to Phase 7 or beyond                              |
| `mt5.market_book_release()` | **none**        | Not implemented — no DOM subscriptions to release                                                                                        | Only needed if `market_book_add` is implemented                      | N/A                                                                                    | N/A                                                  | none             | Low — dependent on `market_book_add`                             |

---

## Category 4: Order Pre-check and Calculations

| MT5 Function              | Bridge Coverage | Coverage Notes                                                         | Constraints                                                  | Known Broker Variance                                                              | Fallback Behavior                                               | Test Coverage    | Operator Readiness Impact                                                   |
| ------------------------- | --------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------- | --------------------------------------------------------------- | ---------------- | --------------------------------------------------------------------------- |
| `mt5.order_check()`       | **full**        | Exposed via `POST /order-check` — validates an order without executing | Requires a fully formed `TradeRequest` structure             | Return codes and margin calculations may differ between hedge and netting accounts | Returns check result; failure → descriptive error               | automated (mock) | High — pre-check prevents unnecessary rejections                            |
| `mt5.order_calc_margin()` | **none**        | Not implemented — margin calculation not exposed                       | Requires symbol, order type, lot size, and price             | Margin calculation formulas vary by account type (hedge vs. netting)               | N/A — consumers must use `order_check` for indirect margin info | none             | Medium — useful for risk assessment, but `order_check` provides margin data |
| `mt5.order_calc_profit()` | **none**        | Not implemented — profit calculation not exposed                       | Requires symbol, order type, lot size, open and close prices | Profit calculation depends on account denomination currency and conversion rates   | N/A — consumers must calculate manually                         | none             | Medium — useful for position sizing, but not blocking                       |

---

## Category 5: Order Submission and Management

| MT5 Function            | Bridge Coverage | Coverage Notes                                                                                                                                | Constraints                                                                     | Known Broker Variance                                                                                              | Fallback Behavior                                                           | Test Coverage                     | Operator Readiness Impact                               |
| ----------------------- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- | --------------------------------- | ------------------------------------------------------- |
| `mt5.order_send()`      | **full**        | Used in `/execute`, `/pending-order`, `/close-position`, `/orders/{ticket}` (modify), `/orders/{ticket}` (delete), `/positions/{ticket}/sltp` | Must be called from worker thread; single-flight queue ensures serial execution | Return codes vary by broker; filling policies differ (FOK vs RETURN); comment length limits vary (max 25–32 chars) | Failure → descriptive error with MT5 return code and `last_error()` context | automated (mock + contract tests) | Critical — all trade operations depend on this          |
| `mt5.positions_get()`   | **full**        | Exposed via `GET /positions` — returns all open positions                                                                                     | Can filter by `symbol`, `ticket`, or `group` — bridge currently fetches all     | Position fields are standardized; no known broker variance                                                         | Returns empty list if no positions; failure → 503                           | automated (mock)                  | High — position visibility drives close operations      |
| `mt5.positions_total()` | **none**        | Not called; `len(positions_get())` used instead                                                                                               | N/A                                                                             | N/A                                                                                                                | Count available through `positions_get()`                                   | none                              | Low — total available indirectly                        |
| `mt5.orders_get()`      | **full**        | Exposed via `GET /orders` — returns all active pending orders                                                                                 | Can filter by `symbol`, `ticket`, or `group` — bridge fetches all               | Some brokers limit the number of simultaneous pending orders                                                       | Returns empty list; failure → 503                                           | automated (mock)                  | High — order visibility drives modify/cancel operations |
| `mt5.orders_total()`    | **none**        | Not called; `len(orders_get())` used instead                                                                                                  | N/A                                                                             | N/A                                                                                                                | Count available through `orders_get()`                                      | none                              | Low — total available indirectly                        |

---

## Category 6: History and Reporting

| MT5 Function                 | Bridge Coverage | Coverage Notes                                                 | Constraints                                                      | Known Broker Variance                                                           | Fallback Behavior                                         | Test Coverage    | Operator Readiness Impact                                      |
| ---------------------------- | --------------- | -------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------- | ---------------- | -------------------------------------------------------------- |
| `mt5.history_deals_get()`    | **full**        | Exposed via `GET /history/deals` with date range query params  | Requires `date_from` and `date_to` as datetime objects           | History retention period varies by broker (typically 30–365 days)               | Returns empty list if no deals; failure → 503             | automated (mock) | Medium — used for trade history review                         |
| `mt5.history_deals_total()`  | **none**        | Not called; deal count derived from `history_deals_get()`      | N/A                                                              | N/A                                                                             | Count available through `history_deals_get()`             | none             | Low — total available indirectly                               |
| `mt5.history_orders_get()`   | **full**        | Exposed via `GET /history/orders` with date range query params | Same as deals — requires date range                              | Same retention variance as deals                                                | Returns empty list; failure → 503                         | automated (mock) | Medium — used for order history review                         |
| `mt5.history_orders_total()` | **none**        | Not called; count derived from `history_orders_get()`          | N/A                                                              | N/A                                                                             | Count available through `history_orders_get()`            | none             | Low — total available indirectly                               |
| `mt5.copy_rates_from()`      | **full**        | Used in `POST /prices` — fetches OHLCV bars from a start date  | Requires symbol, timeframe enum, start datetime, and count       | Some brokers limit how far back historical data goes; weekend/holiday gaps      | Returns None → 503 with error                             | automated (mock) | Medium — supports price charts                                 |
| `mt5.copy_rates_from_pos()`  | **none**        | Not implemented — positional bar fetch not exposed             | Requires start position (int offset) instead of datetime         | Same data, different access pattern — less intuitive for API consumers          | Bridge uses `copy_rates_from()` instead                   | none             | Low — `copy_rates_from()` covers the same data                 |
| `mt5.copy_rates_range()`     | **none**        | Not implemented — date-range bar fetch not exposed             | Requires both `date_from` and `date_to` (no count limit)         | Potentially returns very large datasets for wide ranges                         | Bridge uses `copy_rates_from()` with explicit count limit | none             | Low — count-limited version is safer                           |
| `mt5.copy_ticks_from()`      | **none**        | Not implemented — tick history not exposed                     | Requires symbol, start datetime, count, and flags (TRADE or ALL) | Tick data volume can be extremely high (thousands per second on active symbols) | N/A — tick history not available through bridge           | none             | Medium — useful for micro-analysis but risky for large queries |
| `mt5.copy_ticks_range()`     | **none**        | Not implemented — same as above, range-based                   | Requires date range — can produce massive datasets               | Same as `copy_ticks_from`                                                       | N/A                                                       | none             | Medium — deferred to Phase 7                                   |

---

## Category 7: Advanced Facilities

| MT5 Function            | Bridge Coverage | Coverage Notes                                        | Constraints                                               | Known Broker Variance                                       | Fallback Behavior                | Test Coverage | Operator Readiness Impact                           |
| ----------------------- | --------------- | ----------------------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------- | -------------------------------- | ------------- | --------------------------------------------------- |
| Market Book Depth (DOM) | **none**        | `market_book_add/get/release` not implemented         | Requires subscription model; resource cleanup is critical | Not all brokers provide Level 2 data; data shape may differ | N/A — market depth not available | none          | Low — advanced trading feature, explicitly deferred |
| Custom Indicator Data   | **none**        | No bridge mechanism to query custom indicator outputs | Would require compiled indicator on the MT5 terminal      | Entirely broker/user-dependent; non-standardized            | N/A                              | none          | Low — out of scope for the bridge's role            |

> **Note**: Category 7 items are explicitly deferred and optional per the Phase 7 plan. They represent the lowest-priority gaps and may not be implemented within the current reliability rollout scope.

---

## Summary Statistics

### Coverage by Level

| Coverage Level | Function Count | Percentage |
| -------------- | -------------- | ---------- |
| **full**       | 17             | 52%        |
| **partial**    | 2              | 6%         |
| **none**       | 14             | 42%        |
| **Total**      | 33             | 100%       |

### Coverage by Category

| Category                | Total Functions | Full | Partial | None |
| ----------------------- | --------------- | ---- | ------- | ---- |
| 1. Connection & Session | 4               | 4    | 0       | 0    |
| 2. Terminal & Account   | 3               | 2    | 1       | 0    |
| 3. Symbol & Market Data | 8               | 4    | 1       | 3    |
| 4. Order Pre-check      | 3               | 1    | 0       | 2    |
| 5. Order Submission     | 5               | 3    | 0       | 2    |
| 6. History & Reporting  | 9               | 3    | 0       | 6    |
| 7. Advanced Facilities  | 1+              | 0    | 0       | 1+   |

### Top-3 Highest-Impact Gaps for Phase 7

| Priority | Gap                                            | Rationale                                                                                                                                                       | Effort Estimate                                                    |
| -------- | ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| **1**    | `mt5.order_calc_margin()`                      | Enables pre-trade risk assessment; margin data is partially available via `order_check` but a dedicated calculator is cleaner                                   | Low — single function wrapper                                      |
| **2**    | `mt5.symbol_select()`                          | Explicit symbol selection could prevent silent tick data failures for unselected symbols; especially relevant for direct-symbol trading via `mt5_symbol_direct` | Low — single function wrapper with `auto_select_symbols` config    |
| **3**    | `mt5.copy_ticks_from()` / `copy_ticks_range()` | Tick history enables micro-analysis and backtesting validation; currently only OHLCV bars are available                                                         | Medium — requires query size limits to prevent resource exhaustion |

### Test Coverage Health

| Test Level | Function Count |
| ---------- | -------------- |
| automated  | 15             |
| manual     | 0              |
| none       | 18             |

> **Note**: All 14 "none" coverage functions are also "none" test coverage. Implementing a function automatically requires adding tests per the constitution's testing standards.
