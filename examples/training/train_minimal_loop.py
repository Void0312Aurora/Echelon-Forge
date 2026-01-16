import argparse
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


def run_episode(kernel, policy, rng, max_steps, opponent_mode):
    kernel.reset(rng.integers(0, 2**31 - 1))
    blue_id = kernel.spawn_unit(ef_py.Side.Blue, ef_py.UnitType.Aircraft,
                                0.0, 0.0, 5000.0, 250.0, 0.0, 0.0)
    red_id = kernel.spawn_unit(ef_py.Side.Red, ef_py.UnitType.Aircraft,
                               10000.0, 0.0, 5000.0, -250.0, 0.0, 0.0)

    dt = kernel.get_time_step()
    traj = []
    total_reward = 0.0
    terminated = False

    for step in range(max_steps):
        blue_obs = kernel.get_agent_observation(blue_id)
        red_obs = kernel.get_agent_observation(red_id)
        obs = build_observation(blue_obs, red_obs)

        action, raw_action, mean = policy.act(obs, rng)
        fire_cmd = (action[3] + 1.0) * 0.5
        kernel.set_action(blue_id, action[0], action[1], action[2], fire_cmd)

        if opponent_mode == "pursuit":
            blue_pos = kernel.get_unit_position(blue_id)
            red_pos = kernel.get_unit_position(red_id)
            heading = nav_heading_to_target(red_pos, blue_pos)
            kernel.set_command(red_id, heading, 320.0, red_pos[2])
        else:
            red_action = rng.uniform(-1.0, 1.0, size=3)
            kernel.set_action(red_id, red_action[0], red_action[1], red_action[2], 0.0)

        if fire_cmd > 0.5 and blue_obs.can_fire:
            kernel.fire_missile(blue_id, red_id)

        kernel.step()

        blue_health = kernel.get_unit_health(blue_id)[0]
        red_health = kernel.get_unit_health(red_id)[0]
        blue_pos = kernel.get_unit_position(blue_id)
        red_pos = kernel.get_unit_position(red_id)
        dx = blue_pos[0] - red_pos[0]
        dy = blue_pos[1] - red_pos[1]
        dz = blue_pos[2] - red_pos[2]
        range_m = math.sqrt(dx * dx + dy * dy + dz * dz)

        detections = kernel.get_detections(blue_id)
        reward = -range_m * 1e-4
        if detections:
            reward += 0.1
        reward -= 0.01 * float(action[0] * action[0] + action[1] * action[1] + action[2] * action[2])
        if red_health <= 0:
            reward += 100.0
            terminated = True
        if blue_health <= 0:
            reward -= 100.0
            terminated = True

        total_reward += reward
        traj.append((obs, raw_action, mean, reward))

        if terminated:
            break

    return total_reward, traj


def compute_returns(rewards, gamma):
    returns = []
    running = 0.0
    for r in reversed(rewards):
        running = r + gamma * running
        returns.append(running)
    returns.reverse()
    return returns


def main():
    parser = argparse.ArgumentParser(description="Minimal RL training loop (single agent).")
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--max-steps", type=int, default=600)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--lr", type=float, default=1e-2)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--opponent", choices=["pursuit", "random"], default="pursuit")
    args = parser.parse_args()

    kernel = ef_py.SimulationKernel()
    policy = LinearPolicy(obs_dim=12, act_dim=4, std=0.2, seed=args.seed)
    rng = np.random.default_rng(args.seed)
    baseline = 0.0

    for episode in range(args.episodes):
        total_reward, traj = run_episode(kernel, policy, rng, args.max_steps, args.opponent)
        rewards = [t[3] for t in traj]
        returns = compute_returns(rewards, args.gamma)
        baseline = 0.9 * baseline + 0.1 * (returns[0] if returns else 0.0)

        grad_W = np.zeros_like(policy.W)
        grad_b = np.zeros_like(policy.b)
        for (obs, raw_action, mean, _reward), ret in zip(traj, returns):
            advantage = ret - baseline
            _, gW, gB = policy.logprob_grads(obs, raw_action, mean)
            grad_W += advantage * gW
            grad_b += advantage * gB

        policy.W += args.lr * grad_W
        policy.b += args.lr * grad_b

        print(f"Episode {episode + 1:03d} | return={total_reward:.2f} | steps={len(traj)}")


if __name__ == "__main__":
    main()
