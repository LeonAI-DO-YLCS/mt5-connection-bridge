# Compatibility Pledge — MT5 Connection Bridge

> **Effective Date**: 2026-03-03
> **Pledge Version**: 1.0
> **Applies To**: All endpoint contracts across Phases 0–7 of the user-facing reliability rollout

---

## 1. Pledge Summary

This document commits to specific stability levels for every endpoint in the MT5 Connection Bridge during the phased reliability rollout. The purpose is to prevent unintended breaking changes and to give all consumers (dashboard, AI strategies, external integrations) clear expectations about what will and will not change.

**Three stability levels**:

- **`frozen`**: The endpoint's response shape, HTTP semantics, and URL path will not change across the entire phased rollout. New fields may be added to the response only if they are additive and optional.
- **`evolving`**: The endpoint may receive new response fields, new query parameters, or enriched data. Existing fields will not be removed or renamed. Consumers that ignore unknown fields are unaffected.
- **`migrating`**: The endpoint's error response shape will change from the current `{"detail": ...}` format to the canonical `MessageEnvelope` format during a stated compatibility window. Both shapes will coexist during the window.

---

## 2. Endpoint Pledge Table

### Health and Diagnostics

| Endpoint                   | Stability Level | Phases That May Change It | Compatibility Window | Migration Notes                                             |
| -------------------------- | --------------- | ------------------------- | -------------------- | ----------------------------------------------------------- |
| `GET /health`              | `frozen`        | None                      | N/A                  | Response shape is stable. No changes planned.               |
| `GET /worker/state`        | `frozen`        | None                      | N/A                  | Returns worker state enum. No changes planned.              |
| `GET /metrics`             | `frozen`        | None                      | N/A                  | Rolling metrics structure is stable.                        |
| `GET /diagnostics/runtime` | `evolving`      | Phase 2 (readiness)       | N/A                  | May gain readiness check fields. No removals.               |
| `GET /diagnostics/symbols` | `evolving`      | Phase 7 (parity)          | N/A                  | May gain additional symbol introspection fields.            |
| `GET /logs`                | `evolving`      | Phase 1 (messages)        | N/A                  | Log entries may gain `tracking_id` and `error_code` fields. |

### Market and Symbol Data

| Endpoint                            | Stability Level | Phases That May Change It | Compatibility Window | Migration Notes                                                 |
| ----------------------------------- | --------------- | ------------------------- | -------------------- | --------------------------------------------------------------- |
| `GET /symbols`                      | `evolving`      | Phase 7 (parity)          | N/A                  | May gain additional symbol metadata. Existing fields preserved. |
| `GET /broker-symbols`               | `evolving`      | Phase 7 (parity)          | N/A                  | May gain additional broker symbol fields.                       |
| `GET /broker-capabilities`          | `evolving`      | Phase 2, 7                | N/A                  | May gain readiness and parity fields.                           |
| `POST /broker-capabilities/refresh` | `evolving`      | None planned              | N/A                  | Response shape is simple; no changes expected.                  |
| `GET /tick/{ticker}`                | `evolving`      | Phase 7 (parity)          | N/A                  | May gain additional tick fields (e.g., market book depth).      |
| `POST /prices`                      | `evolving`      | None planned              | N/A                  | No changes planned.                                             |

### Trade Operations

| Endpoint                       | Stability Level | Phases That May Change It                  | Compatibility Window | Migration Notes                                                                                                 |
| ------------------------------ | --------------- | ------------------------------------------ | -------------------- | --------------------------------------------------------------------------------------------------------------- |
| `POST /execute`                | `migrating`     | Phase 1 (envelope), Phase 3 (hardening)    | Phases 1–5           | Error responses will adopt `MessageEnvelope`. Legacy `{"detail":...}` shape maintained through Phase 5. See §3. |
| `POST /pending-order`          | `migrating`     | Phase 1, Phase 3                           | Phases 1–5           | Same as `/execute`.                                                                                             |
| `POST /close-position`         | `migrating`     | Phase 1, Phase 3, Phase 4 (comment compat) | Phases 1–5           | Same as `/execute`. Phase 4 adds comment normalization (transparent to consumer).                               |
| `POST /order-check`            | `evolving`      | Phase 3 (hardening)                        | N/A                  | May gain additional pre-check fields. No breaking changes.                                                      |
| `GET /orders`                  | `evolving`      | Phase 3                                    | N/A                  | May gain additional order fields.                                                                               |
| `PUT /orders/{ticket}`         | `migrating`     | Phase 1, Phase 3                           | Phases 1–5           | Error responses will adopt `MessageEnvelope`.                                                                   |
| `DELETE /orders/{ticket}`      | `migrating`     | Phase 1, Phase 3                           | Phases 1–5           | Error responses will adopt `MessageEnvelope`.                                                                   |
| `GET /positions`               | `evolving`      | Phase 3                                    | N/A                  | May gain additional position fields.                                                                            |
| `PUT /positions/{ticket}/sltp` | `migrating`     | Phase 1, Phase 3                           | Phases 1–5           | Error responses will adopt `MessageEnvelope`.                                                                   |

### Account and Terminal

| Endpoint              | Stability Level | Phases That May Change It | Compatibility Window | Migration Notes                                            |
| --------------------- | --------------- | ------------------------- | -------------------- | ---------------------------------------------------------- |
| `GET /account`        | `frozen`        | None                      | N/A                  | Response is a direct MT5 pass-through. No changes planned. |
| `GET /terminal`       | `frozen`        | None                      | N/A                  | Response is a direct MT5 pass-through. No changes planned. |
| `GET /history/deals`  | `evolving`      | Phase 7 (parity)          | N/A                  | May gain additional history fields.                        |
| `GET /history/orders` | `evolving`      | Phase 7 (parity)          | N/A                  | May gain additional history fields.                        |

### Configuration

| Endpoint      | Stability Level | Phases That May Change It | Compatibility Window | Migration Notes                                   |
| ------------- | --------------- | ------------------------- | -------------------- | ------------------------------------------------- |
| `GET /config` | `evolving`      | Phases 2, 5               | N/A                  | May gain readiness and runtime diagnostic fields. |

### Dashboard

| Path          | Stability Level | Notes                                                  |
| ------------- | --------------- | ------------------------------------------------------ |
| `/dashboard/` | `evolving`      | Phase 6 overhauls the UI but the mount path is stable. |

---

## 3. Legacy Support Window

### Current State

Error responses across all endpoints currently use this shape:

```json
{
  "detail": "Human-readable error message"
}
```

With an `X-Error-Code` response header carrying the machine-readable error code.

### Migration Plan

Starting in **Phase 1**, endpoints marked as `migrating` will begin returning the canonical `MessageEnvelope` alongside the legacy `detail` field:

```json
{
  "detail": "Human-readable error message",
  "message": "Human-readable error message",
  "error_code": "MT5_DISCONNECTED",
  "tracking_id": "brg-20260303T094500-a3f7",
  "severity": "critical",
  "category": "error"
}
```

### Window Timeline

| Phase             | Legacy `detail` field        | `MessageEnvelope` fields    | `X-Error-Code` header                              |
| ----------------- | ---------------------------- | --------------------------- | -------------------------------------------------- |
| Phase 0 (current) | ✅ Present (only)            | ❌ Not yet added            | ✅ Present                                         |
| Phases 1–5        | ✅ Present (backward compat) | ✅ Present (new canonical)  | ✅ Present (kept for header-reading consumers)     |
| Phase 6+          | ❌ **Removed**               | ✅ Present (canonical only) | ⚠️ Deprecated (body `error_code` is authoritative) |

**Retirement trigger**: The legacy `detail` field is removed only after Phase 6 (Dashboard Operator Experience) is deployed and validated — confirming that the only known consumer (the dashboard) has been updated to read `message` instead of `detail`.

---

## 4. Consumer Migration Guide

### For AI Strategy Consumers (Python callers)

1. **Now**: Read `response.json()["detail"]` for error messages and `response.headers["X-Error-Code"]` for error codes.
2. **Phase 1–5**: Begin reading `response.json()["message"]` and `response.json()["error_code"]`. Both legacy and new fields are present.
3. **Phase 6+**: Remove any code reading `detail` or `X-Error-Code` header. Use `message`, `error_code`, `tracking_id`, `severity`, and `category` from the response body.

### For Dashboard (JavaScript)

1. **Now**: `apiHelper` reads `response.detail` and displays in `alert()`.
2. **Phase 6**: Dashboard will be rewritten to read the `MessageEnvelope` fields and render them in the new message center panel.

### For Any New Consumers

If you are integrating with the bridge starting now, use the `MessageEnvelope` fields (`message`, `error_code`, `tracking_id`) from day one (when available in Phase 1+). Do not build new integrations against the legacy `detail` field.
