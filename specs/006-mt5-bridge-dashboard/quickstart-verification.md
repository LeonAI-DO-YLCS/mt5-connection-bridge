# Quickstart Verification Notes

**Feature**: `006-mt5-bridge-dashboard`  
**Date**: 2026-03-02

## Automated Validation Completed

- Full test suite executed from `mt5-connection-bridge` root:
  - Command: `./.venv/bin/pytest`
  - Result: `123 passed, 1 warning`
  - Coverage: `90.43%` (meets `--cov-fail-under=90`)

## Quickstart Runtime Validation Status

Live MT5 quickstart `curl` checks from `specs/006-mt5-bridge-dashboard/quickstart.md` require:

- Running MT5 terminal session on Windows host
- Valid broker login/session
- Bridge process started with real `.env` credentials

This environment does not include a live MT5 terminal session, so commands were not executed against a real broker connection here.

## Expected Manual Verification Outcomes

- `GET /health`: `200`, `connected=true`, `authorized=true`
- Visibility endpoints (`/account`, `/positions`, `/orders`, `/tick/{ticker}`, `/terminal`): `200`, schema-conformant payloads
- Management endpoints (`/close-position`, `/positions/{ticket}/sltp`, `DELETE /orders/{ticket}`): successful response on valid tickets and execution enabled
- Execution endpoints (`/order-check`, `/pending-order`): valid pre-check and pending order placement behavior
- History endpoints (`/history/deals`, `/history/orders`, `/broker-symbols`): `200`, counts and list payloads with expected filters

## Notes

- Contract coverage for these endpoint groups is present in:
  - `tests/contract/test_visibility_contracts.py`
  - `tests/contract/test_management_contracts.py`
  - `tests/contract/test_execution_contracts_v2.py`
  - `tests/contract/test_history_contracts.py`
