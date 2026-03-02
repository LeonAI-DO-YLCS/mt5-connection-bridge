# MT5 Connection Bridge

Windows-native FastAPI microservice that connects MetaTrader 5 (MT5) to the Dockerized AI Hedge Fund backend.

## Purpose

- Keep MT5 integration outside Linux containers (MT5 Python API is Windows-only).
- Expose HTTP endpoints for:
1. Health checks
2. Historical OHLCV prices
3. Live trade execution
- Return schema-compatible payloads used by the existing AI Hedge Fund stack.

## Architecture

- `mt5-connection-bridge` runs on Windows host alongside MT5 terminal.
- AI Hedge Fund backend (Docker/Linux) calls bridge over HTTP via `MT5_BRIDGE_URL`.
- All MT5 calls are serialized through a dedicated worker thread (`app/mt5_worker.py`).

## Project Layout

```text
mt5-connection-bridge/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── auth.py
│   ├── audit.py
│   ├── mt5_worker.py
│   ├── models/
│   ├── mappers/
│   └── routes/
├── config/symbols.yaml
├── logs/
├── requirements.txt
└── .env.example
```

## Requirements

- Windows machine with MetaTrader 5 installed and logged into broker account (e.g. Deriv).
- Python 3.11+.
- MT5 terminal running before bridge startup.

## Setup

```bash
cd mt5-connection-bridge
python -m pip install -r requirements.txt
copy .env.example .env
```

Update `.env`:

```env
MT5_BRIDGE_PORT=8001
MT5_BRIDGE_API_KEY=replace-with-secure-value
MT5_LOGIN=<account_id>
MT5_PASSWORD=<account_password>
MT5_SERVER=Deriv-Demo
```

Update symbol mappings in `config/symbols.yaml` for your broker symbol names.

## Run

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## API

All endpoints require header:

```text
X-API-KEY: <MT5_BRIDGE_API_KEY>
```

### `GET /health`

Reports bridge/terminal connectivity and account status.

### `GET /prices`

Query params:
- `ticker`
- `start_date` (`YYYY-MM-DD`)
- `end_date` (`YYYY-MM-DD`)
- `timeframe` (`M1|M5|M15|M30|H1|H4|D1|W1|MN1`, default `D1`)

Returns:

```json
{
  "ticker": "V75",
  "prices": [
    {
      "open": 0,
      "close": 0,
      "high": 0,
      "low": 0,
      "volume": 0,
      "time": "2026-01-01T00:00:00Z"
    }
  ]
}
```

### `POST /execute`

Request:

```json
{
  "ticker": "V75",
  "action": "buy",
  "quantity": 0.01,
  "current_price": 450000.0
}
```

Response:

```json
{
  "success": true,
  "filled_price": 450001.5,
  "filled_quantity": 0.01,
  "ticket_id": 123456789,
  "error": null
}
```

Trade audit events are written to `logs/trades.jsonl`.

## AI Hedge Fund Environment

Set these in the main project `.env`:

```env
DEFAULT_DATA_PROVIDER=mt5
MT5_BRIDGE_URL=http://host.docker.internal:8001
MT5_BRIDGE_API_KEY=replace-with-same-api-key
LIVE_TRADING=false
```

`LIVE_TRADING` must be explicitly set to `true` before any live execution path is used.

## Failure Handling

- MT5 worker reconnect retries: exponential backoff (`1s, 2s, 4s, 8s...`, max 5 tries, capped to 30s delay).
- If reconnect fails, worker transitions to `DISCONNECTED` and queued requests fail with connection errors (mapped to HTTP 503 in routes).
- Unknown tickers return HTTP 404.
- Invalid actions/quantities return HTTP 422.

## Troubleshooting

- `401 Unauthorized`: `X-API-KEY` mismatch between caller and bridge env.
- `503 MT5 terminal not connected`: MT5 terminal closed/disconnected; restart terminal and bridge.
- Empty `prices`: requested range not available on broker/timeframe.
- Symbol errors: ensure ticker exists in `config/symbols.yaml` and symbol name exactly matches MT5 Market Watch.
