import argparse
import json
import math
import os
import sys

import numpy as np

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(repo_root, "build"))

import ef_py


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


class LinearPolicy:
    def __init__(self, obs_dim, act_dim, std=0.2, seed=0):
        rng = np.random.default_rng(seed)
        self.W = rng.normal(scale=0.1, size=(act_dim, obs_dim))
        self.b = np.zeros(act_dim, dtype=np.float32)
        self.std = float(std)

    def act(self, obs, rng):
        z = self.W @ obs + self.b
        mean = np.tanh(z)
        noise = rng.normal(0.0, self.std, size=mean.shape)
        raw = mean + noise
        action = np.clip(raw, -1.0, 1.0)
        return action, raw, mean

    def logprob_grads(self, obs, raw_action, mean):
        std = self.std
        std_sq = std * std
        diff = raw_action - mean
        logp = -0.5 * np.sum((diff * diff) / std_sq + math.log(2.0 * math.pi * std_sq))
        dlogp_dmean = diff / std_sq
        dmean_dz = 1.0 - mean * mean
        delta = dlogp_dmean * dmean_dz
        grad_W = np.outer(delta, obs)
        grad_b = delta
        return logp, grad_W, grad_b


class PolicySnapshot:
    def __init__(self, W, b):
        self.W = np.array(W, copy=True)
        self.b = np.array(b, copy=True)


class StrategyPool:
    def __init__(self, max_size, rng):
        self.max_size = max_size
        self.rng = rng
        self.pool = []

    def add(self, policy):
        if self.max_size <= 0:
            return
        self.pool.append(PolicySnapshot(policy.W, policy.b))
        if len(self.pool) > self.max_size:
            self.pool.pop(0)

    def sample_policy(self, std):
        if not self.pool:
            return None
        idx = int(self.rng.integers(0, len(self.pool)))
        snap = self.pool[idx]
        policy = LinearPolicy(obs_dim=snap.W.shape[1], act_dim=snap.W.shape[0], std=std, seed=0)
        policy.W = np.array(snap.W, copy=True)
        policy.b = np.array(snap.b, copy=True)
        return policy


def compute_returns(rewards, gamma):
    returns = []
    running = 0.0
    for r in reversed(rewards):
        running = r + gamma * running
        returns.append(running)
    returns.reverse()
    return returns


def run_episode(kernel, blue_policy, red_policy, rng, max_steps, unit_defs_path, cfg):
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

    blue_id = kernel.spawn_unit(ef_py.Side.Blue, ef_py.UnitType.Aircraft,
                                blue_pos[0], blue_pos[1], blue_pos[2],
                                blue_vel[0], blue_vel[1], blue_vel[2])
    red_id = kernel.spawn_unit(ef_py.Side.Red, ef_py.UnitType.Aircraft,
                               red_pos[0], red_pos[1], red_pos[2],
                               red_vel[0], red_vel[1], red_vel[2])

    blue_traj = []
    red_traj = []
    total_reward_blue = 0.0
    total_reward_red = 0.0
    termination_cfg = cfg.get("termination", {})
    disengage_range_m = termination_cfg.get("disengage_range_m")
    disengage_hold_s = float(termination_cfg.get("disengage_hold_s", 0.0))
    min_specific_energy = termination_cfg.get("min_specific_energy_j_kg")
    energy_hold_s = float(termination_cfg.get("energy_hold_s", 0.0))
    ammo_depletion_ends = bool(termination_cfg.get("ammo_depletion_ends", False))
    dt = kernel.get_time_step()
    disengage_timer = 0.0
    energy_timer_blue = 0.0
    energy_timer_red = 0.0

    reward_cfg = cfg.get("reward", {})
    distance_weight = float(reward_cfg.get("distance_weight", -1e-4))
    detection_reward = float(reward_cfg.get("detection_reward", 0.1))
    action_penalty = float(reward_cfg.get("action_penalty", 0.01))
    kill_reward = float(reward_cfg.get("kill_reward", 100.0))
    death_penalty = float(reward_cfg.get("death_penalty", -100.0))
    fire_enabled = bool(cfg.get("fire_enabled", True))

    for step in range(max_steps):
        blue_obs = kernel.get_agent_observation(blue_id)
        red_obs = kernel.get_agent_observation(red_id)

        obs_blue = build_observation(blue_obs, red_obs)
        obs_red = build_observation(red_obs, blue_obs)

        blue_action, blue_raw, blue_mean = blue_policy.act(obs_blue, rng)
        red_action, red_raw, red_mean = red_policy.act(obs_red, rng)

        blue_fire = (blue_action[3] + 1.0) * 0.5
        red_fire = (red_action[3] + 1.0) * 0.5

        kernel.set_action(blue_id, blue_action[0], blue_action[1], blue_action[2], blue_fire)
        kernel.set_action(red_id, red_action[0], red_action[1], red_action[2], red_fire)

        if fire_enabled and blue_fire > 0.5 and blue_obs.can_fire:
            kernel.fire_missile(blue_id, red_id)
        if fire_enabled and red_fire > 0.5 and red_obs.can_fire:
            kernel.fire_missile(red_id, blue_id)

        kernel.step()

        blue_health = kernel.get_unit_health(blue_id)[0]
        red_health = kernel.get_unit_health(red_id)[0]
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
        if red_det:
            reward_red += detection_reward
        reward_blue -= action_penalty * float(blue_action[0] ** 2 + blue_action[1] ** 2 + blue_action[2] ** 2)
        reward_red -= action_penalty * float(red_action[0] ** 2 + red_action[1] ** 2 + red_action[2] ** 2)

        terminated = False
        if red_health <= 0:
            reward_blue += kill_reward
            reward_red += death_penalty
            terminated = True
        if blue_health <= 0:
            reward_blue += death_penalty
            reward_red += kill_reward
            terminated = True

        total_reward_blue += reward_blue
        total_reward_red += reward_red

        blue_traj.append((obs_blue, blue_raw, blue_mean, reward_blue))
        red_traj.append((obs_red, red_raw, red_mean, reward_red))

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

    return total_reward_blue, total_reward_red, blue_traj, red_traj


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


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
    lr = float(cfg.get("learning_rate", 1e-2))
    gamma = float(cfg.get("gamma", 0.99))
    unit_defs = cfg.get("unit_definitions", "content/units/default_units.json")

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

    kernel = ef_py.SimulationKernel()
    unit_defs_path = os.path.join(repo_root, unit_defs) if unit_defs else ""

    policy_cfg = cfg.get("policy", {})
    obs_dim = int(policy_cfg.get("obs_dim", 12))
    act_dim = int(policy_cfg.get("act_dim", 4))
    std = float(policy_cfg.get("std", 0.2))

    blue_policy = LinearPolicy(obs_dim=obs_dim, act_dim=act_dim, std=std, seed=seed)
    red_policy = LinearPolicy(obs_dim=obs_dim, act_dim=act_dim, std=std, seed=seed + 1)
    rng = np.random.default_rng(seed)

    pool_cfg = cfg.get("opponent_pool", {})
    pool_size = int(pool_cfg.get("max_size", 8))
    pool_update_interval = int(pool_cfg.get("update_interval", 5))
    pool_burn_in = int(pool_cfg.get("burn_in", 3))
    history_prob = float(pool_cfg.get("history_prob", 0.5))

    pool = StrategyPool(pool_size, rng)

    baseline_blue = 0.0
    baseline_red = 0.0

    for episode in range(episodes):
        use_history = (rng.random() < history_prob) and pool.pool
        opponent_policy = red_policy
        red_used_history = False
        if use_history:
            sampled = pool.sample_policy(std)
            if sampled is not None:
                opponent_policy = sampled
                red_used_history = True

        total_blue, total_red, traj_blue, traj_red = run_episode(
            kernel, blue_policy, opponent_policy, rng, max_steps, unit_defs_path, cfg
        )

        returns_blue = compute_returns([t[3] for t in traj_blue], gamma)
        returns_red = compute_returns([t[3] for t in traj_red], gamma)

        if returns_blue:
            baseline_blue = 0.9 * baseline_blue + 0.1 * returns_blue[0]
        if returns_red and not red_used_history:
            baseline_red = 0.9 * baseline_red + 0.1 * returns_red[0]

        grad_W_blue = np.zeros_like(blue_policy.W)
        grad_b_blue = np.zeros_like(blue_policy.b)
        for (obs, raw_action, mean, _reward), ret in zip(traj_blue, returns_blue):
            advantage = ret - baseline_blue
            _, gW, gB = blue_policy.logprob_grads(obs, raw_action, mean)
            grad_W_blue += advantage * gW
            grad_b_blue += advantage * gB

        blue_policy.W += lr * grad_W_blue
        blue_policy.b += lr * grad_b_blue

        if not red_used_history:
            grad_W_red = np.zeros_like(red_policy.W)
            grad_b_red = np.zeros_like(red_policy.b)
            for (obs, raw_action, mean, _reward), ret in zip(traj_red, returns_red):
                advantage = ret - baseline_red
                _, gW, gB = red_policy.logprob_grads(obs, raw_action, mean)
                grad_W_red += advantage * gW
                grad_b_red += advantage * gB
            red_policy.W += lr * grad_W_red
            red_policy.b += lr * grad_b_red

        if episode + 1 >= pool_burn_in and pool_update_interval > 0:
            if (episode + 1) % pool_update_interval == 0:
                pool.add(blue_policy)
                pool.add(red_policy)

        history_tag = "history" if red_used_history else "current"
        print(
            f"Episode {episode + 1:03d} | blue_return={total_blue:.2f} | "
            f"red_return={total_red:.2f} | steps={len(traj_blue)} | "
            f"red_opponent={history_tag}"
        )


if __name__ == "__main__":
    main()
