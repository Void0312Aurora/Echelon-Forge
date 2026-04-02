#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from stable_baselines3.common.callbacks import BaseCallback

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", ".."))
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from python.testing.runtime import configure_sim_log_level, ensure_repo_imports, resolve_repo_path

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

from python.rl.ppo_adaptive_kl import AdaptiveKLPPO  # noqa: E402
from python.rl.world_batch_vec_env import WorldBatchVecEnv  # noqa: E402
import ef_py  # noqa: E402


class _NullCallback(BaseCallback):
    def _on_step(self) -> bool:
        return True


@dataclass
class _CaseConfig:
    name: str
    env_kwargs: dict[str, Any]


def _torch_sync() -> None:
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def _gpu_device_info_dict() -> dict[str, object]:
    if not hasattr(ef_py, "probe_gpu_device"):
        return {"binding_available": False}
    info = ef_py.probe_gpu_device()
    return {
        "binding_available": True,
        "cuda_runtime_built": bool(getattr(info, "cuda_runtime_built", False)),
        "cuda_runtime_available": bool(getattr(info, "cuda_runtime_available", False)),
        "device_count": int(getattr(info, "device_count", 0)),
        "active_device": int(getattr(info, "active_device", -1)),
        "device_name": str(getattr(info, "device_name", "")),
    }


def _visual_stats_dict() -> dict[str, object]:
    if not hasattr(ef_py, "last_visual_experiment_stats"):
        return {"binding_available": False}
    stats = ef_py.last_visual_experiment_stats()
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
        return {"binding_available": False}
    stats = ef_py.last_flight_shaping_stats()
    return {
        "binding_available": True,
        "used_cuda": bool(getattr(stats, "used_cuda", False)),
        "host_to_device_ms": float(getattr(stats, "host_to_device_ms", 0.0)),
        "kernel_ms": float(getattr(stats, "kernel_ms", 0.0)),
        "device_to_host_ms": float(getattr(stats, "device_to_host_ms", 0.0)),
        "total_ms": float(getattr(stats, "total_ms", 0.0)),
    }


def _forward_benchmark(
    env: WorldBatchVecEnv,
    model: AdaptiveKLPPO,
    *,
    iters: int,
    seed: int,
) -> dict[str, float]:
    torch.manual_seed(int(seed))
    np.random.seed(int(seed) & 0xFFFFFFFF)
    model._last_obs = env.reset()
    model._last_episode_starts = np.ones((env.num_envs,), dtype=bool)

    # Warm once so CUDA alloc/setup does not dominate.
    with torch.no_grad():
        obs_tensor = model._get_policy_obs_tensor(env, model._last_obs)
        _ = model.policy(obs_tensor)
    _torch_sync()

    start = time.perf_counter()
    for _ in range(max(1, int(iters))):
        with torch.no_grad():
            obs_tensor = model._get_policy_obs_tensor(env, model._last_obs)
            _ = model.policy(obs_tensor)
    _torch_sync()
    elapsed = time.perf_counter() - start
    per_iter_ms = 1000.0 * elapsed / float(max(1, int(iters)))
    per_env_ms = per_iter_ms / float(max(1, int(env.num_envs)))
    return {
        "forward_ms_per_iter": float(per_iter_ms),
        "forward_ms_per_env": float(per_env_ms),
    }


def _collect_rollout_benchmark(
    env: WorldBatchVecEnv,
    model: AdaptiveKLPPO,
    *,
    rollout_steps: int,
    repeats: int,
    seed: int,
) -> dict[str, float]:
    _, callback = model._setup_learn(
        total_timesteps=int(rollout_steps) * int(env.num_envs) * max(1, int(repeats)),
        callback=_NullCallback(),
        reset_num_timesteps=True,
        tb_log_name="bridge_benchmark",
        progress_bar=False,
    )
    total_elapsed = 0.0
    total_steps = 0

    for repeat_idx in range(max(1, int(repeats))):
        torch.manual_seed(int(seed) + repeat_idx)
        np.random.seed((int(seed) + repeat_idx) & 0xFFFFFFFF)
        model.rollout_buffer.reset()
        model._last_obs = env.reset()
        model._last_episode_starts = np.ones((env.num_envs,), dtype=bool)
        _torch_sync()
        start = time.perf_counter()
        ok = model.collect_rollouts(env, callback, model.rollout_buffer, n_rollout_steps=int(rollout_steps))
        _torch_sync()
        if not ok:
            raise RuntimeError("collect_rollouts terminated early during benchmark")
        total_elapsed += time.perf_counter() - start
        total_steps += int(rollout_steps) * int(env.num_envs)

    ms_per_env_step = 1000.0 * total_elapsed / float(max(1, total_steps))
    env_steps_per_s = float(total_steps) / max(total_elapsed, 1.0e-9)
    return {
        "rollout_ms_per_env_step": float(ms_per_env_step),
        "rollout_env_steps_per_s": float(env_steps_per_s),
    }


def _train_update_benchmark(
    env: WorldBatchVecEnv,
    model: AdaptiveKLPPO,
    *,
    rollout_steps: int,
    seed: int,
) -> dict[str, float]:
    total_timesteps = int(rollout_steps) * int(env.num_envs)
    _, callback = model._setup_learn(
        total_timesteps=total_timesteps,
        callback=_NullCallback(),
        reset_num_timesteps=True,
        tb_log_name="bridge_benchmark_train",
        progress_bar=False,
    )
    torch.manual_seed(int(seed))
    np.random.seed(int(seed) & 0xFFFFFFFF)
    model.rollout_buffer.reset()
    model._last_obs = env.reset()
    model._last_episode_starts = np.ones((env.num_envs,), dtype=bool)
    ok = model.collect_rollouts(env, callback, model.rollout_buffer, n_rollout_steps=int(rollout_steps))
    if not ok:
        raise RuntimeError("collect_rollouts terminated early before train benchmark")
    model._update_current_progress_remaining(model.num_timesteps, model._total_timesteps)

    _torch_sync()
    start = time.perf_counter()
    model.train()
    _torch_sync()
    train_elapsed = time.perf_counter() - start
    env_steps = max(1, int(rollout_steps) * int(env.num_envs))
    return {
        "train_ms_per_env_step": float(1000.0 * train_elapsed / float(env_steps)),
        "train_updates_per_s": float(env_steps / max(train_elapsed, 1.0e-9)),
    }


def _run_case(
    *,
    scenario_path: str,
    n_envs: int,
    seed: int,
    forward_iters: int,
    rollout_steps: int,
    rollout_repeats: int,
    policy_observation_torch_bridge: bool,
    observation_return_mode: str,
    env_kwargs: dict[str, Any],
) -> dict[str, object]:
    torch.manual_seed(int(seed))
    np.random.seed(int(seed) & 0xFFFFFFFF)
    env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=int(n_envs),
        policy_observation_torch_bridge=bool(policy_observation_torch_bridge),
        observation_return_mode=str(observation_return_mode),
        **env_kwargs,
    )
    try:
        env.seed(int(seed))
        model = AdaptiveKLPPO(
            "MultiInputPolicy",
            env,
            n_steps=int(rollout_steps),
            batch_size=max(1, int(rollout_steps) * int(n_envs)),
            n_epochs=1,
            learning_rate=3.0e-4,
            gamma=0.99,
            gae_lambda=0.95,
            ent_coef=0.0,
            vf_coef=0.5,
            max_grad_norm=0.5,
            device="cuda",
            verbose=0,
        )
        bridge_obs = env.reset()
        obs_t = env.get_policy_observation_torch(device=torch.device("cuda"))
        visual_on_cuda = bool(obs_t is not None and "visual" in obs_t and bool(obs_t["visual"].is_cuda))
        nonvisual_on_cuda = bool(obs_t is not None and bool(obs_t["instruments"].is_cuda))
        del bridge_obs
        forward = _forward_benchmark(env, model, iters=forward_iters, seed=seed)
        rollout = _collect_rollout_benchmark(
            env,
            model,
            rollout_steps=rollout_steps,
            repeats=rollout_repeats,
            seed=seed,
        )
        train_update = _train_update_benchmark(
            env,
            model,
            rollout_steps=rollout_steps,
            seed=seed + 10000,
        )
        return {
            "bridge_enabled": bool(policy_observation_torch_bridge),
            "observation_return_mode": str(observation_return_mode),
            "torch_bridge_active": bool(getattr(env, "_policy_torch_bridge_enabled", False)),
            "requested_batch_observation_backend": str(env.batch_observation_backend),
            "effective_batch_observation_backend": str(env._batch_observation_backend_mode()),
            "requested_batch_visual_backend": str(env.batch_visual_backend),
            "effective_batch_visual_backend": str(env._batch_visual_backend_mode()),
            "requested_flight_shaping_backend": str(env.flight_shaping_backend),
            "effective_flight_shaping_backend": str(env._flight_shaping_backend_mode()),
            "rollout_buffer_class": type(model.rollout_buffer).__name__,
            "observation_cuda": nonvisual_on_cuda,
            "visual_cuda": visual_on_cuda,
            "visual_runtime_stats": _visual_stats_dict(),
            "flight_shaping_runtime_stats": _flight_shaping_stats_dict(),
            **forward,
            **rollout,
            **train_update,
            "collect_plus_train_ms_per_env_step": float(
                rollout["rollout_ms_per_env_step"] + train_update["train_ms_per_env_step"]
            ),
        }
    finally:
        env.close()


def _pct_delta(base: float, other: float) -> float:
    if abs(base) <= 1.0e-12:
        return 0.0
    return 100.0 * (other - base) / base


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 4 policy-observation bridge benchmark.")
    parser.add_argument(
        "--scenario",
        default="scenarios/combined/takeoff_to_landing_continuous_train_v1.json",
        help="Scenario path to benchmark.",
    )
    parser.add_argument("--n-envs", type=int, default=8, help="Number of parallel environments.")
    parser.add_argument("--seed", type=int, default=123, help="Base seed.")
    parser.add_argument("--forward-iters", type=int, default=128, help="Static policy forward iterations.")
    parser.add_argument("--rollout-steps", type=int, default=64, help="Rollout steps per repeat.")
    parser.add_argument("--rollout-repeats", type=int, default=2, help="Repeated rollout measurements.")
    parser.add_argument(
        "--case",
        choices=["obs_gpuhost_novis", "p5like_visual", "p5like_visual_fullgpu"],
        default="p5like_visual",
        help="Benchmark case to run.",
    )
    parser.add_argument(
        "--sim-log-level",
        default="warn",
        help="Simulation log level for the benchmark process.",
    )
    parser.add_argument(
        "--observation-return-mode",
        choices=["copy", "view"],
        default="copy",
        help="Observation ownership mode for WorldBatchVecEnv reset/step returns.",
    )
    parser.add_argument(
        "--flight-shaping-backend",
        choices=["case", "auto", "legacy", "compiled", "gpu_host"],
        default="case",
        help="Override the benchmark case flight-shaping backend. Use 'case' to keep the built-in case default.",
    )
    args = parser.parse_args()

    configure_sim_log_level(args.sim_log_level)
    scenario_path = resolve_repo_path(str(args.scenario))

    device_info = _gpu_device_info_dict()
    if not bool(device_info.get("cuda_runtime_available", False)):
        print(
            json.dumps(
                {
                    "error": "CUDA runtime is not available for the bridge benchmark.",
                    "gpu_device_info": device_info,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    case_map: dict[str, _CaseConfig] = {
        "obs_gpuhost_novis": _CaseConfig(
            name="obs_gpuhost_novis",
            env_kwargs={
                "include_visual": False,
                "include_proprio": False,
                "action_mode": "full",
                "mission_obs_mode": "nav_v2",
                "step_info_mode": "off",
                "execution_step_runtime_mode": "compiled",
                "flight_shaping_backend": "compiled",
                "batch_observation_backend": "gpu_host",
                "batch_visual_backend": "gpu_host",
            },
        ),
        "p5like_visual": _CaseConfig(
            name="p5like_visual",
            env_kwargs={
                "include_visual": True,
                "include_proprio": False,
                "action_mode": "full",
                "mission_obs_mode": "nav_v2",
                "visual_downsample": 2,
                "visual_update_interval": 2,
                "step_info_mode": "off",
                "execution_step_runtime_mode": "compiled",
                "flight_shaping_backend": "compiled",
                "batch_observation_backend": "compiled",
                "batch_visual_backend": "gpu_host",
            },
        ),
        "p5like_visual_fullgpu": _CaseConfig(
            name="p5like_visual_fullgpu",
            env_kwargs={
                "include_visual": True,
                "include_proprio": False,
                "action_mode": "full",
                "mission_obs_mode": "nav_v2",
                "visual_downsample": 2,
                "visual_update_interval": 2,
                "step_info_mode": "off",
                "execution_step_runtime_mode": "compiled",
                "flight_shaping_backend": "compiled",
                "batch_observation_backend": "gpu_host",
                "batch_visual_backend": "gpu_host",
            },
        ),
    }
    case = case_map[str(args.case)]
    case_env_kwargs = dict(case.env_kwargs)
    if str(args.flight_shaping_backend) != "case":
        case_env_kwargs["flight_shaping_backend"] = str(args.flight_shaping_backend)

    off_result = _run_case(
        scenario_path=scenario_path,
        n_envs=args.n_envs,
        seed=args.seed,
        forward_iters=args.forward_iters,
        rollout_steps=args.rollout_steps,
        rollout_repeats=args.rollout_repeats,
        policy_observation_torch_bridge=False,
        observation_return_mode=args.observation_return_mode,
        env_kwargs=dict(case_env_kwargs),
    )
    on_result = _run_case(
        scenario_path=scenario_path,
        n_envs=args.n_envs,
        seed=args.seed,
        forward_iters=args.forward_iters,
        rollout_steps=args.rollout_steps,
        rollout_repeats=args.rollout_repeats,
        policy_observation_torch_bridge=True,
        observation_return_mode=args.observation_return_mode,
        env_kwargs=dict(case_env_kwargs),
    )

    result = {
        "case": case.name,
        "scenario": scenario_path,
        "n_envs": int(args.n_envs),
        "forward_iters": int(args.forward_iters),
        "rollout_steps": int(args.rollout_steps),
        "rollout_repeats": int(args.rollout_repeats),
        "observation_return_mode": str(args.observation_return_mode),
        "flight_shaping_backend_override": str(args.flight_shaping_backend),
        "gpu_device_info": device_info,
        "bridge_off": off_result,
        "bridge_on": on_result,
        "delta_pct": {
            "forward_ms_per_iter": _pct_delta(
                float(off_result["forward_ms_per_iter"]),
                float(on_result["forward_ms_per_iter"]),
            ),
            "forward_ms_per_env": _pct_delta(
                float(off_result["forward_ms_per_env"]),
                float(on_result["forward_ms_per_env"]),
            ),
            "rollout_ms_per_env_step": _pct_delta(
                float(off_result["rollout_ms_per_env_step"]),
                float(on_result["rollout_ms_per_env_step"]),
            ),
            "rollout_env_steps_per_s": _pct_delta(
                float(off_result["rollout_env_steps_per_s"]),
                float(on_result["rollout_env_steps_per_s"]),
            ),
            "train_ms_per_env_step": _pct_delta(
                float(off_result["train_ms_per_env_step"]),
                float(on_result["train_ms_per_env_step"]),
            ),
            "train_updates_per_s": _pct_delta(
                float(off_result["train_updates_per_s"]),
                float(on_result["train_updates_per_s"]),
            ),
            "collect_plus_train_ms_per_env_step": _pct_delta(
                float(off_result["collect_plus_train_ms_per_env_step"]),
                float(on_result["collect_plus_train_ms_per_env_step"]),
            ),
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
