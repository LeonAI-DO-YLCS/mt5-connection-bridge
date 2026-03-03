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

check() {
  local path="$1"
  local response
  response="$(curl -sS -D - -o /tmp/bridge-smoke-body.txt -H "$AUTH_HEADER" "$BASE_URL$path" || true)"
  local status
  status="$(printf '%s' "$response" | awk '/^HTTP/{code=$2} END{print code}')"
  local error_code
  error_code="$(printf '%s' "$response" | awk -F': ' 'tolower($1)=="x-error-code"{gsub(/\r/,"",$2); print $2}' | tail -n1)"
  echo "$path -> status=$status error_code=${error_code:-none}"
}

check "/health"
check "/config"
check "/diagnostics/runtime"
check "/diagnostics/symbols"

