# Master Blueprint: User-Facing Reliability and MT5-Native Operations

> Status: Implementation planning  
> Date: 2026-03-03  
> Scope: Backend bridge, MT5 worker behavior, dashboard UX, launcher/runtime operations  
> Out of scope: Replacing architecture, changing operator command workflow, React/frontend monorepo changes

---

## 1. Intent

Build a production-grade reliability layer so operators can trust the bridge under real broker variance, while moving toward MT5-native breadth:

1. Human-readable and actionable error/warning/status system.
2. Single prerequisite/readiness contract for all trade operations.
3. Deterministic request compatibility behavior (including comment argument failures).
4. Strict but backward-compatible operational hardening.
5. Progressive MT5 parity via dual API surface:
   - safe domain API
   - advanced raw MT5 capability API

---

## 2. Grounded Current-State Findings

### 2.1 Confirmed technical-error leak to users

- Dashboard API helper currently throws raw JSON payload text.
- Dashboard tabs still rely on direct `alert/confirm/prompt` patterns for operational feedback.
- Backend emits mixed response forms (`detail` string/list/object, `success=false`, and raw error tuples).

### 2.2 Confirmed runtime/operational incidents

Observed in runtime logs:

- `order_send returned None: (-2, 'Invalid "comment" argument')` on close flow.
- `retcode=10030 Unsupported filling mode` events in past runs.
- startup/runtime blockers:
  - missing `MetaTrader5` module
  - port already bound (`10048`)
  - invalid launcher log-level formatting in earlier runs.

### 2.3 Constraint baseline

- Worker queue architecture is core and must remain.
- Runtime state persistence and execution policy controls are already established.
- Launcher scripts are operationally mature and should be improved in place, not replaced.

---

## 3. Decision Matrices

### 3.1 API surface strategy for MT5 parity

| Option | Description | Pros | Cons | Recommendation |
|---|---|---|---|---|
| A | Only safe bridge endpoints | Low complexity | Cannot approach full MT5 parity | No |
| B | Only raw MT5 mirrored endpoints | Max parity | Unsafe and hard for normal users | No |
| C | Dual surface: safe domain API + expert raw namespace | Best balance of safety and parity | Requires governance and docs | **Recommended** |

### 3.2 Error-system migration strategy

| Option | Description | Pros | Cons | Recommendation |
|---|---|---|---|---|
| A | Hard break to new schema | Clean | High regression blast radius | No |
| B | Long-term mixed ad hoc | Easy now | Permanent inconsistency | No |
| C | Canonical envelope + compatibility bridge | Safe rollout | Temporary duality | **Recommended** |

### 3.3 Launcher policy strategy

| Option | Description | Pros | Cons | Recommendation |
|---|---|---|---|---|
| A | Replace launcher with new tool | Could simplify code | Breaks existing operator muscle memory | No |
| B | Keep launcher unchanged forever | Zero risk now | Leaves known diagnostics gaps | No |
| C | Keep same commands/workflow, add guardrails and diagnostics | No workflow break, better reliability | Requires disciplined patching | **Recommended** |

---

## 4. Phase Roadmap

| Phase | File | Goal | Dependency |
|---|---|---|---|
| 0 | [0-baseline-and-constraints.md](./0-baseline-and-constraints.md) | Baseline inventory, invariants, migration contract | none |
| 1 | [1-message-contract-and-taxonomy.md](./1-message-contract-and-taxonomy.md) | Canonical user-facing message system | 0 |
| 2 | [2-readiness-and-prerequisites.md](./2-readiness-and-prerequisites.md) | Unified readiness/preflight contract | 0,1 |
| 3 | [3-execution-hardening-and-compatibility.md](./3-execution-hardening-and-compatibility.md) | Deterministic operation behavior under MT5 variance | 0,1,2 |
| 4 | [4-close-comment-compatibility.md](./4-close-comment-compatibility.md) | Dedicated close-comment compatibility hardening | 3 |
| 5 | [5-launcher-runtime-hardening.md](./5-launcher-runtime-hardening.md) | Runtime and launcher safety upgrades with same UX | 0 |
| 6 | [6-dashboard-operator-experience.md](./6-dashboard-operator-experience.md) | Operator UX modernization and supportability | 1,2,3,4 |
| 7 | [7-native-parity-surface-and-conformance.md](./7-native-parity-surface-and-conformance.md) | MT5 parity expansion and conformance harness | 0..6 |

---

## 5. Global Acceptance Gates

1. Raw technical exceptions/tuples are never primary user-facing copy.
2. Every actionable failure includes semantic code and tracking ID.
3. All trade operations pass a readiness/preflight contract.
4. Launcher commands and basic command-line ergonomics remain unchanged.
5. Broker variance outcomes are deterministic and documented.
6. Rollout is feature-flagged and reversible per phase.

---

## 6. Non-Negotiable Launcher Invariants

Must remain true after all changes:

1. Same entrypoints and defaults:
   - `start_bridge.sh`, `stop_bridge.sh`, `restart_bridge.sh`, `smoke_bridge.sh`
   - `launch_bridge_dashboard.sh`, `launch_bridge_windows.sh`
2. Same one-command ease of usage.
3. Same log bundle model and retention semantics.
4. Same auto-restart policy behavior (single automatic restart attempt).
5. Any new checks are additive and non-breaking (warning or preflight hints, not abrupt behavior shift by default).

---

## 7. Delivery Order Recommendation

1. Phases 0 and 1 first to establish language and compatibility scaffolding.
2. Phase 2 next to block avoidable runtime failures.
3. Phases 3 and 4 to close high-risk trading failure loops.
4. Phase 5 in parallel if runtime incidents are frequent.
5. Phase 6 once backend contract is stable.
6. Phase 7 only after reliability baseline is proven in production-like runs.

