#!/usr/bin/env python3
import argparse
import json
import math
import os
import sys

import numpy as np

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(repo_root, "build"))

import ef_py


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def extract_track(obs, target_id):
    for track in obs.contacts:
        if track.id == target_id:
            return track
    return None


def sample_spawn(rng, cfg, blue_pos, blue_vel, red_pos, red_vel):
    random_cfg = cfg.get("spawn_randomization", {}) if isinstance(cfg, dict) else {}
    if not random_cfg or not bool(random_cfg.get("enabled", False)):
        return blue_pos, blue_vel, red_pos, red_vel

    sep = random_cfg.get("separation_m", [8000.0, 20000.0])
    if isinstance(sep, (int, float)):
        sep_min = sep_max = float(sep)
    else:
        sep_min = float(sep[0])
        sep_max = float(sep[1])
    sep_m = float(rng.uniform(min(sep_min, sep_max), max(sep_min, sep_max)))
    lateral_m = float(random_cfg.get("lateral_m", 0.0))
    alt_m = float(random_cfg.get("alt_m", 0.0))
    speed_delta = float(random_cfg.get("speed_delta_mps", 0.0))

    cx = 0.5 * (float(blue_pos[0]) + float(red_pos[0]))
    cy = 0.5 * (float(blue_pos[1]) + float(red_pos[1]))
    cz = 0.5 * (float(blue_pos[2]) + float(red_pos[2]))

    dy = float(rng.uniform(-lateral_m, lateral_m)) if lateral_m > 0.0 else 0.0
    dz_blue = float(rng.uniform(-alt_m, alt_m)) if alt_m > 0.0 else 0.0
    dz_red = float(rng.uniform(-alt_m, alt_m)) if alt_m > 0.0 else 0.0

    blue_pos = [cx - 0.5 * sep_m, cy - 0.5 * dy, cz + dz_blue]
    red_pos = [cx + 0.5 * sep_m, cy + 0.5 * dy, cz + dz_red]

    blue_speed = float(np.linalg.norm(blue_vel))
    red_speed = float(np.linalg.norm(red_vel))
    if speed_delta > 0.0:
        blue_speed = max(50.0, blue_speed + float(rng.uniform(-speed_delta, speed_delta)))
        red_speed = max(50.0, red_speed + float(rng.uniform(-speed_delta, speed_delta)))

    blue_vel = [blue_speed, 0.0, 0.0]
    red_vel = [-red_speed, 0.0, 0.0]
    return blue_pos, blue_vel, red_pos, red_vel


def policy_aggressive(obs, track, cfg):
    if track is None:
        turn_cmd = 0.0
    else:
        turn_cmd = clamp(track.azimuth / cfg["turn_scale_deg"], -1.0, 1.0)
    accel_cmd = 0.5 if obs.speed < cfg["speed_target_mps"] else 0.0
    climb_cmd = 0.0
    fire_cmd = 0.0
    if track is not None and obs.can_fire:
        if cfg["fire_min_range_m"] <= track.range <= cfg["fire_max_range_m"]:
            if abs(track.azimuth) <= cfg["fire_max_bearing_deg"]:
                fire_cmd = 1.0
    return turn_cmd, accel_cmd, climb_cmd, fire_cmd


def policy_defensive(obs, track, cfg):
    if track is None:
        turn_cmd = 0.0
    else:
        turn_cmd = -clamp(track.azimuth / cfg["turn_scale_deg"], -1.0, 1.0)
    accel_cmd = 0.5 if obs.speed < cfg["speed_target_mps"] else 0.0
    climb_cmd = 0.0
    fire_cmd = 0.0
    if track is not None and obs.can_fire:
        if track.range <= cfg["defensive_fire_range_m"] and abs(track.azimuth) <= cfg["defensive_fire_bearing_deg"]:
            fire_cmd = 1.0
    return turn_cmd, accel_cmd, climb_cmd, fire_cmd


def policy_hold(obs, track, cfg):
    return 0.0, 0.0, 0.0, 0.0


def make_policy(name):
    if name == "aggressive":
        return policy_aggressive
    if name == "defensive":
        return policy_defensive
    if name == "hold":
        return policy_hold
    raise ValueError(f"Unknown policy: {name}")


def missiles_in_flight(kernel):
    return [
        unit for unit in kernel.get_all_units()
        if unit.type == int(ef_py.UnitType.Missile)
    ]


def run_episode(kernel, rng, cfg, unit_defs_path, blue_policy_fn, red_policy_fn, tuning=None):
    kernel.reset(int(rng.integers(0, 2**31 - 1)))
    if unit_defs_path:
        kernel.load_unit_definitions(unit_defs_path)
    if tuning is not None and hasattr(kernel, "set_missile_tuning"):
        kernel.set_missile_tuning(tuning)

    spawn_cfg = cfg.get("spawn", {})
    blue_spawn = spawn_cfg.get("blue", {})
    red_spawn = spawn_cfg.get("red", {})

    blue_pos = blue_spawn.get("position", [0.0, 0.0, 5000.0])
    blue_vel = blue_spawn.get("velocity", [250.0, 0.0, 0.0])
    red_pos = red_spawn.get("position", [10000.0, 0.0, 5000.0])
    red_vel = red_spawn.get("velocity", [-250.0, 0.0, 0.0])
    blue_pos, blue_vel, red_pos, red_vel = sample_spawn(rng, cfg, blue_pos, blue_vel, red_pos, red_vel)

    blue_id = kernel.spawn_unit(ef_py.Side.Blue, ef_py.UnitType.Aircraft,
                                blue_pos[0], blue_pos[1], blue_pos[2],
                                blue_vel[0], blue_vel[1], blue_vel[2])
    red_id = kernel.spawn_unit(ef_py.Side.Red, ef_py.UnitType.Aircraft,
                               red_pos[0], red_pos[1], red_pos[2],
                               red_vel[0], red_vel[1], red_vel[2])

    max_steps = int(cfg.get("max_steps", 600))
    ammo_depletion_ends = bool(cfg.get("termination", {}).get("ammo_depletion_ends", False))

    policy_cfg = {
        "turn_scale_deg": 60.0,
        "speed_target_mps": 450.0,
        "fire_min_range_m": 2000.0,
        "fire_max_range_m": 16000.0,
        "fire_max_bearing_deg": 60.0,
        "defensive_fire_range_m": 6000.0,
        "defensive_fire_bearing_deg": 20.0,
    }

    blue_fire = 0
    red_fire = 0
    blue_det_steps = 0
    red_det_steps = 0

    reason = "max_steps"
    steps = max_steps

    for step in range(max_steps):
        blue_obs = kernel.get_agent_observation(blue_id)
        red_obs = kernel.get_agent_observation(red_id)

        blue_track = extract_track(blue_obs, red_id)
        red_track = extract_track(red_obs, blue_id)

        b_turn, b_accel, b_climb, b_fire = blue_policy_fn(blue_obs, blue_track, policy_cfg)
        r_turn, r_accel, r_climb, r_fire = red_policy_fn(red_obs, red_track, policy_cfg)

        kernel.set_action(blue_id, b_turn, b_accel, b_climb, clamp(b_fire, 0.0, 1.0))
        kernel.set_action(red_id, r_turn, r_accel, r_climb, clamp(r_fire, 0.0, 1.0))

        if b_fire > 0.5 and blue_obs.can_fire:
            if kernel.fire_missile(blue_id, red_id) != 0:
                blue_fire += 1
        if r_fire > 0.5 and red_obs.can_fire:
            if kernel.fire_missile(red_id, blue_id) != 0:
                red_fire += 1

        kernel.step()

        if blue_obs.contacts:
            blue_det_steps += 1
        if red_obs.contacts:
            red_det_steps += 1

        blue_hp = kernel.get_unit_health(blue_id)[0]
        red_hp = kernel.get_unit_health(red_id)[0]

        if blue_hp <= 0 and red_hp <= 0:
            reason = "mutual_kill"
            steps = step + 1
            break
        if blue_hp <= 0:
            reason = "blue_killed"
            steps = step + 1
            break
        if red_hp <= 0:
            reason = "red_killed"
            steps = step + 1
            break

        if ammo_depletion_ends:
            if blue_obs.missiles_remaining == 0 and red_obs.missiles_remaining == 0:
                if not missiles_in_flight(kernel):
                    reason = "ammo_depletion"
                    steps = step + 1
                    break

    outcome = "draw"
    if reason == "blue_killed":
        outcome = "red_win"
    elif reason == "red_killed":
        outcome = "blue_win"
    elif reason == "mutual_kill":
        outcome = "mutual_kill"

    return {
        "steps": steps,
        "reason": reason,
        "outcome": outcome,
        "blue_fire": blue_fire,
        "red_fire": red_fire,
        "blue_det_steps": blue_det_steps,
        "red_det_steps": red_det_steps,
    }


def summarize(results):
    summary = {
        "episodes": len(results),
        "blue_win": 0,
        "red_win": 0,
        "mutual_kill": 0,
        "draw": 0,
        "avg_steps": 0.0,
        "avg_blue_fire": 0.0,
        "avg_red_fire": 0.0,
        "avg_blue_det_steps": 0.0,
        "avg_red_det_steps": 0.0,
        "reasons": {},
    }
    if not results:
        return summary
    for r in results:
        summary["avg_steps"] += r["steps"]
        summary["avg_blue_fire"] += r["blue_fire"]
        summary["avg_red_fire"] += r["red_fire"]
        summary["avg_blue_det_steps"] += r["blue_det_steps"]
        summary["avg_red_det_steps"] += r["red_det_steps"]
        summary["reasons"][r["reason"]] = summary["reasons"].get(r["reason"], 0) + 1
        if r["outcome"] == "blue_win":
            summary["blue_win"] += 1
        elif r["outcome"] == "red_win":
            summary["red_win"] += 1
        elif r["outcome"] == "mutual_kill":
            summary["mutual_kill"] += 1
        else:
            summary["draw"] += 1
    n = float(len(results))
    summary["avg_steps"] /= n
    summary["avg_blue_fire"] /= n
    summary["avg_red_fire"] /= n
    summary["avg_blue_det_steps"] /= n
    summary["avg_red_det_steps"] /= n
    return summary


def print_summary(label, summary):
    print(f"\n== {label} ==")
    print(json.dumps(summary, indent=2, sort_keys=True))


def run_matchups(args, cfg, unit_defs_path, tuning=None):
    rng = np.random.default_rng(args.seed)
    kernel = ef_py.SimulationKernel()

    matchups = [
        ("A_vs_A", "aggressive", "aggressive"),
        ("A_vs_B", "aggressive", "defensive"),
        ("B_vs_B", "defensive", "defensive"),
    ]
    if args.matchup != "all":
        matchups = [(args.matchup, args.blue_policy, args.red_policy)]

    for label, blue_name, red_name in matchups:
        blue_policy = make_policy(blue_name)
        red_policy = make_policy(red_name)
        results = []
        for _ in range(args.episodes):
            results.append(run_episode(kernel, rng, cfg, unit_defs_path, blue_policy, red_policy, tuning=tuning))
        print_summary(label, summarize(results))


def run_sweep(args, cfg, unit_defs_path):
    if not hasattr(ef_py, "MissileTuning"):
        print("MissileTuning not available; rebuild ef_py before sweep.")
        return

    base = {
        "max_speed": 1000.0,
        "turn_rate": 35.0,
        "fuse_distance": 300.0,
        "damage": 120.0,
        "seeker_fov_deg": 180.0,
        "seeker_lock_range": 30000.0,
    }
    for mult in args.sweep_multipliers:
        tuning = ef_py.MissileTuning()
        tuning.max_speed = base["max_speed"] * mult
        tuning.turn_rate = base["turn_rate"] * mult
        tuning.fuse_distance = base["fuse_distance"] * mult
        tuning.damage = base["damage"] * mult
        tuning.seeker_fov_deg = base["seeker_fov_deg"]
        tuning.seeker_lock_range = base["seeker_lock_range"]
        label = f"sweep_x{mult:.2f}"
        run_matchups(args, cfg, unit_defs_path, tuning=tuning)
        print(f"-- sweep done: {label}")


def main():
    parser = argparse.ArgumentParser(description="Environment diagnostics for self-play.")
    parser.add_argument("--config", type=str, default="examples/training/selfplay_config.json")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--log-level", type=str, default="warn")
    parser.add_argument("--matchup", type=str, default="all",
                        choices=["all", "custom", "A_vs_A", "A_vs_B", "B_vs_B"])
    parser.add_argument("--blue-policy", type=str, default="aggressive",
                        choices=["aggressive", "defensive", "hold"])
    parser.add_argument("--red-policy", type=str, default="defensive",
                        choices=["aggressive", "defensive", "hold"])
    parser.add_argument("--sweep", action="store_true", help="Run missile parameter sweep.")
    parser.add_argument("--sweep-multipliers", type=float, nargs="+", default=[0.7, 1.0, 1.3])
    args = parser.parse_args()

    cfg_path = args.config
    if not os.path.isabs(cfg_path):
        cfg_path = os.path.join(repo_root, cfg_path)
    cfg = load_json(cfg_path) if os.path.isfile(cfg_path) else {}

    unit_defs = cfg.get("unit_definitions", "content/units/default_units.json")
    unit_defs_path = os.path.join(repo_root, unit_defs) if unit_defs else ""

    if hasattr(ef_py, "set_log_level"):
        ef_py.set_log_level(str(args.log_level))

    if args.matchup == "custom":
        args.matchup = f"{args.blue_policy}_vs_{args.red_policy}"

    if args.sweep:
        run_sweep(args, cfg, unit_defs_path)
    else:
        run_matchups(args, cfg, unit_defs_path)


if __name__ == "__main__":
    main()
