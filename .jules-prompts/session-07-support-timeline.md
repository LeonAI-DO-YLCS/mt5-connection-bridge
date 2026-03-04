## Context — Phase 6: Dashboard Operator Experience

You are implementing **Phase 6 — Dashboard Operator Experience** for the **MT5 Connection Bridge** project.
Branch: `015-phase6-dashboard-operator-experience`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/015-phase6-dashboard-operator-experience/tasks.md` — your task list (execute ONLY the tasks listed below)
- `specs/015-phase6-dashboard-operator-experience/data-model.md` — SupportPackage and TimelineEntry schemas
- `dashboard/js/message-renderer.js` — you will modify (US5 support package button handler)
- `dashboard/js/readiness.js` — you will modify (expose readiness status to window)
- `dashboard/js/support-package.js` — already implemented (you will call it from message-renderer)
- `dashboard/js/operator-timeline.js` — already implemented (you will import and call it)
- `dashboard/js/app.js` — you will modify (timeline toggle button)
- `dashboard/js/execute-v2.js` — you will modify (push timeline entries)
- `dashboard/js/positions.js` — you will modify (push timeline entries)
- `dashboard/js/orders.js` — you will modify (push timeline entries)
- `dashboard/index.html` — you will modify (add timeline toggle button)

### Your Tasks — Phase 7+8: US5 Support Package + US6 Timeline (T036–T043)

Execute ONLY these tasks from `specs/015-phase6-dashboard-operator-experience/tasks.md`:

**US5: Support Package (T036–T038)**:

- T036 [US5]: In `message-renderer.js`, update the "Copy Support Package" button handler to construct a full `SupportPackageData` object and call `copySupportPackage(data)`. Read T036 in tasks.md for exact field mapping.
- T037 [US5]: In `readiness.js`, at the end of `renderReadinessPanel`, write `window.__lastReadinessStatus = _lastReadiness?.overall_status || null;`.
- T038 [US5]: In `support-package.js`, enhance the clipboard fallback modal: auto-select text on mount, add a Close button.

**US6: Timeline (T039–T043)**:

- T039 [US6]: Add import to `app.js`: `import { renderTimeline, pushTimelineEntry } from "./operator-timeline.js";`.
- T040 [US6]: Add a "📋 Timeline" toggle button to `dashboard/index.html` in the `#tabs` element. In `app.js`, bind click to toggle `#timelineDrawer` visibility and call `renderTimeline()`.
- T041 [US6]: In `execute-v2.js`, add `import { pushTimelineEntry } from "./operator-timeline.js";`. After trade success, call `pushTimelineEntry(...)` with action "execute", outcome "success". After failure, call with outcome "failure". Read T041 in tasks.md for exact entry fields.
- T042 [US6]: In `positions.js`, add `import { pushTimelineEntry } from "./operator-timeline.js";`. After close success/failure, call `pushTimelineEntry(...)` with action "close_position". Read T042 in tasks.md.
- T043 [US6]: In `orders.js`, add `import { pushTimelineEntry } from "./operator-timeline.js";`. After cancel success/failure, call `pushTimelineEntry(...)` with action "cancel_order". Read T043 in tasks.md.

### Rules

1. **Read first**: Read ALL files listed above BEFORE making changes.
2. **Scope control**: ONLY modify the files listed. Do NOT touch other files.
3. **Mark progress**: Mark tasks as `[x]` in tasks.md.
4. **Commit**: `feat(015): T036–T043 support package and operator timeline`
5. **No speckit commands**: Apply manually.
6. **Preserve existing**: All current functionality MUST continue working.
7. **Import placement**: All new imports go at the TOP of the file, alongside existing imports.
