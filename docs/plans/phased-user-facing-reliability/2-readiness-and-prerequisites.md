# Phase 2: Readiness and Prerequisites

> Objective: Prevent avoidable failures by providing a unified readiness contract and preflight gating before trade-affecting actions.

---

## 1. Problem This Phase Solves

Prerequisite checks are currently distributed across multiple endpoints and UI flows.  
Operators can still initiate actions that are guaranteed to fail at runtime.

---

## 2. Unified Readiness Contract

### 2.1 New aggregate endpoint

`GET /readiness` with optional action/symbol context:

- query inputs:
  - `operation` (`execute|pending_order|close_position|modify_order|cancel_order|modify_sltp`)
  - `symbol` (MT5 symbol or alias)
  - `direction` (`buy|sell`)
  - `volume`

### 2.2 Response structure

- `overall_status`: `ready|degraded|blocked`
- `checks[]` entries:
  - `check_id`
  - `status`: `pass|warn|fail|unknown`
  - `blocking`: boolean
  - `user_message`
  - `action`
  - `details`
- summary arrays:
  - `blockers[]`
  - `warnings[]`
  - `advice[]`
- timestamp and freshness metadata.

---

## 3. Required Checks

### 3.1 Global checks

1. Worker connected/authorized.
2. Terminal connected.
3. Account trade allowed.
4. Terminal trade allowed.
5. Execution policy enabled.
6. Queue overload/single-flight status.

### 3.2 Symbol/action checks

1. Symbol existence and visibility/selectability.
2. Trade mode compatibility with action direction.
3. Filling mode support for operation.
4. Volume constraints (min/max/step).
5. Tick freshness for market orders.
6. Stops/freeze level compatibility for SL/TP modifications when applicable.

---

## 4. Decision Matrix: Preflight Source of Truth

| Option | Description | Pros | Cons | Recommendation |
|---|---|---|---|---|
| A | Dashboard computes everything from multiple endpoints | No new API | Drift risk, duplicated logic | No |
| B | Backend readiness contract only | Consistent and testable | Requires endpoint build | **Recommended** |
| C | Hybrid with dashboard overrides | Flexible | Hard to govern | No |

---

## 5. Dashboard Behavior Requirements

1. Before submit/close/modify/cancel, request readiness for specific operation context.
2. If blocked:
   - disable destructive action buttons
   - show blocker list and next steps.
3. If degraded:
   - allow action with explicit warning acknowledgment.
4. Show readiness staleness timer and refresh affordance.

---

## 6. Testing Strategy

1. Unit tests for readiness check evaluators.
2. Integration tests for blocked/degraded/ready states per operation.
3. UI tests for gating behavior and blocker visibility.

---

## 7. Exit Criteria

1. Avoidable failures are blocked before action submit.
2. Readiness output matches actual route-level execution checks.
3. Operators can diagnose “why blocked” without reading raw logs.

