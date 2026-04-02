from __future__ import annotations

from collections.abc import Generator
from typing import Optional, Union

import numpy as np
import torch as th
from gymnasium import spaces

from stable_baselines3.common.buffers import DictRolloutBuffer, RolloutBuffer
from stable_baselines3.common.type_aliases import DictRolloutBufferSamples
from stable_baselines3.common.vec_env import VecNormalize


def _torch_dtype_from_numpy(dtype_like) -> th.dtype:
    return th.from_numpy(np.zeros((), dtype=np.dtype(dtype_like))).dtype


class DeviceDictRolloutBuffer(DictRolloutBuffer):
    """
    Dict rollout buffer that stores rollout tensors directly on the target torch device.

    This removes the default SB3 cycle of:
    1. device observation/value/logprob -> NumPy in `add()`
    2. NumPy -> device tensor again in `get()`

    The maintained Phase-4 CUDA bridge uses this buffer so rollout collection and
    learner minibatch sampling can stay device-resident.
    """

    store_on_device = True

    @staticmethod
    def _swap_and_flatten_tensor(tensor: th.Tensor) -> th.Tensor:
        shape = tuple(tensor.shape)
        if len(shape) < 3:
            shape = (*shape, 1)
            tensor = tensor.reshape(shape)
        return tensor.swapaxes(0, 1).reshape(shape[0] * shape[1], *shape[2:])

    def reset(self) -> None:
        self.observations = {}
        for key, obs_input_shape in self.obs_shape.items():
            self.observations[key] = th.zeros(
                (self.buffer_size, self.n_envs, *obs_input_shape),
                dtype=_torch_dtype_from_numpy(self.observation_space[key].dtype),
                device=self.device,
            )
        self.actions = th.zeros(
            (self.buffer_size, self.n_envs, self.action_dim),
            dtype=_torch_dtype_from_numpy(self.action_space.dtype),
            device=self.device,
        )
        self.rewards = th.zeros((self.buffer_size, self.n_envs), dtype=th.float32, device=self.device)
        self.returns = th.zeros((self.buffer_size, self.n_envs), dtype=th.float32, device=self.device)
        self.episode_starts = th.zeros((self.buffer_size, self.n_envs), dtype=th.float32, device=self.device)
        self.values = th.zeros((self.buffer_size, self.n_envs), dtype=th.float32, device=self.device)
        self.log_probs = th.zeros((self.buffer_size, self.n_envs), dtype=th.float32, device=self.device)
        self.advantages = th.zeros((self.buffer_size, self.n_envs), dtype=th.float32, device=self.device)
        self.generator_ready = False
        super(RolloutBuffer, self).reset()

    def _obs_to_device_tensor(self, key: str, obs) -> th.Tensor:
        if th.is_tensor(obs):
            obs_tensor = obs.detach()
            if obs_tensor.device != self.device:
                obs_tensor = obs_tensor.to(self.device)
        else:
            obs_tensor = th.as_tensor(obs, device=self.device)
        if isinstance(self.observation_space.spaces[key], spaces.Discrete):
            obs_tensor = obs_tensor.reshape((self.n_envs,) + self.obs_shape[key])
        return obs_tensor

    def add(  # type: ignore[override]
        self,
        obs,
        action,
        reward: np.ndarray,
        episode_start: np.ndarray,
        value: th.Tensor,
        log_prob: th.Tensor,
    ) -> None:
        if len(log_prob.shape) == 0:
            log_prob = log_prob.reshape(-1, 1)

        for key in self.observations.keys():
            obs_tensor = self._obs_to_device_tensor(key, obs[key])
            self.observations[key][self.pos].copy_(obs_tensor)

        if th.is_tensor(action):
            action_tensor = action.detach()
            if action_tensor.device != self.device:
                action_tensor = action_tensor.to(self.device)
        else:
            action_tensor = th.as_tensor(action, device=self.device)
        action_tensor = action_tensor.reshape((self.n_envs, self.action_dim))

        reward_tensor = th.as_tensor(reward, dtype=th.float32, device=self.device)
        episode_start_tensor = th.as_tensor(episode_start, dtype=th.float32, device=self.device)
        value_tensor = value.detach().to(self.device).flatten()
        log_prob_tensor = log_prob.detach().to(self.device).flatten()

        self.actions[self.pos].copy_(action_tensor)
        self.rewards[self.pos].copy_(reward_tensor)
        self.episode_starts[self.pos].copy_(episode_start_tensor)
        self.values[self.pos].copy_(value_tensor)
        self.log_probs[self.pos].copy_(log_prob_tensor)
        self.pos += 1
        if self.pos == self.buffer_size:
            self.full = True

    def compute_returns_and_advantage(self, last_values: th.Tensor, dones: np.ndarray) -> None:
        last_values = last_values.detach().to(self.device).flatten()
        dones_tensor = th.as_tensor(dones, dtype=th.float32, device=self.device)

        last_gae_lam = th.zeros((self.n_envs,), dtype=th.float32, device=self.device)
        for step in reversed(range(self.buffer_size)):
            if step == self.buffer_size - 1:
                next_non_terminal = 1.0 - dones_tensor
                next_values = last_values
            else:
                next_non_terminal = 1.0 - self.episode_starts[step + 1]
                next_values = self.values[step + 1]
            delta = self.rewards[step] + self.gamma * next_values * next_non_terminal - self.values[step]
            last_gae_lam = delta + self.gamma * self.gae_lambda * next_non_terminal * last_gae_lam
            self.advantages[step].copy_(last_gae_lam)
        self.returns = self.advantages + self.values

    def get(  # type: ignore[override]
        self,
        batch_size: Optional[int] = None,
    ) -> Generator[DictRolloutBufferSamples, None, None]:
        assert self.full, ""
        indices = np.random.permutation(self.buffer_size * self.n_envs)
        if not self.generator_ready:
            for key, obs in self.observations.items():
                self.observations[key] = self._swap_and_flatten_tensor(obs)

            for tensor_name in ["actions", "values", "log_probs", "advantages", "returns"]:
                self.__dict__[tensor_name] = self._swap_and_flatten_tensor(self.__dict__[tensor_name])
            self.generator_ready = True

        if batch_size is None:
            batch_size = self.buffer_size * self.n_envs

        start_idx = 0
        while start_idx < self.buffer_size * self.n_envs:
            yield self._get_samples(indices[start_idx : start_idx + batch_size])
            start_idx += batch_size

    def _get_samples(  # type: ignore[override]
        self,
        batch_inds: np.ndarray,
        env: Optional[VecNormalize] = None,
    ) -> DictRolloutBufferSamples:
        del env
        index = th.as_tensor(batch_inds, dtype=th.long, device=self.device)
        return DictRolloutBufferSamples(
            observations={key: obs.index_select(0, index) for (key, obs) in self.observations.items()},
            actions=self.actions.index_select(0, index).to(dtype=th.float32),
            old_values=self.values.index_select(0, index).flatten(),
            old_log_prob=self.log_probs.index_select(0, index).flatten(),
            advantages=self.advantages.index_select(0, index).flatten(),
            returns=self.returns.index_select(0, index).flatten(),
        )
