#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PY="${PY:-./.venv/bin/python}"
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

detect_build_dir() {
  local candidate
  for candidate in \
    "${CMO_BUILD_DIR:-}" \
    "build-workshop" \
    "build-gpu" \
    "build" \
    "build-facade-local"
  do
    [[ -n "${candidate}" ]] || continue
    if [[ -d "${candidate}" ]] && compgen -G "${candidate}/ef_py*.so" >/dev/null; then
      printf '%s\n' "${candidate}"
      return 0
    fi
    if [[ -d "${candidate}" && -e "${candidate}/ef_py" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

BUILD_DIR="$(detect_build_dir || true)"
if [[ -n "${BUILD_DIR}" ]]; then
  export CMO_BUILD_DIR="${BUILD_DIR}"
  export PYTHONPATH="${ROOT_DIR}/${BUILD_DIR}:${ROOT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"
fi

mkdir -p "${OUT_DIR}"

run_eval() {
  local label="$1"
  local model_path="$2"
  local json_out="$3"
  local cmd=(
    "${PY}" -u tools/eval/eval_sb3_cooperative_policy.py
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
