# Feature Specification: Phase 2 — Readiness and Prerequisites

**Feature Branch**: `011-phase2-readiness-and-prerequisites`
**Created**: 2026-03-03
**Status**: Draft
**Plan Reference**: `docs/plans/phased-user-facing-reliability/2-readiness-and-prerequisites.md`
**Phase Dependency**: Phase 0 (baseline), Phase 1 (canonical message contract)

---

## Overview

Prerequisite checks are currently scattered: some live in the worker, some in individual endpoint handlers, some are absent. As a result, operators can initiate trade-affecting actions that are guaranteed to fail — the failure only surfaces deep in the MT5 execution path, producing confusing error messages without actionable guidance.

This phase introduces a **single unified readiness contract**: a dedicated endpoint that aggregates all global and symbol/action-specific pre-conditions into a structured response. The dashboard consults this contract before allowing destructive actions, giving operators clear, upfront visibility into what is blocking a trade — before anything goes to MT5.

---

## User Scenarios & Testing _(mandatory)_

### Primary User Story

As a trading operator preparing to place a trade, I want the dashboard to tell me — before I click Submit — exactly which prerequisites are met, which are failing, and what I need to do to unblock the trade. I should never have to click Submit to discover that account trading is disabled, that the symbol is in close-only mode, or that the bridge worker is not connected.

As a support engineer, when an operator asks "why can't I trade?", I want to be able to direct them to a readiness panel that lists every blocker with a plain-English explanation and next step — without needing to read logs.

### Acceptance Scenarios

1. **Given** the MT5 worker is disconnected, **When** the dashboard loads the Execute tab, **Then** the readiness panel shows `overall_status: blocked` and a blocker entry: "Bridge worker is not connected — start or restart the bridge to proceed."

2. **Given** account trading is disabled by the broker, **When** an operator opens the Execute tab for any symbol, **Then** the Submit button is disabled and the readiness panel displays a blocking entry explaining that account trading is disabled, with a next-step action.

3. **Given** a symbol in close-only trade mode, **When** the operator selects it in the Execute tab, **Then** the readiness panel shows `overall_status: blocked`, a blocker item for trade mode restriction, and the Submit button is disabled.

4. **Given** a symbol where the tick data is stale (older than the freshness threshold), **When** a market order is about to be submitted, **Then** the readiness panel shows a `warn` check for tick freshness and the operator is explicitly asked to acknowledge before proceeding.

5. **Given** all readiness checks pass for a given symbol and direction, **When** the operator views the readiness panel, **Then** `overall_status` is `ready`, every check shows `pass`, and the Submit button is enabled.

6. **Given** the readiness response was fetched 30 seconds ago, **When** the operator views the panel, **Then** a freshness timestamp and "Refresh" affordance are shown, indicating how old the readiness data is.

7. **Given** a blocked readiness state, **When** the operator corrects the issue (e.g., re-enables execution policy), **Then** clicking Refresh produces a new readiness response that shows the previously blocked check now passing.

### Edge Cases

- What if the readiness endpoint itself is unreachable (bridge is completely down)? → The dashboard shows a top-level connectivity error using the Phase 1 message renderer, disables all trade actions, and does not show a partial readiness panel.
- What if optional parameters (`symbol`, `direction`, `volume`) are omitted? → Only the global checks are evaluated; symbol/action checks return `status: unknown` (not `fail`) and are noted as "not evaluated."
- What if a readiness check is momentarily flapping (e.g., tick freshness alternates)? → The check result at response time is authoritative; the UI does not need to smooth this — operators use the refresh affordance.

---

## Requirements _(mandatory)_

### Functional Requirements

**Unified Readiness Endpoint**

- **FR-001**: The bridge MUST expose a `GET /readiness` endpoint that evaluates all prerequisite conditions and returns a structured readiness response.
- **FR-002**: The endpoint MUST accept optional query parameters: `operation` (the trade action type), `symbol` (MT5 symbol name or alias), `direction` (`buy` or `sell`), and `volume` — to scope symbol/action-specific checks.
- **FR-003**: When called without optional parameters, the endpoint MUST evaluate and return only the global checks.

**Readiness Response Structure**

- **FR-004**: The response MUST include an `overall_status` field with values `ready`, `degraded`, or `blocked`.
  - `ready`: all checks pass or all failures are non-blocking.
  - `degraded`: at least one non-blocking warning exists, no blocking failures.
  - `blocked`: at least one blocking failure exists.
- **FR-005**: The response MUST include a `checks` array where each check entry contains: `check_id`, `status` (`pass`, `warn`, `fail`, `unknown`), `blocking` (boolean), `user_message`, `action`, and `details`.
- **FR-006**: The response MUST include summary arrays: `blockers` (all failing blocking checks), `warnings` (all non-blocking warnings), and `advice` (informational items).
- **FR-007**: The response MUST include a timestamp and a freshness metadata field indicating when the data was evaluated.

**Global Checks (always evaluated)**

- **FR-008**: The readiness endpoint MUST evaluate: worker connection status, MT5 terminal connection status, account trade authorization, terminal trade authorization, execution policy status, and queue overload/single-flight state.
- **FR-009**: Each global check failure MUST be `blocking: true` unless the phase plan explicitly designates otherwise.

**Symbol/Action Checks (evaluated when parameters provided)**

- **FR-010**: When `symbol` is provided, the readiness endpoint MUST evaluate: symbol existence and selectability, trade mode compatibility with the requested `direction`, filling mode support for the operation type, and volume constraint validation against `volume`.
- **FR-011**: When `operation` is a market order type, the endpoint MUST evaluate tick freshness for the symbol.
- **FR-012**: When the operation involves SL/TP modification, the endpoint MUST evaluate freeze-level and stops-level compatibility.
- **FR-013**: Trade mode violations MUST be `blocking: true`; tick freshness issues MUST be `blocking: false` (degraded/warning).

**Dashboard Gating Behavior**

- **FR-014**: Before the operator submits any trade-affecting action (execute, close, modify, cancel), the dashboard MUST request readiness for the specific operation context.
- **FR-015**: If `overall_status` is `blocked`, the dashboard MUST disable the primary action button(s) and display the blocker list with plain-English explanations and next steps.
- **FR-016**: If `overall_status` is `degraded`, the dashboard MUST allow the action but MUST display all warnings and require explicit operator acknowledgment before submission proceeds.
- **FR-017**: The dashboard MUST display the readiness response freshness timestamp and MUST provide a manual "Refresh" affordance.

### Key Entities

- **ReadinessResponse**: The structured output of `GET /readiness`, containing `overall_status`, `checks[]`, `blockers[]`, `warnings[]`, `advice[]`, and freshness metadata.
- **ReadinessCheck**: A single evaluated pre-condition with a `check_id`, `status`, `blocking` flag, `user_message`, `action`, and `details`.
- **GlobalCheck**: A pre-condition that applies to all trade operations regardless of symbol or direction (e.g., worker connection, account authorization).
- **SymbolCheck**: A pre-condition that is specific to a requested symbol, direction, volume, and/or operation type.
- **ReadinessPanel**: The dashboard UI component that displays the `ReadinessResponse` and gates action submission.

---

## Success Criteria _(mandatory)_

1. **Avoidable failures blocked upfront**: In a test suite of 10 controlled scenarios where a trade would fail at the MT5 level (disconnected worker, trade-disabled account, close-only symbol, invalid volume), 100% of them are caught and blocked by the readiness endpoint before any MT5 call is made.

2. **Clear blocker explanation**: For each blocked scenario, the readiness panel provides a `user_message` and `action` that a non-technical operator can follow to resolve the issue — confirmed by a user acceptance test (UAT) run by a non-developer.

3. **No Submit when blocked**: In end-to-end dashboard testing, the primary action button is disabled in 100% of `blocked` readiness states, and re-enabled in 100% of `ready` states after the blocker is resolved.

4. **Freshness visibility**: The readiness panel always shows either the response timestamp or a staleness warning — operators are never unaware that the data might be from a previous poll cycle.

5. **Backward compatibility**: The `GET /readiness` endpoint is purely additive and does not alter the behavior of any existing endpoint; all existing trade flows continue to work as before.

6. **Check accuracy**: The `overall_status` produced by the readiness endpoint matches the actual execution outcome in at least 95% of tested scenarios (i.e., `blocked` states fail at execution and `ready` states succeed at execution in the test environment).

---

## Assumptions

- The readiness endpoint uses the same Phase 1 canonical message envelope for its own error responses (if the endpoint itself fails to evaluate, it returns a canonical `INTERNAL_SERVER_ERROR` envelope).
- Readiness check results are not cached — each call to `GET /readiness` re-evaluates all checks against live MT5 state. Staleness is a UI concern managed by the freshness timestamp.
- The `GET /readiness` endpoint is protected by the same API key auth as all other bridge endpoints.
- "Execution policy" refers to the existing bridge-level feature flag that enables or disables trade execution — the readiness check reads its current state, it does not modify it.

---

## Out of Scope

- Automatic readiness polling/push (the dashboard polls on demand; no WebSocket streaming of readiness state in this phase).
- Readiness-based rate limiting or circuit breaking (Phase 3).
- Readiness checks for launcher/runtime health (Phase 5).
- Dashboard visual redesign beyond the readiness panel (Phase 6).
- MT5 parity checks (Phase 7).
