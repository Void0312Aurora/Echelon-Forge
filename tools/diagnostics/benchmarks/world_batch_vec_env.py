#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "..", ".."))
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from python.env_config import (
    ACTION_MODES,
    BATCH_OBSERVATION_BACKENDS,
    BATCH_VISUAL_BACKENDS,
    EXECUTION_STEP_RUNTIME_MODES,
    FLIGHT_SHAPING_BACKENDS,
)
from python.mission_obs_taxonomy import BASE_MISSION_OBS_MODES, COOPERATIVE_MISSION_OBS_MODES, NAVAL_MISSION_OBS_MODES
from python.runtime_bootstrap import configure_sim_log_level, ensure_repo_imports, resolve_repo_path

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv  # noqa: E402
import ef_py  # noqa: E402
from tools.diagnostics.common import (  # noqa: E402
    average_timing_sums,
    flight_shaping_runtime_stats_dict,
    gpu_device_info_dict,
    merge_timing_sums,
    visual_runtime_stats_dict,
    write_json_output,
)


def _time_reset(vec_env, *, iters: int, seed_base: int) -> tuple[float, dict[str, float]]:
    timing_sums: dict[str, float] = {}
    timing_count = 0
    timing_scale = 1.0 / float(max(1, int(vec_env.num_envs)))
    start = time.perf_counter()
    for idx in range(max(1, int(iters))):
        vec_env.seed(int(seed_base) + idx * 1000)
        _ = vec_env.reset()
        for info in getattr(vec_env, "reset_infos", []) or []:
            if isinstance(info, dict):
                merge_timing_sums(timing_sums, info.get("timing"), scale=timing_scale)
                if isinstance(info.get("timing"), dict):
                    timing_count += 1
    elapsed = time.perf_counter() - start
    return 1000.0 * elapsed / max(1, int(iters)), average_timing_sums(timing_sums, count=timing_count)


def _time_steps(vec_env, action_batch, *, steps: int) -> tuple[float, dict[str, float]]:
    _ = vec_env.reset()
    timing_sums: dict[str, float] = {}
    timing_count = 0
    timing_scale = 1.0 / float(max(1, int(vec_env.num_envs)))
    start = time.perf_counter()
    for step_idx in range(max(1, int(steps))):
        _, _, _, infos = vec_env.step(action_batch[step_idx])
        for info in infos:
            if isinstance(info, dict):
                merge_timing_sums(timing_sums, info.get("timing"), scale=timing_scale)
                if isinstance(info.get("timing"), dict):
                    timing_count += 1
    elapsed = time.perf_counter() - start
    return (
        1000.0 * elapsed / float(max(1, int(steps)) * max(1, int(vec_env.num_envs))),
        average_timing_sums(timing_sums, count=timing_count),
    )


def _build_action_batch(*, steps: int, n_envs: int, action_dim: int, seed: int) -> list[np.ndarray]:
    rng = np.random.RandomState(int(seed) & 0xFFFFFFFF)
    actions = []
    for _ in range(max(1, int(steps))):
        batch = rng.uniform(-0.25, 0.25, size=(int(n_envs), int(action_dim))).astype(np.float32)
        if action_dim >= 4:
            batch[:, 3] = rng.uniform(0.55, 0.85, size=(int(n_envs),)).astype(np.float32)
        actions.append(batch)
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintained WorldBatchVecEnv training-adapter benchmark.")
    parser.add_argument("--scenario", default="scenarios/takeoff/takeoff.json", help="Scenario path to benchmark.")
    parser.add_argument("--n-envs", type=int, default=8, help="Number of parallel worlds/envs.")
    parser.add_argument("--steps", type=int, default=256, help="Number of rollout steps to benchmark.")
    parser.add_argument("--reset-iters", type=int, default=50, help="Reset iterations per backend.")
    parser.add_argument("--seed", type=int, default=123, help="Seed base for reset and action generation.")
    parser.add_argument(
        "--world-batch-threads",
        type=int,
        default=None,
        help="Configured worker threads for WorldBatchRuntime. Omit to keep the default (1); set 0 for auto mode.",
    )
    parser.add_argument(
        "--mission-obs-mode",
        type=str,
        default="nav_v2",
        choices=list(BASE_MISSION_OBS_MODES) + list(COOPERATIVE_MISSION_OBS_MODES) + list(NAVAL_MISSION_OBS_MODES),
        help="Mission observation mode.",
    )
    parser.add_argument(
        "--include-visual",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Include visual observations in the benchmarked envs.",
    )
    parser.add_argument(
        "--batch-visual-backend",
        type=str,
        default="auto",
        choices=list(BATCH_VISUAL_BACKENDS),
        help="World-batch visual backend to request.",
    )
    parser.add_argument(
        "--batch-observation-backend",
        type=str,
        default="auto",
        choices=list(BATCH_OBSERVATION_BACKENDS),
        help="World-batch observation backend to request.",
    )
    parser.add_argument(
        "--visual-downsample",
        type=int,
        default=1,
        help="Visual downsample factor when --include-visual is enabled.",
    )
    parser.add_argument(
        "--visual-update-interval",
        type=int,
        default=1,
        help="Visual refresh interval when --include-visual is enabled.",
    )
    parser.add_argument(
        "--action-mode",
        type=str,
        default="full",
        # Deliberately narrowed owner-derived subset: the random continuous
        # action batches used here cannot drive the hybrid event-action mode.
        choices=[mode for mode in ACTION_MODES if mode != "air_combat_hybrid_v1"],
        help="Action mode.",
    )
    parser.add_argument("--include-proprio", action="store_true", help="Include proprio in observations.")
    parser.add_argument(
        "--collect-step-timing",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Collect and report per-segment timing breakdowns from the envs.",
    )
    parser.add_argument(
        "--execution-step-runtime-mode",
        choices=list(EXECUTION_STEP_RUNTIME_MODES),
        default=None,
        help="Select the execution step runtime path inside ScenarioLoader.",
    )
    parser.add_argument(
        "--flight-shaping-backend",
        choices=list(FLIGHT_SHAPING_BACKENDS),
        default=None,
        help="Select the flight-shaping backend inside ScenarioLoader.",
    )
    parser.add_argument(
        "--execution-step-batch-prepare",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable the WorldBatchVecEnv C++ batch step-evaluation prepare path for A/B comparison.",
    )
    parser.add_argument(
        "--sim-log-level",
        default="warn",
        help="Simulation log level for the benchmark process (for example: trace, debug, info, warn, error).",
    )
    parser.add_argument("--json-out", default="", help="Optional JSON output path.")
    args = parser.parse_args()

    configure_sim_log_level(args.sim_log_level)
    scenario_path = os.path.abspath(args.scenario)
    if not os.path.exists(scenario_path):
        scenario_path = resolve_repo_path(args.scenario)

    env_kwargs = {
        "include_visual": bool(args.include_visual),
        "include_proprio": bool(args.include_proprio),
        "action_mode": str(args.action_mode),
        "mission_obs_mode": str(args.mission_obs_mode),
        "visual_downsample": max(1, int(args.visual_downsample)),
        "visual_update_interval": max(1, int(args.visual_update_interval)),
        "execution_step_runtime_mode": args.execution_step_runtime_mode,
        "flight_shaping_backend": args.flight_shaping_backend,
        "collect_step_timing": bool(args.collect_step_timing),
    }
    action_dim = 17 if args.action_mode == "full" else (2 if args.action_mode == "takeoff2" else (3 if args.action_mode == "naval_station3" else 4))
    action_batch = _build_action_batch(
        steps=int(args.steps),
        n_envs=int(args.n_envs),
        action_dim=int(action_dim),
        seed=int(args.seed),
    )

    batch_vec_kwargs = {
        "scenario_path": scenario_path,
        "n_envs": int(args.n_envs),
        "worker_threads": args.world_batch_threads,
        "batch_observation_backend": str(args.batch_observation_backend),
        "batch_visual_backend": str(args.batch_visual_backend),
        "execution_step_batch_prepare": bool(args.execution_step_batch_prepare),
        **env_kwargs,
    }
    batch_vec = WorldBatchVecEnv(**batch_vec_kwargs)
    gpu_device_info = gpu_device_info_dict()
    try:
        batch_reset_ms, batch_reset_timing = _time_reset(batch_vec, iters=int(args.reset_iters), seed_base=int(args.seed))
        batch_step_ms, batch_step_timing = _time_steps(
            batch_vec,
            action_batch,
            steps=int(args.steps),
        )
        visual_stats = visual_runtime_stats_dict()
        flight_shaping_stats = flight_shaping_runtime_stats_dict()
        effective_world_batch_threads = int(batch_vec.runtime_facade.effective_worker_threads())
        effective_batch_observation_backend = str(batch_vec._batch_observation_backend_mode())
        effective_batch_visual_backend = str(batch_vec._batch_visual_backend_mode())
    finally:
        batch_vec.close()

    results = {
        "scenario": scenario_path,
        "n_envs": int(args.n_envs),
        "steps": int(args.steps),
        "reset_iters": int(args.reset_iters),
        "configured_world_batch_threads": (
            None if args.world_batch_threads is None else int(args.world_batch_threads)
        ),
        "effective_world_batch_threads": effective_world_batch_threads,
        "action_mode": str(args.action_mode),
        "mission_obs_mode": str(args.mission_obs_mode),
        "include_visual": bool(args.include_visual),
        "include_proprio": bool(args.include_proprio),
        "visual_downsample": max(1, int(args.visual_downsample)),
        "visual_update_interval": max(1, int(args.visual_update_interval)),
        "requested_batch_observation_backend": str(args.batch_observation_backend),
        "requested_batch_visual_backend": str(args.batch_visual_backend),
        "effective_batch_observation_backend": effective_batch_observation_backend,
        "effective_batch_visual_backend": effective_batch_visual_backend,
        "execution_step_runtime_mode": args.execution_step_runtime_mode,
        "execution_step_batch_prepare": bool(args.execution_step_batch_prepare),
        "flight_shaping_backend": args.flight_shaping_backend,
        "collect_step_timing": bool(args.collect_step_timing),
        "sim_log_level": str(args.sim_log_level),
        "gpu_device_info": gpu_device_info,
        "visual_runtime_stats": visual_stats,
        "flight_shaping_runtime_stats": flight_shaping_stats,
        "world_batch_reset_ms": float(batch_reset_ms),
        "world_batch_ms_per_env_step": float(batch_step_ms),
        "world_batch_reset_timing_ms_per_env": batch_reset_timing,
        "world_batch_step_timing_ms_per_env_step": batch_step_timing,
    }

    print("World Batch VecEnv Benchmark")
    print("=" * 29)
    print(f"scenario                  : {results['scenario']}")
    print(f"n_envs                    : {results['n_envs']}")
    print(f"configured threads        : {results['configured_world_batch_threads']}")
    print(f"effective threads         : {results['effective_world_batch_threads']}")
    print(f"include visual            : {results['include_visual']}")
    print(f"requested obs backend     : {results['requested_batch_observation_backend']}")
    print(f"effective obs backend     : {results['effective_batch_observation_backend']}")
    print(f"requested visual backend  : {results['requested_batch_visual_backend']}")
    print(f"effective visual backend  : {results['effective_batch_visual_backend']}")
    print(f"step runtime mode         : {results['execution_step_runtime_mode']}")
    print(f"flight shaping backend    : {results['flight_shaping_backend']}")
    print(
        "gpu device               : "
        f"{json.dumps(results['gpu_device_info'], ensure_ascii=True, sort_keys=True)}"
    )
    print(f"world batch reset         : {results['world_batch_reset_ms']:.6f} ms")
    print(f"world batch ms/env-step   : {results['world_batch_ms_per_env_step']:.6f} ms")
    if results["include_visual"]:
        print(
            "visual runtime stats     : "
            f"{json.dumps(results['visual_runtime_stats'], ensure_ascii=True, sort_keys=True)}"
        )
    print(
        "flight shaping stats     : "
        f"{json.dumps(results['flight_shaping_runtime_stats'], ensure_ascii=True, sort_keys=True)}"
    )
    if results["world_batch_step_timing_ms_per_env_step"]:
        print(
            "world batch step timing  : "
            f"{json.dumps(results['world_batch_step_timing_ms_per_env_step'], ensure_ascii=True, sort_keys=True)}"
        )
    write_json_output(str(args.json_out), results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
