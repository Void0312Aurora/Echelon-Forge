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


def main() -> None:
    p = argparse.ArgumentParser(description="Evaluate runway centerline deviation for the scripted takeoff controller")
    p.add_argument("--scenario", required=True)
    p.add_argument("--episodes", type=int, default=50)
    p.add_argument("--max_steps", type=int, default=2000)
    p.add_argument("--seed", type=int, default=140)
    p.add_argument("--action_mode", type=str, default="full", choices=["full", "takeoff2", "takeoff4"])
    p.add_argument("--include_visual", action="store_true")
    p.add_argument("--include_proprio", action="store_true")
    p.add_argument("--no_randomization", action="store_true")
    args = p.parse_args()

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

    def _q(arr: list[float], qs: list[float]) -> dict[str, float]:
        x = np.asarray(arr, dtype=np.float64)
        if x.size == 0:
            return {}
        out: dict[str, float] = {}
        for q in qs:
            out[f"p{int(q*100):02d}"] = float(np.quantile(x, q))
        out["max"] = float(np.max(x))
        out["mean"] = float(np.mean(x))
        return out

    print("== Summary ==")
    print(
        f"episodes={int(args.episodes)} seed_base={int(args.seed)} action_mode={args.action_mode} "
        f"no_randomization={bool(args.no_randomization)}"
    )
    print("== Centerline (on_ground) ==")
    print(f"episode_max_abs_cross_m: {_q(ep_max_abs_cross, [0.50, 0.90, 0.95, 0.99])}")
    print(f"episode_mean_abs_cross_m: {_q(ep_mean_abs_cross, [0.50, 0.90, 0.95, 0.99])}")
    print(f"all_steps_abs_cross_m: {_q(all_abs_cross, [0.50, 0.90, 0.95, 0.99])}")
    print(f"episode_on_runway_geom_frac: {_q(ep_on_runway_geom_frac, [0.50, 0.90, 0.95, 0.99])}")


if __name__ == "__main__":
    main()

