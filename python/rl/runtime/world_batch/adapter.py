from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import ef_py

from gym_envs.scenario_loader import ScenarioLoader

from python.scenario_runtime import apply_world_layout_to_kernel


@dataclass
class _ObservationPacketCompat:
    refs: list[Any]
    agent_observations: list[Any]
    instrument_states: list[Any]
    mission_commands: list[Any]
    task_orders: list[Any]
    leader_intents: list[Any]
    pilot_reports: list[Any]


class RuntimeFacadeAdapter:
    """Centralized compatibility adapter for facade-shaped runtime access."""

    def __init__(self, world_count: int):
        self.facade = ef_py.RuntimeFacade(int(world_count)) if hasattr(ef_py, "RuntimeFacade") else None
        self._compat_runtime = self.facade.runtime() if self.facade is not None else ef_py.WorldBatchRuntime(int(world_count))

    def world_count(self) -> int:
        target = self.facade if self.facade is not None else self._compat_runtime
        return int(target.world_count())

    def set_worker_threads(self, worker_threads: int) -> None:
        target = self.facade if self.facade is not None else self._compat_runtime
        target.set_worker_threads(int(worker_threads))

    def worker_threads(self) -> int:
        target = self.facade if self.facade is not None else self._compat_runtime
        return int(target.worker_threads())

    def effective_worker_threads(self) -> int:
        target = self.facade if self.facade is not None else self._compat_runtime
        return int(target.effective_worker_threads())

    def load_database(self, path: str) -> bool:
        target = self.facade if self.facade is not None else self._compat_runtime
        return bool(target.load_database(path))

    def world(self, index: int):
        return self._compat_runtime.world(int(index))

    def apply_world_layout(self, world_index: int, layout: Any):
        return apply_world_layout_to_kernel(self.world(int(world_index)), layout)

    def make_scenario_loader(self, index: int) -> ScenarioLoader:
        return ScenarioLoader(self.world(int(index)))

    def get_time_step(self, world_index: int) -> float:
        return float(self.world(int(world_index)).get_time_step())

    def get_visual_observation(self, world_index: int, entity_id: int) -> Any:
        return self.world(int(world_index)).get_visual_observation(int(entity_id))

    def get_visual_observation_downsampled(
        self,
        world_index: int,
        entity_id: int,
        downsample: int,
    ) -> Any:
        return self.world(int(world_index)).get_visual_observation_downsampled(
            int(entity_id),
            int(downsample),
        )

    def supports_visual_observation_downsampled(self, world_index: int) -> bool:
        return hasattr(self.world(int(world_index)), "get_visual_observation_downsampled")

    def compute_visual_observation_batch_numpy(
        self,
        refs: Sequence[Any],
        downsample: int,
        use_gpu_host: bool,
    ) -> Any:
        return ef_py.compute_world_batch_visual_observation_batch_numpy(
            self._compat_runtime,
            list(refs),
            int(downsample),
            bool(use_gpu_host),
        )

    def compute_visual_observation_batch_export(
        self,
        refs: Sequence[Any],
        downsample: int,
        prefer_device_view: bool,
    ) -> Any:
        return ef_py.compute_world_batch_visual_observation_batch_export(
            self._compat_runtime,
            list(refs),
            int(downsample),
            bool(prefer_device_view),
        )

    def apply_world_setup(self, request: Any):
        if self.facade is not None and hasattr(self.facade, "apply_world_setup"):
            return self.facade.apply_world_setup(request)
        result = ef_py.BatchWorldSetupResult() if hasattr(ef_py, "BatchWorldSetupResult") else None
        entity_ids = self._compat_runtime.apply_world_setup_batch(
            list(request.seeds),
            list(request.terrain_assignments),
            list(request.wind_assignments),
            list(request.zones),
            list(request.spawn_requests),
            list(request.time_steps),
        )
        if result is None:
            return entity_ids
        result.entity_ids = list(entity_ids)
        return result

    def apply_world_setup_batch(
        self,
        seeds: Sequence[int],
        terrain_assignments: Sequence[Any],
        wind_assignments: Sequence[Any],
        zones: Sequence[Any],
        requests: Sequence[Any],
        time_steps: Sequence[float] | None = None,
    ) -> list[int]:
        if hasattr(ef_py, "BatchWorldSetupRequest"):
            request = ef_py.BatchWorldSetupRequest()
            request.seeds = [int(seed) & 0xFFFFFFFF for seed in seeds]
            request.terrain_assignments = list(terrain_assignments)
            request.wind_assignments = list(wind_assignments)
            request.zones = list(zones)
            request.spawn_requests = list(requests)
            request.time_steps = [] if time_steps is None else [float(value) for value in time_steps]
            result = self.apply_world_setup(request)
            if hasattr(result, "entity_ids"):
                return [int(entity_id) for entity_id in list(result.entity_ids)]
            return [int(entity_id) for entity_id in list(result)]
        return [
            int(entity_id)
            for entity_id in self._compat_runtime.apply_world_setup_batch(
                list(seeds),
                list(terrain_assignments),
                list(wind_assignments),
                list(zones),
                list(requests),
                [] if time_steps is None else list(time_steps),
            )
        ]

    def export_observation_packet(self, request_or_refs: Any) -> Any:
        if self.facade is not None and hasattr(self.facade, "export_observation_packet"):
            return self.facade.export_observation_packet(request_or_refs)
        refs = (
            list(getattr(request_or_refs, "refs", []) or [])
            if hasattr(request_or_refs, "refs")
            else list(request_or_refs)
        )
        request = request_or_refs if hasattr(request_or_refs, "refs") else None
        include_agent_observations = bool(
            True if request is None else getattr(request, "include_agent_observations", True)
        )
        include_instrument_states = bool(
            True if request is None else getattr(request, "include_instrument_states", True)
        )
        include_mission_commands = bool(
            False if request is None else getattr(request, "include_mission_commands", False)
        )
        return _ObservationPacketCompat(
            refs=refs,
            agent_observations=(
                list(self._compat_runtime.get_agent_observations_batch(refs))
                if include_agent_observations
                else []
            ),
            instrument_states=(
                list(self._compat_runtime.get_instrument_states_batch(refs))
                if include_instrument_states
                else []
            ),
            mission_commands=(
                list(self.get_mission_commands_batch(refs))
                if include_mission_commands
                else []
            ),
            task_orders=[],
            leader_intents=[],
            pilot_reports=[],
        )

    def read_truth_and_instruments(self, refs: Sequence[Any]) -> tuple[list[Any], list[Any]]:
        refs_list = list(refs)
        if self.facade is not None and hasattr(ef_py, "ObservationBatchRequest"):
            request = ef_py.ObservationBatchRequest()
            request.refs = refs_list
            request.include_agent_observations = True
            request.include_instrument_states = True
            request.include_mission_commands = False
            request.include_task_orders = False
            request.include_leader_intents = False
            request.include_pilot_reports = False
            packet = self.facade.export_observation_packet(request)
            return list(packet.agent_observations), list(packet.instrument_states)
        if self.facade is not None:
            return (
                list(self.facade.get_agent_observations_batch(refs_list)),
                list(self.facade.get_instrument_states_batch(refs_list)),
            )
        return (
            list(self._compat_runtime.get_agent_observations_batch(refs_list)),
            list(self._compat_runtime.get_instrument_states_batch(refs_list)),
        )

    def get_instrument_states_batch(self, refs: Sequence[Any]) -> list[Any]:
        _truth, inst = self.read_truth_and_instruments(refs)
        return inst

    def get_agent_observations_batch(self, refs: Sequence[Any]) -> list[Any]:
        truth, _inst = self.read_truth_and_instruments(refs)
        return truth

    def get_mission_commands_batch(self, refs: Sequence[Any]) -> list[Any]:
        target = self.facade if self.facade is not None else self._compat_runtime
        return list(target.get_mission_commands_batch(list(refs)))

    def set_pilot_actions_batch(self, assignments: Sequence[Any]) -> None:
        target = self.facade if self.facade is not None else self._compat_runtime
        target.set_pilot_actions_batch(list(assignments))

    def step_batch(self) -> None:
        target = self.facade if self.facade is not None else self._compat_runtime
        target.step_batch()

    def prime_execution_episode_batch(self, refs: Sequence[Any], states: Sequence[Any]) -> None:
        if self.facade is not None:
            self.facade.prime_execution_episode_batch(list(refs), list(states))
            return
        self._compat_runtime.prime_execution_episode_controller_batch(list(refs), list(states))

    def execution_episode_ready(self, world_index: int) -> bool:
        if self.facade is not None:
            return bool(self.facade.execution_episode_ready(int(world_index)))
        return bool(self._compat_runtime.execution_episode_controller_ready(int(world_index)))

    def execution_episode_controller_ready(self, world_index: int) -> bool:
        return self.execution_episode_ready(int(world_index))

    def step_execution_batch(self, request: Any) -> Any:
        if self.facade is not None:
            return self.facade.step_execution_batch(request)
        result = ef_py.ExecutionBatchStepResult()
        step_results = list(self._compat_runtime.step_execution_episode_results_batch(list(request.step_requests)))
        result.step_results = step_results
        result.rewards = [float(getattr(step_result, "reward_total", 0.0)) for step_result in step_results]
        result.terminated = [bool(getattr(step_result, "terminated", False)) for step_result in step_results]
        result.truncated = [bool(getattr(step_result, "truncated", False)) for step_result in step_results]
        result.status_vectors = [
            [
                float(getattr(step_result, "status0", 0.0)),
                float(getattr(step_result, "status1", 0.0)),
                float(getattr(step_result, "status2", 0.0)),
                float(getattr(step_result, "status3", 0.0)),
            ]
            for step_result in step_results
        ]
        result.termination_reasons = [
            str(getattr(getattr(step_result, "controller_state", None), "last_termination_reason", "") or "")
            for step_result in step_results
        ]
        result.reward_breakdown_jsons = [
            str(getattr(getattr(step_result, "controller_state", None), "last_reward_breakdown_json", "") or "")
            for step_result in step_results
        ]
        result.controller_state_changed_flags = [
            bool(getattr(step_result, "structural_state_changed", False))
            for step_result in step_results
        ]
        return result

    def step_execution_products_batch(self, requests: Sequence[Any]) -> list[Any]:
        if self.facade is not None:
            return list(self.facade.step_execution_products_batch(list(requests)))
        return list(self._compat_runtime.step_execution_episode_batch(list(requests)))

    def export_execution_episode_states(self, refs: Sequence[Any]) -> list[Any]:
        if self.facade is not None:
            return list(self.facade.export_execution_episode_states(list(refs)))
        return list(self._compat_runtime.export_execution_episode_states_batch(list(refs)))

    def export_execution_episode_states_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self.export_execution_episode_states(refs)

    def step_worlds(self, world_indices: Sequence[int]) -> None:
        self._compat_runtime.step_worlds([int(index) for index in world_indices])

    def set_mission_commands_batch(self, assignments: Sequence[Any]) -> None:
        target = self.facade if self.facade is not None else self._compat_runtime
        target.set_mission_commands_batch(list(assignments))

    def set_task_orders_batch(self, assignments: Sequence[Any]) -> None:
        target = self.facade if self.facade is not None else self._compat_runtime
        target.set_task_orders_batch(list(assignments))

    def set_leader_intents_batch(self, assignments: Sequence[Any]) -> None:
        target = self.facade if self.facade is not None else self._compat_runtime
        target.set_leader_intents_batch(list(assignments))

    def set_pilot_reports_batch(self, assignments: Sequence[Any]) -> None:
        target = self.facade if self.facade is not None else self._compat_runtime
        target.set_pilot_reports_batch(list(assignments))


__all__ = ["RuntimeFacadeAdapter"]
