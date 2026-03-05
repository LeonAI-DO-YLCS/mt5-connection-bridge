## Context — Phase 7: Native Parity Surface and Conformance

You are implementing **Phase 7 — Native Parity Surface and Conformance** for the **MT5 Connection Bridge** project.
Branch: `016-phase7-native-parity-surface-and-conformance`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/016-phase7-native-parity-surface-and-conformance/tasks.md` — your task list (execute ONLY the tasks listed below)
- `specs/016-phase7-native-parity-surface-and-conformance/plan.md` — architecture
- `specs/016-phase7-native-parity-surface-and-conformance/data-model.md` — GovernanceEntry, ParityCoverageEntry models
- `specs/016-phase7-native-parity-surface-and-conformance/research.md` — governance checklist (§5), capability inventory (§1)

### Your Tasks — Phase 6: US5 — Governance & Coverage Matrix

Execute ONLY these tasks from `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`:

- [ ] T032 [P] [US5] Create `GovernanceEntry` Pydantic model in `app/models/conformance.py` (append to existing file) per data-model.md
- [ ] T033 [P] [US5] Create `ParityCoverageEntry` Pydantic model in `app/models/conformance.py` (append to existing file) per data-model.md
- [ ] T034 [US5] Populate `config/governance-checklist.yaml` with governance entries for all 6 raw endpoints: `/mt5/raw/margin-check`, `/mt5/raw/profit-calc`, `/mt5/raw/market-book`, `/mt5/raw/terminal-info`, `/mt5/raw/account-info`, `/mt5/raw/last-error` — each with `safety_class`, `auth_required`, `logging_policy`, `readiness_gated`
- [ ] T035 [US5] Create `config/parity-coverage-matrix.yaml` with the 7 MT5 capability categories from research.md §1 — fill `implemented`, `safe_domain_endpoint`, `raw_endpoint`, `constraints`, `known_broker_variance`, `test_coverage` for each capability
- [ ] T036 [US5] Create a governance validation script at `scripts/validate_governance.py` that loads the YAML and validates all raw endpoints have complete governance entries — exit non-zero if any field is missing

### Rules

1. **Read first**: Read every file you are about to modify BEFORE making changes.
2. **Follow exactly**: Each task specifies the exact file, function, and behavior. Follow precisely.
3. **Scope control**: Do NOT modify files not mentioned in your tasks.
4. **Mark progress**: After completing each task, mark it as `[x]` in `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`.
5. **Commit convention**: Commit after each logical group with message format:
   `feat(016): T032–T036 governance checklist and parity coverage matrix`
6. **No speckit commands**: Speckit CLI is not available in this environment. Apply all changes manually.
7. **Preserve existing code**: Only ADD or MODIFY as specified — do not remove unrelated functionality.
8. **No placeholders**: Every task must produce working code, not TODO comments or stubs.
