import argparse
import os
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.eval_utils import add_common_env_args, bootstrap_repo_imports, format_stats, make_universal_env_from_args
from tools.world_model_eval_utils import WorldModelPolicyRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate takeoff ground-roll distance for a world-model checkpoint")
    add_common_env_args(
        parser,
        episodes_default=50,
        max_steps_default=2000,
        seed_default=140,
        default_action_mode="takeoff4",
        include_no_randomization=True,
    )
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--stochastic_state", action="store_true")
    parser.add_argument(
        "--wheel_off_alt_threshold",
        type=float,
        default=None,
        help="Override wheel-off altitude threshold (AGL). Default uses scenario on_ground_alt_threshold.",
    )
    parser.add_argument(
        "--liftoff_alt_threshold",
        type=float,
        default=None,
        help="Override liftoff altitude threshold (AGL). Default uses scenario liftoff_alt_threshold.",
    )
    parser.add_argument(
        "--liftoff_ias_threshold",
        type=float,
        default=None,
        help="Override liftoff IAS threshold. Default uses scenario liftoff_speed_threshold.",
    )
    args = parser.parse_args()

    bootstrap_repo_imports()

    runner = WorldModelPolicyRunner(args.checkpoint, device=str(args.device), include_visual=bool(args.include_visual))
    env = make_universal_env_from_args(args)
    deterministic_state = not bool(args.stochastic_state)

    wheel_off_dist_m: list[float] = []
    wheel_off_time_s: list[float] = []
    wheel_off_ias_mps: list[float] = []
    liftoff_dist_m: list[float] = []
    liftoff_time_s: list[float] = []
    liftoff_ias_mps: list[float] = []
    failures = 0

    for ep in range(int(args.episodes)):
        obs, _ = env.reset(seed=int(args.seed) + ep)
        runner.reset_episode(obs, deterministic_state=deterministic_state)
        dt = float(env.sim.get_time_step())
        max_steps = min(int(args.max_steps), int(env.max_steps))

        try:
            rcfg = dict(env.loader.get_rewards_config())
        except Exception:
            rcfg = {}

        wheel_off_alt_threshold = float(
            rcfg.get("on_ground_alt_threshold", 2.5) if args.wheel_off_alt_threshold is None else args.wheel_off_alt_threshold
        )
        liftoff_alt_threshold = float(
            rcfg.get("liftoff_alt_threshold", 5.0) if args.liftoff_alt_threshold is None else args.liftoff_alt_threshold
        )
        liftoff_speed_threshold = float(
            rcfg.get("liftoff_speed_threshold", 80.0) if args.liftoff_ias_threshold is None else args.liftoff_ias_threshold
        )

        start_along = None
        try:
            truth0 = env.sim.get_agent_observation(env.agent_id)
            valid_rf, along0, _cross0, rw_len, rw_wid = env.loader.get_runway_local_frame(float(truth0.x), float(truth0.y))
            if bool(valid_rf) and float(rw_len) > 1.0 and float(rw_wid) > 1.0:
                start_along = float(along0)
        except Exception:
            start_along = None

        got_wheel_off = False
        wheel_off_time = None
        wheel_off_along = None
        wheel_off_ias = None
        got_liftoff = False
        liftoff_time = None
        liftoff_along = None
        liftoff_ias = None

        steps = 0
        while steps < max_steps:
            action_env = runner.act_env()
            next_obs, _reward, terminated, truncated, info = env.step(action_env)
            runner.observe(next_obs)

            inst = next_obs["instruments"]
            alt_agl = float(inst[3]) if len(inst) >= 4 else 0.0
            ias_mps = float(inst[0]) if len(inst) >= 1 else 0.0

            if not got_wheel_off and alt_agl >= wheel_off_alt_threshold:
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
                        valid_rf, along_m, _cross_m, rw_len, rw_wid = env.loader.get_runway_local_frame(float(truth.x), float(truth.y))
                        if bool(valid_rf) and float(rw_len) > 1.0 and float(rw_wid) > 1.0:
                            wheel_off_along = float(along_m)
                    except Exception:
                        wheel_off_along = None

            if not got_liftoff and alt_agl >= liftoff_alt_threshold and ias_mps >= liftoff_speed_threshold:
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
                        valid_rf, along_m, _cross_m, rw_len, rw_wid = env.loader.get_runway_local_frame(float(truth.x), float(truth.y))
                        if bool(valid_rf) and float(rw_len) > 1.0 and float(rw_wid) > 1.0:
                            liftoff_along = float(along_m)
                    except Exception:
                        liftoff_along = None

            steps += 1
            if terminated or truncated or steps >= max_steps:
                break

        if (
            start_along is None
            or not got_wheel_off
            or wheel_off_along is None
            or wheel_off_time is None
            or wheel_off_ias is None
            or not got_liftoff
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
    print("TAKEOFF ROLL EVAL (world-model)")
    print(f"scenario:   {args.scenario}")
    print(f"checkpoint: {args.checkpoint}")
    print(f"episodes:   {total_eps} (success={succ}, fail={failures})")
    print(f"seed:       {args.seed}..{args.seed + total_eps - 1}")
    print(f"action_mode:{args.action_mode}")
    print("-" * 60)
    print(format_stats("wheel_off_distance", wheel_off_dist_m, unit="m"))
    print(format_stats("wheel_off_time", wheel_off_time_s, unit="s"))
    print(format_stats("wheel_off_ias", wheel_off_ias_mps, unit="m/s"))
    print("-" * 60)
    print(format_stats("liftoff_distance", liftoff_dist_m, unit="m"))
    print(format_stats("liftoff_time", liftoff_time_s, unit="s"))
    print(format_stats("liftoff_ias", liftoff_ias_mps, unit="m/s"))
    print("=" * 60)


if __name__ == "__main__":
    main()
