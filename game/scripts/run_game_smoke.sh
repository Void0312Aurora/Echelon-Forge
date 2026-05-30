#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
GODOT_BIN="${GODOT_BIN:-$HOME/.local/bin/godot}"
HOST_ADDR="${HOST_ADDR:-127.0.0.1}"
PORT_NUM="${PORT_NUM:-8876}"
ROLE_NAME="${ROLE_NAME:-Lead}"
TICK_HZ="${TICK_HZ:-20}"
AUTOMATION_DELAY="${AUTOMATION_DELAY:-2.0}"
REPORT_PATH="${REPORT_PATH:-/tmp/cmo_game_smoke_report.json}"
BACKEND_LOG="${BACKEND_LOG:-/tmp/cmo_game_smoke_backend.log}"
GODOT_LOG="${GODOT_LOG:-/tmp/cmo_game_smoke_godot.log}"
SCREENSHOT_PATH="${SCREENSHOT_PATH:-/tmp/cmo_game_smoke_screen.png}"
WORLD_SCREENSHOT_PATH="${WORLD_SCREENSHOT_PATH:-/tmp/cmo_game_smoke_world.png}"
SCENARIO_PATH="${SCENARIO_PATH:-scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json}"
ORIENTATION_CHECK_LOG="${ORIENTATION_CHECK_LOG:-/tmp/cmo_game_f16_orientation_check.json}"

cleanup() {
  local exit_code=$?
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
  exit "$exit_code"
}
trap cleanup EXIT

rm -f "$REPORT_PATH" "$BACKEND_LOG" "$GODOT_LOG" "$SCREENSHOT_PATH" "$WORLD_SCREENSHOT_PATH" "$ORIENTATION_CHECK_LOG"

if ! "$GODOT_BIN" --path game/client/godot_project --headless --script "$ROOT_DIR/game/scripts/check_f16_orientation.gd" >"$ORIENTATION_CHECK_LOG" 2>&1; then
  echo "F-16 orientation check failed. See $ORIENTATION_CHECK_LOG" >&2
  cat "$ORIENTATION_CHECK_LOG" >&2 || true
  exit 1
fi

"$PYTHON_BIN" game/backend/app.py \
  --host "$HOST_ADDR" \
  --port "$PORT_NUM" \
  --route /game \
  --tick_hz "$TICK_HZ" \
  --scenario "$SCENARIO_PATH" \
  >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

for _ in $(seq 1 50); do
  if "$PYTHON_BIN" - <<PY >/dev/null 2>&1
import socket
s = socket.socket()
try:
    s.connect(("$HOST_ADDR", int("$PORT_NUM")))
finally:
    s.close()
PY
  then
    break
  fi
  sleep 0.2
done

if ! "$PYTHON_BIN" - <<PY >/dev/null 2>&1
import socket, sys
s = socket.socket()
try:
    s.connect(("$HOST_ADDR", int("$PORT_NUM")))
except OSError:
    sys.exit(1)
finally:
    s.close()
PY
then
  echo "Backend failed to start. See $BACKEND_LOG" >&2
  exit 1
fi

CMO_GAME_AUTOMATION=1 \
CMO_GAME_AUTOMATION_ROLE="$ROLE_NAME" \
CMO_GAME_AUTOMATION_DELAY="$AUTOMATION_DELAY" \
CMO_GAME_AUTOMATION_REPORT="$REPORT_PATH" \
CMO_GAME_AUTOMATION_BACKEND_URL="ws://$HOST_ADDR:$PORT_NUM/game" \
CMO_GAME_AUTOMATION_SCREENSHOT="$SCREENSHOT_PATH" \
CMO_GAME_AUTOMATION_WORLD_SCREENSHOT="$WORLD_SCREENSHOT_PATH" \
xvfb-run -a "$GODOT_BIN" \
  --path game/client/godot_project \
  --verbose \
  --log-file "$GODOT_LOG" \
  >/dev/null 2>&1

if [[ ! -f "$REPORT_PATH" ]]; then
  echo "Smoke report missing. See $GODOT_LOG" >&2
  exit 1
fi

"$PYTHON_BIN" - <<PY
import json, sys
from pathlib import Path

report = json.loads(Path("$REPORT_PATH").read_text())
print(json.dumps(report, ensure_ascii=False, indent=2))
if not report.get("pass", False):
    sys.exit(1)
PY
