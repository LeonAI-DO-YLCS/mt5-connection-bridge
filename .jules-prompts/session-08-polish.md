## Context — Phase 6: Dashboard Operator Experience

You are implementing **Phase 6 — Dashboard Operator Experience** for the **MT5 Connection Bridge** project.
Branch: `015-phase6-dashboard-operator-experience`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/015-phase6-dashboard-operator-experience/tasks.md` — your task list (execute ONLY the tasks listed below)
- `dashboard/js/execute-v2.js` — READ THIS (you will modify for inline validation)
- `dashboard/js/confirmation-modal.js` — READ THIS (you will enhance focus trap)
- `dashboard/js/message-renderer.js` — READ THIS (you will add ARIA attributes)
- `dashboard/css/dashboard.css` — READ THIS (you will add validation styles)
- `dashboard/index.html` — READ THIS (you will add ARIA roles)

### Your Tasks — Phases 9–11: US7 Validation + US8 Accessibility + Polish (T044–T056)

Execute ONLY these tasks from `specs/015-phase6-dashboard-operator-experience/tasks.md`:

**US7: Inline Validation Hints (T044–T047)**:

- T044 [US7]: In `execute-v2.js`, modify `runValidation()` to inject inline `<div class="inline-hint error">` elements next to each invalid field with plain-English messages.
- T045 [US7]: In `execute-v2.js`, add `clearInlineHints()` helper to remove all `.inline-hint` elements and `input-error` classes. Call at start of `runValidation()`.
- T046 [US7]: In `dashboard.css`, add styles: `.inline-hint`, `.inline-hint.error`, `.inline-hint.warning`, `.input-error`. Read T046 in tasks.md for exact CSS.
- T047 [US7]: In `execute-v2.js`, add debounced `input` event listeners on Volume and Price fields that trigger validation after 300ms.

**US8: Accessibility (T048–T051)**:

- T048 [US8]: In `confirmation-modal.js`, verify and enhance focus trap: find all focusable elements, cycle on Tab/Shift+Tab, restore focus on close. Read T048 in tasks.md.
- T049 [US8]: In `message-renderer.js`, add `role="status"` to success toasts and `role="alert"` to failure/critical toasts.
- T050 [US8]: In `message-renderer.js` and `confirmation-modal.js`, add `aria-label` attributes to all icon-only buttons (copy, dismiss, support package, refresh). Read T050 in tasks.md.
- T051 [US8]: In `index.html`, add `role="tablist"` to `#tabs`, `role="tab"` to each tab button, `role="tabpanel"` to `#tabContent`. Add `aria-label` to tab buttons.

**Polish (T052–T056)**:

- T052: Verify zero `confirm(` calls remain via code review (search all JS files, exclude false positives like `confirmLabel`).
- T053: Verify zero `alert(` calls remain in critical paths.
- T054: Review all tabs for JavaScript errors — check that imports resolve and functions are called correctly.
- T055: Review new CSS for dark-mode consistency with existing theme.
- T056: Remove any leftover `showDangerCheckboxModal` definitions from `positions.js` and `orders.js`. Remove any `console.log` debug statements.

### Rules

1. **Read first**: Read ALL files listed above BEFORE making changes.
2. **Scope control**: ONLY modify the files listed. Do NOT touch other files.
3. **Mark progress**: Mark tasks as `[x]` in tasks.md.
4. **Commit**: `feat(015): T044–T056 validation hints, accessibility, and polish`
5. **No speckit commands**: Apply manually.
6. **Preserve existing**: All current functionality MUST continue working.
7. **Accessibility standard**: Use WAI-ARIA dialog pattern for modals. Severity must use text labels AND color, not color alone.
8. **Final check**: After all tasks, do a final scan of all dashboard JS files for any remaining `confirm(` or `alert(` calls. Report findings as a comment in the commit.
