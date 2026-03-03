# MT5 Connection Bridge

Windows-native FastAPI microservice that connects MetaTrader 5 (MT5) to the Dockerized AI Hedge Fund backend.

## Purpose

- Keep MT5 integration outside Linux containers (MT5 Python API is Windows-only).
- Preserve existing bridge contracts (`/health`, `/prices`, `/execute`) and add operational verification surfaces.
- Provide dashboard-driven validation for status, symbols, prices, execution safety, logs, config, and metrics.

## Architecture

- `mt5-connection-bridge` runs on Windows host alongside MT5 terminal.
- AI Hedge Fund backend (Docker/Linux) calls bridge over HTTP via `MT5_BRIDGE_URL`.
- MT5 calls remain serialized through a dedicated worker queue (`app/mt5_worker.py`).
- Operational metrics are captured in `logs/dashboard/metrics.jsonl` with a rolling retention policy.

## Project Layout

```text
mt5-connection-bridge/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── auth.py
│   ├── audit.py
│   ├── metrics.py
│   ├── mt5_worker.py
│   ├── models/
│   ├── mappers/
│   └── routes/
├── dashboard/
│   ├── index.html
│   ├── css/dashboard.css
│   └── js/
├── config/symbols.yaml
├── logs/
├── tests/
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```

## Runtime Configuration

Copy `.env.example` to `.env` and set credentials/policies.

Key feature flags:

- `EXECUTION_ENABLED=false` (default safety gate)
- `RUNTIME_STATE_PATH=logs/bridge/runtime_state.json` (persists runtime execution policy toggles)
- `METRICS_RETENTION_DAYS=90`
- `MULTI_TRADE_OVERLOAD_QUEUE_THRESHOLD=100`
- `MAX_PRE_DISPATCH_SLIPPAGE_PCT=1.0`
- `MAX_POST_FILL_SLIPPAGE_PCT=1.0`
- `CAPABILITIES_CACHE_TTL_SECONDS=60` (TTL for live broker capabilities snapshot)
- `AUTO_SELECT_SYMBOLS=true` (auto-select MT5 symbols in Market Watch for direct symbol flows)

## Run

```bash
cd mt5-connection-bridge
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## One-Command Launcher (Inspector Mode)

Use the launcher for live terminal inspection plus persisted per-run artifacts:

```bash
cd mt5-connection-bridge
./scripts/launch_bridge_dashboard.sh
```

For WSL2 users (recommended for MT5 connection on Windows host), use:

```bash
cd mt5-connection-bridge
./scripts/launch_bridge_windows.sh
```

WSL behavior:
- launcher auto-selects Windows-host runtime mode when running in WSL and `LAUNCHER_PREFER_WINDOWS=true`
- PowerShell runner: `scripts/windows/launch_bridge_windows.ps1`
- Windows Python resolution order: `.venv-win\\Scripts\\python.exe`, `.venv\\Scripts\\python.exe`, then `python` on Windows PATH
- Optional override: `MT5_WINDOWS_PYTHON` in `.env`
- Automatic setup: if required modules are missing, launcher bootstraps `.venv-win` (controlled by `LAUNCHER_AUTO_SETUP_WINDOWS_VENV=true`)
- Recommended Windows Python: 3.10-3.12 for `MetaTrader5` compatibility

The launcher prints:
- bridge endpoint URL
- dashboard URL
- run-scoped log bundle path

Interactive TUI behavior:
- on interactive terminals (`LAUNCHER_TUI_MODE=auto`), launcher renders a live status screen
- panel includes runtime mode, process chain, runtime/listener PIDs, API health, dashboard status, and artifact paths
- fixed-screen rendering with color-coded sections and change-only redraws (no growing log stream in the panel)
- set `LAUNCHER_TUI_MODE=false` to force classic streaming logs
- probe cadence is configurable with `LAUNCHER_TUI_PROBE_SECONDS` (default `5`)
- access logs are persisted by default in launcher runtime (`LAUNCHER_UVICORN_ACCESS_LOG=true`)

Per-run artifacts are written to:

```text
logs/bridge/launcher/<run-id>/
├── launcher.log
├── bridge.stdout.log
├── bridge.stderr.log
└── session.json
```

Dashboard event artifacts are written to:

```text
logs/dashboard/
├── trades.jsonl
├── tasks.jsonl
└── metrics.jsonl
```

Runtime reliability policy:
- one automatic restart attempt on unexpected runtime crash
- safe non-success exit if restart attempt also fails
- lifecycle and failure events persisted in the same run bundle

Security/access notes:
- launcher sessions are network-access enabled by default
- authenticated access remains required for operations
- failed authentication attempts are logged for inspection (no lockout/throttling policy in launcher scope)

## API

All API routes require:

```text
X-API-KEY: <MT5_BRIDGE_API_KEY>
```

### Existing routes (compatibility)

- `GET /health`
- `GET /prices`
- `POST /execute`

### Additive operational routes

- `GET /symbols`
- `GET /broker-capabilities`
- `POST /broker-capabilities/refresh`
- `GET /logs?limit=&offset=`
- `GET /config`
- `GET /worker/state`
- `GET /metrics`
- `PUT /config/execution` (runtime execution policy toggle + persistence)
- `GET /diagnostics/runtime` (policy source, fingerprint, uptime, queue/worker state)
- `GET /diagnostics/symbols` (per-symbol reason codes and broker-resolution diagnostics)

Runtime error responses include `X-Error-Code` headers for machine-readable handling.

## Dashboard

- URL: `/dashboard/`
- Tabs: Status, Symbols, Prices, Execute, Logs, Config, Metrics
- Session behavior: API key stored in `sessionStorage`, cleared on browser tab close (`beforeunload`)

Execution tab safety controls:

- Policy badge for `EXECUTION_ENABLED`
- Explicit risk-confirmation checkbox
- Multi-trade toggle with warning
- Single-flight blocking when multi-trade is off
- Queue overload rejection based on `MULTI_TRADE_OVERLOAD_QUEUE_THRESHOLD`
- Per-symbol trade-mode guardrails (long-only/short-only/close-only/disabled)
- `mt5_symbol_direct` routing so dashboard can execute broker-native symbols without YAML aliases

## Testing

Install dev dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run full regression suite:

```bash
pytest
```

Coverage gate:

- Enforced by `pytest.ini`
- Minimum statement coverage: `>=90%`

Optional focused runs:

```bash
pytest tests/unit
pytest tests/integration
pytest tests/contract
pytest tests/performance
```

Fast local smoke/unit cycle:

```bash
./scripts/test-fast.sh
```

Full regression:

```bash
./scripts/test-full.sh
```

## Operations

Start, stop, restart, and smoke-check scripts:

```bash
./scripts/start_bridge.sh --background
./scripts/stop_bridge.sh
./scripts/restart_bridge.sh
./scripts/smoke_bridge.sh
```

These scripts read `.env` safely without shell-sourcing, so special characters in credentials do not break execution.

## Validation Snapshot

Latest local run on **March 2, 2026**:

- `49 passed`
- Coverage: `90.13%`
- Command: `.venv/bin/python -m pytest`

## Troubleshooting

- `401 Unauthorized`: missing/invalid `X-API-KEY`.
- `404`: unknown ticker/symbol mapping.
- `422`: request validation failure.
- `503`: MT5 unavailable or connection failure.
- `success=false` on `/execute`: policy gate, slippage rejection, or overload protection triggered.

## Runtime Hardening Rules

- Persist policy changes through `PUT /config/execution`; do not rely on in-memory toggles.
- Use `GET /diagnostics/symbols` before changing symbol maps when “symbol not found” appears.
- Validate health with `./scripts/smoke_bridge.sh` after every restart.
- Prefer `./scripts/stop_bridge.sh` over ad-hoc process killing by PID.
- Keep test execution tiered: `test-fast.sh` for local loop, `test-full.sh` before merge.
