#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import torch
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from gym_envs.leader_env import LeaderTrainingEnv  # noqa: E402
from python.rl.runtime.shared_memory_vec_env import SharedMemorySubprocVecEnv  # noqa: E402
from python.testing.runtime import configure_sim_log_level  # noqa: E402
from tools.diagnostics.common import average_timing_sums, merge_timing_sums  # noqa: E402


def _collect_reset_timings(reset_infos) -> tuple[dict[str, float], dict[str, float]]:
    leader_sums: dict[str, float] = {}
    execution_sums: dict[str, float] = {}
    leader_count = 0
    execution_count = 0
    for info in list(reset_infos or []):
        if not isinstance(info, dict):
            continue
        if isinstance(info.get("timing"), dict):
            merge_timing_sums(leader_sums, info.get("timing"))
            leader_count += 1
        if isinstance(info.get("execution_reset_timing"), dict):
            merge_timing_sums(execution_sums, info.get("execution_reset_timing"))
            execution_count += 1
    return (
        average_timing_sums(leader_sums, count=leader_count),
        average_timing_sums(execution_sums, count=execution_count),
    )


def _collect_step_timings(infos) -> tuple[dict[str, float], dict[str, float], float]:
    leader_sums: dict[str, float] = {}
    execution_sums: dict[str, float] = {}
    leader_count = 0
    execution_count = 0
    low_level_steps = 0.0
    low_level_count = 0
    for info in list(infos or []):
        if not isinstance(info, dict):
            continue
        if isinstance(info.get("timing"), dict):
            merge_timing_sums(leader_sums, info.get("timing"))
            leader_count += 1
        if isinstance(info.get("execution_timing"), dict):
            merge_timing_sums(execution_sums, info.get("execution_timing"))
            execution_count += 1
        if "leader_low_level_steps" in info:
            try:
                low_level_steps += float(info.get("leader_low_level_steps", 0.0))
                low_level_count += 1
            except Exception:
                pass
    avg_low_level_steps = low_level_steps / float(low_level_count) if low_level_count > 0 else 0.0
    return (
        average_timing_sums(leader_sums, count=leader_count),
        average_timing_sums(execution_sums, count=execution_count),
        float(avg_low_level_steps),
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Quick throughput probe for leader-layer environments.")
    parser.add_argument("--scenario", required=True, help="Scenario JSON path.")
    parser.add_argument("--train_config", required=True, help="Leader-layer train config JSON path.")
    parser.add_argument("--n_envs", type=int, default=None, help="Override number of envs from config.")
    parser.add_argument("--leader_steps", type=int, default=16, help="Number of vectorized leader steps to run.")
    parser.add_argument(
        "--vec_backend",
        choices=["auto", "subproc", "shared", "dummy"],
        default="auto",
        help="Vector env backend for the probe.",
    )
    parser.add_argument("--torch_threads", type=int, default=None, help="Optional PyTorch intra-op thread count.")
    parser.add_argument("--torch_interop_threads", type=int, default=None, help="Optional PyTorch inter-op thread count.")
    parser.add_argument("--execution_device", type=str, default=None, help="Device for low-level execution inference.")
    parser.add_argument(
        "--execution_use_autocast",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable autocast for low-level execution inference.",
    )
    parser.add_argument(
        "--collect-step-timing",
        "--collect_step_timing",
        dest="collect_step_timing",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Collect and report per-segment timing breakdowns from the leader env.",
    )
    parser.add_argument(
        "--execution-step-runtime-mode",
        "--execution_step_runtime_mode",
        dest="execution_step_runtime_mode",
        choices=["compiled", "legacy"],
        default=None,
        help="Select the execution step runtime path inside the low-level execution env.",
    )
    parser.add_argument(
        "--sim-log-level",
        "--sim_log_level",
        dest="sim_log_level",
        default="warn",
        help="Simulation log level for the probe process (for example: trace, debug, info, warn, error).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    configure_sim_log_level(args.sim_log_level)

    scenario_path = os.path.abspath(args.scenario)
    train_cfg_path = os.path.abspath(args.train_config)
    with open(train_cfg_path, "r", encoding="utf-8") as f:
        train_config = json.load(f)

    if str(train_config.get("agent_layer", "")).strip().lower() != "leader":
        raise ValueError("leader_perf_probe.py requires a train config with agent_layer='leader'")

    if args.torch_threads is not None:
        torch.set_num_threads(max(1, int(args.torch_threads)))
    if args.torch_interop_threads is not None:
        try:
            torch.set_num_interop_threads(max(1, int(args.torch_interop_threads)))
        except RuntimeError:
            pass

    leader_cfg = train_config.get("leader_env", {}) if isinstance(train_config.get("leader_env", {}), dict) else {}
    runtime_cfg = train_config.get("runtime", {}) if isinstance(train_config.get("runtime", {}), dict) else {}
    n_envs = int(args.n_envs if args.n_envs is not None else train_config.get("n_envs", 1))
    decision_interval_steps = int(leader_cfg.get("decision_interval_steps", 20))
    leader_execution_torch_threads = runtime_cfg.get("leader_execution_torch_threads")
    if leader_execution_torch_threads is None:
        if n_envs > 1 and str(leader_cfg.get("execution_backend", "scripted")).strip().lower() == "frozen_model":
            leader_execution_torch_threads = 1
    leader_execution_torch_interop_threads = runtime_cfg.get("leader_execution_torch_interop_threads")
    if leader_execution_torch_interop_threads is None:
        if n_envs > 1 and str(leader_cfg.get("execution_backend", "scripted")).strip().lower() == "frozen_model":
            leader_execution_torch_interop_threads = 1

    if args.vec_backend == "subproc":
        vec_cls = SubprocVecEnv
    elif args.vec_backend == "shared":
        vec_cls = SharedMemorySubprocVecEnv
    elif args.vec_backend == "dummy":
        vec_cls = DummyVecEnv
    else:
        vec_cls = SubprocVecEnv if n_envs > 1 else DummyVecEnv

    vec_env = make_vec_env(
        LeaderTrainingEnv,
        n_envs=n_envs,
        env_kwargs={
            "scenario_path": scenario_path,
            "decision_interval_steps": decision_interval_steps,
            "execution_backend": str(leader_cfg.get("execution_backend", "scripted")),
            "execution_train_config": leader_cfg.get("execution_train_config"),
            "execution_model_path": leader_cfg.get("execution_model_path"),
            "execution_algo": str(leader_cfg.get("execution_algo", "auto")),
            "execution_action_repeat": int(leader_cfg.get("execution_action_repeat", 1)),
            "scripted_transition_alt_agl_m": float(leader_cfg.get("scripted_transition_alt_agl_m", 140.0)),
            "heading_bias_limit_deg": float(leader_cfg.get("heading_bias_limit_deg", 45.0)),
            "altitude_bias_limit_m": float(leader_cfg.get("altitude_bias_limit_m", 800.0)),
            "speed_bias_limit_mps": float(leader_cfg.get("speed_bias_limit_mps", 40.0)),
            "command_change_penalty": float(leader_cfg.get("command_change_penalty", 0.0)),
            "teacher_keep_deadband": float(leader_cfg.get("teacher_keep_deadband", 0.20)),
            "invalid_phase_penalty": float(leader_cfg.get("invalid_phase_penalty", 0.0)),
            "premature_approach_penalty": float(leader_cfg.get("premature_approach_penalty", 0.0)),
            "baseline_deviation_penalty": float(leader_cfg.get("baseline_deviation_penalty", 0.0)),
            "mode_change_penalty": float(leader_cfg.get("mode_change_penalty", 0.0)),
            "approach_gate_distance_m": float(leader_cfg.get("approach_gate_distance_m", 18000.0)),
            "approach_gate_cross_m": float(leader_cfg.get("approach_gate_cross_m", 3500.0)),
            "approach_gate_heading_error_deg": float(leader_cfg.get("approach_gate_heading_error_deg", 85.0)),
            "execution_step_runtime_mode": args.execution_step_runtime_mode,
            "collect_step_timing": bool(args.collect_step_timing),
            "execution_torch_threads": (
                None if leader_execution_torch_threads is None else int(leader_execution_torch_threads)
            ),
            "execution_torch_interop_threads": (
                None
                if leader_execution_torch_interop_threads is None
                else int(leader_execution_torch_interop_threads)
            ),
            "execution_device": str(args.execution_device or runtime_cfg.get("execution_device", "cpu")),
            "execution_use_autocast": bool(
                runtime_cfg.get("execution_use_autocast", False)
                if args.execution_use_autocast is None
                else args.execution_use_autocast
            ),
        },
        vec_env_cls=vec_cls,
        vec_env_kwargs={},
    )

    try:
        obs = vec_env.reset()
        reset_infos = list(getattr(vec_env, "reset_infos", []) or [])
        leader_reset_timing, execution_reset_timing = _collect_reset_timings(reset_infos)
        action = np.zeros((n_envs, 6), dtype=np.float32)
        leader_step_timing_sums: dict[str, float] = {}
        execution_step_timing_sums: dict[str, float] = {}
        timed_step_count = 0
        timed_execution_count = 0
        avg_low_level_steps_total = 0.0
        avg_low_level_steps_count = 0
        t0 = time.perf_counter()
        for _ in range(int(args.leader_steps)):
            obs, rewards, dones, infos = vec_env.step(action)
            _ = (obs, rewards, infos)
            leader_step_timing, execution_step_timing, avg_low_level_steps = _collect_step_timings(infos)
            if leader_step_timing:
                merge_timing_sums(leader_step_timing_sums, leader_step_timing)
                timed_step_count += 1
            if execution_step_timing:
                merge_timing_sums(execution_step_timing_sums, execution_step_timing)
                timed_execution_count += 1
            if avg_low_level_steps > 0.0:
                avg_low_level_steps_total += float(avg_low_level_steps)
                avg_low_level_steps_count += 1
            if np.any(dones):
                pass
        elapsed = max(1.0e-9, time.perf_counter() - t0)
        leader_steps_total = float(n_envs) * float(args.leader_steps)
        leader_fps = leader_steps_total / elapsed
        low_level_fps = leader_fps * float(decision_interval_steps)
        leader_step_timing = average_timing_sums(leader_step_timing_sums, count=timed_step_count)
        execution_step_timing = average_timing_sums(execution_step_timing_sums, count=timed_execution_count)
        avg_low_level_steps = (
            avg_low_level_steps_total / float(avg_low_level_steps_count)
            if avg_low_level_steps_count > 0
            else 0.0
        )
        print(
            json.dumps(
                {
                    "scenario": scenario_path,
                    "train_config": train_cfg_path,
                    "vec_backend": str(args.vec_backend if args.vec_backend != "auto" else vec_cls.__name__),
                    "n_envs": n_envs,
                    "leader_steps": int(args.leader_steps),
                    "decision_interval_steps": decision_interval_steps,
                    "execution_action_repeat": int(leader_cfg.get("execution_action_repeat", 1)),
                    "leader_fps": leader_fps,
                    "estimated_low_level_fps": low_level_fps,
                    "torch_threads": int(torch.get_num_threads()),
                    "leader_execution_torch_threads": leader_execution_torch_threads,
                    "leader_execution_torch_interop_threads": leader_execution_torch_interop_threads,
                    "execution_step_runtime_mode": args.execution_step_runtime_mode,
                    "collect_step_timing": bool(args.collect_step_timing),
                    "sim_log_level": str(args.sim_log_level),
                    "leader_reset_timing_ms_per_env": leader_reset_timing,
                    "execution_reset_timing_ms_per_env": execution_reset_timing,
                    "leader_step_timing_ms_per_env_step": leader_step_timing,
                    "execution_step_timing_ms_per_env_step": execution_step_timing,
                    "avg_low_level_steps_per_leader_step": float(avg_low_level_steps),
                },
                ensure_ascii=True,
            )
        )
    finally:
        vec_env.close()


if __name__ == "__main__":
    main()
