# Feature Specification: MT5 Bridge Full Dashboard

**Feature Branch**: `006-mt5-bridge-dashboard`  
**Created**: 2026-03-02  
**Status**: Draft  
**Input**: User description: "Implement the full MT5 Bridge Dashboard covering all 5 phases from the phased blueprint — Foundations, Visibility, Management, Execution, and History & Discovery — to bring bridge coverage from ~30% to ~98% of MT5's capabilities."

---

## Overview

The MT5 Bridge currently provides only basic functionality: a health check endpoint, historical OHLCV price retrieval, and simple market-order execution. The dashboard has no visibility into open positions, no pending order management, no account balance information, and no trade history audit trail.

This feature closes all 9 identified capability gaps (G1–G9) by delivering 15 new API endpoints, 3 new dashboard tabs, 1 rebuilt dashboard tab, and a 7-layer safety architecture — organized as 5 sequential phases that build on each other.

---

## User Scenarios & Testing _(mandatory)_

### Primary User Story

As a **trader using the AI Hedge Fund dashboard**, I want to see my open positions, pending orders, and account balance in real time, manage my trades (close, modify, cancel), place new orders (market and pending) with pre-validation, and review my complete trade history — so that I can manage my entire trading workflow from a single dashboard without switching to the MT5 terminal.

### Acceptance Scenarios

#### Phase 0 — Foundations

1. **Given** the bridge service is running, **When** it starts up, **Then** all shared data models (Position, Order, Account) are available for downstream endpoints and all trade requests support optional stop-loss and take-profit parameters.
2. **Given** a trade request is submitted, **When** the mapper processes it, **Then** the SL/TP values are correctly forwarded to MT5 (or defaulted to 0.0 if not provided).
3. **Given** any write operation is attempted, **Then** it must pass through the 7-layer safety architecture (execution gate, API key auth, concurrency control, slippage protection, pre-validation where applicable, audit logging, UI confirmation).

#### Phase 1 — Visibility

4. **Given** the trader opens the dashboard, **When** the Positions tab loads, **Then** all open positions are displayed as cards showing symbol, direction, volume, entry price, current price, P&L, SL/TP, and swap — refreshing every 5 seconds.
5. **Given** the trader navigates to the Orders tab, **When** pending orders exist, **Then** each is shown as a card with symbol, order type, trigger price, volume, SL/TP, and setup time — refreshing every 10 seconds.
6. **Given** the trader views the Status tab, **When** it loads, **Then** an Account Summary panel shows balance, equity, margin, free margin, profit, currency, and leverage; and a Terminal Diagnostics panel shows build info and connection status.
7. **Given** the trader uses the Prices tab, **When** they select a ticker from the dropdown, **Then** the system fetches and displays current bid, ask, spread, and timestamp for that symbol.

#### Phase 2 — Management

8. **Given** an open position is displayed, **When** the trader clicks "Close" and confirms the modal, **Then** the position is closed (full) and removed from the active positions list.
9. **Given** an open position is displayed, **When** the trader selects a partial close volume and confirms, **Then** only the selected volume is closed and the remaining position is updated.
10. **Given** an open position is displayed, **When** the trader expands the "Modify SL/TP" inline form and submits new values, **Then** the position's stop-loss and take-profit are updated on MT5.
11. **Given** a pending order exists, **When** the trader clicks "Cancel" and confirms the modal, **Then** the order is removed from MT5 and disappears from the Orders tab.
12. **Given** a pending order exists, **When** the trader modifies its trigger price, SL, or TP through the inline form, **Then** the order is updated on MT5 and the card reflects the new values.

#### Phase 3 — Execution

13. **Given** the trader opens the Execute tab, **When** they select an order type (Market, Buy Limit, Sell Limit, Buy Stop, Sell Stop), **Then** the form dynamically shows/hides relevant fields (e.g., "Trigger Price" for pending orders only).
14. **Given** the trader selects a ticker, **When** the ticker changes, **Then** the current bid/ask is auto-fetched and displayed alongside the order form.
15. **Given** the trader fills out an order form, **When** the form values stabilize (500ms debounce), **Then** a pre-validation check runs showing validity status, required margin, estimated profit (if TP set), and post-trade equity projection.
16. **Given** the trader submits a pending order, **When** the pre-validation passes and confirmation is given, **Then** the order is placed on MT5 and appears on the Orders tab.

#### Phase 4 — History & Discovery

17. **Given** the trader opens the Trade History tab, **When** they select a date range, **Then** the system displays historical deals (fills) including ticket, symbol, direction, entry/exit, volume, price, profit, swap, commission, and fee.
18. **Given** the Trade History tab is open, **When** the trader switches to the "Orders" sub-tab, **Then** historical orders are shown with their final state (filled, cancelled, expired, rejected).
19. **Given** the trader clicks "Export to CSV," **When** the export completes, **Then** a CSV file is downloaded containing all records currently displayed in the history table.
20. **Given** the trader opens the Broker Symbols browser, **When** they search or filter by group (Forex, Indices, Crypto), **Then** all matching symbols from the broker catalog are displayed with name, description, spread, digits, volume range, trade mode, and whether the symbol is already configured in the bridge.

### Edge Cases

- **What happens when** the MT5 terminal is disconnected? → The bridge returns an appropriate error response and the dashboard shows a "Terminal Disconnected" banner. Read-only tabs show stale data with a "Last updated" timestamp. Write operations are blocked.
- **What happens when** a position close fails due to insufficient volume step? → The system returns a clear error message and the UI prevents submission of invalid volume increments using the symbol's `volume_step` constraint.
- **What happens when** a pending order is no longer valid (e.g., price already passed)? → The pre-validation check catches this and shows an ❌ with an explanation before the order is submitted.
- **What happens when** the user double-clicks a "Close" or "Cancel" button? → Single-flight concurrency control prevents duplicate submissions; the second click is silently ignored.
- **What happens when** the trade history query returns no results? → The UI displays an empty-state message: "No trades found for this period."
- **What happens when** the broker symbol catalog is very large (1000+ symbols)? → The results are paginated or filtered by group, and the search is debounced to prevent excessive API calls.

---

## Requirements _(mandatory)_

### Functional Requirements

#### Foundations (Phase 0)

- **FR-001**: System MUST provide shared data models for Position, Order, Account, Terminal, and Tick data that serve as the contract between backend endpoints and the dashboard.
- **FR-002**: System MUST accept optional stop-loss (SL) and take-profit (TP) parameters on all market order requests.
- **FR-003**: System MUST map all position data from MT5's native format to the bridge's standardized model (including ticket, symbol, type, volume, open price, current price, SL, TP, profit, swap, time, magic number, and comment).
- **FR-004**: System MUST enforce a 7-layer safety architecture on all write operations: execution gate, API key authentication, concurrency control, slippage protection, pre-validation (where applicable), audit logging, and UI confirmation dialogs.
- **FR-005**: System MUST log all trade operations (executions, closures, modifications, cancellations) to an append-only audit log for traceability.

#### Visibility (Phase 1)

- **FR-006**: System MUST provide read-only access to retrieve current account information (balance, equity, margin, free margin, profit, currency, leverage).
- **FR-007**: System MUST provide read-only access to list all currently open positions with full detail (ticket, symbol, type, volume, open price, current price, SL, TP, profit, swap, time).
- **FR-008**: System MUST provide read-only access to list all active pending orders with full detail (ticket, symbol, type, volume, trigger price, SL, TP, setup time).
- **FR-009**: System MUST provide read-only access to fetch the current tick (bid, ask, spread, timestamp) for any configured symbol.
- **FR-010**: System MUST provide read-only access to return MT5 terminal diagnostic information (build, name, path, connection status, trade-allowed flag).
- **FR-011**: Dashboard MUST display open positions as cards with auto-refresh at 5-second intervals.
- **FR-012**: Dashboard MUST display pending orders as cards with auto-refresh at 10-second intervals.
- **FR-013**: Dashboard MUST show an Account Summary panel with key financial metrics (balance, equity, margin, free margin, total unrealized P&L).
- **FR-014**: Dashboard MUST provide an interactive ticker dropdown for fetching current prices, populated from the available symbols.

#### Management (Phase 2)

- **FR-015**: System MUST allow full closure of an open position by submitting a counter-order with the full position volume.
- **FR-016**: System MUST allow partial closure of an open position by specifying a sub-volume (constrained by the symbol's volume step).
- **FR-017**: System MUST allow modification of an open position's stop-loss and take-profit values.
- **FR-018**: System MUST allow cancellation of a pending order.
- **FR-019**: System MUST allow modification of a pending order's trigger price, stop-loss, and take-profit.
- **FR-020**: All destructive operations (close, cancel) MUST require explicit user confirmation via a modal dialog.
- **FR-021**: "Close All" and "Cancel All" batch operations MUST require an additional checkbox confirmation beyond the standard modal.
- **FR-022**: All management actions MUST be gated by the execution-enabled policy flag.

#### Execution (Phase 3)

- **FR-023**: System MUST allow placement of pending orders (Buy Limit, Sell Limit, Buy Stop, Sell Stop) with ticker, volume, trigger price, SL, TP, and comment.
- **FR-024**: System MUST provide pre-validation checks for order feasibility (margin, validity) without executing the trade.
- **FR-025**: Dashboard MUST rebuild the Execute tab with an order type selector (Market, Buy Limit, Sell Limit, Buy Stop, Sell Stop) and dynamically show/hide the "Trigger Price" field based on selection.
- **FR-026**: Dashboard MUST auto-fetch and display current bid/ask when the selected ticker changes.
- **FR-027**: Dashboard MUST show a live pre-validation panel that updates with a 500ms debounce as the user fills the order form, displaying validity status, required margin, estimated profit, and post-trade equity projection.
- **FR-028**: Volume input MUST be constrained by the broker's minimum, maximum, and step-size for the selected symbol.

#### History & Discovery (Phase 4)

- **FR-029**: System MUST provide retrieval of historical deals (fills) filtered by date range, with optional symbol and position filters.
- **FR-030**: System MUST provide retrieval of historical orders (completed/cancelled/expired/rejected) filtered by date range.
- **FR-031**: System MUST provide discovery of all symbols available from the broker, with optional group filtering.
- **FR-032**: Dashboard MUST display a Trade History tab with sub-tabs for Deals and Orders, a date range picker, summary statistics (net profit, total swap, total commission, trade count), and a CSV export button.
- **FR-033**: Dashboard MUST display a Broker Symbols browser integrated into the Symbols tab, showing the full broker catalog with search, group filtering, and a "configured" status indicator.
- **FR-034**: History data formats MUST accept dates consistently across components without exposing underlying MT5 time formatting constraints.

### Key Entities

- **Position**: Represents an open trade on the MT5 terminal, identified by a ticket number. Contains symbol, direction (buy/sell), volume, entry price, current price, stop-loss, take-profit, unrealized profit, swap, timestamp, magic number, and comment.
- **Order**: Represents a pending instruction to open a trade at a specified price. Contains ticket, symbol, order type (limit/stop), volume, trigger price, stop-loss, take-profit, setup time, and magic number.
- **Account**: Represents the trader's financial state. Contains login, server, balance, equity, margin, free margin, unrealized profit, account currency, and leverage.
- **Deal**: Represents a historical fill (completed transaction). Contains ticket, original order ticket, position ID, symbol, deal type, entry direction (in/out), volume, price, profit, swap, commission, fee, timestamp, and magic number.
- **Historical Order**: An order that has reached a terminal state. Extends Order with a state field (filled, cancelled, expired, rejected).
- **Broker Symbol**: Represents a tradable instrument available from the broker. Contains name, description, category path, spread, decimal digits, volume constraints, trade mode, and whether it's configured in the local bridge.
- **Terminal**: Represents the MT5 terminal instance. Contains build number, name, data path, connection status, and trade-allowed flag.
- **Tick**: A single price snapshot for a symbol. Contains ticker, bid, ask, spread, and timestamp.

---

## Success Criteria _(mandatory)_

1. **Full Visibility**: Traders can view all open positions, pending orders, and account financial metrics within 2 seconds of opening the dashboard.
2. **Real-Time Updates**: Position and order data refreshes automatically without manual page reloads — positions every 5 seconds, orders every 10 seconds.
3. **Trade Lifecycle Control**: Traders can close (full or partial), modify (SL/TP), and cancel trades directly from the dashboard without switching to the MT5 terminal.
4. **Zero Accidental Trades**: All destructive operations require explicit confirmation. No trade can be submitted twice from a single user action. Batch operations require double-confirmation.
5. **Order Flexibility**: Traders can place all 5 order types (Market, Buy Limit, Sell Limit, Buy Stop, Sell Stop) with appropriate risk parameters (SL/TP).
6. **Pre-Trade Confidence**: Before submitting any order, traders see real-time validation showing margin requirements, feasibility, and projected equity impact.
7. **Complete Audit Trail**: Traders can retrieve and review their complete trade history (deals and orders) for any date range, with net-profit, swap, and commission summaries.
8. **Symbol Discovery**: Traders can search and browse the full broker symbol catalog (1000+ symbols) with group filtering and see which symbols are already configured.
9. **Data Export**: Traders can export any historical trade data view to CSV format for external analysis.
10. **Safety Guarantee**: All write operations pass through 7 safety layers. No write operation is possible when the execution-enabled flag is disabled.
11. **Capability Coverage**: The bridge's functional coverage of MT5's capabilities increases from ~30% to ~98%.
12. **Error Resilience**: When the MT5 terminal is disconnected, the dashboard degrades gracefully — showing stale data with timestamps and blocking write operations — without crashing.

---

## Assumptions

- The MT5 terminal is always running on the Windows host machine while the bridge is operational.
- The bridge's existing worker queue pattern (single-threaded MT5 access) is suitable for the expected request volume and will be used for all new endpoints.
- The existing API key authentication mechanism is sufficient for securing all new endpoints.
- Standard web application performance targets apply (page loads < 2 seconds, API responses < 1 second under normal conditions).
- The `symbols.yaml` configuration file will continue to serve as the source of configured symbols, with the broker symbols browser providing discovery of additional unconfigured symbols.
- Auto-refresh intervals (5s for positions, 10s for orders) are appropriate for the trading workflow and won't cause excessive load on the MT5 terminal.
- The existing JSONL audit log format is adequate for trade operation logging.
- Session-based or API-key-based authentication is already in place; no new authentication system is needed.

---

## Dependencies

- **MT5 Terminal**: Must be running and connected to the broker on the Windows host machine.
- **Existing Bridge Infrastructure**: Worker queue, health check, configuration loading, and authentication middleware must be operational (Phase 0 prerequisite).
- **Phased Build Order**: Each phase depends on the previous — Phase 1 depends on Phase 0 models, Phase 2 depends on Phase 1 endpoints, Phase 3 depends on Phase 2 patterns, and Phase 4 is independent but benefits from all prior infrastructure.

---

## Scope Boundaries

### In Scope

- All backend API endpoints described in Phases 0–4 of the phased blueprint.
- Dashboard UI tabs: Positions, Orders, Execute (rebuilt), Trade History, Broker Symbols browser.
- Safety architecture: 7-layer protection on all write operations.
- Data export (CSV) for trade history.
- Auto-refresh for real-time data views.

### Out of Scope

- React frontend modifications to the AI Hedge Fund main app (per architectural directive).
- Changes to the core backtester engine.
- WebSocket/streaming connections for real-time data (manual polling is used instead).
- Charting or advanced technical analysis tools.
- Multi-account management (single MT5 account per bridge instance).
- Mobile-specific responsive optimizations beyond basic card-stacking.

---

## Review & Acceptance Checklist

_GATE: Automated checks run during main() execution_

### Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

### Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed
