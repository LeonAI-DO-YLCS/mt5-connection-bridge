## Context — Phase 7: Native Parity Surface and Conformance

You are implementing **Phase 7 — Native Parity Surface and Conformance** for the **MT5 Connection Bridge** project.
Branch: `016-phase7-native-parity-surface-and-conformance`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/016-phase7-native-parity-surface-and-conformance/tasks.md` — your task list (execute ONLY the tasks listed below)
- `specs/016-phase7-native-parity-surface-and-conformance/plan.md` — architecture, tech stack, project structure
- `specs/016-phase7-native-parity-surface-and-conformance/data-model.md` — CompatibilityProfile model
- `specs/016-phase7-native-parity-surface-and-conformance/contracts/api-contracts.md` — compatibility profile contract (runtime exposure, audit log)
- `specs/016-phase7-native-parity-surface-and-conformance/research.md` — compatibility profiles design (§4)
- `app/config.py` — existing Settings class and get_settings()
- `app/routes/diagnostics.py` — existing diagnostics route

### Your Tasks — Phase 4: US3 — Compatibility Profiles

Execute ONLY these tasks from `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`:

- [ ] T017 [US3] Modify `app/routes/diagnostics.py` to include `compatibility_profile` object in the `/diagnostics/runtime` response — read from `get_compatibility_profile()` helper in config
- [ ] T018 [US3] Implement profile-change audit logging in `app/config.py`: when `get_compatibility_profile()` detects a different profile than last loaded, emit a structured log entry `{ event: "compatibility_profile_changed", old_profile: "...", new_profile: "...", timestamp: "..." }`
- [ ] T019 [US3] Write unit tests for compatibility profiles in `tests/unit/test_compatibility.py` — test profile loading from YAML, default profile, invalid profile handling, diagnostics response shape, audit log emission

### Rules

1. **Read first**: Read every file you are about to modify BEFORE making changes.
2. **Follow exactly**: Each task specifies the exact file, function, and behavior. Follow precisely.
3. **Scope control**: Do NOT modify files not mentioned in your tasks.
4. **Mark progress**: After completing each task, mark it as `[x]` in `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`.
5. **Commit convention**: Commit after each logical group with message format:
   `feat(016): T017–T019 compatibility profiles with runtime diagnostics`
6. **No speckit commands**: Speckit CLI is not available in this environment. Apply all changes manually.
7. **Preserve existing code**: Only ADD or MODIFY as specified — do not remove unrelated functionality.
8. **No placeholders**: Every task must produce working code, not TODO comments or stubs.
