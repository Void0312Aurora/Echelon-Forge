from __future__ import annotations

from collections.abc import Sequence
from typing import Any


class WorldBatchVecEnvAccess:
    """Controlled access surface for thin runtime wrappers around WorldBatchVecEnv."""

    def __init__(self, world_vec: Any):
        self._world_vec = world_vec

    def state(self, env_idx: int) -> Any:
        return self._world_vec._handles[int(env_idx)]

    def loader(self, env_idx: int) -> Any:
        return self.state(env_idx).loader

    def sim(self, env_idx: int) -> Any:
        return self.loader(env_idx).sim

    def agent_id(self, env_idx: int) -> int | None:
        return self.state(env_idx).agent_id

    def steps(self, env_idx: int) -> int:
        return int(self.state(env_idx).steps)

    def max_steps(self, env_idx: int) -> int:
        return int(self.state(env_idx).max_steps)

    def last_state(self, env_idx: int) -> tuple[Any, Any]:
        state = self.state(env_idx)
        return state.last_inst, state.last_truth

    def set_randomization_overrides(self, env_idx: int, overrides: dict | None) -> None:
        self.state(env_idx).set_randomization_overrides(overrides)

    def sync_command_chain(self, env_indices: Sequence[int] | None = None) -> None:
        if env_indices is None:
            self._world_vec._sync_command_chain_batch()
            return
        self._world_vec._sync_command_chain_batch([int(env_idx) for env_idx in env_indices])

    def build_refs(self, env_indices: Sequence[int] | None = None):
        return self._world_vec._build_refs(env_indices)

    def get_instrument_states_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self._world_vec._get_instrument_states_batch(refs)

    def get_agent_observations_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self._world_vec._get_agent_observations_batch(refs)

    def set_pilot_actions_batch(self, assignments: Sequence[Any]) -> None:
        self._world_vec._set_pilot_actions_batch(assignments)

    def step_worlds(self, world_indices: Sequence[int]) -> None:
        self._world_vec._step_runtime_worlds(world_indices)

    def world_time_step(self, env_idx: int) -> float:
        return self._world_vec._world_time_step(int(env_idx))

    def build_observation_from_cached_state(self, env_idx: int):
        return self._world_vec._build_observation_from_cached_state(int(env_idx))

    def normalize_seed(self, seed: int | None) -> int:
        return self._world_vec._normalize_seed(seed)

    def reset_single_world(self, env_idx: int, *, seed: int | None = None):
        return self._world_vec._reset_single_world(int(env_idx), seed=seed)

    @property
    def action_space(self):
        return self._world_vec.action_space

    @property
    def observation_space(self):
        return self._world_vec.observation_space

    @property
    def action_mode(self) -> str:
        return str(self._world_vec.action_mode)

    @property
    def collect_step_timing(self) -> bool:
        return bool(getattr(self._world_vec, "collect_step_timing", False))

    @property
    def reset_infos(self):
        return self._world_vec.reset_infos

    @property
    def last_step_timing(self):
        return self._world_vec.last_step_timing

    @last_step_timing.setter
    def last_step_timing(self, value: Any) -> None:
        self._world_vec.last_step_timing = value

    @property
    def num_envs(self) -> int:
        return int(self._world_vec.num_envs)

    @property
    def seeds(self) -> list[int]:
        return list(self._world_vec._seeds)

    @seeds.setter
    def seeds(self, values: Sequence[int]) -> None:
        self._world_vec._seeds = [int(value) for value in values]

    def reset(self):
        return self._world_vec.reset()

    @property
    def last_runtime_window_evidence(self):
        return getattr(self._world_vec._runtime_adapter, "last_window_evidence", None)

    def clear_runtime_window_evidence(self) -> None:
        clear = getattr(self._world_vec._runtime_adapter, "clear_last_window_evidence", None)
        if callable(clear):
            clear()

    def supports_runtime_window_api(self) -> bool:
        supports = getattr(self._world_vec._runtime_adapter, "supports_runtime_window_api", None)
        return bool(supports()) if callable(supports) else False

    def run_maintained_window(self, **kwargs):
        return self._world_vec._runtime_adapter.run_maintained_window(**kwargs)


__all__ = ["WorldBatchVecEnvAccess"]
