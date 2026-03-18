import argparse
import os
import sys

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.eval_utils import add_common_env_args, bootstrap_repo_imports, format_stats, make_universal_env_from_args
from tools.waypoint_eval_utils import (
    finalize_waypoint_episode,
    make_waypoint_distance_trackers,
    update_waypoint_distance_samples,
    update_waypoint_min_distances,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate waypoint navigation using the scripted stable-flight controller")
    add_common_env_args(
        parser,
        episodes_default=10,
        max_steps_default=6000,
        seed_default=0,
        default_action_mode="full",
    )
    args = parser.parse_args()

    bootstrap_repo_imports()

    from python.rl.scripted_stable_flight import ScriptedStableFlightController  # noqa: E402

    env = make_universal_env_from_args(args)

    successes = 0
    ep_steps: list[int] = []
    ep_return: list[float] = []
    ep_final_wp_idx: list[int] = []
    ep_min_dist: list[float] = []
    ep_final_dist: list[float] = []
    ep_wp_min_last: list[float] = []
    ep_wp_min_max: list[float] = []

    for ep in range(int(args.episodes)):
        obs, _ = env.reset(seed=int(args.seed) + ep)
        ctrl = ScriptedStableFlightController(action_dim=int(env.action_space.shape[0]), dt=float(env.sim.get_time_step()))
        ctrl.reset(obs)

        done = False
        steps = 0
        total_rew = 0.0
        dists: list[float] = []
        last_ms = None
        waypoints, wp_min_d = make_waypoint_distance_trackers(env)

        while not done and steps < int(args.max_steps):
            action = ctrl.step(obs)
            obs, rew, terminated, truncated, info = env.step(action)
            total_rew += float(rew)
            steps += 1

            update_waypoint_min_distances(env, waypoints, wp_min_d)
            last_ms = update_waypoint_distance_samples(info, dists, last_ms)

            done = bool(terminated or truncated or steps >= int(args.max_steps))

        episode = finalize_waypoint_episode(last_ms=last_ms, dists=dists, wp_min_d=wp_min_d)
        success = bool(episode["success"])
        failed = bool(episode["failed"])
        wp_idx = int(episode["wp_idx"])
        dist_final = float(episode["final_dist"])
        successes += int(success)

        ep_steps.append(int(steps))
        ep_return.append(float(total_rew))
        ep_final_wp_idx.append(int(wp_idx))
        ep_min_dist.append(float(episode["min_dist"]))
        ep_final_dist.append(float(episode["final_dist"]))
        ep_wp_min_last.append(float(episode["wp_min_last"]))
        ep_wp_min_max.append(float(episode["wp_min_max"]))

        print(
            f"[ep {ep+1}/{int(args.episodes)}] success={success} failed={failed} steps={steps} "
            f"final_wp_idx={wp_idx} min_dist={ep_min_dist[-1]:.1f}m final_dist={dist_final:.1f}m "
            f"wp_min_last={ep_wp_min_last[-1]:.1f}m wp_min_max={ep_wp_min_max[-1]:.1f}m return={total_rew:.1f}"
        )

    print("=" * 60)
    print(f"success_rate: {successes}/{int(args.episodes)} = {successes / max(1, int(args.episodes)):.3f}")
    print(format_stats("steps", ep_steps, unit=""))
    print(format_stats("return", ep_return, unit=""))
    print(format_stats("final_wp_idx", ep_final_wp_idx, unit=""))
    print(format_stats("min_dist", ep_min_dist, unit="m"))
    print(format_stats("final_dist", ep_final_dist, unit="m"))
    print(format_stats("wp_min_last", ep_wp_min_last, unit="m"))
    print(format_stats("wp_min_max", ep_wp_min_max, unit="m"))


if __name__ == "__main__":
    main()
