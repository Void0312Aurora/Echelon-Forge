#!/usr/bin/env bash
set -euo pipefail

# Cruise waypoint training pipeline (realism-first, full action + full observation).
#
# This script:
#  1) collects scripted waypoint demonstrations
#  2) BC-finetunes the actor starting from a stable-flight checkpoint (WM frozen)
#  3) collects DAgger episodes (student executes, scripted labels) to reduce covariate shift
#  4) BC-finetunes again on the appended dataset
#  5) evaluates and prints success metrics
#
# Requirements:
#  - run from repo root
#  - use the in-repo venv: `./.venv/bin/python`

PY="${PY:-./.venv/bin/python}"
PY_ARGS=(-u)

SCENARIO="${SCENARIO:-scenarios/cruise/cruise_waypoints_stresswind_rewardbalance_v1.json}"

# Base checkpoint: a stable-flight world-model policy trained with full action + ARB visual + proprio.
BASE_CKPT="${BASE_CKPT:-experiments/wm_stable_flight_full_visual_proprio_offline_bc_v28_mixv4_dagger_ft_thr10/checkpoint.pt}"

DATASET_DIR="${DATASET_DIR:-datasets/cruise_waypoints_full_visual_proprio_v1}"
RUN_DIR_STAGE1="${RUN_DIR_STAGE1:-experiments/wm_cruise_waypoints_full_visual_proprio_bc_v1}"
RUN_DIR_STAGE2="${RUN_DIR_STAGE2:-experiments/wm_cruise_waypoints_full_visual_proprio_bc_dagger_v1}"

# Data collection knobs
VIS_DOWNSAMPLE="${VIS_DOWNSAMPLE:-4}"   # must match BASE_CKPT visual_shape (48x96 -> 12x24)
EPISODES_SCRIPTED="${EPISODES_SCRIPTED:-20}"
EPISODES_DAGGER="${EPISODES_DAGGER:-20}"
SEED_SCRIPTED="${SEED_SCRIPTED:-100}"
SEED_DAGGER="${SEED_DAGGER:-1000}"

# Training knobs
DEVICE_TRAIN="${DEVICE_TRAIN:-auto}"
DEVICE_DAGGER="${DEVICE_DAGGER:-auto}"
STEPS_STAGE1="${STEPS_STAGE1:-3000}"
STEPS_STAGE2="${STEPS_STAGE2:-3000}"
BATCH_SIZE="${BATCH_SIZE:-16}"
SEQ_LEN="${SEQ_LEN:-64}"

_auto_device() {
  # Pick a sane default device without crashing on busy GPUs.
  #
  # - Prefer CUDA when available and there is enough free memory.
  # - Fall back to CPU otherwise.
  local want="${1:-auto}"
  local min_free_mib="${2:-4096}"
  if [[ "${want}" != "auto" ]]; then
    echo "${want}"
    return 0
  fi
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "cpu"
    return 0
  fi
  local free_mib
  free_mib="$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -n1 | tr -d ' ')"
  if [[ -z "${free_mib}" ]]; then
    echo "cpu"
    return 0
  fi
  if (( free_mib >= min_free_mib )); then
    echo "cuda"
  else
    echo "cpu"
  fi
}

DEVICE_TRAIN="$(_auto_device "${DEVICE_TRAIN}" 8192)"
DEVICE_DAGGER="$(_auto_device "${DEVICE_DAGGER}" 2048)"

echo "[pipeline] scenario: ${SCENARIO}"
echo "[pipeline] base_ckpt: ${BASE_CKPT}"
echo "[pipeline] dataset:  ${DATASET_DIR}"
echo "[pipeline] run1:     ${RUN_DIR_STAGE1}"
echo "[pipeline] run2:     ${RUN_DIR_STAGE2}"
echo "[pipeline] device_train: ${DEVICE_TRAIN}  device_dagger: ${DEVICE_DAGGER}"

echo "[pipeline] (1/5) collect scripted waypoint demos..."
"${PY}" "${PY_ARGS[@]}" world_model_train.py collect \
  --scenario "${SCENARIO}" \
  --out_dir "${DATASET_DIR}" \
  --episodes "${EPISODES_SCRIPTED}" \
  --seed "${SEED_SCRIPTED}" \
  --action_mode full \
  --policy scripted_waypoint \
  --include_visual \
  --include_proprio \
  --visual_downsample "${VIS_DOWNSAMPLE}"

echo "[pipeline] (2/5) BC finetune actor (freeze WM)..."
"${PY}" "${PY_ARGS[@]}" world_model_train.py train \
  --dataset_dir "${DATASET_DIR}" \
  --run_dir "${RUN_DIR_STAGE1}" \
  --checkpoint "${BASE_CKPT}" \
  --skip_wm \
  --train_policy \
  --policy_mode bc \
  --actor_input obs_sincos_track_vis \
  --steps "${STEPS_STAGE1}" \
  --device "${DEVICE_TRAIN}" \
  --batch_size "${BATCH_SIZE}" \
  --seq_len "${SEQ_LEN}" \
  --bc_scale 1.0 \
  --bc_hdg_weight 1.0 \
  --bc_hdg_norm_deg 45.0 \
  --log_compact \
  --log_every 50 \
  --save_every 500

echo "[pipeline] (3/5) collect DAgger episodes (student executes, scripted labels)..."
"${PY}" "${PY_ARGS[@]}" world_model_train.py collect \
  --scenario "${SCENARIO}" \
  --out_dir "${DATASET_DIR}" \
  --episodes "${EPISODES_DAGGER}" \
  --seed "${SEED_DAGGER}" \
  --action_mode full \
  --policy dagger_scripted_waypoint \
  --student_checkpoint "${RUN_DIR_STAGE1}/checkpoint.pt" \
  --device "${DEVICE_DAGGER}" \
  --dagger_teacher_prob 0.0 \
  --include_visual \
  --include_proprio \
  --visual_downsample "${VIS_DOWNSAMPLE}"

echo "[pipeline] (4/5) BC finetune actor on appended dataset..."
"${PY}" "${PY_ARGS[@]}" world_model_train.py train \
  --dataset_dir "${DATASET_DIR}" \
  --run_dir "${RUN_DIR_STAGE2}" \
  --checkpoint "${RUN_DIR_STAGE1}/checkpoint.pt" \
  --skip_wm \
  --train_policy \
  --policy_mode bc \
  --actor_input obs_sincos_track_vis \
  --steps "${STEPS_STAGE2}" \
  --device "${DEVICE_TRAIN}" \
  --batch_size "${BATCH_SIZE}" \
  --seq_len "${SEQ_LEN}" \
  --bc_scale 1.0 \
  --bc_hdg_weight 1.0 \
  --bc_hdg_norm_deg 45.0 \
  --log_compact \
  --log_every 50 \
  --save_every 500

echo "[pipeline] (5/5) evaluate waypoint success..."
"${PY}" "${PY_ARGS[@]}" tools/eval_waypoint_nav.py \
  --scenario "${SCENARIO}" \
  --checkpoint "${RUN_DIR_STAGE2}/checkpoint.pt" \
  --episodes 5 \
  --max_steps 6000 \
  --seed 200 \
  --device cpu \
  --action_mode full \
  --include_visual \
  --include_proprio

echo "[pipeline] done."
