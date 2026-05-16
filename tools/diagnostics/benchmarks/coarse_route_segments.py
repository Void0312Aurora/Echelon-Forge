#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from typing import Any

import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "..", ".."))
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)

from python.testing.runtime import configure_sim_log_level, ensure_repo_imports, resolve_repo_path
from tools.diagnostics.common import load_json_config, write_json_output

REPO_ROOT = ensure_repo_imports()
os.chdir(REPO_ROOT)

from gym_envs.universal_env import UniversalEnv  # noqa: E402
from python.artifact_paths import resolve_artifact_path  # noqa: E402
from python.env_config import resolve_env_settings  # noqa: E402
from python.rl.planning.coarse_route_propagator import (  # noqa: E402
    CoarseRouteConfig,
    RouteSnapshot,
    compare_route_states,
    project_route_window,
    route_waypoints_from_iterable,
)
from python.rl.control.wrappers import get_action_wrapper_spec  # noqa: E402
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO  # noqa: E402


DEFAULT_SCENARIO = "scenarios/combined/takeoff_to_landing_continuous_train_v1.json"
DEFAULT_TRAIN_CONFIG = "examples/config/training/frozen/execution/p5_continuous_retrain_v1.json"
DEFAULT_MODEL = "experiments_tmp/20260318_p5_takeoff_to_landing_continuous_v3_retrain_v1/final_model.zip"


def _load_policy(model_path: str, algo: str):
    load_path = model_path[:-4] if model_path.endswith(".zip") else model_path
    algo_name = str(algo).strip()
    if algo_name in ("auto", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
        try:
            return AdaptiveKLPPO.load(load_path, device="cpu")
        except Exception:
            if algo_name != "auto":
                raise
    from stable_baselines3 import PPO

    return PPO.load(load_path, device="cpu")


def _build_env(scenario_path: str, train_config: dict[str, Any]):
    class _Args:
        include_visual = None
        include_proprio = None
        action_mode = None
        mission_obs_mode = None
        visual_downsample = None
        visual_update_interval = None
        execution_step_runtime_mode = None

    env_settings = resolve_env_settings(train_config, _Args())
    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
    env = UniversalEnv(os.path.abspath(scenario_path), **env_settings)
    if wrapper_class is not None:
        env = wrapper_class(env, **(wrapper_kwargs or {}))
    return env, env_settings


def _capture_snapshot(env) -> RouteSnapshot:
    base_env = env.unwrapped
    loader = base_env.loader
    sim = base_env.sim
    truth = getattr(base_env, "_last_truth", None) or sim.get_agent_observation(base_env.agent_id)
    inst = getattr(base_env, "_last_inst", None) or sim.get_instrument_state(base_env.agent_id)
    mission_cmd = dict(getattr(loader, "mission_cmd", {}) or {})
    return RouteSnapshot(
        sim_time_s=float(getattr(truth, "sim_time", float(getattr(base_env, "steps", 0)) * float(sim.get_time_step()))),
        x_m=float(getattr(truth, "x", 0.0)),
        y_m=float(getattr(truth, "y", 0.0)),
        altitude_m=float(getattr(truth, "z", 0.0)),
        heading_deg=float(getattr(truth, "heading", getattr(inst, "heading", 0.0))),
        ground_track_deg=float(getattr(inst, "ground_track", getattr(inst, "heading", getattr(truth, "heading", 0.0)))),
        ground_speed_mps=float(getattr(inst, "ground_speed", math.hypot(float(getattr(truth, "vx", 0.0)), float(getattr(truth, "vy", 0.0))))),
        vertical_speed_mps=float(getattr(inst, "vvi", -float(getattr(truth, "vz", 0.0)))),
        wind_speed_mps=float(getattr(inst, "wind_speed", 0.0)),
        wind_from_deg=float(getattr(inst, "wind_dir", 0.0)),
        target_heading_deg=float(mission_cmd.get("target_heading", 0.0)),
        target_altitude_m=float(mission_cmd.get("target_altitude", 0.0)),
        target_speed_mps=float(mission_cmd.get("target_speed", 0.0)),
        lnav_bank_limit_deg=float(mission_cmd.get("lnav_bank_limit_deg", 25.0)),
        command_code=int(mission_cmd.get("command_code", 0) or 0),
        waypoint_idx=int(getattr(loader, "waypoint_idx", 0) or 0),
    )


def _parse_horizons(raw: str) -> list[float]:
    out: list[float] = []
    for item in str(raw or "").split(","):
        item = item.strip()
        if not item:
            continue
        out.append(float(item))
    return [x for x in out if x > 0.0]


def _summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {"count": 0.0, "mean": 0.0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "max": 0.0}
    arr = np.asarray(values, dtype=np.float64)
    return {
        "count": float(arr.size),
        "mean": float(np.mean(arr)),
        "p50": float(np.percentile(arr, 50)),
        "p90": float(np.percentile(arr, 90)),
        "p95": float(np.percentile(arr, 95)),
        "max": float(np.max(arr)),
    }


def _action_delta_rms(actions: list[np.ndarray]) -> float:
    if len(actions) < 2:
        return 0.0
    diffs = [float(np.linalg.norm(actions[i + 1] - actions[i])) for i in range(len(actions) - 1)]
    if not diffs:
        return 0.0
    arr = np.asarray(diffs, dtype=np.float64)
    return float(np.sqrt(np.mean(arr * arr)))


def main() -> int:
    parser = argparse.ArgumentParser(description="Quantify coarse route-segment errors against fine p5 rollouts.")
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--train_config", default=DEFAULT_TRAIN_CONFIG)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--algo", default="auto")
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max_steps", type=int, default=16000)
    parser.add_argument("--horizons_s", default="2,5,10")
    parser.add_argument("--sample_stride_steps", type=int, default=20)
    parser.add_argument("--start_waypoint_idx", type=int, default=1)
    parser.add_argument("--stop_before_terminal_waypoints", type=int, default=3)
    parser.add_argument("--max_windows", type=int, default=256)
    parser.add_argument("--coarse_dt_s", type=float, default=0.5)
    parser.add_argument("--sim-log-level", default="warn")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    configure_sim_log_level(args.sim_log_level)
    scenario_path = os.path.abspath(args.scenario)
    if not os.path.exists(scenario_path):
        scenario_path = resolve_repo_path(args.scenario)
    train_config_path = os.path.abspath(args.train_config)
    if not os.path.exists(train_config_path):
        train_config_path = resolve_repo_path(args.train_config)
    model_path = resolve_artifact_path(args.model) or os.path.abspath(args.model)
    train_config = load_json_config(train_config_path)
    model = _load_policy(model_path, algo=str(args.algo))
    env, env_settings = _build_env(scenario_path, train_config)

    horizons_s = _parse_horizons(args.horizons_s)
    if not horizons_s:
        raise ValueError("at least one positive horizon is required")

    aggregate_errors: dict[float, dict[str, list[float]]] = {
        horizon: defaultdict(list) for horizon in horizons_s
    }
    aggregate_flags: dict[float, dict[str, int]] = {
        horizon: {"window_count": 0, "waypoint_boundary_count": 0, "command_change_count": 0} for horizon in horizons_s
    }

    cfg = CoarseRouteConfig(internal_dt_s=float(args.coarse_dt_s))
    route_lengths: list[int] = []
    collected_windows = 0

    try:
        for ep in range(int(args.episodes)):
            obs, _ = env.reset(seed=int(args.seed) + ep)
            base_env = env.unwrapped
            loader = base_env.loader
            route_waypoints = route_waypoints_from_iterable(
                list(getattr(loader, "waypoints", []) or []),
                default_speed_mps=float(getattr(loader, "mission_cmd", {}).get("target_speed", 0.0)),
            )
            route_lengths.append(len(route_waypoints))

            states: list[RouteSnapshot] = []
            rewards: list[float] = []
            actions: list[np.ndarray] = []
            done = False
            while not done and len(rewards) < int(args.max_steps):
                states.append(_capture_snapshot(env))
                action, _ = model.predict(obs, deterministic=True)
                action_arr = np.asarray(action, dtype=np.float32).reshape(-1)
                obs, reward, terminated, truncated, _info = env.step(action)
                actions.append(action_arr)
                rewards.append(float(reward))
                current_state = _capture_snapshot(env)
                remaining_route = len(route_waypoints) - int(current_state.waypoint_idx)
                if (
                    len(route_waypoints) > 0
                    and int(current_state.command_code) == 3
                    and remaining_route <= max(0, int(args.stop_before_terminal_waypoints))
                ):
                    done = True
                done = done or bool(terminated or truncated)

            states.append(_capture_snapshot(env))

            candidate_indices: list[int] = []
            for idx in range(0, len(rewards), max(1, int(args.sample_stride_steps))):
                snap = states[idx]
                if int(snap.command_code) != 3:
                    continue
                if int(snap.waypoint_idx) < int(args.start_waypoint_idx):
                    continue
                if int(snap.waypoint_idx) >= max(0, len(route_waypoints) - int(args.stop_before_terminal_waypoints)):
                    continue
                candidate_indices.append(idx)
                if len(candidate_indices) >= int(args.max_windows):
                    break

            for start_idx in candidate_indices:
                for horizon_s in horizons_s:
                    horizon_steps = max(1, int(round(float(horizon_s) / 0.05)))
                    end_idx = start_idx + horizon_steps
                    if end_idx >= len(states):
                        continue
                    start_state = states[start_idx]
                    future_state = states[end_idx]
                    reward_window = rewards[start_idx:end_idx]
                    action_window = actions[start_idx:end_idx]
                    forecast = project_route_window(
                        start_state,
                        waypoints=route_waypoints,
                        horizon_s=float(horizon_s),
                        config=cfg,
                    )
                    errors = compare_route_states(forecast.state, future_state)
                    bucket = aggregate_errors[horizon_s]
                    bucket["position_error_m"].append(float(errors.position_error_m))
                    bucket["altitude_error_m"].append(float(errors.altitude_error_m))
                    bucket["ground_speed_error_mps"].append(float(errors.ground_speed_error_mps))
                    bucket["track_error_deg"].append(float(errors.track_error_deg))
                    bucket["reward_sum"].append(float(np.sum(np.asarray(reward_window, dtype=np.float64))))
                    bucket["reward_std"].append(float(np.std(np.asarray(reward_window, dtype=np.float64))) if reward_window else 0.0)
                    bucket["action_delta_rms"].append(float(_action_delta_rms(action_window)))
                    flags = aggregate_flags[horizon_s]
                    flags["window_count"] += 1
                    if int(future_state.waypoint_idx) != int(start_state.waypoint_idx):
                        flags["waypoint_boundary_count"] += 1
                    if int(future_state.command_code) != int(start_state.command_code):
                        flags["command_change_count"] += 1
                    collected_windows += 1

        results: dict[str, Any] = {
            "scenario": scenario_path,
            "train_config": train_config_path,
            "model": model_path,
            "episodes": int(args.episodes),
            "seed_start": int(args.seed),
            "env_settings": env_settings,
            "route_lengths": route_lengths,
            "horizons_s": horizons_s,
            "sample_stride_steps": int(args.sample_stride_steps),
            "coarse_internal_dt_s": float(args.coarse_dt_s),
            "max_windows": int(args.max_windows),
            "collected_windows_total": int(collected_windows),
            "by_horizon": {},
        }

        for horizon_s in horizons_s:
            flag_row = aggregate_flags[horizon_s]
            window_count = max(1, int(flag_row["window_count"]))
            results["by_horizon"][str(horizon_s)] = {
                "decision_reduction_x": float(round(float(horizon_s) / 0.05)),
                "window_count": int(flag_row["window_count"]),
                "waypoint_boundary_rate": float(flag_row["waypoint_boundary_count"] / window_count),
                "command_change_rate": float(flag_row["command_change_count"] / window_count),
                "position_error_m": _summary(list(aggregate_errors[horizon_s]["position_error_m"])),
                "altitude_error_m": _summary(list(aggregate_errors[horizon_s]["altitude_error_m"])),
                "ground_speed_error_mps": _summary(list(aggregate_errors[horizon_s]["ground_speed_error_mps"])),
                "track_error_deg": _summary(list(aggregate_errors[horizon_s]["track_error_deg"])),
                "reward_sum": _summary(list(aggregate_errors[horizon_s]["reward_sum"])),
                "reward_std": _summary(list(aggregate_errors[horizon_s]["reward_std"])),
                "action_delta_rms": _summary(list(aggregate_errors[horizon_s]["action_delta_rms"])),
            }

        print("Coarse Route Segment Benchmark")
        print("=" * 31)
        print(f"scenario            : {scenario_path}")
        print(f"train_config        : {train_config_path}")
        print(f"model               : {model_path}")
        print(f"episodes            : {int(args.episodes)}")
        print(f"route lengths       : {route_lengths}")
        print(f"windows collected   : {int(collected_windows)}")
        print("-" * 31)
        for horizon_s in horizons_s:
            row = results["by_horizon"][str(horizon_s)]
            print(
                f"h={horizon_s:>4.1f}s "
                f"decision_x={row['decision_reduction_x']:.0f} "
                f"pos_mean={row['position_error_m']['mean']:.1f}m "
                f"alt_mean={row['altitude_error_m']['mean']:.1f}m "
                f"spd_mean={row['ground_speed_error_mps']['mean']:.2f}mps "
                f"trk_mean={row['track_error_deg']['mean']:.2f}deg "
                f"wp_boundary={row['waypoint_boundary_rate']:.3f} "
                f"reward_std={row['reward_std']['mean']:.3f} "
                f"action_delta_rms={row['action_delta_rms']['mean']:.3f}"
            )

        write_json_output(str(args.json_out), results)
        return 0
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
