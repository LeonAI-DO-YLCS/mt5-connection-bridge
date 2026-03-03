# Research: MT5 Bridge Full Dashboard

**Branch**: `006-mt5-bridge-dashboard` | **Date**: 2026-03-02

---

## 1. Existing Architecture Analysis

### Worker Pattern (Single-Threaded Queue)

- **Decision**: Reuse the existing `mt5_worker.py` queue pattern for all new endpoints.
- **Rationale**: MT5 Python API is strictly single-threaded. The existing worker with `submit(fn) → Future` already handles this correctly with reconnection logic (exponential backoff, 5 retries, max 30s delay) and a `WorkerState` FSM.
- **Alternatives Considered**:
  - Direct `mt5.*()` calls from route handlers → Rejected: would break MT5's single-thread requirement.
  - `asyncio.to_thread()` pool → Rejected: MT5 is COM-bound to a single thread; pooling would cause race conditions.

### Concurrency Control (Single-Flight)

- **Decision**: Extend the existing single-flight mechanism from `/execute` to all new write endpoints (`/close-position`, `/pending-order`, `/orders/{ticket}`, `/positions/{ticket}/sltp`).
- **Rationale**: The `_inflight_lock` + `_inflight_requests` pattern prevents double-click races. Already proven in production for market orders.
- **Alternatives Considered**:
  - Per-resource locking (lock per ticket) → Rejected: adds complexity without clear benefit given the single-threaded MT5 backend already serializes operations.

### Safety Layers

- **Decision**: All new write endpoints inherit the full 7-layer safety stack.
- **Rationale**: The blueprint mandates these layers for all write operations. The existing stack already implements: (1) `execution_enabled` ENV gate, (2) API key auth, (3) single-flight, (4) pre/post-dispatch slippage checks, (5) pre-validation where applicable, (6) JSONL audit logging, (7) UI confirmation modals.
- **Alternatives Considered**: None — non-negotiable per constitution.

---

## 2. Technology Decisions

### New Pydantic Models

- **Decision**: Add 8 new models (`Position`, `Order`, `AccountInfo`, `TickPrice`, `TerminalInfo`, `Deal`, `HistoricalOrder`, `BrokerSymbol`) following existing patterns (Pydantic v2 `BaseModel`, `Field` descriptors, `from __future__ import annotations`).
- **Rationale**: Matches existing codebase conventions (`app/models/` directory, single model per file, exported via `__init__.py`).
- **Alternatives Considered**: Embedding new fields in existing models → Rejected: violates single-responsibility and would clutter `trade.py`.

### Enhanced TradeRequest

- **Decision**: Add `sl: float | None = None` and `tp: float | None = None` fields to the existing `TradeRequest` model.
- **Rationale**: Required by the blueprint (Phase 0, Section 2.1). Non-breaking change since both fields default to `None`.
- **Alternatives Considered**: Separate `MarketOrderRequest` model → Rejected: existing model is well-suited, and defaults maintain backward compatibility.

### Route Organization

- **Decision**: Separate endpoint files per concern (one file for account, one for positions, one for orders, etc.), matching the existing `app/routes/` pattern.
- **Rationale**: Each route file handles one logical resource. Self-documenting Swagger UI. Isolated test suites. Matches existing conventions.
- **Alternatives Considered**: Unified `/trade` endpoint → Rejected per blueprint Decision Matrix (Section 4).

### Dashboard UI Style

- **Decision**: Position cards (not tables) for positions and orders tabs.
- **Rationale**: Better fit for inline action buttons (Close, Modify SL/TP), mobile-responsive card stacking, and P&L color coding. Decided per blueprint Section 4.
- **Alternatives Considered**: Table-based view → Rejected per blueprint Decision Matrix (Section 4).

---

## 3. Dependency Research

### MT5 Trade Action Constants

| Constant                | Value | Used In          |
| :---------------------- | :---- | :--------------- |
| `TRADE_ACTION_DEAL`     | 1     | Market orders    |
| `TRADE_ACTION_PENDING`  | 5     | Pending orders   |
| `TRADE_ACTION_SLTP`     | 6     | Modify position  |
| `TRADE_ACTION_MODIFY`   | 7     | Modify order     |
| `TRADE_ACTION_REMOVE`   | 8     | Cancel order     |
| `TRADE_ACTION_CLOSE_BY` | 10    | Close by counter |

### MT5 Order Type Constants

| Constant                | Value | Used In              |
| :---------------------- | :---- | :------------------- |
| `ORDER_TYPE_BUY`        | 0     | Market buy           |
| `ORDER_TYPE_SELL`       | 1     | Market sell          |
| `ORDER_TYPE_BUY_LIMIT`  | 2     | Pending below market |
| `ORDER_TYPE_SELL_LIMIT` | 3     | Pending above market |
| `ORDER_TYPE_BUY_STOP`   | 4     | Pending above market |
| `ORDER_TYPE_SELL_STOP`  | 5     | Pending below market |

### MT5 API Functions Needed

| Function                   | Phase | Purpose                |
| :------------------------- | :---- | :--------------------- |
| `mt5.account_info()`       | 1     | Account balance/equity |
| `mt5.positions_get()`      | 1     | List open positions    |
| `mt5.orders_get()`         | 1     | List pending orders    |
| `mt5.symbol_info_tick()`   | 1     | Current bid/ask        |
| `mt5.terminal_info()`      | 1     | Terminal diagnostics   |
| `mt5.order_send()`         | 2,3   | Close/place orders     |
| `mt5.order_check()`        | 3     | Pre-validate orders    |
| `mt5.history_deals_get()`  | 4     | Historical deals       |
| `mt5.history_orders_get()` | 4     | Historical orders      |
| `mt5.symbols_get()`        | 4     | Broker symbol catalog  |

---

## 4. Testing Strategy

- **Decision**: Follow existing test structure: `tests/unit/` for models + mappers, `tests/integration/` for route-level tests via `TestClient`, `tests/contract/` for schema conformance.
- **Rationale**: Matches established patterns. Existing `conftest.py` already provides test fixtures for the FastAPI app.
- **Alternatives Considered**: None — the existing structure is well-organized and proven.

---

## 5. Resolved Unknowns

All technical context items resolved — zero NEEDS CLARIFICATION remaining.

| Item                 | Resolution                                          |
| :------------------- | :-------------------------------------------------- |
| Language/Version     | Python 3.11+ (confirmed from constitution)          |
| Primary Dependencies | FastAPI, Pydantic v2, MetaTrader5 (confirmed)       |
| Storage              | N/A (no database; MT5 is the source of truth)       |
| Testing              | pytest + httpx TestClient (confirmed from codebase) |
| Target Platform      | Windows host (MT5), Linux Docker (AI Hedge Fund)    |
| Performance Goals    | < 1s per API response under normal conditions       |
| Constraints          | Single-threaded MT5 access via worker queue         |
