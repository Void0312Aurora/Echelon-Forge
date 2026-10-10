#!/usr/bin/env python3
"""Reproducible WorldBatch thread-count matrix benchmark.

This benchmark measures the maintained ``WorldBatchVecEnv`` path without
claiming that a local microbenchmark represents end-to-end policy training.
It records the effective worker count and per-stage timings so a thread-pool
decision can be made from repeatable data rather than from thread creation
cost alone.
"""

from __future__ import annotations

import argparse
import math
import os
import platform
import subprocess
import sys
import time
from typing import Any

import numpy as np

from python.runtime_bootstrap import configure_sim_log_level, ensure_repo_imports, resolve_repo_path

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

from python.rl.runtime.world_batch.vec_env import WorldBatchVecEnv  # noqa: E402
from tools.diagnostics.common import write_json_output  # noqa: E402


def _parse_int_list(raw: str, *, name: str) -> list[int]:
    values = [int(item.strip()) for item in str(raw).split(",") if item.strip()]
    if not values or any(value < 0 for value in values):
        raise ValueError(f"{name} must contain one or more non-negative integers")
    return values


def _percentile(samples: list[float], fraction: float) -> float:
    if not samples:
        raise ValueError("cannot summarize an empty sample set")
    ordered = sorted(float(sample) for sample in samples)
    position = (len(ordered) - 1) * float(fraction)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _summary(samples: list[float]) -> dict[str, Any]:
    if not samples:
        raise ValueError("cannot summarize an empty sample set")
    values = [float(sample) for sample in samples]
    return {
        "sample_count": len(values),
        "samples": values,
        "min": min(values),
        "median": float(_percentile(values, 0.50)),
        "p95": float(_percentile(values, 0.95)),
        "max": max(values),
    }


def _git_revision() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "unknown"
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def _build_actions(*, steps: int, n_envs: int, action_dim: int, seed: int) -> list[np.ndarray]:
    rng = np.random.RandomState(int(seed) & 0xFFFFFFFF)
    actions: list[np.ndarray] = []
    for _ in range(max(1, int(steps))):
        batch = rng.uniform(-0.25, 0.25, size=(int(n_envs), int(action_dim))).astype(np.float32)
        if action_dim >= 4:
            batch[:, 3] = rng.uniform(0.55, 0.85, size=(int(n_envs),)).astype(np.float32)
        actions.append(batch)
    return actions


def _run_case(
    *,
    scenario_path: str,
    n_envs: int,
    configured_threads: int,
    steps: int,
    repeats: int,
    warmup_steps: int,
    seed: int,
    env_kwargs: dict[str, Any],
) -> dict[str, Any]:
    vec_env = WorldBatchVecEnv(
        scenario_path=scenario_path,
        n_envs=int(n_envs),
        worker_threads=int(configured_threads),
        collect_step_timing=True,
        **env_kwargs,
    )
    try:
        action_dim = int(vec_env.action_space.shape[-1])
        actions = _build_actions(steps=steps, n_envs=n_envs, action_dim=action_dim, seed=seed)
        for _ in range(max(0, int(warmup_steps))):
            vec_env.reset()
            vec_env.step(actions[0])

        reset_samples: list[float] = []
        step_samples: list[float] = []
        stage_samples: dict[str, list[float]] = {}
        for repeat_idx in range(max(1, int(repeats))):
            reset_t0 = time.perf_counter()
            vec_env.reset()
            reset_samples.append(1000.0 * (time.perf_counter() - reset_t0) / float(n_envs))

            repeat_step_total_ms = 0.0
            repeat_stage_totals: dict[str, float] = {}
            for action in actions:
                step_t0 = time.perf_counter()
                vec_env.step(action)
                step_ms = 1000.0 * (time.perf_counter() - step_t0)
                repeat_step_total_ms += step_ms
                for name, value in dict(getattr(vec_env, "last_step_timing", {}) or {}).items():
                    repeat_stage_totals[name] = repeat_stage_totals.get(name, 0.0) + float(value)
            denominator = float(max(1, int(steps)) * int(n_envs))
            step_samples.append(repeat_step_total_ms / denominator)
            for name, value in repeat_stage_totals.items():
                stage_samples.setdefault(name, []).append(float(value) / denominator)

        effective_threads = int(vec_env.runtime_facade.effective_worker_threads())
    finally:
        vec_env.close()

    return {
        "n_envs": int(n_envs),
        "configured_worker_threads": int(configured_threads),
        "effective_worker_threads": effective_threads,
        "steps_per_repeat": int(steps),
        "repeats": int(max(1, repeats)),
        "warmup_steps": int(max(0, warmup_steps)),
        "reset_wall_ms_per_env": _summary(reset_samples),
        "step_wall_ms_per_env_step": _summary(step_samples),
        "step_stage_ms_per_env_step": {name: _summary(values) for name, values in sorted(stage_samples.items())},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="WorldBatch transient-thread matrix benchmark.")
    parser.add_argument("--scenario", default="scenarios/takeoff/takeoff.json")
    parser.add_argument("--n-envs", default="1,2,4,8,16,32,64", help="Comma-separated world counts.")
    parser.add_argument("--worker-threads", default="1,2,4,8,0", help="Comma-separated configured counts; 0 means auto.")
    parser.add_argument("--steps", type=int, default=64)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--warmup-steps", type=int, default=2)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--sim-log-level", default="warn")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    configure_sim_log_level(args.sim_log_level)
    scenario_path = os.path.abspath(args.scenario)
    if not os.path.exists(scenario_path):
        scenario_path = resolve_repo_path(args.scenario)
    n_envs_values = _parse_int_list(args.n_envs, name="--n-envs")
    thread_values = _parse_int_list(args.worker_threads, name="--worker-threads")
    if int(args.steps) <= 0 or int(args.repeats) <= 0:
        raise ValueError("--steps and --repeats must be positive")

    env_kwargs = {
        "include_visual": False,
        "include_proprio": False,
        "action_mode": "full",
        "mission_obs_mode": "nav_v2",
        "batch_observation_backend": "auto",
        "batch_visual_backend": "auto",
    }
    cases = []
    for n_envs in n_envs_values:
        for configured_threads in thread_values:
            cases.append(
                _run_case(
                    scenario_path=scenario_path,
                    n_envs=n_envs,
                    configured_threads=configured_threads,
                    steps=int(args.steps),
                    repeats=int(args.repeats),
                    warmup_steps=int(args.warmup_steps),
                    seed=int(args.seed) + n_envs * 1000 + configured_threads,
                    env_kwargs=env_kwargs,
                )
            )

    payload = {
        "benchmark": "world_batch_thread_matrix",
        "git_revision": _git_revision(),
        "scenario": scenario_path,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": sys.version,
            "logical_cpus": os.cpu_count(),
        },
        "n_envs": n_envs_values,
        "configured_worker_threads": thread_values,
        "steps": int(args.steps),
        "repeats": int(args.repeats),
        "warmup_steps": int(args.warmup_steps),
        "cases": cases,
    }
    print("WorldBatch transient-thread matrix")
    print("=" * 36)
    print(f"scenario: {scenario_path}")
    print(f"revision: {payload['git_revision']}")
    print(f"cases: {len(cases)}")
    for case in cases:
        median = case["step_wall_ms_per_env_step"]["median"]
        p95 = case["step_wall_ms_per_env_step"]["p95"]
        print(
            f"n_envs={case['n_envs']:>3} configured={case['configured_worker_threads']:>2} "
            f"effective={case['effective_worker_threads']:>2} "
            f"step_ms/env={median:.4f} p95={p95:.4f}"
        )
    write_json_output(str(args.json_out), payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
