#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
SCENARIO_PATH="${SCENARIO_PATH:-scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json}"
TICK_HZ="${TICK_HZ:-20}"
HOST_ADDR="${HOST_ADDR:-127.0.0.1}"
PORT_NUM="${PORT_NUM:-8765}"
ROUTE_PATH="${ROUTE_PATH:-/game}"

exec "$PYTHON_BIN" game/backend/app.py \
  --host "$HOST_ADDR" \
  --port "$PORT_NUM" \
  --route "$ROUTE_PATH" \
  --tick_hz "$TICK_HZ" \
  --scenario "$SCENARIO_PATH" \
  "$@"
