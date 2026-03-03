# Quickstart: MT5 Bridge Full Dashboard

**Branch**: `006-mt5-bridge-dashboard` | **Date**: 2026-03-02

---

## Prerequisites

1. Python 3.11+ installed
2. MT5 terminal running on Windows host
3. `.env` file configured with MT5 credentials, API key, and `EXECUTION_ENABLED=true`

## Setup

```bash
cd mt5-connection-bridge
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Run the Bridge

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## Verify Phase 0: Foundations

```bash
# Health check (should show connected=true, authorized=true)
curl -H "X-API-KEY: $API_KEY" http://localhost:8001/health
```

## Verify Phase 1: Visibility

```bash
# Account info
curl -H "X-API-KEY: $API_KEY" http://localhost:8001/account

# Open positions
curl -H "X-API-KEY: $API_KEY" http://localhost:8001/positions

# Pending orders
curl -H "X-API-KEY: $API_KEY" http://localhost:8001/orders

# Tick price
curl -H "X-API-KEY: $API_KEY" http://localhost:8001/tick/V75

# Terminal info
curl -H "X-API-KEY: $API_KEY" http://localhost:8001/terminal
```

## Verify Phase 2: Management

```bash
# Close a position (replace TICKET with actual ticket number)
curl -X POST -H "X-API-KEY: $API_KEY" -H "Content-Type: application/json" \
  -d '{"ticket": TICKET}' \
  http://localhost:8001/close-position

# Modify SL/TP on a position
curl -X PUT -H "X-API-KEY: $API_KEY" -H "Content-Type: application/json" \
  -d '{"sl": 940.0, "tp": 970.0}' \
  http://localhost:8001/positions/TICKET/sltp

# Cancel a pending order
curl -X DELETE -H "X-API-KEY: $API_KEY" \
  http://localhost:8001/orders/TICKET
```

## Verify Phase 3: Execution

```bash
# Pre-validate an order
curl -X POST -H "X-API-KEY: $API_KEY" -H "Content-Type: application/json" \
  -d '{"ticker":"V75","type":"buy_limit","volume":0.01,"price":940.0}' \
  http://localhost:8001/order-check

# Place a pending order
curl -X POST -H "X-API-KEY: $API_KEY" -H "Content-Type: application/json" \
  -d '{"ticker":"V75","type":"buy_limit","volume":0.01,"price":940.0,"sl":930.0,"tp":960.0,"comment":"test"}' \
  http://localhost:8001/pending-order
```

## Verify Phase 4: History & Discovery

```bash
# Trade history (deals)
curl -H "X-API-KEY: $API_KEY" \
  "http://localhost:8001/history/deals?date_from=2026-03-01T00:00:00&date_to=2026-03-02T23:59:59"

# Historical orders
curl -H "X-API-KEY: $API_KEY" \
  "http://localhost:8001/history/orders?date_from=2026-03-01T00:00:00&date_to=2026-03-02T23:59:59"

# Broker symbols
curl -H "X-API-KEY: $API_KEY" \
  "http://localhost:8001/broker-symbols?group=Forex*"
```

## Run Tests

```bash
# All tests
pytest

# Specific suites
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
```

## Dashboard

Open `http://localhost:8001/dashboard` in a browser to access the HTML/JS dashboard with all new tabs.
