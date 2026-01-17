import argparse
import json
import math
import os
import sys
from datetime import datetime
import multiprocessing as mp

import numpy as np

try:
    import torch
    import torch.nn as nn
except ImportError as exc:
    raise SystemExit(
        "PyTorch is required for this script. Install it in your venv, e.g.:\n"
        "  pip install torch"
    ) from exc

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(repo_root, "build"))

import ef_py


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


def render_progress(current, total, metrics):
    message = (
        f"{current}/{total} "
        f"blue_win={metrics['blue_win_rate']:.2f} "
        f"red_win={metrics['red_win_rate']:.2f} "
        f"steps={metrics['avg_steps']:.1f} "
        f"blue_ret={metrics['avg_blue_return']:.2f} "
        f"red_ret={metrics['avg_red_return']:.2f}"
    )
    sys.stdout.write("\r" + message)
    sys.stdout.flush()


def normalize_angle_deg(angle):
    while angle > 180.0:
        angle -= 360.0
    while angle < -180.0:
        angle += 360.0
    return angle


def nav_heading_to_target(src, dst):
    dx = dst[0] - src[0]
    dy = dst[1] - src[1]
    math_angle = math.atan2(dy, dx)
    nav_heading = 90.0 - math.degrees(math_angle)
    return nav_heading % 360.0


def build_observation(self_obs, target_obs):
    rx = target_obs.x - self_obs.x
    ry = target_obs.y - self_obs.y
    rz = target_obs.z - self_obs.z
    rvx = target_obs.vx - self_obs.vx
    rvy = target_obs.vy - self_obs.vy
    rvz = target_obs.vz - self_obs.vz
    range_m = math.sqrt(rx * rx + ry * ry + rz * rz)
    nav_bearing = nav_heading_to_target((self_obs.x, self_obs.y), (target_obs.x, target_obs.y))
    rel_bearing = normalize_angle_deg(nav_bearing - self_obs.heading)

    return np.array([
        rx / 10000.0,
        ry / 10000.0,
        rz / 10000.0,
        rvx / 300.0,
        rvy / 300.0,
        rvz / 300.0,
        self_obs.speed / 300.0,
        target_obs.speed / 300.0,
        self_obs.z / 10000.0,
        target_obs.z / 10000.0,
        rel_bearing / 180.0,
        range_m / 20000.0,
    ], dtype=np.float32)


class MLPPolicy(nn.Module):
    def __init__(self, obs_dim, act_dim, hidden_sizes, log_std_init, device,
                 log_std_min=-3.0, log_std_max=0.5):
        super().__init__()
        layers = []
        input_dim = obs_dim
        for size in hidden_sizes:
            layers.append(nn.Linear(input_dim, size))
            layers.append(nn.Tanh())
            input_dim = size
        self.backbone = nn.Sequential(*layers)
        self.mean_head = nn.Linear(input_dim, act_dim)
        self.log_std = nn.Parameter(torch.full((act_dim,), log_std_init))
        self.log_std_min = float(log_std_min)
        self.log_std_max = float(log_std_max)
        self.device = device
        self.to(device)

    def forward(self, obs_tensor):
        x = self.backbone(obs_tensor)
        mean = self.mean_head(x)
        log_std = torch.clamp(self.log_std, self.log_std_min, self.log_std_max)
        std = torch.exp(log_std)
        return mean, std

    def act(self, obs_np):
        obs_tensor = torch.as_tensor(obs_np, dtype=torch.float32, device=self.device).unsqueeze(0)
        mean, std = self(obs_tensor)
        dist = torch.distributions.Normal(mean, std)
        raw_action = dist.sample()
        action = torch.tanh(raw_action)
        log_probs = dist.log_prob(raw_action) - torch.log(1.0 - action * action + 1e-6)
        entropy = dist.entropy()
        return action.squeeze(0).cpu().numpy(), log_probs.squeeze(0), entropy.squeeze(0)

    def act_no_grad(self, obs_np):
        with torch.no_grad():
            obs_tensor = torch.as_tensor(obs_np, dtype=torch.float32, device=self.device).unsqueeze(0)
            mean, std = self(obs_tensor)
            dist = torch.distributions.Normal(mean, std)
            raw_action = dist.sample()
            action = torch.tanh(raw_action)
            return action.squeeze(0).cpu().numpy()

    def act_mean(self, obs_np):
        with torch.no_grad():
            obs_tensor = torch.as_tensor(obs_np, dtype=torch.float32, device=self.device).unsqueeze(0)
            mean, _ = self(obs_tensor)
            action = torch.tanh(mean)
            return action.squeeze(0).cpu().numpy()


class RunningMeanStd:
    def __init__(self, size, epsilon=1e-4):
        self.mean = np.zeros(size, dtype=np.float64)
        self.var = np.ones(size, dtype=np.float64)
        self.count = float(epsilon)

    def update(self, batch):
        batch = np.asarray(batch, dtype=np.float64)
        if batch.ndim == 1:
            batch = batch[None, :]
        batch_mean = batch.mean(axis=0)
        batch_var = batch.var(axis=0)
        batch_count = batch.shape[0]

        delta = batch_mean - self.mean
        tot_count = self.count + batch_count
        new_mean = self.mean + delta * batch_count / tot_count
        m_a = self.var * self.count
        m_b = batch_var * batch_count
        m2 = m_a + m_b + delta * delta * self.count * batch_count / tot_count
        new_var = m2 / tot_count

        self.mean = new_mean
        self.var = new_var
        self.count = tot_count

    def normalize(self, obs):
        return (obs - self.mean) / (np.sqrt(self.var) + 1e-8)

    def snapshot(self):
        return {
            "mean": self.mean.copy(),
            "var": self.var.copy(),
            "count": float(self.count),
        }


def normalize_with_state(obs_batch, state):
    if state is None:
        return obs_batch
    mean = state["mean"]
    var = state["var"]
    return (obs_batch - mean) / (np.sqrt(var) + 1e-8)


def compute_log_probs(policy, obs_batch, raw_batch, fire_mask_batch):
    obs_tensor = torch.as_tensor(obs_batch, dtype=torch.float32, device=policy.device)
    raw_tensor = torch.as_tensor(raw_batch, dtype=torch.float32, device=policy.device)
    mean, std = policy(obs_tensor)
    dist = torch.distributions.Normal(mean, std)
    action = torch.tanh(raw_tensor)
    log_probs = dist.log_prob(raw_tensor) - torch.log(1.0 - action * action + 1e-6)
    entropies = dist.entropy()
    if fire_mask_batch is not None and len(fire_mask_batch):
        mask = torch.as_tensor(fire_mask_batch, dtype=torch.bool, device=policy.device)
        if mask.any():
            log_probs[mask, 3] = 0.0
            entropies[mask, 3] = 0.0
    return log_probs.sum(dim=-1), entropies.sum(dim=-1)


def _sample_action(policy, obs_np):
    obs_tensor = torch.as_tensor(obs_np, dtype=torch.float32, device=policy.device).unsqueeze(0)
    mean, std = policy(obs_tensor)
    dist = torch.distributions.Normal(mean, std)
    raw_action = dist.sample()
    action = torch.tanh(raw_action)
    return raw_action.squeeze(0).cpu().numpy(), action.squeeze(0).cpu().numpy()


def run_episode_worker(payload):
    import ef_py as ef_local

    torch.set_num_threads(1)
    rng = np.random.default_rng(int(payload.get("seed", 0)))
    cfg = payload["cfg"]
    unit_defs_path = payload["unit_defs_path"]
    seed = payload["seed"]
    train_blue = bool(payload.get("train_blue", True))
    train_red = bool(payload.get("train_red", True))
    blue_state = payload["blue_state"]
    red_state = payload["red_state"]
    policy_cfg = payload["policy_cfg"]
    norm_state = payload.get("norm_state")
    log_level = payload.get("log_level", "warn")
    swap_sides = bool(payload.get("swap_sides", False))

    obs_dim = int(policy_cfg.get("obs_dim", 12))
    act_dim = int(policy_cfg.get("act_dim", 4))
    hidden_sizes = policy_cfg.get("hidden_sizes", [64, 64])
    log_std_init = float(policy_cfg.get("log_std_init", -0.5))
    log_std_min = float(policy_cfg.get("log_std_min", -3.0))
    log_std_max = float(policy_cfg.get("log_std_max", 0.5))

    blue_policy = MLPPolicy(obs_dim=obs_dim, act_dim=act_dim,
                            hidden_sizes=hidden_sizes,
                            log_std_init=log_std_init,
                            device=torch.device("cpu"),
                            log_std_min=log_std_min,
                            log_std_max=log_std_max)
    red_policy = MLPPolicy(obs_dim=obs_dim, act_dim=act_dim,
                           hidden_sizes=hidden_sizes,
                           log_std_init=log_std_init,
                           device=torch.device("cpu"),
                           log_std_min=log_std_min,
                           log_std_max=log_std_max)
    blue_policy.load_state_dict(blue_state)
    red_policy.load_state_dict(red_state)
    blue_policy.eval()
    red_policy.eval()

    blue_side_policy = red_policy if swap_sides else blue_policy
    red_side_policy = blue_policy if swap_sides else red_policy
    blue_side_policy_name = "red" if swap_sides else "blue"
    red_side_policy_name = "blue" if swap_sides else "red"

    if hasattr(ef_local, "set_log_level"):
        ef_local.set_log_level(str(log_level))

    kernel = ef_local.SimulationKernel()
    kernel.reset(seed)
    if unit_defs_path:
        kernel.load_unit_definitions(unit_defs_path)

    spawn_cfg = cfg.get("spawn", {})
    blue_spawn = spawn_cfg.get("blue", {})
    red_spawn = spawn_cfg.get("red", {})

    blue_pos = blue_spawn.get("position", [0.0, 0.0, 5000.0])
    blue_vel = blue_spawn.get("velocity", [250.0, 0.0, 0.0])
    red_pos = red_spawn.get("position", [10000.0, 0.0, 5000.0])
    red_vel = red_spawn.get("velocity", [-250.0, 0.0, 0.0])
    blue_pos, blue_vel, red_pos, red_vel = sample_spawn(rng, cfg, blue_pos, blue_vel, red_pos, red_vel)

    blue_id = kernel.spawn_unit(ef_local.Side.Blue, ef_local.UnitType.Aircraft,
                                blue_pos[0], blue_pos[1], blue_pos[2],
                                blue_vel[0], blue_vel[1], blue_vel[2])
    red_id = kernel.spawn_unit(ef_local.Side.Red, ef_local.UnitType.Aircraft,
                               red_pos[0], red_pos[1], red_pos[2],
                               red_vel[0], red_vel[1], red_vel[2])

    termination_cfg = cfg.get("termination", {})
    disengage_range_m = termination_cfg.get("disengage_range_m")
    disengage_hold_s = float(termination_cfg.get("disengage_hold_s", 0.0))
    min_specific_energy = termination_cfg.get("min_specific_energy_j_kg")
    energy_hold_s = float(termination_cfg.get("energy_hold_s", 0.0))
    ammo_depletion_ends = bool(termination_cfg.get("ammo_depletion_ends", False))
    no_detection_hold_s = float(termination_cfg.get("no_detection_hold_s", 0.0))
    fire_enabled = bool(cfg.get("fire_enabled", True))

    reward_cfg = cfg.get("reward", {})
    distance_weight = float(reward_cfg.get("distance_weight", -1e-4))
    detection_reward = float(reward_cfg.get("detection_reward", 0.1))
    action_penalty = float(reward_cfg.get("action_penalty", 0.01))
    fire_penalty = float(reward_cfg.get("fire_penalty", 0.0))
    damage_reward = float(reward_cfg.get("damage_reward", 0.0))
    mutual_kill_penalty = float(reward_cfg.get("mutual_kill_penalty", 0.0))
    kill_reward = float(reward_cfg.get("kill_reward", 100.0))
    death_penalty = float(reward_cfg.get("death_penalty", -100.0))

    train_cfg = cfg.get("training", {})
    mask_fire = bool(train_cfg.get("mask_fire_if_unavailable", True))
    normalize_obs = bool(train_cfg.get("normalize_observations", False))

    dt = kernel.get_time_step()
    max_steps = int(cfg.get("max_steps", 600))
    disengage_timer = 0.0
    energy_timer_blue = 0.0
    energy_timer_red = 0.0
    no_detection_timer = 0.0

    blue_obs_list = []
    blue_raw_list = []
    blue_rewards = []
    blue_fire_mask = []
    red_obs_list = []
    red_raw_list = []
    red_rewards = []
    red_fire_mask = []

    blue_fire_count = 0
    red_fire_count = 0
    blue_detection_steps = 0
    red_detection_steps = 0
    policy_fire_count = {"blue": 0, "red": 0}
    policy_detection_steps = {"blue": 0, "red": 0}
    policy_return = {"blue": 0.0, "red": 0.0}

    def record_step(policy_name, obs, raw, reward, masked):
        if policy_name == "blue" and train_blue:
            blue_obs_list.append(obs)
            blue_raw_list.append(raw)
            blue_rewards.append(reward)
            blue_fire_mask.append(masked)
        elif policy_name == "red" and train_red:
            red_obs_list.append(obs)
            red_raw_list.append(raw)
            red_rewards.append(reward)
            red_fire_mask.append(masked)

    blue_health = kernel.get_unit_health(blue_id)[0]
    red_health = kernel.get_unit_health(red_id)[0]
    prev_blue_health = blue_health
    prev_red_health = red_health
    steps_taken = 0

    for step in range(max_steps):
        blue_obs = kernel.get_agent_observation(blue_id)
        red_obs = kernel.get_agent_observation(red_id)

        obs_blue = build_observation(blue_obs, red_obs)
        obs_red = build_observation(red_obs, blue_obs)
        if normalize_obs and norm_state is not None:
            obs_blue = normalize_with_state(obs_blue, norm_state)
            obs_red = normalize_with_state(obs_red, norm_state)

        blue_raw, blue_action = _sample_action(blue_side_policy, obs_blue)
        red_raw, red_action = _sample_action(red_side_policy, obs_red)

        blue_masked = False
        red_masked = False
        blue_has_track = any(t.id == red_id for t in blue_obs.contacts)
        red_has_track = any(t.id == blue_id for t in red_obs.contacts)
        if mask_fire and not blue_obs.can_fire:
            blue_action[3] = -1.0
            blue_raw[3] = 0.0
            blue_masked = True
        if mask_fire and not red_obs.can_fire:
            red_action[3] = -1.0
            red_raw[3] = 0.0
            red_masked = True
        if mask_fire and not blue_has_track:
            blue_action[3] = -1.0
            blue_raw[3] = 0.0
            blue_masked = True
        if mask_fire and not red_has_track:
            red_action[3] = -1.0
            red_raw[3] = 0.0
            red_masked = True

        blue_fire = (blue_action[3] + 1.0) * 0.5
        red_fire = (red_action[3] + 1.0) * 0.5

        kernel.set_action(blue_id, blue_action[0], blue_action[1], blue_action[2], blue_fire)
        kernel.set_action(red_id, red_action[0], red_action[1], red_action[2], red_fire)

        blue_fired = False
        red_fired = False
        if fire_enabled and blue_fire > 0.5 and blue_obs.can_fire:
            if kernel.fire_missile(blue_id, red_id) != 0:
                blue_fired = True
                blue_fire_count += 1
        if fire_enabled and red_fire > 0.5 and red_obs.can_fire:
            if kernel.fire_missile(red_id, blue_id) != 0:
                red_fired = True
                red_fire_count += 1

        kernel.step()

        blue_health = kernel.get_unit_health(blue_id)[0]
        red_health = kernel.get_unit_health(red_id)[0]
        damage_to_blue = max(0.0, float(prev_blue_health - blue_health))
        damage_to_red = max(0.0, float(prev_red_health - red_health))
        prev_blue_health = blue_health
        prev_red_health = red_health
        steps_taken = step + 1
        blue_pos = kernel.get_unit_position(blue_id)
        red_pos = kernel.get_unit_position(red_id)
        dx = blue_pos[0] - red_pos[0]
        dy = blue_pos[1] - red_pos[1]
        dz = blue_pos[2] - red_pos[2]
        range_m = math.sqrt(dx * dx + dy * dy + dz * dz)

        blue_det = kernel.get_detections(blue_id)
        red_det = kernel.get_detections(red_id)

        reward_blue = distance_weight * range_m
        reward_red = distance_weight * range_m
        if blue_det:
            reward_blue += detection_reward
            blue_detection_steps += 1
            policy_detection_steps[blue_side_policy_name] += 1
        if red_det:
            reward_red += detection_reward
            red_detection_steps += 1
            policy_detection_steps[red_side_policy_name] += 1
        reward_blue -= action_penalty * float(blue_action[0] ** 2 + blue_action[1] ** 2 + blue_action[2] ** 2)
        reward_red -= action_penalty * float(red_action[0] ** 2 + red_action[1] ** 2 + red_action[2] ** 2)
        if blue_fired:
            reward_blue -= fire_penalty
            policy_fire_count[blue_side_policy_name] += 1
        if red_fired:
            reward_red -= fire_penalty
            policy_fire_count[red_side_policy_name] += 1
        if damage_reward > 0.0:
            reward_blue += damage_reward * damage_to_red
            reward_red += damage_reward * damage_to_blue

        terminated = False
        if red_health <= 0:
            reward_blue += kill_reward
            reward_red += death_penalty
            terminated = True
        if blue_health <= 0:
            reward_blue += death_penalty
            reward_red += kill_reward
            terminated = True
        if mutual_kill_penalty > 0.0 and blue_health <= 0 and red_health <= 0:
            reward_blue -= mutual_kill_penalty
            reward_red -= mutual_kill_penalty

        policy_return[blue_side_policy_name] += reward_blue
        policy_return[red_side_policy_name] += reward_red

        record_step(blue_side_policy_name, obs_blue, blue_raw, reward_blue, blue_masked)
        record_step(red_side_policy_name, obs_red, red_raw, reward_red, red_masked)

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

        if no_detection_hold_s > 0.0:
            if not blue_det and not red_det:
                no_detection_timer += dt
            else:
                no_detection_timer = 0.0
            if no_detection_timer >= no_detection_hold_s:
                terminated = True

        if ammo_depletion_ends:
            if blue_obs.missiles_remaining == 0 and red_obs.missiles_remaining == 0:
                missiles_in_flight = [
                    unit for unit in kernel.get_all_units()
                    if unit.type == int(ef_local.UnitType.Missile)
                ]
                if not missiles_in_flight:
                    terminated = True

        if terminated:
            break

    blue_side_dead = blue_health <= 0
    red_side_dead = red_health <= 0
    if swap_sides:
        blue_policy_win = blue_side_dead
        red_policy_win = red_side_dead
    else:
        blue_policy_win = red_side_dead
        red_policy_win = blue_side_dead

    if not blue_side_dead and not red_side_dead:
        if blue_health > red_health:
            winner = blue_side_policy_name
        elif red_health > blue_health:
            winner = red_side_policy_name
        else:
            winner = None
        blue_policy_win = (winner == "blue")
        red_policy_win = (winner == "red")

    outcome = "draw"
    if blue_policy_win and not red_policy_win:
        outcome = "blue_win"
    elif red_policy_win and not blue_policy_win:
        outcome = "red_win"

    stats = {
        "steps": steps_taken,
        "outcome": outcome,
        "blue_fire_count": blue_fire_count,
        "red_fire_count": red_fire_count,
        "blue_detection_steps": blue_detection_steps,
        "red_detection_steps": red_detection_steps,
        "return_blue": float(policy_return["blue"]),
        "return_red": float(policy_return["red"]),
        "blue_policy_fire_count": int(policy_fire_count["blue"]),
        "red_policy_fire_count": int(policy_fire_count["red"]),
        "blue_policy_detection_steps": int(policy_detection_steps["blue"]),
        "red_policy_detection_steps": int(policy_detection_steps["red"]),
    }

    return {
        "train_blue": train_blue,
        "train_red": train_red,
        "blue_obs": np.array(blue_obs_list, dtype=np.float32),
        "blue_raw": np.array(blue_raw_list, dtype=np.float32),
        "blue_rewards": blue_rewards,
        "blue_fire_mask": blue_fire_mask,
        "red_obs": np.array(red_obs_list, dtype=np.float32) if red_obs_list else np.zeros((0, obs_dim), dtype=np.float32),
        "red_raw": np.array(red_raw_list, dtype=np.float32) if red_raw_list else np.zeros((0, act_dim), dtype=np.float32),
        "red_rewards": red_rewards,
        "red_fire_mask": red_fire_mask,
        "stats": stats,
    }

class PolicySnapshot:
    def __init__(self, state_dict):
        self.state_dict = {k: v.cpu().clone() for k, v in state_dict.items()}


class StrategyPool:
    def __init__(self, max_size, rng):
        self.max_size = max_size
        self.rng = rng
        self.pool = []

    def add(self, policy):
        if self.max_size <= 0:
            return
        self.pool.append(PolicySnapshot(policy.state_dict()))
        if len(self.pool) > self.max_size:
            self.pool.pop(0)

    def sample_policy(self, policy_factory):
        if not self.pool:
            return None
        idx = int(self.rng.integers(0, len(self.pool)))
        snap = self.pool[idx]
        policy = policy_factory()
        policy.load_state_dict(snap.state_dict)
        policy.eval()
        return policy


def compute_returns(rewards, gamma):
    returns = []
    running = 0.0
    for r in reversed(rewards):
        running = r + gamma * running
        returns.append(running)
    returns.reverse()
    return returns


def run_episode(kernel, blue_policy, red_policy, rng, max_steps, unit_defs_path, cfg,
                train_blue, train_red, obs_stats, swap_sides=False):
    kernel.reset(rng.integers(0, 2**31 - 1))
    if unit_defs_path:
        kernel.load_unit_definitions(unit_defs_path)

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

    policy_map = {
        "blue": {"policy": blue_policy, "train": train_blue},
        "red": {"policy": red_policy, "train": train_red},
    }
    blue_side_policy_name = "red" if swap_sides else "blue"
    red_side_policy_name = "blue" if swap_sides else "red"
    blue_side_policy = policy_map[blue_side_policy_name]["policy"]
    red_side_policy = policy_map[red_side_policy_name]["policy"]
    blue_side_train = policy_map[blue_side_policy_name]["train"]
    red_side_train = policy_map[red_side_policy_name]["train"]

    blue_log_probs = []
    blue_entropies = []
    blue_rewards = []
    red_log_probs = []
    red_entropies = []
    red_rewards = []
    total_reward_blue = 0.0
    total_reward_red = 0.0
    termination_cfg = cfg.get("termination", {})
    disengage_range_m = termination_cfg.get("disengage_range_m")
    disengage_hold_s = float(termination_cfg.get("disengage_hold_s", 0.0))
    min_specific_energy = termination_cfg.get("min_specific_energy_j_kg")
    energy_hold_s = float(termination_cfg.get("energy_hold_s", 0.0))
    ammo_depletion_ends = bool(termination_cfg.get("ammo_depletion_ends", False))
    no_detection_hold_s = float(termination_cfg.get("no_detection_hold_s", 0.0))
    dt = kernel.get_time_step()
    disengage_timer = 0.0
    energy_timer_blue = 0.0
    energy_timer_red = 0.0
    no_detection_timer = 0.0

    reward_cfg = cfg.get("reward", {})
    distance_weight = float(reward_cfg.get("distance_weight", -1e-4))
    detection_reward = float(reward_cfg.get("detection_reward", 0.1))
    action_penalty = float(reward_cfg.get("action_penalty", 0.01))
    fire_penalty = float(reward_cfg.get("fire_penalty", 0.0))
    damage_reward = float(reward_cfg.get("damage_reward", 0.0))
    mutual_kill_penalty = float(reward_cfg.get("mutual_kill_penalty", 0.0))
    kill_reward = float(reward_cfg.get("kill_reward", 100.0))
    death_penalty = float(reward_cfg.get("death_penalty", -100.0))
    fire_enabled = bool(cfg.get("fire_enabled", True))
    train_cfg = cfg.get("training", {})
    mask_fire = bool(train_cfg.get("mask_fire_if_unavailable", True))
    normalize_obs = bool(train_cfg.get("normalize_observations", False))

    blue_fire_count = 0
    red_fire_count = 0
    blue_detection_steps = 0
    red_detection_steps = 0
    policy_fire_count = {"blue": 0, "red": 0}
    policy_detection_steps = {"blue": 0, "red": 0}
    policy_return = {"blue": 0.0, "red": 0.0}

    def act_for_side(policy, obs, train_policy):
        if train_policy:
            return policy.act(obs)
        action = policy.act_no_grad(obs)
        return action, None, None

    def record_step(policy_name, reward, logp, entropy):
        nonlocal total_reward_blue, total_reward_red
        if policy_name == "blue" and train_blue:
            total_reward_blue += reward
            blue_log_probs.append(logp.sum())
            blue_entropies.append(entropy.sum())
            blue_rewards.append(reward)
        elif policy_name == "red" and train_red:
            total_reward_red += reward
            red_log_probs.append(logp.sum())
            red_entropies.append(entropy.sum())
            red_rewards.append(reward)

    blue_health = kernel.get_unit_health(blue_id)[0]
    red_health = kernel.get_unit_health(red_id)[0]
    prev_blue_health = blue_health
    prev_red_health = red_health
    steps_taken = 0

    for step in range(max_steps):
        blue_obs = kernel.get_agent_observation(blue_id)
        red_obs = kernel.get_agent_observation(red_id)

        obs_blue = build_observation(blue_obs, red_obs)
        obs_red = build_observation(red_obs, blue_obs)
        if normalize_obs and obs_stats is not None:
            obs_stats.update([obs_blue, obs_red])
            obs_blue = obs_stats.normalize(obs_blue)
            obs_red = obs_stats.normalize(obs_red)

        blue_action, blue_logp, blue_entropy = act_for_side(blue_side_policy, obs_blue, blue_side_train)
        red_action, red_logp, red_entropy = act_for_side(red_side_policy, obs_red, red_side_train)

        if mask_fire and not blue_obs.can_fire:
            blue_action[3] = -1.0
            if blue_side_train and blue_logp is not None:
                blue_logp = blue_logp[:3]
                blue_entropy = blue_entropy[:3]
        if mask_fire and not red_obs.can_fire:
            red_action[3] = -1.0
            if red_side_train and red_logp is not None:
                red_logp = red_logp[:3]
                red_entropy = red_entropy[:3]
        if mask_fire and not any(t.id == red_id for t in blue_obs.contacts):
            blue_action[3] = -1.0
            if blue_side_train and blue_logp is not None:
                blue_logp = blue_logp[:3]
                blue_entropy = blue_entropy[:3]
        if mask_fire and not any(t.id == blue_id for t in red_obs.contacts):
            red_action[3] = -1.0
            if red_side_train and red_logp is not None:
                red_logp = red_logp[:3]
                red_entropy = red_entropy[:3]

        blue_fire = (blue_action[3] + 1.0) * 0.5
        red_fire = (red_action[3] + 1.0) * 0.5

        kernel.set_action(blue_id, blue_action[0], blue_action[1], blue_action[2], blue_fire)
        kernel.set_action(red_id, red_action[0], red_action[1], red_action[2], red_fire)

        blue_fired = False
        red_fired = False
        if fire_enabled and blue_fire > 0.5 and blue_obs.can_fire:
            if kernel.fire_missile(blue_id, red_id) != 0:
                blue_fired = True
                blue_fire_count += 1
        if fire_enabled and red_fire > 0.5 and red_obs.can_fire:
            if kernel.fire_missile(red_id, blue_id) != 0:
                red_fired = True
                red_fire_count += 1

        kernel.step()

        blue_health = kernel.get_unit_health(blue_id)[0]
        red_health = kernel.get_unit_health(red_id)[0]
        damage_to_blue = max(0.0, float(prev_blue_health - blue_health))
        damage_to_red = max(0.0, float(prev_red_health - red_health))
        prev_blue_health = blue_health
        prev_red_health = red_health
        steps_taken = step + 1
        blue_pos = kernel.get_unit_position(blue_id)
        red_pos = kernel.get_unit_position(red_id)
        dx = blue_pos[0] - red_pos[0]
        dy = blue_pos[1] - red_pos[1]
        dz = blue_pos[2] - red_pos[2]
        range_m = math.sqrt(dx * dx + dy * dy + dz * dz)

        blue_det = kernel.get_detections(blue_id)
        red_det = kernel.get_detections(red_id)

        reward_blue = distance_weight * range_m
        reward_red = distance_weight * range_m
        if blue_det:
            reward_blue += detection_reward
            blue_detection_steps += 1
            policy_detection_steps[blue_side_policy_name] += 1
        if red_det:
            reward_red += detection_reward
            red_detection_steps += 1
            policy_detection_steps[red_side_policy_name] += 1
        reward_blue -= action_penalty * float(blue_action[0] ** 2 + blue_action[1] ** 2 + blue_action[2] ** 2)
        reward_red -= action_penalty * float(red_action[0] ** 2 + red_action[1] ** 2 + red_action[2] ** 2)
        if blue_fired:
            reward_blue -= fire_penalty
            policy_fire_count[blue_side_policy_name] += 1
        if red_fired:
            reward_red -= fire_penalty
            policy_fire_count[red_side_policy_name] += 1
        if damage_reward > 0.0:
            reward_blue += damage_reward * damage_to_red
            reward_red += damage_reward * damage_to_blue

        terminated = False
        if red_health <= 0:
            reward_blue += kill_reward
            reward_red += death_penalty
            terminated = True
        if blue_health <= 0:
            reward_blue += death_penalty
            reward_red += kill_reward
            terminated = True
        if mutual_kill_penalty > 0.0 and blue_health <= 0 and red_health <= 0:
            reward_blue -= mutual_kill_penalty
            reward_red -= mutual_kill_penalty

        policy_return[blue_side_policy_name] += reward_blue
        policy_return[red_side_policy_name] += reward_red

        record_step(blue_side_policy_name, reward_blue, blue_logp, blue_entropy)
        record_step(red_side_policy_name, reward_red, red_logp, red_entropy)

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

        if no_detection_hold_s > 0.0:
            if not blue_det and not red_det:
                no_detection_timer += dt
            else:
                no_detection_timer = 0.0
            if no_detection_timer >= no_detection_hold_s:
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

    blue_side_dead = blue_health <= 0
    red_side_dead = red_health <= 0

    if blue_side_dead and not red_side_dead:
        winner = red_side_policy_name
    elif red_side_dead and not blue_side_dead:
        winner = blue_side_policy_name
    elif not blue_side_dead and not red_side_dead:
        if blue_health > red_health:
            winner = blue_side_policy_name
        elif red_health > blue_health:
            winner = red_side_policy_name
        else:
            winner = None
    else:
        winner = None

    outcome = "draw"
    if winner == "blue":
        outcome = "blue_win"
    elif winner == "red":
        outcome = "red_win"

    stats = {
        "steps": steps_taken,
        "outcome": outcome,
        "blue_fire_count": blue_fire_count,
        "red_fire_count": red_fire_count,
        "blue_detection_steps": blue_detection_steps,
        "red_detection_steps": red_detection_steps,
        "return_blue": float(policy_return["blue"]),
        "return_red": float(policy_return["red"]),
        "blue_policy_fire_count": int(policy_fire_count["blue"]),
        "red_policy_fire_count": int(policy_fire_count["red"]),
        "blue_policy_detection_steps": int(policy_detection_steps["blue"]),
        "red_policy_detection_steps": int(policy_detection_steps["red"]),
    }
    return (total_reward_blue, total_reward_red,
            blue_log_probs, blue_entropies, blue_rewards,
            red_log_probs, red_entropies, red_rewards,
            stats)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def ensure_dir(path):
    if path:
        os.makedirs(path, exist_ok=True)


def write_jsonl(path, record):
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True))
        handle.write("\n")


def save_checkpoint(output_dir, episode_idx, blue_policy, red_policy, strategy_pool, state):
    if not output_dir:
        return
    ckpt_dir = os.path.join(output_dir, "checkpoints", f"ep_{episode_idx:05d}")
    ensure_dir(ckpt_dir)
    torch.save(blue_policy.state_dict(), os.path.join(ckpt_dir, "blue.pt"))
    torch.save(red_policy.state_dict(), os.path.join(ckpt_dir, "red.pt"))
    torch.save([snap.state_dict for snap in strategy_pool.pool], os.path.join(ckpt_dir, "pool.pt"))
    with open(os.path.join(ckpt_dir, "trainer_state.json"), "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, ensure_ascii=True)


def load_checkpoint(path, policy, strategy_pool):
    if not path or not os.path.isdir(path):
        return None
    blue_path = os.path.join(path, "blue.pt")
    red_path = os.path.join(path, "red.pt")
    pool_path = os.path.join(path, "pool.pt")
    state_path = os.path.join(path, "trainer_state.json")
    state = None
    if os.path.isfile(blue_path):
        policy["blue"].load_state_dict(torch.load(blue_path, map_location=policy["device"]))
    if os.path.isfile(red_path):
        policy["red"].load_state_dict(torch.load(red_path, map_location=policy["device"]))
    if os.path.isfile(pool_path):
        loaded = torch.load(pool_path, map_location="cpu")
        strategy_pool.pool = [PolicySnapshot(snap) for snap in loaded]
    if os.path.isfile(state_path):
        with open(state_path, "r", encoding="utf-8") as handle:
            state = json.load(handle)
    return state


def main():
    parser = argparse.ArgumentParser(description="Minimal self-play training loop.")
    parser.add_argument("--config", type=str, default="examples/training/selfplay_config.json")
    parser.add_argument("--episodes", type=int, default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--gamma", type=float, default=None)
    parser.add_argument("--unit-defs", type=str, default=None)
    args = parser.parse_args()

    cfg = {}
    if args.config:
        cfg_path = args.config
        if not os.path.isabs(cfg_path):
            cfg_path = os.path.join(repo_root, cfg_path)
        if os.path.isfile(cfg_path):
            cfg = load_json(cfg_path)

    episodes = int(cfg.get("episodes", 30))
    max_steps = int(cfg.get("max_steps", 600))
    seed = int(cfg.get("seed", 7))
    lr = float(cfg.get("learning_rate", 1e-3))
    gamma = float(cfg.get("gamma", 0.99))
    unit_defs = cfg.get("unit_definitions", "content/units/default_units.json")
    num_envs = int(cfg.get("num_envs", 1))
    parallel_mode = cfg.get("parallel_mode", "process")
    output_dir = cfg.get("output_dir", "")
    checkpoint_interval = int(cfg.get("checkpoint_interval", 0))
    resume_dir = cfg.get("resume_dir", "")
    log_level = cfg.get("log_level", "warn")

    if args.episodes is not None:
        episodes = args.episodes
    if args.max_steps is not None:
        max_steps = args.max_steps
    if args.seed is not None:
        seed = args.seed
    if args.lr is not None:
        lr = args.lr
    if args.gamma is not None:
        gamma = args.gamma
    if args.unit_defs is not None:
        unit_defs = args.unit_defs

    unit_defs_path = os.path.join(repo_root, unit_defs) if unit_defs else ""
    if hasattr(ef_py, "set_log_level"):
        ef_py.set_log_level(str(log_level))

    torch.manual_seed(seed)
    policy_cfg = cfg.get("policy", {})
    obs_dim = int(policy_cfg.get("obs_dim", 12))
    act_dim = int(policy_cfg.get("act_dim", 4))
    hidden_sizes = policy_cfg.get("hidden_sizes", [64, 64])
    log_std_init = float(policy_cfg.get("log_std_init", -0.5))
    log_std_min = float(policy_cfg.get("log_std_min", -3.0))
    log_std_max = float(policy_cfg.get("log_std_max", 0.5))
    use_cuda = bool(policy_cfg.get("use_cuda", False))
    device = torch.device("cuda" if use_cuda and torch.cuda.is_available() else "cpu")

    def make_policy(seed_offset):
        torch.manual_seed(seed + seed_offset)
        return MLPPolicy(obs_dim=obs_dim,
                         act_dim=act_dim,
                         hidden_sizes=hidden_sizes,
                         log_std_init=log_std_init,
                         device=device,
                         log_std_min=log_std_min,
                         log_std_max=log_std_max)

    blue_policy = make_policy(0)
    red_policy = make_policy(1)
    blue_optimizer = torch.optim.Adam(blue_policy.parameters(), lr=lr)
    red_optimizer = torch.optim.Adam(red_policy.parameters(), lr=lr)
    rng = np.random.default_rng(seed)

    pool_cfg = cfg.get("opponent_pool", {})
    pool_size = int(pool_cfg.get("max_size", 8))
    pool_update_interval = int(pool_cfg.get("update_interval", 5))
    pool_burn_in = int(pool_cfg.get("burn_in", 3))
    history_prob = float(pool_cfg.get("history_prob", 0.5))

    strategy_pool = StrategyPool(pool_size, rng)

    baseline_blue = 0.0
    baseline_red = 0.0
    train_cfg = cfg.get("training", {})
    entropy_coef = float(train_cfg.get("entropy_coef", 0.0))
    grad_clip_norm = float(train_cfg.get("grad_clip_norm", 0.0))
    normalize_adv = bool(train_cfg.get("advantage_norm", False))
    normalize_obs = bool(train_cfg.get("normalize_observations", False))
    symmetric_training = bool(train_cfg.get("symmetric_training", False))

    if parallel_mode == "process" and num_envs > 1:
        kernels = []
    else:
        kernels = [ef_py.SimulationKernel() for _ in range(max(1, num_envs))]
    obs_stats = RunningMeanStd(obs_dim) if normalize_obs else None

    run_id = cfg.get("run_id")
    if not run_id:
        run_id = f"selfplay_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    if output_dir:
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(repo_root, output_dir)
        output_dir = os.path.join(output_dir, run_id)
        ensure_dir(output_dir)
    log_path = os.path.join(output_dir, "train_log.jsonl") if output_dir else ""
    if output_dir:
        print(f"Logging to: {output_dir}")

    resume_state = None
    if resume_dir:
        if not os.path.isabs(resume_dir):
            resume_dir = os.path.join(repo_root, resume_dir)
        resume_state = load_checkpoint(resume_dir, {"blue": blue_policy, "red": red_policy, "device": device}, strategy_pool)
        if resume_state:
            baseline_blue = resume_state.get("baseline_blue", baseline_blue)
            baseline_red = resume_state.get("baseline_red", baseline_red)
            seed = resume_state.get("seed", seed)

    mp_pool = None
    if parallel_mode == "process" and num_envs > 1:
        mp_ctx = mp.get_context("spawn")
        mp_pool = mp_ctx.Pool(processes=num_envs)

    try:
        for episode in range(episodes):
            batch_blue_log_probs = []
            batch_blue_entropies = []
            batch_blue_returns = []
            batch_red_log_probs = []
            batch_red_entropies = []
            batch_red_returns = []
            batch_stats = []
            history_used_count = 0

            norm_state = obs_stats.snapshot() if obs_stats is not None else None

            if mp_pool is not None:
                tasks = []
                for env_idx in range(num_envs):
                    swap_sides = symmetric_training and (rng.random() < 0.5)
                    train_blue = True
                    train_red = True
                    blue_state = blue_policy.state_dict()
                    red_state = red_policy.state_dict()
                    if (rng.random() < history_prob) and strategy_pool.pool:
                        sampled = strategy_pool.sample_policy(lambda: make_policy(1000 + episode + env_idx))
                        if sampled is not None:
                            history_used_count += 1
                            if rng.random() < 0.5:
                                blue_state = sampled.state_dict()
                                train_blue = False
                            else:
                                red_state = sampled.state_dict()
                                train_red = False

                    task = {
                        "cfg": cfg,
                        "unit_defs_path": unit_defs_path,
                        "seed": int(rng.integers(0, 2**31 - 1)),
                        "train_blue": train_blue,
                        "train_red": train_red,
                        "blue_state": blue_state,
                        "red_state": red_state,
                        "policy_cfg": policy_cfg,
                        "norm_state": norm_state,
                        "log_level": log_level,
                        "swap_sides": swap_sides,
                    }
                    tasks.append(task)
                results = mp_pool.map(run_episode_worker, tasks)

                all_blue_obs = []
                all_blue_raw = []
                all_blue_masks = []
                all_blue_returns = []
                all_blue_rewards = []
                all_red_obs = []
                all_red_raw = []
                all_red_masks = []
                all_red_returns = []
                all_red_rewards = []

                for result in results:
                    stats = result["stats"]
                    batch_stats.append(stats)
                    if result.get("train_blue", True):
                        blue_rewards = result["blue_rewards"]
                        returns_blue = compute_returns(blue_rewards, gamma)
                        all_blue_rewards.extend(blue_rewards)
                        all_blue_returns.extend(returns_blue)
                        all_blue_obs.extend(result["blue_obs"])
                        all_blue_raw.extend(result["blue_raw"])
                        all_blue_masks.extend(result["blue_fire_mask"])

                    if result.get("train_red", False):
                        red_rewards = result["red_rewards"]
                        returns_red = compute_returns(red_rewards, gamma)
                        all_red_rewards.extend(red_rewards)
                        all_red_returns.extend(returns_red)
                        all_red_obs.extend(result["red_obs"])
                        all_red_raw.extend(result["red_raw"])
                        all_red_masks.extend(result["red_fire_mask"])

                if normalize_obs and obs_stats is not None:
                    if all_blue_obs:
                        obs_stats.update(all_blue_obs)
                    if all_red_obs:
                        obs_stats.update(all_red_obs)

                blue_obs_np = np.array(all_blue_obs, dtype=np.float32) if all_blue_obs else np.zeros((0, obs_dim), dtype=np.float32)
                blue_raw_np = np.array(all_blue_raw, dtype=np.float32) if all_blue_raw else np.zeros((0, act_dim), dtype=np.float32)
                if normalize_obs and norm_state is not None and len(blue_obs_np):
                    blue_obs_np = normalize_with_state(blue_obs_np, norm_state)
                blue_lp, blue_ent = compute_log_probs(blue_policy, blue_obs_np, blue_raw_np, all_blue_masks) if len(blue_obs_np) else (torch.tensor([], device=device), torch.tensor([], device=device))
                batch_blue_log_probs.extend(list(blue_lp))
                batch_blue_entropies.extend(list(blue_ent))
                batch_blue_returns.extend(all_blue_returns)

                if all_red_obs:
                    red_obs_np = np.array(all_red_obs, dtype=np.float32)
                    red_raw_np = np.array(all_red_raw, dtype=np.float32)
                    if normalize_obs and norm_state is not None:
                        red_obs_np = normalize_with_state(red_obs_np, norm_state)
                    red_lp, red_ent = compute_log_probs(red_policy, red_obs_np, red_raw_np, all_red_masks)
                    batch_red_log_probs.extend(list(red_lp))
                    batch_red_entropies.extend(list(red_ent))
                    batch_red_returns.extend(all_red_returns)
            else:
                for env_idx in range(len(kernels)):
                    swap_sides = symmetric_training and (rng.random() < 0.5)
                    train_blue = True
                    train_red = True
                    blue_policy_used = blue_policy
                    red_policy_used = red_policy
                    if (rng.random() < history_prob) and strategy_pool.pool:
                        sampled = strategy_pool.sample_policy(lambda: make_policy(1000 + episode + env_idx))
                        if sampled is not None:
                            history_used_count += 1
                            if rng.random() < 0.5:
                                blue_policy_used = sampled
                                train_blue = False
                            else:
                                red_policy_used = sampled
                                train_red = False

                    (total_blue, total_red,
                     blue_log_probs, blue_entropies, blue_rewards,
                     red_log_probs, red_entropies, red_rewards,
                     stats) = run_episode(
                        kernels[env_idx],
                        blue_policy_used,
                        red_policy_used,
                        rng,
                        max_steps,
                        unit_defs_path,
                        cfg,
                        train_blue=train_blue,
                        train_red=train_red,
                        obs_stats=obs_stats,
                        swap_sides=swap_sides
                    )

                    returns_blue = compute_returns(blue_rewards, gamma)
                    if returns_blue:
                        batch_blue_returns.extend(returns_blue)
                        batch_blue_log_probs.extend(blue_log_probs)
                        batch_blue_entropies.extend(blue_entropies)
                    if train_red and red_rewards:
                        returns_red = compute_returns(red_rewards, gamma)
                        batch_red_returns.extend(returns_red)
                        batch_red_log_probs.extend(red_log_probs)
                        batch_red_entropies.extend(red_entropies)

                    batch_stats.append(stats)

            if batch_blue_returns:
                baseline_blue = 0.9 * baseline_blue + 0.1 * float(np.mean(batch_blue_returns))
            if batch_red_returns:
                baseline_red = 0.9 * baseline_red + 0.1 * float(np.mean(batch_red_returns))

            if batch_blue_log_probs:
                blue_optimizer.zero_grad()
                returns_tensor = torch.tensor(batch_blue_returns, dtype=torch.float32, device=device)
                advantages = returns_tensor - baseline_blue
                if normalize_adv:
                    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
                log_probs_tensor = torch.stack(batch_blue_log_probs)
                entropies_tensor = torch.stack(batch_blue_entropies) if batch_blue_entropies else None
                loss_blue = -(log_probs_tensor * advantages).mean()
                if entropies_tensor is not None:
                    loss_blue -= entropy_coef * entropies_tensor.mean()
                loss_blue.backward()
                if grad_clip_norm > 0.0:
                    torch.nn.utils.clip_grad_norm_(blue_policy.parameters(), grad_clip_norm)
                blue_optimizer.step()

            if batch_red_log_probs:
                red_optimizer.zero_grad()
                returns_tensor = torch.tensor(batch_red_returns, dtype=torch.float32, device=device)
                advantages = returns_tensor - baseline_red
                if normalize_adv:
                    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
                log_probs_tensor = torch.stack(batch_red_log_probs)
                entropies_tensor = torch.stack(batch_red_entropies) if batch_red_entropies else None
                loss_red = -(log_probs_tensor * advantages).mean()
                if entropies_tensor is not None:
                    loss_red -= entropy_coef * entropies_tensor.mean()
                loss_red.backward()
                if grad_clip_norm > 0.0:
                    torch.nn.utils.clip_grad_norm_(red_policy.parameters(), grad_clip_norm)
                red_optimizer.step()

            if episode + 1 >= pool_burn_in and pool_update_interval > 0:
                if (episode + 1) % pool_update_interval == 0:
                    strategy_pool.add(blue_policy)
                    strategy_pool.add(red_policy)

            wins_blue = sum(1 for s in batch_stats if s["outcome"] == "blue_win")
            wins_red = sum(1 for s in batch_stats if s["outcome"] == "red_win")
            draws = len(batch_stats) - wins_blue - wins_red
            avg_steps = float(np.mean([s["steps"] for s in batch_stats])) if batch_stats else 0.0
            avg_blue_return = float(np.mean([s["return_blue"] for s in batch_stats])) if batch_stats else 0.0
            avg_red_return = float(np.mean([s["return_red"] for s in batch_stats])) if batch_stats else 0.0
            avg_blue_fire = float(np.mean([s.get("blue_policy_fire_count", s.get("blue_fire_count", 0.0)) for s in batch_stats])) if batch_stats else 0.0
            avg_red_fire = float(np.mean([s.get("red_policy_fire_count", s.get("red_fire_count", 0.0)) for s in batch_stats])) if batch_stats else 0.0
            avg_blue_det = float(np.mean([s.get("blue_policy_detection_steps", s.get("blue_detection_steps", 0.0)) for s in batch_stats])) if batch_stats else 0.0
            avg_red_det = float(np.mean([s.get("red_policy_detection_steps", s.get("red_detection_steps", 0.0)) for s in batch_stats])) if batch_stats else 0.0

            record = {
                "update": episode + 1,
                "num_envs": num_envs if mp_pool is not None else len(kernels),
                "avg_blue_return": avg_blue_return,
                "avg_red_return": avg_red_return,
                "blue_win_rate": wins_blue / max(1, len(batch_stats)),
                "red_win_rate": wins_red / max(1, len(batch_stats)),
                "draw_rate": draws / max(1, len(batch_stats)),
                "avg_steps": avg_steps,
                "avg_blue_fire": avg_blue_fire,
                "avg_red_fire": avg_red_fire,
                "avg_blue_detection_steps": avg_blue_det,
                "avg_red_detection_steps": avg_red_det,
                "history_opponent_rate": history_used_count / max(1, len(batch_stats)),
            }
            write_jsonl(log_path, record)
            render_progress(episode + 1, episodes, record)

            if checkpoint_interval > 0 and output_dir:
                if (episode + 1) % checkpoint_interval == 0:
                    state = {
                        "episode": episode + 1,
                        "baseline_blue": baseline_blue,
                        "baseline_red": baseline_red,
                        "seed": seed
                    }
                    save_checkpoint(output_dir, episode + 1, blue_policy, red_policy, strategy_pool, state)

        if output_dir:
            state = {
                "episode": episodes,
                "baseline_blue": baseline_blue,
                "baseline_red": baseline_red,
                "seed": seed
            }
            save_checkpoint(output_dir, episodes, blue_policy, red_policy, strategy_pool, state)

        if episodes > 0:
            sys.stdout.write("\n")
            sys.stdout.flush()
    finally:
        if mp_pool is not None:
            mp_pool.close()
            mp_pool.join()


if __name__ == "__main__":
    main()
