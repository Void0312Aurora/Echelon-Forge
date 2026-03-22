from __future__ import annotations

import numpy as np
import torch

import gymnasium as gym
from gymnasium import spaces


class CounterDictEnv(gym.Env):
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


class DummyFrozenPolicy:
    def __init__(self):
        self.calls = 0

    def predict(self, obs, deterministic=True):
        _ = (obs, deterministic)
        self.calls += 1
        value = float(self.calls)
        return np.asarray([value, -value], dtype=np.float32), None


class DirectPredictPolicy:
    def __init__(self):
        self.training_modes: list[bool] = []
        self.obs_calls = 0
        self.predict_calls = 0
        self.squash_output = False

    def set_training_mode(self, mode: bool) -> None:
        self.training_modes.append(bool(mode))

    def obs_to_tensor(self, obs):
        self.obs_calls += 1
        return {"vec": torch.as_tensor(obs["vec"], dtype=torch.float32).reshape(1, -1)}, None

    def _predict(self, obs_tensor, deterministic: bool = True):
        _ = (obs_tensor, deterministic)
        self.predict_calls += 1
        return torch.as_tensor([[0.25, -0.5]], dtype=torch.float32)


class DirectPredictModel:
    def __init__(self):
        self.policy = DirectPredictPolicy()
        self.reset_calls = 0

    def reset(self, obs) -> None:
        _ = obs
        self.reset_calls += 1


class FakeExecutionRuntime:
    def __init__(self):
        self.policy_env = object()
        self.unwrapped = object()
        self.last_overrides = None

    def reset(self, *, seed=None):
        _ = seed
        raise AssertionError("reset should not be called in this constructor wiring test")

    def step(self, action):
        raise AssertionError(f"step should not be called in this constructor wiring test: {action!r}")

    def set_randomization_overrides(self, overrides):
        self.last_overrides = overrides


class FakePreparedExecutionRuntime:
    def __init__(self):
        self.prepare_calls = 0
        self.finalize_calls = 0

    def prepare_action(self, action):
        self.prepare_calls += 1
        arr = np.asarray(action, dtype=np.float32).reshape(-1)
        return arr + 1.0, {"prepared": True}

    def finalize_step_result(self, obs, reward, info, prepared_action_state=None):
        self.finalize_calls += 1
        info_out = dict(info or {})
        info_out["prepared_action_state"] = prepared_action_state
        return obs, float(reward) + 2.0, info_out


class CountingWindowRuntime:
    def __init__(self, *, terminate_after: int = 2):
        self.terminate_after = max(1, int(terminate_after))
        self.step_calls = 0

    def step(self, action):
        _ = np.asarray(action, dtype=np.float32).reshape(-1)
        self.step_calls += 1
        idx = self.step_calls
        return (
            {"vec": np.asarray([float(idx)], dtype=np.float32)},
            float(idx),
            idx >= self.terminate_after,
            False,
            {"runtime_step": idx},
        )

    def finalize_step_result(self, obs, reward, info, prepared_action_state=None):
        _ = prepared_action_state
        info_out = dict(info or {})
        info_out["finalized"] = True
        return obs, float(reward) + 0.5, info_out


class FakeLeaderWindowRuntime:
    def __init__(self):
        self.run_calls: list[np.ndarray] = []

    def run_step(self, action):
        arr = np.asarray(action, dtype=np.float32).reshape(-1)
        self.run_calls.append(arr)
        return {"task": np.asarray([1.0], dtype=np.float32)}, 7.0, True, False, {"runtime": "leader_window"}


class PendingLeaderState:
    def __init__(self):
        self.exec_reward = 0.0
        self.terminated = False
        self.truncated = False
        self.last_info = {}
        self.decision_c2_transitioned = False
        self.decision_c2_transition_reason = ""
        self.execution_step_count = 0
        self.timing = {}
