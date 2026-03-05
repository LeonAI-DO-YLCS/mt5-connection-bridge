## Context — Phase 7: Native Parity Surface and Conformance

You are implementing **Phase 7 — Native Parity Surface and Conformance** for the **MT5 Connection Bridge** project.
Branch: `016-phase7-native-parity-surface-and-conformance`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/016-phase7-native-parity-surface-and-conformance/tasks.md` — your task list (execute ONLY the tasks listed below)
- `specs/016-phase7-native-parity-surface-and-conformance/plan.md` — architecture, full project structure
- `specs/016-phase7-native-parity-surface-and-conformance/quickstart.md` — quick test guide to update
- All `app/routes/*.py` files — verify registration
- All `app/models/*.py` files — verify docstrings

### Your Tasks — Phase 7: Polish & Cross-Cutting Concerns

Execute ONLY these tasks from `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`:

- [ ] T037 Update `specs/016-phase7-native-parity-surface-and-conformance/quickstart.md` with actual CLI commands for all new endpoints and conformance harness
- [ ] T038 Verify no existing safe domain endpoints are affected — run full `pytest` suite and confirm all prior tests pass
- [ ] T039 Run governance validation script: `python scripts/validate_governance.py`
- [ ] T040 Run conformance suite dry-run (if MT5 available): `python -m app.conformance --base-url http://localhost:8001 --api-key test --output-json /tmp/conformance.json`
- [ ] T041 Code cleanup — ensure all new files have module docstrings, type hints, and follow project conventions

### Rules

1. **Read first**: Read every file you are about to modify BEFORE making changes.
2. **Follow exactly**: Each task specifies the exact file, function, and behavior. Follow precisely.
3. **Scope control**: Do NOT modify files not mentioned in your tasks.
4. **Mark progress**: After completing each task, mark it as `[x]` in `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`.
5. **Commit convention**: Commit after each logical group with message format:
   `feat(016): T037–T041 Phase 7 polish, quickstart, and validation`
6. **No speckit commands**: Speckit CLI is not available in this environment. Apply all changes manually.
7. **Preserve existing code**: Only ADD or MODIFY as specified — do not remove unrelated functionality.
8. **No placeholders**: Every task must produce working code, not TODO comments or stubs.
