#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

source "${ROOT_DIR}/tools/maintenance/cmo_env.sh"
cmo_activate_env
PY="${PY:-${CMO_PYTHON}}"
SCENARIO="${SCENARIO:-scenarios/combined/cooperative_takeoff_to_cruise_landing_continuous_train_v1.json}"
TRAIN_CONFIG="${TRAIN_CONFIG:-examples/config/training/active/cooperative_takeoff_to_cruise_landing_hmoe_v1.json}"

SHARED_MODEL="${SHARED_MODEL:-experiments/coop_takeoff_to_cruise_landing_formal_20260514/final_model.zip}"
HMOE_MODEL="${HMOE_MODEL:-experiments/20260515_coop_takeoff_to_cruise_landing_hmoe_probe_fix_v1/checkpoints/model_130048_steps.zip}"

CURRICULUM_STAGE="${CURRICULUM_STAGE:-2}"
EPISODES="${EPISODES:-1}"
SEED="${SEED:-20260515}"
DEVICE="${DEVICE:-cuda}"
OUT_DIR="${OUT_DIR:-experiments/strict_terminal_eval_$(date +%Y%m%d)}"
DRY_RUN="${DRY_RUN:-0}"

mkdir -p "${OUT_DIR}"

run_eval() {
  local label="$1"
  local model_path="$2"
  local json_out="$3"
  local cmd=(
    "${PY}" -u tools/eval/eval_sb3.py
    --mode cooperative
    --scenario "${SCENARIO}"
    --train_config "${TRAIN_CONFIG}"
    --model "${model_path}"
    --episodes "${EPISODES}"
    --seed "${SEED}"
    --device "${DEVICE}"
    --curriculum_stage "${CURRICULUM_STAGE}"
    --json_out "${json_out}"
  )

  echo "[strict-terminal] ${label}"
  printf '  %q' "${cmd[@]}"
  printf '\n'

  if [[ "${DRY_RUN}" == "1" ]]; then
    return 0
  fi
  "${cmd[@]}"
}

run_eval "shared" "${SHARED_MODEL}" "${OUT_DIR}/shared_final_stage2_ep${EPISODES}.json"
run_eval "hmoe" "${HMOE_MODEL}" "${OUT_DIR}/hmoe_130048_stage2_ep${EPISODES}.json"

echo "[strict-terminal] out_dir=${OUT_DIR}"
