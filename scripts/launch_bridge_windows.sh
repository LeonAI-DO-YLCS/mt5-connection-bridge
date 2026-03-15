#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

LAUNCHER_PREFER_WINDOWS=true exec "$ROOT_DIR/scripts/launch_bridge_dashboard.sh" "$@"
