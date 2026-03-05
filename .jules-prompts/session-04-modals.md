## Context — Phase 6: Dashboard Operator Experience

You are implementing **Phase 6 — Dashboard Operator Experience** for the **MT5 Connection Bridge** project.
Branch: `015-phase6-dashboard-operator-experience`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/015-phase6-dashboard-operator-experience/tasks.md` — your task list (execute ONLY the tasks listed below)
- `specs/015-phase6-dashboard-operator-experience/contracts/dashboard-components.md` — ConfirmationModal contract
- `dashboard/js/confirmation-modal.js` — already implemented, you will import from this
- `dashboard/js/execute-v2.js` — READ THIS FIRST (you will modify it)
- `dashboard/js/app.js` — READ THIS FIRST (you will modify it)
- `dashboard/js/positions.js` — READ THIS FIRST (you will modify it)
- `dashboard/js/orders.js` — READ THIS FIRST (you will modify it)

### Your Tasks — Phase 4: US2 Confirmation Modals (T016–T024)

Execute ONLY these tasks from `specs/015-phase6-dashboard-operator-experience/tasks.md`:

- T016 [US2]: Add `import { showConfirmationModal } from "./confirmation-modal.js";` to `dashboard/js/execute-v2.js`.

- T017 [US2]: In `execute-v2.js`, replace the `confirm()` call (~line 563) with `await showConfirmationModal(...)`. Read T017 in tasks.md for the exact config with title, message, details array, riskSummary, confirmLabel, and variant.

- T018 [US2]: Add `import { showConfirmationModal } from "./confirmation-modal.js";` to `dashboard/js/app.js`.

- T019 [US2]: In `app.js`, replace the `confirm()` call (~line 145, execution toggle) with `await showConfirmationModal(...)`. Read T019 in tasks.md for the dynamic config based on `targetEnabled`.

- T020 [US2]: Add `import { showConfirmationModal } from "./confirmation-modal.js";` to `dashboard/js/positions.js`.

- T021 [US2]: In `positions.js`, replace the `confirm()` call (~line 196) with `await showConfirmationModal(...)`. Read T021 in tasks.md for the config with position details and `requireCheckbox: true`.

- T022 [US2]: Add `import { showConfirmationModal } from "./confirmation-modal.js";` to `dashboard/js/orders.js`.

- T023 [US2]: In `orders.js`, replace the `confirm()` call (~line 114, cancel individual order) with `await showConfirmationModal(...)`. Read T023 in tasks.md for the config with order details.

- T024 [US2]: In `positions.js` and `orders.js`, REMOVE the local `showDangerCheckboxModal` function definitions. Update the "Cancel All" flow in `orders.js` (~line 139) to use `showConfirmationModal` with `requireCheckbox: true`. Read T024 in tasks.md for the exact config.

### Rules

1. **Read first**: Read ALL four files COMPLETELY before making ANY changes.
2. **Follow exactly**: Each task specifies the exact `confirm()` call to replace and its replacement config.
3. **Scope control**: ONLY modify `execute-v2.js`, `app.js`, `positions.js`, `orders.js`. Do NOT touch other files.
4. **Mark progress**: After completing each task, mark it as `[x]` in `specs/015-phase6-dashboard-operator-experience/tasks.md`.
5. **Commit convention**: Commit with message: `feat(015): T016–T024 standardized confirmation modals`
6. **No speckit commands**: Speckit CLI is not available. Apply all changes manually.
7. **Preserve existing functionality**: All existing features MUST continue working. You are REPLACING `confirm()` calls with `showConfirmationModal()` — same behavior, better UX.
8. **Async conversion**: Where a `confirm()` call is replaced, the enclosing function must become `async` if it isn't already. The `const approved/confirmed = confirm(...)` becomes `const approved/confirmed = await showConfirmationModal(...)`.
