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
- Operational metrics are captured in `logs/metrics.jsonl` with a rolling retention policy.

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
- `RUNTIME_STATE_PATH=logs/runtime_state.json` (persists runtime execution policy toggles)
- `METRICS_RETENTION_DAYS=90`
- `MULTI_TRADE_OVERLOAD_QUEUE_THRESHOLD=100`
- `MAX_PRE_DISPATCH_SLIPPAGE_PCT=1.0`
- `MAX_POST_FILL_SLIPPAGE_PCT=1.0`

## Run

```bash
cd mt5-connection-bridge
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

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
