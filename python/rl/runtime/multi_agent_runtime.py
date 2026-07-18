from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

import ef_py

from gym_envs.universal_env import build_pilot_action, build_universal_observation, normalize_action
from python.scenario.compiler import _clone_runtime_mission_command
from python.scenario.runtime import AppliedScenarioRosterMember, active_roster_world_entity_refs


@dataclass(frozen=True)
class MultiAgentControlSlot:
    world_index: int
    entity_id: int
    entity_name: str
    roster_index: int
    team_id: int | None = None
    element_id: int | None = None
    role_code: int | None = None
    formation_role_id: str | None = None
    relative_slot_code: int | None = None
    policy_route: str | None = None
    reference_entity_id: int | None = None
    reference_entity_name: str | None = None
    mission_command_overrides: dict[str, Any] | None = None
    task_order_overrides: dict[str, Any] | None = None


def _slot_from_member(member: AppliedScenarioRosterMember, *, roster_index: int, world_index: int) -> MultiAgentControlSlot:
    return MultiAgentControlSlot(
        world_index=int(world_index),
        entity_id=int(member.entity_id),
        entity_name=str(member.entity_name),
        roster_index=int(roster_index),
        team_id=None if member.team_id is None else int(member.team_id),
        element_id=None if member.element_id is None else int(member.element_id),
        role_code=None if member.role_code is None else int(member.role_code),
        formation_role_id=None if member.formation_role_id is None else str(member.formation_role_id),
        relative_slot_code=None if member.relative_slot_code is None else int(member.relative_slot_code),
        policy_route=None if member.policy_route is None else str(member.policy_route),
        reference_entity_id=None if member.reference_entity_id is None else int(member.reference_entity_id),
        reference_entity_name=None if member.reference_entity_name is None else str(member.reference_entity_name),
        mission_command_overrides=(
            None if member.mission_command_overrides is None else _clone_runtime_mission_command(member.mission_command_overrides)
        ),
        task_order_overrides=None if member.task_order_overrides is None else dict(member.task_order_overrides),
    )


def build_control_slots_from_loader(loader, *, world_index: int) -> list[MultiAgentControlSlot]:
    roster = list(getattr(loader, "active_roster", []) or [])
    slots: list[MultiAgentControlSlot] = []
    for roster_index, member in enumerate(roster):
        slots.append(_slot_from_member(member, roster_index=roster_index, world_index=world_index))
    return slots


def _mission_command_view(command: Any) -> dict[str, Any]:
    shared_core = getattr(command, "shared_core", command)
    air_recovery = getattr(command, "air_recovery", command)
    air_takeoff = getattr(command, "air_takeoff", command)
    air_formation = getattr(command, "air_formation", command)
    return {
        "command_code": int(getattr(shared_core, "command_code", 0)),
        "target_heading": float(getattr(shared_core, "cmd_heading_deg", 0.0)),
        "target_altitude": float(getattr(shared_core, "cmd_altitude_m", 0.0)),
        "target_speed": float(getattr(shared_core, "cmd_speed_mps", 0.0)),
        "route_ref_id": int(getattr(shared_core, "route_ref_id", 0)),
        "recovery_base_id": int(getattr(air_recovery, "recovery_base_id", 0)),
        "recovery_runway_id": int(getattr(air_recovery, "recovery_runway_id", 0)),
        "takeoff_procedure_code": int(getattr(air_takeoff, "takeoff_procedure_id", 0)),
        "takeoff_clearance_code": int(getattr(air_takeoff, "takeoff_clearance_id", 0)),
        "takeoff_interval_s": float(getattr(air_takeoff, "takeoff_interval_s", 0.0)),
        "runway_slot_code": int(getattr(air_takeoff, "runway_slot_id", 0)),
        "formation_id": int(getattr(air_formation, "formation_id", 0)),
        "form_offset_x": float(getattr(air_formation, "form_offset_x", 0.0)),
        "form_offset_y": float(getattr(air_formation, "form_offset_y", 0.0)),
        "form_offset_z": float(getattr(air_formation, "form_offset_z", 0.0)),
    }


class MultiAgentWorldRuntimeView:
    """
    Minimal roster-driven routing layer for one world.

    This keeps policy metadata in the control slots while observations stay on the
    existing execution-layer contract. It is intentionally narrow so WP2 can start
    from the already maintained loader/runtime facilities.
    """

    def __init__(
        self,
        *,
        runtime,
        loader,
        world_index: int,
        action_space: Any,
        action_mode: str,
        mission_obs_mode: str,
        include_proprio: bool,
        max_contacts: int = 10,
        max_rwr: int = 4,
    ) -> None:
        self.runtime = runtime
        self.loader = loader
        self.world_index = int(world_index)
        self.action_space = action_space
        self.action_mode = str(action_mode)
        self.mission_obs_mode = str(mission_obs_mode)
        self.include_proprio = bool(include_proprio)
        self.max_contacts = int(max_contacts)
        self.max_rwr = int(max_rwr)

    def slots(self) -> list[MultiAgentControlSlot]:
        return build_control_slots_from_loader(self.loader, world_index=self.world_index)

    def refs(self) -> list[Any]:
        return active_roster_world_entity_refs(getattr(self.loader, "active_roster", None), world_index=self.world_index)

    def export_packet(
        self,
        *,
        include_agent_observations: bool = True,
        include_instrument_states: bool = True,
    ) -> Any:
        refs = self.refs()
        if not hasattr(ef_py, "ObservationBatchRequest") or not hasattr(self.runtime, "export_observation_packet"):
            raise RuntimeError(
                "MultiAgentWorldRuntimeView requires maintained RuntimeFacade observation packet export"
            )
        request = ef_py.ObservationBatchRequest()
        request.refs = list(refs)
        request.include_agent_observations = bool(include_agent_observations)
        request.include_instrument_states = bool(include_instrument_states)
        return self.runtime.export_observation_packet(request)

    def export_tasking_packet(
        self,
        *,
        include_mission_command_contracts: bool = True,
        include_task_order_contracts: bool = False,
        include_leader_intent_contracts: bool = False,
        include_pilot_report_contracts: bool = False,
    ) -> Any:
        refs = self.refs()
        if not hasattr(ef_py, "TaskingBatchRequest") or not hasattr(self.runtime, "export_tasking_packet"):
            raise RuntimeError(
                "MultiAgentWorldRuntimeView requires maintained RuntimeFacade tasking packet export"
            )
        request = ef_py.TaskingBatchRequest()
        request.refs = list(refs)
        request.include_mission_command_contracts = bool(include_mission_command_contracts)
        request.include_task_order_contracts = bool(include_task_order_contracts)
        request.include_leader_intent_contracts = bool(include_leader_intent_contracts)
        request.include_pilot_report_contracts = bool(include_pilot_report_contracts)
        return self.runtime.export_tasking_packet(request)

    def build_observations(
        self,
        *,
        last_actions: dict[int, Any] | None = None,
    ) -> dict[int, dict[str, np.ndarray]]:
        packet = self.export_packet(
            include_agent_observations=True,
            include_instrument_states=True,
        )
        tasking_packet = self.export_tasking_packet(include_mission_command_contracts=True)
        refs = list(getattr(packet, "refs", []) or [])
        truth_list = list(getattr(packet, "agent_observations", []) or [])
        inst_list = list(getattr(packet, "instrument_states", []) or [])
        mission_list = list(getattr(tasking_packet, "mission_command_contracts", []) or [])

        obs_by_entity_id: dict[int, dict[str, np.ndarray]] = {}
        for idx, ref in enumerate(refs):
            entity_id = int(getattr(ref, "entity_id", 0))
            truth = truth_list[idx] if idx < len(truth_list) else None
            inst = inst_list[idx] if idx < len(inst_list) else None
            mission_cmd = mission_list[idx] if idx < len(mission_list) else None
            if truth is None or inst is None:
                continue

            original_mission_cmd = getattr(self.loader, "mission_cmd", None)
            if mission_cmd is not None:
                self.loader.mission_cmd = _mission_command_view(mission_cmd)
            try:
                obs_by_entity_id[entity_id] = build_universal_observation(
                    self.loader,
                    inst,
                    truth,
                    mission_obs_mode=self.mission_obs_mode,
                    max_contacts=self.max_contacts,
                    max_rwr=self.max_rwr,
                    include_proprio=self.include_proprio,
                    last_action=None if not isinstance(last_actions, dict) else last_actions.get(entity_id),
                    action_space=self.action_space,
                    steps=None,
                    max_steps=None,
                )
            finally:
                if isinstance(original_mission_cmd, dict):
                    self.loader.mission_cmd = _clone_runtime_mission_command(original_mission_cmd)
                else:
                    self.loader.mission_cmd = original_mission_cmd
        return obs_by_entity_id

    def apply_actions(
        self,
        actions_by_entity_id: dict[int, Any],
        *,
        inst_by_entity_id: dict[int, Any] | None = None,
    ) -> list[Any]:
        assignments: list[Any] = []
        for slot in self.slots():
            if int(slot.entity_id) not in actions_by_entity_id:
                continue
            action = normalize_action(
                actions_by_entity_id[int(slot.entity_id)],
                action_space=self.action_space,
                action_mode=self.action_mode,
            )
            assign = ef_py.WorldPilotActionAssignment()
            assign.world_index = int(slot.world_index)
            assign.entity_id = int(slot.entity_id)
            assign.action = build_pilot_action(
                action,
                action_mode=self.action_mode,
                inst_now=None if not isinstance(inst_by_entity_id, dict) else inst_by_entity_id.get(int(slot.entity_id)),
            )
            assignments.append(assign)

        if assignments and hasattr(self.runtime, "set_pilot_actions_batch"):
            self.runtime.set_pilot_actions_batch(assignments)
        return assignments
