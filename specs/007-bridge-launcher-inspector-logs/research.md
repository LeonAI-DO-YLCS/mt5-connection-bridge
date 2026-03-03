# Research: Bridge Launcher Inspector Logging

**Branch**: `007-bridge-launcher-inspector-logs` | **Date**: 2026-03-02

## 1. Launch Process Model

**Decision**: Use a foreground launcher that starts the existing bridge runtime and exposes live output while persisting run-scoped logs.

**Rationale**:
- Foreground mode gives immediate operator visibility for inspector debugging.
- Preserving the existing runtime process model avoids architecture drift.
- Dual-stream persistence (stdout/stderr + lifecycle log) satisfies auditability and post-mortem analysis.

**Alternatives considered**:
- Background-only launcher: rejected because it weakens real-time inspection and delays failure detection.
- Separate dashboard process: rejected because the bridge already serves `/dashboard` and a second process adds avoidable complexity.

## 2. Crash Recovery Policy

**Decision**: Attempt exactly one automatic restart after unexpected runtime crash, then exit non-success if restart fails.

**Rationale**:
- Balances resilience and diagnosability.
- Prevents infinite restart loops that obscure root causes.
- Aligns with clarified feature requirement for deterministic failure outcomes.

**Alternatives considered**:
- No restart: rejected because it increases manual recovery burden.
- Infinite restart with backoff: rejected because it can hide persistent faults and produce noisy logs.

## 3. Authentication & Access Boundary

**Decision**: Allow network access by default for launcher sessions, requiring authenticated access for all operations with one shared operator credential.

**Rationale**:
- Supports cross-host operational use in MT5 bridge environments.
- Shared credential model fits current operational simplicity goals.
- Existing bridge authentication mechanisms can be preserved without introducing identity-management scope.

**Alternatives considered**:
- Localhost-only default: rejected due to operational constraints for remote consumers.
- Per-operator credentials: rejected for this feature scope because it introduces account lifecycle work not requested.

## 4. Failed Authentication Handling

**Decision**: Log all failed authentication attempts with request context; do not apply lockout or throttling in this feature.

**Rationale**:
- Matches accepted feature clarification and avoids operational lockout risks.
- Preserves traceability while keeping behavior predictable for automated clients.

**Alternatives considered**:
- Fixed lockout: rejected by requirement.
- Progressive delay/lockout: rejected by requirement.

## 5. Run-Scoped Log Retention

**Decision**: Keep run-scoped log bundles retrievable for 90 days before cleanup eligibility.

**Rationale**:
- Supports investigation windows for operational incidents and audits.
- Aligns with existing metrics retention horizon and clarified requirement.

**Alternatives considered**:
- 7-day retention: rejected as too short for incident lookback.
- 30-day retention: rejected because accepted requirement is 90 days.

## 6. Existing Script Compatibility

**Decision**: Keep `start_bridge.sh`, `stop_bridge.sh`, `restart_bridge.sh`, and `smoke_bridge.sh` behavior-stable; add launcher as an additive script.

**Rationale**:
- Avoids regression in established runbooks.
- Reduces rollout risk for existing operators.

**Alternatives considered**:
- Replace existing scripts with one launcher: rejected due to backward-compatibility risk.

## Resolved Clarifications

All technical-context unknowns are resolved. No outstanding `NEEDS CLARIFICATION` items remain for planning.
