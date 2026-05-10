#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "build-gpu"))
sys.path.insert(0, str(REPO_ROOT))

import ef_py  # noqa: F401
import numpy as np

from python.env_config import resolve_env_settings
from python.rl.world_batch_vec_env import WorldBatchVecEnv
from python.rl.wrappers import get_action_wrapper_spec


_DEFAULT_TRAIN_CONFIG = "examples/config/training/frozen/execution/p5_continuous_retrain_v1.json"
_DEFAULT_SCENARIO = "scenarios/combined/takeoff_to_landing_continuous_train_v1.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark WorldBatchVecEnv execution throughput.")
    parser.add_argument("--train-config", default=_DEFAULT_TRAIN_CONFIG, help="Training config JSON used to derive env/runtime settings.")
    parser.add_argument("--scenario", default=_DEFAULT_SCENARIO, help="Scenario JSON to load into WorldBatchVecEnv.")
    parser.add_argument("--n-envs", type=int, default=64, help="Number of parallel worlds to benchmark.")
    parser.add_argument("--warmup-steps", type=int, default=5, help="Number of warmup steps before measuring.")
    parser.add_argument("--benchmark-steps", type=int, default=20, help="Number of timed benchmark steps.")
    parser.add_argument("--seed", type=int, default=123, help="Seed forwarded to the vec env.")
    return parser.parse_args()


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def main() -> int:
    args = _parse_args()
    train_config_path = str((REPO_ROOT / args.train_config).resolve())
    scenario_path = str((REPO_ROOT / args.scenario).resolve())

    train_config = _load_json(train_config_path)
    runtime_cfg = train_config.get("runtime", {}) if isinstance(train_config.get("runtime", {}), dict) else {}
    env_settings = resolve_env_settings(
        train_config,
        SimpleNamespace(
            include_visual=None,
            include_proprio=None,
            action_mode=None,
            mission_obs_mode=None,
            visual_downsample=None,
            visual_update_interval=None,
            execution_step_runtime_mode=None,
            step_info_mode=None,
            flight_shaping_backend=None,
        ),
    )

    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
    action_wrapper_kwargs = dict(wrapper_kwargs or {}) if wrapper_class is not None else None

    env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=max(1, int(args.n_envs)),
        worker_threads=runtime_cfg.get("world_batch_threads"),
        collect_step_timing=True,
        batch_observation_backend=str(runtime_cfg.get("batch_observation_backend", "auto")),
        batch_visual_backend=str(runtime_cfg.get("batch_visual_backend", "auto")),
        policy_observation_torch_bridge=bool(runtime_cfg.get("policy_observation_torch_bridge", True)),
        observation_return_mode=str(runtime_cfg.get("observation_return_mode", "copy")),
        action_wrapper_kwargs=action_wrapper_kwargs,
        **env_settings,
    )

    try:
        env.seed(int(args.seed))

        print(f"Train config: {train_config_path}")
        print(f"Scenario:     {scenario_path}")
        print(f"Creating environment batch with {env.num_envs} worlds...")

        print("Resetting environment...")
        env.reset()

        print(f"Warmup ({int(args.warmup_steps)} steps)...")
        for _ in range(int(args.warmup_steps)):
            actions = np.random.randn(env.num_envs, env.action_space.shape[0]).astype(np.float32)
            env.step(actions)

        print(f"Benchmarking ({int(args.benchmark_steps)} steps)...")
        times = []
        for i in range(int(args.benchmark_steps)):
            actions = np.random.randn(env.num_envs, env.action_space.shape[0]).astype(np.float32)
            t0 = time.perf_counter()
            env.step(actions)
            times.append((time.perf_counter() - t0) * 1000.0)
            if i == 0:
                print(f"First step: {times[0]:.3f}ms")

        timing = env.last_step_timing
        print(f"\n=== Timing Results ({env.num_envs} envs) ===")
        print(f"step_eval_prepare_ms:            {timing.get('step_eval_prepare_ms', 0.0):.3f}")
        print(f"action_prepare_ms:               {timing.get('action_prepare_ms', 0.0):.3f}")
        print(f"batch_step_ms:                   {timing.get('batch_step_ms', 0.0):.3f}")
        print(f"state_read_ms:                   {timing.get('state_read_ms', 0.0):.3f}")
        print(f"behavior_update_ms:              {timing.get('behavior_update_ms', 0.0):.3f}")
        print(f"total_ms (per batch):            {np.mean(times):.3f}")
        print(f"ms/env-step:                     {np.mean(times) / float(env.num_envs):.3f}")
        return 0
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
