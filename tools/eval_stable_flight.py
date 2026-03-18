import argparse
import os
import sys

import numpy as np


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.eval_utils import add_common_env_args, bootstrap_repo_imports, format_stats, make_universal_env_from_args, wrap_deg
from tools.world_model_eval_utils import WorldModelPolicyRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate stable-flight tracking for a world-model checkpoint")
    add_common_env_args(
        parser,
        episodes_default=20,
        max_steps_default=2000,
        seed_default=0,
        default_action_mode="full",
        include_no_randomization=True,
    )
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--stochastic_state", action="store_true")
    parser.add_argument("--warmup_steps", type=int, default=100, help="Ignore first N steps when computing hold fractions.")
    parser.add_argument("--alt_tol_m", type=float, default=30.0)
    parser.add_argument("--spd_tol_mps", type=float, default=10.0)
    parser.add_argument("--hdg_tol_deg", type=float, default=10.0)
    args = parser.parse_args()

    bootstrap_repo_imports()

    runner = WorldModelPolicyRunner(args.checkpoint, device=str(args.device), include_visual=bool(args.include_visual))
    env = make_universal_env_from_args(args)
    deterministic_state = not bool(args.stochastic_state)

    ep_rewards: list[float] = []
    ep_steps: list[int] = []
    ep_alt_err_mean: list[float] = []
    ep_spd_err_mean: list[float] = []
    ep_hdg_err_mean: list[float] = []
    ep_hold_frac: list[float] = []
    alt_err_abs: list[float] = []
    spd_err_abs: list[float] = []
    hdg_err_abs: list[float] = []
    roll_abs: list[float] = []
    pitch_abs: list[float] = []
    crashes = 0

    for ep in range(int(args.episodes)):
        obs, _ = env.reset(seed=int(args.seed) + ep)
        runner.reset_episode(obs, deterministic_state=deterministic_state)

        done = False
        steps = 0
        total_rew = 0.0
        ep_alt: list[float] = []
        ep_spd: list[float] = []
        ep_hdg: list[float] = []
        ep_hold = 0
        hold_total = 0

        while not done and steps < int(args.max_steps):
            action_env = runner.act_env()
            next_obs, reward, terminated, truncated, info = env.step(action_env)
            runner.observe(next_obs)
            total_rew += float(reward)
            done = bool(terminated or truncated or (steps + 1) >= int(args.max_steps))

            try:
                inst = np.asarray(next_obs["instruments"], dtype=np.float32).reshape(-1)
                mission = np.asarray(next_obs.get("mission", []), dtype=np.float32).reshape(-1)
            except Exception:
                inst = None
                mission = None

            if inst is not None and mission is not None and inst.size >= 10 and mission.size >= 4:
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
                hdg_e = abs(wrap_deg(hdg - tgt_hdg))

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
                    if alt_e <= float(args.alt_tol_m) and spd_e <= float(args.spd_tol_mps) and hdg_e <= float(args.hdg_tol_deg):
                        ep_hold += 1

            if isinstance(info, dict):
                ms = info.get("mission_status", None)
                if ms is not None:
                    try:
                        ms_arr = np.asarray(ms, dtype=np.float32).reshape(-1)
                        if ms_arr.size >= 4 and float(ms_arr[3]) < -0.5:
                            crashes += 1
                    except Exception:
                        pass

            steps += 1

        ep_rewards.append(float(total_rew))
        ep_steps.append(int(steps))
        ep_alt_err_mean.append(float(np.mean(ep_alt)) if ep_alt else float("nan"))
        ep_spd_err_mean.append(float(np.mean(ep_spd)) if ep_spd else float("nan"))
        ep_hdg_err_mean.append(float(np.mean(ep_hdg)) if ep_hdg else float("nan"))
        ep_hold_frac.append(float(ep_hold) / float(hold_total) if hold_total > 0 else 0.0)

    print("=" * 60)
    print("STABLE FLIGHT EVAL (world-model)")
    print(f"scenario:   {args.scenario}")
    print(f"checkpoint: {args.checkpoint}")
    print(f"episodes:   {int(args.episodes)} seed: {int(args.seed)}..{int(args.seed) + int(args.episodes) - 1}")
    print(f"action_mode:{args.action_mode} include_visual={bool(args.include_visual)} include_proprio={bool(args.include_proprio)}")
    print(
        f"tolerances: alt<= {float(args.alt_tol_m):.1f}m, spd<= {float(args.spd_tol_mps):.1f}m/s, "
        f"hdg<= {float(args.hdg_tol_deg):.1f}deg (warmup={int(args.warmup_steps)} steps)"
    )
    print("-" * 60)
    print(format_stats("episode_reward", ep_rewards))
    print(format_stats("episode_steps", [float(x) for x in ep_steps]))
    print(format_stats("episode_alt_err_mean", ep_alt_err_mean, unit="m"))
    print(format_stats("episode_spd_err_mean", ep_spd_err_mean, unit="m/s"))
    print(format_stats("episode_hdg_err_mean", ep_hdg_err_mean, unit="deg"))
    print(format_stats("episode_hold_frac", ep_hold_frac))
    print("-" * 60)
    print(format_stats("alt_err_abs", alt_err_abs, unit="m"))
    print(format_stats("spd_err_abs", spd_err_abs, unit="m/s"))
    print(format_stats("hdg_err_abs", hdg_err_abs, unit="deg"))
    print(format_stats("roll_abs", roll_abs, unit="deg"))
    print(format_stats("pitch_abs", pitch_abs, unit="deg"))
    print("-" * 60)
    print(f"crashes={int(crashes)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
