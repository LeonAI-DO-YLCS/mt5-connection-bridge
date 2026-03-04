## Context — Phase 6: Dashboard Operator Experience

You are implementing **Phase 6 — Dashboard Operator Experience** for the **MT5 Connection Bridge** project.
Branch: `015-phase6-dashboard-operator-experience`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/015-phase6-dashboard-operator-experience/tasks.md` — your task list (execute ONLY the tasks listed below)
- `dashboard/js/app.js` — READ THIS (you will modify it — add banner update logic)
- `dashboard/css/dashboard.css` — READ THIS (you may add CSS comments)

### Your Tasks — Phase 6: US4 Sticky Connection Banner (T032–T035)

Execute ONLY these tasks from `specs/015-phase6-dashboard-operator-experience/tasks.md`:

- T032 [US4]: In `app.js`, add a new function `updateStickyBanner(healthOk, readinessData)` that gets `#stickyBanner`, removes `hidden`, sets state class (`connected`/`degraded`/`disconnected`) and text content with icon + explanation. Read T032 in tasks.md for the exact logic for each state.

- T033 [US4]: In `app.js`, inside the status tab's `doLoad()` function (~line 167), add `api("/readiness").catch(() => null)` to the existing Promise.all array. After resolving, call `updateStickyBanner(!!health, readinessResp)`.

- T034 [US4]: In `app.js`, inside the status tab's catch block (terminal-disconnected fallback, ~line 186), call `updateStickyBanner(false, null)` to show disconnected banner.

- T035 [US4]: In `dashboard/css/dashboard.css`, add a CSS comment above sticky-banner styles: `/* FR-023: Banner uses text labels + color, not color alone. */`.

### Rules

1. **Read first**: Read `app.js` COMPLETELY before making ANY changes.
2. **Scope control**: ONLY modify `app.js` and `dashboard.css`. Do NOT touch other files.
3. **Mark progress**: Mark tasks as `[x]` in tasks.md.
4. **Commit**: `feat(015): T032–T035 sticky connection/readiness banner`
5. **No speckit commands**: Apply manually.
6. **Preserve existing**: The status tab's existing rendering (including `renderRuntimeSummary`) MUST continue working.
7. **Promise.all modification**: Add the new readiness fetch to the EXISTING Promise.all — do not create a separate fetch.
