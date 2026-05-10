#!/usr/bin/env python3
"""Quick probe for the C++ batch preparation API."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "build-gpu"))
sys.path.insert(0, str(REPO_ROOT))

import ef_py
import time

# Create config
config = ef_py.StepEvaluationBatchConfig()
config.altitude_progress_weight = 0.1
config.speed_progress_weight = 0.1
config.crash_penalty = -1000.0
config.target_altitude_m = 1000.0
config.target_speed_mps = 100.0
config.target_heading_deg = 90.0
config.time_step_s = 0.05

# Create batch of env states
n_envs = 64
env_states = []
for i in range(n_envs):
    state = ef_py.StepEvaluationBatchEnvState()
    state.steps = i
    state.max_steps = 1000
    state.truncated = False
    state.truth_x = 1000.0 + i * 10.0
    state.truth_y = 2000.0
    state.truth_z = 500.0 + i * 5.0
    state.truth_vx = 50.0
    state.truth_vy = 50.0
    state.truth_vz = 1.0
    state.truth_speed = 70.7
    state.truth_pitch = 5.0
    state.truth_roll = 2.0
    state.truth_heading = 45.0
    state.truth_health = 100.0

    # Instrument vector (30+ elements)
    state.inst_vec = [70.0] * 35  # IAS, etc.
    state.inst_vec[0] = 70.0  # IAS
    state.inst_vec[3] = 500.0  # AGL
    state.inst_vec[5] = 3.0  # AOA
    state.inst_vec[8] = 2.0  # Roll
    state.inst_vec[10] = 1.05  # G
    state.inst_vec[18] = 0.0  # Gear

    # ILS vector
    state.ils_vec = [0.0, 0.0, 0.0, 0.0]

    state.liftoff_awarded = False
    state.gear_bonus_awarded = False
    state.prev_altitude_m = 495.0
    state.prev_ias_mps = 69.0

    env_states.append(state)

print(f"Testing batch preparation with {n_envs} environments...")

# Warmup
for _ in range(3):
    results = ef_py.prepare_step_evaluations_batch(config, env_states)

# Benchmark
n_iters = 100
t0 = time.perf_counter()
for _ in range(n_iters):
    results = ef_py.prepare_step_evaluations_batch(config, env_states)
elapsed = (time.perf_counter() - t0) * 1000.0 / n_iters

print(f"Batch preparation: {elapsed:.3f}ms for {n_envs} envs")
print(f"Per-env cost: {elapsed / n_envs:.3f}ms")
print(f"Results count: {len(results)}")
print(f"First result has_execution_step: {results[0].has_execution_step}")
print(f"First result has_flight_shaping: {results[0].has_flight_shaping}")

print("\nBatch API test passed!")
