from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import ef_py

from gym_envs.scenario_loader import ScenarioLoader

from python.scenario.runtime import AppliedScenarioWorld
from python.scenario.runtime import BatchWorldApplyBuffer
from python.scenario.runtime import resolve_active_controllable_roster
from python.scenario.runtime.world_setup_compat import apply_runtime_world_layout_request_compatibility_quarantine
from python.scenario.runtime.world_setup_compat import apply_runtime_world_layout_request_maintained
from python.scenario.runtime.world_setup_compat import apply_world_setup_payload_compatibility_quarantine
from python.scenario.runtime.world_setup_compat import apply_world_setup_request_compatibility_quarantine
from python.scenario.runtime.world_setup_compat import apply_world_setup_request_maintained
from python.scenario.runtime.world_setup_compat import build_batch_world_setup_request
from python.scenario.runtime.world_setup_compat import build_runtime_world_layout_request
from python.scenario.runtime.world_setup_compat import extract_batch_world_setup_entity_ids
from python.scenario.runtime.world_setup_compat import read_runtime_world_time_step_compat

from python.rl.runtime.agent_shim import MAINTAINED
from python.rl.runtime.agent_shim import OBS_DECISION_BELIEF_PACKET
from python.rl.runtime.agent_shim import OBS_FACADE_OBSERVATION_PACKET
from .compat import normalize_runtime_compatibility_enabled
from .compat import runtime_compatibility_required_message
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
class _ObservationPacketCompat:
    refs: list[Any]
    agent_observations: list[Any]
    instrument_states: list[Any]


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


@dataclass
class _WorldLayoutSnapshot:
    world_index: int
    applied_world: AppliedScenarioWorld | None = None
    time_step_s: float | None = None


class _WorldAccessProxy:
    """Compatibility-facing world proxy that prefers adapter-owned read seams."""

    def __init__(self, adapter: "RuntimeFacadeAdapter", world_index: int):
        self._adapter = adapter
        self._world_index = int(world_index)

    def _fallback_world(self) -> Any:
        return self._adapter._compat_world(self._world_index)

    def get_time_step(self) -> float:
        return self._adapter.get_time_step(self._world_index)

    def get_layout(self) -> Any:
        layout = self._adapter.get_world_layout(self._world_index)
        if layout is None:
            raise AttributeError(f"world {self._world_index} has no adapter-owned layout snapshot")
        return layout

    def __getattr__(self, name: str) -> Any:
        return getattr(self._fallback_world(), name)


class _ScenarioLoaderRuntimeProxy:
    """World-indexed loader runtime shim that prefers facade-owned batch surfaces."""

    def __init__(self, adapter: "RuntimeFacadeAdapter", world_index: int):
        self._adapter = adapter
        self._world_index = int(world_index)

    def _fallback_world(self):
        return self._adapter._compat_world(self._world_index)

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
        return getattr(self._fallback_world(), name)


class RuntimeFacadeAdapter:
    """Centralized compatibility adapter for facade-shaped runtime access."""

    def __init__(self, world_count: int, *, runtime_compatibility_enabled: bool = False):
        self._world_count = int(world_count)
        self.facade = ef_py.RuntimeFacade(self._world_count) if hasattr(ef_py, "RuntimeFacade") else None
        self.runtime_compatibility_enabled = normalize_runtime_compatibility_enabled(runtime_compatibility_enabled)
        self._compat_runtime = None
        self._last_window_evidence: RuntimeWindowEvidence | None = None
        self._world_layout_snapshots: dict[int, _WorldLayoutSnapshot] = {}

    def _batch_target(self):
        if self.facade is not None:
            return self.facade
        if not self.runtime_compatibility_enabled:
            raise RuntimeError(runtime_compatibility_required_message("RuntimeFacadeAdapter._batch_target"))
        return self._compat_runtime_handle()

    def _compat_runtime_handle(self):
        if self._compat_runtime is not None:
            return self._compat_runtime
        if self.facade is not None:
            if not self.runtime_compatibility_enabled:
                raise RuntimeError(
                    runtime_compatibility_required_message(
                        "RuntimeFacadeAdapter._compat_runtime_handle"
                    )
                )
            self._compat_runtime = self.facade.runtime()
            return self._compat_runtime
        if not self.runtime_compatibility_enabled:
            raise RuntimeError(runtime_compatibility_required_message("RuntimeFacadeAdapter._compat_runtime_handle"))
        self._compat_runtime = ef_py.WorldBatchRuntime(self._world_count)
        return self._compat_runtime

    def _compat_world(self, index: int):
        return self._compat_runtime_handle().world(int(index))

    def _require_compatibility_fallback(self, surface: str) -> None:
        if not self.runtime_compatibility_enabled:
            raise RuntimeError(runtime_compatibility_required_message(surface))

    def _scenario_loader_runtime(self, index: int) -> _ScenarioLoaderRuntimeProxy:
        return _ScenarioLoaderRuntimeProxy(self, int(index))

    def compatibility_fallback_enabled(self) -> bool:
        return bool(self.runtime_compatibility_enabled)

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
            and hasattr(ef_py, "AgentRole")
            and hasattr(ef_py, "authorize_maintained_action_intent")
        )

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
        if hasattr(observation_request, "include_mission_commands"):
            observation_request.include_mission_commands = False
        if hasattr(observation_request, "include_leader_intents"):
            observation_request.include_leader_intents = False
        if hasattr(observation_request, "include_pilot_reports"):
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
            action_request.action_intent.action_family = "direct_control"
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
        if self.facade is not None:
            return int(self.facade.world_count())
        return int(self._world_count)

    def set_worker_threads(self, worker_threads: int) -> None:
        self._batch_target().set_worker_threads(int(worker_threads))

    def worker_threads(self) -> int:
        return int(self._batch_target().worker_threads())

    def effective_worker_threads(self) -> int:
        return int(self._batch_target().effective_worker_threads())

    def load_database(self, path: str) -> bool:
        return bool(self._batch_target().load_database(path))

    def world(self, index: int):
        return _WorldAccessProxy(self, int(index))

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
        if self.facade is not None:
            return apply_runtime_world_layout_request_maintained(self.facade, request)
        if self.runtime_compatibility_enabled:
            return apply_runtime_world_layout_request_compatibility_quarantine(
                self._compat_runtime_handle(),
                request,
            )
        raise RuntimeError(
            runtime_compatibility_required_message("RuntimeFacadeAdapter.apply_world_layout")
        )

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
        self._world_layout_snapshots[int(world_index)] = _WorldLayoutSnapshot(
            world_index=int(world_index),
            applied_world=applied_world,
            time_step_s=None if getattr(layout, "time_step_s", None) is None else float(layout.time_step_s),
        )
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
        snapshot = self._world_layout_snapshots.get(int(world_index))
        if self.facade is not None and hasattr(self.facade, "world_time_step"):
            return float(self.facade.world_time_step(int(world_index)))
        compat_runtime = self._compat_runtime_handle()
        return float(
            read_runtime_world_time_step_compat(
                compat_runtime,
                int(world_index),
                fallback_time_step_s=None if snapshot is None else snapshot.time_step_s,
            )
        )

    def get_world_layout(self, world_index: int) -> Any | None:
        snapshot = self._world_layout_snapshots.get(int(world_index))
        if snapshot is None or snapshot.applied_world is None:
            return None
        return snapshot.applied_world.layout

    def get_visual_observation(self, world_index: int, entity_id: int) -> Any:
        self._require_compatibility_fallback("RuntimeFacadeAdapter.legacy_visual_observation")
        return self._compat_world(int(world_index)).get_visual_observation(int(entity_id))

    def get_visual_observation_downsampled(
        self,
        world_index: int,
        entity_id: int,
        downsample: int,
    ) -> Any:
        self._require_compatibility_fallback("RuntimeFacadeAdapter.legacy_visual_observation")
        return self._compat_world(int(world_index)).get_visual_observation_downsampled(
            int(entity_id),
            int(downsample),
        )

    def supports_visual_observation_downsampled(self, world_index: int) -> bool:
        self._require_compatibility_fallback("RuntimeFacadeAdapter.legacy_visual_observation")
        return hasattr(self._compat_world(int(world_index)), "get_visual_observation_downsampled")

    def compute_visual_observation_batch_numpy(
        self,
        refs: Sequence[Any],
        downsample: int,
        use_gpu_host: bool,
    ) -> Any:
        batch_target = self.facade if self.facade is not None else self._compat_runtime_handle()
        return ef_py.compute_world_batch_visual_observation_batch_numpy(
            batch_target,
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
        batch_target = self.facade if self.facade is not None else self._compat_runtime_handle()
        return ef_py.compute_world_batch_visual_observation_batch_export(
            batch_target,
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
        if self.facade is not None:
            entity_ids = apply_world_setup_request_maintained(self.facade, request)
        elif self.runtime_compatibility_enabled:
            entity_ids = apply_world_setup_request_compatibility_quarantine(
                self._compat_runtime_handle(),
                request,
            )
        else:
            raise RuntimeError(
                runtime_compatibility_required_message("RuntimeFacadeAdapter.apply_world_setup")
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
        if not self.runtime_compatibility_enabled:
            raise RuntimeError(
                runtime_compatibility_required_message("RuntimeFacadeAdapter.apply_world_setup_batch")
            )
        return apply_world_setup_payload_compatibility_quarantine(
            self._compat_runtime_handle(),
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
        return _ObservationPacketCompat(
            refs=refs,
            agent_observations=(
                list(self._compat_runtime_handle().get_agent_observations_batch(refs))
                if include_agent_observations
                else []
            ),
            instrument_states=(
                list(self._compat_runtime_handle().get_instrument_states_batch(refs))
                if include_instrument_states
                else []
            ),
        )

    def export_observation_packet_for_refs(
        self,
        refs: Sequence[Any],
        *,
        include_agent_observations: bool = True,
        include_instrument_states: bool = True,
        include_mission_commands: bool = False,
        include_leader_intents: bool = False,
        include_pilot_reports: bool = False,
    ) -> Any:
        refs_list = list(refs)
        if hasattr(ef_py, "ObservationBatchRequest"):
            request = ef_py.ObservationBatchRequest()
            request.refs = refs_list
            request.include_agent_observations = bool(include_agent_observations)
            request.include_instrument_states = bool(include_instrument_states)
            if hasattr(request, "include_mission_commands"):
                request.include_mission_commands = bool(include_mission_commands)
            if hasattr(request, "include_leader_intents"):
                request.include_leader_intents = bool(include_leader_intents)
            if hasattr(request, "include_pilot_reports"):
                request.include_pilot_reports = bool(include_pilot_reports)
            return self.export_observation_packet(request)
        return self.export_observation_packet(refs_list)

    def read_truth_and_instruments(self, refs: Sequence[Any]) -> tuple[list[Any], list[Any]]:
        packet = self.export_observation_packet_for_refs(
            refs,
            include_agent_observations=True,
            include_instrument_states=True,
            include_mission_commands=False,
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
        compat_runtime = self._compat_runtime_handle()
        return (
            list(compat_runtime.get_agent_observations_batch(refs_list)),
            list(compat_runtime.get_instrument_states_batch(refs_list)),
        )

    def read_observation_packet(
        self,
        refs: Sequence[Any],
        *,
        include_agent_observations: bool = True,
        include_instrument_states: bool = True,
        include_mission_commands: bool = False,
        include_leader_intents: bool = False,
        include_pilot_reports: bool = False,
    ) -> Any:
        return self.export_observation_packet_for_refs(
            refs,
            include_agent_observations=include_agent_observations,
            include_instrument_states=include_instrument_states,
            include_mission_commands=include_mission_commands,
            include_leader_intents=include_leader_intents,
            include_pilot_reports=include_pilot_reports,
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
        return self._compat_world(int(world_index)).get_agent_observation(int(entity_id))

    def get_instrument_state(self, world_index: int, entity_id: int) -> Any:
        ref = ef_py.WorldEntityRef()
        ref.world_index = int(world_index)
        ref.entity_id = int(entity_id)
        instrument_states = self.get_instrument_states_batch([ref])
        if instrument_states:
            return instrument_states[0]
        return self._compat_world(int(world_index)).get_instrument_state(int(entity_id))

    def get_mission_commands_maintained_batch(self, refs: Sequence[Any]) -> list[Any]:
        return list(self._batch_target().get_mission_commands_maintained_batch(list(refs)))

    def get_task_orders_maintained_batch(self, refs: Sequence[Any]) -> list[Any]:
        batch_target = self._batch_target()
        if hasattr(batch_target, "get_task_orders_maintained_batch"):
            return list(batch_target.get_task_orders_maintained_batch(list(refs)))
        return []

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
        self._compat_runtime_handle().prime_execution_episode_controller_batch(list(refs), list(states))

    def execution_episode_ready(self, world_index: int) -> bool:
        if self.facade is not None:
            return bool(self.facade.execution_episode_ready(int(world_index)))
        return bool(self._compat_runtime_handle().execution_episode_controller_ready(int(world_index)))

    def execution_episode_controller_ready(self, world_index: int) -> bool:
        return self.execution_episode_ready(int(world_index))

    def step_execution_batch(self, request: Any) -> Any:
        if self.facade is not None:
            return self.facade.step_execution_batch(request)
        result = ef_py.ExecutionBatchStepResult()
        compat_runtime = self._compat_runtime_handle()
        step_results = list(compat_runtime.step_execution_episode_results_batch(list(request.step_requests)))
        refs = []
        for step_request in list(getattr(request, "step_requests", []) or []):
            ref = ef_py.WorldEntityRef()
            ref.world_index = int(getattr(step_request, "world_index", 0))
            ref.entity_id = int(getattr(step_request, "entity_id", 0))
            refs.append(ref)
        result.step_results = step_results
        result.execution_episode_states = list(
            compat_runtime.export_execution_episode_states_batch(refs)
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
        return list(self._compat_runtime_handle().step_execution_episode_batch(list(requests)))

    def export_execution_episode_states(self, refs: Sequence[Any]) -> list[Any]:
        if self.facade is not None:
            return list(self.facade.export_execution_episode_states(list(refs)))
        return list(self._compat_runtime_handle().export_execution_episode_states_batch(list(refs)))

    def export_execution_episode_states_batch(self, refs: Sequence[Any]) -> list[Any]:
        return self.export_execution_episode_states(refs)

    def step_worlds(self, world_indices: Sequence[int]) -> None:
        self._last_window_evidence = None
        indices = [int(index) for index in world_indices]
        if self.facade is not None:
            if len(indices) == self.world_count() and indices == list(range(self.world_count())):
                self.facade.step_batch()
                return
            if not self.runtime_compatibility_enabled:
                raise RuntimeError(runtime_compatibility_required_message("RuntimeFacadeAdapter.step_worlds"))
        self._compat_runtime_handle().step_worlds(indices)

    def set_mission_commands_maintained_batch(self, assignments: Sequence[Any]) -> None:
        batch_target = self._batch_target()
        if hasattr(batch_target, "set_mission_commands_maintained_batch"):
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
        if hasattr(batch_target, "set_task_orders_maintained_batch"):
            batch_target.set_task_orders_maintained_batch(materialized_assignments)
            return
        raise RuntimeError(
            _maintained_task_order_write_required_message(
                "RuntimeFacadeAdapter.set_task_orders_maintained_batch"
            )
        )

    def set_leader_intents_maintained_batch(self, assignments: Sequence[Any]) -> None:
        batch_target = self._batch_target()
        if hasattr(batch_target, "set_leader_intents_maintained_batch"):
            batch_target.set_leader_intents_maintained_batch(list(assignments))
            return
        raise RuntimeError(
            _maintained_command_chain_write_required_message(
                "RuntimeFacadeAdapter.set_leader_intents_maintained_batch"
            )
        )

    def set_pilot_reports_maintained_batch(self, assignments: Sequence[Any]) -> None:
        batch_target = self._batch_target()
        if hasattr(batch_target, "set_pilot_reports_maintained_batch"):
            batch_target.set_pilot_reports_maintained_batch(list(assignments))
            return
        raise RuntimeError(
            _maintained_command_chain_write_required_message(
                "RuntimeFacadeAdapter.set_pilot_reports_maintained_batch"
            )
        )


__all__ = ["RuntimeFacadeAdapter"]
