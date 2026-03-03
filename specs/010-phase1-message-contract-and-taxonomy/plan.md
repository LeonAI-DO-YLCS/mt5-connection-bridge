# Implementation Plan: Phase 1 — Message Contract and Taxonomy

**Branch**: `010-phase1-message-contract-and-taxonomy` | **Date**: 2026-03-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-phase1-message-contract-and-taxonomy/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command.

## Summary

Replace all user-facing technical leak-through (raw MT5 retcode tuples, Pydantic validation arrays, and inconsistent response shapes) with a canonical `MessageEnvelope` that is consistent, human-readable, and actionable. Backend introduces a messaging normalization module (`app/messaging/`); dashboard introduces a centralized message renderer. Full backward compatibility maintained via legacy `detail` field during the migration window (Phases 1–5).

## Technical Context

**Language/Version**: Python 3.12 (backend), Vanilla JS ES2020+ (dashboard)
**Primary Dependencies**: FastAPI ≥0.104, Pydantic v2 ≥2.5, MetaTrader5 ≥5.0.5640
**Storage**: N/A (no new persistence)
**Testing**: pytest (existing suite in `tests/contract/` and `tests/integration/`)
**Target Platform**: WSL2/Linux host + Windows MT5 runtime
**Project Type**: Web-service (REST API bridge + single-page dashboard)
**Performance Goals**: No measurable latency regression — normalization is a thin data transformation
**Constraints**: Must not change HTTP status code semantics (Phase 3). Must not redefine Pydantic business models (Phase 0 invariant). Legacy `detail` field retained until Phase 6.
**Scale/Scope**: 6 trade-affecting endpoint families, 19 `alert()` calls to replace, 18 error codes in taxonomy

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

| Principle                            | Status  | Evidence                                                                                                             |
| ------------------------------------ | ------- | -------------------------------------------------------------------------------------------------------------------- |
| I. Multi-Agent Orchestration         | N/A     | Phase 1 does not modify orchestration logic                                                                          |
| II. Trading Modes & Execution Safety | ✅ Pass | Error normalization preserves execution gating. No execution logic is changed — only the error _shape_ is normalized |
| III. Data-Driven Valuation           | N/A     | No valuation logic affected                                                                                          |
| IV. Risk-Managed Decision Making     | ✅ Pass | Risk controls unchanged. Canonical codes make risk events _more_ traceable                                           |
| V. Execution & Connection Frameworks | ✅ Pass | Adapter isolation preserved. New messaging module is additive, not modifying connection logic                        |
| VI. MT5 Connection Framework         | ✅ Pass | MT5 interactions unchanged. Only response shapes are normalized post-execution                                       |
| Workflow (feature branch)            | ✅ Pass | Working on branch `010-phase1-message-contract-and-taxonomy`                                                         |

**Post-design re-check**: ✅ All gates still pass. No new violations introduced by the design.

## Project Structure

### Documentation (this feature)

```text
specs/010-phase1-message-contract-and-taxonomy/
├── plan.md              # This file
├── research.md          # Phase 0 output — 6 unknowns resolved
├── data-model.md        # Phase 1 output — 5 entities defined
├── quickstart.md        # Phase 1 output — developer implementation guide
├── contracts/
│   └── api-contracts.md # Phase 1 output — canonical envelope + error code registry
├── checklists/
│   └── requirements.md  # Requirements checklist (pre-existing)
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
app/
├── messaging/              # NEW — Phase 1 messaging normalization module
│   ├── __init__.py
│   ├── envelope.py         # MessageEnvelope model + MessageEnvelopeException
│   ├── codes.py            # ErrorCode enum with metadata
│   ├── tracking.py         # generate_tracking_id() factory
│   └── normalizer.py       # normalize_error() / normalize_success() entry points
├── main.py                 # MODIFIED — exception handlers call normalizer
├── routes/
│   ├── execute.py          # MODIFIED — error returns → MessageEnvelopeException
│   ├── close_position.py   # MODIFIED
│   ├── pending_order.py    # MODIFIED
│   ├── order_check.py      # MODIFIED
│   ├── orders.py           # MODIFIED
│   └── positions.py        # MODIFIED
├── models/                 # UNCHANGED — no model redefinitions
└── mappers/                # UNCHANGED

dashboard/
├── js/
│   ├── message-renderer.js # NEW — centralized envelope renderer
│   ├── execute-v2.js       # MODIFIED — alert() → renderMessage()
│   ├── positions.js        # MODIFIED
│   ├── orders.js           # MODIFIED
│   └── app.js              # MODIFIED
├── css/
│   └── messages.css        # NEW — message severity styling
└── index.html              # MODIFIED — new script/link tags

tests/
├── unit/
│   ├── test_envelope.py    # NEW
│   ├── test_codes.py       # NEW
│   ├── test_tracking.py    # NEW
│   └── test_normalizer.py  # NEW
└── contract/
    ├── test_envelope_contract.py   # NEW
    └── test_backward_compat.py     # NEW
```

**Structure Decision**: Follows the existing option-2 pattern (backend `app/` + frontend `dashboard/`). The new `app/messaging/` package is a clean addition parallel to `app/mappers/` and `app/models/`.

## Verification Plan

### Automated Tests

**Existing tests** (must still pass — backward compatibility gate):

```bash
cd /home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge
.venv/bin/python -m pytest tests/ -v
```

**New unit tests**:

```bash
.venv/bin/python -m pytest tests/unit/test_envelope.py tests/unit/test_codes.py tests/unit/test_tracking.py tests/unit/test_normalizer.py -v
```

- `test_envelope.py`: MessageEnvelope serialization, field constraints, context sanitization (no secrets)
- `test_codes.py`: All ErrorCode members have required metadata, no duplicate codes, domain prefixes valid
- `test_tracking.py`: Format matches `brg-\d{8}T\d{6}-[0-9a-f]{4}`, length ≤ 30, uniqueness within a second
- `test_normalizer.py`: `normalize_error()` and `normalize_success()` produce valid envelopes with all fields

**New contract tests**:

```bash
.venv/bin/python -m pytest tests/contract/test_envelope_contract.py tests/contract/test_backward_compat.py -v
```

- `test_envelope_contract.py`: All 6 trade-affecting endpoints return canonical envelope fields on error
- `test_backward_compat.py`: All error responses still contain legacy `detail` field

### Manual Verification

Dashboard-side changes require browser testing. After implementation:

1. Start the bridge: `./scripts/start_bridge.sh`
2. Open the dashboard at `http://localhost:8001/dashboard/`
3. Trigger a trade with invalid volume → verify: styled message with title/message/action, tracking ID with copy button, no raw JSON
4. Trigger a trade while MT5 is disconnected → verify: severity=critical styling, retryable indicator
5. Execute a successful trade → verify: success envelope displayed with green styling
6. Click the tracking ID copy button → verify: correct ID copied to clipboard
7. Expand the "Details" section → verify: context field displayed as key-value pairs

## Complexity Tracking

No Constitution Check violations to justify. All gates pass cleanly.
