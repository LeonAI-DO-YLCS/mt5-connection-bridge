# Phase 0: Baseline and Constraints

> Objective: Establish a shared, code-grounded baseline and freeze non-negotiable constraints before behavioral changes.

---

## 1. Codebase Baseline (as of 2026-03-03)

### 1.1 Existing API and runtime building blocks

- FastAPI app-level exception handlers and `X-Error-Code` headers exist.
- Worker state machine and queue serialization exist in `app/mt5_worker.py`.
- Broker capability surfaces already exist (`/broker-capabilities`, `/broker-symbols`).
- Diagnostics surfaces exist (`/diagnostics/runtime`, `/diagnostics/symbols`).
- Dashboard has multi-tab operational UI and basic safety controls.

### 1.2 Existing endpoint families to preserve

1. Health/diagnostics:
   - `/health`, `/worker/state`, `/metrics`, `/diagnostics/runtime`, `/diagnostics/symbols`
2. Market and symbol data:
   - `/symbols`, `/broker-symbols`, `/broker-capabilities`, `/tick/{ticker}`, `/prices`
3. Trade operations:
   - `/execute`, `/pending-order`, `/close-position`, `/order-check`
   - `/orders` (list/modify/cancel), `/positions` (list/modify-sltp)
4. Account/terminal/history:
   - `/account`, `/terminal`, `/history/deals`, `/history/orders`

### 1.3 Existing model constraints to preserve

1. Request validation currently enforced by Pydantic models.
2. Trade models already enforce key fields like positive `quantity` and `current_price`.
3. Pending/close/modify models are intentionally compact; compatibility layers must adapt to them rather than forcing schema churn.

### 1.4 Existing operational scripts

Current scripts and workflow are in active use:

- `scripts/start_bridge.sh`
- `scripts/stop_bridge.sh`
- `scripts/restart_bridge.sh`
- `scripts/smoke_bridge.sh`
- `scripts/launch_bridge_dashboard.sh`
- `scripts/launch_bridge_windows.sh`
- `scripts/windows/launch_bridge_windows.ps1`

---

## 2. Requirements Captured from Operations

1. Failures must be understandable by non-developer operators.
2. Failures must be traceable by support without log archaeology.
3. Trade actions must fail fast on prerequisites, not deep in `order_send`.
4. Bridge behavior must remain deterministic under broker variability.
5. Launcher and scripts must remain as easy to use as today.

### 2.1 Requirements implied by current failures

Based on observed runtime incidents:

1. Comment-field compatibility handling is required for close and other comment-bearing paths.
2. Filling-mode and trade-mode guidance must remain explicit to avoid silent broker rejections.
3. Launcher/runtime diagnostics must make environment mismatch obvious before operators debug manually.
4. Error contracts must handle:
   - MT5 `last_error()` tuple patterns
   - broker `retcode` patterns
   - Pydantic validation error arrays.

---

## 3. Constraints and Invariants

### 3.1 Architecture invariants

1. MT5 worker queue model remains the execution backbone.
2. Existing endpoint contracts stay backward compatible during migration.
3. Pydantic business models are not redefined for convenience.

### 3.2 Operational invariants

1. Script entrypoints and invocation style do not change.
2. Existing launcher restart and artifact semantics remain.
3. Any launcher hardening is additive and opt-in where risky.

### 3.3 Security and operations invariants

1. API key auth behavior remains required for protected routes.
2. Structured logs remain first-class artifacts for postmortem and support.
3. Readiness and error details must avoid leaking sensitive credentials/paths.

### 3.4 Product invariants

1. Dashboard must remain usable for quick manual verification.
2. Error copy must never require JSON/MT5 internals to interpret.
3. Support must be able to map user screenshot to backend event quickly.

---

## 4. Deliverables

1. Reliability terminology glossary:
   - error, warning, status, advice, blocker, recovery.
2. Canonical incident identity policy:
   - `tracking_id` format.
3. Error-code namespace policy:
   - stable semantic codes.
4. Compatibility pledge document:
   - what remains stable per phase.
5. Launcher invariants checklist:
   - explicit “must not break” assertions.
6. MT5 parity gap register:
   - current coverage, target coverage, broker variance risks.

---

## 5. Exit Criteria

1. All teams agree on constraints and migration compatibility rules.
2. Phase 1 schema work can proceed without architectural ambiguity.
3. Launcher non-breaking policy is documented and approved.
4. Gap register exists for subsequent phase tracking.
