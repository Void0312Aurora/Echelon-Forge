#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Avoid CPU over-subscription when using many Subproc env workers.
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# P2 decoupling and rotational/integration limits (aggressive but stable defaults).
export CMO_FBW_PROTECTION_MODE=relaxed
export CMO_ROT_MAX_RATE_CROSS_RAD_S=60
export CMO_ROT_MAX_TORQUE_NM=7000000
export CMO_ROT_MAX_ANG_ACCEL_RAD_S2=12000
export CMO_ROT_MAX_RATE_RAD_S=7
export CMO_ROT_SINGULARITY_MIN_PITCH_DEG=88
export CMO_ROT_PITCH_LIMIT_DEG=89

# Stage A: stable flight under stress wind, visual + proprio.
/home/void0312/CMO/.venv/bin/python train.py \
  --scenario scenarios/stable_flight/stable_flight_stresswind.json \
  --train_config examples/config/training/p2_aggressive_adaptivekl_3090.json \
  --include_visual \
  --diagnostics \
  --diagnostics_every 50000 \
  --run_name p2_aggressive_stable_3090

# Stage B: waypoint cruise fine-tune from stable model.
/home/void0312/CMO/.venv/bin/python train.py \
  --scenario scenarios/cruise/cruise_waypoints_stresswind_rewardbalance_v1.json \
  --train_config examples/config/training/p2_aggressive_adaptivekl_3090.json \
  --include_visual \
  --diagnostics \
  --diagnostics_every 50000 \
  --resume_path experiments/p2_aggressive_stable_3090/final_model.zip \
  --run_name p2_aggressive_cruise_3090
