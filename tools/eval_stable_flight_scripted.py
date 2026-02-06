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


def _wrap_deg(x: float) -> float:
    y = (float(x) + 180.0) % 360.0 - 180.0
    return 0.0 if abs(y) < 1.0e-9 else y


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
        f"{name}: mean={mean:.3f}{suffix} std={std:.3f}{suffix} "
        f"p50={p50:.3f}{suffix} p90={p90:.3f}{suffix} p95={p95:.3f}{suffix} "
        f"min={mn:.3f}{suffix} max={mx:.3f}{suffix}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate stable-flight tracking for the scripted controller")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--max_steps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--action_mode", type=str, default="full", choices=["full", "takeoff2", "takeoff4"])
    parser.add_argument("--include_visual", action="store_true")
    parser.add_argument("--include_proprio", action="store_true")
    parser.add_argument("--no_randomization", action="store_true")
    parser.add_argument("--warmup_steps", type=int, default=100)
    parser.add_argument("--alt_tol_m", type=float, default=30.0)
    parser.add_argument("--spd_tol_mps", type=float, default=10.0)
    parser.add_argument("--hdg_tol_deg", type=float, default=10.0)
    args = parser.parse_args()

    repo_root = _repo_root()
    _prepend_local_ef_py(repo_root)
    sys.path.insert(0, repo_root)

    from gym_envs.universal_env import UniversalEnv  # noqa: E402
    from python.rl.scripted_stable_flight import ScriptedStableFlightController  # noqa: E402
    import world_model_train as wmt  # noqa: E402

    env = UniversalEnv(
        args.scenario,
        include_visual=bool(args.include_visual),
        include_proprio=bool(args.include_proprio),
        action_mode=str(args.action_mode),
    )
    if bool(args.no_randomization):
        wmt._apply_env_overrides(env, args)

    alt_err_abs: list[float] = []
    spd_err_abs: list[float] = []
    hdg_err_abs: list[float] = []
    roll_abs: list[float] = []
    pitch_abs: list[float] = []

    ep_alt_err_mean: list[float] = []
    ep_spd_err_mean: list[float] = []
    ep_hdg_err_mean: list[float] = []
    ep_hold_frac: list[float] = []
    ep_rewards: list[float] = []
    ep_steps: list[int] = []

    for ep in range(int(args.episodes)):
        obs, _ = env.reset(seed=int(args.seed) + ep)
        ctrl = ScriptedStableFlightController(action_dim=int(env.action_space.shape[0]), dt=float(env.sim.get_time_step()))
        ctrl.reset(obs)

        done = False
        steps = 0
        total_rew = 0.0
        ep_alt: list[float] = []
        ep_spd: list[float] = []
        ep_hdg: list[float] = []
        ep_hold = 0
        hold_total = 0

        while not done and steps < int(args.max_steps):
            action = ctrl.step(obs)
            next_obs, reward, terminated, truncated, _info = env.step(action)
            total_rew += float(reward)
            done = bool(terminated or truncated or (steps + 1) >= int(args.max_steps))

            inst = np.asarray(next_obs["instruments"], dtype=np.float32).reshape(-1)
            mission = np.asarray(next_obs.get("mission", []), dtype=np.float32).reshape(-1)
            if inst.size >= 10 and mission.size >= 4:
                ias = float(inst[0])
                alt = float(inst[2])
                hdg = float(inst[9])
                roll = float(inst[8])
                pitch = float(inst[7])

                tgt_hdg = float(mission[1])
                tgt_alt = float(mission[2])
                tgt_spd = float(mission[3])

                alt_e = abs(alt - tgt_alt)
                spd_e = abs(ias - tgt_spd)
                hdg_e = abs(_wrap_deg(hdg - tgt_hdg))

                alt_err_abs.append(alt_e)
                spd_err_abs.append(spd_e)
                hdg_err_abs.append(hdg_e)
                roll_abs.append(abs(roll))
                pitch_abs.append(abs(pitch))

                ep_alt.append(alt_e)
                ep_spd.append(spd_e)
                ep_hdg.append(hdg_e)

                if steps >= int(args.warmup_steps):
                    hold_total += 1
                    if (
                        alt_e <= float(args.alt_tol_m)
                        and spd_e <= float(args.spd_tol_mps)
                        and hdg_e <= float(args.hdg_tol_deg)
                    ):
                        ep_hold += 1

            obs = next_obs
            steps += 1

        ep_rewards.append(float(total_rew))
        ep_steps.append(int(steps))
        ep_alt_err_mean.append(float(np.mean(ep_alt)) if ep_alt else float("nan"))
        ep_spd_err_mean.append(float(np.mean(ep_spd)) if ep_spd else float("nan"))
        ep_hdg_err_mean.append(float(np.mean(ep_hdg)) if ep_hdg else float("nan"))
        ep_hold_frac.append(float(ep_hold) / float(hold_total) if hold_total > 0 else 0.0)

    print("=" * 60)
    print("STABLE FLIGHT EVAL (scripted controller)")
    print(f"scenario:   {args.scenario}")
    print(f"episodes:   {int(args.episodes)} seed: {int(args.seed)}..{int(args.seed) + int(args.episodes) - 1}")
    print(f"action_mode:{args.action_mode} include_visual={bool(args.include_visual)} include_proprio={bool(args.include_proprio)}")
    print(f"tolerances: alt<= {float(args.alt_tol_m):.1f}m, spd<= {float(args.spd_tol_mps):.1f}m/s, hdg<= {float(args.hdg_tol_deg):.1f}deg (warmup={int(args.warmup_steps)} steps)")
    print("-" * 60)
    print(_fmt_stats("episode_reward", ep_rewards))
    print(_fmt_stats("episode_steps", [float(x) for x in ep_steps]))
    print(_fmt_stats("episode_alt_err_mean", ep_alt_err_mean, unit="m"))
    print(_fmt_stats("episode_spd_err_mean", ep_spd_err_mean, unit="m/s"))
    print(_fmt_stats("episode_hdg_err_mean", ep_hdg_err_mean, unit="deg"))
    print(_fmt_stats("episode_hold_frac", ep_hold_frac))
    print("-" * 60)
    print(_fmt_stats("all_alt_err_abs", alt_err_abs, unit="m"))
    print(_fmt_stats("all_spd_err_abs", spd_err_abs, unit="m/s"))
    print(_fmt_stats("all_hdg_err_abs", hdg_err_abs, unit="deg"))
    print(_fmt_stats("all_roll_abs", roll_abs, unit="deg"))
    print(_fmt_stats("all_pitch_abs", pitch_abs, unit="deg"))
    print("=" * 60)


if __name__ == "__main__":
    main()

