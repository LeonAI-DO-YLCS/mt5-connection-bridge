# mt5-connection-bridge Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-02

## Active Technologies
- Python 3.11+, Bash (POSIX shell on WSL/Linux host) + FastAPI app (existing), uvicorn, MetaTrader5 runtime worker, existing bridge shell scripts (`start_bridge.sh`, `stop_bridge.sh`, `restart_bridge.sh`, `smoke_bridge.sh`) (007-bridge-launcher-inspector-logs)
- File-based logs in `logs/` (`metrics.jsonl`, `trades.jsonl`, and new run-scoped launcher bundles) (007-bridge-launcher-inspector-logs)

- Python 3.11+ + FastAPI, Uvicorn, MetaTrader5, Pydantic v2, pydantic-settings, NumPy, PyYAML (001-mt5-bridge-dashboard)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 007-bridge-launcher-inspector-logs: Added Python 3.11+, Bash (POSIX shell on WSL/Linux host) + FastAPI app (existing), uvicorn, MetaTrader5 runtime worker, existing bridge shell scripts (`start_bridge.sh`, `stop_bridge.sh`, `restart_bridge.sh`, `smoke_bridge.sh`)

- 001-mt5-bridge-dashboard: Added Python 3.11+ + FastAPI, Uvicorn, MetaTrader5, Pydantic v2, pydantic-settings, NumPy, PyYAML

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
