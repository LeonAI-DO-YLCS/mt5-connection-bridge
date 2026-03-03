#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${LAUNCHER_ENV_FILE:-$ROOT_DIR/.env}"
LOG_ROOT="${LAUNCHER_LOG_ROOT:-$ROOT_DIR/logs/bridge/launcher}"
HOST="${LAUNCHER_HOST:-0.0.0.0}"
RUN_ID="${LAUNCHER_RUN_ID:-$(date -u +%Y%m%d-%H%M%S)-$$}"
RUN_DIR="$LOG_ROOT/$RUN_ID"
LAUNCHER_LOG="$RUN_DIR/launcher.log"
STDOUT_LOG="$RUN_DIR/bridge.stdout.log"
STDERR_LOG="$RUN_DIR/bridge.stderr.log"
SESSION_JSON="$RUN_DIR/session.json"
BRIDGE_PID=""
TUI_PID=""
TUI_ALT_SCREEN=false

STOP_REQUESTED=0
RESTART_ATTEMPTED=false
RESTART_SUCCESSFUL=null
FINAL_EXIT_CODE=0
TERMINATION_REASON=""
STARTED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
ENDED_AT_UTC=""
RETENTION_UNTIL_UTC="$(python3 - <<'PY'
from datetime import datetime, timezone, timedelta
print((datetime.now(timezone.utc) + timedelta(days=90)).isoformat().replace('+00:00', 'Z'))
PY
)"
IS_WSL=false
if [[ -r /proc/version ]] && grep -qiE "(microsoft|wsl)" /proc/version; then
  IS_WSL=true
fi

get_env() {
  local key="$1"
  if [[ -f "$ENV_FILE" ]]; then
    awk -F= -v key="$key" '$1==key {print substr($0, index($0, "=")+1); exit}' "$ENV_FILE"
  fi
}

to_windows_path() {
  local linux_path="$1"
  if command -v wslpath >/dev/null 2>&1; then
    wslpath -w "$linux_path"
  else
    echo "$linux_path"
  fi
}

utc_now() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

init_colors() {
  if [[ -t 1 ]] && [[ -z "${NO_COLOR:-}" ]]; then
    C_RESET=$'\033[0m'
    C_HEADER=$'\033[1;36m'
    C_LABEL=$'\033[1;37m'
    C_OK=$'\033[1;32m'
    C_WARN=$'\033[1;33m'
    C_ERR=$'\033[1;31m'
    C_MUTED=$'\033[0;37m'
  fi
}

log_event() {
  local level="$1"
  local source="$2"
  shift 2
  local message="$*"
  local line="[$(utc_now)] [$level] [$source] $message"
  LAST_LAUNCHER_EVENT="$line"
  echo "$line" >>"$LAUNCHER_LOG"
  if [[ "$TUI_ENABLED" == "true" ]]; then
    return
  fi
  if [[ "$level" == "ERROR" ]]; then
    echo "$line" >&2
  else
    echo "$line"
  fi
}

write_session_metadata() {
  local ended="${1:-}"
  python3 - <<PY
import json
from pathlib import Path
restart_attempted = json.loads("${RESTART_ATTEMPTED}".lower())
restart_successful = json.loads("${RESTART_SUCCESSFUL}".lower())
payload = {
  "run_id": "${RUN_ID}",
  "started_at_utc": "${STARTED_AT_UTC}",
  "ended_at_utc": "${ended}",
  "host": "${HOST}",
  "port": ${PORT},
  "log_level": "${LOG_LEVEL}",
  "restart_attempted": restart_attempted,
  "restart_successful": restart_successful,
  "exit_code": ${FINAL_EXIT_CODE},
  "termination_reason": "${TERMINATION_REASON}",
  "retention_until_utc": "${RETENTION_UNTIL_UTC}",
  "bundle_root_path": "${RUN_DIR}",
  "launcher_log_path": "${LAUNCHER_LOG}",
  "stdout_log_path": "${STDOUT_LOG}",
  "stderr_log_path": "${STDERR_LOG}"
}
Path("${SESSION_JSON}").write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY
}

stop_windows_listener() {
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command "\$c=Get-NetTCPConnection -State Listen -LocalPort ${PORT} -ErrorAction SilentlyContinue; if(\$c){ \$c | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id \$_ -Force -ErrorAction SilentlyContinue } }" >/dev/null 2>&1 || true
  fi
}

stop_other_launchers() {
  local launchers
  launchers="$(pgrep -f "$ROOT_DIR/scripts/launch_bridge_dashboard.sh" || true)"
  for pid in $launchers; do
    if [[ "$pid" != "$$" ]]; then
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done
}

handle_signal() {
  STOP_REQUESTED=1
  if [[ -z "$TERMINATION_REASON" ]]; then
    TERMINATION_REASON="interrupted"
  fi
  log_event "WARN" "launcher" "Termination signal received; shutting down."
  if [[ -n "$BRIDGE_PID" ]] && kill -0 "$BRIDGE_PID" 2>/dev/null; then
    kill -TERM "$BRIDGE_PID" 2>/dev/null || true
  fi
  if [[ "${USE_WINDOWS_BRIDGE:-false}" == "true" ]]; then
    stop_windows_listener
  fi
  if [[ -n "$TUI_PID" ]] && kill -0 "$TUI_PID" 2>/dev/null; then
    kill -TERM "$TUI_PID" 2>/dev/null || true
  fi
}

trap handle_signal INT TERM

PORT="${MT5_BRIDGE_PORT:-$(get_env MT5_BRIDGE_PORT)}"
PORT="${PORT:-8001}"
LOG_LEVEL="${LOG_LEVEL:-$(get_env LOG_LEVEL)}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"
LOG_LEVEL="${LOG_LEVEL,,}"
API_KEY="${MT5_BRIDGE_API_KEY:-$(get_env MT5_BRIDGE_API_KEY)}"
PREFER_WINDOWS="${LAUNCHER_PREFER_WINDOWS:-$(get_env LAUNCHER_PREFER_WINDOWS)}"
PREFER_WINDOWS="${PREFER_WINDOWS:-true}"
WIN_PYTHON_EXE="${MT5_WINDOWS_PYTHON:-$(get_env MT5_WINDOWS_PYTHON)}"
USE_WINDOWS_BRIDGE=false
TUI_MODE="${LAUNCHER_TUI_MODE:-$(get_env LAUNCHER_TUI_MODE)}"
TUI_MODE="${TUI_MODE:-auto}"
TUI_ENABLED=false
TUI_REFRESH_SECONDS="${LAUNCHER_TUI_REFRESH_SECONDS:-$(get_env LAUNCHER_TUI_REFRESH_SECONDS)}"
TUI_REFRESH_SECONDS="${TUI_REFRESH_SECONDS:-1}"
TUI_PROBE_SECONDS="${LAUNCHER_TUI_PROBE_SECONDS:-$(get_env LAUNCHER_TUI_PROBE_SECONDS)}"
TUI_PROBE_SECONDS="${TUI_PROBE_SECONDS:-5}"
HEALTH_URL=""
DASHBOARD_URL=""
ACCESS_LOG="${LAUNCHER_UVICORN_ACCESS_LOG:-$(get_env LAUNCHER_UVICORN_ACCESS_LOG)}"
ACCESS_LOG="${ACCESS_LOG:-true}"
LAST_LAUNCHER_EVENT="n/a"
LAST_RUNTIME_ERROR="n/a"
LAST_TUI_FRAME=""
LAST_PROBE_EPOCH=0
LAST_HEALTH_AUTH="n/a"
LAST_HEALTH_PUBLIC="n/a"
LAST_DASHBOARD_CODE="n/a"
C_RESET=""
C_HEADER=""
C_LABEL=""
C_OK=""
C_WARN=""
C_ERR=""
C_MUTED=""

if [[ -z "$API_KEY" ]]; then
  echo "MT5_BRIDGE_API_KEY is required for authenticated launcher sessions." >&2
  exit 2
fi

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

if [[ "$IS_WSL" == "true" ]] \
  && [[ "${PREFER_WINDOWS,,}" == "true" ]] \
  && [[ -z "${LAUNCHER_BRIDGE_CMD:-}" ]] \
  && command -v powershell.exe >/dev/null 2>&1; then
  USE_WINDOWS_BRIDGE=true
fi

WIN_PS_SCRIPT_LINUX="$ROOT_DIR/scripts/windows/launch_bridge_windows.ps1"
WIN_PS_SCRIPT="$(to_windows_path "$WIN_PS_SCRIPT_LINUX")"
WIN_REPO_ROOT="$(to_windows_path "$ROOT_DIR")"
WIN_ENV_FILE="$(to_windows_path "$ENV_FILE")"

if [[ "$USE_WINDOWS_BRIDGE" == "true" ]] && [[ ! -f "$WIN_PS_SCRIPT_LINUX" ]]; then
  echo "Windows launcher script not found: $WIN_PS_SCRIPT_LINUX" >&2
  exit 3
fi

if [[ "$TUI_MODE" == "true" || "$TUI_MODE" == "false" ]]; then
  TUI_ENABLED="$TUI_MODE"
elif [[ -t 1 ]]; then
  TUI_ENABLED=true
fi

init_colors

mkdir -p "$RUN_DIR"
touch "$LAUNCHER_LOG" "$STDOUT_LOG" "$STDERR_LOG"

write_session_metadata ""

if [[ "${LAUNCHER_SKIP_PORT_CLEANUP:-false}" != "true" ]]; then
  stop_other_launchers
  sleep 1
  log_event "INFO" "launcher" "Preflight: clearing listeners on :${PORT} before startup."
  "$ROOT_DIR/scripts/stop_bridge.sh" >>"$LAUNCHER_LOG" 2>&1 || true
fi

log_event "INFO" "launcher" "Starting bridge launcher session run_id=${RUN_ID}"
log_event "INFO" "launcher" "Bridge endpoint: http://127.0.0.1:${PORT}"
log_event "INFO" "launcher" "Dashboard: http://127.0.0.1:${PORT}/dashboard/"
log_event "INFO" "launcher" "Log bundle: ${RUN_DIR}"
if [[ "$USE_WINDOWS_BRIDGE" == "true" ]]; then
  log_event "INFO" "launcher" "Runtime mode: windows-host bridge via WSL wrapper"
else
  log_event "INFO" "launcher" "Runtime mode: local shell runtime"
fi

HEALTH_URL="http://127.0.0.1:${PORT}/health"
DASHBOARD_URL="http://127.0.0.1:${PORT}/dashboard/"

probe_http_code() {
  local url="$1"
  local key="${2:-}"
  local code=""
  if command -v curl >/dev/null 2>&1; then
    if [[ -n "$key" ]]; then
      code="$(curl -s -m 2 -o /dev/null -w "%{http_code}" -H "X-API-Key: $key" "$url" || true)"
    else
      code="$(curl -s -m 2 -o /dev/null -w "%{http_code}" "$url" || true)"
    fi
  fi
  echo "${code:-n/a}"
}

sanitize_text() {
  local input="${1:-}"
  printf '%s' "$input" | tr -d '\r' | tr -cd '\11\12\15\40-\176'
}

truncate_text() {
  local text
  text="$(sanitize_text "${1:-}")"
  local max_len="${2:-92}"
  if ((${#text} > max_len)); then
    printf '%s...' "${text:0:max_len-3}"
  else
    printf '%s' "$text"
  fi
}

status_style() {
  local value="$1"
  case "$value" in
    200|RUNNING|READY) printf '%s%s%s' "$C_OK" "$value" "$C_RESET" ;;
    none) printf '%s%s%s' "$C_MUTED" "$value" "$C_RESET" ;;
    401|STARTING|NOT_STARTED|n/a|000) printf '%s%s%s' "$C_WARN" "$value" "$C_RESET" ;;
    *) printf '%s%s%s' "$C_ERR" "$value" "$C_RESET" ;;
  esac
}

get_listener_pid() {
  if [[ "$USE_WINDOWS_BRIDGE" == "true" ]] && command -v powershell.exe >/dev/null 2>&1; then
    local win_pid=""
    win_pid="$(powershell.exe -NoProfile -Command "(Get-NetTCPConnection -State Listen -LocalPort ${PORT} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -First 1)" 2>/dev/null | tr -d '\r' | tr -d '\n' || true)"
    echo "${win_pid:-n/a}"
    return
  fi

  local local_pid=""
  if command -v lsof >/dev/null 2>&1; then
    local_pid="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  fi
  echo "${local_pid:-n/a}"
}

extract_runtime_banner() {
  local value=""
  if [[ -f "$STDOUT_LOG" ]]; then
    value="$(grep -m1 -E '^\[windows-launcher\]|^INFO:\s+Uvicorn running on' "$STDOUT_LOG" 2>/dev/null || true)"
  fi
  if [[ -z "$value" ]] && [[ -f "$STDERR_LOG" ]]; then
    value="$(grep -m1 -E '^INFO:\s+Uvicorn running on|^INFO:\s+Started server process' "$STDERR_LOG" 2>/dev/null || true)"
  fi
  if [[ -z "$value" ]]; then
    value="waiting for runtime startup..."
  fi
  truncate_text "$value" 98
}

extract_last_runtime_error() {
  local value="none"
  if [[ -f "$STDERR_LOG" ]]; then
    value="$(grep -E 'ERROR|CRITICAL|Traceback|Exception' "$STDERR_LOG" | tail -n 1 || true)"
  fi
  if [[ -z "$value" ]]; then
    value="none"
  fi
  LAST_RUNTIME_ERROR="$(truncate_text "$value" 98)"
}

probe_endpoints_if_due() {
  local now_epoch
  now_epoch="$(date +%s)"
  if (( now_epoch - LAST_PROBE_EPOCH < TUI_PROBE_SECONDS )); then
    return
  fi
  LAST_PROBE_EPOCH="$now_epoch"
  LAST_HEALTH_AUTH="$(probe_http_code "$HEALTH_URL" "$API_KEY")"
  LAST_HEALTH_PUBLIC="$(probe_http_code "$HEALTH_URL")"
  LAST_DASHBOARD_CODE="$(probe_http_code "$DASHBOARD_URL")"
}

render_tui_frame() {
  local runtime_mode
  local runtime_proc_desc
  if [[ -n "${LAUNCHER_BRIDGE_CMD:-}" ]]; then
    runtime_mode="custom-cmd"
    runtime_proc_desc="bash -lc custom command"
  elif [[ "$USE_WINDOWS_BRIDGE" == "true" ]]; then
    runtime_mode="windows-host"
    runtime_proc_desc="powershell.exe -> python -m uvicorn"
  else
    runtime_mode="local-shell"
    runtime_proc_desc="python -m uvicorn"
  fi

  local runtime_status="NOT_STARTED"
  local runtime_pid="${BRIDGE_PID:-n/a}"
  if [[ -n "$BRIDGE_PID" ]]; then
    if kill -0 "$BRIDGE_PID" 2>/dev/null; then
      runtime_status="RUNNING"
    else
      runtime_status="EXITED"
    fi
  fi

  local listener_pid
  listener_pid="$(get_listener_pid)"
  local runtime_banner
  runtime_banner="$(extract_runtime_banner)"
  extract_last_runtime_error
  probe_endpoints_if_due

  local state_summary="STARTING"
  if [[ "$LAST_HEALTH_AUTH" == "200" && "$LAST_DASHBOARD_CODE" == "200" ]]; then
    state_summary="READY"
  fi

  cat <<EOF
${C_HEADER}================================================================================================================${C_RESET}
${C_HEADER} MT5 Bridge Launcher Control Panel                                                                                     ${C_RESET}
${C_HEADER}================================================================================================================${C_RESET}
${C_LABEL} Session${C_RESET}
   Run ID                : ${RUN_ID}
   Runtime Mode          : ${runtime_mode}
   Runtime Chain         : ${runtime_proc_desc}
   Overall State         : $(status_style "$state_summary")

${C_LABEL} Processes${C_RESET}
   Launcher PID          : $$ ($(status_style "RUNNING"))
   Runtime PID           : ${runtime_pid} ($(status_style "$runtime_status"))
   Listener PID          : ${listener_pid}
   Probe Interval        : ${TUI_PROBE_SECONDS}s

${C_LABEL} Endpoints${C_RESET}
   API /health (auth)    : $(status_style "$LAST_HEALTH_AUTH")   ${C_MUTED}${HEALTH_URL}${C_RESET}
   API /health (anon)    : $(status_style "$LAST_HEALTH_PUBLIC")   ${C_MUTED}(expected 401)${C_RESET}
   Dashboard             : $(status_style "$LAST_DASHBOARD_CODE")   ${C_MUTED}${DASHBOARD_URL}${C_RESET}

${C_LABEL} Diagnostics${C_RESET}
   Runtime Banner        : ${runtime_banner}
   Last Runtime Error    : $(status_style "$LAST_RUNTIME_ERROR")
   Last Launcher Event   : $(truncate_text "$LAST_LAUNCHER_EVENT" 98)

${C_LABEL} Artifacts${C_RESET}
   Logs Directory        : ${RUN_DIR}
   Session Metadata      : ${SESSION_JSON}

${C_MUTED} Keys: Ctrl+C stops launcher and bridge. Logs remain in files under logs/bridge/launcher/<run-id>/.${C_RESET}
EOF
}

render_tui() {
  while true; do
    if [[ "$STOP_REQUESTED" -eq 1 ]]; then
      break
    fi
    local frame=""
    frame="$(render_tui_frame)"
    if [[ "$frame" != "$LAST_TUI_FRAME" ]]; then
      printf '\033[H\033[2J%s\n' "$frame"
      LAST_TUI_FRAME="$frame"
    fi
    sleep "$TUI_REFRESH_SECONDS"
  done
}

start_tui() {
  if [[ "$TUI_ENABLED" != "true" ]]; then
    return
  fi
  if command -v tput >/dev/null 2>&1; then
    tput smcup 2>/dev/null || true
    tput civis 2>/dev/null || true
    TUI_ALT_SCREEN=true
  fi
  render_tui &
  TUI_PID=$!
}

stop_tui() {
  if [[ -n "$TUI_PID" ]] && kill -0 "$TUI_PID" 2>/dev/null; then
    kill -TERM "$TUI_PID" 2>/dev/null || true
    wait "$TUI_PID" 2>/dev/null || true
    TUI_PID=""
  fi
  if [[ "$TUI_ALT_SCREEN" == "true" ]] && command -v tput >/dev/null 2>&1; then
    tput cnorm 2>/dev/null || true
    tput rmcup 2>/dev/null || true
    TUI_ALT_SCREEN=false
  fi
}

run_bridge_once() {
  local attempt="$1"
  log_event "INFO" "runtime" "Starting runtime attempt ${attempt}."

  cd "$ROOT_DIR"
  local rc=0
  if [[ -n "${LAUNCHER_BRIDGE_CMD:-}" ]]; then
    set +e
    if [[ "$TUI_ENABLED" == "true" ]]; then
      bash -lc "$LAUNCHER_BRIDGE_CMD" \
        > >(tee -a "$STDOUT_LOG" "$LAUNCHER_LOG" >/dev/null) \
        2> >(tee -a "$STDERR_LOG" "$LAUNCHER_LOG" >/dev/null) &
    else
      bash -lc "$LAUNCHER_BRIDGE_CMD" \
        > >(tee -a "$STDOUT_LOG" "$LAUNCHER_LOG") \
        2> >(tee -a "$STDERR_LOG" "$LAUNCHER_LOG" >&2) &
    fi
    BRIDGE_PID=$!
    wait "$BRIDGE_PID"
    rc=$?
    BRIDGE_PID=""
    set -e
  elif [[ "$USE_WINDOWS_BRIDGE" == "true" ]]; then
    local ps_args=(
      -NoProfile
      -ExecutionPolicy Bypass
      -File "$WIN_PS_SCRIPT"
      -RepoRoot "$WIN_REPO_ROOT"
      -EnvFile "$WIN_ENV_FILE"
      -Port "$PORT"
      -LogLevel "$LOG_LEVEL"
      -AccessLogEnabled "${ACCESS_LOG,,}"
    )
    if [[ -n "$WIN_PYTHON_EXE" ]]; then
      ps_args+=(-PythonExe "$WIN_PYTHON_EXE")
    fi

    set +e
    if [[ "$TUI_ENABLED" == "true" ]]; then
      powershell.exe "${ps_args[@]}" \
        > >(tee -a "$STDOUT_LOG" "$LAUNCHER_LOG" >/dev/null) \
        2> >(tee -a "$STDERR_LOG" "$LAUNCHER_LOG" >/dev/null) &
    else
      powershell.exe "${ps_args[@]}" \
        > >(tee -a "$STDOUT_LOG" "$LAUNCHER_LOG") \
        2> >(tee -a "$STDERR_LOG" "$LAUNCHER_LOG" >&2) &
    fi
    BRIDGE_PID=$!
    wait "$BRIDGE_PID"
    rc=$?
    BRIDGE_PID=""
    set -e
  else
    local uvicorn_args=(
      -m uvicorn app.main:app
      --host "$HOST"
      --port "$PORT"
      --no-use-colors
      --log-level "$LOG_LEVEL"
    )
    if [[ "${ACCESS_LOG,,}" != "true" ]]; then
      uvicorn_args+=(--no-access-log)
    fi

    set +e
    if [[ "$TUI_ENABLED" == "true" ]]; then
      "$PYTHON_BIN" "${uvicorn_args[@]}" \
        > >(tee -a "$STDOUT_LOG" "$LAUNCHER_LOG" >/dev/null) \
        2> >(tee -a "$STDERR_LOG" "$LAUNCHER_LOG" >/dev/null) &
    else
      "$PYTHON_BIN" "${uvicorn_args[@]}" \
        > >(tee -a "$STDOUT_LOG" "$LAUNCHER_LOG") \
        2> >(tee -a "$STDERR_LOG" "$LAUNCHER_LOG" >&2) &
    fi
    BRIDGE_PID=$!
    wait "$BRIDGE_PID"
    rc=$?
    BRIDGE_PID=""
    set -e
  fi

  log_event "WARN" "runtime" "Runtime attempt ${attempt} exited with code ${rc}."
  return "$rc"
}

start_tui

if run_bridge_once 1; then
  FINAL_EXIT_CODE=0
  if [[ "$STOP_REQUESTED" -eq 1 ]]; then
    TERMINATION_REASON="interrupted"
  else
    TERMINATION_REASON="completed"
  fi
else
  first_rc=$?
  if [[ "$STOP_REQUESTED" -eq 1 ]]; then
    FINAL_EXIT_CODE="$first_rc"
    TERMINATION_REASON="interrupted"
  else
    RESTART_ATTEMPTED=true
    log_event "WARN" "launcher" "Runtime exited unexpectedly. Attempting one automatic restart."

    if run_bridge_once 2; then
      RESTART_SUCCESSFUL=true
      FINAL_EXIT_CODE=0
      TERMINATION_REASON="recovered_after_restart"
    else
      second_rc=$?
      if [[ "$STOP_REQUESTED" -eq 1 ]]; then
        RESTART_SUCCESSFUL=false
        FINAL_EXIT_CODE="$second_rc"
        TERMINATION_REASON="interrupted"
      else
        RESTART_SUCCESSFUL=false
        FINAL_EXIT_CODE="$second_rc"
        TERMINATION_REASON="failed_after_restart"
        log_event "ERROR" "launcher" "Restart attempt failed; exiting non-success."
      fi
    fi
  fi
fi

stop_tui
ENDED_AT_UTC="$(utc_now)"
write_session_metadata "$ENDED_AT_UTC"

log_event "INFO" "launcher" "Session ended with exit_code=${FINAL_EXIT_CODE} reason=${TERMINATION_REASON}"
exit "$FINAL_EXIT_CODE"
