from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import ef_py

from gym_envs.scenario_loader import ScenarioLoader

from python.scenario.runtime import AppliedScenarioWorld
from python.scenario.runtime import BatchWorldApplyBuffer
from python.scenario.runtime import resolve_active_controllable_roster
from python.scenario.runtime.world_setup import apply_runtime_world_layout_request_maintained
from python.scenario.runtime.world_setup import apply_world_setup_request_maintained
from python.scenario.runtime.world_setup import build_batch_world_setup_request
from python.scenario.runtime.world_setup import build_runtime_world_layout_request
from python.scenario.runtime.world_setup import extract_batch_world_setup_entity_ids

from python.rl.runtime.agent_shim import MAINTAINED
from python.rl.runtime.agent_shim import OBS_DECISION_BELIEF_PACKET
from python.rl.runtime.agent_shim import OBS_FACADE_OBSERVATION_PACKET
from .command_chain_cache import project_world_leader_intent_maintained_assignment
from .command_chain_cache import project_world_mission_command_maintained_assignment
from .command_chain_cache import project_world_pilot_report_maintained_assignment
from .command_chain_cache import project_world_task_order_maintained_assignment


def _maintained_task_order_write_required_message(surface: str) -> str:
    return (
        f"{surface} requires maintained TaskOrder batch bindings; "
        "legacy TaskOrder whole-shell and raw world.set_task_order fallback are disabled "
        "for Python business paths."
    )


def _maintained_command_chain_write_required_message(surface: str) -> str:
    return (
        f"{surface} requires maintained command-chain batch bindings; "
        "MissionCommand, LeaderIntent, and PilotReport whole-shell fallback writers are "
        "disabled for Python business paths."
    )


def _maintained_window_authorization_required_message(reason: str) -> str:
    return (
        "RuntimeFacadeAdapter.run_maintained_window requires explicit maintained "
        "ObservationPacket/DecisionBelief provenance and AgentRole authorization; "
        f"{reason}"
    )


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


@dataclass(frozen=True)
class RuntimeFacadeAdapterCapabilities:
    """Resolved adapter capability snapshot for the current facade binding."""

    has_runtime_window_api: bool
    has_world_time_step: bool
    has_observation_batch_request: bool
    has_export_observation_packet: bool
    has_get_task_orders_maintained_batch: bool
    has_apply_launch_requests_batch: bool
    has_set_mission_commands_maintained_batch: bool
    has_set_task_orders_maintained_batch: bool
    has_set_leader_intents_maintained_batch: bool
    has_set_pilot_reports_maintained_batch: bool


def _resolve_runtime_facade_adapter_capabilities(facade: Any) -> RuntimeFacadeAdapterCapabilities:
    return RuntimeFacadeAdapterCapabilities(
        has_runtime_window_api=bool(
            hasattr(facade, "run_wp10_window")
            and hasattr(ef_py, "RuntimeWindowRequest")
            and hasattr(ef_py, "RuntimeWindowActionRequest")
            and hasattr(ef_py, "AgentRole")
            and hasattr(ef_py, "authorize_maintained_action_intent")
        ),
        has_world_time_step=bool(hasattr(facade, "world_time_step")),
        has_observation_batch_request=bool(hasattr(ef_py, "ObservationBatchRequest")),
        has_export_observation_packet=bool(hasattr(facade, "export_observation_packet")),
        has_get_task_orders_maintained_batch=bool(
            hasattr(facade, "get_task_orders_maintained_batch")
        ),
        has_apply_launch_requests_batch=bool(
            hasattr(facade, "apply_launch_requests_batch")
        ),
        has_set_mission_commands_maintained_batch=bool(
            hasattr(facade, "set_mission_commands_maintained_batch")
        ),
        has_set_task_orders_maintained_batch=bool(
            hasattr(facade, "set_task_orders_maintained_batch")
        ),
        has_set_leader_intents_maintained_batch=bool(
            hasattr(facade, "set_leader_intents_maintained_batch")
        ),
        has_set_pilot_reports_maintained_batch=bool(
            hasattr(facade, "set_pilot_reports_maintained_batch")
        ),
    )


class _ScenarioLoaderRuntimeProxy:
    """World-indexed loader runtime shim that prefers facade-owned batch surfaces."""

    def __init__(self, adapter: "RuntimeFacadeAdapter", world_index: int):
        self._adapter = adapter
        self._world_index = int(world_index)
        self._mission_commands: dict[int, Any] = {}

    def _ref(self, entity_id: int):
        ref = ef_py.WorldEntityRef()
        ref.world_index = int(self._world_index)
        ref.entity_id = int(entity_id)
        return ref

    def get_agent_observation(self, entity_id: int) -> Any:
        return self._adapter.get_agent_observation(self._world_index, int(entity_id))

    def get_instrument_state(self, entity_id: int) -> Any:
        return self._adapter.get_instrument_state(self._world_index, int(entity_id))

    def get_time_step(self) -> float:
        return self._adapter.get_time_step(self._world_index)

    def is_unit_active(self, entity_id: int) -> bool:
        observation = self.get_agent_observation(int(entity_id))
        return float(getattr(observation, "health", 0.0) or 0.0) > 0.0

    def _mission_command_shell(self, entity_id: int) -> Any:
        entity_key = int(entity_id)
        command = self._mission_commands.get(entity_key)
        if command is None:
            command = ef_py.MissionCommand()
            self._mission_commands[entity_key] = command
        return command

    def get_unit_position(self, entity_id: int) -> tuple[float, float, float]:
        observation = self.get_agent_observation(int(entity_id))
        return (
            float(getattr(observation, "x", 0.0) or 0.0),
            float(getattr(observation, "y", 0.0) or 0.0),
            float(getattr(observation, "z", 0.0) or 0.0),
        )

    def set_command(
        self,
        entity_id: int,
        target_heading_deg: float,
        target_speed_mps: float,
        target_altitude_m: float,
    ) -> None:
        command = self._mission_command_shell(int(entity_id))
        command.cmd_heading_deg = float(target_heading_deg)
        command.cmd_speed_mps = float(target_speed_mps)
        command.cmd_altitude_m = float(target_altitude_m)
        command.active = True
        self.set_mission_command(int(entity_id), command)

    def fire_missile(self, entity_id: int, target_id: int) -> int:
        command = self._mission_command_shell(int(entity_id))
        command.assigned_target_id = int(target_id)
        command.authorization_to_fire = True
        command.active = True
        self.set_mission_command(int(entity_id), command)

        try:
            observation = self.get_agent_observation(int(entity_id))
            requested_time_s = float(getattr(observation, "sim_time", 0.0) or 0.0)
        except Exception:
            requested_time_s = 0.0
        request = ef_py.LaunchRequest()
        request.request_id = self._adapter.next_launch_request_id()
        request.shooter.world_index = int(self._world_index)
        request.shooter.entity_id = int(entity_id)
        request.target_entity.world_index = int(self._world_index)
        request.target_entity.entity_id = int(target_id)
        request.has_target_entity = True
        request.authority = "scripted_opponent"
        request.requested_time_s = requested_time_s
        request.requested_munition_family = "missile"
        events = self._adapter.apply_launch_requests_batch([request])
        if not events:
            return 0
        event = events[0]
        return int(getattr(event, "spawned_munition").entity_id) if bool(getattr(event, "accepted", False)) else 0

    def set_mission_command(self, entity_id: int, command: Any) -> None:
        try:
            assignment = ef_py.WorldMissionCommandMaintainedAssignment()
            project_world_mission_command_maintained_assignment(
                assignment,
                world_index=int(self._world_index),
                entity_id=int(entity_id),
                compatibility_mission_command_shell=command,
            )
        except (AttributeError, RuntimeError) as exc:
            raise RuntimeError(
                _maintained_command_chain_write_required_message(
                    "ScenarioLoader.set_mission_command"
                )
            ) from exc
        self._mission_commands[int(entity_id)] = command
        self._adapter.set_mission_commands_maintained_batch([assignment])

    def set_task_order(self, entity_id: int, order: Any) -> None:
        try:
            assignment = ef_py.WorldTaskOrderMaintainedAssignment()
        except AttributeError as exc:
            raise RuntimeError(
                _maintained_task_order_write_required_message("ScenarioLoader.set_task_order")
            ) from exc
        try:
            project_world_task_order_maintained_assignment(
                assignment,
                world_index=int(self._world_index),
                entity_id=int(entity_id),
                compatibility_task_order_shell=order,
            )
        except (AttributeError, RuntimeError) as exc:
            raise RuntimeError(
                _maintained_task_order_write_required_message("ScenarioLoader.set_task_order")
            ) from exc
        self._adapter.set_task_orders_maintained_batch([assignment])

    def set_leader_intent(self, entity_id: int, intent: Any) -> None:
        try:
            assignment = ef_py.WorldLeaderIntentMaintainedAssignment()
            project_world_leader_intent_maintained_assignment(
                assignment,
                world_index=int(self._world_index),
                entity_id=int(entity_id),
                compatibility_intent_shell=intent,
            )
        except (AttributeError, RuntimeError) as exc:
            raise RuntimeError(
                _maintained_command_chain_write_required_message(
                    "ScenarioLoader.set_leader_intent"
                )
            ) from exc
        self._adapter.set_leader_intents_maintained_batch([assignment])

    def set_pilot_report(self, entity_id: int, report: Any) -> None:
        try:
            assignment = ef_py.WorldPilotReportMaintainedAssignment()
            project_world_pilot_report_maintained_assignment(
                assignment,
                world_index=int(self._world_index),
                entity_id=int(entity_id),
                compatibility_report_shell=report,
            )
        except (AttributeError, RuntimeError) as exc:
            raise RuntimeError(
                _maintained_command_chain_write_required_message(
                    "ScenarioLoader.set_pilot_report"
                )
            ) from exc
        self._adapter.set_pilot_reports_maintained_batch([assignment])

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(name)


class RuntimeFacadeAdapter:
    """Centralized compatibility adapter for facade-shaped runtime access."""

    def __init__(self, world_count: int):
        self._world_count = int(world_count)
        if not hasattr(ef_py, "RuntimeFacade"):
            raise RuntimeError("RuntimeFacadeAdapter requires ef_py.RuntimeFacade bindings")
        self.facade = ef_py.RuntimeFacade(self._world_count)
        self._capabilities_facade_id: int | None = None
        self._capabilities: RuntimeFacadeAdapterCapabilities | None = None
        self._last_window_evidence: RuntimeWindowEvidence | None = None
        self._world_layouts: dict[int, AppliedScenarioWorld] = {}
        self._world_time_steps: dict[int, float] = {}
        self._next_launch_request_id = 1

    @property
    def capabilities(self) -> RuntimeFacadeAdapterCapabilities:
        facade_id = id(self.facade)
        if self._capabilities is None or self._capabilities_facade_id != facade_id:
            self._capabilities = _resolve_runtime_facade_adapter_capabilities(self.facade)
            self._capabilities_facade_id = facade_id
        return self._capabilities

    def _batch_target(self):
        return self.facade

    def _scenario_loader_runtime(self, index: int) -> _ScenarioLoaderRuntimeProxy:
        return _ScenarioLoaderRuntimeProxy(self, int(index))

    @property
    def last_window_evidence(self) -> RuntimeWindowEvidence | None:
        return self._last_window_evidence

    def clear_last_window_evidence(self) -> None:
        self._last_window_evidence = None

    def supports_runtime_window_api(self) -> bool:
        return self.capabilities.has_runtime_window_api

    def _runtime_window_authorized_action_role(
        self,
        *,
        world_index: int,
        entity_id: int,
        information_state_label: str,
        input_snapshot_version: str,
        action_interface_kind: str,
        action_interface_payload_type: str,
        decision_model_kind: str,
        decision_model_id: str,
    ) -> Any:
        normalized_label = str(information_state_label).strip()
        if normalized_label not in {
            OBS_FACADE_OBSERVATION_PACKET,
            OBS_DECISION_BELIEF_PACKET,
        }:
            raise RuntimeError(
                _maintained_window_authorization_required_message(
                    f"unsupported provenance label {information_state_label!r}"
                )
            )

        role = ef_py.AgentRole()
        role.role.role_id = f"agent:{int(world_index)}:{int(entity_id)}"
        role.role.role_type = "autopilot_controller"
        role.authority_scope.scope = (
            "mission_command"
            if str(action_interface_payload_type) == "mission_command"
            else "platform_control"
        )
        role.authority_scope.world_index = int(world_index)
        role.authority_scope.has_world_index = True
        role.authority_scope.entity_ids = [int(entity_id)]
        if normalized_label == OBS_DECISION_BELIEF_PACKET:
            role.information_state_source.information_state_layer = "DecisionBelief"
            role.information_state_source.source_label = "observation_derived_belief"
        else:
            role.information_state_source.information_state_layer = "AgentObservation"
            role.information_state_source.source_label = "facade_observation_packet"
            role.information_state_source.observation_packet_ids = [
                f"obs:{int(world_index)}:{int(entity_id)}"
            ]
        role.information_state_source.maintained_status = MAINTAINED
        role.information_state_source.source_observation_versions = [
            str(input_snapshot_version)
        ]
        role.decision_model_ref.kind = str(decision_model_kind)
        role.decision_model_ref.id = str(decision_model_id)
        role.action_interface.kind = str(action_interface_kind)
        role.action_interface.payload_type = str(action_interface_payload_type)
        return role

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
        information_state_label: str | None = None,
        decision_model_kind: str = "policy",
        decision_model_id: str = "runtime_window_policy",
        action_family: str = "direct_control",
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
            snapshot_version = str(
                input_snapshot_version
                if input_snapshot_version is not None and str(input_snapshot_version).strip()
                else f"obs:{int(world_index)}:{int(entity_id)}"
            )
            action_request.input_snapshot_version = snapshot_version
            action_request.action_intent.source_id = (
                f"{action_request.source_layer}:{int(world_index)}:{int(entity_id)}"
            )
            action_request.action_intent.effective_time_s = request.source_time_s
            action_request.action_intent.valid_until_s = request.source_time_s + 1.0
            action_request.action_intent.target.world_index = int(world_index)
            action_request.action_intent.target.entity_id = int(entity_id)
            action_request.action_intent.action_family = str(action_family)
            action_request.action_intent.merge_policy = "last_write_wins"
            payload_type = "mission_command" if mission_command is not None else "pilot_action"
            interface_kind = (
                "CommandChainAssignmentCompat"
                if mission_command is not None
                else "PilotActionAssignmentCompat"
            )
            action_request.action_intent.action_interface.kind = interface_kind
            action_request.action_intent.action_interface.payload_type = payload_type
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
            role = self._runtime_window_authorized_action_role(
                world_index=int(world_index),
                entity_id=int(entity_id),
                information_state_label="" if information_state_label is None else str(information_state_label),
                input_snapshot_version=snapshot_version,
                action_interface_kind=interface_kind,
                action_interface_payload_type=payload_type,
                decision_model_kind=str(decision_model_kind),
                decision_model_id=str(decision_model_id),
            )
            authorization = ef_py.authorize_maintained_action_intent(
                role,
                action_request.action_intent,
            )
            if not bool(getattr(authorization, "authorized", False)):
                raise RuntimeError(
                    _maintained_window_authorization_required_message(
                        str(getattr(authorization, "reason", "") or "authorization failed")
                    )
                )
            request.action_requests = [action_request]

        result = self.facade.run_wp10_window(request)
        return self._store_window_evidence(
            result,
            cadence_reason="selected_slice_cadence_trace_runtime_window_wp17c",
            uses_compat_fallback=False,
        )

    def world_count(self) -> int:
        return int(self.facade.world_count())

    def set_worker_threads(self, worker_threads: int) -> None:
        self._batch_target().set_worker_threads(int(worker_threads))

    def worker_threads(self) -> int:
        return int(self._batch_target().worker_threads())

    def effective_worker_threads(self) -> int:
        return int(self._batch_target().effective_worker_threads())

    def load_database(self, path: str) -> bool:
        return bool(self._batch_target().load_database(path))

    def _build_runtime_world_layout_request(self, world_index: int, layout: Any):
        apply_buffer = BatchWorldApplyBuffer(1)
        _terrain_assignments, _wind_assignments, zone_defs, spawn_requests = apply_buffer.prepare([layout])
        for zone_def in list(zone_defs):
            zone_def.world_index = int(world_index)
        for spawn_request in list(spawn_requests):
            spawn_request.world_index = int(world_index)
        return build_runtime_world_layout_request(
            world_index=int(world_index),
            seed=int(layout.seed),
            terrain_type=str(layout.terrain_type),
            wind_speed_mps=float(layout.wind_speed_mps),
            wind_dir_from_deg=float(layout.wind_dir_from_deg),
            wind_shear_mps_per_km=float(layout.wind_shear_mps_per_km),
            maritime_configured=bool(getattr(layout, "maritime_configured", False)),
            sea_state=float(getattr(layout, "sea_state", 0.0)),
            wave_heading_deg=float(getattr(layout, "wave_heading_deg", 0.0)),
            wave_period_s=float(getattr(layout, "wave_period_s", 8.0)),
            zones=list(zone_defs),
            spawn_requests=list(spawn_requests),
            time_steps=[] if layout.time_step_s is None else [float(layout.time_step_s)],
        )

    def _apply_runtime_world_layout_request(self, request: Any) -> Any:
        return apply_runtime_world_layout_request_maintained(self.facade, request)

    def _materialize_applied_world(self, world_index: int, layout: Any, entity_ids: Sequence[Any]) -> AppliedScenarioWorld:
        entities: dict[str, int] = {}
        agent_id: int | None = None
        for spawn, entity_id in zip(list(layout.spawns), list(entity_ids), strict=False):
            entity_ids_int = int(entity_id)
            entities[str(spawn.entity_name)] = entity_ids_int
            if bool(spawn.is_agent) and agent_id is None:
                agent_id = entity_ids_int
        applied_world = AppliedScenarioWorld(layout=layout, entities=entities, agent_id=agent_id)
        applied_world.active_roster = resolve_active_controllable_roster(
            getattr(layout, "scenario_data", None),
            entities,
            world_index=int(world_index),
        )
        self._world_layouts[int(world_index)] = applied_world
        if getattr(layout, "time_step_s", None) is not None:
            self._world_time_steps[int(world_index)] = float(layout.time_step_s)
        return applied_world

    def apply_world_layout(self, world_index: int, layout: Any):
        request = self._build_runtime_world_layout_request(int(world_index), layout)
        result = self._apply_runtime_world_layout_request(request)
        return self._materialize_applied_world(
            int(world_index),
            layout,
            list(getattr(result, "entity_ids", []) or []),
        )

    def make_scenario_loader(self, index: int) -> ScenarioLoader:
        return ScenarioLoader(self._scenario_loader_runtime(int(index)))

    def get_time_step(self, world_index: int) -> float:
        if int(world_index) in self._world_time_steps:
            return float(self._world_time_steps[int(world_index)])
        if self.capabilities.has_world_time_step:
            return float(self.facade.world_time_step(int(world_index)))
        raise RuntimeError("RuntimeFacadeAdapter.get_time_step requires maintained facade time-step bindings")

    def get_world_layout(self, world_index: int) -> Any | None:
        applied_world = self._world_layouts.get(int(world_index))
        if applied_world is None:
            return None
        return applied_world.layout

    def compute_visual_observation_batch_numpy(
        self,
        refs: Sequence[Any],
        downsample: int,
        use_gpu_host: bool,
    ) -> Any:
        return ef_py.compute_world_batch_visual_observation_batch_numpy(
            self.facade,
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
            self.facade,
            list(refs),
            int(downsample),
            bool(prefer_device_view),
        )

    def get_sensor_candidate_ids_batch(
        self,
        refs: Sequence[Any],
        use_gpu: bool = False,
    ) -> list[Any]:
        return list(self._batch_target().get_sensor_candidate_ids_batch(list(refs), bool(use_gpu)))

    def get_visual_candidate_ids_batch(
        self,
        refs: Sequence[Any],
        range_m: float = 25000.0,
        use_gpu: bool = False,
    ) -> list[Any]:
        return list(
            self._batch_target().get_visual_candidate_ids_batch(
                list(refs),
                float(range_m),
                bool(use_gpu),
            )
        )

    def get_comm_candidate_ids_batch(
        self,
        refs: Sequence[Any],
        use_gpu: bool = False,
    ) -> list[Any]:
        return list(self._batch_target().get_comm_candidate_ids_batch(list(refs), bool(use_gpu)))

    def apply_world_setup(self, request: Any):
        entity_ids = apply_world_setup_request_maintained(self.facade, request)
        if not hasattr(ef_py, "BatchWorldSetupResult"):
            raise RuntimeError(
                "RuntimeFacadeAdapter.apply_world_setup requires maintained BatchWorldSetupResult bindings"
            )
        result = ef_py.BatchWorldSetupResult()
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
        return extract_batch_world_setup_entity_ids(self.apply_world_setup(request))

    def export_observation_packet(self, request_or_refs: Any) -> Any:
        if self.capabilities.has_export_observation_packet:
            return self.facade.export_observation_packet(request_or_refs)
        raise RuntimeError(
            "RuntimeFacadeAdapter.export_observation_packet requires maintained "
            "RuntimeFacade observation packet bindings"
        )

    def export_observation_packet_for_refs(
        self,
        refs: Sequence[Any],
        *,
        include_agent_observations: bool = True,
        include_instrument_states: bool = True,
    ) -> Any:
        refs_list = list(refs)
        if self.capabilities.has_observation_batch_request:
            request = ef_py.ObservationBatchRequest()
            request.refs = refs_list
            request.include_agent_observations = bool(include_agent_observations)
            request.include_instrument_states = bool(include_instrument_states)
            return self.export_observation_packet(request)
        return self.export_observation_packet(refs_list)

    def read_truth_and_instruments(self, refs: Sequence[Any]) -> tuple[list[Any], list[Any]]:
        packet = self.export_observation_packet_for_refs(
            refs,
            include_agent_observations=True,
            include_instrument_states=True,
        )
        if hasattr(packet, "agent_observations") and hasattr(packet, "instrument_states"):
            return list(packet.agent_observations), list(packet.instrument_states)
        refs_list = list(refs)
        return (
            list(self.facade.get_agent_observations_batch(refs_list)),
            list(self.facade.get_instrument_states_batch(refs_list)),
        )

    def read_observation_packet(
        self,
        refs: Sequence[Any],
        *,
        include_agent_observations: bool = True,
        include_instrument_states: bool = True,
    ) -> Any:
        return self.export_observation_packet_for_refs(
            refs,
            include_agent_observations=include_agent_observations,
            include_instrument_states=include_instrument_states,
        )

    def get_instrument_states_batch(self, refs: Sequence[Any]) -> list[Any]:
        _truth, inst = self.read_truth_and_instruments(refs)
        return inst

    def get_agent_observations_batch(self, refs: Sequence[Any]) -> list[Any]:
        truth, _inst = self.read_truth_and_instruments(refs)
        return truth

    def get_agent_observation(self, world_index: int, entity_id: int) -> Any:
        ref = ef_py.WorldEntityRef()
        ref.world_index = int(world_index)
        ref.entity_id = int(entity_id)
        observations = self.get_agent_observations_batch([ref])
        if observations:
            return observations[0]
        raise RuntimeError("RuntimeFacadeAdapter.get_agent_observation received no facade observation result")

    def get_instrument_state(self, world_index: int, entity_id: int) -> Any:
        ref = ef_py.WorldEntityRef()
        ref.world_index = int(world_index)
        ref.entity_id = int(entity_id)
        instrument_states = self.get_instrument_states_batch([ref])
        if instrument_states:
            return instrument_states[0]
        raise RuntimeError("RuntimeFacadeAdapter.get_instrument_state received no facade instrument result")

    def get_mission_commands_maintained_batch(self, refs: Sequence[Any]) -> list[Any]:
        return list(self._batch_target().get_mission_commands_maintained_batch(list(refs)))

    def get_task_orders_maintained_batch(self, refs: Sequence[Any]) -> list[Any]:
        batch_target = self._batch_target()
        if self.capabilities.has_get_task_orders_maintained_batch:
            return list(batch_target.get_task_orders_maintained_batch(list(refs)))
        return []

    def set_pilot_actions_batch(self, assignments: Sequence[Any]) -> None:
        self._last_window_evidence = None
        self._batch_target().set_pilot_actions_batch(list(assignments))

    def next_launch_request_id(self) -> int:
        request_id = int(self._next_launch_request_id)
        self._next_launch_request_id += 1
        return request_id

    def apply_launch_requests_batch(self, requests: Sequence[Any]) -> list[Any]:
        self._last_window_evidence = None
        batch_target = self._batch_target()
        if not self.capabilities.has_apply_launch_requests_batch:
            raise RuntimeError(
                "RuntimeFacadeAdapter.apply_launch_requests_batch requires maintained "
                "LaunchRequest batch bindings"
            )
        return list(batch_target.apply_launch_requests_batch(list(requests)))

    def step_batch(self) -> None:
        self._last_window_evidence = None
        self._batch_target().step_batch()

    def prime_execution_episode_batch(self, refs: Sequence[Any], states: Sequence[Any]) -> None:
        self.facade.prime_execution_episode_batch(list(refs), list(states))

    def execution_episode_ready(self, world_index: int) -> bool:
        return bool(self.facade.execution_episode_ready(int(world_index)))

    def execution_episode_controller_ready(self, world_index: int) -> bool:
        return self.execution_episode_ready(int(world_index))

    def step_execution_batch(self, request: Any) -> Any:
        return self.facade.step_execution_batch(request)

    def step_execution_products_batch(self, requests: Sequence[Any]) -> list[Any]:
        return list(self.facade.step_execution_products_batch(list(requests)))

    def export_execution_episode_states(self, refs: Sequence[Any]) -> list[Any]:
        return list(self.facade.export_execution_episode_states(list(refs)))

    def export_execution_episode_states_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self.export_execution_episode_states(refs)

    def step_worlds(self, world_indices: Sequence[int]) -> None:
        self._last_window_evidence = None
        indices = [int(index) for index in world_indices]
        if len(indices) == self.world_count() and indices == list(range(self.world_count())):
            self.facade.step_batch()
            return
        raise RuntimeError("RuntimeFacadeAdapter.step_worlds requires a full facade-owned batch step")

    def set_mission_commands_maintained_batch(self, assignments: Sequence[Any]) -> None:
        batch_target = self._batch_target()
        if self.capabilities.has_set_mission_commands_maintained_batch:
            batch_target.set_mission_commands_maintained_batch(list(assignments))
            return
        raise RuntimeError(
            _maintained_command_chain_write_required_message(
                "RuntimeFacadeAdapter.set_mission_commands_maintained_batch"
            )
        )

    def set_task_orders_maintained_batch(self, assignments: Sequence[Any]) -> None:
        batch_target = self._batch_target()
        materialized_assignments = list(assignments)
        if self.capabilities.has_set_task_orders_maintained_batch:
            batch_target.set_task_orders_maintained_batch(materialized_assignments)
            return
        raise RuntimeError(
            _maintained_task_order_write_required_message(
                "RuntimeFacadeAdapter.set_task_orders_maintained_batch"
            )
        )

    def set_leader_intents_maintained_batch(self, assignments: Sequence[Any]) -> None:
        batch_target = self._batch_target()
        if self.capabilities.has_set_leader_intents_maintained_batch:
            batch_target.set_leader_intents_maintained_batch(list(assignments))
            return
        raise RuntimeError(
            _maintained_command_chain_write_required_message(
                "RuntimeFacadeAdapter.set_leader_intents_maintained_batch"
            )
        )

    def set_pilot_reports_maintained_batch(self, assignments: Sequence[Any]) -> None:
        batch_target = self._batch_target()
        if self.capabilities.has_set_pilot_reports_maintained_batch:
            batch_target.set_pilot_reports_maintained_batch(list(assignments))
            return
        raise RuntimeError(
            _maintained_command_chain_write_required_message(
                "RuntimeFacadeAdapter.set_pilot_reports_maintained_batch"
            )
        )


__all__ = ["RuntimeFacadeAdapter", "RuntimeFacadeAdapterCapabilities"]
