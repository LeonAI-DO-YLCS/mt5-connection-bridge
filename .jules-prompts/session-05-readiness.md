## Context — Phase 6: Dashboard Operator Experience

You are implementing **Phase 6 — Dashboard Operator Experience** for the **MT5 Connection Bridge** project.
Branch: `015-phase6-dashboard-operator-experience`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/015-phase6-dashboard-operator-experience/tasks.md` — your task list (execute ONLY the tasks listed below)
- `dashboard/js/readiness.js` — READ THIS (already implemented readiness panel — you will import from it)
- `dashboard/js/positions.js` — READ THIS (you will modify it)
- `dashboard/js/orders.js` — READ THIS (you will modify it)
- `dashboard/js/message-renderer.js` — provides `showEnvelope` (already imported in both files)

### Your Tasks — Phase 5: US3 Readiness Panels (T025–T031)

Execute ONLY these tasks from `specs/015-phase6-dashboard-operator-experience/tasks.md`:

- T025 [US3]: Add import to `positions.js`: `import { renderReadinessPanel, isReadinessBlocked, isReadinessDegraded, isWarningAcknowledged } from "./readiness.js";`.

- T026 [US3]: In `positions.js`, inside `renderPositions`, after HTML is set, create and insert a `<div id="positions-readiness-panel"></div>` before the positions grid, then call `renderReadinessPanel(...)` with `{ operation: "close_position" }`.

- T027 [US3]: In `positions.js`, in each Close button click handler, after the confirmation modal resolves true, check `isReadinessBlocked()` — if blocked, show error via `showEnvelope` and return. If degraded and not acknowledged, show warning and return.

- T028 [US3]: Add import to `orders.js`: `import { renderReadinessPanel, isReadinessBlocked } from "./readiness.js";`.

- T029 [US3]: In `orders.js`, inside `renderOrders`, after HTML is set, create and insert a `<div id="orders-readiness-panel"></div>` before the orders grid, then call `renderReadinessPanel(...)` with `{ operation: "cancel_order" }`.

- T030 [US3]: In `orders.js`, in each Cancel button click handler, after the confirmation modal resolves true, check `isReadinessBlocked()` — if blocked, show error and return.

- T031 [US3]: In both `positions.js` and `orders.js`, add a listener for the `readiness-ack-change` custom event. When fired, update disabled state of Close/Cancel buttons based on `isReadinessBlocked()`.

### Rules

1. **Read first**: Read `positions.js`, `orders.js`, and `readiness.js` COMPLETELY before changes.
2. **Scope control**: ONLY modify `positions.js` and `orders.js`. Do NOT touch `readiness.js` or other files.
3. **Mark progress**: After completing each task, mark it as `[x]` in tasks.md.
4. **Commit**: `feat(015): T025–T031 inline readiness panels for positions and orders`
5. **No speckit commands**: Apply manually.
6. **Preserve existing**: All current position/order functionality MUST continue working.
