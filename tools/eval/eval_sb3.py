#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from typing import Any

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from gym_envs.universal_env import UniversalEnv
from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv
from python.rl.runtime.single_world_batch_runtime import build_single_world_batch_execution_runtime
from python.rl.control.wrappers import MultiTimescaleActionWrapper, get_action_wrapper_spec
from tools.eval.eval_utils import format_stats
from tools.eval.sb3_eval_base import (
    add_common_sb3_eval_args,
    load_json_config,
    load_sb3_policy,
    make_env_settings,
    write_json_output,
)


VALID_MODES = {"single", "cooperative"}


def _build_single_env(scenario_path: str, train_config: dict[str, Any], args: argparse.Namespace):
    env_settings = make_env_settings(train_config, args, include_runtime_overrides=False)
    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
    runtime_cfg = train_config.get("runtime", {}) if isinstance(train_config.get("runtime", {}), dict) else {}
    if bool(runtime_cfg.get("world_batch_vec_env", False)):
        env = build_single_world_batch_execution_runtime(
            scenario_path=os.path.abspath(scenario_path),
            env_settings=env_settings,
            wrapper_class=wrapper_class,
            wrapper_kwargs=wrapper_kwargs,
            worker_threads=runtime_cfg.get("world_batch_threads"),
        )
    else:
        env = UniversalEnv(os.path.abspath(scenario_path), **env_settings)
        if wrapper_class is not None:
            env = wrapper_class(env, **(wrapper_kwargs or {}))
    return env, env_settings


def _run_single_episode(
    env,
    model,
    *,
    seed: int,
    deterministic: bool,
    max_steps: int | None,
) -> dict[str, Any]:
    obs, _ = env.reset(seed=int(seed))
    total_reward = 0.0
    steps = 0
    success = False
    survived = True
    term_reason = "done_unknown"
    final_wp_idx = 0
    final_command_code = 0

    limit = int(max_steps) if max_steps is not None else int(getattr(env.unwrapped, "max_steps", 0))
    if limit <= 0:
        limit = 100000

    while steps < limit:
        action, _ = model.predict(obs, deterministic=bool(deterministic))
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += float(reward)
        steps += 1

        base_env = env.unwrapped
        loader = getattr(base_env, "loader", None)
        if loader is not None:
            try:
                final_wp_idx = int(getattr(loader, "waypoint_idx", 0))
            except Exception:
                pass
            try:
                final_command_code = int(getattr(loader, "mission_cmd", {}).get("command_code", 0))
            except Exception:
                pass

        if isinstance(info, dict):
            ms = info.get("mission_status")
            if ms is not None:
                try:
                    flag = float(np.asarray(ms, dtype=np.float32).reshape(-1)[3])
                    if flag > 0.5:
                        success = True
                    elif flag < -0.5:
                        survived = False
                except Exception:
                    pass
            tr = info.get("termination_reason")
            if isinstance(tr, str) and tr.strip():
                term_reason = tr.strip().lower()

        if bool(terminated or truncated):
            break

    return {
        "reward": float(total_reward),
        "steps": int(steps),
        "success": bool(success),
        "survived": bool(survived),
        "termination_reason": str(term_reason),
        "final_waypoint_idx": int(final_wp_idx),
        "final_command_code": int(final_command_code),
    }


def _run_single_eval(args: argparse.Namespace) -> int:
    train_config = load_json_config(os.path.abspath(args.train_config))
    model = load_sb3_policy(os.path.abspath(args.model), algo=str(args.algo), device=str(args.device))
    env, env_settings = _build_single_env(os.path.abspath(args.scenario), train_config, args)

    try:
        rows: list[dict[str, Any]] = []
        term_counts: Counter[str] = Counter()
        for ep in range(int(args.episodes)):
            row = _run_single_episode(
                env,
                model,
                seed=int(args.seed) + ep,
                deterministic=not bool(args.stochastic),
                max_steps=args.max_steps,
            )
            rows.append(row)
            term_counts[str(row["termination_reason"])] += 1

        rewards = [float(r["reward"]) for r in rows]
        steps = [float(r["steps"]) for r in rows]
        success_rate = float(np.mean([1.0 if bool(r["success"]) else 0.0 for r in rows])) if rows else 0.0
        survival_rate = float(np.mean([1.0 if bool(r["survived"]) else 0.0 for r in rows])) if rows else 0.0
        final_wp = [float(r["final_waypoint_idx"]) for r in rows]
        final_cmd = [float(r["final_command_code"]) for r in rows]

        payload = {
            "mode": "single",
            "scenario": os.path.abspath(args.scenario),
            "train_config": os.path.abspath(args.train_config),
            "model": os.path.abspath(args.model),
            "algo": str(args.algo),
            "episodes": int(args.episodes),
            "seed_start": int(args.seed),
            "env_settings": env_settings,
            "success_rate": float(success_rate),
            "survival_rate": float(survival_rate),
            "mean_reward": float(np.mean(np.asarray(rewards, dtype=np.float64))) if rewards else 0.0,
            "mean_steps": float(np.mean(np.asarray(steps, dtype=np.float64))) if steps else 0.0,
            "termination_counts": dict(term_counts),
            "rows": rows,
        }

        print("=" * 60)
        print("SB3 EVAL [single]")
        print(f"scenario:   {payload['scenario']}")
        print(f"train_cfg:  {payload['train_config']}")
        print(f"model:      {payload['model']}")
        print(f"episodes:   {int(args.episodes)} seed: {int(args.seed)}..{int(args.seed) + int(args.episodes) - 1}")
        print(f"env:        {env_settings}")
        print("-" * 60)
        print(f"success_rate:  {payload['success_rate']:.3f}")
        print(f"survival_rate: {payload['survival_rate']:.3f}")
        print(format_stats("reward", rewards))
        print(format_stats("steps", steps))
        print(format_stats("final_waypoint_idx", final_wp))
        print(format_stats("final_command_code", final_cmd))
        print(f"termination_counts: {dict(term_counts)}")
        print("=" * 60)
        print(json.dumps(payload, indent=2, ensure_ascii=True))

        write_json_output(str(args.json_out), payload)
        return 0
    finally:
        env.close()


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


def _run_cooperative_eval(args: argparse.Namespace) -> int:
    train_config = load_json_config(os.path.abspath(args.train_config))
    env_settings = make_env_settings(train_config, args, include_runtime_overrides=True)
    model = load_sb3_policy(os.path.abspath(args.model), algo=str(args.algo), device=str(args.device))
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
            "mode": "cooperative",
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
        print("SB3 EVAL [cooperative]")
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

        write_json_output(str(args.json_out), payload)
        return 0
    finally:
        env.close()


def _extract_mode(argv: list[str]) -> str | None:
    for idx, arg in enumerate(argv):
        if arg == "--mode" and idx + 1 < len(argv):
            mode = str(argv[idx + 1]).strip().lower()
            return mode if mode in VALID_MODES else None
        if arg.startswith("--mode="):
            mode = str(arg.split("=", 1)[1]).strip().lower()
            return mode if mode in VALID_MODES else None
    return None


def _build_mode_parser(mode: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified SB3 evaluator for single-agent and cooperative policies.")
    parser.add_argument("--mode", default=mode, choices=sorted(VALID_MODES), help="Evaluation mode.")

    if mode == "single":
        add_common_sb3_eval_args(
            parser,
            include_runtime_overrides=False,
            cooperative=False,
            episodes_default=8,
            seed_default=0,
        )
        parser.add_argument("--max_steps", type=int, default=None)
    else:
        add_common_sb3_eval_args(
            parser,
            include_runtime_overrides=True,
            cooperative=True,
            episodes_default=8,
            seed_default=0,
            episodes_help="Number of world episodes to evaluate.",
            seed_help="Starting seed. Each episode increments by 1.",
        )
        parser.add_argument("--max_world_steps", type=int, default=None)
        parser.add_argument("--n_worlds", type=int, default=1, help="Evaluation world count. Recommended to keep at 1.")
        parser.add_argument(
            "--curriculum_stage",
            type=int,
            default=None,
            help="Curriculum stage index to apply before reset. Default: last configured stage.",
        )

    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = list(sys.argv[1:] if argv is None else argv)
    mode = _extract_mode(argv)
    if mode is None:
        parser = argparse.ArgumentParser(description="Unified SB3 evaluator for single-agent and cooperative policies.")
        parser.add_argument("--mode", required=True, choices=sorted(VALID_MODES), help="Evaluation mode.")
        parser.epilog = "Use `--mode single --help` or `--mode cooperative --help` for mode-specific options."
        return parser.parse_args(argv)
    return _build_mode_parser(mode).parse_args(argv)


def main() -> int:
    args = parse_args()
    if str(args.mode) == "single":
        return _run_single_eval(args)
    return _run_cooperative_eval(args)


if __name__ == "__main__":
    raise SystemExit(main())
