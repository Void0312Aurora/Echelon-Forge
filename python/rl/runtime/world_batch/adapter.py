from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import ef_py

from gym_envs.scenario_loader import ScenarioLoader

from python.scenario_runtime import apply_world_layout_to_kernel
from python.scenario_runtime import apply_world_setup_payload_compat
from python.scenario_runtime import build_batch_world_setup_request
from python.scenario_runtime import extract_batch_world_setup_entity_ids


@dataclass
class _ObservationPacketCompat:
    refs: list[Any]
    agent_observations: list[Any]
    instrument_states: list[Any]
    mission_commands: list[Any]
    task_orders: list[Any]
    leader_intents: list[Any]
    pilot_reports: list[Any]


@dataclass
class RuntimeWindowEvidence:
    """Consumer-facing view of the selected facade window evidence slice."""

    window_result: Any
    barrier_trace: list[Any]
    visibility_trace: list[Any]
    executed_nodes: list[Any]
    injected_inputs: list[Any]
    observation_packet: Any
    engagement_packet: Any
    diagnostics_traces: list[Any]
    cadence_reason: str
    uses_compat_fallback: bool = False


class RuntimeFacadeAdapter:
    """Centralized compatibility adapter for facade-shaped runtime access."""

    def __init__(self, world_count: int):
        self.facade = ef_py.RuntimeFacade(int(world_count)) if hasattr(ef_py, "RuntimeFacade") else None
        self._compat_runtime = self.facade.runtime() if self.facade is not None else ef_py.WorldBatchRuntime(int(world_count))
        self._last_window_evidence: RuntimeWindowEvidence | None = None

    def _batch_target(self):
        return self.facade if self.facade is not None else self._compat_runtime

    @property
    def last_window_evidence(self) -> RuntimeWindowEvidence | None:
        return self._last_window_evidence

    def clear_last_window_evidence(self) -> None:
        self._last_window_evidence = None

    def supports_runtime_window_api(self) -> bool:
        return bool(
            self.facade is not None
            and hasattr(self.facade, "run_wp10_window")
            and hasattr(ef_py, "RuntimeWindowRequest")
            and hasattr(ef_py, "RuntimeWindowActionRequest")
        )

    def _store_window_evidence(
        self,
        result: Any,
        *,
        cadence_reason: str,
        uses_compat_fallback: bool,
    ) -> RuntimeWindowEvidence:
        evidence = RuntimeWindowEvidence(
            window_result=result,
            barrier_trace=list(getattr(result, "barrier_trace", []) or []),
            visibility_trace=list(getattr(result, "visibility_trace", []) or []),
            executed_nodes=list(getattr(result, "executed_nodes", []) or []),
            injected_inputs=list(getattr(result, "injected_inputs", []) or []),
            observation_packet=getattr(result, "observation_packet", None),
            engagement_packet=getattr(result, "engagement_packet", None),
            diagnostics_traces=list(getattr(result, "diagnostics_traces", []) or []),
            cadence_reason=str(cadence_reason),
            uses_compat_fallback=bool(uses_compat_fallback),
        )
        self._last_window_evidence = evidence
        return evidence

    def run_maintained_window(
        self,
        *,
        world_index: int,
        entity_id: int,
        pilot_action: Any | None = None,
        mission_command: Any | None = None,
        source_time_s: float | None = None,
        window_id: str | None = None,
        input_snapshot_version: str | None = None,
        source_layer: str = "training_policy",
        include_engagement: bool = True,
        include_diagnostics: bool = True,
    ) -> RuntimeWindowEvidence | None:
        if not self.supports_runtime_window_api():
            self._last_window_evidence = None
            return None

        request = ef_py.RuntimeWindowRequest()
        request.window_id = (
            str(window_id)
            if window_id is not None and str(window_id).strip()
            else f"window:facade_batch:{int(world_index)}:{int(entity_id)}"
        )
        request.world_id = int(world_index)
        request.source_time_s = float(0.0 if source_time_s is None else source_time_s)

        observation_request = ef_py.ObservationBatchRequest()
        observation_ref = ef_py.WorldEntityRef()
        observation_ref.world_index = int(world_index)
        observation_ref.entity_id = int(entity_id)
        observation_request.refs = [observation_ref]
        observation_request.include_agent_observations = True
        observation_request.include_instrument_states = True
        observation_request.include_mission_commands = False
        observation_request.include_task_orders = False
        observation_request.include_leader_intents = False
        observation_request.include_pilot_reports = False
        request.observation_request = observation_request

        engagement_request = ef_py.EngagementBatchRequest()
        engagement_ref = ef_py.EngagementEntityRef()
        engagement_ref.world_index = int(world_index)
        engagement_ref.entity_id = int(entity_id)
        engagement_request.refs = [engagement_ref]
        engagement_request.trace_ids = [1]
        request.engagement_request = engagement_request
        request.export_observation = True
        request.export_engagement = bool(include_engagement)
        request.export_diagnostics = bool(include_diagnostics)

        if pilot_action is not None or mission_command is not None:
            action_request = ef_py.RuntimeWindowActionRequest()
            action_request.source_layer = str(source_layer)
            action_request.input_snapshot_version = str(
                input_snapshot_version
                if input_snapshot_version is not None and str(input_snapshot_version).strip()
                else f"obs:{int(world_index)}:{int(entity_id)}"
            )
            action_request.action_intent.source_id = (
                f"{action_request.source_layer}:{int(world_index)}:{int(entity_id)}"
            )
            action_request.action_intent.effective_time_s = request.source_time_s
            action_request.action_intent.valid_until_s = request.source_time_s + 1.0
            action_request.action_intent.target.world_index = int(world_index)
            action_request.action_intent.target.entity_id = int(entity_id)
            action_request.action_intent.action_family = "direct_control"
            action_request.action_intent.merge_policy = "last_write_wins"
            action_request.action_intent.action_interface.kind = "PilotActionAssignmentCompat"
            action_request.action_intent.action_interface.payload_type = "pilot_action"
            action_request.cadence_control.enabled = True
            action_request.cadence_control.hold_policy.hold_mode = "hold_last"
            action_request.cadence_control.hold_policy.validity_duration_s = 0.1
            action_request.cadence_control.source_cadence_domain = "control"
            action_request.cadence_control.source_tick = 0
            if pilot_action is not None:
                action_request.action_intent.has_pilot_action = True
                action_request.action_intent.pilot_action = pilot_action
            if mission_command is not None:
                action_request.action_intent.has_mission_command = True
                action_request.action_intent.mission_command = mission_command
            request.action_requests = [action_request]

        result = self.facade.run_wp10_window(request)
        return self._store_window_evidence(
            result,
            cadence_reason="selected_slice_cadence_trace_runtime_window_wp17c",
            uses_compat_fallback=False,
        )

    def world_count(self) -> int:
        return int(self._batch_target().world_count())

    def set_worker_threads(self, worker_threads: int) -> None:
        self._batch_target().set_worker_threads(int(worker_threads))

    def worker_threads(self) -> int:
        return int(self._batch_target().worker_threads())

    def effective_worker_threads(self) -> int:
        return int(self._batch_target().effective_worker_threads())

    def load_database(self, path: str) -> bool:
        return bool(self._batch_target().load_database(path))

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
        entity_ids = apply_world_setup_payload_compat(
            self._batch_target(),
            seeds=list(request.seeds),
            terrain_assignments=list(request.terrain_assignments),
            wind_assignments=list(request.wind_assignments),
            zones=list(request.zones),
            spawn_requests=list(request.spawn_requests),
            time_steps=list(request.time_steps),
        )
        result = ef_py.BatchWorldSetupResult() if hasattr(ef_py, "BatchWorldSetupResult") else None
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
        normalized_time_steps = [] if time_steps is None else [float(value) for value in time_steps]
        request = build_batch_world_setup_request(
            seeds=[int(seed) for seed in seeds],
            terrain_assignments=list(terrain_assignments),
            wind_assignments=list(wind_assignments),
            zones=list(zones),
            spawn_requests=list(requests),
            time_steps=normalized_time_steps,
        )
        if request is not None:
            return extract_batch_world_setup_entity_ids(self.apply_world_setup(request))
        return apply_world_setup_payload_compat(
            self._batch_target(),
            seeds=[int(seed) for seed in seeds],
            terrain_assignments=list(terrain_assignments),
            wind_assignments=list(wind_assignments),
            zones=list(zones),
            spawn_requests=list(requests),
            time_steps=normalized_time_steps,
        )

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

    def export_observation_packet_for_refs(
        self,
        refs: Sequence[Any],
        *,
        include_agent_observations: bool = True,
        include_instrument_states: bool = True,
        include_mission_commands: bool = False,
        include_task_orders: bool = False,
        include_leader_intents: bool = False,
        include_pilot_reports: bool = False,
    ) -> Any:
        refs_list = list(refs)
        if hasattr(ef_py, "ObservationBatchRequest"):
            request = ef_py.ObservationBatchRequest()
            request.refs = refs_list
            request.include_agent_observations = bool(include_agent_observations)
            request.include_instrument_states = bool(include_instrument_states)
            request.include_mission_commands = bool(include_mission_commands)
            request.include_task_orders = bool(include_task_orders)
            request.include_leader_intents = bool(include_leader_intents)
            request.include_pilot_reports = bool(include_pilot_reports)
            return self.export_observation_packet(request)
        return self.export_observation_packet(refs_list)

    def read_truth_and_instruments(self, refs: Sequence[Any]) -> tuple[list[Any], list[Any]]:
        packet = self.export_observation_packet_for_refs(
            refs,
            include_agent_observations=True,
            include_instrument_states=True,
            include_mission_commands=False,
            include_task_orders=False,
            include_leader_intents=False,
            include_pilot_reports=False,
        )
        if hasattr(packet, "agent_observations") and hasattr(packet, "instrument_states"):
            return list(packet.agent_observations), list(packet.instrument_states)
        refs_list = list(refs)
        if self.facade is not None:
            return (
                list(self.facade.get_agent_observations_batch(refs_list)),
                list(self.facade.get_instrument_states_batch(refs_list)),
            )
        return (
            list(self._compat_runtime.get_agent_observations_batch(refs_list)),
            list(self._compat_runtime.get_instrument_states_batch(refs_list)),
        )

    def read_observation_packet(
        self,
        refs: Sequence[Any],
        *,
        include_agent_observations: bool = True,
        include_instrument_states: bool = True,
        include_mission_commands: bool = False,
        include_task_orders: bool = False,
        include_leader_intents: bool = False,
        include_pilot_reports: bool = False,
    ) -> Any:
        return self.export_observation_packet_for_refs(
            refs,
            include_agent_observations=include_agent_observations,
            include_instrument_states=include_instrument_states,
            include_mission_commands=include_mission_commands,
            include_task_orders=include_task_orders,
            include_leader_intents=include_leader_intents,
            include_pilot_reports=include_pilot_reports,
        )

    def get_instrument_states_batch(self, refs: Sequence[Any]) -> list[Any]:
        _truth, inst = self.read_truth_and_instruments(refs)
        return inst

    def get_agent_observations_batch(self, refs: Sequence[Any]) -> list[Any]:
        truth, _inst = self.read_truth_and_instruments(refs)
        return truth

    def get_mission_commands_batch(self, refs: Sequence[Any]) -> list[Any]:
        return list(self._batch_target().get_mission_commands_batch(list(refs)))

    def set_pilot_actions_batch(self, assignments: Sequence[Any]) -> None:
        self._last_window_evidence = None
        self._batch_target().set_pilot_actions_batch(list(assignments))

    def step_batch(self) -> None:
        self._last_window_evidence = None
        self._batch_target().step_batch()

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
        refs = []
        for step_request in list(getattr(request, "step_requests", []) or []):
            ref = ef_py.WorldEntityRef()
            ref.world_index = int(getattr(step_request, "world_index", 0))
            ref.entity_id = int(getattr(step_request, "entity_id", 0))
            refs.append(ref)
        result.step_results = step_results
        result.execution_episode_states = list(
            self._compat_runtime.export_execution_episode_states_batch(refs)
        )
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
        self._last_window_evidence = None
        self._compat_runtime.step_worlds([int(index) for index in world_indices])

    def set_mission_commands_batch(self, assignments: Sequence[Any]) -> None:
        self._batch_target().set_mission_commands_batch(list(assignments))

    def set_task_orders_batch(self, assignments: Sequence[Any]) -> None:
        self._batch_target().set_task_orders_batch(list(assignments))

    def set_leader_intents_batch(self, assignments: Sequence[Any]) -> None:
        self._batch_target().set_leader_intents_batch(list(assignments))

    def set_pilot_reports_batch(self, assignments: Sequence[Any]) -> None:
        self._batch_target().set_pilot_reports_batch(list(assignments))


__all__ = ["RuntimeFacadeAdapter"]
