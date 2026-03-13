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

1. **Read first**: Read every file you are about to modify BEFORE making changes.
2. **Follow exactly**: Each task specifies the exact file, function, and behavior. Follow precisely.
3. **ALLOWED FILES — you may ONLY modify these files**:
   - `dashboard/js/positions.js`
   - `dashboard/js/orders.js`
4. **DO NOT MODIFY any other file**. Specifically:
   - ❌ DO NOT modify any `.jules-prompts/` files
   - ❌ DO NOT modify `tasks.md` or any spec files
   - ❌ DO NOT modify `dashboard/index.html`, `dashboard/css/dashboard.css`
   - ❌ DO NOT modify `readiness.js` — read it but do NOT modify it
   - ❌ DO NOT modify `.agent/` or any config files
   - ❌ DO NOT create any new files
5. **Commit convention**: Commit with message: `feat(015): T025–T031 inline readiness panels for positions and orders`
6. **No speckit commands**: Apply manually.
7. **Preserve existing code**: All current position/order functionality MUST continue working.
8. **No stubs**: Every function must be fully implemented and working.
9. **Follow contracts**: The API signatures in `contracts/dashboard-components.md` are the authoritative specification.
