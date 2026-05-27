from __future__ import annotations

import unittest
from collections import deque

import gymnasium as gym
import numpy as np
import torch as th
from gymnasium import spaces

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.rl.policy_algo.policies import HierarchicalMoEExecutionPolicy, SquashedMultiInputPolicy
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import configure
from stable_baselines3.common.vec_env import DummyVecEnv


class _WarmupSchedule:
    def __call__(self, progress_remaining: float) -> float:
        return 3.0e-4


class _TinyHMoEEnv(gym.Env):
    metadata = {}

    def __init__(self) -> None:
        self.observation_space = spaces.Dict(
            {
                "image": spaces.Box(low=0.0, high=1.0, shape=(1, 8, 8), dtype=np.float32),
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(26,), dtype=np.float32),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(21,), dtype=np.float32),
                "prev_action": spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=np.float32),
            }
        )
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=np.float32)
        self._steps = 0

    def reset(self, *, seed=None, options=None):
        self._steps = 0
        return self._obs(), {}

    def step(self, action):
        self._steps += 1
        terminated = self._steps >= 1
        truncated = False
        return self._obs(), 0.0, terminated, truncated, {}

    def _obs(self):
        return {
            "image": np.zeros((1, 8, 8), dtype=np.float32),
            "instruments": np.zeros((26,), dtype=np.float32),
            "mission": np.zeros((21,), dtype=np.float32),
            "prev_action": np.zeros((17,), dtype=np.float32),
        }


class _TinyHoldEnv(gym.Env):
    metadata = {}

    def __init__(self) -> None:
        self.observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32),
                "mission": spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32),
            }
        )
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
        self._steps = 0

    def reset(self, *, seed=None, options=None):
        self._steps = 0
        return self._obs(), {}

    def step(self, action):
        self._steps += 1
        reward = -float(np.mean(np.square(np.asarray(action, dtype=np.float32))))
        terminated = self._steps >= 1
        truncated = False
        return self._obs(), reward, terminated, truncated, {}

    def _obs(self):
        return {
            "instruments": np.zeros((4,), dtype=np.float32),
            "mission": np.zeros((3,), dtype=np.float32),
        }


class _NoopCallback(BaseCallback):
    def _on_step(self) -> bool:
        return True


class HMoEPPOWarmupTests(unittest.TestCase):
    def test_collect_rollouts_applies_hmoe_warmup_before_first_step(self) -> None:
        env = DummyVecEnv([_TinyHMoEEnv])
        model = AdaptiveKLPPO(
            HierarchicalMoEExecutionPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=2,
            batch_size=2,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            policy_kwargs={
                "net_arch": {"pi": [32], "vf": [32]},
                "hmoe_residual_warmup_fraction": 0.3,
                "hmoe_residual_start_factor": 0.0,
            },
        )
        model._last_obs = env.reset()
        model._last_episode_starts = np.ones((env.num_envs,), dtype=bool)
        model.ep_info_buffer = deque(maxlen=model._stats_window_size)
        model.ep_success_buffer = deque(maxlen=model._stats_window_size)

        recorded: list[float] = []
        original_forward = model.policy.forward

        def wrapped_forward(obs, deterministic: bool = False):
            recorded.append(float(model.policy._hmoe_residual_gate))
            return original_forward(obs, deterministic=deterministic)

        model.policy.forward = wrapped_forward  # type: ignore[method-assign]
        callback = _NoopCallback()
        callback.init_callback(model)

        ok = model.collect_rollouts(
            env,
            callback,
            model.rollout_buffer,
            n_rollout_steps=model.n_steps,
        )

        self.assertTrue(ok)
        self.assertTrue(recorded)
        self.assertAlmostEqual(recorded[0], 0.0, places=6)

    def test_action_mean_regularization_pulls_deterministic_action_toward_target(self) -> None:
        env = DummyVecEnv([_TinyHoldEnv])
        model = AdaptiveKLPPO(
            SquashedMultiInputPolicy,
            env,
            learning_rate=_WarmupSchedule(),
            n_steps=2,
            batch_size=2,
            n_epochs=1,
            gamma=0.99,
            gae_lambda=0.95,
            normalize_advantage=False,
            action_mean_regularization_coef=5.0,
            action_mean_regularization_target=[0.0, 0.0, 0.0],
            policy_kwargs={
                "net_arch": {"pi": [16], "vf": [16]},
            },
        )
        model.set_logger(configure(format_strings=[]))
        model._last_obs = env.reset()
        model._last_episode_starts = np.ones((env.num_envs,), dtype=bool)
        model.ep_info_buffer = deque(maxlen=model._stats_window_size)
        model.ep_success_buffer = deque(maxlen=model._stats_window_size)
        with th.no_grad():
            model.policy.action_net.weight.zero_()
            model.policy.action_net.bias.fill_(0.5)

        obs = env.reset()
        before, _ = model.predict(obs, deterministic=True)
        before_abs = float(np.mean(np.abs(before)))

        callback = _NoopCallback()
        callback.init_callback(model)
        ok = model.collect_rollouts(
            env,
            callback,
            model.rollout_buffer,
            n_rollout_steps=model.n_steps,
        )
        self.assertTrue(ok)
        model.train()

        after, _ = model.predict(obs, deterministic=True)
        after_abs = float(np.mean(np.abs(after)))

        self.assertLess(after_abs, before_abs)


if __name__ == "__main__":
    unittest.main()
