#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
LOG_FILE="$ROOT_DIR/logs/bridge.out"

get_env() {
  local key="$1"
  if [[ -f "$ENV_FILE" ]]; then
    awk -F= -v key="$key" '$1==key {print substr($0, index($0, "=")+1); exit}' "$ENV_FILE"
  fi
}

PORT="${MT5_BRIDGE_PORT:-$(get_env MT5_BRIDGE_PORT)}"
PORT="${PORT:-8001}"

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

mkdir -p "$ROOT_DIR/logs"
cd "$ROOT_DIR"

if [[ "${1:-}" == "--background" ]]; then
  nohup "$PYTHON_BIN" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --no-use-colors --log-level info >"$LOG_FILE" 2>&1 &
  echo "Bridge started in background on :$PORT (pid=$!, log=$LOG_FILE)"
else
  exec "$PYTHON_BIN" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --no-use-colors --log-level info
fi

