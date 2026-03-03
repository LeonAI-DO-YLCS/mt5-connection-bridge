# Quickstart: Phase 0 — Baseline and Constraints

**Branch**: `009-phase0-baseline-and-constraints`
**Date**: 2026-03-03

---

## What Is This?

Phase 0 produces **seven reference documents** that capture the current state of the MT5 bridge and establish shared agreements for all subsequent reliability phases. No code changes are made.

## Prerequisites

- Access to the `mt5-connection-bridge` repository
- Familiarity with the bridge's endpoint structure (see `app/routes/`)
- Familiarity with the launcher scripts (see `scripts/`)

## Deliverables

All documents are produced under `docs/baseline/`:

| Document                  | Purpose                                                       | Serves Phases |
| ------------------------- | ------------------------------------------------------------- | ------------- |
| `glossary.md`             | Shared terminology definitions (error, warning, status, etc.) | 1–7           |
| `tracking-id-policy.md`   | Tracking ID format and propagation rules                      | 1, 3, 6       |
| `error-code-namespace.md` | Canonical error code registry                                 | 1, 3, 4       |
| `compatibility-pledge.md` | Per-endpoint stability commitments across phases              | 1–7           |
| `launcher-invariants.md`  | Frozen launcher behaviors checklist                           | 5             |
| `parity-gap-register.md`  | MT5 Python API coverage assessment                            | 7             |
| `endpoint-snapshot.md`    | Current endpoint + script inventory                           | 1–7           |

## How to Consume These Documents

### For Phase 1+ implementers

1. Read `glossary.md` to understand the exact meaning of `error`, `warning`, `status`, `advice`, `blocker`, and `recovery`.
2. Read `error-code-namespace.md` before adding any new error code — verify no namespace collision.
3. Read `compatibility-pledge.md` to understand which endpoint contracts you can change and which are frozen.

### For Phase 5 (launcher) implementers

1. Read `launcher-invariants.md` before modifying anything in `scripts/`.
2. Use the checklist as a required gate in your code review PR template.

### For Phase 7 (parity) implementers

1. Read `parity-gap-register.md` to scope which MT5 capabilities to tackle first.
2. Use the `bridge_coverage` and `operator_readiness_impact` fields to prioritize work.

### For code reviewers

1. Reference `compatibility-pledge.md` when reviewing any endpoint change — verify the change respects the stability level.
2. Reference `launcher-invariants.md` when reviewing any `scripts/` change — verify no invariant is violated.

## How to Maintain These Documents

1. **Snapshot date**: All documents are baseline-dated. If the codebase changes materially before Phase 1 starts, trigger a Phase 0 re-review.
2. **Error codes**: When a new phase adds error codes, update `error-code-namespace.md` with the new entries and set `phase_introduced` correctly.
3. **Parity register**: When Phase 7 progresses, update `bridge_coverage` levels in `parity-gap-register.md`.
4. **Compatibility pledge**: When a phase introduces a migration window, update the corresponding endpoint's `stability_level` and `migration_notes`.

## Verification

After all 7 documents are written, verify:

1. `glossary.md` defines all 6 core terms with severity scale.
2. `tracking-id-policy.md` enables the "60-second log lookup" success criterion.
3. `error-code-namespace.md` has zero semantic duplicates.
4. `compatibility-pledge.md` covers 100% of endpoints listed in `endpoint-snapshot.md`.
5. `launcher-invariants.md` covers all 8 scripts in `scripts/`.
6. `parity-gap-register.md` covers all 7 MT5 capability categories.
7. `endpoint-snapshot.md` matches the routes registered in `app/main.py`.

## Next Steps

After Phase 0 is complete and signed off:

```
/speckit.plan   Phase 1 — Message Contract and Taxonomy
/speckit.tasks  Phase 1 — Message Contract and Taxonomy
/speckit.implement Phase 1 — Message Contract and Taxonomy
```
