from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .adapter import RuntimeFacadeAdapter


class RuntimeCompatibilityView:
    """Compatibility-only view for callers that still expect `vec_env.batch_runtime`."""

    def __init__(self, adapter: RuntimeFacadeAdapter):
        self._adapter = adapter

    def __getattr__(self, name: str) -> Any:
        return getattr(self._adapter, name)

    def world_count(self) -> int:
        return self._adapter.world_count()

    def worker_threads(self) -> int:
        return self._adapter.worker_threads()

    def effective_worker_threads(self) -> int:
        return self._adapter.effective_worker_threads()

    def get_agent_observations_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self._adapter.get_agent_observations_batch(refs)

    def get_instrument_states_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self._adapter.get_instrument_states_batch(refs)

    def set_pilot_actions_batch(self, assignments: Sequence[Any]) -> None:
        self._adapter.set_pilot_actions_batch(assignments)

    def step_worlds(self, world_indices: Sequence[int]) -> None:
        self._adapter.step_worlds(world_indices)

    def export_execution_episode_states_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self._adapter.export_execution_episode_states_batch(refs)

    def execution_episode_controller_ready(self, world_index: int) -> bool:
        return self._adapter.execution_episode_controller_ready(world_index)


__all__ = ["RuntimeCompatibilityView"]
