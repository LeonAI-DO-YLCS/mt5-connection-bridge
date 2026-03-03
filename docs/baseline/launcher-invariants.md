# Launcher Invariants Checklist — MT5 Connection Bridge

> **Effective Date**: 2026-03-03
> **Checklist Version**: 1.0
> **Applies To**: All changes to `scripts/` directory across Phases 0–7

---

## 1. Invariant Registry

| ID     | Category             | Description                                                                              | Current Behavior                                                                                                                                                                        | Verification Method                                                                                                           |
| ------ | -------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| LI-001 | `script_name`        | `start_bridge.sh` name and location must not change                                      | Located at `scripts/start_bridge.sh`; launches uvicorn with configured host/port                                                                                                        | `ls scripts/start_bridge.sh` — must exist and be executable                                                                   |
| LI-002 | `script_name`        | `stop_bridge.sh` name and location must not change                                       | Located at `scripts/stop_bridge.sh`; kills processes on configured port                                                                                                                 | `ls scripts/stop_bridge.sh` — must exist and be executable                                                                    |
| LI-003 | `script_name`        | `restart_bridge.sh` name and location must not change                                    | Located at `scripts/restart_bridge.sh`; runs stop then start sequentially                                                                                                               | `ls scripts/restart_bridge.sh` — must exist and be executable                                                                 |
| LI-004 | `script_name`        | `smoke_bridge.sh` name and location must not change                                      | Located at `scripts/smoke_bridge.sh`; probes health endpoint                                                                                                                            | `ls scripts/smoke_bridge.sh` — must exist and be executable                                                                   |
| LI-005 | `script_name`        | `launch_bridge_dashboard.sh` name and location must not change                           | Located at `scripts/launch_bridge_dashboard.sh`; full-featured launcher with TUI                                                                                                        | `ls scripts/launch_bridge_dashboard.sh` — must exist and be executable                                                        |
| LI-006 | `script_name`        | `launch_bridge_windows.sh` name and location must not change                             | Located at `scripts/launch_bridge_windows.sh`; thin WSL→PowerShell wrapper                                                                                                              | `ls scripts/launch_bridge_windows.sh` — must exist and be executable                                                          |
| LI-007 | `invocation_pattern` | All scripts accept `MT5_BRIDGE_PORT` and `MT5_BRIDGE_API_KEY` from environment or `.env` | Scripts source `.env` at the top and use `MT5_BRIDGE_PORT` and `MT5_BRIDGE_API_KEY` as their primary configuration inputs                                                               | `grep -l 'MT5_BRIDGE_PORT\|MT5_BRIDGE_API_KEY' scripts/*.sh` — all operational scripts must match                             |
| LI-008 | `restart_policy`     | `launch_bridge_dashboard.sh` attempts exactly 1 auto-restart on unexpected exit          | On unexpected bridge exit (non-zero, non-signal), the launcher attempts one restart. If both fail → exits non-success. No infinite restart loop.                                        | Read `launch_bridge_dashboard.sh` restart logic; confirm `MAX_RETRIES=1` or equivalent                                        |
| LI-009 | `log_structure`      | Log bundles are written to `logs/bridge/launcher/<run-id>/` with 4 files                 | Each launcher run creates a directory with: `launcher.log`, `bridge.stdout.log`, `bridge.stderr.log`, `session.json`                                                                    | `ls logs/bridge/launcher/<latest-run-id>/` — confirm all 4 files present after a launcher run                                 |
| LI-010 | `log_structure`      | `session.json` contains required metadata fields                                         | Fields: `run_id`, `started_at_utc`, `ended_at_utc`, `exit_code`, `termination_reason`, `restart_attempted`, `restart_successful`                                                        | `cat logs/bridge/launcher/<run-id>/session.json \| python -m json.tool` — validate all required keys present                  |
| LI-011 | `smoke_test`         | `smoke_bridge.sh` probes `GET /health` and returns 0 on 200, non-zero on failure         | Uses `curl` to hit the health endpoint on configured port; exits 0 if HTTP 200, non-zero otherwise                                                                                      | Run `./scripts/smoke_bridge.sh && echo PASS \|\| echo FAIL` with bridge running                                               |
| LI-012 | `env_var`            | `LAUNCHER_PREFER_WINDOWS` controls WSL→Windows bridge dispatch (default `true`)          | When `true`, `launch_bridge_dashboard.sh` delegates to `launch_bridge_windows.sh` for the actual bridge process. When `false` or unset in some contexts, runs bridge directly in shell. | `grep 'LAUNCHER_PREFER_WINDOWS' scripts/launch_bridge_dashboard.sh` — confirm the variable is read and respected              |
| LI-013 | `invocation_pattern` | `test-fast.sh` and `test-full.sh` names and invocation patterns must not change          | `test-fast.sh` runs `pytest -x` (fast subset); `test-full.sh` runs `pytest` (full suite). Both exit with pytest's exit code.                                                            | `ls scripts/test-fast.sh scripts/test-full.sh` — must exist; `head -20 scripts/test-*.sh` — confirm pytest invocation pattern |

---

## 2. Review Gate Instructions

### For Code Reviewers

When reviewing any PR that touches files in the `scripts/` directory:

1. **Open this checklist**: Navigate to `docs/baseline/launcher-invariants.md` and review the Invariant Registry table above.

2. **Verify each invariant**: For every invariant in the table, confirm that the PR's changes do not violate the described behavior. Pay special attention to:
   - **LI-001 through LI-006**: File renames or relocations
   - **LI-007**: Removal or renaming of environment variable references
   - **LI-008**: Changes to restart loop count or logic
   - **LI-009 / LI-010**: Changes to log directory path or session.json fields
   - **LI-011**: Changes to smoke test endpoint or exit code semantics
   - **LI-013**: Changes to test script names or invocations

3. **If an invariant would be violated**: The PR **must** include a formal exception comment with:
   - The invariant ID being violated (e.g., `LI-008`)
   - The justification for the violation
   - The approved replacement behavior
   - Reference to the exception process (see §3)

4. **Block the PR** if an invariant is violated without a documented exception.

### Checklist Pass Template

Add this comment to the PR after verification:

```
✅ Launcher Invariants Review
- LI-001 through LI-013: All verified
- No invariants violated
- Reviewer: [name] | Date: [date]
```

---

## 3. Exception Process

If a proposed change must violate a launcher invariant:

1. **Open an issue** titled `Launcher Invariant Exception: LI-<ID>` with:
   - Which invariant is affected
   - Why the current behavior must change
   - What the new behavior will be
   - Impact assessment: what consumers or scripts will be affected
   - Migration plan: how to update dependent scripts or documentation

2. **Get approval** from at least one other team member (via issue comment).

3. **Update this document**: In the same PR that makes the change:
   - Update the `Current Behavior` column for the affected invariant
   - Add an "Exception History" entry at the bottom of this document:

   ```
   ## Exception History

   | Date | Invariant | Approved By | Change Summary |
   |------|-----------|-------------|----------------|
   | YYYY-MM-DD | LI-XXX | [name] | [brief description] |
   ```

4. **Do not remove invariants**. If a behavior is no longer relevant, update the description to reflect the new state rather than deleting the row.
