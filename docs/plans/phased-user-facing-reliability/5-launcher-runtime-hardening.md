# Phase 5: Launcher and Runtime Hardening

> Objective: Improve launch/runtime reliability and diagnostics while preserving current operator workflow and command ergonomics.

---

## 1. Explicit Workflow Preservation Rule

This phase is constrained by a strict policy:

1. Do not replace launcher scripts.
2. Do not change primary command names or normal invocation patterns.
3. Do not remove current restart/artifact behavior.
4. Additions must be backward-compatible and easy to adopt.

---

## 2. Current Runtime/Launcher Risk Signals

Known observed incidents:

1. Invalid log-level format mismatches in prior launcher sessions.
2. Port binding conflicts from stale listeners.
3. Missing `MetaTrader5` runtime dependency in wrong environment.
4. Restart attempt failures ending sessions non-success.

Additional observed operational friction:

1. Operators discover bootstrap/runtime issues late instead of in early preflight context.
2. Root cause often requires opening multiple logs when a concise diagnostic summary would suffice.

---

## 3. Decision Matrix: How to Improve Without Workflow Break

| Option | Description | Pros | Cons | Recommendation |
|---|---|---|---|---|
| A | Replace launcher system | Potentially cleaner code | Breaks operator habits | No |
| B | No changes | Zero risk now | Leaves recurring incidents unresolved | No |
| C | Additive preflight/diagnostic hardening in current scripts | Preserves workflow and improves reliability | Requires careful patching | **Recommended** |

---

## 4. Allowed Improvements

### 4.1 Additive preflight checks

1. Validate effective runtime configuration before launch.
2. Emit explicit warnings for likely operator mistakes.
3. Preserve launch even when warnings exist (unless critical blockers).

Recommended preflight checks:

1. effective port availability and listener ownership summary
2. Python/runtime dependency presence summary
3. environment key sanity summary (non-secret, presence-only)
4. normalized log-level preview before process spawn.

### 4.2 Structured error guidance

Map runtime startup failures to user-readable diagnostics:

- dependency missing
- port conflict
- environment mismatch
- auth misconfiguration

And include exact next-step hints:

1. which command to rerun
2. which file to inspect first
3. which compatibility flag may help for known scenarios.

### 4.3 Better incident linkage

1. Correlate launcher run ID with API tracking IDs.
2. Expose quick “where to look” hints in dashboard status.

### 4.4 Safety guardrails

1. Keep existing stop/start/restart flow.
2. Keep current `smoke_bridge.sh` step in standard procedure.
3. Add optional health gate summaries, not mandatory new command flows.

### 4.5 Dashboard-runtime linkage

Additive dashboard enhancements allowed:

1. show last launcher run ID and termination reason snapshot
2. expose quick links/hints to current run bundle location
3. preserve existing tabs and navigation behavior.

---

## 5. Non-Breaking Guarantee Matrix

| Concern | Must remain unchanged | Allowed enhancements |
|---|---|---|
| Command entrypoints | script names and basic invocation | optional flags, better logs |
| Restart behavior | single automatic restart attempt policy | clearer restart diagnostics |
| Artifact layout | run bundle structure under `logs/bridge/launcher/<run-id>/` | extra metadata fields |
| Smoke flow | `stop -> start -> smoke` procedure | richer smoke output messaging |
| WSL Windows wrapper usage | `launch_bridge_windows.sh` path | improved bootstrap hints |

---

## 6. Backward-Compatibility Tests for Scripts

Required validation before release:

1. Existing documented commands run unchanged.
2. Existing environment variables remain supported.
3. Log bundle files remain in same location/shape.
4. Existing CI or operator scripts do not need rewrites.

---

## 7. Exit Criteria

1. Startup failure causes are clearly reported in plain language.
2. Workflow remains one-command friendly.
3. No regression in script ergonomics or documented runbook procedure.
