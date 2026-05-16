#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

import numpy as np
from stable_baselines3.common.vec_env import DummyVecEnv

from python.testing.runtime import ensure_repo_imports


def _repo_root() -> str:
    return ensure_repo_imports()


def _load_wrapper(train_config_path: str | None):
    if train_config_path is None:
        return None, None
    with open(train_config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    from python.rl.control.wrappers import get_action_wrapper_spec

    return get_action_wrapper_spec(cfg)


def _build_env(scenario_path: str, wrapper_class, wrapper_kwargs, include_visual: bool, include_proprio: bool, mission_obs_mode: str, visual_downsample: int, visual_update_interval: int):
    from gym_envs.universal_env import UniversalEnv

    env = UniversalEnv(
        scenario_path,
        action_mode="full",
        include_visual=include_visual,
        include_proprio=include_proprio,
        mission_obs_mode=mission_obs_mode,
        visual_downsample=visual_downsample,
        visual_update_interval=visual_update_interval,
    )
    if wrapper_class is not None:
        env = wrapper_class(env, **(wrapper_kwargs or {}))
    return env


def _eval_one(model, env, seed: int):
    env.seed(seed)
    obs = env.reset()

    total_reward = 0.0
    steps = 0
    success = False
    survived = True
    term_reason = "done_unknown"

    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, rewards, dones, infos = env.step(action)
        total_reward += float(rewards[0])
        steps += 1
        info = infos[0] if infos else {}
        ms = info.get("mission_status") if isinstance(info, dict) else None
        if ms is not None:
            try:
                flag = float(ms[3])
                if flag > 0.5:
                    success = True
                elif flag < -0.5:
                    survived = False
            except Exception:
                pass
        if dones[0]:
            if isinstance(info, dict):
                tr = info.get("termination_reason")
                if isinstance(tr, str) and tr.strip():
                    term_reason = tr.strip().lower()
            done = True

    return {
        "reward": total_reward,
        "steps": steps,
        "success": success,
        "survived": survived,
        "termination_reason": term_reason,
    }


def main() -> int:
    repo_root = _repo_root()
    os.chdir(repo_root)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    build_dir = os.path.join(repo_root, "build")
    if build_dir not in sys.path:
        sys.path.insert(0, build_dir)

    parser = argparse.ArgumentParser(description="Cruise OOD diagnostics")
    parser.add_argument("--model", required=True, help="Path to SB3 model zip")
    parser.add_argument("--train_config", default=None, help="Training config JSON for wrapper semantics")
    parser.add_argument("--episodes", type=int, default=4)
    parser.add_argument("--seed", type=int, default=321)
    parser.add_argument("--include_visual", action="store_true")
    parser.add_argument("--include_proprio", action="store_true")
    parser.add_argument(
        "--mission_obs_mode",
        type=str,
        default="basic",
        choices=["basic", "nav_v1", "nav_v2", "nav_v2_formation_v1"],
    )
    parser.add_argument("--visual_downsample", type=int, default=2)
    parser.add_argument("--visual_update_interval", type=int, default=2)
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=[
            "scenarios/cruise/cruise_waypoints_stresswind_rewardbalance_v1.json",
            "scenarios/cruise/cruise_waypoints_ood_geometry_v1.json",
            "scenarios/cruise/cruise_waypoints_ood_profile_v1.json",
            "scenarios/cruise/cruise_waypoints_ood_wind_v1.json",
        ],
    )
    args = parser.parse_args()

    from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO

    wrapper_class, wrapper_kwargs = _load_wrapper(args.train_config)

    scenario_paths = [os.path.abspath(p) for p in args.scenarios]
    for p in scenario_paths:
        if not os.path.exists(p):
            raise FileNotFoundError(p)

    model_path = os.path.abspath(args.model)
    load_path = model_path[:-4] if model_path.endswith(".zip") else model_path

    print("OOD Cruise Evaluation")
    print(f"model={model_path}")
    print(f"episodes_per_scenario={args.episodes}")
    print("")

    for idx, scenario_path in enumerate(scenario_paths):
        vec_env = DummyVecEnv(
            [
                lambda sp=scenario_path: _build_env(
                    sp,
                    wrapper_class,
                    wrapper_kwargs,
                    include_visual=bool(args.include_visual),
                    include_proprio=bool(args.include_proprio),
                    mission_obs_mode=str(args.mission_obs_mode),
                    visual_downsample=int(args.visual_downsample),
                    visual_update_interval=int(args.visual_update_interval),
                )
            ]
        )
        model = AdaptiveKLPPO.load(load_path, env=vec_env, device="cpu")

        rows = []
        term_counts = Counter()
        for ep in range(args.episodes):
            row = _eval_one(model, vec_env, seed=int(args.seed + idx * 1000 + ep))
            rows.append(row)
            term_counts[row["termination_reason"]] += 1

        rewards = np.asarray([r["reward"] for r in rows], dtype=np.float64)
        success_rate = float(np.mean([1.0 if r["success"] else 0.0 for r in rows]))
        survival_rate = float(np.mean([1.0 if r["survived"] else 0.0 for r in rows]))
        mean_steps = float(np.mean([r["steps"] for r in rows]))

        print(f"SCENARIO {os.path.basename(scenario_path)}")
        print(f"  mean_reward={rewards.mean():.2f} std={rewards.std():.2f}")
        print(f"  success_rate={success_rate:.3f} survival_rate={survival_rate:.3f} mean_steps={mean_steps:.1f}")
        print(f"  terminations={dict(term_counts)}")
        for ep, row in enumerate(rows, start=1):
            print(
                f"    ep{ep}: reward={row['reward']:.2f} steps={row['steps']} "
                f"success={row['success']} term={row['termination_reason']}"
            )
        print("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
