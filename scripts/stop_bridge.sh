#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"

get_env() {
  local key="$1"
  if [[ -f "$ENV_FILE" ]]; then
    awk -F= -v key="$key" '$1==key {print substr($0, index($0, "=")+1); exit}' "$ENV_FILE"
  fi
}

PORT="${MT5_BRIDGE_PORT:-$(get_env MT5_BRIDGE_PORT)}"
PORT="${PORT:-8001}"

echo "Stopping bridge listeners on :$PORT"

if command -v lsof >/dev/null 2>&1; then
  linux_pids="$(lsof -t -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | tr '\n' ' ' || true)"
  if [[ -n "${linux_pids// }" ]]; then
    kill -9 $linux_pids || true
    echo "Stopped Linux listener pid(s): $linux_pids"
  fi
fi

if command -v powershell.exe >/dev/null 2>&1; then
  powershell.exe -NoProfile -Command "\$c=Get-NetTCPConnection -State Listen -LocalPort $PORT -ErrorAction SilentlyContinue; if(\$c){ \$c | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id \$_ -Force -ErrorAction SilentlyContinue; Write-Output \"Stopped Windows PID \$_\" } } else { Write-Output \"No Windows listener on port $PORT\" }" >/dev/null || true
fi

echo "Stop command completed."

