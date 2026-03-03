# Baseline Documents — MT5 Connection Bridge

> **Established**: 2026-03-03 | **Phase**: 0 — Baseline and Constraints

This directory contains the seven foundational reference documents that establish the shared vocabulary, contracts, and constraints for the phased user-facing reliability rollout (Phases 0–7).

**No runtime code changes are made by these documents.** They are agreements and inventories that all subsequent phases reference.

---

## Document Index

| Document                                                 | Purpose                                                                                                                                                         | Key Consumers                                                                  |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| [**endpoint-snapshot.md**](./endpoint-snapshot.md)       | Complete inventory of all 28 endpoints and 9 operational scripts as of 2026-03-03. The baseline "do not remove" list.                                           | All phases — cross-reference target                                            |
| [**glossary.md**](./glossary.md)                         | Shared terminology: 6 core terms (`error`, `warning`, `status`, `advice`, `blocker`, `recovery`) + 4-level severity scale (`critical`, `high`, `medium`, `low`) | Phase 1+ — event categorization                                                |
| [**tracking-id-policy.md**](./tracking-id-policy.md)     | Canonical tracking ID format (`brg-<timestamp>-<hex4>`), generation rules, propagation path, and 60-second log correlation guide                                | Phase 1 (message contract), Phase 3 (hardening), Phase 6 (dashboard)           |
| [**error-code-namespace.md**](./error-code-namespace.md) | Stable error-code registry (10 initial codes), naming conventions (`DOMAIN_CONDITION`), and governance rules for adding/deprecating codes                       | Phase 1 (canonical codes), Phase 3 (new error paths), Phase 4 (comment errors) |
| [**compatibility-pledge.md**](./compatibility-pledge.md) | Per-endpoint stability commitments: `frozen`, `evolving`, or `migrating` — with legacy support window timeline                                                  | All phases — code review gate for endpoint changes                             |
| [**launcher-invariants.md**](./launcher-invariants.md)   | 13 frozen launcher behaviors (script names, restart policy, log structure, env vars) — mandatory code review checklist for `scripts/` changes                   | Phase 5 (launcher hardening) — primary gate document                           |
| [**parity-gap-register.md**](./parity-gap-register.md)   | MT5 Python API coverage matrix: 33 functions across 7 categories, with 52% full / 6% partial / 42% none coverage. Includes top-3 gap priorities.                | Phase 7 (native parity) — scoping and prioritization                           |

---

## How to Use These Documents

- **Before changing an endpoint**: Check [compatibility-pledge.md](./compatibility-pledge.md) for its stability level
- **Before adding an error code**: Check [error-code-namespace.md](./error-code-namespace.md) for collisions
- **Before categorizing a new event**: Read [glossary.md](./glossary.md) for the correct term and severity
- **Before changing a script**: Read [launcher-invariants.md](./launcher-invariants.md) and follow the review gate
- **Before scoping Phase 7 work**: Read [parity-gap-register.md](./parity-gap-register.md) for gap priorities

---

## Maintenance

These documents are living references. Update them when:

1. A new phase introduces error codes → update `error-code-namespace.md`
2. A new endpoint is added → update `endpoint-snapshot.md` and `compatibility-pledge.md`
3. A parity gap is closed → update `parity-gap-register.md`
4. A launcher invariant exception is approved → update `launcher-invariants.md`
