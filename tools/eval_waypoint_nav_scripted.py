import argparse
import os
import sys

import numpy as np


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _prepend_local_ef_py(repo_root: str) -> None:
    build_dir = os.path.join(repo_root, "build")
    if not os.path.isdir(build_dir):
        return
    if any(fname.startswith("ef_py") and fname.endswith(".so") for fname in os.listdir(build_dir)):
        sys.path.insert(0, build_dir)


def _fmt_stats(name: str, xs: list[float], *, unit: str = "") -> str:
    if not xs:
        return f"{name}: <empty>"
    arr = np.asarray(xs, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return f"{name}: <all_nan>"
    mean = float(np.mean(arr))
    std = float(np.std(arr))
    p50 = float(np.percentile(arr, 50))
    p90 = float(np.percentile(arr, 90))
    mn = float(np.min(arr))
    mx = float(np.max(arr))
    suffix = f" {unit}" if unit else ""
    return (
        f"{name}: mean={mean:.3f}{suffix} std={std:.3f}{suffix} "
        f"p50={p50:.3f}{suffix} p90={p90:.3f}{suffix} min={mn:.3f}{suffix} max={mx:.3f}{suffix}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate waypoint navigation using the scripted stable-flight controller")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--max_steps", type=int, default=6000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--action_mode", type=str, default="full", choices=["full", "takeoff2", "takeoff4"])
    parser.add_argument("--include_visual", action="store_true")
    parser.add_argument("--include_proprio", action="store_true")
    args = parser.parse_args()

    repo_root = _repo_root()
    _prepend_local_ef_py(repo_root)
    sys.path.insert(0, repo_root)

    from gym_envs.universal_env import UniversalEnv  # noqa: E402
    from python.rl.scripted_stable_flight import ScriptedStableFlightController  # noqa: E402

    env = UniversalEnv(
        args.scenario,
        include_visual=bool(args.include_visual),
        include_proprio=bool(args.include_proprio),
        action_mode=str(args.action_mode),
    )

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
        wps = list(getattr(getattr(env, "loader", None), "waypoints", []) or [])
        wp_min_d = [float("inf")] * int(len(wps))

        while not done and steps < int(args.max_steps):
            action = ctrl.step(obs)
            obs, rew, terminated, truncated, info = env.step(action)
            total_rew += float(rew)
            steps += 1

            # Per-waypoint min pass distance (geometry-only, for realism-aligned accuracy).
            if wp_min_d:
                try:
                    truth = env.sim.get_agent_observation(env.agent_id)
                    x = float(getattr(truth, "x", 0.0))
                    y = float(getattr(truth, "y", 0.0))
                    for i, wp in enumerate(wps):
                        dx = float(wp.get("x", 0.0)) - x
                        dy = float(wp.get("y", 0.0)) - y
                        d = float(np.hypot(dx, dy))
                        if d < wp_min_d[i]:
                            wp_min_d[i] = d
                except Exception:
                    pass

            ms = info.get("mission_status", None) if isinstance(info, dict) else None
            if ms is not None:
                ms = np.asarray(ms, dtype=np.float32).reshape(-1)
                last_ms = ms
                if ms.size >= 1:
                    # Avoid polluting distance stats on explicit failure: on crash/failfast,
                    # mission_status[0] can be left at the default 0.0 (not a real waypoint distance).
                    if ms.size >= 4 and float(ms[3]) < -0.5:
                        pass
                    else:
                        d = float(ms[0])
                        if np.isfinite(d):
                            dists.append(d)

            done = bool(terminated or truncated or steps >= int(args.max_steps))

        success = False
        failed = False
        wp_idx = 0
        dist_final = float("nan")
        if last_ms is not None and last_ms.size >= 4:
            success = bool(float(last_ms[3]) > 0.5)
            failed = bool(float(last_ms[3]) < -0.5)
            wp_idx = int(float(last_ms[1])) if last_ms.size >= 2 else 0
            if failed:
                dist_final = float("nan")
            else:
                dist_final = float(last_ms[0]) if last_ms.size >= 1 else float("nan")
        successes += int(success)

        ep_steps.append(int(steps))
        ep_return.append(float(total_rew))
        ep_final_wp_idx.append(int(wp_idx))
        ep_min_dist.append(float(np.min(dists)) if dists else float("nan"))
        ep_final_dist.append(float(dist_final))
        if wp_min_d:
            ep_wp_min_last.append(float(wp_min_d[-1]))
            ep_wp_min_max.append(float(np.max(np.asarray(wp_min_d, dtype=np.float64))))
        else:
            ep_wp_min_last.append(float("nan"))
            ep_wp_min_max.append(float("nan"))

        print(
            f"[ep {ep+1}/{int(args.episodes)}] success={success} failed={failed} steps={steps} "
            f"final_wp_idx={wp_idx} min_dist={ep_min_dist[-1]:.1f}m final_dist={dist_final:.1f}m "
            f"wp_min_last={ep_wp_min_last[-1]:.1f}m wp_min_max={ep_wp_min_max[-1]:.1f}m return={total_rew:.1f}"
        )

    print("=" * 60)
    print(f"success_rate: {successes}/{int(args.episodes)} = {successes / max(1, int(args.episodes)):.3f}")
    print(_fmt_stats("steps", ep_steps, unit=""))
    print(_fmt_stats("return", ep_return, unit=""))
    print(_fmt_stats("final_wp_idx", ep_final_wp_idx, unit=""))
    print(_fmt_stats("min_dist", ep_min_dist, unit="m"))
    print(_fmt_stats("final_dist", ep_final_dist, unit="m"))
    print(_fmt_stats("wp_min_last", ep_wp_min_last, unit="m"))
    print(_fmt_stats("wp_min_max", ep_wp_min_max, unit="m"))


if __name__ == "__main__":
    main()
