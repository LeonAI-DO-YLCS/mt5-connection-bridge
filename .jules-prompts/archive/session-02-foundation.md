## Context — Phase 6: Dashboard Operator Experience

You are implementing **Phase 6 — Dashboard Operator Experience** for the **MT5 Connection Bridge** project.
Branch: `015-phase6-dashboard-operator-experience`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/015-phase6-dashboard-operator-experience/tasks.md` — your task list (execute ONLY the tasks listed below)
- `specs/015-phase6-dashboard-operator-experience/plan.md` — architecture, tech stack, project structure
- `specs/015-phase6-dashboard-operator-experience/data-model.md` — entity schemas (ConfirmationModalConfig, TimelineEntry, SupportPackage)
- `specs/015-phase6-dashboard-operator-experience/contracts/dashboard-components.md` — component API contracts (CRITICAL — follow these exactly)

### Your Tasks — Phase 2: Foundation (T006–T008)

Execute ONLY these tasks from `specs/015-phase6-dashboard-operator-experience/tasks.md`:

- T006: Implement the FULL `showConfirmationModal(config)` function in `dashboard/js/confirmation-modal.js`. This is a complete replacement of the placeholder from T001. Read the FULL T006 description in tasks.md — it has 17 detailed sub-steps covering the config schema, DOM rendering, focus trapping, keyboard handling (Escape/Enter/Tab), checkbox gating, `role="dialog"`, `aria-modal="true"`, and `aria-labelledby`/`aria-describedby`. Also read the ConfirmationModal contract in `contracts/dashboard-components.md`.

- T007: Implement the FULL `copySupportPackage(data)` function in `dashboard/js/support-package.js`. This replaces the placeholder from T003. Read T007 in tasks.md for the exact plain-text format, clipboard API usage with `navigator.clipboard.writeText()`, and the textarea fallback modal for when clipboard is unavailable.

- T008: Implement the FULL operator timeline module in `dashboard/js/operator-timeline.js`. This replaces the placeholders from T002. Read T008 in tasks.md for: internal `_entries` array (max 50, FIFO), `sessionStorage` persistence, `pushTimelineEntry()`, `getTimelineEntries()`, `renderTimeline()` with entry rendering, and "Clear Timeline" button.

### Rules

1. **Read first**: Read every file you are about to modify BEFORE making changes.
2. **Follow exactly**: Each task specifies the exact file, function, and behavior. Follow precisely.
3. **ALLOWED FILES — you may ONLY modify these 3 files**:
   - `dashboard/js/confirmation-modal.js`
   - `dashboard/js/support-package.js`
   - `dashboard/js/operator-timeline.js`
4. **DO NOT MODIFY any other file**. Specifically:
   - ❌ DO NOT modify any `.jules-prompts/` files
   - ❌ DO NOT modify `tasks.md` or any spec files
   - ❌ DO NOT modify `dashboard/index.html`, `dashboard/css/dashboard.css`, or any other JS file
   - ❌ DO NOT modify `.agent/` or any config files
   - ❌ DO NOT create any new files
5. **Commit convention**: Commit with message: `feat(015): T006–T008 Phase 6 foundational modules`
6. **No speckit commands**: Speckit CLI is not available in this environment. Apply all changes manually.
7. **Preserve existing code**: Only ADD or REPLACE within the same file — do not remove unrelated functionality.
8. **No stubs**: Every function must be fully implemented and working, not a TODO or placeholder.
9. **Follow contracts**: The API signatures in `contracts/dashboard-components.md` are the authoritative specification.
