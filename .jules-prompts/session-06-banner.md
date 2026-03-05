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
### Rules

1. **Read first**: Read every file you are about to modify BEFORE making changes.
2. **Follow exactly**: Each task specifies the exact file, function, and behavior. Follow precisely.
3. **ALLOWED FILES — you may ONLY modify these files**:
   - `dashboard/js/app.js`
   - `dashboard/css/dashboard.css`
4. **DO NOT MODIFY any other file**. Specifically:
   - ❌ DO NOT modify any `.jules-prompts/` files
   - ❌ DO NOT modify `tasks.md` or any spec files
   - ❌ DO NOT modify `dashboard/index.html` or any other JS file
   - ❌ DO NOT modify `.agent/` or any config files
   - ❌ DO NOT create any new files
5. **Commit convention**: Commit with message: `feat(015): T032–T035 sticky connection/readiness banner`
6. **No speckit commands**: Apply manually.
7. **Preserve existing code**: The status tab's existing rendering (including `renderRuntimeSummary`) MUST continue working.
8. **Promise.all modification**: Add the new readiness fetch to the EXISTING Promise.all — do not create a separate fetch.
9. **No stubs**: Every function must be fully implemented and working.
