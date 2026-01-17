import argparse
import json
import math
import os
import sys
from datetime import datetime

import numpy as np

try:
    import torch
except ImportError as exc:
    raise SystemExit(
        "PyTorch is required for this script. Install it in your venv, e.g.:\n"
        "  pip install torch"
    ) from exc

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(repo_root, "build"))
sys.path.append(repo_root)

import ef_py
from examples.training.train_self_play import (
    MLPPolicy,
    apply_missile_tuning,
    build_observation,
    extract_track,
    scripted_action,
)
from python.scenario_metrics import ScenarioLogger, ScenarioMetrics
from python.scenario_visualizer import render_gif


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_path(path):
    if not path:
        return ""
    if os.path.isabs(path):
        return path
    return os.path.join(repo_root, path)


def run_eval_episode(kernel, blue_policy, red_policy, cfg, unit_defs_path, output_dir, episode_idx,
                     deterministic, scripted_side=None, scripted_cfg=None):
    kernel.reset(42 + episode_idx)
    if unit_defs_path:
        kernel.load_unit_definitions(unit_defs_path)
    apply_missile_tuning(kernel, cfg, ef_py)

    spawn_cfg = cfg.get("spawn", {})
    blue_spawn = spawn_cfg.get("blue", {})
    red_spawn = spawn_cfg.get("red", {})

    blue_pos = blue_spawn.get("position", [0.0, 0.0, 5000.0])
    blue_vel = blue_spawn.get("velocity", [250.0, 0.0, 0.0])
    red_pos = red_spawn.get("position", [10000.0, 0.0, 5000.0])
    red_vel = red_spawn.get("velocity", [-250.0, 0.0, 0.0])

    blue_id = kernel.spawn_unit(ef_py.Side.Blue, ef_py.UnitType.Aircraft,
                                blue_pos[0], blue_pos[1], blue_pos[2],
                                blue_vel[0], blue_vel[1], blue_vel[2])
    red_id = kernel.spawn_unit(ef_py.Side.Red, ef_py.UnitType.Aircraft,
                               red_pos[0], red_pos[1], red_pos[2],
                               red_vel[0], red_vel[1], red_vel[2])

    termination_cfg = cfg.get("termination", {})
    disengage_range_m = termination_cfg.get("disengage_range_m")
    disengage_hold_s = float(termination_cfg.get("disengage_hold_s", 0.0))
    min_specific_energy = termination_cfg.get("min_specific_energy_j_kg")
    energy_hold_s = float(termination_cfg.get("energy_hold_s", 0.0))
    ammo_depletion_ends = bool(termination_cfg.get("ammo_depletion_ends", False))
    fire_enabled = bool(cfg.get("fire_enabled", True))

    dt = kernel.get_time_step()
    max_steps = int(cfg.get("max_steps", 600))
    disengage_timer = 0.0
    energy_timer_blue = 0.0
    energy_timer_red = 0.0

    run_dir = os.path.join(output_dir, f"eval_{episode_idx:03d}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(run_dir, exist_ok=True)
    log_path = os.path.join(run_dir, "log.jsonl")
    metrics_path = os.path.join(run_dir, "metrics.json")
    gif_path = os.path.join(run_dir, "playback.gif")

    metadata = {
        "schema_version": 1,
        "scenario": "selfplay_eval",
        "seed": 42 + episode_idx,
        "duration_seconds": max_steps * dt,
        "tick_hz": 1.0 / dt if dt > 0 else 0.0,
        "dt": dt,
        "entities": ["blue", "red"],
    }
    logger = ScenarioLogger(log_path, metadata)
    metrics = ScenarioMetrics(["blue", "red"])

    obs_cfg = cfg.get("observation", {})
    obs_mode = str(obs_cfg.get("mode", "truth"))

    for step in range(max_steps):
        blue_obs = kernel.get_agent_observation(blue_id)
        red_obs = kernel.get_agent_observation(red_id)
        blue_track = extract_track(blue_obs, red_id) if obs_mode == "track" else None
        red_track = extract_track(red_obs, blue_id) if obs_mode == "track" else None
        obs_blue = build_observation(blue_obs, red_obs, blue_track, obs_mode, obs_cfg)
        obs_red = build_observation(red_obs, blue_obs, red_track, obs_mode, obs_cfg)

        if scripted_side == "blue":
            blue_action = scripted_action(blue_obs, red_obs, blue_track, scripted_cfg, cfg.get("launch_envelope", {}))
            if deterministic:
                red_action = red_policy.act_mean(obs_red)
            else:
                red_action = red_policy.act_no_grad(obs_red)
        elif scripted_side == "red":
            red_action = scripted_action(red_obs, blue_obs, red_track, scripted_cfg, cfg.get("launch_envelope", {}))
            if deterministic:
                blue_action = blue_policy.act_mean(obs_blue)
            else:
                blue_action = blue_policy.act_no_grad(obs_blue)
        else:
            if deterministic:
                blue_action = blue_policy.act_mean(obs_blue)
                red_action = red_policy.act_mean(obs_red)
            else:
                blue_action = blue_policy.act_no_grad(obs_blue)
                red_action = red_policy.act_no_grad(obs_red)

        blue_fire = (blue_action[3] + 1.0) * 0.5
        red_fire = (red_action[3] + 1.0) * 0.5

        kernel.set_action(blue_id, blue_action[0], blue_action[1], blue_action[2], blue_fire)
        kernel.set_action(red_id, red_action[0], red_action[1], red_action[2], red_fire)

        if fire_enabled and blue_fire > 0.5 and blue_obs.can_fire:
            kernel.fire_missile(blue_id, red_id)
        if fire_enabled and red_fire > 0.5 and red_obs.can_fire:
            kernel.fire_missile(red_id, blue_id)

        kernel.step()

        positions = {
            "blue": kernel.get_unit_position(blue_id),
            "red": kernel.get_unit_position(red_id),
        }
        healths = {
            "blue": kernel.get_unit_health(blue_id),
            "red": kernel.get_unit_health(red_id),
        }
        detections = {
            "blue": kernel.get_detections(blue_id),
            "red": kernel.get_detections(red_id),
        }
        sim_time = (step + 1) * dt
        metrics.update(sim_time, positions, detections, healths)
        logger.log_tick(step, sim_time, positions, detections)

        blue_health = healths["blue"][0]
        red_health = healths["red"][0]
        dx = positions["blue"][0] - positions["red"][0]
        dy = positions["blue"][1] - positions["red"][1]
        dz = positions["blue"][2] - positions["red"][2]
        range_m = math.sqrt(dx * dx + dy * dy + dz * dz)

        terminated = False
        if red_health <= 0 or blue_health <= 0:
            terminated = True

        if disengage_range_m is not None:
            if range_m > disengage_range_m:
                disengage_timer += dt
            else:
                disengage_timer = 0.0
            if disengage_hold_s <= 0.0 or disengage_timer >= disengage_hold_s:
                terminated = True

        if min_specific_energy is not None:
            blue_energy = 0.5 * blue_obs.speed * blue_obs.speed + 9.80665 * blue_obs.z
            red_energy = 0.5 * red_obs.speed * red_obs.speed + 9.80665 * red_obs.z
            if blue_energy < min_specific_energy:
                energy_timer_blue += dt
            else:
                energy_timer_blue = 0.0
            if red_energy < min_specific_energy:
                energy_timer_red += dt
            else:
                energy_timer_red = 0.0
            if energy_hold_s <= 0.0:
                if blue_energy < min_specific_energy or red_energy < min_specific_energy:
                    terminated = True
            elif energy_timer_blue >= energy_hold_s or energy_timer_red >= energy_hold_s:
                terminated = True

        if ammo_depletion_ends:
            if blue_obs.missiles_remaining == 0 and red_obs.missiles_remaining == 0:
                missiles_in_flight = [
                    unit for unit in kernel.get_all_units()
                    if unit.type == int(ef_py.UnitType.Missile)
                ]
                if not missiles_in_flight:
                    terminated = True

        if terminated:
            break

    logger.close()
    summary = metrics.summary()
    summary["schema_version"] = 1
    summary["steps"] = step + 1
    with open(metrics_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=True)

    try:
        render_gif(log_path, gif_path, fps=20, max_frames=600)
    except Exception as exc:
        print(f"Warning: failed to render GIF ({exc}).")

    return run_dir


def main():
    parser = argparse.ArgumentParser(description="Evaluate a self-play checkpoint.")
    parser.add_argument("--config", type=str, default="examples/training/selfplay_config.json")
    parser.add_argument("--checkpoint", type=str, required=True,
                        help="Path to checkpoint dir or run dir containing checkpoints/")
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--output-dir", type=str, default="logs/selfplay_eval")
    parser.add_argument("--deterministic", action="store_true", help="Use mean actions (no noise)")
    parser.add_argument("--fixed-opponent", action="store_true",
                        help="Use scripted opponent from config.fixed_opponent")
    parser.add_argument("--fixed-side", choices=["blue", "red", "random"], default="red")
    args = parser.parse_args()

    cfg = load_json(resolve_path(args.config))
    unit_defs_path = resolve_path(cfg.get("unit_definitions", "content/units/default_units.json"))

    policy_cfg = cfg.get("policy", {})
    obs_dim = int(policy_cfg.get("obs_dim", 14))
    act_dim = int(policy_cfg.get("act_dim", 4))
    hidden_sizes = policy_cfg.get("hidden_sizes", [64, 64])
    log_std_init = float(policy_cfg.get("log_std_init", -0.5))
    use_cuda = bool(policy_cfg.get("use_cuda", False))
    device = torch.device("cuda" if use_cuda and torch.cuda.is_available() else "cpu")

    blue_policy = MLPPolicy(obs_dim=obs_dim, act_dim=act_dim,
                            hidden_sizes=hidden_sizes,
                            log_std_init=log_std_init,
                            device=device)
    red_policy = MLPPolicy(obs_dim=obs_dim, act_dim=act_dim,
                           hidden_sizes=hidden_sizes,
                           log_std_init=log_std_init,
                           device=device)

    checkpoint_dir = resolve_path(args.checkpoint)
    if os.path.isfile(os.path.join(checkpoint_dir, "blue.pt")):
        resolved_ckpt = checkpoint_dir
    else:
        checkpoints_root = checkpoint_dir
        if os.path.isdir(os.path.join(checkpoint_dir, "checkpoints")):
            checkpoints_root = os.path.join(checkpoint_dir, "checkpoints")
        candidates = [
            os.path.join(checkpoints_root, d)
            for d in os.listdir(checkpoints_root)
            if d.startswith("ep_") and os.path.isdir(os.path.join(checkpoints_root, d))
        ] if os.path.isdir(checkpoints_root) else []
        if not candidates:
            raise SystemExit(f"No checkpoints found under: {checkpoint_dir}")
        resolved_ckpt = sorted(candidates)[-1]

    blue_path = os.path.join(resolved_ckpt, "blue.pt")
    red_path = os.path.join(resolved_ckpt, "red.pt")
    if not os.path.isfile(blue_path) or not os.path.isfile(red_path):
        raise SystemExit(f"Checkpoint missing blue.pt/red.pt: {resolved_ckpt}")

    blue_policy.load_state_dict(torch.load(blue_path, map_location=device))
    red_policy.load_state_dict(torch.load(red_path, map_location=device))
    blue_policy.eval()
    red_policy.eval()

    fixed_cfg = cfg.get("fixed_opponent", {})
    output_dir = resolve_path(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    for ep in range(args.episodes):
        kernel = ef_py.SimulationKernel()
        scripted_side = None
        scripted_cfg = None
        if args.fixed_opponent:
            scripted_cfg = fixed_cfg
            if args.fixed_side == "random":
                scripted_side = "blue" if (ep % 2 == 0) else "red"
            else:
                scripted_side = args.fixed_side
        run_dir = run_eval_episode(kernel, blue_policy, red_policy,
                                   cfg, unit_defs_path, output_dir,
                                   ep + 1, deterministic=args.deterministic,
                                   scripted_side=scripted_side,
                                   scripted_cfg=scripted_cfg)
        print(f"Episode {ep + 1} saved to {run_dir}")


if __name__ == "__main__":
    main()
