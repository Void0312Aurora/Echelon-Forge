from __future__ import annotations

import unittest

import numpy as np

import gymnasium as gym
from gymnasium import spaces

from gym_envs.leader_env import LeaderTrainingEnv
from python.rl.shared_memory_vec_env import SharedMemorySubprocVecEnv


class _CounterDictEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, env_id: int):
        super().__init__()
        self.render_mode = None
        self.env_id = int(env_id)
        self.count = 0
        self.observation_space = spaces.Dict(
            {
                "vec": spaces.Box(low=-1.0e6, high=1.0e6, shape=(3,), dtype=np.float32),
                "mat": spaces.Box(low=-1.0e6, high=1.0e6, shape=(2, 2), dtype=np.float32),
            }
        )
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)

    def _obs(self):
        base = float(self.env_id * 10 + self.count)
        return {
            "vec": np.asarray([float(self.env_id), float(self.count), base], dtype=np.float32),
            "mat": np.full((2, 2), base, dtype=np.float32),
        }

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.count = 0
        return self._obs(), {"count": self.count, "env_id": self.env_id}

    def step(self, action):
        _ = action
        self.count += 1
        terminated = self.count >= 2
        truncated = False
        return self._obs(), float(self.count), terminated, truncated, {"count": self.count, "env_id": self.env_id}


class _DummyFrozenPolicy:
    def __init__(self):
        self.calls = 0

    def predict(self, obs, deterministic=True):
        _ = (obs, deterministic)
        self.calls += 1
        value = float(self.calls)
        return np.asarray([value, -value], dtype=np.float32), None


class PerformanceKnobTests(unittest.TestCase):
    def test_execution_action_repeat_reuses_predicted_action(self):
        env = LeaderTrainingEnv.__new__(LeaderTrainingEnv)
        env.execution_backend = "frozen_model"
        env.execution_action_repeat = 3
        env._exec_policy = _DummyFrozenPolicy()
        env._last_exec_action = None
        env._exec_action_repeat_remaining = 0
        env._last_effective_execution_action_repeat = 1

        first = env._predict_execution_action({})
        second = env._predict_execution_action({})
        third = env._predict_execution_action({})
        fourth = env._predict_execution_action({})

        self.assertEqual(env._exec_policy.calls, 2)
        self.assertTrue(np.allclose(first, second))
        self.assertTrue(np.allclose(first, third))
        self.assertFalse(np.allclose(first, fourth))
        self.assertEqual(env._last_effective_execution_action_repeat, 3)

    def test_shared_memory_vec_env_returns_shared_observation_views(self):
        vec_env = SharedMemorySubprocVecEnv(
            [lambda env_id=i: _CounterDictEnv(env_id) for i in range(2)],
            start_method="forkserver",
        )
        try:
            obs = vec_env.reset()
            self.assertEqual(obs["vec"].shape, (2, 3))
            self.assertEqual(obs["mat"].shape, (2, 2, 2))
            self.assertTrue(np.shares_memory(obs["vec"], vec_env.buf_obs["vec"]))
            self.assertTrue(np.allclose(obs["vec"][:, 1], np.asarray([0.0, 0.0], dtype=np.float32)))

            obs, rewards, dones, infos = vec_env.step(np.zeros((2, 1), dtype=np.float32))
            self.assertTrue(np.allclose(rewards, np.asarray([1.0, 1.0], dtype=np.float32)))
            self.assertTrue(np.all(dones == np.asarray([False, False])))
            self.assertTrue(np.allclose(obs["vec"][:, 1], np.asarray([1.0, 1.0], dtype=np.float32)))
            self.assertEqual(infos[0]["count"], 1)

            obs, rewards, dones, infos = vec_env.step(np.zeros((2, 1), dtype=np.float32))
            self.assertTrue(np.all(dones == np.asarray([True, True])))
            self.assertTrue(np.allclose(rewards, np.asarray([2.0, 2.0], dtype=np.float32)))
            self.assertTrue(np.allclose(obs["vec"][:, 1], np.asarray([0.0, 0.0], dtype=np.float32)))
            self.assertEqual(infos[0]["terminal_observation"]["vec"][1], 2.0)
            self.assertEqual(infos[1]["terminal_observation"]["vec"][1], 2.0)
        finally:
            vec_env.close()


if __name__ == "__main__":
    unittest.main()
