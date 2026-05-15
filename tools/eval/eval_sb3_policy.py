#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from gym_envs.universal_env import UniversalEnv
from python.env_config import resolve_env_settings
from python.rl.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.wrappers import get_action_wrapper_spec
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

    return resolve_env_settings(train_config, _Args())


def _build_env(scenario_path: str, train_config: dict[str, Any], args: argparse.Namespace):
    env_settings = _make_env_settings(train_config, args)
    wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
    env = UniversalEnv(os.path.abspath(scenario_path), **env_settings)
    if wrapper_class is not None:
        env = wrapper_class(env, **(wrapper_kwargs or {}))
    return env, env_settings


def _run_episode(env, model, *, seed: int, deterministic: bool, max_steps: int | None) -> dict[str, Any]:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Generic SB3 policy evaluator for UniversalEnv tasks.")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--train_config", required=True)
    parser.add_argument("--model", required=True, help="Path to SB3 model zip.")
    parser.add_argument("--algo", default="auto", help="auto / AdaptiveKLPPO / PPO")
    parser.add_argument("--episodes", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max_steps", type=int, default=None)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--device", type=str, default="auto", help="Policy inference device: auto / cpu / cuda")
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
        choices=["basic", "nav_v1", "nav_v2", "nav_v2_formation_v1", "nav_v2_formation_role_v1"],
    )
    parser.add_argument("--visual_downsample", type=int, default=None)
    parser.add_argument("--visual_update_interval", type=int, default=None)
    parser.add_argument("--action_mode", type=str, default=None, choices=["full", "takeoff2", "takeoff4"])
    parser.add_argument("--json_out", default="", help="Optional JSON output path.")
    args = parser.parse_args()

    train_config = _load_json(os.path.abspath(args.train_config))
    model = _load_policy(os.path.abspath(args.model), algo=str(args.algo), device=str(args.device))
    env, env_settings = _build_env(os.path.abspath(args.scenario), train_config, args)

    try:
        rows: list[dict[str, Any]] = []
        term_counts: Counter[str] = Counter()
        for ep in range(int(args.episodes)):
            row = _run_episode(
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
        print("SB3 POLICY EVAL")
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
