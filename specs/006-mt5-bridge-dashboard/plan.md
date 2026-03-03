# Implementation Plan: MT5 Bridge Full Dashboard

**Branch**: `006-mt5-bridge-dashboard` | **Date**: 2026-03-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/006-mt5-bridge-dashboard/spec.md`

---

## Summary

The MT5 Bridge currently operates at ~30% of MT5's capabilities with 3 core endpoints (`/health`, `/prices`, `/execute`). This plan extends the bridge to ~98% coverage by adding 15 new API endpoints, 3 new dashboard tabs, 1 rebuilt dashboard tab, and a 7-layer safety architecture. All new backend work follows the established single-threaded worker queue pattern, Pydantic model conventions, and pytest test structure.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Pydantic v2, MetaTrader5 Python API, uvicorn
**Storage**: N/A (MT5 terminal is the data source; JSONL for audit logs)
**Testing**: pytest, httpx TestClient, existing `conftest.py` fixtures
**Target Platform**: Windows host (MT5 runtime), Linux Docker (AI Hedge Fund consumer)
**Project Type**: Web application (FastAPI backend + HTML/JS dashboard)
**Performance Goals**: < 1s per API response under normal conditions
**Constraints**: Single-threaded MT5 access via worker queue; no changes to React frontend or backtester engine
**Scale/Scope**: Single MT5 account per bridge instance

---

## Constitution Check (v1.1.0)

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

| Principle                                | Status  | Notes                                                                                                                                                                                        |
| :--------------------------------------- | :-----: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **I. Multi-Agent Orchestration**         | ✅ PASS | No impact — bridge is an adapter, not an agent. Agents consume bridge data.                                                                                                                  |
| **II. Trading Modes & Execution Safety** | ✅ PASS | All write endpoints gated by `execution_enabled` ENV policy. Audit logs maintained for all execution modes.                                                                                  |
| **III. Data-Driven Valuation**           | ✅ PASS | No impact — bridge provides raw data; valuation agents are upstream.                                                                                                                         |
| **IV. Risk-Managed Decision Making**     | ✅ PASS | Pre-validation (`/order-check`) adds a risk verification layer. All operations pass through 7-layer safety architecture.                                                                     |
| **V. Execution & Connection Frameworks** | ✅ PASS | Bridge is a pluggable adapter module. Worker handles connection persistence, failure recovery with exponential backoff.                                                                      |
| **VI. MT5 Connection Framework**         | ✅ PASS | Connection persistence via `mt5_worker.py`. Symbol management via `symbols.yaml`. Tick data via `/tick/{ticker}`. Slippage protection on execution. Order confirmation before state updates. |
| **Tech Stack**                           | ✅ PASS | Python 3.11+, FastAPI, MT5 Python API — all aligned.                                                                                                                                         |
| **Dev Workflow**                         | ✅ PASS | Working on feature branch `006-mt5-bridge-dashboard`. Spec → Plan → Tasks → Implementation flow.                                                                                             |

**Initial Constitution Check**: ✅ PASS (all 8 principles satisfied)

---

## Project Structure

### Documentation (this feature)

```
specs/006-mt5-bridge-dashboard/
├── spec.md                       ✅ Complete
├── plan.md                       ✅ This file
├── research.md                   ✅ Complete
├── data-model.md                 ✅ Complete
├── quickstart.md                 ✅ Complete
├── contracts/
│   └── api-contracts.md          ✅ Complete
├── checklists/
│   └── requirements.md           ✅ Complete
└── tasks.md                      ⬜ /tasks command
```

### Source Code (repository root)

```
app/
├── models/
│   ├── __init__.py               # Update: export new models
│   ├── trade.py                  # Modify: add sl/tp fields
│   ├── position.py               # NEW
│   ├── order.py                  # NEW
│   ├── account.py                # NEW
│   ├── tick.py                   # NEW
│   ├── terminal.py               # NEW
│   ├── deal.py                   # NEW
│   ├── historical_order.py       # NEW
│   ├── broker_symbol.py          # NEW
│   ├── close_position.py         # NEW
│   ├── modify_sltp.py            # NEW
│   ├── modify_order.py           # NEW
│   ├── pending_order.py          # NEW
│   └── order_check.py            # NEW
├── mappers/
│   ├── trade_mapper.py           # Modify: add close/pending/modify/cancel builders
│   ├── position_mapper.py        # NEW
│   ├── order_mapper.py           # NEW
│   ├── account_mapper.py         # NEW
│   └── history_mapper.py         # NEW
├── routes/
│   ├── account.py                # NEW
│   ├── positions.py              # NEW
│   ├── orders.py                 # NEW
│   ├── tick.py                   # NEW
│   ├── terminal.py               # NEW
│   ├── close_position.py         # NEW
│   ├── pending_order.py          # NEW
│   ├── order_check.py            # NEW
│   ├── history.py                # NEW
│   └── broker_symbols.py         # NEW
├── main.py                       # Modify: register new routers

dashboard/
├── js/
│   ├── positions.js              # NEW
│   ├── orders.js                 # NEW
│   ├── execute-v2.js             # NEW (rebuilt Execute tab)
│   ├── history.js                # NEW
│   └── symbols-browser.js        # NEW
├── css/
│   └── style.css                 # Modify: add new tab styles
└── index.html                    # Modify: add new tab navigation

tests/
├── unit/
│   ├── test_position_mapper.py   # NEW
│   ├── test_order_mapper.py      # NEW
│   ├── test_account_mapper.py    # NEW
│   ├── test_history_mapper.py    # NEW
│   └── test_trade_mapper_v2.py   # NEW (close/pending/modify builders)
├── integration/
│   ├── test_account_route.py     # NEW
│   ├── test_positions_route.py   # NEW
│   ├── test_orders_route.py      # NEW
│   ├── test_tick_route.py        # NEW
│   ├── test_terminal_route.py    # NEW
│   ├── test_close_position.py    # NEW
│   ├── test_pending_order.py     # NEW
│   ├── test_order_check.py       # NEW
│   ├── test_modify_sltp.py       # NEW
│   ├── test_modify_order.py      # NEW
│   ├── test_cancel_order.py      # NEW
│   ├── test_history_deals.py     # NEW
│   ├── test_history_orders.py    # NEW
│   └── test_broker_symbols.py    # NEW
└── contract/
    ├── test_visibility_contracts.py   # NEW
    ├── test_management_contracts.py   # NEW
    ├── test_execution_contracts_v2.py # NEW
    └── test_history_contracts.py      # NEW
```

**Structure Decision**: Web application pattern — FastAPI backend (`app/`) + HTML/JS dashboard (`dashboard/`). New files follow existing conventions: one model per file, one route per resource, dedicated mapper files per entity group.

---

## Phase 0: Outline & Research

**Status**: ✅ Complete — See [research.md](./research.md)

All technical unknowns resolved:

- Worker pattern: reuse existing single-threaded queue
- Concurrency control: extend single-flight to all write endpoints
- Safety layers: 7-layer stack inherited by all write endpoints
- MT5 API coverage: 10 new MT5 functions mapped
- Testing strategy: follow existing unit/integration/contract structure

---

## Phase 1: Design & Contracts

**Status**: ✅ Complete

Outputs:

- [data-model.md](./data-model.md) — 8 new entities, 5 request/response models, 5 new mapper files
- [contracts/api-contracts.md](./contracts/api-contracts.md) — 15 new endpoints with full request/response schemas
- [quickstart.md](./quickstart.md) — Verification commands for each phase

---

## Phase 2: Task Planning Approach

_This section describes what the `/tasks` command will do — DO NOT execute during `/plan`_

**Task Generation Strategy**:

- Load data-model.md entities → model creation tasks per file
- Load api-contracts.md endpoints → route implementation tasks per endpoint
- Load data-model.md mappers → mapper creation tasks per file
- Dashboard tab tasks from feature spec
- Each entity → unit test task
- Each route → integration test task
- Each phase → contract test task

**Ordering Strategy** (TDD, dependency-first):

1. **Models first** (no dependencies): Position, Order, Account, TickPrice, TerminalInfo, Deal, HistoricalOrder, BrokerSymbol + request models → can be parallel `[P]`
2. **TradeRequest enhancement** (modify existing)
3. **Mappers** (depend on models): position, order, account, history, trade_mapper enhancements
4. **Unit tests for mappers** (depend on mappers + models)
5. **Routes** (depend on mappers + models + worker): Phase 1 read-only endpoints first, then Phase 2 management, Phase 3 execution, Phase 4 history
6. **Integration tests for routes** (depend on routes)
7. **Contract tests** (depend on routes)
8. **main.py router registration** (depend on all routes)
9. **Dashboard UI** (depend on all routes being functional): tabs, JS files, CSS updates
10. **End-to-end quickstart verification**

**Estimated Output**: ~35-40 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the `/tasks` command, NOT by `/plan`

---

## Post-Design Constitution Check

| Principle                                | Status  | Notes                                                                                                                                               |
| :--------------------------------------- | :-----: | :-------------------------------------------------------------------------------------------------------------------------------------------------- |
| **I. Multi-Agent Orchestration**         | ✅ PASS | Unchanged — adapter pattern maintained.                                                                                                             |
| **II. Trading Modes & Execution Safety** | ✅ PASS | All 10 new write endpoints gated by `execution_enabled`. Audit logging via existing `log_trade()`.                                                  |
| **III. Data-Driven Valuation**           | ✅ PASS | No impact.                                                                                                                                          |
| **IV. Risk-Managed Decision Making**     | ✅ PASS | `/order-check` endpoint adds pre-trade validation. Confirmation modals on all destructive UI actions.                                               |
| **V. Execution & Connection Frameworks** | ✅ PASS | All new endpoints use existing worker queue. 5 new trade action mappers (close, pending, modify, cancel, sltp).                                     |
| **VI. MT5 Connection Framework**         | ✅ PASS | Connection persistence unchanged. Symbol management extended with broker symbol discovery. Tick data endpoint added. Slippage protection inherited. |
| **Tech Stack**                           | ✅ PASS | No new dependencies beyond existing stack.                                                                                                          |
| **Dev Workflow**                         | ✅ PASS | Feature branch. Spec → Plan → Tasks flow followed.                                                                                                  |

**Post-Design Constitution Check**: ✅ PASS (no new violations)

---

## Complexity Tracking

No constitutional violations found. No deviations to justify.

---

## Progress Tracking

**Phase Status**:

- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command — describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:

- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none needed)

---

_Based on Constitution v1.1.0 — See `.specify/memory/constitution.md`_
