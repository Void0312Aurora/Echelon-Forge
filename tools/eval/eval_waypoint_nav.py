import argparse
import os
import sys

import numpy as np


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.eval.eval_utils import add_common_env_args, bootstrap_repo_imports, format_stats, make_universal_env_from_args
from tools.eval.waypoint_eval_utils import (
    finalize_waypoint_episode,
    make_waypoint_distance_trackers,
    update_waypoint_distance_samples,
    update_waypoint_min_distances,
)
from tools.eval.world_model_eval_utils import WorldModelPolicyRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate waypoint navigation for a world-model checkpoint")
    add_common_env_args(
        parser,
        episodes_default=10,
        max_steps_default=6000,
        seed_default=0,
        default_action_mode="full",
        include_no_randomization=True,
    )
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--stochastic_state", action="store_true")
    args = parser.parse_args()

    bootstrap_repo_imports()

    runner = WorldModelPolicyRunner(args.checkpoint, device=str(args.device), include_visual=bool(args.include_visual))
    env = make_universal_env_from_args(args)
    deterministic_state = not bool(args.stochastic_state)

    ep_success: list[float] = []
    ep_steps: list[int] = []
    ep_rewards: list[float] = []
    ep_final_wp_idx: list[int] = []
    ep_min_dist: list[float] = []
    ep_final_dist: list[float] = []
    ep_wp_min_last: list[float] = []
    ep_wp_min_max: list[float] = []
    crashes = 0
    failures = 0

    for ep in range(int(args.episodes)):
        obs, _ = env.reset(seed=int(args.seed) + ep)
        runner.reset_episode(obs, deterministic_state=deterministic_state)

        done = False
        steps = 0
        total_rew = 0.0
        dists: list[float] = []
        last_ms = None
        waypoints, wp_min_d = make_waypoint_distance_trackers(env)

        while not done and steps < int(args.max_steps):
            action_env = runner.act_env()
            next_obs, reward, terminated, truncated, info = env.step(action_env)
            runner.observe(next_obs)
            total_rew += float(reward)

            update_waypoint_min_distances(env, waypoints, wp_min_d)
            last_ms = update_waypoint_distance_samples(info, dists, last_ms)

            steps += 1
            done = bool(terminated or truncated or steps >= int(args.max_steps))

        episode = finalize_waypoint_episode(last_ms=last_ms, dists=dists, wp_min_d=wp_min_d)
        success = bool(episode["success"])
        failed = bool(episode["failed"])
        wp_idx = int(episode["wp_idx"])
        dist_final = float(episode["final_dist"])

        if failed:
            failures += 1
            crashes += 1

        ep_success.append(1.0 if success else 0.0)
        ep_steps.append(int(steps))
        ep_rewards.append(float(total_rew))
        ep_final_wp_idx.append(int(wp_idx))
        ep_min_dist.append(float(episode["min_dist"]))
        ep_final_dist.append(float(episode["final_dist"]))
        ep_wp_min_last.append(float(episode["wp_min_last"]))
        ep_wp_min_max.append(float(episode["wp_min_max"]))

        print(
            f"[ep {ep + 1}/{int(args.episodes)}] success={success} failed={failed} steps={steps} "
            f"final_wp_idx={wp_idx} min_dist={ep_min_dist[-1]:.1f}m final_dist={dist_final:.1f}m "
            f"wp_min_last={ep_wp_min_last[-1]:.1f}m wp_min_max={ep_wp_min_max[-1]:.1f}m return={total_rew:.1f}"
        )

    print("=" * 60)
    print("WAYPOINT NAV EVAL (world-model)")
    print(f"scenario:   {args.scenario}")
    print(f"checkpoint: {args.checkpoint}")
    print(f"episodes:   {int(args.episodes)} seed: {int(args.seed)}..{int(args.seed) + int(args.episodes) - 1}")
    print(f"action_mode:{args.action_mode} include_visual={bool(args.include_visual)} include_proprio={bool(args.include_proprio)}")
    print("-" * 60)
    print(f"success_rate: {float(np.mean(ep_success)):.3f}")
    print(f"failures={failures}/{int(args.episodes)} crashes={crashes}/{int(args.episodes)}")
    print(format_stats("steps", [float(x) for x in ep_steps]))
    print(format_stats("return", ep_rewards))
    print(format_stats("final_wp_idx", [float(x) for x in ep_final_wp_idx]))
    print(format_stats("min_dist", ep_min_dist, unit="m"))
    print(format_stats("final_dist", ep_final_dist, unit="m"))
    print(format_stats("wp_min_last", ep_wp_min_last, unit="m"))
    print(format_stats("wp_min_max", ep_wp_min_max, unit="m"))
    print("=" * 60)


if __name__ == "__main__":
    main()
