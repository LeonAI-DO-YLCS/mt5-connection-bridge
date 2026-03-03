# Feature Specification: Phase 6 — Dashboard Operator Experience

**Feature Branch**: `015-phase6-dashboard-operator-experience`
**Created**: 2026-03-03
**Status**: Draft
**Plan Reference**: `docs/plans/phased-user-facing-reliability/6-dashboard-operator-experience.md`
**Phase Dependency**: Phase 1 (message contract), Phase 2 (readiness), Phase 3 (execution hardening), Phase 4 (close compatibility)

---

## Overview

The dashboard currently surfaces many capabilities, but its operator experience is that of a raw API development tool: actions trigger browser `alert()` dialogs, error messages are raw JSON, and there is no persistent operation history or centralized feedback area. When things go wrong, operators have no obvious next step.

This phase transforms the dashboard into an **operational control plane**: consistent confirmation flows, a centralized message center, inline readiness panels, an operator timeline, and copy-to-clipboard support package for fast support escalation — all built incrementally within the existing dashboard architecture.

---

## User Scenarios & Testing _(mandatory)_

### Primary User Story

As a trading operator who has just received an error message, I want to immediately understand: (1) what happened in plain language, (2) whether I can resolve it myself or need support, and (3) how to hand off the incident to support with all relevant context in one click. I should never need to open a browser developer console or read raw JSON to answer these questions.

As an operator in a fast-moving trading session, I want destructive actions (close position, cancel order) to require a contextual confirmation modal — not a raw browser `confirm()` dialog — so I can verify the details of what I'm about to do before committing.

### Acceptance Scenarios

1. **Given** an operator on the Execute tab about to submit a trade, **When** they click "Submit", **Then** a standardized confirmation modal appears showing the action details, a risk summary line, and Confirm/Cancel buttons — not a browser `confirm()` dialog.

2. **Given** a failed trade operation, **When** the error is shown in the dashboard, **Then** the message center displays: the error title in plain language, the explanation, the action to take, the `tracking_id`, and a "Copy Support Package" button — not a raw alert box.

3. **Given** the operator clicks "Copy Support Package", **When** the clipboard content is pasted, **Then** it contains: the `tracking_id`, the operation type, the key readiness statuses at the time of the action, and the timestamp — formatted for easy support handoff.

4. **Given** an operator on the Positions tab about to close a position, **When** the readiness panel shows `overall_status: blocked`, **Then** the "Close" button is visually disabled and a blocker summary is shown inline in the panel — no submit is possible until the blocker resolves.

5. **Given** a series of operations performed in the current session, **When** the operator opens the operation timeline panel, **Then** they can see each recent operation: action type, outcome, canonical code, tracking ID, and timestamp — in reverse chronological order.

6. **Given** an operator using only a keyboard (no mouse), **When** they navigate to a confirmation modal, **Then** they can Tab between Confirm and Cancel, press Enter to confirm or Escape to cancel, without mouse interaction required.

7. **Given** a message with `severity: critical`, **When** it is displayed in the message center, **Then** the styling (icon, color border, and a text label e.g. "CRITICAL") makes its severity immediately distinct from a `low` advisory — even for operators with color vision impairment (text labels, not color alone).

### Edge Cases

- What if the readiness panel cannot be fetched before a submit (e.g., bridge is fully down)? → The submit button is still disabled, and the message center shows a "Cannot verify readiness — bridge may be offline" message using the Phase 1 envelope renderer.
- What if the operation timeline grows very large during a long session? → The timeline shows the most recent N operations (e.g., 50), with an option to view older entries in a scrollable panel — not an unbounded list.
- What if the "Copy Support Package" action fails (clipboard API not available)? → A text area containing the support package content is shown in a modal so the operator can manually select and copy it.

---

## Requirements _(mandatory)_

### Functional Requirements

**Centralized Message Center**

- **FR-001**: The dashboard MUST introduce a centralized message center component that replaces direct `alert()`, `confirm()`, and `prompt()` calls in all critical operation paths (execute, close-position, pending order, cancel order).
- **FR-002**: The message center MUST render messages from the Phase 1 canonical envelope: `category`, `severity`, `title`, `message`, `action`, and `tracking_id`.
- **FR-003**: The message center MUST apply consistent visual styling by `category` and `severity` using both color and text/icon indicators — no critical information conveyed by color alone.
- **FR-004**: The message center MUST display the `tracking_id` in every failure message with a one-click copy shortcut adjacent to the ID.
- **FR-005**: The message center MUST provide a collapsible "Details" section containing the `context` field — collapsed by default, expandable for advanced troubleshooting.

**Standardized Confirmation Modals**

- **FR-006**: Destructive actions (close position, cancel order) MUST trigger a standardized confirmation modal — not a browser `confirm()` dialog.
- **FR-007**: Confirmation modals MUST display contextual details about the specific action being confirmed (e.g., symbol name, volume, position direction for close operations).
- **FR-008**: Confirmation modals MUST include a risk summary line appropriate to the action category.
- **FR-009**: Confirmation modals MUST have clearly labeled Confirm and Cancel action buttons.

**Inline Readiness Panels**

- **FR-010**: The Execute tab, Positions tab (close/modify actions), and Orders tab (cancel/modify actions) MUST each include an inline readiness panel that displays the Phase 2 readiness response for the currently selected operation context.
- **FR-011**: When `overall_status: blocked`, the primary action button MUST be visually disabled and the readiness panel MUST list each blocker with its `user_message` and `action`.
- **FR-012**: When `overall_status: degraded`, the primary action button MUST be active but MUST display a non-blocking warning summary that the operator must acknowledge (e.g., a visible warning state, not a hidden warning).
- **FR-013**: The readiness panel MUST show the freshness timestamp and a "Refresh" affordance.

**Sticky Connection/Readiness Banner**

- **FR-014**: A persistent banner across the top of the dashboard MUST show the current bridge connection and readiness state (`connected`, `degraded`, `disconnected`), updating based on periodic polls.
- **FR-015**: When the banner shows `blocked` or `disconnected`, it MUST display a brief summary of the most critical blocking condition.

**Copy Support Package**

- **FR-016**: Every failure message displayed by the message center MUST include a "Copy Support Package" action button.
- **FR-017**: The support package content MUST include: `tracking_id`, operation metadata (operation type, symbol, direction/volume where applicable), key readiness statuses at the time of the action, and a timestamp.
- **FR-018**: If the clipboard API is unavailable, the support package MUST be displayed in a selectable text area as a fallback.

**Operator Timeline**

- **FR-019**: The dashboard MUST provide an operator timeline panel showing recent operations in the current session in reverse chronological order.
- **FR-020**: Each timeline entry MUST display: action type, outcome (success/failure), canonical code, `tracking_id`, and timestamp.
- **FR-021**: The timeline MUST be limited to the most recent 50 operations, with a scrollable view for all entries in the current session.

**Accessibility**

- **FR-022**: All confirmation modals and message center dialogs MUST be keyboard-navigable (Tab, Enter, Escape).
- **FR-023**: Severity and state indicators MUST use both color/visual style AND a text label or icon — not color alone.
- **FR-024**: All interactive elements MUST have descriptive labels readable by screen readers.

**Inline Validation and Hints**

- **FR-025**: Form inputs on the Execute and Pending Order tabs MUST display inline validation hints (e.g., volume outside allowed range) before submission, using the readiness check data where available.
- **FR-026**: Inline hints MUST use plain-English text matching the Phase 1 message contract style — not raw field names or Pydantic error objects.

### Key Entities

- **MessageCenter**: The centralized dashboard component responsible for rendering Phase 1 canonical envelopes as styled, interactive messages with copy-to-clipboard and expand-details affordances.
- **ConfirmationModal**: The standardized dialog for destructive action confirmation, with contextual details and risk summary.
- **ReadinessPanel**: The per-tab inline panel displaying the Phase 2 readiness response, gating submission when blocked.
- **StickyConnectionBanner**: The persistent dashboard header element showing current bridge state and critical blockers.
- **SupportPackage**: The copyable incident context bundle containing `tracking_id`, operation metadata, readiness snapshot, and timestamp.
- **OperatorTimeline**: The session-scoped reverse-chronological log of recent operations with outcome, code, and tracking ID.

---

## Success Criteria _(mandatory)_

1. **No alerts, confirms, or prompts in critical paths**: After deployment, zero browser-native `alert()`, `confirm()`, or `prompt()` calls exist in the Execute, Close Position, Cancel Order, or Pending Order flows — confirmed by code review and automated browser test.

2. **Support resolution time**: Given a representative incident, a support engineer using only the information from the "Copy Support Package" clipboard content can identify the operation, the failure code, and the correlation ID needed to find the log entry — in under 2 minutes.

3. **Blocked state enforcement**: In an end-to-end test, with a simulated blocked readiness state, the primary action button is disabled in 100% of tested tabs (Execute, Positions, Orders).

4. **Accessibility baseline**: All confirmation modals and the message center can be operated entirely by keyboard (Tab/Enter/Escape) — confirmed by a keyboard-only interaction test.

5. **Operator comprehension**: Five onboarding operators (non-developers) can correctly answer "why is this operation blocked?" and "what should I do?" using only the dashboard UI — no log reading, no JSON inspection — in a moderated UAT session.

6. **Existing behavior preserved**: All existing tab layouts, navigation patterns, and non-critical-path `alert` usages (e.g., informational banners not tied to trade operations) are unchanged after this phase is deployed.

---

## Assumptions

- This phase is built on the existing Vanilla JS dashboard architecture — no framework migration, no React, no full redesign.
- The Phase 1 message contract (canonical envelope) is fully deployed before this phase begins; the dashboard renders from that contract.
- The Phase 2 readiness endpoint is available and functional before the readiness panels are built.
- "Critical operation paths" that require the message center and modal replacement are: execute, close-position, pending-order, cancel-order, and modify-order/sltp. Informational-only `alert` calls outside these paths may be addressed as a follow-up.
- The operator timeline is session-local (in browser memory) — no backend storage of timeline events is required.

---

## Out of Scope

- Full dashboard redesign or component library migration.
- WebSocket-based real-time event streaming to the timeline (polling is sufficient).
- Persistent timeline storage (session-local memory is sufficient).
- Authentication or permission changes.
- MT5 parity expansion (Phase 7).
- Changes to launcher scripts or runtime diagnostics (Phase 5).
