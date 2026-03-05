# Tasks: Phase 6 — Dashboard Operator Experience

**Input**: Design documents from `/specs/015-phase6-dashboard-operator-experience/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/dashboard-components.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Tasks are written at junior-developer granularity — each task should be completable by following the instructions without additional context.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new file scaffolds and shared CSS foundation before any user story work begins.

- [x] T001 Create an empty JavaScript module file at `dashboard/js/confirmation-modal.js`. Add a file-level JSDoc comment: `/** MT5 Bridge — Shared Confirmation Modal (Phase 6). */`. Export a placeholder function `showConfirmationModal(config)` that returns `Promise.resolve(false)`.

- [x] T002 Create an empty JavaScript module file at `dashboard/js/operator-timeline.js`. Add a file-level JSDoc comment: `/** MT5 Bridge — Operator Timeline (Phase 6). */`. Export three placeholder functions: `pushTimelineEntry(entry)`, `renderTimeline(containerEl)`, `getTimelineEntries()` (returns `[]`).

- [x] T003 Create an empty JavaScript module file at `dashboard/js/support-package.js`. Add a file-level JSDoc comment: `/** MT5 Bridge — Support Package Clipboard Helper (Phase 6). */`. Export a placeholder function `copySupportPackage(data)` that logs to console.

- [x] T004 [P] In `dashboard/index.html`, add three new DOM containers for Phase 6 components. Place these **inside** `<div id="dashboardScreen">`, **before** the `<div id="tabContent">`:
  1. `<div id="stickyBanner" class="sticky-banner hidden"></div>` — for the sticky connection/readiness banner (FR-014/FR-015).
  2. `<div id="messageCenterContainer" class="message-center-container" aria-live="polite"></div>` — for the centralized message center (FR-001).
  3. `<div id="timelineDrawer" class="timeline-drawer hidden"></div>` — for the operator timeline panel (FR-019).
     Also add a `<div id="modalRoot"></div>` as the last child of `<body>`, **after** all other content — this is the mount point for confirmation modals (FR-006).

- [x] T005 [P] In `dashboard/css/dashboard.css`, add the following CSS class blocks at the **end** of the file (do NOT modify existing styles). Each block should contain placeholder styles that will be refined per user story:
  1. `.confirmation-modal-overlay` — full-screen overlay with `position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: center; justify-content: center;`.
  2. `.confirmation-modal` — centered card with `background: var(--bg-card, #1e1e2e); border-radius: 12px; padding: 24px; max-width: 480px; width: 90%;`.
  3. `.confirmation-modal-details` — key-value grid: `display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; font-size: 0.9em;`.
  4. `.confirmation-modal-risk` — risk warning line: `padding: 8px 12px; border-left: 3px solid #fd7e14; margin: 12px 0; font-size: 0.85em;`.
  5. `.confirmation-modal-actions` — button row: `display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px;`.
  6. `.sticky-banner` — sticky header: `position: sticky; top: 0; z-index: 100; padding: 8px 16px; text-align: center; font-weight: 600;`.
  7. `.sticky-banner.connected` — green: `background: #198754; color: white;`.
  8. `.sticky-banner.degraded` — amber: `background: #fd7e14; color: white;`.
  9. `.sticky-banner.disconnected` — red: `background: #dc3545; color: white;`.
  10. `.message-center-container` — fixed bottom-right stack: `position: fixed; bottom: 16px; right: 16px; z-index: 900; display: flex; flex-direction: column-reverse; gap: 8px; max-width: 420px;`.
  11. `.message-center-item` — card base: `background: var(--bg-card, #1e1e2e); border-radius: 8px; padding: 16px; border-left: 4px solid #6c757d; box-shadow: 0 4px 12px rgba(0,0,0,0.3);`.
  12. `.message-center-item.severity-critical` — `border-left-color: #dc3545;`.
  13. `.message-center-item.severity-high` — `border-left-color: #fd7e14;`.
  14. `.message-center-item.severity-medium` — `border-left-color: #0dcaf0;`.
  15. `.message-center-item.severity-low` — `border-left-color: #6c757d;`.
  16. `.message-center-item.severity-success` — `border-left-color: #198754;`.
  17. `.message-severity-label` — inline badge: `font-size: 0.7em; font-weight: 700; text-transform: uppercase; padding: 2px 6px; border-radius: 4px; margin-right: 8px;`.
  18. `.timeline-drawer` — side drawer: `position: fixed; right: 0; top: 0; bottom: 0; width: 360px; background: var(--bg-card, #1e1e2e); z-index: 800; overflow-y: auto; padding: 16px; box-shadow: -4px 0 16px rgba(0,0,0,0.3); transition: transform 0.3s ease;`.
  19. `.timeline-entry` — single entry: `padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1); font-size: 0.85em;`.
  20. `.timeline-entry .outcome-success` — `color: #198754;`.
  21. `.timeline-entry .outcome-failure` — `color: #dc3545;`.
  22. `.copy-btn` — small copy button: `cursor: pointer; background: none; border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; padding: 2px 6px; font-size: 0.75em; color: inherit;`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core shared components that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Implement the full `showConfirmationModal(config)` function in `dashboard/js/confirmation-modal.js`. The function must:
  1. Accept a `config` object with fields: `title` (string, required), `message` (string, required), `details` (array of `{label, value}`, optional), `riskSummary` (string, optional), `confirmLabel` (string, required), `cancelLabel` (string, optional, default "Cancel"), `variant` ("danger"|"warning"|"default", optional), `requireCheckbox` (boolean, optional), `checkboxLabel` (string, optional).
  2. Return a `Promise<boolean>` that resolves `true` when confirmed, `false` when cancelled.
  3. Create a full-screen overlay `<div class="confirmation-modal-overlay">` and append it to `document.getElementById("modalRoot")`.
  4. Inside the overlay, render a `<div class="confirmation-modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" aria-describedby="modal-desc">`.
  5. Render `<h4 id="modal-title">${title}</h4>`.
  6. Render `<p id="modal-desc">${message}</p>`.
  7. If `details` is provided and non-empty, render a `<div class="confirmation-modal-details">` containing one `<span class="detail-label">${label}:</span> <span class="detail-value">${value}</span>` per entry.
  8. If `riskSummary` is provided, render a `<div class="confirmation-modal-risk">⚠️ ${riskSummary}</div>`.
  9. If `requireCheckbox` is true, render a `<label class="confirm-checkbox"><input type="checkbox" id="modalConfirmCheckbox"> ${checkboxLabel || "I understand this action is irreversible"}</label>`.
  10. Render a `<div class="confirmation-modal-actions">` with: `<button class="btn btn-secondary" id="modalCancelBtn">${cancelLabel}</button>` and `<button class="btn btn-${variant || 'primary'}" id="modalConfirmBtn">${confirmLabel}</button>`.
  11. If `requireCheckbox` is true, the Confirm button must start `disabled` and only enable when the checkbox is checked.
  12. Bind **Cancel button click** → resolve `false`, remove overlay.
  13. Bind **Confirm button click** → resolve `true`, remove overlay.
  14. Bind **Escape key** (document keydown) → resolve `false`, remove overlay.
  15. Bind **Enter key** when Confirm button is focused → resolve `true`, remove overlay.
  16. On mount, move focus to the Cancel button (safe default).
  17. Implement basic focus trapping: Tab should cycle between the interactive elements within the modal only.

- [ ] T007 Implement the `copySupportPackage(data)` function in `dashboard/js/support-package.js`. The function must:
  1. Accept a `data` object with fields: `tracking_id`, `operation`, `symbol`, `direction`, `volume`, `readiness_status`, `error_code`, `error_message`, `timestamp`.
  2. Build a plain-text string in this exact format:
     ```
     --- MT5 Bridge Support Package ---
     Tracking ID   : {tracking_id}
     Operation     : {operation}
     Symbol        : {symbol || "N/A"}
     Direction     : {direction || "N/A"}
     Volume        : {volume || "N/A"}
     Readiness     : {readiness_status || "N/A"}
     Error Code    : {error_code || "N/A"}
     Error Message : {error_message || "N/A"}
     Timestamp     : {timestamp}
     ----------------------------------
     ```
  3. Try `navigator.clipboard.writeText(text)`. If successful, return `{ success: true }`.
  4. If clipboard API fails (catch the error), create a fallback: render a modal overlay with a `<textarea readonly>` containing the text, pre-selected, with a "Close" button. Return `{ success: false, fallback: true }`.

- [ ] T008 Implement the operator timeline module in `dashboard/js/operator-timeline.js`. The module must:
  1. Maintain an internal array `_entries` (max 50, FIFO eviction).
  2. On module load, try to restore `_entries` from `sessionStorage.getItem("mt5_timeline")` (JSON parse, default to `[]` on error).
  3. `pushTimelineEntry(entry)`: Accept `{ action, outcome, code, tracking_id, symbol, timestamp }`. Push to the front of `_entries`. If length > 50, pop from the end. Save to `sessionStorage.setItem("mt5_timeline", JSON.stringify(_entries))`.
  4. `getTimelineEntries()`: Return a shallow copy of `_entries`.
  5. `renderTimeline(containerEl)`: Render the timeline inside the given element. For each entry, render a `<div class="timeline-entry">` containing:
     - An icon: `✅` for success, `❌` for failure.
     - `<span class="outcome-${entry.outcome}">${entry.action}</span>`.
     - `<span class="mono text-muted">${entry.code || "—"}</span>`.
     - `<span class="mono small">${entry.tracking_id ? entry.tracking_id.slice(0, 12) + "…" : "—"}</span>`.
     - `<span class="text-muted small">${new Date(entry.timestamp).toLocaleTimeString()}</span>`.
  6. If `_entries` is empty, render `<p class="text-muted">No operations yet in this session.</p>`.
  7. Add a "Clear Timeline" button at the bottom that empties `_entries`, clears `sessionStorage`, and re-renders.

**Checkpoint**: Foundation ready — all three shared modules are functional. User story implementation can now begin.

---

## Phase 3: User Story 1 — Centralized Message Center (Priority: P1) 🎯 MVP

**Goal**: Replace `alert()` calls and enhance the existing `message-renderer.js` to render Phase 1 canonical envelopes as styled, interactive messages with `tracking_id` copy, collapsible details, and severity text labels.

**Independent Test**: Trigger any API error from the Execute tab. Verify the error appears in the bottom-right message center with: severity label (text, not just color), title, message, action, tracking_id with copy button, and a collapsible Details section.

### Implementation for User Story 1

- [ ] T009 [US1] In `dashboard/js/message-renderer.js`, add the import for `copySupportPackage` at the top of the file: `import { copySupportPackage } from "./support-package.js";`. Also add `import { pushTimelineEntry } from "./operator-timeline.js";` for later integration.

- [ ] T010 [US1] In `dashboard/js/message-renderer.js`, modify the `getContainer()` function. Currently it creates a container and appends it to `document.body`. Change it to instead look for `document.getElementById("messageCenterContainer")`. If found, use that element as the container. If not found (fallback), create one and append to body as before.

- [ ] T011 [US1] In `dashboard/js/message-renderer.js`, add a new helper function `_severityLabel(severity)` that returns an HTML string for a colored severity badge:
  - `critical` → `<span class="message-severity-label" style="background:#dc3545;color:#fff;">⛔ CRITICAL</span>`
  - `high` → `<span class="message-severity-label" style="background:#fd7e14;color:#fff;">⚠️ HIGH</span>`
  - `medium` → `<span class="message-severity-label" style="background:#0dcaf0;color:#000;">ℹ️ MEDIUM</span>`
  - `low` → `<span class="message-severity-label" style="background:#6c757d;color:#fff;">💡 LOW</span>`
  - Default/success → `<span class="message-severity-label" style="background:#198754;color:#fff;">✅ OK</span>`

- [ ] T012 [US1] In `dashboard/js/message-renderer.js`, modify the `showEnvelope(source)` function. After parsing the envelope (via `_parseEnvelope`), change the rendered HTML to include:
  1. The severity label from `_severityLabel(env.severity)` at the top of the toast.
  2. The CSS class `severity-${env.severity || "medium"}` added to the toast element's classList.
  3. The `tracking_id` (if present) displayed as: `<div class="mono small">ID: <code>${env.tracking_id}</code> <button class="copy-btn" data-copy="${env.tracking_id}" title="Copy Tracking ID">📋</button></div>`.
  4. A collapsible details section if `env.context` exists: `<details class="mt-2"><summary class="small">Details</summary><pre class="small">${JSON.stringify(env.context, null, 2)}</pre></details>`.
  5. A "Copy Support Package" button for failure messages (`severity` is `critical` or `high`): `<button class="btn btn-sm copy-support-btn mt-2">📋 Copy Support Package</button>`.

- [ ] T013 [US1] In `dashboard/js/message-renderer.js`, modify the `renderToast()` function to bind click handlers **after** the toast is appended to the DOM:
  1. Find all `.copy-btn[data-copy]` elements inside the toast. On click, copy the `data-copy` attribute value to clipboard using `navigator.clipboard.writeText()`. Show a brief "Copied!" text change on the button.
  2. Find any `.copy-support-btn` elements inside the toast. On click, call `copySupportPackage()` with the envelope data extracted during rendering (store it as a data attribute or closure variable).

- [ ] T014 [US1] In `dashboard/js/message-renderer.js`, change the `autoCloseMs` behavior: success messages (`severity: undefined` or `low`) should auto-close after 8 seconds (existing behavior). Failure messages (`severity: critical`, `high`, or `medium`) should **NOT auto-close** — they persist until the operator clicks the dismiss button.

- [ ] T015 [US1] In `dashboard/js/message-renderer.js`, export a new function `showMessage(entry)` that accepts a `MessageCenterEntry` object (as defined in data-model.md) and renders it using the same rendering pipeline as `showEnvelope` but directly from the entry fields without needing to parse an envelope. This allows programmatic message injection.

**Checkpoint**: Message center now renders styled, interactive messages with severity labels, tracking ID copy, collapsible details, and support package button. Success messages auto-dismiss; failures persist.

---

## Phase 4: User Story 2 — Standardized Confirmation Modals (Priority: P1)

**Goal**: Replace all 4 remaining `confirm()` calls in critical operation paths with the shared `ConfirmationModal` component, showing contextual details and a risk summary.

**Independent Test**: Go to the Execute tab, fill in a trade, and click Submit. Verify a styled modal appears with symbol, volume, direction details and a risk warning — not a browser `confirm()` dialog. Press Escape to dismiss. Repeat for Close Position and Cancel Order.

### Implementation for User Story 2

- [ ] T016 [US2] In `dashboard/js/execute-v2.js`, add the import at the top: `import { showConfirmationModal } from "./confirmation-modal.js";`.

- [ ] T017 [US2] In `dashboard/js/execute-v2.js`, find the `confirm()` call on approximately line 563 (`if (!confirm(\`Submit ${actionLabel}...`)). Replace the entire `confirm()`block with an`async`call to`showConfirmationModal`. The config should be:
  - `title`: `"Confirm Trade Submission"`
  - `message`: `"You are about to submit a trade order. Please review the details below."`
  - `details`: array built from the form values: `[{ label: "Action", value: actionLabel }, { label: "Symbol", value: val }, { label: "Volume", value: volume }, { label: "Type", value: typeEl.value }]` — add SL/TP details if set.
  - `riskSummary`: `"This will submit a live market order. Ensure your risk parameters are correct."`
  - `confirmLabel`: `"Submit Order"`
  - `variant`: `"danger"`

- [ ] T018 [US2] In `dashboard/js/app.js`, add the import at the top: `import { showConfirmationModal } from "./confirmation-modal.js";`.

- [ ] T019 [US2] In `dashboard/js/app.js`, find the `confirm()` call on approximately line 145 (execution toggle confirmation). Replace it with an `async` call to `showConfirmationModal`. The config should be:
  - `title`: `targetEnabled ? "Enable Order Execution" : "Disable Order Execution"`
  - `message`: `targetEnabled ? "Enabling execution will allow the bridge to submit real trades to MT5." : "Disabling execution will block all trade submissions."`
  - `riskSummary`: `targetEnabled ? "Live trading will become active." : "No orders will be executed while disabled."`
  - `confirmLabel`: `targetEnabled ? "Enable Execution" : "Disable Execution"`
  - `variant`: `targetEnabled ? "danger" : "warning"`

- [ ] T020 [US2] In `dashboard/js/positions.js`, add the import at the top: `import { showConfirmationModal } from "./confirmation-modal.js";`.

- [ ] T021 [US2] In `dashboard/js/positions.js`, find the `confirm()` call on approximately line 196 (close position/partial close confirmation). Replace it with an `async` call to `showConfirmationModal`. The config should be:
  - `title`: `"Confirm Close Position"`
  - `message`: `"You are about to close a position. This action is irreversible."`
  - `details`: `[{ label: "Symbol", value: pos.symbol }, { label: "Ticket", value: pos.ticket }, { label: "Volume", value: closeVolume }, { label: "Direction", value: pos.type }]`
  - `riskSummary`: `"Closing this position will realize any unrealized P&L."`
  - `confirmLabel`: `"Close Position"`
  - `variant`: `"danger"`
  - `requireCheckbox`: `true`

- [ ] T022 [US2] In `dashboard/js/orders.js`, add the import at the top: `import { showConfirmationModal } from "./confirmation-modal.js";`.

- [ ] T023 [US2] In `dashboard/js/orders.js`, find the `confirm()` call on approximately line 114 (cancel individual order). Replace it with an `async` call to `showConfirmationModal`. The config should be:
  - `title`: `"Confirm Cancel Order"`
  - `message`: `"You are about to cancel a pending order. This action is irreversible."`
  - `details`: `[{ label: "Symbol", value: symbol }, { label: "Ticket", value: ticket }, { label: "Type", value: type.replace("_", " ").toUpperCase() }, { label: "Volume", value: volume }, { label: "Price", value: price }]`
  - `confirmLabel`: `"Cancel Order"`
  - `variant`: `"danger"`

- [ ] T024 [US2] In `dashboard/js/positions.js` and `dashboard/js/orders.js`, remove the local `showDangerCheckboxModal` function definitions (they are now replaced by the shared `showConfirmationModal`). Update the "Cancel All" flow in `orders.js` (approx. line 139) to use `showConfirmationModal` instead of `showDangerCheckboxModal`, with config: `title: "Cancel All Pending Orders"`, `message: "You are about to cancel ${orders.length} pending order(s)."`, `requireCheckbox: true`, `checkboxLabel: "I understand this action is irreversible."`, `confirmLabel: "Cancel All"`, `variant: "danger"`. Also update the corresponding code in `positions.js` for any "close all" flow if present.

**Checkpoint**: All `confirm()` and `showDangerCheckboxModal` calls are replaced. Every destructive action now triggers a styled, accessible modal.

---

## Phase 5: User Story 3 — Inline Readiness Panels (Priority: P1)

**Goal**: Add inline readiness panels to the Positions and Orders tabs (Execute tab already has one from Phase 2), gating submission when readiness is blocked.

**Independent Test**: Simulate a blocked readiness state. Navigate to the Positions tab and verify the Close button is disabled with blockers listed. Navigate to the Orders tab and verify the Cancel button is disabled with blockers listed.

### Implementation for User Story 3

- [ ] T025 [US3] In `dashboard/js/positions.js`, add the import at the top: `import { renderReadinessPanel, isReadinessBlocked, isReadinessDegraded, isWarningAcknowledged } from "./readiness.js";`.

- [ ] T026 [US3] In `dashboard/js/positions.js`, inside the `renderPositions` function, after the HTML is set to `contentEl.innerHTML`, add a readiness panel mount point. Create a `<div id="positions-readiness-panel"></div>` element, insert it before the positions grid. Then call `renderReadinessPanel(document.getElementById("positions-readiness-panel"), { operation: "close_position" })`.

- [ ] T027 [US3] In `dashboard/js/positions.js`, find each Close button click handler. Before executing the close action (after the confirmation modal resolves `true`), check `isReadinessBlocked()`. If blocked, show a message via `showEnvelope` with title "Cannot Close Position" and message "Readiness is currently blocked. Resolve blockers before closing positions." and return without executing. If `isReadinessDegraded()` and `!isWarningAcknowledged()`, show a warning message and return.

- [ ] T028 [US3] In `dashboard/js/orders.js`, add the import at the top: `import { renderReadinessPanel, isReadinessBlocked } from "./readiness.js";`.

- [ ] T029 [US3] In `dashboard/js/orders.js`, inside the `renderOrders` function, after the HTML is set to `contentEl.innerHTML`, add a readiness panel mount point. Create a `<div id="orders-readiness-panel"></div>` element, insert it before the orders grid. Then call `renderReadinessPanel(document.getElementById("orders-readiness-panel"), { operation: "cancel_order" })`.

- [ ] T030 [US3] In `dashboard/js/orders.js`, find each Cancel button click handler. Before executing the cancel action (after the confirmation modal resolves `true`), check `isReadinessBlocked()`. If blocked, show a message via `showEnvelope` with title "Cannot Cancel Order" and message "Readiness is currently blocked." and return without executing.

- [ ] T031 [US3] In `dashboard/js/positions.js` and `dashboard/js/orders.js`, add a listener for the `readiness-ack-change` custom event (already dispatched by `readiness.js`). When the event fires, update the disabled state of all Close/Cancel buttons based on `isReadinessBlocked()`.

**Checkpoint**: Readiness panels are active in Execute, Positions, and Orders tabs. Blocked states disable action buttons. Degraded states require acknowledgment.

---

## Phase 6: User Story 4 — Sticky Connection/Readiness Banner (Priority: P2)

**Goal**: Display a persistent banner across the top of the dashboard showing the current bridge connection and readiness state.

**Independent Test**: Start the dashboard with the bridge offline. Verify a red "Disconnected" banner appears at the top. Start the bridge and verify the banner turns green "Connected". Simulate a degraded readiness state and verify the banner turns amber.

### Implementation for User Story 4

- [ ] T032 [US4] In `dashboard/js/app.js`, add a new function `updateStickyBanner(healthOk, readinessData)` that:
  1. Gets the element `document.getElementById("stickyBanner")`.
  2. Removes the `hidden` class.
  3. Removes all state classes: `connected`, `degraded`, `disconnected`.
  4. If `healthOk` is false or null: add class `disconnected`, set text to `"⛔ DISCONNECTED — Bridge is not responding. Check if the bridge process is running."`.
  5. Else if `readinessData` and `readinessData.overall_status === "blocked"`: add class `disconnected`, set text to `"🚫 BLOCKED — ${readinessData.blockers?.[0]?.user_message || 'Critical blocker detected'}"`.
  6. Else if `readinessData` and `readinessData.overall_status === "degraded"`: add class `degraded`, set text to `"⚠️ DEGRADED — ${readinessData.warnings?.[0]?.user_message || 'Warnings detected'}"`.
  7. Else: add class `connected`, set text to `"✅ Connected — Bridge is ready"`.

- [ ] T033 [US4] In `dashboard/js/app.js`, inside the `doLoad()` function for the "status" tab (approx. line 167), after the `Promise.all` call that fetches health/worker/etc, also fetch readiness data: add `api("/readiness").catch(() => null)` to the Promise.all array. After resolving, call `updateStickyBanner(!!health, readinessResp)`.

- [ ] T034 [US4] In `dashboard/js/app.js`, inside the status tab's `catch` block (the terminal-disconnected fallback path, approx. line 186), call `updateStickyBanner(false, null)` to show the disconnected banner.

- [ ] T035 [US4] In `dashboard/css/dashboard.css`, add an `aria-label` reminder comment above the `.sticky-banner` class block: `/* FR-023: Banner uses text labels + color, not color alone. */`. Ensure each state class (`.connected`, `.degraded`, `.disconnected`) has distinct styling that is readable without color differentiation (the text already conveys the state).

**Checkpoint**: The dashboard now shows a persistent, color-coded + text-labeled banner reflecting bridge connection and readiness state.

---

## Phase 7: User Story 5 — Copy Support Package (Priority: P2)

**Goal**: Every failure message in the message center includes a "Copy Support Package" button that copies a structured incident context to clipboard.

**Independent Test**: Trigger a trade error (e.g., submit with execution disabled). In the message center, click "Copy Support Package". Paste into a text editor and verify the format includes tracking_id, operation, symbol, readiness status, and timestamp.

### Implementation for User Story 5

- [ ] T036 [US5] In `dashboard/js/message-renderer.js`, update the `showEnvelope` function's "Copy Support Package" button handler (added in T013). When the button is clicked, construct a `SupportPackageData` object using the envelope fields:
  - `tracking_id`: from envelope.
  - `operation`: infer from `category` or envelope context (e.g., "trade_execution", "close_position") or default to "unknown".
  - `symbol`: from `env.context?.symbol || env.context?.ticker || null`.
  - `direction`: from `env.context?.direction || null`.
  - `volume`: from `env.context?.volume || null`.
  - `readiness_status`: try to read from `window.__lastReadinessStatus || null` (will be set in T037).
  - `error_code`: from `env.code || null`.
  - `error_message`: from `env.title || env.message || null`.
  - `timestamp`: `new Date().toISOString()`.
    Call `copySupportPackage(data)`.

- [ ] T037 [US5] In `dashboard/js/readiness.js`, at the end of the `renderReadinessPanel` function (after `_lastReadiness` is set), write the current overall_status to `window.__lastReadinessStatus = _lastReadiness?.overall_status || null;`. This makes the readiness status available to the support package builder without tight coupling.

- [ ] T038 [US5] In `dashboard/js/support-package.js`, enhance the clipboard fallback modal: when the `<textarea>` modal is shown, automatically select all text on mount so the operator can press Ctrl+C immediately. Add a "Close" button with `class="btn btn-secondary"` that removes the modal overlay.

**Checkpoint**: Failure messages now have actionable "Copy Support Package" buttons with clipboard + fallback support.

---

## Phase 8: User Story 6 — Operator Timeline (Priority: P2)

**Goal**: Show a session-scoped reverse-chronological log of recent operations with outcome, code, and tracking ID.

**Independent Test**: Execute a trade (success), then trigger an error (failure). Open the timeline panel and verify both entries appear in reverse chronological order with correct icons and details.

### Implementation for User Story 6

- [ ] T039 [US6] In `dashboard/js/app.js`, add the import at the top: `import { renderTimeline, pushTimelineEntry } from "./operator-timeline.js";`.

- [ ] T040 [US6] In `dashboard/js/app.js`, add a "Timeline" toggle button to the tab bar. Inside the `#tabs` element in `dashboard/index.html`, add: `<button class="tab" id="timelineToggle">📋 Timeline</button>` after the logout button. In `app.js`, bind the click handler: toggle the `hidden` class on `document.getElementById("timelineDrawer")`, and call `renderTimeline(document.getElementById("timelineDrawer"))` each time it's shown.

- [ ] T041 [US6] In `dashboard/js/execute-v2.js`, add the import at the top: `import { pushTimelineEntry } from "./operator-timeline.js";`. After a trade is submitted successfully (the API call resolves), call `pushTimelineEntry({ action: "execute", outcome: "success", code: result?.code || null, tracking_id: result?.tracking_id || null, symbol: tickerEl.value, timestamp: new Date().toISOString() })`. After a trade fails (the catch block), call `pushTimelineEntry({ action: "execute", outcome: "failure", code: err?.envelope?.code || null, tracking_id: err?.envelope?.tracking_id || null, symbol: tickerEl.value, timestamp: new Date().toISOString() })`.

- [ ] T042 [US6] In `dashboard/js/positions.js`, add the import at the top: `import { pushTimelineEntry } from "./operator-timeline.js";`. After a position close succeeds, call `pushTimelineEntry({ action: "close_position", outcome: "success", code: null, tracking_id: null, symbol: pos.symbol, timestamp: new Date().toISOString() })`. After a close fails, call `pushTimelineEntry({ action: "close_position", outcome: "failure", code: err?.envelope?.code || null, tracking_id: err?.envelope?.tracking_id || null, symbol: pos.symbol, timestamp: new Date().toISOString() })`.

- [ ] T043 [US6] In `dashboard/js/orders.js`, add the import at the top: `import { pushTimelineEntry } from "./operator-timeline.js";`. After an order cancel succeeds, call `pushTimelineEntry({ action: "cancel_order", outcome: "success", code: null, tracking_id: null, symbol: order.symbol, timestamp: new Date().toISOString() })`. After a cancel fails, call `pushTimelineEntry({ action: "cancel_order", outcome: "failure", code: err?.envelope?.code || null, tracking_id: err?.envelope?.tracking_id || null, symbol: order.symbol, timestamp: new Date().toISOString() })`.

**Checkpoint**: Every operation (execute, close, cancel) is logged to the timeline. The timeline drawer shows entries in reverse chronological order.

---

## Phase 9: User Story 7 — Inline Validation Hints (Priority: P3)

**Goal**: Display inline validation hints on form inputs in the Execute tab before submission, using readiness data and plain-English text.

**Independent Test**: On the Execute tab, enter a volume of 0 or a negative number. Verify an inline validation message appears below the Volume field in plain English (e.g., "Volume must be greater than zero"). Enter a valid volume and verify the message disappears.

### Implementation for User Story 7

- [ ] T044 [US7] In `dashboard/js/execute-v2.js`, find the `runValidation()` function (approx. line 404). This function already performs validation but shows results in a summary area. Modify it to also inject inline hints next to each invalid field. For each validation error:
  1. Find the corresponding input element by ID.
  2. Create or update a `<div class="inline-hint error">` sibling element directly after the input.
  3. Set the text to plain English (e.g., for volume: "Volume must be between {min} and {max}" instead of raw field names).
  4. Add the CSS class `input-error` to the input element itself to highlight it.

- [ ] T045 [US7] In `dashboard/js/execute-v2.js`, add a `clearInlineHints()` helper function that removes all `.inline-hint` elements and `input-error` classes from the form. Call this at the start of `runValidation()` to clear previous hints.

- [ ] T046 [US7] In `dashboard/css/dashboard.css`, add styles for inline validation:
  1. `.inline-hint` — `font-size: 0.8em; margin-top: 4px;`.
  2. `.inline-hint.error` — `color: #dc3545;`.
  3. `.inline-hint.warning` — `color: #fd7e14;`.
  4. `.input-error` — `border-color: #dc3545 !important; box-shadow: 0 0 0 2px rgba(220,53,69,0.2);`.

- [ ] T047 [US7] In `dashboard/js/execute-v2.js`, bind an `input` event listener on the Volume and Price input fields. On each input event, call `triggerValidation()` (already exists, approx. line 399) with a 300ms debounce to provide real-time feedback as the operator types.

**Checkpoint**: Form inputs now display inline validation hints in plain English before submission.

---

## Phase 10: User Story 8 — Accessibility Compliance (Priority: P3)

**Goal**: Ensure all modals, message center, and interactive elements are keyboard-navigable and screen-reader friendly.

**Independent Test**: Using only the keyboard (no mouse), navigate to the Execute tab, fill in a trade, press Tab to Submit, press Enter to open the modal, Tab to Confirm, press Enter to confirm. Verify the entire flow works without mouse interaction.

### Implementation for User Story 8

- [ ] T048 [US8] In `dashboard/js/confirmation-modal.js`, verify and enhance the focus trap implementation from T006:
  1. On modal open, find all focusable elements inside the modal: `button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])`.
  2. On Tab press: if focus is on the last focusable element, move to the first. On Shift+Tab: if focus is on the first, move to the last.
  3. On Escape: dismiss the modal.
  4. Store the element that had focus before the modal opened. On modal close, restore focus to that element.

- [ ] T049 [US8] In `dashboard/js/message-renderer.js`, add `role="status"` to success toasts and `role="alert"` to failure/critical toasts. This ensures screen readers announce important messages.

- [ ] T050 [US8] In `dashboard/js/message-renderer.js` and `dashboard/js/confirmation-modal.js`, add `aria-label` attributes to all icon-only buttons:
  1. Copy button → `aria-label="Copy tracking ID to clipboard"`.
  2. Dismiss button → `aria-label="Dismiss message"`.
  3. Support Package button → `aria-label="Copy support package to clipboard"`.
  4. Refresh readiness button → `aria-label="Refresh readiness check"`.

- [ ] T051 [US8] In `dashboard/index.html`, add `aria-label` attributes to all existing tab buttons that don't already have them. Add `role="tablist"` to the `#tabs` container and `role="tab"` to each tab button. Add `role="tabpanel"` to `#tabContent`.

**Checkpoint**: All modals, message center, and interactive elements are fully keyboard-navigable and screen-reader accessible.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and validation

- [ ] T052 Run `grep -rn 'confirm(' dashboard/js/ | grep -v '//' | grep -v 'confirmLabel' | grep -v 'confirmBtn' | grep -v 'confirmed' | grep -v 'showConfirmationModal'` and verify zero results. If any `confirm()` calls remain, replace them.

- [ ] T053 Run `grep -rn 'alert(' dashboard/js/` and verify zero results in critical operation paths. Document any intentional `alert()` calls that remain outside critical paths.

- [ ] T054 Open every tab (Status, Positions, Orders, Execute, Symbols, Prices, History, Logs, Config, Metrics) in the dashboard and verify no JavaScript console errors. Verify the sticky banner is visible. Verify the Timeline toggle works.

- [ ] T055 [P] Review all new CSS in `dashboard/css/dashboard.css` for consistency with existing theme variables and color palette. Ensure dark mode compatibility (the dashboard uses a dark theme). Verify all new components render correctly at viewport widths of 1024px, 1440px, and 1920px.

- [ ] T056 Code cleanup: remove any leftover `showDangerCheckboxModal` function definitions from `dashboard/js/positions.js` and `dashboard/js/orders.js` if not already removed in T024. Remove any `console.log` debugging statements added during development.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational completion
  - US1 (Message Center) and US2 (Modals) can proceed in parallel
  - US3 (Readiness Panels) depends on US2 (modals are used in gating flows)
  - US4 (Sticky Banner) is independent of US1–US3
  - US5 (Support Package) depends on US1 (message center renders the button)
  - US6 (Timeline) is independent — can be done in parallel with US1–US5
  - US7 (Validation Hints) is independent
  - US8 (Accessibility) should be done last (polishes all other stories)
- **Polish (Phase 11)**: Depends on all user stories being complete

### User Story Dependencies

```text
Phase 2 (Foundation)
  ├── US1 (Message Center)  ──→ US5 (Support Package)
  ├── US2 (Modals)          ──→ US3 (Readiness Panels)
  ├── US4 (Sticky Banner)   [independent]
  ├── US6 (Timeline)        [independent]
  ├── US7 (Validation)      [independent]
  └── US8 (Accessibility)   [do last, polishes all]
```

### Within Each User Story

- Read the task description carefully — each task specifies the exact file and the exact change
- Complete tasks in order within each story (they build on each other)
- Commit after each completed task or logical group of tasks
- Test by opening the dashboard in a browser after each implementation task

### Parallel Opportunities

- T004 and T005 can run in parallel (different files: HTML vs CSS)
- US1 and US2 can run in parallel (message-renderer.js vs confirmation-modal.js integrations)
- US4, US6, and US7 are all independent and can run in parallel with each other
- T009 through T015 (US1) can be done by one developer while T016–T024 (US2) are done by another

---

## Parallel Example: User Stories 1 & 2

```bash
# Developer A focuses on Message Center (US1)
Task: "Add severity label helper to dashboard/js/message-renderer.js"
Task: "Update showEnvelope to render tracking_id copy and severity badges"
Task: "Add persistent failure messages and auto-dismiss success messages"

# Developer B focuses on Confirmation Modals (US2)
Task: "Replace confirm() in dashboard/js/execute-v2.js with showConfirmationModal"
Task: "Replace confirm() in dashboard/js/positions.js with showConfirmationModal"
Task: "Replace confirm() in dashboard/js/orders.js with showConfirmationModal"
Task: "Replace confirm() in dashboard/js/app.js with showConfirmationModal"
```

---

## Implementation Strategy

### MVP First (User Story 1 & 2)

1. Complete Phase 1 & 2 (Setup + Foundation)
2. Implement Phase 3 (Message Center — operators see styled errors)
3. Implement Phase 4 (Modals — operators get contextual confirmations)
4. **STOP and VALIDATE**: Verify no `confirm()` or `alert()` calls remain. Test all critical paths.

### Incremental Delivery

1. Deploy Message Center + Modals → operators immediately get better error UX
2. Add Readiness Panels to remaining tabs → blocked states prevent operator errors
3. Add Sticky Banner → operators always know bridge state
4. Add Timeline + Support Package → operators can self-serve troubleshooting
5. Add Validation Hints + Accessibility → polish and compliance
