from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from python.env_config import resolve_env_settings
from python.rl.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv
from python.rl.execution_runtime import coerce_timing_dict
from python.rl.single_world_batch_runtime import build_single_world_batch_execution_runtime


@dataclass
class BenchmarkResult:
    mode: str
    steps: int
    env_count: int
    slot_count: int
    metrics: dict[str, float]
    timing: dict[str, float]
    notes: list[str]


def _rss_bytes() -> int | None:
    try:
        import psutil  # type: ignore
    except Exception:
        psutil = None
    if psutil is not None:
        try:
            return int(psutil.Process(os.getpid()).memory_info().rss)
        except Exception:
            return None
    try:
        import resource

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if os.name == "posix" and os.uname().sysname == "Darwin":  # pragma: no cover
            return int(rss)
        return int(rss) * 1024
    except Exception:
        return None


def _safe_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.fmean(values))


def _extract_timing(info: Any) -> dict[str, float]:
    if not isinstance(info, dict):
        return {}
    return coerce_timing_dict(info.get("timing"))


def _build_env_settings(train_config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    env_settings = resolve_env_settings(train_config, args)
    env_settings["collect_step_timing"] = True
    return env_settings


def _rand_action(action_space, rng: np.random.Generator) -> np.ndarray:
    low = np.asarray(action_space.low, dtype=np.float32)
    high = np.asarray(action_space.high, dtype=np.float32)
    return rng.uniform(low, high).astype(np.float32)


def _flatten_timing_stats(
    prefix: str,
    timing_keys: dict[str, list[float]],
    *,
    scale: float = 1.0,
) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, values in timing_keys.items():
        out[f"{prefix}{key}_mean_ms"] = _safe_mean(values) * float(scale)
    return out


def _run_single_agent(
    *,
    scenario_path: str,
    train_config: dict[str, Any],
    args: argparse.Namespace,
    steps: int,
    seed: int,
) -> BenchmarkResult:
    env_settings = _build_env_settings(train_config, args)
    runtime = build_single_world_batch_execution_runtime(
        scenario_path=scenario_path,
        env_settings=env_settings,
        worker_threads=1,
    )
    rng = np.random.default_rng(int(seed))
    _obs, _info = runtime.reset(seed=int(seed))
    step_times: list[float] = []
    timing_keys: dict[str, list[float]] = {}
    notes: list[str] = []
    try:
        for _ in range(int(steps)):
            action = _rand_action(runtime.action_space, rng)
            t0 = time.perf_counter()
            _obs, _reward, terminated, truncated, info = runtime.step(action)
            step_times.append((time.perf_counter() - t0) * 1000.0)
            timing = _extract_timing(info)
            for key, value in timing.items():
                timing_keys.setdefault(key, []).append(float(value))
            if bool(terminated or truncated):
                _obs, _info = runtime.reset(seed=int(seed))
        timing = {
            "rss_bytes": float(_rss_bytes() or 0),
            "step_time_ms": _safe_mean(step_times),
            **_flatten_timing_stats("", timing_keys),
        }
        metrics = {
            "step_time_ms": float(timing.get("step_time_ms", 0.0)),
            "per_agent_step_time_ms": float(timing.get("step_time_ms", 0.0)),
            "obs_build_ms": float(timing.get("obs_build_ms_mean_ms", 0.0)),
            "runtime_step_ms": float(timing.get("batch_step_ms_mean_ms", 0.0)),
        }
        return BenchmarkResult(
            mode="single_agent",
            steps=int(steps),
            env_count=1,
            slot_count=1,
            metrics=metrics,
            timing=timing,
            notes=notes,
        )
    finally:
        runtime.close()


def _run_leader(
    *,
    scenario_path: str,
    train_config: dict[str, Any],
    steps: int,
    seed: int,
) -> BenchmarkResult:
    from gym_envs.leader_env import LeaderTrainingEnv

    leader_cfg = train_config.get("leader_env", {}) if isinstance(train_config, dict) else {}
    if not isinstance(leader_cfg, dict):
        leader_cfg = {}
    env = LeaderTrainingEnv(
        scenario_path=scenario_path,
        decision_interval_steps=int(leader_cfg.get("decision_interval_steps", 20)),
        execution_backend=str(leader_cfg.get("execution_backend", "scripted")),
        execution_train_config=leader_cfg.get("execution_train_config"),
        execution_model_path=leader_cfg.get("execution_model_path"),
        execution_algo=str(leader_cfg.get("execution_algo", "auto")),
        execution_action_repeat=int(leader_cfg.get("execution_action_repeat", 1)),
        scripted_transition_alt_agl_m=float(leader_cfg.get("scripted_transition_alt_agl_m", 140.0)),
        heading_bias_limit_deg=float(leader_cfg.get("heading_bias_limit_deg", 45.0)),
        altitude_bias_limit_m=float(leader_cfg.get("altitude_bias_limit_m", 800.0)),
        speed_bias_limit_mps=float(leader_cfg.get("speed_bias_limit_mps", 40.0)),
        command_change_penalty=float(leader_cfg.get("command_change_penalty", 0.0)),
        teacher_keep_deadband=float(leader_cfg.get("teacher_keep_deadband", 0.20)),
        invalid_phase_penalty=float(leader_cfg.get("invalid_phase_penalty", 0.0)),
        premature_approach_penalty=float(leader_cfg.get("premature_approach_penalty", 0.0)),
        baseline_deviation_penalty=float(leader_cfg.get("baseline_deviation_penalty", 0.0)),
        mode_change_penalty=float(leader_cfg.get("mode_change_penalty", 0.0)),
        approach_gate_distance_m=float(leader_cfg.get("approach_gate_distance_m", 18000.0)),
        approach_gate_cross_m=float(leader_cfg.get("approach_gate_cross_m", 3500.0)),
        approach_gate_heading_error_deg=float(leader_cfg.get("approach_gate_heading_error_deg", 85.0)),
        execution_device=str(leader_cfg.get("execution_device", "cpu")),
        execution_use_autocast=bool(leader_cfg.get("execution_use_autocast", False)),
        execution_step_runtime_mode=leader_cfg.get("execution_step_runtime_mode"),
        execution_world_batch_runtime=bool(leader_cfg.get("execution_world_batch_runtime", False)),
        execution_world_batch_threads=leader_cfg.get("execution_world_batch_threads"),
        collect_step_timing=True,
    )
    rng = np.random.default_rng(int(seed))
    _obs, _info = env.reset(seed=int(seed))
    step_times: list[float] = []
    timing_keys: dict[str, list[float]] = {}
    execution_timing_keys: dict[str, list[float]] = {}
    notes: list[str] = []
    try:
        for _ in range(int(steps)):
            action = _rand_action(env.action_space, rng)
            t0 = time.perf_counter()
            _obs, _reward, terminated, truncated, info = env.step(action)
            step_times.append((time.perf_counter() - t0) * 1000.0)
            timing = _extract_timing(info)
            for key, value in timing.items():
                timing_keys.setdefault(key, []).append(float(value))
            execution_timing = coerce_timing_dict(info.get("execution_timing"))
            for key, value in execution_timing.items():
                execution_timing_keys.setdefault(key, []).append(float(value))
            if bool(terminated or truncated):
                _obs, _info = env.reset(seed=int(seed))
        timing = {
            "rss_bytes": float(_rss_bytes() or 0),
            "step_time_ms": _safe_mean(step_times),
            **_flatten_timing_stats("", timing_keys),
            **_flatten_timing_stats("execution_", execution_timing_keys),
        }
        metrics = {
            "step_time_ms": float(timing.get("step_time_ms", 0.0)),
            "per_agent_step_time_ms": float(timing.get("step_time_ms", 0.0)),
            "obs_build_ms": float(timing.get("obs_build_ms_mean_ms", 0.0)),
            "policy_forward_ms": float(
                timing.get("execution_execution_runtime_step_ms_mean_ms", 0.0)
                + timing.get("execution_execution_prepare_action_ms_mean_ms", 0.0)
            ),
        }
        return BenchmarkResult(
            mode="leader",
            steps=int(steps),
            env_count=1,
            slot_count=1,
            metrics=metrics,
            timing=timing,
            notes=notes,
        )
    finally:
        env.close()


def _run_cooperative(
    *,
    scenario_path: str,
    train_config: dict[str, Any],
    args: argparse.Namespace,
    steps: int,
    seed: int,
    n_envs: int,
) -> BenchmarkResult:
    env_settings = _build_env_settings(train_config, args)
    runtime_cfg = train_config.get("runtime", {}) if isinstance(train_config, dict) else {}
    if not isinstance(runtime_cfg, dict):
        runtime_cfg = {}
    runtime = CooperativeWorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=int(n_envs),
        worker_threads=runtime_cfg.get("world_batch_threads", 1),
        batch_observation_backend=str(runtime_cfg.get("batch_observation_backend", "auto")),
        batch_visual_backend=str(runtime_cfg.get("batch_visual_backend", "auto")),
        **env_settings,
    )
    rng = np.random.default_rng(int(seed))
    _obs = runtime.reset()
    step_times: list[float] = []
    timing_keys: dict[str, list[float]] = {}
    notes: list[str] = [
        f"observation_backend={runtime._batch_observation_backend_mode()}",
        f"visual_backend={runtime._batch_visual_backend_mode()}",
    ]
    try:
        for _ in range(int(steps)):
            actions = np.stack([_rand_action(runtime.action_space, rng) for _ in range(int(runtime.num_envs))], axis=0)
            t0 = time.perf_counter()
            _obs, _rewards, dones, infos = runtime.step(actions)
            step_times.append((time.perf_counter() - t0) * 1000.0)
            for info in infos:
                timing = _extract_timing(info)
                for key, value in timing.items():
                    timing_keys.setdefault(key, []).append(float(value))
            if bool(np.any(dones)):
                _obs = runtime.reset()
        slot_count = int(runtime.num_envs)
        timing = {
            "rss_bytes": float(_rss_bytes() or 0),
            "step_time_ms": _safe_mean(step_times),
            "worlds": float(runtime.world_count),
            "slots_per_world": float(runtime.slots_per_world),
            **_flatten_timing_stats("", timing_keys),
        }
        metrics = {
            "step_time_ms": float(timing.get("step_time_ms", 0.0)),
            "per_agent_step_time_ms": float(timing.get("step_time_ms", 0.0)) / float(max(1, slot_count)),
            "slot_count": float(slot_count),
            "world_count": float(runtime.world_count),
        }
        return BenchmarkResult(
            mode="cooperative_execution",
            steps=int(steps),
            env_count=int(runtime.world_count),
            slot_count=slot_count,
            metrics=metrics,
            timing=timing,
            notes=notes,
        )
    finally:
        runtime.close()


def run_benchmark(
    *,
    scenario_path: str,
    train_config: dict[str, Any],
    mode: str,
    steps: int,
    seed: int,
    n_envs: int,
    args: argparse.Namespace,
) -> BenchmarkResult | dict[str, Any]:
    mode = str(mode).strip().lower()
    if mode == "single_agent":
        return _run_single_agent(
            scenario_path=scenario_path,
            train_config=train_config,
            args=args,
            steps=steps,
            seed=seed,
        )
    if mode == "leader":
        return _run_leader(
            scenario_path=scenario_path,
            train_config=train_config,
            steps=steps,
            seed=seed,
        )
    if mode == "cooperative_execution":
        return _run_cooperative(
            scenario_path=scenario_path,
            train_config=train_config,
            args=args,
            steps=steps,
            seed=seed,
            n_envs=n_envs,
        )
    if mode == "all":
        single = _run_single_agent(
            scenario_path=scenario_path,
            train_config=train_config,
            args=args,
            steps=steps,
            seed=seed,
        )
        leader = _run_leader(
            scenario_path=scenario_path,
            train_config=train_config,
            steps=steps,
            seed=seed,
        )
        coop = _run_cooperative(
            scenario_path=scenario_path,
            train_config=train_config,
            args=args,
            steps=steps,
            seed=seed,
            n_envs=n_envs,
        )
        return {
            "mode": "all",
            "results": [asdict(single), asdict(leader), asdict(coop)],
        }
    raise ValueError(f"Unknown benchmark mode: {mode!r}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Multi-agent timing benchmark")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--train_config", required=True)
    parser.add_argument("--mode", default="all", choices=["single_agent", "leader", "cooperative_execution", "all"])
    parser.add_argument("--steps", type=int, default=32)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--n_envs", type=int, default=1)
    parser.add_argument("--include_visual", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--include_proprio", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--action_mode", type=str, default=None)
    parser.add_argument("--mission_obs_mode", type=str, default=None)
    parser.add_argument("--visual_downsample", type=int, default=None)
    parser.add_argument("--visual_update_interval", type=int, default=None)
    parser.add_argument("--step_info_mode", type=str, default=None)
    parser.add_argument("--execution_step_runtime_mode", type=str, default=None)
    parser.add_argument("--flight_shaping_backend", type=str, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    scenario_path = os.path.abspath(str(args.scenario))
    train_config_path = os.path.abspath(str(args.train_config))
    with open(train_config_path, "r", encoding="utf-8") as f:
        train_config = json.load(f)
    result = run_benchmark(
        scenario_path=scenario_path,
        train_config=train_config,
        mode=str(args.mode),
        steps=int(args.steps),
        seed=int(args.seed),
        n_envs=int(args.n_envs),
        args=args,
    )
    if isinstance(result, BenchmarkResult):
        payload: Any = asdict(result)
    else:
        payload = result
    print(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
