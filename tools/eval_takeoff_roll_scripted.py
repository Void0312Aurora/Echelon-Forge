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


def _percentile(xs: list[float], q: float) -> float:
    if not xs:
        return float("nan")
    return float(np.percentile(np.asarray(xs, dtype=np.float64), q))


def _fmt_stats(name: str, xs: list[float], *, unit: str = "") -> str:
    if not xs:
        return f"{name}: <empty>"
    mean = float(np.mean(xs))
    std = float(np.std(xs))
    p50 = _percentile(xs, 50)
    p90 = _percentile(xs, 90)
    p95 = _percentile(xs, 95)
    mn = float(np.min(xs))
    mx = float(np.max(xs))
    suffix = f" {unit}" if unit else ""
    return (
        f"{name}: mean={mean:.2f}{suffix} std={std:.2f}{suffix} "
        f"p50={p50:.2f}{suffix} p90={p90:.2f}{suffix} p95={p95:.2f}{suffix} "
        f"min={mn:.2f}{suffix} max={mx:.2f}{suffix}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate takeoff ground-roll distance for the scripted controller")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--max_steps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=140)
    parser.add_argument("--action_mode", type=str, default="takeoff4", choices=["full", "takeoff2", "takeoff4"])
    parser.add_argument("--include_visual", action="store_true")
    parser.add_argument("--include_proprio", action="store_true")
    parser.add_argument("--no_randomization", action="store_true")
    parser.add_argument("--wheel_off_alt_threshold", type=float, default=None)
    parser.add_argument("--liftoff_alt_threshold", type=float, default=None)
    parser.add_argument("--liftoff_ias_threshold", type=float, default=None)
    args = parser.parse_args()

    repo_root = _repo_root()
    _prepend_local_ef_py(repo_root)
    sys.path.insert(0, repo_root)

    from gym_envs.universal_env import UniversalEnv  # noqa: E402
    from python.rl.scripted_takeoff import ScriptedTakeoffController  # noqa: E402

    import world_model_train as wmt  # noqa: E402

    env = UniversalEnv(
        args.scenario,
        include_visual=bool(args.include_visual),
        include_proprio=bool(args.include_proprio),
        action_mode=str(args.action_mode),
    )
    if bool(args.no_randomization):
        wmt._apply_env_overrides(env, args)

    dt = float(env.sim.get_time_step())

    wheel_off_dist_m: list[float] = []
    wheel_off_time_s: list[float] = []
    wheel_off_ias_mps: list[float] = []

    liftoff_dist_m: list[float] = []
    liftoff_time_s: list[float] = []
    liftoff_ias_mps: list[float] = []

    failures = 0

    for ep in range(int(args.episodes)):
        obs, _ = env.reset(seed=int(args.seed) + ep)
        dt = float(env.sim.get_time_step())
        max_steps = min(int(args.max_steps), int(env.max_steps))

        # Liftoff thresholds follow scenario rewards config (realism-first).
        rcfg = {}
        try:
            rcfg = dict(env.loader.get_rewards_config())
        except Exception:
            rcfg = {}

        default_on_ground_alt_threshold = float(rcfg.get("on_ground_alt_threshold", 2.5))
        default_liftoff_alt_threshold = float(rcfg.get("liftoff_alt_threshold", 5.0))
        default_liftoff_speed_threshold = float(rcfg.get("liftoff_speed_threshold", 80.0))

        wheel_off_alt_threshold = float(
            default_on_ground_alt_threshold if args.wheel_off_alt_threshold is None else args.wheel_off_alt_threshold
        )
        liftoff_alt_threshold = float(
            default_liftoff_alt_threshold if args.liftoff_alt_threshold is None else args.liftoff_alt_threshold
        )
        liftoff_speed_threshold = float(
            default_liftoff_speed_threshold if args.liftoff_ias_threshold is None else args.liftoff_ias_threshold
        )

        # Start runway coordinate at t=0.
        start_along = None
        try:
            truth0 = env.sim.get_agent_observation(env.agent_id)
            valid_rf, along0, _cross0, rw_len, rw_wid = env.loader.get_runway_local_frame(float(truth0.x), float(truth0.y))
            if bool(valid_rf) and float(rw_len) > 1.0 and float(rw_wid) > 1.0:
                start_along = float(along0)
        except Exception:
            start_along = None

        ctrl = ScriptedTakeoffController(action_dim=int(env.action_space.shape[0]), dt=dt)
        ctrl.reset(obs)

        got_wheel_off = False
        wheel_off_along = None
        wheel_off_ias = None
        wheel_off_time = None

        got_liftoff = False
        liftoff_along = None
        liftoff_ias = None
        liftoff_time = None

        steps = 0
        done = False
        while not done and steps < max_steps:
            action = ctrl.step(obs)
            next_obs, _reward, terminated, truncated, info = env.step(action)
            done = bool(terminated or truncated or (steps + 1) >= max_steps)

            inst = np.asarray(next_obs.get("instruments", []), dtype=np.float32).reshape(-1)
            ias_mps = float(inst[0]) if inst.size >= 1 else float("nan")
            alt_agl = float(inst[3]) if inst.size >= 4 else float("nan")

            if np.isfinite(ias_mps) and np.isfinite(alt_agl):
                if (not got_wheel_off) and alt_agl > wheel_off_alt_threshold and ias_mps >= liftoff_speed_threshold:
                    got_wheel_off = True
                    wheel_off_time = (steps + 1) * dt
                    wheel_off_ias = ias_mps
                    try:
                        if isinstance(info, dict) and "runway_along_m" in info:
                            wheel_off_along = float(info["runway_along_m"])
                    except Exception:
                        wheel_off_along = None
                    if wheel_off_along is None:
                        try:
                            truth = env.sim.get_agent_observation(env.agent_id)
                            valid_rf, along_m, _cross_m, rw_len, rw_wid = env.loader.get_runway_local_frame(
                                float(truth.x), float(truth.y)
                            )
                            if bool(valid_rf) and float(rw_len) > 1.0 and float(rw_wid) > 1.0:
                                wheel_off_along = float(along_m)
                        except Exception:
                            wheel_off_along = None

                if (not got_liftoff) and alt_agl >= liftoff_alt_threshold and ias_mps >= liftoff_speed_threshold:
                    got_liftoff = True
                    liftoff_time = (steps + 1) * dt
                    liftoff_ias = ias_mps
                    try:
                        if isinstance(info, dict) and "runway_along_m" in info:
                            liftoff_along = float(info["runway_along_m"])
                    except Exception:
                        liftoff_along = None
                    if liftoff_along is None:
                        try:
                            truth = env.sim.get_agent_observation(env.agent_id)
                            valid_rf, along_m, _cross_m, rw_len, rw_wid = env.loader.get_runway_local_frame(
                                float(truth.x), float(truth.y)
                            )
                            if bool(valid_rf) and float(rw_len) > 1.0 and float(rw_wid) > 1.0:
                                liftoff_along = float(along_m)
                        except Exception:
                            liftoff_along = None

            obs = next_obs
            steps += 1

        if (
            start_along is None
            or (not got_wheel_off)
            or wheel_off_along is None
            or wheel_off_time is None
            or wheel_off_ias is None
            or (not got_liftoff)
            or liftoff_along is None
            or liftoff_time is None
            or liftoff_ias is None
        ):
            failures += 1
            continue

        wheel_off_dist_m.append(float(wheel_off_along - start_along))
        wheel_off_time_s.append(float(wheel_off_time))
        wheel_off_ias_mps.append(float(wheel_off_ias))

        liftoff_dist_m.append(float(liftoff_along - start_along))
        liftoff_time_s.append(float(liftoff_time))
        liftoff_ias_mps.append(float(liftoff_ias))

    total_eps = int(args.episodes)
    succ = total_eps - failures
    print("=" * 60)
    print("TAKEOFF ROLL EVAL (scripted controller)")
    print(f"scenario:   {args.scenario}")
    print(f"episodes:   {total_eps} (success={succ}, fail={failures})")
    print(f"seed:       {args.seed}..{args.seed + total_eps - 1}")
    print(f"action_mode:{args.action_mode}")
    print("-" * 60)
    print(_fmt_stats("wheel_off_distance", wheel_off_dist_m, unit="m"))
    print(_fmt_stats("wheel_off_time", wheel_off_time_s, unit="s"))
    print(_fmt_stats("wheel_off_ias", wheel_off_ias_mps, unit="m/s"))
    print("-" * 60)
    print(_fmt_stats("liftoff_distance", liftoff_dist_m, unit="m"))
    print(_fmt_stats("liftoff_time", liftoff_time_s, unit="s"))
    print(_fmt_stats("liftoff_ias", liftoff_ias_mps, unit="m/s"))
    print("=" * 60)


if __name__ == "__main__":
    main()

