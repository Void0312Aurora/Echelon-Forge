#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.env_config import resolve_env_settings
from python.rl.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv
from python.rl.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.wrappers import MultiTimescaleActionWrapper, get_action_wrapper_spec
from tools.eval.eval_utils import format_stats


def _load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"expected dict JSON at {path!r}")
    return data


def _load_policy(model_path: str, algo: str, device: str):
    load_path = model_path[:-4] if model_path.endswith(".zip") else model_path
    algo_name = str(algo).strip()
    if algo_name in ("auto", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
        try:
            return AdaptiveKLPPO.load(load_path, device=device)
        except Exception:
            if algo_name != "auto":
                raise
    from stable_baselines3 import PPO

    return PPO.load(load_path, device=device)


def _make_env_settings(train_config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    class _Args:
        include_visual = args.include_visual
        include_proprio = args.include_proprio
        action_mode = args.action_mode
        mission_obs_mode = args.mission_obs_mode
        visual_downsample = args.visual_downsample
        visual_update_interval = args.visual_update_interval
        execution_step_runtime_mode = args.execution_step_runtime_mode
        step_info_mode = args.step_info_mode
        flight_shaping_backend = args.flight_shaping_backend

    return resolve_env_settings(train_config, _Args())


def _cooperative_action_wrapper_kwargs(train_config: dict[str, Any]) -> dict[str, Any] | None:
    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
    if wrapper_class is not MultiTimescaleActionWrapper:
        return None
    return dict(wrapper_kwargs or {})


def _apply_curriculum_stage(
    env: CooperativeWorldBatchVecEnv,
    train_config: dict[str, Any],
    stage_index: int | None,
) -> dict[str, Any]:
    curriculum_cfg = train_config.get("curriculum", {}) if isinstance(train_config.get("curriculum", {}), dict) else {}
    stages = list(curriculum_cfg.get("stages", []) or [])
    if not stages:
        env.set_randomization_overrides(None)
        env.set_leader_overrides(None)
        return {"stage_index": None, "randomization": {}, "leader_overrides": {}}

    idx = len(stages) - 1 if stage_index is None else max(0, min(len(stages) - 1, int(stage_index)))
    stage = dict(stages[idx] or {})
    overrides = stage.get("randomization_overrides", stage.get("randomization", {}))
    leader_overrides = stage.get("leader_env_overrides", {})
    env.set_randomization_overrides(dict(overrides or {}))
    env.set_leader_overrides(dict(leader_overrides or {}))
    return {
        "stage_index": int(idx),
        "randomization": dict(overrides or {}),
        "leader_overrides": dict(leader_overrides or {}),
    }


def _format_slot_name(slot_idx: int, control_slot: Any) -> str:
    role = str(getattr(control_slot, "formation_role_id", "") or "").strip()
    entity_name = str(getattr(control_slot, "entity_name", "") or "").strip()
    if role:
        return f"{role}:{entity_name}" if entity_name else role
    if entity_name:
        return entity_name
    return f"slot{int(slot_idx)}"


def _mission_status_summary(info: dict[str, Any]) -> dict[str, float | bool]:
    ms = info.get("mission_status", None)
    if ms is None:
        return {}
    try:
        arr = np.asarray(ms, dtype=np.float32).reshape(-1)
    except Exception:
        return {}
    out: dict[str, float | bool] = {}
    if arr.size >= 1:
        out["distance_to_active_waypoint_m"] = float(arr[0])
    if arr.size >= 2:
        out["waypoint_index"] = float(arr[1])
    if arr.size >= 3:
        out["waypoint_count"] = float(arr[2])
    if arr.size >= 4:
        out["success_flag"] = bool(float(arr[3]) > 0.5)
    return out


def _run_world_episode(
    env: CooperativeWorldBatchVecEnv,
    model,
    *,
    seed: int,
    deterministic: bool,
    max_world_steps: int | None,
) -> dict[str, Any]:
    env.seed(int(seed))
    obs = env.reset()
    world_steps = 0
    limit = int(max_world_steps) if max_world_steps is not None else 0
    if limit <= 0:
        limit = int(max((getattr(slot, "max_steps", 0) for slot in env._slots if slot is not None), default=0))
    if limit <= 0:
        limit = 100000

    final_infos: list[dict[str, Any]] | None = None
    while world_steps < limit:
        action, _ = model.predict(obs, deterministic=bool(deterministic))
        obs, _rewards, dones, infos = env.step(action)
        world_steps += 1
        if bool(np.any(dones)):
            final_infos = list(infos)
            break

    if final_infos is None:
        raise RuntimeError(f"cooperative evaluation failed to terminate within {limit} steps")

    slot_rows: list[dict[str, Any]] = []
    world_success = True
    for slot_idx, info in enumerate(final_infos):
        slot_state = env._slots[slot_idx]
        control_slot = None if slot_state is None else slot_state.control_slot
        ep = info.get("episode", {}) if isinstance(info.get("episode", {}), dict) else {}
        mission_summary = _mission_status_summary(info)
        success = bool(mission_summary.get("success_flag", False))
        world_success = bool(world_success and success)
        slot_rows.append(
            {
                "slot_index": int(slot_idx),
                "slot_name": _format_slot_name(slot_idx, control_slot),
                "entity_name": None if control_slot is None else str(getattr(control_slot, "entity_name", "") or ""),
                "formation_role_id": (
                    None if control_slot is None else str(getattr(control_slot, "formation_role_id", "") or "")
                ),
                "role_code": None if control_slot is None else getattr(control_slot, "role_code", None),
                "relative_slot_code": None if control_slot is None else getattr(control_slot, "relative_slot_code", None),
                "reference_entity_name": (
                    None if control_slot is None else getattr(control_slot, "reference_entity_name", None)
                ),
                "policy_route": None if control_slot is None else getattr(control_slot, "policy_route", None),
                "episode_reward": float(ep.get("r", 0.0)),
                "episode_length": int(ep.get("l", 0)),
                "termination_reason": str(info.get("termination_reason", "") or ""),
                "world_done": bool(float(info.get("world_done", 0.0)) > 0.5),
                "shared_world_reset": bool(float(info.get("shared_world_reset", 0.0)) > 0.5),
                "time_limit_truncated": bool(info.get("TimeLimit.truncated", False)),
                "success": bool(success),
                "mission_status": mission_summary,
            }
        )

    return {
        "seed": int(seed),
        "world_steps": int(world_steps),
        "world_success": bool(world_success),
        "slots": slot_rows,
    }


def _aggregate_slot_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["slot_name"])].append(row)

    out: dict[str, Any] = {}
    for slot_name, slot_rows in grouped.items():
        rewards = [float(r["episode_reward"]) for r in slot_rows]
        lengths = [float(r["episode_length"]) for r in slot_rows]
        success_rate = float(np.mean([1.0 if bool(r["success"]) else 0.0 for r in slot_rows])) if slot_rows else 0.0
        shared_reset_rate = (
            float(np.mean([1.0 if bool(r["shared_world_reset"]) else 0.0 for r in slot_rows])) if slot_rows else 0.0
        )
        term_counts = Counter(str(r["termination_reason"]) for r in slot_rows)
        waypoint_idx = [
            float(r.get("mission_status", {}).get("waypoint_index", np.nan))
            for r in slot_rows
            if r.get("mission_status", {}).get("waypoint_index", None) is not None
        ]
        waypoint_count = [
            float(r.get("mission_status", {}).get("waypoint_count", np.nan))
            for r in slot_rows
            if r.get("mission_status", {}).get("waypoint_count", None) is not None
        ]
        out[slot_name] = {
            "episodes": int(len(slot_rows)),
            "formation_role_id": str(slot_rows[0].get("formation_role_id", "") or ""),
            "entity_name": str(slot_rows[0].get("entity_name", "") or ""),
            "success_rate": float(success_rate),
            "shared_world_reset_rate": float(shared_reset_rate),
            "mean_reward": float(np.mean(np.asarray(rewards, dtype=np.float64))) if rewards else 0.0,
            "mean_steps": float(np.mean(np.asarray(lengths, dtype=np.float64))) if lengths else 0.0,
            "termination_counts": dict(term_counts),
            "reward_stats": {
                "mean": float(np.mean(np.asarray(rewards, dtype=np.float64))) if rewards else 0.0,
                "min": float(np.min(np.asarray(rewards, dtype=np.float64))) if rewards else 0.0,
                "max": float(np.max(np.asarray(rewards, dtype=np.float64))) if rewards else 0.0,
            },
            "length_stats": {
                "mean": float(np.mean(np.asarray(lengths, dtype=np.float64))) if lengths else 0.0,
                "min": float(np.min(np.asarray(lengths, dtype=np.float64))) if lengths else 0.0,
                "max": float(np.max(np.asarray(lengths, dtype=np.float64))) if lengths else 0.0,
            },
            "mean_final_waypoint_index": (
                float(np.mean(np.asarray(waypoint_idx, dtype=np.float64))) if waypoint_idx else float("nan")
            ),
            "mean_waypoint_count": (
                float(np.mean(np.asarray(waypoint_count, dtype=np.float64))) if waypoint_count else float("nan")
            ),
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="SB3 evaluator for cooperative execution policies.")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--train_config", required=True)
    parser.add_argument("--model", required=True, help="Path to SB3 model zip.")
    parser.add_argument("--algo", default="auto", help="auto / AdaptiveKLPPO / PPO")
    parser.add_argument("--episodes", type=int, default=8, help="Number of world episodes to evaluate.")
    parser.add_argument("--seed", type=int, default=0, help="Starting seed. Each episode increments by 1.")
    parser.add_argument("--max_world_steps", type=int, default=None)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--n_worlds", type=int, default=1, help="Evaluation world count. Recommended to keep at 1.")
    parser.add_argument("--device", type=str, default="auto", help="Policy inference device: auto / cpu / cuda")
    parser.add_argument(
        "--curriculum_stage",
        type=int,
        default=None,
        help="Curriculum stage index to apply before reset. Default: last configured stage.",
    )
    parser.add_argument(
        "--include_visual",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override env visual flag from train config.",
    )
    parser.add_argument(
        "--include_proprio",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override env proprio flag from train config.",
    )
    parser.add_argument(
        "--mission_obs_mode",
        type=str,
        default=None,
        choices=["basic", "nav_v1", "nav_v2", "nav_v2_formation_v1", "nav_v2_formation_role_v1", "nav_v2_cooperative_takeoff_v1"],
    )
    parser.add_argument("--visual_downsample", type=int, default=None)
    parser.add_argument("--visual_update_interval", type=int, default=None)
    parser.add_argument("--action_mode", type=str, default=None, choices=["full", "takeoff2", "takeoff4"])
    parser.add_argument("--execution_step_runtime_mode", type=str, default=None, choices=["compiled", "legacy"])
    parser.add_argument("--step_info_mode", type=str, default=None, choices=["full", "terminal", "off"])
    parser.add_argument("--flight_shaping_backend", type=str, default=None, choices=["auto", "legacy", "compiled", "gpu_host"])
    parser.add_argument("--json_out", default="", help="Optional JSON output path.")
    args = parser.parse_args()

    train_config = _load_json(os.path.abspath(args.train_config))
    env_settings = _make_env_settings(train_config, args)
    model = _load_policy(os.path.abspath(args.model), algo=str(args.algo), device=str(args.device))
    action_wrapper_kwargs = _cooperative_action_wrapper_kwargs(train_config)
    env = CooperativeWorldBatchVecEnv(
        scenario_path=os.path.abspath(args.scenario),
        n_envs=max(1, int(args.n_worlds)),
        action_wrapper_kwargs=action_wrapper_kwargs,
        **env_settings,
    )
    curriculum_applied = _apply_curriculum_stage(env, train_config, args.curriculum_stage)
    try:
        world_rows: list[dict[str, Any]] = []
        flat_slot_rows: list[dict[str, Any]] = []
        for ep in range(int(args.episodes)):
            row = _run_world_episode(
                env,
                model,
                seed=int(args.seed) + ep,
                deterministic=not bool(args.stochastic),
                max_world_steps=args.max_world_steps,
            )
            world_rows.append(row)
            flat_slot_rows.extend(list(row["slots"]))

        slot_routes = env.slot_indices_by_policy_route()
        slot_control = env.slot_control_slots()
        world_steps = [float(r["world_steps"]) for r in world_rows]
        world_success_rate = (
            float(np.mean([1.0 if bool(r["world_success"]) else 0.0 for r in world_rows])) if world_rows else 0.0
        )
        slot_summary = _aggregate_slot_rows(flat_slot_rows)
        term_counts_world = Counter()
        for row in world_rows:
            term_counts_world.update(str(slot["termination_reason"]) for slot in row["slots"])

        payload = {
            "scenario": os.path.abspath(args.scenario),
            "train_config": os.path.abspath(args.train_config),
            "model": os.path.abspath(args.model),
            "algo": str(args.algo),
            "episodes": int(args.episodes),
            "seed_start": int(args.seed),
            "n_worlds": int(args.n_worlds),
            "device": str(args.device),
            "env_settings": env_settings,
            "curriculum_applied": curriculum_applied,
            "policy_routes": {str(k): [int(v) for v in vals] for k, vals in slot_routes.items()},
            "slot_control": [
                {
                    "slot_index": int(idx),
                    "slot_name": _format_slot_name(idx, slot),
                    "entity_name": str(getattr(slot, "entity_name", "") or ""),
                    "formation_role_id": str(getattr(slot, "formation_role_id", "") or ""),
                    "role_code": getattr(slot, "role_code", None),
                    "relative_slot_code": getattr(slot, "relative_slot_code", None),
                    "reference_entity_name": getattr(slot, "reference_entity_name", None),
                    "policy_route": getattr(slot, "policy_route", None),
                }
                for idx, slot in enumerate(slot_control)
            ],
            "world_success_rate": float(world_success_rate),
            "world_steps_stats": {
                "mean": float(np.mean(np.asarray(world_steps, dtype=np.float64))) if world_steps else 0.0,
                "min": float(np.min(np.asarray(world_steps, dtype=np.float64))) if world_steps else 0.0,
                "max": float(np.max(np.asarray(world_steps, dtype=np.float64))) if world_steps else 0.0,
            },
            "slot_summary": slot_summary,
            "world_termination_counts": dict(term_counts_world),
            "world_rows": world_rows,
        }

        print("=" * 60)
        print("SB3 COOPERATIVE POLICY EVAL")
        print(f"scenario:   {payload['scenario']}")
        print(f"train_cfg:  {payload['train_config']}")
        print(f"model:      {payload['model']}")
        print(f"episodes:   {int(args.episodes)} seed: {int(args.seed)}..{int(args.seed) + int(args.episodes) - 1}")
        print(f"env:        {env_settings}")
        print(f"curriculum: stage={payload['curriculum_applied']['stage_index']}")
        print(f"policy_routes: {payload['policy_routes']}")
        print("-" * 60)
        print(f"world_success_rate: {payload['world_success_rate']:.3f}")
        print(format_stats("world_steps", world_steps))
        for slot_name, summary in slot_summary.items():
            rewards = [float(row["episode_reward"]) for row in flat_slot_rows if str(row["slot_name"]) == slot_name]
            lengths = [float(row["episode_length"]) for row in flat_slot_rows if str(row["slot_name"]) == slot_name]
            print(f"[{slot_name}]")
            print(f"  success_rate:        {float(summary['success_rate']):.3f}")
            print(f"  shared_reset_rate:   {float(summary['shared_world_reset_rate']):.3f}")
            print(f"  termination_counts:  {summary['termination_counts']}")
            print(f"  {format_stats('reward', rewards)}")
            print(f"  {format_stats('steps', lengths)}")
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
