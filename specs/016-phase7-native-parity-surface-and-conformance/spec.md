# Feature Specification: Phase 7 — Native Parity Surface and Conformance

**Feature Branch**: `016-phase7-native-parity-surface-and-conformance`
**Created**: 2026-03-03
**Status**: Draft
**Plan Reference**: `docs/plans/phased-user-facing-reliability/7-native-parity-surface-and-conformance.md`
**Phase Dependency**: Phases 0–6 must all be delivered and proven in production-like runs before this phase begins.

---

## Overview

The MT5 bridge currently exposes a curated "safe domain" API covering the most common trading operations. This is intentional and correct for most operators. However, advanced users and integrations need access to a broader set of MT5 capabilities that are not currently surfaced — margin calculations, market book data, richer terminal session introspection — without the guardrails being removed for standard operators.

Additionally, broker variance (different brokers implement different subsets of the MT5 protocol) means "parity" cannot mean identical behavior everywhere. It must mean: **broad capability coverage, explicit variance documentation, deterministic fallback policies, and a conformance harness** that maps what works in each broker environment.

This phase delivers: (1) extension of the safe domain API to cover parity gaps, (2) a governed advanced/expert namespace for near-1:1 MT5 function exposure, (3) operational compatibility profiles, and (4) a conformance report harness for per-broker validation.

---

## User Scenarios & Testing _(mandatory)_

### Primary User Story

As an advanced integration developer, I want to access MT5 capabilities that go beyond the current bridge operations — margin and profit calculations, market book depth, richer order pre-checks — through a clearly labeled expert API namespace, so that I can build advanced tooling without needing a separate MT5 Python connection.

As a system operator deploying the bridge for a new broker for the first time, I want to run a conformance check that tells me: which capabilities work for this broker, which don't, which may have fallback behavior, and what compatibility mode to use for production — so that I go into production with documented expectations, not surprises.

As a standard trading operator, I want the safe domain API to continue working exactly as today — the expert namespace exists but I am never exposed to it unless I explicitly navigate to it.

### Acceptance Scenarios

1. **Given** an advanced user with access to the bridge API, **When** they call a `GET /mt5/raw/margin-check` endpoint with a symbol and volume, **Then** they receive the MT5 margin check result including free margin and margin rate — and the response clearly labels the endpoint as "advanced/expert mode."

2. **Given** the bridge running against Broker A (which supports FOK and IOC), **When** the conformance harness is run, **Then** the conformance report shows all order execution capability areas as `pass`, notes the supported filling modes, and recommends `strict_safe` compatibility mode.

3. **Given** the bridge running against Broker B (which supports only RETURN filling), **When** the conformance harness is run, **Then** the conformance report shows filling mode checks as `warn` with fallback behavior confirmed, and recommends `balanced` or `max_compat` mode.

4. **Given** a standard operator using the Execute tab, **When** the expert namespace is deployed, **Then** the operator's experience is identical to before — the safe domain API routes respond identically, the Execute/Positions/Orders tabs are unchanged, and no advanced endpoint is visible in the standard dashboard UI unless it is explicitly navigated to.

5. **Given** the bridge is configured with `compatibility_mode: max_compat`, **When** an order is submitted, **Then** the retry/fallback behavior is more aggressive than in `strict_safe` mode, and the operator-facing warning verbosity is higher — the mode difference is observable in the response and logs.

6. **Given** a coverage matrix entry for MT5 capability area "margin and profit calculation", **When** it is implemented and the conformance harness runs, **Then** the matrix entry is updated with `implemented: true`, `test_coverage: pass`, and the known broker variance field documents any broker-specific differences observed.

7. **Given** any new raw endpoint added to the `/mt5/raw/` namespace, **When** it is deployed, **Then** it has documented: safety classification, authentication behavior (same key required), redaction/logging policy (no sensitive data logged), and its interaction with the readiness system (does it gate on readiness or not).

### Edge Cases

- What if a broker does not support a capability in the conformance harness at all (e.g., no market book data)? → The conformance report marks the capability as `not_supported` (not `fail`), documents the broker-specific limitation, and the operator is informed which mode to use to avoid the unsupported feature.
- What if an advanced endpoint is called by an operator who is not aware of its risks? → The response includes a safety disclaimer in the wrapper field of the response, and the dashboard does not surface raw endpoints in standard navigation — discovery is intentional, not accidental.
- What if a compatibility profile is set to `max_compat` but a destructive operation fails destructively anyway? → The canonical error is returned with the compatibility mode noted in the `context` field, and the conformance report is updated with the failure scenario.

---

## Requirements _(mandatory)_

### Functional Requirements

**Coverage Matrix (existing parity gaps)**

- **FR-001**: The team MUST maintain a live MT5 parity coverage matrix tracking the seven MT5 Python library capability categories: connection/session lifecycle, terminal/account metadata, symbol and market data, order pre-check and calculations, order submission and management, history and reporting, and advanced facilities (market book, etc.).
- **FR-002**: For each capability in the matrix, the team MUST record: `implemented` (yes/partial/no), `constraints`, `known_broker_variance`, `fallback_behavior`, `test_coverage`, and `operator_readiness_impact`.
- **FR-003**: The coverage matrix MUST be updated whenever a capability is added, changed, or a new broker variance is discovered.

**Safe Domain API Extensions**

- **FR-004**: Parity gaps identified as missing from the safe domain that are commonly needed — explicit margin/profit calculation surfaces, deeper retcode/last-error translation coverage — MUST be added to the safe domain API before or alongside the expert namespace, following the same Phase 1–3 contracts (canonical envelope, readiness integration, idempotency where applicable).

**Expert/Advanced Namespace**

- **FR-005**: An advanced API namespace at `/mt5/raw/` MUST be introduced for near-1:1 MT5 function exposure to expert users.
- **FR-006**: Every endpoint in the `/mt5/raw/` namespace MUST require the same API key authentication as the safe domain API.
- **FR-007**: Every `/mt5/raw/` endpoint MUST include in its response a safety disclaimer field indicating that the endpoint is in "advanced mode" and that guardrails are reduced.
- **FR-008**: Every `/mt5/raw/` endpoint MUST be documented with: safety classification, authentication behavior, redaction/logging policy (no credentials or sensitive data), and its interaction with the readiness system.
- **FR-009**: The safe domain API MUST remain the default recommended path — the advanced namespace MUST be clearly labeled as expert-only in all documentation and responses.
- **FR-010**: The dashboard MUST NOT surface `/mt5/raw/` endpoints in standard operator navigation. Advanced access requires explicit API client configuration.

**Conformance Harness**

- **FR-011**: The bridge MUST provide a conformance suite that can be executed against any connected broker/terminal environment to validate capability behavior.
- **FR-012**: The conformance suite MUST validate: endpoint behavior across key operation classes, readiness checks vs. runtime outcomes, retcode/error normalization consistency, fallback behavior correctness (including comment compatibility from Phase 4), and launcher/runtime diagnostics integrity.
- **FR-013**: The conformance report MUST include per-broker dimensions: broker name and server, terminal build/version, Python runtime context, compatibility profile used, and a pass/warn/fail breakdown by capability area.
- **FR-014**: The conformance report MUST include a recommendation for which compatibility mode to use in production for the tested broker/environment.
- **FR-015**: The conformance suite MUST be runnable without interrupting an active production bridge session — it uses read-only and non-destructive operations where possible, and labels any write-tests clearly.

**Operational Compatibility Profiles**

- **FR-016**: The bridge MUST support three named operational compatibility profiles: `strict_safe`, `balanced`, and `max_compat`.
- **FR-017**: Each profile MUST define its behavior across four dimensions: retry/fallback aggressiveness, optional field handling policy, gating strictness, and user-facing warning verbosity.
- **FR-018**: The active profile MUST be set via an environment variable and readable at runtime from the `/diagnostics/runtime` endpoint without requiring a bridge restart to change.
- **FR-019**: Profile switches MUST be explicit and auditable — changing the profile logs a structured entry with the old and new profile values, the timestamp, and (if available) the operator identity.
- **FR-020**: All three profiles MUST be reversible — switching from `max_compat` back to `strict_safe` MUST not require a code change or schema migration.

**Governance**

- **FR-021**: Any new raw endpoint addition MUST pass a governance checklist review before merge: safety classification defined, authentication required, logging/redaction policy defined, readiness interaction defined.
- **FR-022**: The safe domain API MUST be the recommended path in all operator-facing documentation — the expert namespace is a documented but explicitly secondary surface.

### Key Entities

- **ParityCoverageMatrix**: The living inventory of MT5 capability categories vs. bridge coverage levels, with variance and risk annotations per capability.
- **AdvancedNamespace**: The `/mt5/raw/` endpoint collection offering near-1:1 MT5 library function exposure to expert API consumers.
- **ConformanceSuite**: The runnable validation harness that exercises the bridge against a connected broker and produces a structured conformance report.
- **ConformanceReport**: The per-broker output of the conformance suite: capability pass/warn/fail table, variance notes, and production mode recommendation.
- **CompatibilityProfile**: One of three named operational modes (`strict_safe`, `balanced`, `max_compat`) controlling bridge behavior in four dimensions for different broker environments.
- **GovernanceChecklist**: The required documentation set for any new raw endpoint before it can be merged.

---

## Success Criteria _(mandatory)_

1. **Coverage matrix maintained**: The MT5 parity coverage matrix covers all 7 capability categories and is updated as part of the standard code review process for any change that affects coverage — confirmed by a matrix review at phase completion.

2. **Conformance harness usable**: The conformance suite can be executed against a live MT5 terminal and produces a complete conformance report without requiring any code change — confirmed by running it against at least two different broker environments.

3. **Advanced endpoints governed**: 100% of endpoints in the `/mt5/raw/` namespace have completed the governance checklist (safety class, auth, logging policy, readiness interaction) — confirmed by a namespace review sign-off.

4. **Standard operator unaffected**: In an end-to-end regression test of Phases 1–6 behaviors after Phase 7 is deployed, no existing safe domain API contract, dashboard UI flow, or operator runbook procedure is broken.

5. **Compatibility mode observable**: Changing the compatibility profile is reflected in the `/diagnostics/runtime` response within one poll cycle (≤10 seconds), and the change is logged with the required structured fields.

6. **Conformance-guided production deployment**: At least one broker onboarding session uses the conformance report output as the basis for selecting the production compatibility mode — documented as a case study in the operator runbook.

---

## Assumptions

- Phase 7 is the only phase that requires Phases 1–6 to be fully deployed and validated in production-like conditions before it begins. The "proven in production-like runs" gate is an out-of-band sign-off process.
- The conformance suite uses the bridge's own API (not direct MT5 calls) where possible — it is an end-to-end test of the bridge, not an MT5 unit test.
- The conformance suite includes at least some write operations (e.g., order send + immediate cancel) that require a live but safe test account. These are clearly labeled as write tests and require explicit opt-in to run.
- The `/mt5/raw/` namespace does not include raw `order_send` without guardrails in the initial delivery — the expert namespace starts with read-heavy capabilities (margin checks, market book, session introspection) and expands write coverage incrementally after governance review.

---

## Out of Scope

- Removing or changing the safe domain API (it remains unchanged and is the default).
- Supporting non-MT5 execution adapters.
- Real-time streaming of market book data (WebSocket upgrade is a separate future feature).
- Persistent cross-session storage of conformance reports (they are generated and saved to disk at run time by the operator; no server-side storage).
- UI for running the conformance suite from the dashboard (CLI-first; dashboard integration is a future enhancement).
