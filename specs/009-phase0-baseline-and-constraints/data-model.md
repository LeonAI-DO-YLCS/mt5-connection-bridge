# Data Model: Phase 0 — Baseline and Constraints

**Branch**: `009-phase0-baseline-and-constraints`
**Date**: 2026-03-03
**Source**: [spec.md](./spec.md) key entities, grounded by [research.md](./research.md)

---

## Entity Definitions

Phase 0 entities are reference documents, not runtime data structures. Each entity below defines the structure and fields that the corresponding deliverable markdown document must contain.

---

### 1. TerminologyGlossary

The shared vocabulary mapping message-system terms to precise definitions.

| Field                 | Type   | Description                                                                              |
| --------------------- | ------ | ---------------------------------------------------------------------------------------- |
| `term`                | string | The canonical term (e.g., `error`, `warning`, `status`, `advice`, `blocker`, `recovery`) |
| `definition`          | text   | Precise meaning in the context of this bridge's user-facing messaging                    |
| `example_trigger`     | text   | A concrete scenario that would produce this message type                                 |
| `dashboard_treatment` | text   | How this term renders on the dashboard (color, icon concept)                             |

**Severity Scale** (embedded sub-entity):

| Field             | Type | Description                                   |
| ----------------- | ---- | --------------------------------------------- |
| `level`           | enum | `low`, `medium`, `high`, `critical`           |
| `criteria`        | text | When this level applies                       |
| `action_required` | text | What the operator must do                     |
| `example`         | text | A concrete example from the existing codebase |

---

### 2. TrackingIDPolicy

Definition of the unique incident identity format and propagation path.

| Field                    | Type   | Description                                                         |
| ------------------------ | ------ | ------------------------------------------------------------------- |
| `format`                 | string | Pattern: `brg-<YYYYMMDDTHHMMSS>-<hex4>`                             |
| `generation_strategy`    | text   | How the bridge generates the ID (UTC timestamp + 4-char random hex) |
| `uniqueness_scope`       | text   | Per runtime session (not globally unique across restarts)           |
| `propagation_path`       | text   | Backend structured log → response header → dashboard display        |
| `log_correlation_method` | text   | How an operator finds the log entry: grep by tracking_id in JSONL   |
| `format_constraints`     | text   | Must be human-readable, screenshot-safe (≤ 30 chars), and URL-safe  |

---

### 3. ErrorCodeNamespace

The enumerated, stable list of semantic error codes with governance rules.

| Field              | Type   | Description                                                                                |
| ------------------ | ------ | ------------------------------------------------------------------------------------------ |
| `domain_prefix`    | string | One of: `VALIDATION_`, `MT5_`, `EXECUTION_`, `WORKER_`, `SYMBOL_`, `REQUEST_`, `INTERNAL_` |
| `code_name`        | string | Full code (e.g., `MT5_DISCONNECTED`)                                                       |
| `description`      | text   | What this code means                                                                       |
| `http_status_map`  | int    | Typical HTTP status code associated with this error                                        |
| `severity`         | enum   | `low`, `medium`, `high`, `critical`                                                        |
| `phase_introduced` | string | Phase in which this code was added                                                         |

**Governance Rules** (embedded):

| Field                  | Type | Description                                                                   |
| ---------------------- | ---- | ----------------------------------------------------------------------------- |
| `naming_convention`    | text | `<DOMAIN>_<CONDITION>` in uppercase with underscores                          |
| `collision_prevention` | text | New codes must be checked against the existing namespace list before adoption |
| `deprecation_process`  | text | Codes are never removed; they can be deprecated with a successor noted        |

---

### 4. CompatibilityPledge

Per-phase statement of which behaviors are frozen.

| Field                  | Type   | Description                                                                                                 |
| ---------------------- | ------ | ----------------------------------------------------------------------------------------------------------- |
| `endpoint_family`      | string | The endpoint group (e.g., `/health`, `/execute`, `/close-position`)                                         |
| `stability_level`      | enum   | `frozen` (no changes), `evolving` (may add fields), `migrating` (breaking change with compatibility window) |
| `phase_affected`       | string | In which phase(s) this endpoint may change                                                                  |
| `compatibility_window` | text   | How long legacy shapes are supported alongside new ones                                                     |
| `migration_notes`      | text   | What will change and how consumers should adapt                                                             |

---

### 5. LauncherInvariantsChecklist

Explicit list of launcher behaviors that must survive all changes.

| Field                 | Type   | Description                                                                                     |
| --------------------- | ------ | ----------------------------------------------------------------------------------------------- |
| `invariant_id`        | string | Short identifier (e.g., `LI-001`)                                                               |
| `category`            | enum   | `script_name`, `invocation_pattern`, `restart_policy`, `log_structure`, `smoke_test`, `env_var` |
| `description`         | text   | What must not change                                                                            |
| `current_behavior`    | text   | Current observed behavior (as of snapshot date)                                                 |
| `verification_method` | text   | How to verify compliance in code review                                                         |

---

### 6. ParityGapRegister

Structured inventory of MT5 Python API capabilities vs. current bridge coverage.

| Field                       | Type   | Description                                                              |
| --------------------------- | ------ | ------------------------------------------------------------------------ |
| `category`                  | string | One of the 7 MT5 capability categories (see research.md §6.5)            |
| `mt5_function`              | string | Specific MT5 Python library function (e.g., `mt5.order_check`)           |
| `bridge_coverage`           | enum   | `full`, `partial`, `none`                                                |
| `coverage_notes`            | text   | What is covered, what is missing                                         |
| `constraints`               | text   | Known limitations (e.g., single-flight queue limits throughput)          |
| `known_broker_variance`     | text   | Broker-specific differences observed or expected                         |
| `fallback_behavior`         | text   | What happens if this function is unavailable                             |
| `test_coverage`             | enum   | `automated`, `manual`, `none`                                            |
| `operator_readiness_impact` | text   | How this gap affects the dashboard operator's ability to diagnose issues |

---

### 7. EndpointSnapshot

Baseline inventory of all active endpoint families and operational scripts.

| Field            | Type    | Description                        |
| ---------------- | ------- | ---------------------------------- |
| `endpoint_path`  | string  | URL path (e.g., `/close-position`) |
| `http_method`    | string  | HTTP verb                          |
| `module`         | string  | Source file in `app/routes/`       |
| `purpose`        | text    | What this endpoint does            |
| `response_shape` | text    | Current response format key fields |
| `auth_required`  | boolean | Whether the route requires API key |

**Scripts sub-table**:

| Field              | Type   | Description                                         |
| ------------------ | ------ | --------------------------------------------------- |
| `script_name`      | string | Filename relative to `scripts/`                     |
| `purpose`          | text   | What this script does                               |
| `invocation`       | text   | How to run it                                       |
| `phase5_relevance` | text   | Whether Phase 5 (launcher hardening) will affect it |

---

## Relationships

```
TerminologyGlossary ← referenced by → ErrorCodeNamespace (severity field)
TrackingIDPolicy ← referenced by → CompatibilityPledge (propagation changes per phase)
ErrorCodeNamespace ← validated against → EndpointSnapshot (every endpoint's error codes must be in namespace)
LauncherInvariantsChecklist ← validated against → EndpointSnapshot.scripts (every script must appear)
ParityGapRegister ← scopes → Phase 7 spec requirements
EndpointSnapshot ← grounds → CompatibilityPledge (every endpoint must have a pledge entry)
```

## State Transitions

N/A — Phase 0 produces reference documents only. No runtime state changes.

## Validation Rules

1. Every term in the glossary must have a non-empty `example_trigger`.
2. Every error code must map to exactly one `domain_prefix` from the allowed set.
3. Every endpoint in the snapshot must have a corresponding entry in the compatibility pledge.
4. Every script in the snapshot must have a corresponding entry in the launcher invariants checklist.
5. Every MT5 capability category must have at least one entry in the parity gap register.
