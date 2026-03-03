# Error-Code Namespace Policy — MT5 Connection Bridge

> **Effective Date**: 2026-03-03
> **Namespace Version**: 1.0
> **Applies To**: All bridge error responses (current and future phases)

---

## 1. Naming Convention

### Pattern

```
<DOMAIN>_<CONDITION>
```

All codes use **UPPERCASE** letters with **underscores** as separators.

### Allowed Domain Prefixes

| Domain Prefix | Scope                                                                                 | Examples                  |
| ------------- | ------------------------------------------------------------------------------------- | ------------------------- |
| `VALIDATION_` | Input validation failures (malformed requests, missing fields, constraint violations) | `VALIDATION_ERROR`        |
| `MT5_`        | MT5 terminal connectivity, session, and API-level failures                            | `MT5_DISCONNECTED`        |
| `EXECUTION_`  | Trade execution policy, queue overload, single-flight gates                           | `EXECUTION_DISABLED`      |
| `WORKER_`     | Internal worker state and lifecycle errors                                            | — (reserved for Phase 3+) |
| `SYMBOL_`     | Symbol lookup, configuration, and capability errors                                   | `SYMBOL_NOT_CONFIGURED`   |
| `REQUEST_`    | Generic request-level errors not covered by a specific domain                         | `REQUEST_ERROR`           |
| `INTERNAL_`   | Unhandled exceptions, unexpected server errors                                        | `INTERNAL_SERVER_ERROR`   |

New domain prefixes may only be added through the governance process defined in §3.

---

## 2. Initial Code Registry

### Validation Failures

| Code               | Domain        | Description                                                 | HTTP Status | Severity | Phase Introduced  |
| ------------------ | ------------- | ----------------------------------------------------------- | ----------- | -------- | ----------------- |
| `VALIDATION_ERROR` | `VALIDATION_` | Request body or query parameters failed Pydantic validation | 422         | medium   | Phase 0 — initial |

### Connectivity and Runtime Failures

| Code                    | Domain      | Description                                                 | HTTP Status | Severity | Phase Introduced  |
| ----------------------- | ----------- | ----------------------------------------------------------- | ----------- | -------- | ----------------- |
| `MT5_DISCONNECTED`      | `MT5_`      | MT5 terminal is not connected or connection was lost        | 503         | critical | Phase 0 — initial |
| `SERVICE_UNAVAILABLE`   | `INTERNAL_` | Bridge service is unavailable (non-MT5 connectivity reason) | 503         | critical | Phase 0 — initial |
| `INTERNAL_SERVER_ERROR` | `INTERNAL_` | Unhandled exception occurred during request processing      | 500         | critical | Phase 0 — initial |

### Policy and Capability Failures

| Code                        | Domain       | Description                                                  | HTTP Status | Severity | Phase Introduced  |
| --------------------------- | ------------ | ------------------------------------------------------------ | ----------- | -------- | ----------------- |
| `EXECUTION_DISABLED`        | `EXECUTION_` | Execution policy is disabled (`EXECUTION_ENABLED=false`)     | 403         | high     | Phase 0 — initial |
| `OVERLOAD_OR_SINGLE_FLIGHT` | `EXECUTION_` | Request rejected due to queue overload or single-flight gate | 409         | high     | Phase 0 — initial |

### Request Compatibility Failures

| Code                    | Domain     | Description                                                   | HTTP Status | Severity | Phase Introduced  |
| ----------------------- | ---------- | ------------------------------------------------------------- | ----------- | -------- | ----------------- |
| `UNAUTHORIZED_API_KEY`  | `REQUEST_` | Missing or invalid API key in `X-API-Key` header              | 401         | high     | Phase 0 — initial |
| `SYMBOL_NOT_CONFIGURED` | `SYMBOL_`  | Requested ticker is not found in the symbol map configuration | 404         | medium   | Phase 0 — initial |
| `RESOURCE_NOT_FOUND`    | `REQUEST_` | Requested resource (position, order, endpoint) does not exist | 404         | medium   | Phase 0 — initial |

### Generic Fallback

| Code            | Domain     | Description                                                | HTTP Status | Severity | Phase Introduced  |
| --------------- | ---------- | ---------------------------------------------------------- | ----------- | -------- | ----------------- |
| `REQUEST_ERROR` | `REQUEST_` | Catch-all for client errors not matched by a specific code | 4xx         | medium   | Phase 0 — initial |

### Registry Summary

| Category                       | Codes                                                                 | Count  |
| ------------------------------ | --------------------------------------------------------------------- | ------ |
| Validation failures            | `VALIDATION_ERROR`                                                    | 1      |
| Connectivity/runtime failures  | `MT5_DISCONNECTED`, `SERVICE_UNAVAILABLE`, `INTERNAL_SERVER_ERROR`    | 3      |
| Policy/capability failures     | `EXECUTION_DISABLED`, `OVERLOAD_OR_SINGLE_FLIGHT`                     | 2      |
| Request compatibility failures | `UNAUTHORIZED_API_KEY`, `SYMBOL_NOT_CONFIGURED`, `RESOURCE_NOT_FOUND` | 3      |
| Generic fallback               | `REQUEST_ERROR`                                                       | 1      |
| **Total**                      |                                                                       | **10** |

---

## 3. Governance Rules

### Adding New Error Codes

1. **Check for collisions**: Before adopting a new code, search this registry table for any code with the same or overlapping semantic meaning. If a collision is found, use the existing code or propose renaming.

2. **Select the domain prefix**: The new code's domain MUST be from the allowed set in §1. If no domain fits, propose a new domain prefix as a formal amendment to this document.

3. **Document the code**: Add a row to the appropriate category table in §2 with all fields populated, including `Phase Introduced` (the phase in which this code was first added).

4. **Update this document**: Commit the change to `docs/baseline/error-code-namespace.md` in the same PR that introduces the code in runtime code.

### Deprecation Process

- Error codes are **never removed**. A code may be deprecated by adding a `Deprecated` column entry with the successor code and the deprecation date.
- Deprecated codes continue to be recognized by consumers but should no longer be produced by new error paths.
- The deprecated code and its successor must coexist in the registry for at least one full phase cycle.

### Collision Prevention

- No two codes in the registry may have the same semantic meaning (i.e., they would be triggered by the same runtime condition).
- The `HTTP Status` column may have duplicates (multiple codes can map to 503, for example), but the `Description` must be distinct.
- If a proposed code is semantically equivalent to an existing one, prefer the existing code.

---

## 4. Minimum Required Codes

### Coverage Validation

All 5 failure categories are covered:

| Failure Category               | Required | Covered By                                                            | Status |
| ------------------------------ | -------- | --------------------------------------------------------------------- | ------ |
| Validation failures            | ≥1 code  | `VALIDATION_ERROR`                                                    | ✅     |
| Connectivity/runtime failures  | ≥1 code  | `MT5_DISCONNECTED`, `SERVICE_UNAVAILABLE`, `INTERNAL_SERVER_ERROR`    | ✅     |
| Policy/capability failures     | ≥1 code  | `EXECUTION_DISABLED`, `OVERLOAD_OR_SINGLE_FLIGHT`                     | ✅     |
| Request compatibility failures | ≥1 code  | `UNAUTHORIZED_API_KEY`, `SYMBOL_NOT_CONFIGURED`, `RESOURCE_NOT_FOUND` | ✅     |
| Generic fallback               | ≥1 code  | `REQUEST_ERROR`                                                       | ✅     |

**No gaps identified.** All 5 categories have at least one code. The namespace is ready for Phase 1 expansion.

### Anticipated Phase 1+ Additions

The following codes are expected to be added in future phases (not yet registered):

- Phase 1: `MT5_COMMENT_REJECTED` (comment field validation failure)
- Phase 2: `WORKER_NOT_READY` (readiness check failure)
- Phase 3: `EXECUTION_IDEMPOTENT_DUPLICATE` (duplicate idempotency key)
- Phase 4: `MT5_COMMENT_FALLBACK` (comment normalization triggered)

These will be formally registered when their respective phases are implemented.
