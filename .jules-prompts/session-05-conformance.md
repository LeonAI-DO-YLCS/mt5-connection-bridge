## Context — Phase 7: Native Parity Surface and Conformance

You are implementing **Phase 7 — Native Parity Surface and Conformance** for the **MT5 Connection Bridge** project.
Branch: `016-phase7-native-parity-surface-and-conformance`

### Required Reading (READ BEFORE WRITING CODE)

Read these files in the repository for full context:

- `specs/016-phase7-native-parity-surface-and-conformance/tasks.md` — your task list (execute ONLY the tasks listed below)
- `specs/016-phase7-native-parity-surface-and-conformance/plan.md` — architecture, conformance module structure
- `specs/016-phase7-native-parity-surface-and-conformance/data-model.md` — ConformanceResult, ConformanceReport models
- `specs/016-phase7-native-parity-surface-and-conformance/contracts/api-contracts.md` — conformance CLI contract (invocation, JSON output, Markdown output)
- `specs/016-phase7-native-parity-surface-and-conformance/research.md` — conformance harness architecture (§3)

### Your Tasks — Phase 5: US4 — Conformance Harness

Execute ONLY these tasks from `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`:

- [ ] T020 [P] [US4] Create conformance CLI entry point at `app/conformance/__main__.py` — argparse with `--base-url`, `--api-key`, `--include-write-tests`, `--output-json`, `--output-md`
- [ ] T021 [P] [US4] Create conformance test runner at `app/conformance/runner.py` — orchestrates probe execution by category, collects `ConformanceResult` list, builds `ConformanceReport`
- [ ] T022 [P] [US4] Create connection probe at `app/conformance/probes/connection.py` — tests `/health`, `/diagnostics/runtime`, `/readiness`; returns list of `ConformanceResult`
- [ ] T023 [P] [US4] Create symbols probe at `app/conformance/probes/symbols.py` — tests `/broker-capabilities`, symbol resolution; returns `ConformanceResult` list
- [ ] T024 [P] [US4] Create pricing probe at `app/conformance/probes/pricing.py` — tests `/tick/{symbol}`, price data availability; returns `ConformanceResult` list
- [ ] T025 [P] [US4] Create calculations probe at `app/conformance/probes/calculations.py` — tests `/margin-check`, `/profit-calc`, `/mt5/raw/margin-check`, `/mt5/raw/profit-calc`; returns `ConformanceResult` list
- [ ] T026 [P] [US4] Create market-book probe at `app/conformance/probes/market_book.py` — tests `/mt5/raw/market-book`; handles `not_supported` gracefully; returns `ConformanceResult` list
- [ ] T027 [P] [US4] Create write-tests probe at `app/conformance/probes/write_tests.py` — opt-in only (skipped unless `--include-write-tests`); tests order send + immediate cancel on test account; returns `ConformanceResult` list
- [ ] T028 [US4] Create report generator at `app/conformance/reporter.py` — takes `ConformanceReport`, writes JSON to stdout or file, generates Markdown summary with pass/warn/fail table, recommendation section per contracts/api-contracts.md §Conformance CLI
- [ ] T029 [US4] Create `app/conformance/probes/__init__.py` that exports all probe modules
- [ ] T030 [US4] Wire runner to discover and execute all probes, compute summary stats, generate recommendation based on pass/warn/fail ratios, output via reporter
- [ ] T031 [US4] Write integration test for conformance harness in `tests/integration/test_conformance.py` — mock bridge API responses, verify report structure matches `ConformanceReport` model, verify JSON and Markdown output

### Rules

1. **Read first**: Read every file you are about to modify BEFORE making changes.
2. **Follow exactly**: Each task specifies the exact file, function, and behavior. Follow precisely.
3. **Scope control**: Do NOT modify files not mentioned in your tasks.
4. **Mark progress**: After completing each task, mark it as `[x]` in `specs/016-phase7-native-parity-surface-and-conformance/tasks.md`.
5. **Commit convention**: Commit after each logical group with message format:
   `feat(016): T020–T031 conformance harness CLI, probes, and reporter`
6. **No speckit commands**: Speckit CLI is not available in this environment. Apply all changes manually.
7. **Preserve existing code**: Only ADD or MODIFY as specified — do not remove unrelated functionality.
8. **No placeholders**: Every task must produce working code, not TODO comments or stubs.
