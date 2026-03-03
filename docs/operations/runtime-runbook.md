# MT5 Bridge Runtime Runbook

## Rules

1. Never source `.env` directly in shell scripts.
2. Change execution policy only through `PUT /config/execution`.
3. After restart, always run `./scripts/smoke_bridge.sh`.
4. Use diagnostics endpoints for RCA before editing symbol configs.
5. Treat `X-Error-Code` as the primary automation signal for error handling.

## Standard Procedure

1. `./scripts/stop_bridge.sh`
2. `./scripts/start_bridge.sh --background`
3. `./scripts/smoke_bridge.sh`
4. Open dashboard `/dashboard` and verify `Status` + `Execution Policy`.
5. If symbol issues appear, call `GET /diagnostics/symbols`.

## Mistakes To Avoid

- Killing random PIDs without checking listener port ownership.
- Assuming runtime toggles survive restart without persisted state.
- Treating all 404 errors equally; inspect `X-Error-Code`.
- Running the full test suite for every small check; use fast profile first.

