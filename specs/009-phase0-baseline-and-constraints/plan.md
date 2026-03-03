# Implementation Plan: Phase 0 — Baseline and Constraints

**Branch**: `009-phase0-baseline-and-constraints` | **Date**: 2026-03-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-phase0-baseline-and-constraints/spec.md`

## Summary

Phase 0 captures a code-grounded baseline of the existing MT5 bridge, freezes non-negotiable constraints, and produces the shared terminology and compatibility artifacts that all subsequent reliability phases depend on. This is a documentation and agreement phase — no runtime behavior changes are made.

The deliverables are six distinct documents: (1) a terminology glossary, (2) a canonical tracking ID policy, (3) an error-code namespace policy, (4) a compatibility pledge, (5) a launcher invariants checklist, and (6) an MT5 parity gap register. All are grounded in a codebase snapshot taken on 2026-03-03.

## Technical Context

**Language/Version**: Python 3.12 (backend bridge); Vanilla JS ES2020+ (dashboard)
**Primary Dependencies**: FastAPI ≥0.104, Pydantic v2 ≥2.5, MetaTrader5 ≥5.0.5640, PyYAML ≥6.0
**Storage**: JSONL log files (audit), JSON session metadata (launcher), YAML (symbol config)
**Testing**: pytest, ruff (linting)
**Target Platform**: Windows-native MT5 terminal via WSL2 bridge wrapper
**Project Type**: Microservice (REST API bridge) + Vanilla JS dashboard
**Performance Goals**: N/A for this phase (documentation only)
**Constraints**: No runtime code changes; all outputs are markdown/reference documents
**Scale/Scope**: Single bridge instance, single operator, single MT5 terminal

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

| Principle                            | Status  | Notes                                                                         |
| ------------------------------------ | ------- | ----------------------------------------------------------------------------- |
| I. Multi-Agent Orchestration         | ✅ N/A  | Phase 0 is documentation; no agent changes                                    |
| II. Trading Modes & Execution Safety | ✅ Pass | Baseline documents existing execution policy controls without modifying them  |
| III. Data-Driven Valuation           | ✅ N/A  | Not relevant to infrastructure baseline                                       |
| IV. Risk-Managed Decision Making     | ✅ N/A  | Not relevant to infrastructure baseline                                       |
| V. Execution & Connection Frameworks | ✅ Pass | Baseline inventories existing connection/failure handling without changing it |
| VI. MT5 Connection Framework         | ✅ Pass | Parity gap register documents current MT5 integration coverage as-is          |

No violations. Proceed.

## Project Structure

### Documentation (this feature)

```text
specs/009-phase0-baseline-and-constraints/
├── plan.md              # This file
├── research.md          # Phase 0 output — codebase findings
├── data-model.md        # Phase 1 output — entity definitions for the 6 deliverables
├── quickstart.md        # Phase 1 output — how to consume and maintain the baseline docs
├── contracts/           # Phase 1 output — document schemas for each deliverable
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (deliverable output locations)

```text
docs/baseline/
├── glossary.md                  # FR-001, FR-002: Terminology definitions + severity scale
├── tracking-id-policy.md        # FR-003, FR-004: tracking_id format, generation, propagation
├── error-code-namespace.md      # FR-005, FR-006: Code namespace, naming rules, initial codes
├── compatibility-pledge.md      # FR-007, FR-008: Per-phase stability commitments
├── launcher-invariants.md       # FR-009, FR-010: Script behavior freeze checklist
├── parity-gap-register.md       # FR-011, FR-012: MT5 API coverage matrix
└── endpoint-snapshot.md         # FR-013, FR-014: Current endpoint families + scripts inventory
```

**Structure Decision**: All Phase 0 deliverables are markdown reference documents placed under `docs/baseline/`. This is a new directory not yet in the codebase — it becomes the shared source of truth for all subsequent phases. No `app/`, `tests/`, or `dashboard/` changes.

## Complexity Tracking

> No complexity violations detected. Phase 0 is purely documentation with zero new dependencies and zero runtime changes.
