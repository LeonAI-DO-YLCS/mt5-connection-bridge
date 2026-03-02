# Quickstart — MT5 Bridge Verification Dashboard

## 1. What You Need To Know First (Plain English)

- The dashboard can open even when MT5 is not connected.
- MT5 connectivity only works when the bridge process is running on **Windows** with MT5 terminal running and logged in.
- If you run the bridge in Linux/WSL dashboard-only mode (`DISABLE_MT5_WORKER=true`), you will see: `MT5 terminal not connected`.

In short:
- **Windows** runs MT5 terminal + live bridge process.
- **WSL/Linux** is used for curl checks, tests, and the main app/backend.

## 2. Prerequisites

1. Windows machine with MetaTrader 5 installed.
2. MT5 terminal is open and logged into your broker account.
3. Python installed on Windows (3.11+ recommended).
4. Bridge project available at:
   - `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge`
5. `.env` file created from `.env.example`.

## 3. Required `.env` Values

Set these in `mt5-connection-bridge/.env`:

```env
MT5_BRIDGE_PORT=8001
MT5_BRIDGE_API_KEY=your-secret-key

MT5_LOGIN=12345678
MT5_PASSWORD=your-password
MT5_SERVER=Deriv-Demo
# MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe  # optional

EXECUTION_ENABLED=false
METRICS_RETENTION_DAYS=90
MULTI_TRADE_OVERLOAD_QUEUE_THRESHOLD=100
```

Important:
- `MT5_LOGIN=0` means not configured.
- Wrong login/password/server will keep bridge disconnected or unauthorized.

## 4. Install Dependencies

### 4.1 Linux/WSL (tests and local checks)

```bash
cd /home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r requirements-dev.txt
```

### 4.2 Windows Python (required for live MT5 bridge)

From WSL (adjust Python path if different):

```bash
cd /home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge
/mnt/c/Users/<YOUR_WINDOWS_USER>/AppData/Local/Programs/Python/Python312/python.exe -m pip install MetaTrader5
/mnt/c/Users/<YOUR_WINDOWS_USER>/AppData/Local/Programs/Python/Python312/python.exe -m pip install -r requirements.txt
```

## 5. Start The Live Bridge (Windows, Not WSL)

Run this from WSL (edit `<DISTRO_NAME>` and `<YOUR_WINDOWS_USER>`):

```bash
powershell.exe -NoProfile -Command '$wd="\\wsl.localhost\<DISTRO_NAME>\home\lnx-ubuntu-wsl\LeonAI_DO\dev\TRADING\ai-hedge-fund\mt5-connection-bridge"; $py="C:\Users\<YOUR_WINDOWS_USER>\AppData\Local\Programs\Python\Python312\python.exe"; $arg="-m uvicorn app.main:app --host 0.0.0.0 --port 8001"; $p=Start-Process -FilePath $py -ArgumentList $arg -WorkingDirectory $wd -WindowStyle Hidden -PassThru; Start-Sleep -Seconds 2; Write-Output ("PID=" + $p.Id); Get-NetTCPConnection -LocalPort 8001 -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess'
```

Expected result:
- A listener exists on port `8001`.
- The dashboard is reachable at `http://127.0.0.1:8001/dashboard/`.

## 6. Verify Connection State

Use API key from `.env`:

```bash
cd /home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge
MT5_BRIDGE_API_KEY=$(awk -F= '/^MT5_BRIDGE_API_KEY=/{print $2}' .env | tr -d '\r')
curl -s -H "X-API-KEY: ${MT5_BRIDGE_API_KEY}" "http://127.0.0.1:8001/health"
```

Expected healthy live output:
- `"connected": true`
- `"authorized": true`

If either is `false`:
- MT5 terminal is not running/logged in, or
- credentials/server in `.env` are wrong, or
- bridge was started in dashboard-only mode with `DISABLE_MT5_WORKER=true`.

## 7. Dashboard Verification Flow

1. Open `http://127.0.0.1:8001/dashboard/`.
2. Enter API key (`MT5_BRIDGE_API_KEY`).
3. Check `Status` tab:
   - Must show connected/authorized true for live MT5.
4. Check `Prices` tab:
   - Request a mapped symbol (for example `V75`) and validate non-empty response during market availability.
5. Check `Execute` tab:
   - With `EXECUTION_ENABLED=false`, execution is intentionally blocked (safety gate).

## 8. Useful API Smoke Checks

```bash
curl -s -H "X-API-KEY: ${MT5_BRIDGE_API_KEY}" "http://127.0.0.1:8001/symbols"
curl -s -H "X-API-KEY: ${MT5_BRIDGE_API_KEY}" "http://127.0.0.1:8001/config"
curl -s -H "X-API-KEY: ${MT5_BRIDGE_API_KEY}" "http://127.0.0.1:8001/worker/state"
curl -s -H "X-API-KEY: ${MT5_BRIDGE_API_KEY}" "http://127.0.0.1:8001/metrics"
curl -s -H "X-API-KEY: ${MT5_BRIDGE_API_KEY}" "http://127.0.0.1:8001/prices?ticker=V75&start_date=2026-01-01&end_date=2026-01-31&timeframe=D1"
```

## 9. Stop Bridge

```bash
powershell.exe -NoProfile -Command '$conn = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue; if ($conn) { Stop-Process -Id $conn.OwningProcess -Force; Write-Output ("STOPPED_PID=" + $conn.OwningProcess) } else { Write-Output "NO_LISTENER" }'
```

## 10. Failure Expectations

- `401`: missing/invalid API key.
- `404`: unknown ticker/symbol mapping.
- `422`: invalid payload/date/timeframe.
- `503`: MT5 disconnected/unavailable.
