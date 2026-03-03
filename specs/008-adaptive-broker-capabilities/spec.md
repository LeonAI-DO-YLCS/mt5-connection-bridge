# Feature Specification: Adaptive Broker Capabilities

**Feature Branch**: `008-adaptive-broker-capabilities`
**Created**: 2026-03-02
**Status**: Draft
**Input**: See `docs/plans/adaptive-broker-capabilities.md` for the full exploration plan.

---

## Overview

The MT5 Bridge and its dashboard currently make four categories of hardcoded assumptions about the connected broker. These assumptions cause silent failures or user-visible errors when the broker's actual capabilities differ from the defaults.

This feature makes the bridge and dashboard **fully adaptive**: every broker-specific constraint (order filling mode, supported symbols, symbol categories, per-symbol trade direction rules) is read directly from the live MT5 terminal at runtime, never hardcoded.

---

## User Scenarios & Testing _(mandatory)_

### Primary User Story

As a trader using the dashboard, I want the Execute tab to show me every symbol my broker offers grouped by their real categories, and automatically prevent me from placing orders that my broker does not support for a given symbol — so that I never receive a confusing broker rejection error.

As a system operator, I want the bridge to automatically detect and adapt to the filling modes, trade modes, and symbol catalog of any connected MT5 broker — so that the system works correctly without manual YAML maintenance for each new broker or instrument.

### Acceptance Scenarios

1. **Given** a connected MT5 terminal with a symbol that only supports RETURN filling mode, **When** a market order is submitted for that symbol, **Then** the order uses RETURN filling mode and executes successfully (no retcode=10030).

2. **Given** a connected MT5 terminal, **When** the user opens the Execute tab, **Then** the ticker dropdown lists every tradeable symbol the broker provides, grouped by the exact same categories as the MT5 Symbols tree.

3. **Given** a connected MT5 terminal, **When** the user opens the Symbols tab, **Then** the category filter dropdown is built dynamically from the real MT5 symbol hierarchy — not from a hardcoded list of categories.

4. **Given** a symbol with trade mode "Long Only" (buy only), **When** the user selects that symbol in the Execute tab, **Then** the Sell/Short option is visually disabled before submission, and a clear explanation is shown.

5. **Given** a symbol with trade mode "Long Only", **When** a sell order is submitted via the API directly, **Then** the bridge rejects it with a descriptive error message (not a broker rejection code).

6. **Given** a newly offered symbol on the broker (not in `config/symbols.yaml`), **When** the user opens the Execute or Prices tab, **Then** the new symbol is visible and selectable without any configuration file change.

7. **Given** the broker's symbol catalog has been fetched, **When** the user requests a manual refresh of capabilities, **Then** the catalog is re-fetched from MT5 and updated across all dashboard tabs.

8. **Given** the terminal or account has `trade_allowed = false`, **When** the user views the dashboard Status tab, **Then** a prominent warning panel shows which trading restriction is active.

### Edge Cases

- What happens when a symbol has no `path` set by the broker? → It is placed in a fallback "Other" category.
- What happens when a symbol's `filling_mode` bitmask is 0 (no FOK or IOC)? → RETURN filling mode is used (the implicit MT5 fallback).
- What happens when `symbols_get()` returns more than 1,000 symbols? → The result is cached and the dropdown includes a text search/filter to avoid overwhelming the user.
- What happens when the MT5 terminal disconnects mid-session? → The last-known capabilities cache continues to serve requests; a stale-data banner is shown.
- What happens when a symbol path uses `/` as separator instead of `\`? → Path parsing normalizes both separators before splitting.
- What happens when `trade_mode` returns an undocumented integer value? → The symbol is treated as fully tradeable, with a warning logged.

---

## Requirements _(mandatory)_

### Functional Requirements

**Filling Mode (Order Execution)**

- **FR-001**: The bridge MUST resolve the correct order filling mode for each symbol at order submission time by reading the symbol's filling capability bitmask from the MT5 terminal.
- **FR-002**: The bridge MUST select filling modes in priority order: FOK first, then IOC, then RETURN — using only modes the symbol supports.
- **FR-003**: The bridge MUST apply dynamic filling mode resolution to market orders, pending orders, and position close requests.

**Trade Mode Enforcement**

- **FR-004**: The bridge MUST reject a buy or cover order for a symbol whose trade mode prohibits long positions, returning a descriptive human-readable error before sending the order to MT5.
- **FR-005**: The bridge MUST reject a sell or short order for a symbol whose trade mode prohibits short positions, returning a descriptive error before sending the order to MT5.
- **FR-006**: The bridge MUST reject any new position order (both directions) for symbols in close-only or trading-disabled mode, with a descriptive error.
- **FR-007**: Trade mode enforcement MUST apply to both market orders (`POST /execute`) and pending limit/stop orders (`POST /pending-order`).

**Broker Capabilities Endpoint**

- **FR-008**: The bridge MUST expose a single endpoint that returns the complete broker symbol catalog, including for each symbol: its name, description, broker path, derived category, derived subcategory, filling mode details, trade mode details, volume constraints, spread, and Market Watch visibility status.
- **FR-009**: The broker capabilities endpoint MUST also return account-level and terminal-level trade authorization flags (whether trading is allowed by the account and by the terminal).
- **FR-010**: The broker capabilities endpoint MUST return a pre-computed category tree that maps each top-level category to its subcategories, derived from the actual MT5 symbol paths.
- **FR-011**: The bridge MUST cache the broker capabilities response in memory, with a configurable time-to-live (default: 60 seconds), to avoid redundant MT5 calls on frequent dashboard polls.
- **FR-012**: The bridge MUST provide a manual refresh endpoint that invalidates the capabilities cache and re-fetches from MT5 on demand.
- **FR-013**: The capabilities cache MUST be automatically invalidated whenever the MT5 worker reconnects to the terminal.

**Symbol Discovery — Dashboard Execute Tab**

- **FR-014**: The Execute tab MUST populate its ticker dropdown from the live broker symbol catalog (not from `config/symbols.yaml`), showing all symbols whose trade mode allows new positions.
- **FR-015**: The Execute tab ticker dropdown MUST group symbols using `<optgroup>` elements that reflect the broker's real category hierarchy.
- **FR-016**: When a symbol is selected in the Execute tab, the system MUST read the symbol's trade mode and disable the Buy or Sell option if that direction is not permitted for that symbol, displaying a tooltip or inline message explaining the restriction.
- **FR-017**: The Execute tab MUST disable the Submit button and display a warning banner for symbols in close-only or trading-disabled mode.

**Symbol Discovery — Dashboard Symbols Browser Tab**

- **FR-018**: The Symbols Browser tab category filter dropdown MUST be built dynamically from the live broker category tree — not from a hardcoded list.
- **FR-019**: The Symbols Browser table MUST display each symbol's derived category, derived subcategory, trade mode (with a color-coded badge), and supported filling modes.
- **FR-020**: The Symbols Browser MUST provide a toggle to show or hide symbols with trade mode "Disabled" (which are hidden by default).

**Dashboard Prices Tab**

- **FR-021**: The Prices tab ticker dropdown MUST be populated from the live broker symbol catalog, allowing the user to query prices for any symbol the broker provides — not only those in `config/symbols.yaml`.

**Dashboard Status Tab**

- **FR-022**: The Status tab MUST display a clear capability panel showing: terminal trade allowed status, account trade allowed status, and execution policy status — with visual indicators (green/red) for each.
- **FR-023**: If either terminal or account trade authorization is `false`, the Status tab MUST display a prominent warning banner.

**Backward Compatibility**

- **FR-024**: The existing `GET /symbols` endpoint and `config/symbols.yaml` strategy alias layer MUST remain unchanged and functional, as they are used by the AI hedge fund trading strategies to map their own tickers to MT5 symbols.
- **FR-025**: The existing `GET /broker-symbols` endpoint MUST remain functional, extended with additional fields (category, subcategory, filling mode, trade mode, volume step, visibility) rather than replaced.

**Configuration**

- **FR-026**: The capabilities cache time-to-live MUST be configurable via an environment variable without code changes.
- **FR-027**: The system MUST support an environment variable to control whether symbols are automatically selected in the MT5 Market Watch when a capability scan is performed.

### Key Entities

- **BrokerSymbol**: A single instrument available on the connected broker, with its full set of trading constraints from MT5 (name, path, category, subcategory, filling mode bitmask, trade mode, volume limits, spread, visibility flag).
- **BrokerCapabilities**: The full snapshot of what this broker supports at a given point in time — the symbol list, the category tree, account trade authorization, and terminal trade authorization.
- **CategoryTree**: A hierarchical structure derived from MT5 symbol paths, mapping top-level categories (e.g., "Forex") to their subcategories (e.g., ["Majors", "Minors"]).
- **FillingMode**: An attribute of a symbol describing which order filling behaviors (FOK, IOC, RETURN) the broker allows for that instrument.
- **TradeMode**: An attribute of a symbol describing which trade directions (buy, sell, both, close-only, none) the broker allows for that instrument.

---

## Success Criteria _(mandatory)_

1. **Zero broker rejection errors due to filling mode**: After this feature is live, no order rejected with retcode=10030 ("Unsupported filling mode") is produced by the bridge for any symbol on any supported broker.

2. **Dashboard reflects broker state without configuration**: A new symbol added at the broker level appears in the Execute, Prices, and Symbols tabs within one cache TTL cycle (≤ 60 seconds by default) without any change to `config/symbols.yaml` or any other file.

3. **Category accuracy**: The Symbols Browser category and subcategory values exactly match the MT5 Symbols tree folder hierarchy for 100% of returned symbols.

4. **Trade mode guard effectiveness**: 100% of buy/sell orders that violate a symbol's trade mode are rejected by the bridge with a human-readable error before reaching the MT5 terminal.

5. **Dashboard usability with large catalogs**: The Execute tab ticker dropdown and Symbols Browser remain usable (search/filter provided) when the broker offers more than 500 symbols.

6. **Backward compatibility intact**: All existing API consumers (AI hedge fund strategies, `GET /symbols`, `GET /broker-symbols`) continue to function without modification after this feature is deployed.

7. **Stale-data resilience**: When the MT5 terminal briefly disconnects, the dashboard continues to show the last-known capabilities with a visible freshness/stale data indicator rather than showing an error.

---

## Assumptions

- `config/symbols.yaml` is intentionally a strategy alias layer (mapping human-readable tickers like "V75" to MT5 symbol names). It is NOT a broker catalog and should not be treated as one. Both serve different purposes and both are kept.
- The MT5 `symbol_info.path` field uses `\` as the segment separator on Windows (the only supported environment for MT5). The path may occasionally use `/` depending on the broker; the implementation normalizes both.
- The MT5 `filling_mode` bitmask of `0` (no bits set) means only RETURN filling is possible — this is the implicit MT5 fallback and is always safe to use.
- Unknown `trade_mode` integer values (not in the documented 0–4 range) are treated conservatively as "Full" (SYMBOL_TRADE_MODE_FULL) to avoid blocking trades that the broker may actually allow, with a warning emitted to the bridge log.
- The capabilities cache is stored in memory only (not persisted to disk). After a bridge restart, the first request refreshes the cache.
- The existing MT5 worker threading model (single-threaded queue via `submit()`) is not changed. All new MT5 calls use the same `submit()` mechanism.

---

## Out of Scope

- Changes to the AI hedge fund trading strategy layer or LangGraph orchestration.
- Streaming/real-time symbol updates (the TTL polling model is sufficient).
- Persistent caching of capabilities to disk or database.
- UI redesign beyond the specific tab changes described in the requirements.
- Authentication or authorization changes.
- Support for brokers other than MT5 (non-MT5 execution adapters are out of scope).
