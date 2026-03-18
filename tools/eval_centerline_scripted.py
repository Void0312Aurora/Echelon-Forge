import argparse
import os
import sys

import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.eval_utils import add_common_env_args, bootstrap_repo_imports, make_universal_env_from_args, quantile_summary


def main() -> None:
    p = argparse.ArgumentParser(description="Evaluate runway centerline deviation for the scripted takeoff controller")
    add_common_env_args(
        p,
        episodes_default=50,
        max_steps_default=2000,
        seed_default=140,
        default_action_mode="full",
        include_no_randomization=True,
    )
    args = p.parse_args()

    bootstrap_repo_imports()

    from gym_envs.universal_env import UniversalEnv  # noqa: E402
    from python.rl.scripted_takeoff import ScriptedTakeoffController  # noqa: E402
    env = make_universal_env_from_args(args)

    dt = float(env.sim.get_time_step())

    ep_max_abs_cross: list[float] = []
    ep_mean_abs_cross: list[float] = []
    ep_on_runway_geom_frac: list[float] = []
    all_abs_cross: list[float] = []

    for ep in range(int(args.episodes)):
        obs, _ = env.reset(seed=int(args.seed) + ep)
        max_steps = min(int(args.max_steps), int(env.max_steps))
        dt = float(env.sim.get_time_step())

        ctrl = ScriptedTakeoffController(action_dim=int(env.action_space.shape[0]), dt=dt)
        ctrl.reset(obs)

        done = False
        steps = 0
        ep_cross: list[float] = []
        ground_steps = 0
        on_runway_geom_steps = 0

        while not done and steps < max_steps:
            action = ctrl.step(obs)
            next_obs, _reward, terminated, truncated, info = env.step(action)
            done = bool(terminated or truncated or (steps + 1) >= max_steps)

            try:
                if float(info.get("on_ground", 0.0)) > 0.5 and "runway_cross_m" in info:
                    cross = abs(float(info["runway_cross_m"]))
                    ep_cross.append(cross)
                    all_abs_cross.append(cross)
                    ground_steps += 1
                    if float(info.get("on_runway_geom", 0.0)) > 0.5:
                        on_runway_geom_steps += 1
            except Exception:
                pass

            obs = next_obs
            steps += 1

        if ep_cross:
            ep_max_abs_cross.append(float(np.max(ep_cross)))
            ep_mean_abs_cross.append(float(np.mean(ep_cross)))
        else:
            ep_max_abs_cross.append(0.0)
            ep_mean_abs_cross.append(0.0)
        if ground_steps > 0:
            ep_on_runway_geom_frac.append(float(on_runway_geom_steps) / float(ground_steps))
        else:
            ep_on_runway_geom_frac.append(0.0)

    print("== Summary ==")
    print(
        f"episodes={int(args.episodes)} seed_base={int(args.seed)} action_mode={args.action_mode} "
        f"no_randomization={bool(args.no_randomization)}"
    )
    print("== Centerline (on_ground) ==")
    print(f"episode_max_abs_cross_m: {quantile_summary(ep_max_abs_cross, [0.50, 0.90, 0.95, 0.99])}")
    print(f"episode_mean_abs_cross_m: {quantile_summary(ep_mean_abs_cross, [0.50, 0.90, 0.95, 0.99])}")
    print(f"all_steps_abs_cross_m: {quantile_summary(all_abs_cross, [0.50, 0.90, 0.95, 0.99])}")
    print(f"episode_on_runway_geom_frac: {quantile_summary(ep_on_runway_geom_frac, [0.50, 0.90, 0.95, 0.99])}")


if __name__ == "__main__":
    main()
