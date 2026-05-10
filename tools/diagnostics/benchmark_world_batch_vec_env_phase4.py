#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
from stable_baselines3.common.vec_env import DummyVecEnv

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from python.testing.runtime import configure_sim_log_level, ensure_repo_imports, resolve_repo_path

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

from gym_envs.universal_env import UniversalEnv  # noqa: E402
from python.rl.world_batch_vec_env import WorldBatchVecEnv  # noqa: E402
import ef_py  # noqa: E402


def _merge_timing_sums(acc: dict[str, float], timing: dict[str, float] | None, *, scale: float = 1.0) -> None:
    if not isinstance(timing, dict):
        return
    factor = float(scale)
    for key, value in timing.items():
        try:
            acc[str(key)] = float(acc.get(str(key), 0.0) + float(value) * factor)
        except Exception:
            pass


def _average_timing_sums(acc: dict[str, float], *, count: int) -> dict[str, float]:
    if count <= 0:
        return {}
    denom = float(count)
    return {key: float(value) / denom for key, value in acc.items()}


def _time_reset(vec_env, *, iters: int, seed_base: int) -> tuple[float, dict[str, float]]:
    timing_sums: dict[str, float] = {}
    timing_count = 0
    timing_scale = 1.0 / float(max(1, int(vec_env.num_envs))) if isinstance(vec_env, WorldBatchVecEnv) else 1.0
    start = time.perf_counter()
    for idx in range(max(1, int(iters))):
        vec_env.seed(int(seed_base) + idx * 1000)
        _ = vec_env.reset()
        for info in getattr(vec_env, "reset_infos", []) or []:
            if isinstance(info, dict):
                _merge_timing_sums(timing_sums, info.get("timing"), scale=timing_scale)
                if isinstance(info.get("timing"), dict):
                    timing_count += 1
    elapsed = time.perf_counter() - start
    return 1000.0 * elapsed / max(1, int(iters)), _average_timing_sums(timing_sums, count=timing_count)


def _time_steps(vec_env, action_batch, *, steps: int) -> tuple[float, dict[str, float], dict[str, object]]:
    _ = vec_env.reset()
    timing_sums: dict[str, float] = {}
    timing_count = 0
    shadow_total = 0
    shadow_match_count = 0
    shadow_mismatch_count = 0
    shadow_max_reward_total_delta = 0.0
    shadow_max_execution_step_reward_delta = 0.0
    timing_scale = 1.0 / float(max(1, int(vec_env.num_envs))) if isinstance(vec_env, WorldBatchVecEnv) else 1.0
    start = time.perf_counter()
    for step_idx in range(max(1, int(steps))):
        _, _, _, infos = vec_env.step(action_batch[step_idx])
        for info in infos:
            if isinstance(info, dict):
                _merge_timing_sums(timing_sums, info.get("timing"), scale=timing_scale)
                if isinstance(info.get("timing"), dict):
                    timing_count += 1
                shadow_report = info.get("execution_episode_controller_shadow_compare")
                if isinstance(shadow_report, dict):
                    shadow_total += 1
                    comparison = shadow_report.get("comparison")
                    if isinstance(comparison, dict):
                        if bool(comparison.get("overall_match", False)):
                            shadow_match_count += 1
                        else:
                            shadow_mismatch_count += 1
                        try:
                            shadow_max_reward_total_delta = max(
                                shadow_max_reward_total_delta,
                                abs(float(comparison.get("reward_total_delta", 0.0))),
                            )
                        except Exception:
                            pass
                        try:
                            shadow_max_execution_step_reward_delta = max(
                                shadow_max_execution_step_reward_delta,
                                abs(float(comparison.get("execution_step_reward_delta", 0.0))),
                            )
                        except Exception:
                            pass
    elapsed = time.perf_counter() - start
    shadow_stats = {}
    if shadow_total > 0:
        shadow_stats = {
            "report_count": int(shadow_total),
            "overall_match_count": int(shadow_match_count),
            "overall_mismatch_count": int(shadow_mismatch_count),
            "overall_match_rate": float(shadow_match_count) / float(max(1, shadow_total)),
            "max_reward_total_abs_delta": float(shadow_max_reward_total_delta),
            "max_execution_step_reward_abs_delta": float(shadow_max_execution_step_reward_delta),
        }
    return (
        1000.0 * elapsed / float(max(1, int(steps)) * max(1, int(vec_env.num_envs))),
        _average_timing_sums(timing_sums, count=timing_count),
        shadow_stats,
    )


def _build_dummy_vec_env(*, scenario_path: str, n_envs: int, env_kwargs: dict) -> DummyVecEnv:
    return DummyVecEnv(
        [
            lambda scenario_path=scenario_path, env_kwargs=dict(env_kwargs): UniversalEnv(
                scenario_path=scenario_path,
                **env_kwargs,
            )
            for _ in range(int(n_envs))
        ]
    )


def _gpu_device_info_dict() -> dict[str, object]:
    if not hasattr(ef_py, "probe_gpu_device"):
        return {
            "binding_available": False,
        }
    try:
        info = ef_py.probe_gpu_device()
    except Exception as ex:
        return {
            "binding_available": True,
            "probe_error": str(ex),
        }
    return {
        "binding_available": True,
        "cuda_runtime_built": bool(getattr(info, "cuda_runtime_built", False)),
        "cuda_runtime_available": bool(getattr(info, "cuda_runtime_available", False)),
        "device_count": int(getattr(info, "device_count", 0)),
        "active_device": int(getattr(info, "active_device", -1)),
        "compute_major": int(getattr(info, "compute_major", 0)),
        "compute_minor": int(getattr(info, "compute_minor", 0)),
        "runtime_version": int(getattr(info, "runtime_version", 0)),
        "total_global_mem_bytes": int(getattr(info, "total_global_mem_bytes", 0)),
        "free_global_mem_bytes": int(getattr(info, "free_global_mem_bytes", 0)),
        "device_name": str(getattr(info, "device_name", "")),
        "error_message": str(getattr(info, "error_message", "")),
    }


def _visual_stats_dict() -> dict[str, object]:
    if not hasattr(ef_py, "last_visual_experiment_stats"):
        return {
            "binding_available": False,
        }
    try:
        stats = ef_py.last_visual_experiment_stats()
    except Exception as ex:
        return {
            "binding_available": True,
            "stats_error": str(ex),
        }
    return {
        "binding_available": True,
        "used_cuda": bool(getattr(stats, "used_cuda", False)),
        "host_to_device_ms": float(getattr(stats, "host_to_device_ms", 0.0)),
        "kernel_ms": float(getattr(stats, "kernel_ms", 0.0)),
        "device_to_host_ms": float(getattr(stats, "device_to_host_ms", 0.0)),
        "total_ms": float(getattr(stats, "total_ms", 0.0)),
    }


def _flight_shaping_stats_dict() -> dict[str, object]:
    if not hasattr(ef_py, "last_flight_shaping_stats"):
        return {
            "binding_available": False,
        }
    try:
        stats = ef_py.last_flight_shaping_stats()
    except Exception as ex:
        return {
            "binding_available": True,
            "stats_error": str(ex),
        }
    return {
        "binding_available": True,
        "used_cuda": bool(getattr(stats, "used_cuda", False)),
        "host_to_device_ms": float(getattr(stats, "host_to_device_ms", 0.0)),
        "kernel_ms": float(getattr(stats, "kernel_ms", 0.0)),
        "device_to_host_ms": float(getattr(stats, "device_to_host_ms", 0.0)),
        "total_ms": float(getattr(stats, "total_ms", 0.0)),
    }


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
    parser = argparse.ArgumentParser(description="Phase 4 execution training adapter benchmark.")
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
        choices=["basic", "nav_v1", "nav_v2"],
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
        choices=["auto", "legacy", "compiled", "gpu_host"],
        help="World-batch visual backend to request.",
    )
    parser.add_argument(
        "--batch-observation-backend",
        type=str,
        default="auto",
        choices=["auto", "legacy", "compiled", "gpu_host"],
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
        choices=["full", "takeoff2", "takeoff4"],
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
        choices=["compiled", "legacy"],
        default=None,
        help="Select the execution step runtime path inside ScenarioLoader.",
    )
    parser.add_argument(
        "--flight-shaping-backend",
        choices=["auto", "legacy", "compiled", "gpu_host"],
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
        "--execution-episode-controller-shadow-compare",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable the opt-in WorldBatchVecEnv compiled controller shadow-compare diagnostics during rollout.",
    )
    parser.add_argument(
        "--execution-episode-controller-mainline",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable the opt-in WorldBatchVecEnv runtime-owned compiled episode-controller rollout path.",
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
    action_dim = 17 if args.action_mode == "full" else (2 if args.action_mode == "takeoff2" else 4)
    action_batch = _build_action_batch(
        steps=int(args.steps),
        n_envs=int(args.n_envs),
        action_dim=int(action_dim),
        seed=int(args.seed),
    )

    dummy_vec = _build_dummy_vec_env(scenario_path=scenario_path, n_envs=int(args.n_envs), env_kwargs=env_kwargs)
    batch_vec_kwargs = {
        "scenario_path": scenario_path,
        "n_envs": int(args.n_envs),
        "worker_threads": args.world_batch_threads,
        "batch_observation_backend": str(args.batch_observation_backend),
        "batch_visual_backend": str(args.batch_visual_backend),
        "execution_step_batch_prepare": bool(args.execution_step_batch_prepare),
        "execution_episode_controller_shadow_compare": bool(args.execution_episode_controller_shadow_compare),
        "execution_episode_controller_mainline": bool(args.execution_episode_controller_mainline),
        **env_kwargs,
    }
    batch_vec = WorldBatchVecEnv(**batch_vec_kwargs)
    gpu_device_info = _gpu_device_info_dict()
    try:
        dummy_reset_ms, dummy_reset_timing = _time_reset(dummy_vec, iters=int(args.reset_iters), seed_base=int(args.seed))
        batch_reset_ms, batch_reset_timing = _time_reset(batch_vec, iters=int(args.reset_iters), seed_base=int(args.seed))
        dummy_step_ms, dummy_step_timing, dummy_shadow_compare_stats = _time_steps(
            dummy_vec, action_batch, steps=int(args.steps)
        )
        batch_step_ms, batch_step_timing, batch_shadow_compare_stats = _time_steps(
            batch_vec, action_batch, steps=int(args.steps)
        )
        visual_stats = _visual_stats_dict()
        flight_shaping_stats = _flight_shaping_stats_dict()
        effective_world_batch_threads = int(batch_vec.batch_runtime.effective_worker_threads())
        effective_batch_observation_backend = str(batch_vec._batch_observation_backend_mode())
        effective_batch_visual_backend = str(batch_vec._batch_visual_backend_mode())
    finally:
        dummy_vec.close()
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
        "execution_episode_controller_shadow_compare": bool(args.execution_episode_controller_shadow_compare),
        "execution_episode_controller_mainline": bool(args.execution_episode_controller_mainline),
        "flight_shaping_backend": args.flight_shaping_backend,
        "collect_step_timing": bool(args.collect_step_timing),
        "sim_log_level": str(args.sim_log_level),
        "gpu_device_info": gpu_device_info,
        "visual_runtime_stats": visual_stats,
        "flight_shaping_runtime_stats": flight_shaping_stats,
        "dummy_reset_ms": float(dummy_reset_ms),
        "world_batch_reset_ms": float(batch_reset_ms),
        "reset_speedup": float(dummy_reset_ms / max(batch_reset_ms, 1.0e-12)),
        "dummy_ms_per_env_step": float(dummy_step_ms),
        "world_batch_ms_per_env_step": float(batch_step_ms),
        "step_speedup": float(dummy_step_ms / max(batch_step_ms, 1.0e-12)),
        "dummy_reset_timing_ms_per_env": dummy_reset_timing,
        "world_batch_reset_timing_ms_per_env": batch_reset_timing,
        "dummy_step_timing_ms_per_env_step": dummy_step_timing,
        "world_batch_step_timing_ms_per_env_step": batch_step_timing,
        "dummy_shadow_compare_stats": dummy_shadow_compare_stats,
        "world_batch_shadow_compare_stats": batch_shadow_compare_stats,
    }

    print("World Batch VecEnv Phase 4 Benchmark")
    print("=" * 37)
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
    print(f"controller shadow compare : {results['execution_episode_controller_shadow_compare']}")
    print(f"controller mainline       : {results['execution_episode_controller_mainline']}")
    print(f"flight shaping backend    : {results['flight_shaping_backend']}")
    print(
        "gpu device               : "
        f"{json.dumps(results['gpu_device_info'], ensure_ascii=True, sort_keys=True)}"
    )
    print(f"dummy reset               : {results['dummy_reset_ms']:.6f} ms")
    print(f"world batch reset         : {results['world_batch_reset_ms']:.6f} ms")
    print(f"reset speedup             : {results['reset_speedup']:.2f}x")
    print(f"dummy ms/env-step         : {results['dummy_ms_per_env_step']:.6f} ms")
    print(f"world batch ms/env-step   : {results['world_batch_ms_per_env_step']:.6f} ms")
    print(f"step speedup              : {results['step_speedup']:.2f}x")
    if results["include_visual"]:
        print(
            "visual runtime stats     : "
            f"{json.dumps(results['visual_runtime_stats'], ensure_ascii=True, sort_keys=True)}"
        )
    print(
        "flight shaping stats     : "
        f"{json.dumps(results['flight_shaping_runtime_stats'], ensure_ascii=True, sort_keys=True)}"
    )
    if results["dummy_step_timing_ms_per_env_step"]:
        print(f"dummy step timing         : {json.dumps(results['dummy_step_timing_ms_per_env_step'], ensure_ascii=True, sort_keys=True)}")
    if results["world_batch_step_timing_ms_per_env_step"]:
        print(
            "world batch step timing  : "
            f"{json.dumps(results['world_batch_step_timing_ms_per_env_step'], ensure_ascii=True, sort_keys=True)}"
        )
    if results["world_batch_shadow_compare_stats"]:
        print(
            "shadow compare stats     : "
            f"{json.dumps(results['world_batch_shadow_compare_stats'], ensure_ascii=True, sort_keys=True)}"
        )

    if args.json_out:
        with open(os.path.abspath(args.json_out), "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
