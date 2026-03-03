# Feature Specification: Phase 0 — Baseline and Constraints

**Feature Branch**: `009-phase0-baseline-and-constraints`
**Created**: 2026-03-03
**Status**: Draft
**Plan Reference**: `docs/plans/phased-user-facing-reliability/0-baseline-and-constraints.md`
**Phase Dependency**: none (foundation for all subsequent phases)

---

## Overview

Before any behavioral changes are made to the bridge, a shared and explicitly agreed-upon baseline must be captured and locked. This phase establishes a code-grounded inventory of what exists, freezes non-negotiable constraints, and produces the compatibility and terminology artifacts that every subsequent phase depends on.

This is a documentation, agreement, and scaffolding phase — no user-facing runtime behavior changes. Its outputs gate the start of Phase 1.

---

## User Scenarios & Testing _(mandatory)_

### Primary User Story

As a developer or operator about to implement reliability improvements, I need a single locked source of truth covering what the bridge currently does, what must never change, and what shared vocabulary the team uses — so that every subsequent change can be implemented and reviewed consistently without renegotiating fundamentals each time.

### Acceptance Scenarios

1. **Given** a developer beginning work on Phase 1, **When** they read the Phase 0 artifacts, **Then** they can immediately answer: "what are the stable endpoint families?", "what terms mean error vs warning vs status?", and "what tracking ID format is required?"

2. **Given** an operator reviewing a proposed change to launcher scripts, **When** they consult the launcher invariants checklist produced in this phase, **Then** they can determine whether the proposed change violates a non-negotiable constraint — without needing a code review.

3. **Given** a developer producing a Phase 3 error-handling change, **When** they check the error-code namespace policy from Phase 0, **Then** they can select a semantically correct and future-proof error code without creating a namespace collision.

4. **Given** a new team member onboarding to the project, **When** they read the compatibility pledge document, **Then** they understand exactly which API contracts and script behaviors must remain unchanged across the full phased rollout.

5. **Given** the MT5 parity gap register produced in this phase, **When** a new parity feature is proposed in Phase 7, **Then** the register already contains the capability area, its current coverage level, and any known broker variance risks.

### Edge Cases

- What if a constraint from the baseline conflicts with a requirement in a later phase? → The conflict is documented in the gap register; the invariant takes precedence unless an explicit exception is formally approved and recorded.
- What if the codebase changes significantly before Phase 1 begins? → The baseline snapshot date is recorded; any material changes must trigger a Phase 0 re-review before Phase 1 proceeds.

---

## Requirements _(mandatory)_

### Functional Requirements

**Terminology Glossary**

- **FR-001**: The team MUST produce and agree upon a written glossary that defines: `error`, `warning`, `status`, `advice`, `blocker`, and `recovery` in the context of this bridge's user-facing messaging system.
- **FR-002**: The glossary MUST include a severity scale (`low`, `medium`, `high`, `critical`) with explicit criteria for each level.

**Canonical Incident Identity Policy**

- **FR-003**: The team MUST define a `tracking_id` format: its structure, generation strategy, uniqueness scope, and how it propagates from backend log to user-facing message.
- **FR-004**: The tracking ID policy MUST specify how operators can use a `tracking_id` from a dashboard screenshot to locate the corresponding backend log entry.

**Error-Code Namespace Policy**

- **FR-005**: The team MUST define a stable error-code namespace: allowed prefixes, naming conventions, and the process for adding new codes in future phases.
- **FR-006**: The namespace policy MUST enumerate the minimum required codes covering validation failures, connectivity/runtime failures, policy/capability failures, request-compatibility failures, and generic fallback codes.

**Compatibility Pledge**

- **FR-007**: The team MUST produce a compatibility pledge document that explicitly lists, per phase, which endpoint contracts, response shapes, and HTTP behaviors remain stable and which may change only during a versioned migration window.
- **FR-008**: The pledge MUST state the backward-compatibility window policy (i.e., how long legacy `detail`-shaped responses continue to be supported alongside the canonical envelope).

**Launcher Invariants Checklist**

- **FR-009**: The team MUST produce an explicit checklist of launcher and script behaviors that MUST NOT change in any phase: script names, invocation patterns, restart policy, log bundle structure, and smoke-test procedure.
- **FR-010**: The checklist MUST be used as a required gate in code review for any change affecting `scripts/`.

**MT5 Parity Gap Register**

- **FR-011**: The team MUST produce an initial MT5 parity gap register enumerating the MT5 Python library capability categories, their current bridge coverage level, and any known broker variance risks per category.
- **FR-012**: The gap register MUST define the tracking fields used in subsequent phases: `implemented`, `constraints`, `known_broker_variance`, `fallback_behavior`, `test_coverage`, `operator_readiness_impact`.

**Existing-State Snapshot**

- **FR-013**: The baseline MUST explicitly record, as of the snapshot date, all active endpoint families (`/health`, `/execute`, `/close-position`, etc.) and their primary purpose — so subsequent phases have a testable regression surface.
- **FR-014**: The baseline MUST record all existing operational scripts and their purpose, so launcher hardening in Phase 5 has a clear "do not remove" list.

### Key Entities

- **Terminology Glossary**: A shared vocabulary document mapping terms like `error`, `warning`, `blocker`, `severity` to their precise definitions within this bridge's messaging system.
- **TrackingID Policy**: Definition of the unique incident identity format and its propagation path from bridge backend to operator dashboard.
- **ErrorCode Namespace**: The enumerated, stable list of semantic error codes with their assigned prefixes, purpose, and governance rules.
- **CompatibilityPledge**: A per-phase statement of which behaviors are frozen, which may evolve, and under what backward-compatibility window.
- **LauncherInvariantsChecklist**: An explicit, reviewable list of launcher behaviors that must survive all changes.
- **ParityGapRegister**: A structured inventory of MT5 Python API capability categories vs. current bridge coverage, with variance and risk annotations.

---

## Success Criteria _(mandatory)_

1. **Glossary consensus**: All team members can read the glossary and immediately categorize a new runtime event into the correct term (error, warning, status, advice) without ambiguity — validated by a peer-review sign-off.

2. **Tracking ID clarity**: Given a `tracking_id` from a dashboard screenshot, any team member can locate the corresponding structured log entry within 60 seconds — no log archaeology required.

3. **Error-code uniqueness**: No two error codes in the namespace have the same semantic meaning — validated by a namespace review sign-off before Phase 1 begins.

4. **Compatibility pledge coverage**: The compatibility pledge explicitly covers 100% of the endpoint families listed in the baseline snapshot, with a stated per-family stability level.

5. **Launcher checklist enforceability**: The launcher invariants checklist is used as a mandatory gate for the first Phase 5 code review — its presence and use is the acceptance test.

6. **Gap register completeness**: The MT5 parity gap register covers all 7 MT5 Python library category areas defined in Phase 7's plan, with at least an initial coverage assessment for each.

---

## Assumptions

- The codebase inventory is taken from the bridge as it exists on 2026-03-03. Later phases will update rather than replace this baseline.
- "Team agreement" on glossary and compatibility pledge is an out-of-band process (review meeting or async sign-off) — this spec does not define that governance process, only requires it happens and is recorded.
- The parity gap register does not need to be exhaustive at Phase 0; it must be sufficient to guide Phase 7 scoping.

---

## Out of Scope

- Any changes to runtime bridge behavior.
- Changes to API endpoints, response shapes, or dashboard UI.
- Implementation of any error code, tracking ID, or message normalization logic (those belong to Phase 1+).
- Automated enforcement tooling for the launcher checklist (manual review/reading is sufficient at this stage).
