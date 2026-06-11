#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.env_config import resolve_env_settings
from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv
from python.training.bootstrap import validate_declared_training_entry_env_surface, validate_declared_training_entry_paths
from tools.eval.sb3_eval_base import load_json_config, write_json_output


FORBIDDEN_REWARD_TERMS = {
    "off_runway_penalty",
    "naval_off_runway_penalty_suppressed",
    "speed_reward",
    "roll_stability",
    "weapon_release",
    "fire_weapon",
    "fire_gun",
    "damage",
    "damage_reward",
    "kill",
    "kill_reward",
    "hit",
    "intercept",
}

REQUIRED_REWARD_TERMS = {
    "naval_station_error_penalty",
    "naval_screen_separation_penalty",
    "naval_contact_maintained_bonus",
    "naval_shared_track_bonus",
    "naval_pre_fire_roe_hold_bonus",
}


class _EnvArgs:
    include_visual = None
    include_proprio = None
    action_mode = None
    mission_obs_mode = None
    visual_downsample = None
    visual_update_interval = None
    temporal_history_len = None
    execution_step_runtime_mode = None
    step_info_mode = "full"
    flight_shaping_backend = None
    runtime_compatibility_enabled = None


def _finite_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    return out if np.isfinite(out) else float(default)


def _slot_control_summary(env: CooperativeWorldBatchVecEnv) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, slot in enumerate(env.slot_control_slots()):
        out.append(
            {
                "slot_index": int(idx),
                "entity_name": str(getattr(slot, "entity_name", "") or ""),
                "formation_role_id": str(getattr(slot, "formation_role_id", "") or ""),
                "role_code": None if getattr(slot, "role_code", None) is None else int(getattr(slot, "role_code")),
                "relative_slot_code": (
                    None
                    if getattr(slot, "relative_slot_code", None) is None
                    else int(getattr(slot, "relative_slot_code"))
                ),
                "reference_entity_name": getattr(slot, "reference_entity_name", None),
                "policy_route": getattr(slot, "policy_route", None),
                "roster_index": int(getattr(slot, "roster_index", idx)),
            }
        )
    return out


def _active_roster_summary(env: CooperativeWorldBatchVecEnv) -> list[dict[str, Any]]:
    for slot_state in getattr(env, "_slots", []):
        if slot_state is None:
            continue
        roster = list(getattr(slot_state.loader, "active_roster", []) or [])
        out: list[dict[str, Any]] = []
        for idx, member in enumerate(roster):
            out.append(
                {
                    "roster_index": int(idx),
                    "entity_name": str(getattr(member, "entity_name", "") or ""),
                    "is_agent": bool(getattr(member, "is_agent", True)),
                    "reference_entity_name": getattr(member, "reference_entity_name", None),
                    "policy_route": getattr(member, "policy_route", None),
                    "role_code": (
                        None if getattr(member, "role_code", None) is None else int(getattr(member, "role_code"))
                    ),
                    "relative_slot_code": (
                        None
                        if getattr(member, "relative_slot_code", None) is None
                        else int(getattr(member, "relative_slot_code"))
                    ),
                }
            )
        return out
    return []


def _mission_status_list(info: dict[str, Any]) -> list[float]:
    try:
        return [float(x) for x in np.asarray(info.get("mission_status", []), dtype=np.float32).reshape(-1)]
    except Exception:
        return []


def _build_env_settings(train_config: dict[str, Any]) -> dict[str, Any]:
    env_settings = resolve_env_settings(train_config, _EnvArgs())
    env_settings["step_info_mode"] = "full"
    return env_settings


def _load_validated_train_config(scenario_path: str, train_config_path: str) -> dict[str, Any]:
    train_config = load_json_config(os.path.abspath(train_config_path))
    entry_error = validate_declared_training_entry_paths(
        scenario_path=os.path.abspath(scenario_path),
        train_cfg_path=os.path.abspath(train_config_path),
        train_config=train_config,
    )
    if entry_error is not None:
        raise ValueError(entry_error)
    env_settings = _build_env_settings(train_config)
    env_surface_error = validate_declared_training_entry_env_surface(
        train_config=train_config,
        env_settings=env_settings,
    )
    if env_surface_error is not None:
        raise ValueError(env_surface_error)
    return train_config


def _load_train_config_unchecked(train_config_path: str) -> dict[str, Any]:
    return load_json_config(os.path.abspath(train_config_path))


def _reward_term_sums(last_info: dict[str, Any], accum: dict[str, float]) -> dict[str, float]:
    reward_terms_last = {
        str(key): _finite_float(value)
        for key, value in dict(last_info.get("reward_terms", {}) or {}).items()
    }
    for key, value in reward_terms_last.items():
        accum[str(key)] += float(value)
    return reward_terms_last


def _run_fixed_action_eval(
    *,
    scenario_path: str,
    train_config_path: str,
    steps: int,
    seed: int,
    worker_threads: int,
    action: np.ndarray,
    validate_entry_scenario: bool = True,
) -> dict[str, Any]:
    train_config = (
        _load_validated_train_config(scenario_path, train_config_path)
        if bool(validate_entry_scenario)
        else _load_train_config_unchecked(train_config_path)
    )
    env_settings = _build_env_settings(train_config)
    env = CooperativeWorldBatchVecEnv(
        scenario_path=os.path.abspath(scenario_path),
        n_envs=1,
        worker_threads=max(1, int(worker_threads)),
        **env_settings,
    )
    try:
        env.seed(int(seed))
        obs = env.reset()
        del obs

        action_arr = np.asarray(action, dtype=np.float32).reshape(1, int(env.action_space.shape[0]))
        reward_total = 0.0
        reward_terms_sum: dict[str, float] = defaultdict(float)
        reward_terms_last: dict[str, float] = {}
        termination_counts: Counter[str] = Counter()
        finite_reward = True
        done = False
        final_info: dict[str, Any] = {}
        first_status: list[float] = []
        executed_steps = 0

        for _step in range(max(1, int(steps))):
            _obs, rewards, dones, infos = env.step(action_arr)
            reward = _finite_float(rewards[0], default=float("nan"))
            if not np.isfinite(reward):
                finite_reward = False
                reward = 0.0
            reward_total += float(reward)
            executed_steps += 1
            final_info = dict(infos[0])
            reward_terms_last = _reward_term_sums(final_info, reward_terms_sum)
            status = _mission_status_list(final_info)
            if not first_status:
                first_status = list(status)
            reason = str(final_info.get("termination_reason", "") or "").strip()
            if reason:
                termination_counts[reason] += 1
            if bool(dones[0]):
                done = True
                break

        present_terms = set(reward_terms_sum)
        return {
            "requested_steps": int(steps),
            "executed_steps": int(executed_steps),
            "done": bool(done),
            "finite_reward": bool(finite_reward),
            "action": [float(x) for x in action_arr.reshape(-1)],
            "reward_total": float(reward_total),
            "reward_mean": float(reward_total / max(1, executed_steps)),
            "reward_terms_sum": dict(sorted(reward_terms_sum.items())),
            "reward_terms_last": dict(sorted(reward_terms_last.items())),
            "forbidden_reward_terms_present": sorted(present_terms & FORBIDDEN_REWARD_TERMS),
            "termination_counts": dict(termination_counts),
            "first_mission_status": first_status,
            "final_mission_status": _mission_status_list(final_info),
        }
    finally:
        env.close()


def run_baseline_eval(
    *,
    scenario_path: str,
    train_config_path: str,
    steps: int,
    seed: int,
    worker_threads: int,
) -> dict[str, Any]:
    train_config = _load_validated_train_config(scenario_path, train_config_path)
    env_settings = _build_env_settings(train_config)
    env = CooperativeWorldBatchVecEnv(
        scenario_path=os.path.abspath(scenario_path),
        n_envs=1,
        worker_threads=max(1, int(worker_threads)),
        **env_settings,
    )
    try:
        env.seed(int(seed))
        obs = env.reset()
        del obs

        slot_control = _slot_control_summary(env)
        active_roster = _active_roster_summary(env)
        action = np.zeros((env.num_envs, int(env.action_space.shape[0])), dtype=np.float32)
        reward_total = 0.0
        reward_terms_sum: dict[str, float] = defaultdict(float)
        reward_terms_last: dict[str, float] = {}
        termination_counts: Counter[str] = Counter()
        finite_reward = True
        done = False
        final_info: dict[str, Any] = {}
        executed_steps = 0

        for _step in range(max(1, int(steps))):
            _obs, rewards, dones, infos = env.step(action)
            reward = _finite_float(rewards[0], default=float("nan"))
            if not np.isfinite(reward):
                finite_reward = False
                reward = 0.0
            reward_total += float(reward)
            executed_steps += 1
            final_info = dict(infos[0])
            reward_terms_last = _reward_term_sums(final_info, reward_terms_sum)
            reason = str(final_info.get("termination_reason", "") or "").strip()
            if reason:
                termination_counts[reason] += 1
            if bool(dones[0]):
                done = True
                break

        present_terms = set(reward_terms_sum)
        forbidden_present = sorted(present_terms & FORBIDDEN_REWARD_TERMS)
        required_missing = sorted(REQUIRED_REWARD_TERMS - present_terms)
        policy_slot_count = int(env.num_envs)
        active_roster_count = int(len(active_roster))
        non_agent_roster_count = int(sum(1 for member in active_roster if not bool(member.get("is_agent", True))))
        passed = bool(
            finite_reward
            and policy_slot_count == 1
            and active_roster_count >= 2
            and non_agent_roster_count >= 1
            and not forbidden_present
            and not required_missing
        )

        return {
            "mode": "naval_station_cooperative_zero_action_baseline",
            "scenario": os.path.abspath(scenario_path),
            "train_config": os.path.abspath(train_config_path),
            "seed": int(seed),
            "requested_steps": int(steps),
            "executed_steps": int(executed_steps),
            "done": bool(done),
            "passed": bool(passed),
            "env_settings": env_settings,
            "slots_per_world": int(env.slots_per_world),
            "policy_slot_count": int(policy_slot_count),
            "active_roster_count": int(active_roster_count),
            "non_agent_roster_count": int(non_agent_roster_count),
            "slot_control": slot_control,
            "active_roster": active_roster,
            "reward_total": float(reward_total),
            "reward_mean": float(reward_total / max(1, executed_steps)),
            "reward_terms_sum": dict(sorted(reward_terms_sum.items())),
            "reward_terms_last": dict(sorted(reward_terms_last.items())),
            "required_reward_terms": sorted(REQUIRED_REWARD_TERMS),
            "required_reward_terms_missing": required_missing,
            "forbidden_reward_terms": sorted(FORBIDDEN_REWARD_TERMS),
            "forbidden_reward_terms_present": forbidden_present,
            "finite_reward": bool(finite_reward),
            "termination_counts": dict(termination_counts),
            "final_mission_status": _mission_status_list(final_info),
        }
    finally:
        env.close()


def _derive_station_radius_offset_scenario(
    *,
    scenario_path: str,
    offset_m: float,
    output_path: str,
    reward_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scenario = load_json_config(os.path.abspath(scenario_path))
    if isinstance(reward_overrides, dict) and reward_overrides:
        rewards = dict(scenario.get("rewards", {}) or {})
        rewards.update(dict(reward_overrides))
        scenario["rewards"] = rewards
    task = dict(scenario.get("task_order", {}) or {})
    station_radius_m = float(task.get("station_radius_m", 0.0)) + float(offset_m)
    heading_rad = math.radians(float(task.get("station_heading_deg", 0.0)))
    entities = list(scenario.get("entities", []) or [])
    ref = next(entity for entity in entities if entity.get("name") == "Blue_HVU_TAKE1")
    ddg = next(entity for entity in entities if entity.get("name") == "Blue_Screen_DDG51")
    ref_pos = list(ref.get("pos", [0.0, 0.0, 0.0]))
    ddg["pos"] = [
        float(ref_pos[0]) + math.sin(heading_rad) * station_radius_m,
        float(ref_pos[1]) + math.cos(heading_rad) * station_radius_m,
        0.0,
    ]
    Path(output_path).write_text(json.dumps(scenario, indent=2, ensure_ascii=True), encoding="utf-8")
    return {
        "station_radius_offset_m": float(offset_m),
        "derived_scenario": os.path.abspath(output_path),
        "ddg_pos": [float(x) for x in ddg["pos"]],
    }


def _naval_station_geometry(scenario_path: str) -> tuple[float, float, float]:
    scenario = load_json_config(os.path.abspath(scenario_path))
    task = dict(scenario.get("task_order", {}) or {})
    station_radius_m = float(task.get("station_radius_m", 0.0))
    station_heading_deg = float(task.get("station_heading_deg", 0.0))
    heading_rad = math.radians(station_heading_deg)
    entities = list(scenario.get("entities", []) or [])
    ref = next(entity for entity in entities if entity.get("name") == "Blue_HVU_TAKE1")
    ddg = next(entity for entity in entities if entity.get("name") == "Blue_Screen_DDG51")
    ref_pos = list(ref.get("pos", [0.0, 0.0, 0.0]))
    ddg_pos = list(ddg.get("pos", [0.0, 0.0, 0.0]))
    desired_x = float(ref_pos[0]) + math.sin(heading_rad) * station_radius_m
    desired_y = float(ref_pos[1]) + math.cos(heading_rad) * station_radius_m
    station_error_m = math.hypot(desired_x - float(ddg_pos[0]), desired_y - float(ddg_pos[1]))
    sep_m = math.hypot(float(ddg_pos[0]) - float(ref_pos[0]), float(ddg_pos[1]) - float(ref_pos[1]))
    return float(station_radius_m), float(sep_m), float(station_error_m)


def run_offstation_command_probe(
    *,
    scenario_path: str,
    train_config_path: str,
    steps: int,
    seed: int,
    worker_threads: int,
    station_radius_offset_m: float = -1800.0,
) -> dict[str, Any]:
    _load_validated_train_config(scenario_path, train_config_path)
    station_radius_m, initial_sep_m, initial_station_error_m = _naval_station_geometry(scenario_path)
    scenario_is_offstation = bool(initial_station_error_m >= 1000.0)
    if scenario_is_offstation:
        eval_path = os.path.abspath(scenario_path)
        derived: dict[str, Any] = {
            "station_radius_offset_m": None,
            "derived_scenario": None,
            "source_scenario": os.path.abspath(scenario_path),
            "initial_separation_m": float(initial_sep_m),
            "initial_station_error_m": float(initial_station_error_m),
        }
        zero = _run_fixed_action_eval(
            scenario_path=eval_path,
            train_config_path=train_config_path,
            steps=int(steps),
            seed=int(seed),
            worker_threads=int(worker_threads),
            action=np.zeros((3,), dtype=np.float32),
            validate_entry_scenario=False,
        )
        sign = -1.0 if float(initial_sep_m) < float(station_radius_m) else 1.0
        matched_radius = _run_fixed_action_eval(
            scenario_path=eval_path,
            train_config_path=train_config_path,
            steps=int(steps),
            seed=int(seed),
            worker_threads=int(worker_threads),
            action=np.array([0.0, sign, 0.0], dtype=np.float32),
            validate_entry_scenario=False,
        )
    else:
        with TemporaryDirectory() as tmpdir:
            derived_path = os.path.join(tmpdir, "naval_station_offstation_probe.json")
            derived = _derive_station_radius_offset_scenario(
                scenario_path=scenario_path,
                offset_m=float(station_radius_offset_m),
                output_path=derived_path,
                reward_overrides={
                    "naval_station_recovery_progress_weight": 0.08,
                    "naval_station_recovery_progress_norm_m": 100.0,
                    "naval_station_recovery_progress_clip": 1.0,
                },
            )
            zero = _run_fixed_action_eval(
                scenario_path=derived_path,
                train_config_path=train_config_path,
                steps=int(steps),
                seed=int(seed),
                worker_threads=int(worker_threads),
                action=np.zeros((3,), dtype=np.float32),
                validate_entry_scenario=False,
            )
            sign = -1.0 if float(station_radius_offset_m) < 0.0 else 1.0
            matched_radius = _run_fixed_action_eval(
                scenario_path=derived_path,
                train_config_path=train_config_path,
                steps=int(steps),
                seed=int(seed),
                worker_threads=int(worker_threads),
                action=np.array([0.0, sign, 0.0], dtype=np.float32),
                validate_entry_scenario=False,
            )

    zero_first_error = float((zero.get("first_mission_status") or [0.0])[0])
    zero_final_error = float((zero.get("final_mission_status") or [0.0])[0])
    action_first_error = float((matched_radius.get("first_mission_status") or [0.0])[0])
    action_final_error = float((matched_radius.get("final_mission_status") or [0.0])[0])
    reward_delta = float(matched_radius["reward_total"]) - float(zero["reward_total"])
    zero_error_delta = zero_final_error - zero_first_error
    action_error_delta = action_final_error - action_first_error
    action_vs_zero_final_error_delta = action_final_error - zero_final_error
    min_recovery_delta_m = min(100.0, max(10.0, float(steps) * 0.5))
    action_terms = dict(matched_radius.get("reward_terms_sum", {}) or {})
    zero_terms = dict(zero.get("reward_terms_sum", {}) or {})
    forbidden_present = sorted(
        set(zero.get("forbidden_reward_terms_present", []))
        | set(matched_radius.get("forbidden_reward_terms_present", []))
    )
    passed = bool(
        zero.get("finite_reward")
        and matched_radius.get("finite_reward")
        and not forbidden_present
        and float(zero_terms.get("naval_station_recovery_progress_bonus", 0.0)) > 0.0
        and "naval_station_action_radius_penalty" in action_terms
        and "naval_station_band_bonus" not in dict(matched_radius.get("reward_terms_last", {}) or {})
        and action_final_error > 1000.0
        and zero_error_delta < -min_recovery_delta_m
        and action_vs_zero_final_error_delta > min_recovery_delta_m
        and reward_delta < 0.0
    )
    return {
        "mode": "naval_station_offstation_station_order_probe",
        "scenario": os.path.abspath(scenario_path),
        "train_config": os.path.abspath(train_config_path),
        "seed": int(seed),
        "requested_steps": int(steps),
        "passed": bool(passed),
        "derived": derived,
        "zero_action": zero,
        "matched_radius_action": matched_radius,
        "reward_delta_matched_minus_zero": float(reward_delta),
        "minimum_recovery_delta_m": float(min_recovery_delta_m),
        "zero_station_error_delta_final_minus_first": float(zero_error_delta),
        "matched_station_error_delta_final_minus_first": float(action_error_delta),
        "final_station_error_delta_matched_minus_zero": float(action_vs_zero_final_error_delta),
        "forbidden_reward_terms_present": forbidden_present,
        "claim_boundary": (
            "This probe verifies that the scripted naval station hold recovers from an "
            "off-station start while station-order actions cannot move the reward "
            "reference to the ship. It is not a learned-policy acceptance."
        ),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate maintained naval station cooperative policy gates.")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--train_config", required=True)
    parser.add_argument("--steps", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=20260525)
    parser.add_argument("--worker_threads", type=int, default=1)
    parser.add_argument("--json_out", default="")
    parser.add_argument(
        "--mode",
        choices=["baseline", "offstation_probe"],
        default="baseline",
        help="baseline runs the zero-action station hold gate; offstation_probe checks station-order reward-reference closure.",
    )
    parser.add_argument("--station_radius_offset_m", type=float, default=-1800.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if str(args.mode) == "offstation_probe":
            payload = run_offstation_command_probe(
                scenario_path=str(args.scenario),
                train_config_path=str(args.train_config),
                steps=int(args.steps),
                seed=int(args.seed),
                worker_threads=int(args.worker_threads),
                station_radius_offset_m=float(args.station_radius_offset_m),
            )
        else:
            payload = run_baseline_eval(
                scenario_path=str(args.scenario),
                train_config_path=str(args.train_config),
                steps=int(args.steps),
                seed=int(args.seed),
                worker_threads=int(args.worker_threads),
            )
    except ValueError as exc:
        payload = {
            "mode": str(args.mode),
            "scenario": os.path.abspath(str(args.scenario)),
            "train_config": os.path.abspath(str(args.train_config)),
            "passed": False,
            "error": str(exc),
        }
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        write_json_output(str(args.json_out), payload)
        return 1
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    write_json_output(str(args.json_out), payload)
    if not bool(payload.get("passed", False)):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
