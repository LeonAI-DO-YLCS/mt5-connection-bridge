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
API_KEY="${MT5_BRIDGE_API_KEY:-$(get_env MT5_BRIDGE_API_KEY)}"

if [[ -z "$API_KEY" ]]; then
  echo "MT5_BRIDGE_API_KEY is missing; cannot run smoke checks."
  exit 1
fi

BASE_URL="http://127.0.0.1:$PORT"
AUTH_HEADER="X-API-KEY: $API_KEY"

ALL_PASS="true"

check() {
  local path="$1"
  local response=""
  local err_msg=""
  
  if ! response="$(curl -sS --max-time 5 -D - -o /tmp/bridge-smoke-body.txt -H "$AUTH_HEADER" "$BASE_URL$path" 2>&1)"; then
    err_msg="$response"
  fi
  
  local status=""
  if [[ -z "$err_msg" ]]; then
    status="$(printf '%s' "$response" | awk '/^HTTP/{code=$2} END{print code}')"
  fi
  
  local error_code
  error_code="$(printf '%s' "$response" | awk -F': ' 'tolower($1)=="x-error-code"{gsub(/\r/,"",$2); print $2}' | tail -n1 | tr -d '\r\n')"
  
  if [[ -n "$err_msg" ]]; then
    echo "[FAIL] $path -> Connection Error: $err_msg"
    ALL_PASS="false"
  elif [[ "$status" == "200" ]]; then
    echo "[PASS] $path -> status=$status error_code=${error_code:-none}"
  else
    echo "[FAIL] $path -> status=$status error_code=${error_code:-none}"
    ALL_PASS="false"
  fi
}

check "/health"
check "/config"
check "/diagnostics/runtime"
check "/diagnostics/symbols"

if curl -sS --max-time 5 -H "$AUTH_HEADER" "$BASE_URL/diagnostics/runtime" -o /tmp/bridge-smoke-runtime.json 2>/dev/null; then
  python3 -c '
import json, sys
try:
    with open("/tmp/bridge-smoke-runtime.json") as f:
        d = json.load(f)
    print("")
    print("--- Runtime Summary ---")
    print("App Version       : %s" % d.get("app_version", "unknown"))
    print("MT5 Connected     : %s" % d.get("mt5_connected", False))
    print("Uptime (s)        : %.2f" % d.get("uptime_seconds", 0))
    print("Launcher Run ID   : %s" % (d.get("launcher_run_id") or "N/A"))
    print("-----------------------")
except Exception:
    pass
'
fi

if [[ "$ALL_PASS" != "true" ]]; then
  echo "Smoke check failed."
  exit 1
fi

