# Implementation Plan: MT5 Bridge Verification Dashboard

**Branch**: `001-mt5-bridge-dashboard` | **Date**: 2026-03-02 | **Spec**: [/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/001-mt5-bridge-dashboard/spec.md](/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/001-mt5-bridge-dashboard/spec.md)
**Input**: Feature specification from `/specs/001-mt5-bridge-dashboard/spec.md`

## Summary

Deliver an additive verification dashboard and planning/design artifacts for the MT5 bridge with zero contract-breaking changes to existing endpoints. The implementation introduces new operational endpoints (`/symbols`, `/logs`, `/config`, `/worker/state`, `/metrics`), execution safety gates (default-off execution enablement + multi-trade toggle risk controls), 90-day metrics retention, and a test strategy runnable on Linux/CI without native MT5.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, Uvicorn, MetaTrader5, Pydantic v2, pydantic-settings, NumPy, PyYAML  
**Storage**: File-based (`config/symbols.yaml`, `logs/trades.jsonl`, `logs/metrics.jsonl`)  
**Testing**: pytest, pytest-asyncio, pytest-mock, httpx/TestClient  
**Target Platform**: Windows host service for MT5 bridge; Linux Docker callers via HTTP  
**Project Type**: Web service (FastAPI microservice + static dashboard)  
**Performance Goals**: 99% dashboard interactions <=3s; log pagination median <=2s for 1,000 entries  
**Constraints**: Preserve `/health` `/prices` `/execute` contracts; preserve existing MT5 tick/bar streaming capability; enforce execution slippage protection and fill-confirmed state updates; execution disabled by default; fixed 90-day metrics retention; no inactivity timeout while tab remains open; enforce overload protection via `multi_trade_overload_queue_threshold` (default: 100 pending submissions) surfaced as a non-secret runtime policy; additive-only design  
**Scale/Scope**: Single bridge instance dashboard; additive endpoints + dashboard + test expansion; no changes to main app frontend or backtester core

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Multi-Agent Orchestration**: PASS. Feature is a bridge adapter/dashboard enhancement and does not alter orchestrator decision logic.
- **II. Trading Modes & Execution Safety**: PASS. Execution remains explicit-gated (`execution_enabled`), with multi-step confirmations, slippage protection, definitive fill-state handling, and explicit multi-trade risk warning.
- **III. Data-Driven Valuation**: PASS/NOT IMPACTED. No valuation-agent logic changes.
- **IV. Risk-Managed Decision Making**: PASS. No risk-manager bypass introduced; controls are additive and defensive.
- **V. Execution & Connection Frameworks**: PASS. Adapter isolation preserved; failure handling remains retry/safe-halt oriented.
- **VI. MT5 Connection Framework**: PASS. MT5 access remains isolated in bridge worker patterns, preserving MT5-specific execution/data responsibilities, including non-regression of existing tick/bar streaming capability.

**Pre-Phase-0 Gate Result**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/001-mt5-bridge-dashboard/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
mt5-connection-bridge/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── auth.py
│   ├── audit.py
│   ├── mt5_worker.py
│   ├── models/
│   ├── mappers/
│   └── routes/
├── config/
│   └── symbols.yaml
├── dashboard/
│   ├── index.html
│   ├── css/
│   └── js/
├── logs/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   └── performance/
├── specs/
└── .specify/
```

**Structure Decision**: Single Python web-service project rooted at `mt5-connection-bridge/` with feature artifacts isolated under `specs/001-mt5-bridge-dashboard/`.

## Phase 0 — Research Plan

1. Confirm API-key dashboard auth best practice for same-origin static FastAPI UI.
2. Confirm real-money execution gating model (default disabled, explicit enablement).
3. Confirm concurrent submission behavior with user-controlled multi-trade mode and warning UX.
4. Confirm 90-day rolling retention strategy for metrics file storage.
5. Confirm MT5 Linux/CI test strategy via complete module mocking.
6. Confirm OpenAPI-first contract strategy for additive endpoint growth while keeping existing contracts stable.
7. Confirm measurable validation approach for SC-001, SC-003, SC-005, SC-007, and streaming non-regression.
8. Confirm slippage-protection and fill-confirmed state update validation patterns aligned with MT5 adapter expectations, including pre-dispatch rejection and post-fill exception classification semantics.
9. Confirm overload-threshold policy definition (`multi_trade_overload_queue_threshold`), default value, and runtime config visibility contract.

## Phase 1 — Design Plan

1. Create `data-model.md` with entity fields, relationships, validations, and state transitions.
2. Create `contracts/openapi.yaml` as single source of truth for current + additive endpoint contracts.
3. Create `quickstart.md` with setup, smoke tests, dashboard validation flow, and test commands.
4. Update Codex agent context via `../.specify/scripts/bash/update-agent-context.sh codex`.
5. Add explicit validation coverage for session-policy behavior (FR-022), performance outcomes (SC-001/003/005), metrics retention review continuity (SC-007), and MT5 streaming non-regression (SC-008).
6. Add explicit test and contract validation coverage for pre-dispatch slippage rejection, post-fill slippage exception classification, and fill-confirmed state transitions (FR-024, FR-025, SC-009).
7. Add explicit config-model and UI-surface coverage for `multi_trade_overload_queue_threshold` policy visibility.
8. Add a consolidated execution-safety acceptance report artifact proving SC-009 pass/fail criteria.
9. Re-run constitution check against finalized design artifacts.

## Post-Design Constitution Re-check

- **I. Multi-Agent Orchestration**: PASS
- **II. Trading Modes & Execution Safety**: PASS (including slippage protection and fill-confirmed state transitions)
- **III. Data-Driven Valuation**: PASS/NOT IMPACTED
- **IV. Risk-Managed Decision Making**: PASS
- **V. Execution & Connection Frameworks**: PASS
- **VI. MT5 Connection Framework**: PASS (including streaming non-regression validation and MT5 execution confirmation handling)

**Post-Phase-1 Gate Result**: PASS

## Complexity Tracking

No constitution violations or exceptions required.
