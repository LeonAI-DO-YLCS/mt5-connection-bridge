# Data Model: Bridge Launcher Inspector Logging

**Branch**: `007-bridge-launcher-inspector-logs` | **Date**: 2026-03-02

## 1. LaunchSession

Represents one invocation of the launcher command.

| Field | Type | Required | Validation | Description |
|---|---|---|---|---|
| `run_id` | string | Yes | Unique per launch attempt | Session identifier used for log bundle pathing |
| `started_at_utc` | datetime string | Yes | ISO 8601 UTC | Session start timestamp |
| `ended_at_utc` | datetime string | No | ISO 8601 UTC when present | Session end timestamp |
| `port` | integer | Yes | 1-65535 | Runtime bind port used for bridge endpoint |
| `log_level` | string | Yes | Allowed runtime levels | Active runtime verbosity |
| `restart_attempted` | boolean | Yes | True/False | Indicates whether auto-restart was attempted |
| `restart_successful` | boolean | No | Present only if restart attempted | Outcome of restart attempt |
| `exit_code` | integer | Yes | Process exit code semantics | Final launcher result |
| `termination_reason` | string | Yes | Non-empty | Normal shutdown, startup failure, crash-after-restart, interrupt, etc. |

## 2. RunLogBundle

Represents persisted artifacts for one LaunchSession.

| Field | Type | Required | Validation | Description |
|---|---|---|---|---|
| `run_id` | string | Yes | Must match LaunchSession `run_id` | Correlation key |
| `bundle_root_path` | string | Yes | Existing directory path | Root artifact location |
| `launcher_log_path` | string | Yes | Existing file path | Lifecycle and orchestration events |
| `stdout_log_path` | string | Yes | Existing file path | Runtime standard output stream |
| `stderr_log_path` | string | Yes | Existing file path | Runtime error stream |
| `retention_until_utc` | datetime string | Yes | `started_at_utc + 90 days` | Earliest cleanup eligibility point |

## 3. RuntimeEvent

Represents a terminal-visible and persisted operational message.

| Field | Type | Required | Validation | Description |
|---|---|---|---|---|
| `event_time_utc` | datetime string | Yes | ISO 8601 UTC | Event timestamp |
| `severity` | enum | Yes | info/warn/error | Event severity |
| `source` | enum | Yes | launcher/runtime/auth | Event producer |
| `message` | string | Yes | Non-empty | Human-readable content |
| `run_id` | string | Yes | Must resolve to LaunchSession | Correlation to session |

## 4. AuthFailureEvent

Represents a failed authenticated request during an active launcher session.

| Field | Type | Required | Validation | Description |
|---|---|---|---|---|
| `event_time_utc` | datetime string | Yes | ISO 8601 UTC | Failure timestamp |
| `run_id` | string | Yes | Must resolve to LaunchSession | Session linkage |
| `request_path` | string | Yes | Non-empty | Request path attempted |
| `remote_address` | string | No | IP/host text if available | Caller context |
| `failure_reason` | string | Yes | Non-empty | Auth failure category |
| `error_code` | string | No | Machine-readable code if available | Log/search key |

## 5. Entity Relationships

- `LaunchSession` 1:1 `RunLogBundle`
- `LaunchSession` 1:N `RuntimeEvent`
- `LaunchSession` 1:N `AuthFailureEvent`

## 6. State Transitions

### LaunchSession State Machine

1. `initialized` -> `starting`
2. `starting` -> `running` (successful startup)
3. `starting` -> `failed_startup` (startup error)
4. `running` -> `restarting` (unexpected crash)
5. `restarting` -> `running` (restart success)
6. `restarting` -> `failed_after_restart` (restart failure)
7. `running` -> `terminated` (operator interrupt or normal stop)

### Retention Lifecycle

1. `active_bundle` (creation through 90-day window)
2. `eligible_for_cleanup` (after `retention_until_utc`)

## 7. Validation Rules Derived from Requirements

- Every launch attempt must create exactly one `LaunchSession` and one `RunLogBundle`.
- `RunLogBundle` must contain all three log channels (`launcher`, `stdout`, `stderr`).
- Crash recovery permits at most one restart attempt per launch session.
- All auth failures must produce an `AuthFailureEvent` record.
- No lockout/throttle state is modeled for auth failures in this feature.
