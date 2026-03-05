## Context — Phase 7: Native Parity Surface and Conformance

You are implementing **Phase 7 — Native Parity Surface and Conformance** for the **MT5 Connection Bridge** project.
Branch: `016-phase7-native-parity-surface-and-conformance`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/016-phase7-native-parity-surface-and-conformance/tasks.md` — your task list (execute ONLY the tasks listed below)
- `specs/016-phase7-native-parity-surface-and-conformance/plan.md` — architecture, tech stack, project structure
- `specs/016-phase7-native-parity-surface-and-conformance/data-model.md` — entity schemas and relationships
- `specs/016-phase7-native-parity-surface-and-conformance/contracts/api-contracts.md` — API contracts
- `specs/016-phase7-native-parity-surface-and-conformance/research.md` — technical decisions and constraints
- `app/config.py` — existing Settings class (you will modify this)
- `app/models/` — existing model patterns

### Your Tasks — Phase 1: Setup (Shared Infrastructure)

Execute ONLY these tasks from `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`:

- [ ] T001 Create `app/conformance/` directory with empty `__init__.py` at `app/conformance/__init__.py`
- [ ] T002 [P] Create `config/` directory and empty `config/governance-checklist.yaml` scaffold (YAML with top-level `endpoints: {}` key)
- [ ] T003 [P] Create `config/compatibility-profiles.yaml` with the three named profiles (`strict_safe`, `balanced`, `max_compat`) and their four dimensions per research.md §4 profile matrix
- [ ] T004 [P] Create `CompatibilityProfile` Pydantic model in `app/models/compatibility.py` per data-model.md (fields: `name`, `retry_aggressiveness`, `optional_field_handling`, `gating_strictness`, `warning_verbosity`)
- [ ] T005 [P] Create `ConformanceResult` and `ConformanceReport` Pydantic models in `app/models/conformance.py` per data-model.md
- [ ] T006 Add `COMPATIBILITY_PROFILE` setting to `app/config.py` (`str`, default `"strict_safe"`, alias `COMPATIBILITY_PROFILE`). Add helper `get_compatibility_profile()` that loads the YAML and returns the matching `CompatibilityProfile` instance.

### Rules

1. **Read first**: Read every file you are about to modify BEFORE making changes.
2. **Follow exactly**: Each task specifies the exact file, function, and behavior. Follow precisely.
3. **Scope control**: Do NOT modify files not mentioned in your tasks.
4. **Mark progress**: After completing each task, mark it as `[x]` in `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`.
5. **Commit convention**: Commit after each logical group with message format:
   `feat(016): T001–T006 Phase 1 setup — models, configs, directories`
6. **No speckit commands**: Speckit CLI is not available in this environment. Apply all changes manually.
7. **Preserve existing code**: Only ADD or MODIFY as specified — do not remove unrelated functionality.
8. **No placeholders**: Every task must produce working code, not TODO comments or stubs.
