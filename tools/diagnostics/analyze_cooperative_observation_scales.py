#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Any

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from gym_envs.universal_env import UniversalEnv
from python.env_config import resolve_env_settings
from python.rl.wrappers import get_action_wrapper_spec


INSTRUMENT_NAMES = [
    "ias",
    "mach",
    "alt_baro",
    "alt_radar",
    "vvi",
    "aoa",
    "beta",
    "pitch",
    "roll",
    "heading",
    "g_load",
    "g_load_axial",
    "p",
    "q",
    "r",
    "engine_rpm",
    "fuel_total",
    "fuel_flow",
    "gear_pos",
    "flaps_pos",
    "speedbrake_pos",
    "cmd_heading",
    "cmd_alt",
    "cmd_speed",
    "lat",
    "lon",
    "vn",
    "ve",
    "vd",
    "ground_speed",
    "ground_track",
    "wind_speed",
    "wind_dir",
    "oat",
    "gps_available",
    "position_uncertainty",
    "rwr_active",
    "missiles_remaining",
    "ils_loc_dev",
    "ils_gs_dev",
    "ils_valid",
    "ils_dme",
]

CONTACT_FIELD_NAMES = [
    "range_m",
    "azimuth_deg",
    "elevation_deg",
    "closing_speed_mps",
    "time_since_update_s",
]

MISSION_FIELD_NAMES = {
    "nav_v2_cooperative_takeoff_v1": [
        "command_code",
        "target_heading_deg",
        "target_altitude_m",
        "target_speed_mps",
        "selected_steerpoint",
        "steerpoint_mode_code",
        "dist_m",
        "bearing_rel_deg",
        "altitude_delta_m",
        "cdi_norm",
        "track_angle_error_deg",
        "leg_distance_remaining_m",
        "next_turn_deg",
        "distance_to_turn_m",
        "takeoff_procedure_code",
        "takeoff_clearance_code",
        "takeoff_interval_s",
        "runway_slot_code",
        "form_offset_x_m",
        "form_offset_y_m",
        "form_offset_z_m",
        "self_role_code",
        "self_formation_role_code",
        "relative_slot_code",
        "reference_relative_slot_code",
    ],
}


@dataclass
class RunningStats:
    count: int = 0
    sum: float = 0.0
    sum_sq: float = 0.0
    min: float = math.inf
    max: float = -math.inf
    max_abs: float = 0.0

    def update(self, values: np.ndarray) -> None:
        arr = np.asarray(values, dtype=np.float64).reshape(-1)
        if arr.size == 0:
            return
        finite = arr[np.isfinite(arr)]
        if finite.size == 0:
            return
        self.count += int(finite.size)
        self.sum += float(finite.sum())
        self.sum_sq += float(np.square(finite).sum())
        self.min = min(self.min, float(finite.min()))
        self.max = max(self.max, float(finite.max()))
        self.max_abs = max(self.max_abs, float(np.abs(finite).max()))

    def to_dict(self) -> dict[str, Any]:
        if self.count <= 0:
            return {"count": 0}
        mean = self.sum / float(self.count)
        var = max(0.0, self.sum_sq / float(self.count) - mean * mean)
        return {
            "count": int(self.count),
            "min": float(self.min),
            "max": float(self.max),
            "max_abs": float(self.max_abs),
            "mean": float(mean),
            "std": float(math.sqrt(var)),
        }


def _load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"expected dict JSON at {path!r}")
    return data


def _make_env(scenario_path: str, train_config: dict[str, Any]):
    class _Args:
        include_visual = None
        include_proprio = None
        action_mode = None
        mission_obs_mode = None
        visual_downsample = None
        visual_update_interval = None

    env_settings = resolve_env_settings(train_config, _Args())
    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
    env = UniversalEnv(os.path.abspath(scenario_path), **env_settings)
    if wrapper_class is not None:
        env = wrapper_class(env, **(wrapper_kwargs or {}))
    return env, env_settings


def _field_names_for_mission(mode: str, dim: int) -> list[str]:
    names = list(MISSION_FIELD_NAMES.get(str(mode).strip().lower(), []))
    if len(names) < int(dim):
        names.extend([f"mission_{idx}" for idx in range(len(names), int(dim))])
    return names[: int(dim)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze cooperative observation scales to guide numeric fixes.")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--train_config", required=True)
    parser.add_argument("--episodes", type=int, default=4)
    parser.add_argument("--max_steps", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--json_out", default="")
    args = parser.parse_args()

    train_config = _load_json(os.path.abspath(args.train_config))
    env, env_settings = _make_env(os.path.abspath(args.scenario), train_config)

    instrument_stats: dict[str, RunningStats] = {}
    contact_stats: dict[str, RunningStats] = {}
    mission_stats: dict[str, RunningStats] = {}

    try:
        mission_mode = str(env_settings["mission_obs_mode"])
        mission_names: list[str] | None = None

        for ep in range(int(args.episodes)):
            obs, _ = env.reset(seed=int(args.seed) + ep)
            steps = 0
            done = False
            while not done and steps < int(args.max_steps):
                instruments = np.asarray(obs["instruments"], dtype=np.float32).reshape(-1)
                contacts = np.asarray(obs["contacts"], dtype=np.float32)
                mission = np.asarray(obs["mission"], dtype=np.float32).reshape(-1)

                if mission_names is None:
                    mission_names = _field_names_for_mission(mission_mode, int(mission.size))

                for idx, value in enumerate(instruments):
                    name = INSTRUMENT_NAMES[idx] if idx < len(INSTRUMENT_NAMES) else f"instrument_{idx}"
                    instrument_stats.setdefault(name, RunningStats()).update(np.asarray([value], dtype=np.float32))

                for field_idx, field_name in enumerate(CONTACT_FIELD_NAMES):
                    if contacts.ndim == 2 and field_idx < contacts.shape[1]:
                        contact_stats.setdefault(field_name, RunningStats()).update(contacts[:, field_idx])

                for idx, value in enumerate(mission):
                    field_name = mission_names[idx]
                    mission_stats.setdefault(field_name, RunningStats()).update(np.asarray([value], dtype=np.float32))

                action = env.action_space.sample()
                obs, _, terminated, truncated, _ = env.step(action)
                steps += 1
                done = bool(terminated or truncated)

        payload = {
            "scenario": os.path.abspath(args.scenario),
            "train_config": os.path.abspath(args.train_config),
            "env_settings": env_settings,
            "episodes": int(args.episodes),
            "max_steps": int(args.max_steps),
            "instrument_stats": {k: v.to_dict() for k, v in instrument_stats.items()},
            "contact_stats": {k: v.to_dict() for k, v in contact_stats.items()},
            "mission_stats": {k: v.to_dict() for k, v in mission_stats.items()},
        }

        def _top_scale(items: dict[str, dict[str, Any]], limit: int = 8) -> list[tuple[str, float]]:
            rows = []
            for key, stats in items.items():
                rows.append((str(key), float(stats.get("max_abs", 0.0))))
            rows.sort(key=lambda x: x[1], reverse=True)
            return rows[:limit]

        print("=" * 60)
        print("COOPERATIVE OBSERVATION SCALE ANALYSIS")
        print(f"scenario:   {payload['scenario']}")
        print(f"train_cfg:  {payload['train_config']}")
        print(f"env:        {env_settings}")
        print("-" * 60)
        print("top instrument |max_abs|:")
        for name, value in _top_scale(payload["instrument_stats"]):
            print(f"  {name}: {value:.3f}")
        print("top contact |max_abs|:")
        for name, value in _top_scale(payload["contact_stats"]):
            print(f"  {name}: {value:.3f}")
        print("top mission |max_abs|:")
        for name, value in _top_scale(payload["mission_stats"]):
            print(f"  {name}: {value:.3f}")
        print("=" * 60)
        print(json.dumps(payload, indent=2, ensure_ascii=True))

        if args.json_out:
            out_path = os.path.abspath(args.json_out)
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=True)
                f.write("\n")
        return 0
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
