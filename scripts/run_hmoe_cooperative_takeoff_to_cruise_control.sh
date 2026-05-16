#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

source "${ROOT_DIR}/tools/maintenance/cmo_env.sh"
cmo_activate_env
PY="${PY:-${CMO_PYTHON}}"
OUTPUT_BASE="${OUTPUT_BASE:-experiments}"
TRAIN_SCENARIO="${TRAIN_SCENARIO:-scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json}"
EVAL_SCENARIO="${EVAL_SCENARIO:-${TRAIN_SCENARIO}}"

SHARED_CFG="${SHARED_CFG:-examples/config/training/active/cooperative_takeoff_to_cruise_nav_shared_fair_v1.json}"
HMOE_CFG="${HMOE_CFG:-examples/config/training/active/cooperative_takeoff_to_cruise_nav_hmoe_fair_v1.json}"

STAMP="$(date +%Y%m%d)"
SHARED_RUN_NAME="${SHARED_RUN_NAME:-${STAMP}_coop_takeoff_to_cruise_shared_fair_v1}"
HMOE_RUN_NAME="${HMOE_RUN_NAME:-${STAMP}_coop_takeoff_to_cruise_hmoe_fair_v1}"

TRAIN_SHARED="${TRAIN_SHARED:-1}"
TRAIN_HMOE="${TRAIN_HMOE:-1}"
EVAL_SHARED="${EVAL_SHARED:-1}"
EVAL_HMOE="${EVAL_HMOE:-1}"

SHARED_RESUME_PATH="${SHARED_RESUME_PATH:-}"
HMOE_RESUME_PATH="${HMOE_RESUME_PATH:-}"
SHARED_INIT_FROM="${SHARED_INIT_FROM:-}"
HMOE_INIT_FROM="${HMOE_INIT_FROM:-}"

EVAL_EPISODES="${EVAL_EPISODES:-12}"
EVAL_SEED="${EVAL_SEED:-200}"
CURRICULUM_STAGE="${CURRICULUM_STAGE:-2}"

SHARED_EVAL_JSON="${SHARED_EVAL_JSON:-output/${SHARED_RUN_NAME}_eval.json}"
HMOE_EVAL_JSON="${HMOE_EVAL_JSON:-output/${HMOE_RUN_NAME}_eval.json}"

mkdir -p "$(dirname "${SHARED_EVAL_JSON}")" "$(dirname "${HMOE_EVAL_JSON}")"

infer_model_path() {
  local resume_path="$1"
  local run_name="$2"
  if [[ -n "${resume_path}" ]]; then
    local abs_resume parent_dir
    abs_resume="$(cd "$(dirname "${resume_path}")" && pwd)/$(basename "${resume_path}")"
    parent_dir="$(dirname "${abs_resume}")"
    if [[ "$(basename "${parent_dir}")" == "checkpoints" ]]; then
      printf '%s/final_model.zip\n' "$(dirname "${parent_dir}")"
      return 0
    fi
    printf '%s/final_model.zip\n' "${parent_dir}"
    return 0
  fi
  printf '%s/%s/final_model.zip\n' "${OUTPUT_BASE}" "${run_name}"
}

run_train() {
  local label="$1"
  local scenario="$2"
  local config="$3"
  local run_name="$4"
  local resume_path="$5"
  local init_from="$6"

  local cmd=("${PY}" -u train.py --scenario "${scenario}" --train_config "${config}")
  if [[ -n "${resume_path}" ]]; then
    cmd+=(--resume_path "${resume_path}")
  else
    cmd+=(--run_name "${run_name}" --output_base "${OUTPUT_BASE}")
  fi
  if [[ -n "${init_from}" ]]; then
    cmd+=(--init_from "${init_from}")
  fi

  echo "[control] train ${label}"
  printf '  %q' "${cmd[@]}"
  printf '\n'
  "${cmd[@]}"
}

run_eval() {
  local label="$1"
  local scenario="$2"
  local config="$3"
  local model_path="$4"
  local json_out="$5"

  local cmd=(
    "${PY}" -u tools/eval/eval_sb3.py
    --mode cooperative
    --scenario "${scenario}"
    --train_config "${config}"
    --model "${model_path}"
    --episodes "${EVAL_EPISODES}"
    --seed "${EVAL_SEED}"
    --curriculum_stage "${CURRICULUM_STAGE}"
    --json_out "${json_out}"
  )

  echo "[control] eval ${label}"
  printf '  %q' "${cmd[@]}"
  printf '\n'
  "${cmd[@]}"
}

SHARED_MODEL_PATH="$(infer_model_path "${SHARED_RESUME_PATH}" "${SHARED_RUN_NAME}")"
HMOE_MODEL_PATH="$(infer_model_path "${HMOE_RESUME_PATH}" "${HMOE_RUN_NAME}")"

if [[ "${TRAIN_SHARED}" == "1" ]]; then
  run_train "shared" "${TRAIN_SCENARIO}" "${SHARED_CFG}" "${SHARED_RUN_NAME}" "${SHARED_RESUME_PATH}" "${SHARED_INIT_FROM}"
fi

if [[ "${TRAIN_HMOE}" == "1" ]]; then
  run_train "hmoe" "${TRAIN_SCENARIO}" "${HMOE_CFG}" "${HMOE_RUN_NAME}" "${HMOE_RESUME_PATH}" "${HMOE_INIT_FROM}"
fi

if [[ "${EVAL_SHARED}" == "1" ]]; then
  run_eval "shared" "${EVAL_SCENARIO}" "${SHARED_CFG}" "${SHARED_MODEL_PATH}" "${SHARED_EVAL_JSON}"
fi

if [[ "${EVAL_HMOE}" == "1" ]]; then
  run_eval "hmoe" "${EVAL_SCENARIO}" "${HMOE_CFG}" "${HMOE_MODEL_PATH}" "${HMOE_EVAL_JSON}"
fi

echo "[control] shared_eval_json=${SHARED_EVAL_JSON}"
echo "[control] hmoe_eval_json=${HMOE_EVAL_JSON}"
