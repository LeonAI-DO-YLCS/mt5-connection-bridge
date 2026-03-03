# Quickstart: Bridge Launcher Inspector Logging

## Prerequisites

1. Repository: `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge`
2. Environment configured in `.env` (`MT5_BRIDGE_PORT`, `MT5_BRIDGE_API_KEY`, MT5 settings)
3. Python dependencies installed from `requirements.txt`

## 1. Start Launcher Session

```bash
cd /home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/mt5-connection-bridge
./scripts/launch_bridge_dashboard.sh
```

Expected checks:
- terminal shows service endpoint and dashboard URL
- terminal shows run log bundle paths
- API and dashboard are reachable
- stop the session with `Ctrl+C` when validation is complete

## 2. Validate Authentication Gate

From another shell, run an unauthenticated request:

```bash
curl -i "http://127.0.0.1:${MT5_BRIDGE_PORT:-8001}/health"
```

Expected checks:
- request denied by auth policy
- auth failure appears in terminal/log bundle

## 3. Validate Successful Authenticated Request

```bash
curl -i -H "X-API-KEY: ${MT5_BRIDGE_API_KEY}" "http://127.0.0.1:${MT5_BRIDGE_PORT:-8001}/health"
```

Expected checks:
- successful response
- request telemetry captured in existing metrics/audit surfaces

## 4. Validate Crash-Restart Policy

1. Trigger runtime crash scenario (controlled local test).
2. Observe one automatic restart attempt.
3. If restart fails, confirm non-success launcher exit.

Expected checks:
- exactly one restart attempt is logged
- both failure events are recorded on restart failure

## 5. Validate Log Bundle Structure

```bash
find logs/launcher -maxdepth 2 -type f | sort
```

Expected checks for each run-id bundle:
- `launcher.log`
- `bridge.stdout.log`
- `bridge.stderr.log`
- `session.json`

## 6. Validate Compatibility of Existing Scripts

```bash
./scripts/start_bridge.sh --background
./scripts/smoke_bridge.sh
./scripts/stop_bridge.sh
```

Expected checks:
- existing script behavior remains unchanged
- no regression introduced by launcher feature

## 7. Validate 90-Day Retention Policy

Retention verification checks:
1. New bundles include metadata/timestamps sufficient to compute 90-day retention window.
2. Bundles remain available for retrieval during acceptance window.
3. Cleanup eligibility starts only after 90 days.
