from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
from typing import Any, TypeAlias

import gymnasium as gym
import numpy as np

try:
    from stable_baselines3.common.vec_env.base_vec_env import VecEnv, VecEnvIndices, VecEnvObs, VecEnvStepReturn
    from stable_baselines3.common.vec_env.util import dict_to_obs, obs_space_info
except Exception:
    VecEnvObs: TypeAlias = Any
    VecEnvIndices: TypeAlias = int | Iterable[int] | None
    VecEnvStepReturn: TypeAlias = tuple[VecEnvObs, np.ndarray, np.ndarray, list[dict[str, Any]]]

    def obs_space_info(observation_space: gym.Space) -> tuple[list[Any], dict[Any, tuple[int, ...]], dict[Any, Any]]:
        if isinstance(observation_space, gym.spaces.Dict):
            subspaces = observation_space.spaces
            keys = list(subspaces.keys())
            shapes = {key: tuple(space.shape or ()) for key, space in subspaces.items()}
            dtypes = {key: space.dtype for key, space in subspaces.items()}
            return keys, shapes, dtypes
        if isinstance(observation_space, gym.spaces.Tuple):
            keys = list(range(len(observation_space.spaces)))
            shapes = {idx: tuple(space.shape or ()) for idx, space in enumerate(observation_space.spaces)}
            dtypes = {idx: space.dtype for idx, space in enumerate(observation_space.spaces)}
            return keys, shapes, dtypes
        return [None], {None: tuple(observation_space.shape or ())}, {None: observation_space.dtype}

    def dict_to_obs(observation_space: gym.Space, obs_dict: OrderedDict[Any, np.ndarray]) -> VecEnvObs:
        if isinstance(observation_space, gym.spaces.Dict):
            return dict(obs_dict)
        if isinstance(observation_space, gym.spaces.Tuple):
            return tuple(obs_dict[idx] for idx in range(len(observation_space.spaces)))
        return obs_dict[None]

    class VecEnv:
        metadata: dict[str, Any] = {"render_modes": []}

        def __init__(self, num_envs: int, observation_space: gym.Space, action_space: gym.Space):
            self.num_envs = int(num_envs)
            self.observation_space = observation_space
            self.action_space = action_space
            self.reset_infos: list[dict[str, Any]] = [{} for _ in range(self.num_envs)]
            self._seeds: list[int | None] = [None for _ in range(self.num_envs)]
            self._options: list[dict[str, Any]] = [{} for _ in range(self.num_envs)]
            self.render_mode = None

        def step(self, actions: np.ndarray) -> VecEnvStepReturn:
            self.step_async(actions)
            return self.step_wait()

        def seed(self, seed: int | None = None) -> list[int]:
            base_seed = int(seed) if seed is not None else int(np.random.randint(0, 2**31 - 1))
            self._seeds = [base_seed + env_idx for env_idx in range(self.num_envs)]
            return list(self._seeds)

        def set_options(self, options: dict[str, Any] | list[dict[str, Any]] | None = None) -> None:
            if options is None:
                self._options = [{} for _ in range(self.num_envs)]
                return
            if isinstance(options, list):
                if len(options) != self.num_envs:
                    raise ValueError("options list length must match num_envs")
                self._options = [dict(opt or {}) for opt in options]
                return
            self._options = [dict(options) for _ in range(self.num_envs)]

        def _get_indices(self, indices: VecEnvIndices) -> list[int]:
            if indices is None:
                return list(range(self.num_envs))
            if isinstance(indices, (int, np.integer)):
                return [int(indices)]
            return [int(idx) for idx in indices]

        def _reset_seeds(self) -> None:
            self._seeds = [None for _ in range(self.num_envs)]

        def _reset_options(self) -> None:
            self._options = [{} for _ in range(self.num_envs)]
