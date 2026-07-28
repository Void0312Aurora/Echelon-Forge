from __future__ import annotations

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from gym_envs.universal_env_parts import make_action_space
from python.rl.policy_algo.first_event_hazard import FirstEventHazardLabels
from stable_baselines3.common.callbacks import BaseCallback


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


class _TinyHybridAirCombatEnv(gym.Env):
  metadata = {}

  def __init__(self) -> None:
    self.observation_space = spaces.Dict(
      {
        "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=np.float32),
        "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=np.float32),
        "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=np.float32),
        "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(21,), dtype=np.float32),
        "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=np.float32),
      }
    )
    self.action_space = make_action_space("air_combat_hybrid_v1")
    self._steps = 0

  def reset(self, *, seed=None, options=None):
    self._steps = 0
    return self._obs(), {}

  def step(self, action):
    self._steps += 1
    action_arr = np.asarray(action, dtype=np.float32).reshape(-1)
    reward = -float(np.mean(np.square(action_arr[:6])))
    terminated = self._steps >= 1
    truncated = False
    return self._obs(), reward, terminated, truncated, {}

  def _obs(self):
    return {
      "instruments": np.zeros((42,), dtype=np.float32),
      "contacts": np.zeros((10, 5), dtype=np.float32),
      "rwr": np.zeros((4, 4), dtype=np.float32),
      "mission": np.zeros((21,), dtype=np.float32),
      "proprio": np.zeros((12,), dtype=np.float32),
    }


class _TinyA6HybridAirCombatEnv(_TinyHybridAirCombatEnv):
  def step(self, action):
    self._steps += 1
    action_arr = np.asarray(action, dtype=np.float32).reshape(-1)
    reward = -float(np.mean(np.square(action_arr[:6])))
    terminated = False
    truncated = False
    info = {
      "engagement_state": "AuthorizedReady",
      "fire_mask": 1,
      "event_action_mask": [1, 1],
      "fire_once_accepted": False,
    }
    return self._obs(), reward, terminated, truncated, info


class _TinyM3S1HybridAirCombatEnv(_TinyA6HybridAirCombatEnv):
  def _obs(self):
    obs = super()._obs()
    contacts = np.zeros((10, 5), dtype=np.float32)
    if self._steps >= 2:
      contacts[0, 0] = 1000.0
      contacts[0, 4] = 0.1
    obs["contacts"] = contacts
    return obs


class _TinyA7ProjectionHybridAirCombatEnv(gym.Env):
  metadata = {}

  def __init__(self) -> None:
    self.observation_space = spaces.Dict(
      {
        "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=np.float32),
        "contacts": spaces.Box(low=-1.0e6, high=1.0e6, shape=(10, 5), dtype=np.float32),
        "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=np.float32),
        "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=np.float32),
        "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=np.float32),
      }
    )
    self.action_space = make_action_space("air_combat_hybrid_v1")

  def reset(self, *, seed=None, options=None):
    return self._obs(), {}

  def step(self, action):
    return self._obs(), 0.0, False, False, {}

  def _obs(self):
    mission = np.zeros((20,), dtype=np.float32)
    mission[5] = 1.0
    mission[6] = 0.0
    mission[14] = 4.0
    mission[15] = 0.0
    mission[16] = 0.0
    mission[17] = 1.0
    mission[19] = 0.0
    contacts = np.zeros((10, 5), dtype=np.float32)
    contacts[0, 0] = 1.0
    contacts[0, 4] = 0.2
    return {
      "instruments": np.zeros((42,), dtype=np.float32),
      "contacts": contacts,
      "rwr": np.zeros((4, 4), dtype=np.float32),
      "mission": mission,
      "proprio": np.zeros((12,), dtype=np.float32),
    }


class _TinyA7LegalOpenHybridAirCombatEnv(_TinyA7ProjectionHybridAirCombatEnv):
  def _obs(self):
    obs = super()._obs()
    mission = np.array(obs["mission"], copy=True)
    mission[5] = 2.0
    mission[6] = 1.0
    mission[14] = 2.0
    mission[15] = 1.0
    mission[16] = 1.0
    mission[17] = 0.0
    mission[19] = 1.0
    obs["mission"] = mission
    return obs


class _NoopCallback(BaseCallback):
  def _on_step(self) -> bool:
    return True


def _grad_norm(params) -> float:
  total = 0.0
  for param in params:
    if param.grad is not None:
      total += float(param.grad.detach().pow(2).sum().cpu().item())
  return total**0.5


class _FirstEventLabelBuffer:
  supports_first_event_labels = True

  def __init__(self, buffer_size: int, n_envs: int = 1) -> None:
    self.buffer_size = int(buffer_size)
    self.n_envs = int(n_envs)
    self.labels: FirstEventHazardLabels | None = None

  def set_first_event_labels(self, labels: FirstEventHazardLabels) -> None:
    self.labels = labels
