## Context — Phase 6: Dashboard Operator Experience

You are implementing **Phase 6 — Dashboard Operator Experience** for the **MT5 Connection Bridge** project.
Branch: `015-phase6-dashboard-operator-experience`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/015-phase6-dashboard-operator-experience/tasks.md` — your task list (execute ONLY the tasks listed below)
- `specs/015-phase6-dashboard-operator-experience/contracts/dashboard-components.md` — Message Center contract
- `specs/015-phase6-dashboard-operator-experience/data-model.md` — MessageCenterEntry schema
- `dashboard/js/message-renderer.js` — THE file you are modifying (READ THIS FIRST)
- `dashboard/js/support-package.js` — already implemented, you will import from this

### Your Tasks — Phase 3: US1 Message Center (T009–T015)

Execute ONLY these tasks from `specs/015-phase6-dashboard-operator-experience/tasks.md`:

- T009 [US1]: Add imports to `dashboard/js/message-renderer.js`: `import { copySupportPackage } from "./support-package.js";` and `import { pushTimelineEntry } from "./operator-timeline.js";`.

- T010 [US1]: Modify `getContainer()` in `dashboard/js/message-renderer.js` to use `document.getElementById("messageCenterContainer")` if it exists, with fallback to the current body-append behavior.

- T011 [US1]: Add a new `_severityLabel(severity)` function in `dashboard/js/message-renderer.js` returning HTML badge strings for critical/high/medium/low/success. Read T011 in tasks.md for exact HTML + colors.

- T012 [US1]: Modify `showEnvelope(source)` to include: severity label, severity CSS class, tracking_id with copy button, collapsible details section, and "Copy Support Package" button for critical/high severity. Read T012 in tasks.md for exact HTML.

- T013 [US1]: Modify `renderToast()` to bind click handlers for `.copy-btn[data-copy]` (clipboard copy) and `.copy-support-btn` (calls copySupportPackage). Read T013 in tasks.md.

- T014 [US1]: Change auto-close behavior: success/low severity auto-close at 8s (existing). Critical/high/medium do NOT auto-close — persist until operator dismisses.

- T015 [US1]: Export a new `showMessage(entry)` function that renders a MessageCenterEntry directly without needing to parse an envelope.

### Rules

1. **Read first**: Read `dashboard/js/message-renderer.js` COMPLETELY before making ANY changes.
2. **Follow exactly**: Each task specifies exact modifications. Follow precisely.
3. **Scope control**: ONLY modify `dashboard/js/message-renderer.js`. Do NOT touch any other file.
4. **Mark progress**: After completing each task, mark it as `[x]` in `specs/015-phase6-dashboard-operator-experience/tasks.md`.
5. **Commit convention**: Commit with message: `feat(015): T009–T015 centralized message center`
6. **No speckit commands**: Speckit CLI is not available. Apply all changes manually.
7. **Preserve existing functionality**: The existing `showEnvelope`, `showSuccess`, `showError` functions MUST continue to work. You are ENHANCING them, not replacing them.
8. **XSS safety**: Continue using the existing `_esc()` function for all user-supplied content.
