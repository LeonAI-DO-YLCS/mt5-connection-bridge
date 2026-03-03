# Implementation Plan: Bridge Launcher Inspector Logging

**Branch**: `007-bridge-launcher-inspector-logs` | **Date**: 2026-03-02 | **Spec**: [/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/007-bridge-launcher-inspector-logs/spec.md](/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/007-bridge-launcher-inspector-logs/spec.md)
**Input**: Feature specification from `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/007-bridge-launcher-inspector-logs/spec.md`

## Summary

Add an inspector-focused launcher workflow that starts the existing bridge + dashboard runtime in one command, streams live output, persists run-scoped logs for 90 days, enforces authenticated operations under network-access-enabled sessions, attempts exactly one restart on unexpected crash, and preserves all existing operational scripts.

## Technical Context

**Language/Version**: Python 3.11+, Bash (POSIX shell on WSL/Linux host)  
**Primary Dependencies**: FastAPI app (existing), uvicorn, MetaTrader5 runtime worker, existing bridge shell scripts (`start_bridge.sh`, `stop_bridge.sh`, `restart_bridge.sh`, `smoke_bridge.sh`)  
**Storage**: File-based logs in `logs/` (`metrics.jsonl`, `trades.jsonl`, and new run-scoped launcher bundles)  
**Testing**: pytest (unit/integration/contract/performance markers) + script-level smoke execution  
**Target Platform**: Windows host MT5 terminal + bridge runtime invoked from WSL/Linux shell  
**Project Type**: Web-service adapter with operational shell tooling  
**Performance Goals**: Startup availability within 60 seconds for >=95% valid launches; failure diagnostics emitted immediately to terminal and persisted per run  
**Constraints**: Preserve existing API route behavior and existing operational scripts; no React frontend changes; shared operator credential model; no throttling/lockout behavior; exactly one auto-restart attempt on crash; 90-day run-log retention  
**Scale/Scope**: Single bridge instance per operator session; run-scoped logs for every launch attempt

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Multi-Agent Orchestration | PASS | No agent orchestration behavior is modified; feature is bridge operations-only. |
| II. Trading Modes & Execution Safety | PASS | Authenticated operations remain required, audit signals retained, and execution policy gates remain in place. |
| III. Data-Driven Valuation | PASS | No valuation logic modified; feature only improves runtime operability and observability. |
| IV. Risk-Managed Decision Making | PASS | No bypass of risk manager semantics; execution safety path remains unchanged. |
| V. Execution & Connection Frameworks | PASS | Adapter boundary is preserved; failure handling is strengthened via explicit restart-once + safe halt behavior. |
| VI. MT5 Connection Framework | PASS | MT5 adapter and worker model stay intact; launcher orchestration is additive around existing runtime. |
| Tech Stack & Standards | PASS | Uses existing Python/FastAPI/MT5 stack and current scripting conventions. |
| Development Workflow | PASS | Spec -> Plan -> Tasks sequence maintained on numeric feature branch. |

**Gate Result (Pre-Phase-0)**: PASS

## Project Structure

### Documentation (this feature)

```text
/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/007-bridge-launcher-inspector-logs/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── launcher-runtime-contract.md
└── tasks.md                 # Created later by /speckit.tasks
```

### Source Code (repository root)

```text
/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/
├── scripts/
│   ├── launch_bridge_dashboard.sh      # NEW
│   ├── start_bridge.sh                 # Existing, unchanged behavior required
│   ├── stop_bridge.sh                  # Existing, unchanged behavior required
│   ├── restart_bridge.sh               # Existing, unchanged behavior required
│   └── smoke_bridge.sh                 # Existing, unchanged behavior required
├── docs/
│   └── operations/
│       └── runtime-runbook.md          # UPDATE
├── README.md                           # UPDATE
├── logs/
│   ├── metrics.jsonl                   # Existing
│   ├── trades.jsonl                    # Existing
│   └── launcher/<run-id>/              # NEW run-scoped bundle root
└── tests/
    ├── integration/
    │   └── test_launcher_runtime.py    # NEW
    └── contract/
        └── test_launcher_contract.py   # NEW
```

**Structure Decision**: Single bridge project with additive operational-script and documentation changes, plus focused integration/contract coverage for launcher behavior.

## Phase 0: Outline & Research

**Objective**: Resolve all implementation unknowns and codify best practices for reliability, observability, and compatibility.

Research tasks executed:
1. Research run-scoped logging patterns for foreground + persisted dual-stream output in shell launchers.
2. Research failure-handling policy for one-retry restart semantics aligned with inspector-first debugging.
3. Research access-control implications of network-enabled runtime sessions with shared operator credential model.
4. Research retention policy mechanics for run-scoped artifacts with 90-day availability target.
5. Research compatibility constraints to keep existing bridge lifecycle scripts behavior-stable.

**Output**: [/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/007-bridge-launcher-inspector-logs/research.md](/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/007-bridge-launcher-inspector-logs/research.md)

## Phase 1: Design & Contracts

**Prerequisite**: research.md complete and no unresolved NEEDS CLARIFICATION.

Design outputs:
1. Data model for launch session, run log bundle, restart attempt, and auth failure event.
2. External interface contract for launcher command behavior and run-log artifact structure.
3. Operator quickstart for end-to-end launch, auth validation, restart behavior, and retention checks.
4. Agent context update via Codex context sync script.

**Outputs**:
- [/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/007-bridge-launcher-inspector-logs/data-model.md](/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/007-bridge-launcher-inspector-logs/data-model.md)
- [/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/007-bridge-launcher-inspector-logs/contracts/launcher-runtime-contract.md](/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/007-bridge-launcher-inspector-logs/contracts/launcher-runtime-contract.md)
- [/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/007-bridge-launcher-inspector-logs/quickstart.md](/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge/specs/007-bridge-launcher-inspector-logs/quickstart.md)

## Phase 2: Task Planning Approach

This plan stops at Phase 2 strategy (no task file generation in this command).

Task decomposition strategy for `/speckit.tasks`:
1. Script implementation tasks for launcher lifecycle, dual-stream logging, restart-once, and exit semantics.
2. Documentation update tasks for README and runtime runbook inspector mode.
3. Log-retention handling task for 90-day window and cleanup eligibility logic.
4. Test tasks:
   - Integration tests for launch success/failure and restart-once behavior.
   - Contract tests for log-bundle structure and compatibility expectations.
5. Regression guard tasks to confirm `start_bridge.sh`, `stop_bridge.sh`, `restart_bridge.sh`, and `smoke_bridge.sh` remain behavior-compatible.

## Post-Design Constitution Check

| Principle | Status | Notes |
|---|---|---|
| I. Multi-Agent Orchestration | PASS | Still adapter-only scope. |
| II. Trading Modes & Execution Safety | PASS | Authenticated operation access and auditability explicitly preserved. |
| III. Data-Driven Valuation | PASS | No valuation agent impact. |
| IV. Risk-Managed Decision Making | PASS | Risk/execution guardrails unchanged. |
| V. Execution & Connection Frameworks | PASS | Retry-once + safe halt meets failure handling expectations without architectural drift. |
| VI. MT5 Connection Framework | PASS | MT5 worker and symbol/runtime architecture remain unchanged. |
| Tech Stack & Standards | PASS | No stack deviation introduced. |
| Development Workflow | PASS | Plan artifacts generated in proper feature branch and spec directory. |

**Gate Result (Post-Phase-1)**: PASS

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| None | N/A | N/A |

## Progress Tracking

- [x] Phase 0: Research complete
- [x] Phase 1: Design complete
- [x] Phase 2: Task planning approach documented
- [ ] Phase 3: Tasks generated (`/speckit.tasks`)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation complete

