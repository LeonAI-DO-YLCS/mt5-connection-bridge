## Context — Phase 6: Dashboard Operator Experience

You are implementing **Phase 6 — Dashboard Operator Experience** for the **MT5 Connection Bridge** project.
Branch: `015-phase6-dashboard-operator-experience`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/015-phase6-dashboard-operator-experience/tasks.md` — your task list (execute ONLY the tasks listed below)
- `specs/015-phase6-dashboard-operator-experience/plan.md` — architecture, tech stack, project structure
- `specs/015-phase6-dashboard-operator-experience/data-model.md` — entity schemas and relationships
- `specs/015-phase6-dashboard-operator-experience/contracts/dashboard-components.md` — component API contracts

### Your Tasks — Phase 1: Setup (T001–T005)

Execute ONLY these tasks from `specs/015-phase6-dashboard-operator-experience/tasks.md`:

- T001: Create `dashboard/js/confirmation-modal.js` with a JSDoc header `/** MT5 Bridge — Shared Confirmation Modal (Phase 6). */` and a placeholder export `showConfirmationModal(config)` that returns `Promise.resolve(false)`.

- T002: Create `dashboard/js/operator-timeline.js` with JSDoc header `/** MT5 Bridge — Operator Timeline (Phase 6). */` and three placeholder exports: `pushTimelineEntry(entry)`, `renderTimeline(containerEl)`, `getTimelineEntries()` (returns `[]`).

- T003: Create `dashboard/js/support-package.js` with JSDoc header `/** MT5 Bridge — Support Package Clipboard Helper (Phase 6). */` and a placeholder export `copySupportPackage(data)` that logs to console.

- T004: In `dashboard/index.html`, add four new DOM containers inside `<div id="dashboardScreen">`, BEFORE `<div id="tabContent">`:
  1. `<div id="stickyBanner" class="sticky-banner hidden"></div>`
  2. `<div id="messageCenterContainer" class="message-center-container" aria-live="polite"></div>`
  3. `<div id="timelineDrawer" class="timeline-drawer hidden"></div>`
     Also add `<div id="modalRoot"></div>` as the LAST child of `<body>`.

- T005: In `dashboard/css/dashboard.css`, ADD (do NOT modify existing styles) all Phase 6 CSS class blocks at the END of the file. Read the full T005 description in tasks.md for the complete list of 22 CSS class blocks including `.confirmation-modal-overlay`, `.confirmation-modal`, `.sticky-banner`, `.message-center-container`, `.message-center-item`, severity variants, `.timeline-drawer`, `.timeline-entry`, and `.copy-btn`.

### Rules

1. **Read first**: Read every file you are about to modify BEFORE making changes.
2. **Follow exactly**: Each task specifies the exact file, function, and behavior. Follow precisely.
3. **Scope control**: Do NOT modify files not mentioned in your tasks.
4. **Mark progress**: After completing each task, mark it as `[x]` in `specs/015-phase6-dashboard-operator-experience/tasks.md`.
5. **Commit convention**: Commit with message: `feat(015): T001–T005 Phase 6 setup scaffolds`
6. **No speckit commands**: Speckit CLI is not available in this environment. Apply all changes manually.
7. **Preserve existing code**: Only ADD to files — do not remove unrelated functionality.
8. **No placeholders in CSS**: Every CSS class must have real property values as described in T005.
