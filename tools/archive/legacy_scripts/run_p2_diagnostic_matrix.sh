#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <stageA_model.zip> <stageB_model.zip>"
  exit 1
fi

STAGE_A_MODEL="$1"
STAGE_B_MODEL="$2"

PY="/home/void0312/CMO/.venv/bin/python"

"$PY" tools/archive/diagnose_training_matrix.py \
  --algo AdaptiveKLPPO \
  --episodes 8 \
  --include_visual \
  --pair "$STAGE_A_MODEL" scenarios/cruise/cruise_waypoints_stresswind_rewardbalance_v1.json \
  --pair "$STAGE_B_MODEL" scenarios/cruise/cruise_waypoints_stresswind_rewardbalance_v1.json \
  --pair "$STAGE_A_MODEL" scenarios/stable_flight/stable_flight_stresswind.json \
  --pair "$STAGE_B_MODEL" scenarios/stable_flight/stable_flight_stresswind.json
