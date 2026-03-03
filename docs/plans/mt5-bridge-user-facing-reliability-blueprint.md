# MT5 Bridge User-Facing Reliability Blueprint

> Status: Active planning artifact  
> Scope: `mt5-connection-bridge` (bridge API, MT5 worker integration, dashboard UX, launcher/runtime operations)  
> Constraint: Additive changes only; preserve architecture and operator workflows  
> Date: 2026-03-03

This document is now the entrypoint/index for the phased blueprint set.

## Objective

Provide a comprehensive and implementation-ready roadmap to make the bridge behave as a user-comprehensible, MT5-native operational system:

1. All errors, warnings, status, advice, and safety prompts become human-readable and traceable.
2. Prerequisites and runtime constraints are visible before actions are attempted.
3. MT5 request compatibility edge cases (including invalid close-order comments) are handled deterministically.
4. Launcher and operator workflow are enhanced without changing current usage patterns.
5. The bridge evolves toward broad MT5 parity with a safe API plus advanced expert surface.

## Phased Blueprint Set

All details are split into phase files under `docs/plans/phased-user-facing-reliability/`.

1. [master-blueprint.md](./phased-user-facing-reliability/master-blueprint.md)
2. [0-baseline-and-constraints.md](./phased-user-facing-reliability/0-baseline-and-constraints.md)
3. [1-message-contract-and-taxonomy.md](./phased-user-facing-reliability/1-message-contract-and-taxonomy.md)
4. [2-readiness-and-prerequisites.md](./phased-user-facing-reliability/2-readiness-and-prerequisites.md)
5. [3-execution-hardening-and-compatibility.md](./phased-user-facing-reliability/3-execution-hardening-and-compatibility.md)
6. [4-close-comment-compatibility.md](./phased-user-facing-reliability/4-close-comment-compatibility.md)
7. [5-launcher-runtime-hardening.md](./phased-user-facing-reliability/5-launcher-runtime-hardening.md)
8. [6-dashboard-operator-experience.md](./phased-user-facing-reliability/6-dashboard-operator-experience.md)
9. [7-native-parity-surface-and-conformance.md](./phased-user-facing-reliability/7-native-parity-surface-and-conformance.md)

## Non-Negotiable Guardrails

1. Existing operator entry points remain intact:
   - `./scripts/start_bridge.sh --background`
   - `./scripts/stop_bridge.sh`
   - `./scripts/restart_bridge.sh`
   - `./scripts/smoke_bridge.sh`
   - `./scripts/launch_bridge_dashboard.sh`
   - `./scripts/launch_bridge_windows.sh`
2. Launcher workflow remains the same:
   - same one-command start behavior
   - same restart semantics (single automatic restart attempt)
   - same run-bundle artifact model under `logs/bridge/launcher/<run-id>/`
3. Enhancements to scripts/launcher are allowed only when additive and backward-compatible.
4. Existing bridge API contracts remain backward-compatible during migration windows.

## Why This Was Split

The previous monolithic reliability blueprint became too dense for incremental implementation and review.  
This phased structure gives:

- clear dependency ordering
- smaller implementation units
- explicit acceptance gates per phase
- safer rollout and rollback planning
