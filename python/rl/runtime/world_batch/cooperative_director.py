from __future__ import annotations

from copy import deepcopy
from typing import Any

import ef_py
import numpy as np

from .state import CooperativeSlotState, CooperativeWorldState


def count_control_slots(runtime_scenario: dict[str, Any]) -> int:
    roster_cfg = runtime_scenario.get("active_controllable_roster", None)
    if not isinstance(roster_cfg, dict):
        roster_cfg = runtime_scenario.get("cooperative_roster", None)
    if isinstance(roster_cfg, dict):
        members = roster_cfg.get("members", None)
        if isinstance(members, list) and members:
            count = 0
            for member in members:
                if not isinstance(member, dict):
                    continue
                if bool(member.get("is_agent", True)):
                    count += 1
            if count > 0:
                return int(count)

    entities = runtime_scenario.get("entities", None)
    if not isinstance(entities, list):
        return 0
    return sum(1 for entity in entities if isinstance(entity, dict) and bool(entity.get("is_agent", False)))


def mission_status_success_flag(mission_status: Any) -> bool:
    try:
        arr = np.asarray(mission_status, dtype=np.float32).reshape(-1)
    except Exception:
        return False
    return bool(arr.size >= 4 and float(arr[3]) > 0.5)


def clone_small_dict(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return deepcopy(value)


def _coerce_optional_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _coerce_optional_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _cooperative_roll_start_time(loader: Any) -> float:
    raw = getattr(loader, "_coop_takeoff_roll_start_time_s", None)
    if raw is None:
        return -1.0
    try:
        return float(raw)
    except Exception:
        return -1.0


def _enum_member(namespace: Any, raw_value: Any, default_value: Any) -> Any:
    if namespace is None:
        return default_value
    if raw_value is None:
        return default_value
    if isinstance(raw_value, str):
        return getattr(namespace, str(raw_value).strip(), default_value)
    try:
        return namespace(int(raw_value))
    except Exception:
        pass
    try:
        return int(raw_value)
    except Exception:
        return default_value


def _offset_triplet_from_spec(spec: Any, *, fallback: tuple[float, float, float]) -> tuple[float, float, float]:
    if isinstance(spec, dict):
        x = spec.get("form_offset_x", spec.get("offset_x", fallback[0]))
        y = spec.get("form_offset_y", spec.get("offset_y", fallback[1]))
        z = spec.get("form_offset_z", spec.get("offset_z", fallback[2]))
        return (
            _coerce_optional_float(x, fallback[0]),
            _coerce_optional_float(y, fallback[1]),
            _coerce_optional_float(z, fallback[2]),
        )
    if isinstance(spec, (list, tuple)) and len(spec) >= 3:
        return (
            _coerce_optional_float(spec[0], fallback[0]),
            _coerce_optional_float(spec[1], fallback[1]),
            _coerce_optional_float(spec[2], fallback[2]),
        )
    return tuple(float(v) for v in fallback)


_MISSING = object()


def _mapping_value_changed(mapping: dict[str, Any], key: str, value: Any) -> bool:
    current = mapping.get(key, _MISSING)
    if current is _MISSING:
        return True
    return current != value


def _assign_mapping_value(mapping: dict[str, Any], key: str, value: Any) -> bool:
    if not _mapping_value_changed(mapping, key, value):
        return False
    mapping[key] = value
    return True


def _assign_attr_if_present(obj: Any, attr: str, value: Any) -> bool:
    if obj is None or not hasattr(obj, attr):
        return False
    try:
        current = getattr(obj, attr)
    except Exception:
        current = _MISSING
    if current is not _MISSING and current == value:
        return False
    try:
        setattr(obj, attr, value)
    except Exception:
        return False
    return True


class ScriptedCooperativeCoordinationDirector:
    """
    World-level scripted coordination director for cooperative execution.

    The director keeps the cooperative world on the existing command-chain contract:
    it post-processes per-slot `mission_cmd` / `leader_intent` / `task_order` /
    `pilot_report` state, then the vec env flushes those objects with the existing
    batch sync path.
    """

    def reset(self, world_state: CooperativeWorldState, slot_states: list[CooperativeSlotState]) -> None:
        self.update(world_state, slot_states, force=True)

    def update(
        self,
        world_state: CooperativeWorldState,
        slot_states: list[CooperativeSlotState],
        *,
        force: bool = False,
    ) -> None:
        if not isinstance(slot_states, list) or not slot_states:
            return
        if not force and not bool(getattr(world_state, "director_dirty", True)):
            return
        overrides = dict(getattr(world_state, "leader_overrides", {}) or {})
        slot_state_by_entity_id = {int(slot_state.entity_id): slot_state for slot_state in slot_states}
        for slot_state in slot_states:
            self._apply_slot(
                world_state,
                slot_state,
                slot_state_by_entity_id=slot_state_by_entity_id,
                overrides=overrides,
            )
        world_state.director_dirty = False

    def _resolve_formation_command(
        self,
        world_state: CooperativeWorldState,
        slot_state: CooperativeSlotState,
        *,
        overrides: dict[str, Any] | None = None,
    ) -> tuple[int, float, float, float]:
        if overrides is None:
            overrides = dict(getattr(world_state, "leader_overrides", {}) or {})
        loader = slot_state.loader
        mission_cmd = getattr(loader, "mission_cmd", None)
        if not isinstance(mission_cmd, dict):
            mission_cmd = {}

        formation_id = _coerce_optional_int(
            overrides.get(
                "formation_id",
                overrides.get("formation_template_id", mission_cmd.get("formation_id", 0)),
            ),
            _coerce_optional_int(mission_cmd.get("formation_id", 0), 0),
        )
        base_offsets = (
            _coerce_optional_float(mission_cmd.get("form_offset_x", 0.0), 0.0),
            _coerce_optional_float(mission_cmd.get("form_offset_y", 0.0), 0.0),
            _coerce_optional_float(mission_cmd.get("form_offset_z", 0.0), 0.0),
        )

        if bool(overrides):
            for key in (
                "formation_offsets_by_entity",
                "formation_offsets_by_role",
                "formation_offsets_by_relative_slot_code",
                "formation_offsets_by_entity_id",
                "formation_offsets_by_index",
            ):
                mapping = overrides.get(key, None)
                if not isinstance(mapping, dict):
                    continue
                candidates = [
                    str(slot_state.control_slot.entity_name),
                    str(slot_state.entity_id),
                    str(slot_state.control_slot.formation_role_id or ""),
                    str(slot_state.control_slot.relative_slot_code or ""),
                    str(slot_state.local_slot_index),
                ]
                for candidate in candidates:
                    if candidate not in mapping:
                        continue
                    offset_triplet = _offset_triplet_from_spec(mapping[candidate], fallback=base_offsets)
                    return formation_id, offset_triplet[0], offset_triplet[1], offset_triplet[2]

        role_name = str(slot_state.control_slot.formation_role_id or "").strip().lower()
        reference_entity_id = slot_state.control_slot.reference_entity_id
        is_leader = (
            reference_entity_id is None
            or int(reference_entity_id) <= 0
            or int(reference_entity_id) == int(slot_state.entity_id)
            or role_name in {"elementlead", "leader", "lead"}
            or (slot_state.local_slot_index == 0 and role_name not in {"wingman", "trail", "support"})
        )

        if is_leader:
            leader_offsets = _offset_triplet_from_spec(
                {
                    "form_offset_x": overrides.get("leader_form_offset_x", 0.0),
                    "form_offset_y": overrides.get("leader_form_offset_y", 0.0),
                    "form_offset_z": overrides.get("leader_form_offset_z", 0.0),
                },
                fallback=(0.0, 0.0, 0.0),
            )
            return formation_id, leader_offsets[0], leader_offsets[1], leader_offsets[2]

        wingman_offsets = _offset_triplet_from_spec(
            {
                "form_offset_x": overrides.get(
                    "wingman_form_offset_x",
                    overrides.get("default_form_offset_x", base_offsets[0]),
                ),
                "form_offset_y": overrides.get(
                    "wingman_form_offset_y",
                    overrides.get("default_form_offset_y", base_offsets[1]),
                ),
                "form_offset_z": overrides.get(
                    "wingman_form_offset_z",
                    overrides.get("default_form_offset_z", base_offsets[2]),
                ),
            },
            fallback=base_offsets,
        )
        return formation_id, wingman_offsets[0], wingman_offsets[1], wingman_offsets[2]

    def _apply_role_metadata(self, slot_state: CooperativeSlotState) -> None:
        loader = slot_state.loader
        control_slot = slot_state.control_slot
        role_code = _coerce_optional_int(control_slot.role_code, 0)
        relative_slot_code = _coerce_optional_int(control_slot.relative_slot_code, 0)
        element_id = _coerce_optional_int(control_slot.element_id or control_slot.team_id, 0)
        formation_role_name = str(control_slot.formation_role_id or "").strip()
        leader_intent = getattr(loader, "leader_intent", None)

        task_order = getattr(loader, "task_order", None)
        if task_order is not None:
            if hasattr(task_order, "role_code"):
                _assign_attr_if_present(task_order, "role_code", int(role_code))
            if hasattr(task_order, "relative_slot_code"):
                _assign_attr_if_present(task_order, "relative_slot_code", int(relative_slot_code))
            if hasattr(task_order, "element_id") and element_id > 0:
                _assign_attr_if_present(task_order, "element_id", int(element_id))
            if hasattr(task_order, "lead_aircraft_id"):
                _assign_attr_if_present(
                    task_order,
                    "lead_aircraft_id",
                    int(
                        control_slot.reference_entity_id
                        if control_slot.reference_entity_id is not None
                        else slot_state.entity_id
                    ),
                )
            if hasattr(task_order, "formation_template_id"):
                _assign_attr_if_present(
                    task_order,
                    "formation_template_id",
                    int(
                        getattr(task_order, "formation_template_id", 0)
                        or getattr(leader_intent, "formation_id", 0)
                        or 0
                    ),
                )
            if hasattr(task_order, "formation_role_id") and formation_role_name and hasattr(ef_py, "FormationRole"):
                _assign_attr_if_present(
                    task_order,
                    "formation_role_id",
                    _enum_member(
                        ef_py.FormationRole,
                        formation_role_name,
                        getattr(task_order, "formation_role_id", getattr(ef_py.FormationRole, "Unspecified", 0)),
                    ),
                )

        if leader_intent is not None:
            if hasattr(leader_intent, "role_code"):
                _assign_attr_if_present(leader_intent, "role_code", int(role_code))
            if hasattr(leader_intent, "relative_slot_code"):
                _assign_attr_if_present(leader_intent, "relative_slot_code", int(relative_slot_code))
            if hasattr(leader_intent, "tactical_unit_id") and element_id > 0:
                _assign_attr_if_present(leader_intent, "tactical_unit_id", int(element_id))

        pilot_report = getattr(loader, "pilot_report", None)
        if pilot_report is not None:
            if hasattr(pilot_report, "role_code"):
                _assign_attr_if_present(pilot_report, "role_code", int(role_code))
            if hasattr(pilot_report, "element_id") and element_id > 0:
                _assign_attr_if_present(pilot_report, "element_id", int(element_id))
            if hasattr(pilot_report, "coordination_mode") and hasattr(task_order, "coordination_mode"):
                _assign_attr_if_present(pilot_report, "coordination_mode", getattr(task_order, "coordination_mode"))
            if hasattr(pilot_report, "formation_role_id") and formation_role_name and hasattr(ef_py, "FormationRole"):
                _assign_attr_if_present(
                    pilot_report,
                    "formation_role_id",
                    _enum_member(
                        ef_py.FormationRole,
                        formation_role_name,
                        getattr(pilot_report, "formation_role_id", getattr(ef_py.FormationRole, "Unspecified", 0)),
                    ),
                )

    def _resolve_takeoff_semantics(
        self,
        world_state: CooperativeWorldState,
        slot_state: CooperativeSlotState,
        *,
        slot_state_by_entity_id: dict[int, CooperativeSlotState] | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        loader = slot_state.loader
        control_slot = slot_state.control_slot
        mission_cmd = getattr(loader, "mission_cmd", None)
        if not isinstance(mission_cmd, dict):
            mission_cmd = {}
        if overrides is None:
            overrides = dict(getattr(world_state, "leader_overrides", {}) or {})

        result = {
            "takeoff_procedure_code": _coerce_optional_int(mission_cmd.get("takeoff_procedure_code", 0), 0),
            "takeoff_clearance_code": _coerce_optional_int(mission_cmd.get("takeoff_clearance_code", 0), 0),
            "takeoff_interval_s": _coerce_optional_float(mission_cmd.get("takeoff_interval_s", 0.0), 0.0),
            "runway_slot_code": _coerce_optional_int(mission_cmd.get("runway_slot_code", 0), 0),
        }

        member_cmd = clone_small_dict(getattr(control_slot, "mission_command_overrides", None)) or {}
        for key in ("takeoff_procedure_code", "takeoff_clearance_code", "takeoff_interval_s", "runway_slot_code"):
            if key in member_cmd:
                result[key] = member_cmd[key]

        for key in ("takeoff_procedure_code", "takeoff_interval_s"):
            if key in overrides:
                result[key] = overrides[key]

        role_name = str(control_slot.formation_role_id or "").strip().lower()
        entity_name = str(control_slot.entity_name or "")
        candidate_keys = [
            entity_name,
            str(slot_state.entity_id),
            str(control_slot.relative_slot_code or ""),
            str(control_slot.roster_index),
            str(control_slot.local_slot_index) if hasattr(control_slot, "local_slot_index") else "",
            str(control_slot.formation_role_id or ""),
        ]
        for key in ("takeoff_clearance_by_entity", "takeoff_clearance_by_role", "takeoff_clearance_by_relative_slot_code"):
            mapping = overrides.get(key, None)
            if not isinstance(mapping, dict):
                continue
            for candidate in candidate_keys:
                if candidate and candidate in mapping:
                    result["takeoff_clearance_code"] = mapping[candidate]
                    break

        for key in ("runway_slot_by_entity", "runway_slot_by_role", "runway_slot_by_relative_slot_code"):
            mapping = overrides.get(key, None)
            if not isinstance(mapping, dict):
                continue
            for candidate in candidate_keys:
                if candidate and candidate in mapping:
                    result["runway_slot_code"] = mapping[candidate]
                    break

        clearance_code = _coerce_optional_int(result.get("takeoff_clearance_code", 0), 0)
        interval_s = max(0.0, _coerce_optional_float(result.get("takeoff_interval_s", 0.0), 0.0))
        reference_entity_id = control_slot.reference_entity_id
        if interval_s > 0.0 and reference_entity_id is not None and int(reference_entity_id) > 0:
            release_clearance_code = overrides.get("takeoff_release_clearance_code", None)
            for key in (
                "takeoff_release_clearance_by_entity",
                "takeoff_release_clearance_by_role",
                "takeoff_release_clearance_by_relative_slot_code",
            ):
                mapping = overrides.get(key, None)
                if not isinstance(mapping, dict):
                    continue
                for candidate in candidate_keys:
                    if candidate and candidate in mapping:
                        release_clearance_code = mapping[candidate]
                        break
                if release_clearance_code is not None:
                    break
            if release_clearance_code is None:
                release_clearance_code = 3 if clearance_code <= 2 else clearance_code
            release_clearance_code = _coerce_optional_int(release_clearance_code, 3)
            reference_state = None if not isinstance(slot_state_by_entity_id, dict) else slot_state_by_entity_id.get(int(reference_entity_id))
            if reference_state is not None:
                ref_inst = getattr(reference_state, "last_inst", None)
                ref_loader = reference_state.loader
                ref_started = False
                ref_airborne = False
                if ref_inst is not None:
                    ref_ground_speed = float(getattr(ref_inst, "ground_speed", 0.0) or 0.0)
                    ref_alt_agl = float(getattr(ref_inst, "alt_radar", 0.0) or 0.0)
                    ref_started = ref_ground_speed >= 35.0
                    ref_airborne = ref_alt_agl >= 5.0
                ref_start_time = _cooperative_roll_start_time(ref_loader)
                if ref_started and ref_start_time < 0.0:
                    ref_start_time = float(reference_state.steps) * float(getattr(loader.sim, "get_time_step", lambda: 0.05)())
                    setattr(ref_loader, "_coop_takeoff_roll_start_time_s", ref_start_time)
                current_time = float(slot_state.steps) * float(getattr(loader.sim, "get_time_step", lambda: 0.05)())
                gate_open = False
                if ref_airborne:
                    gate_open = True
                elif ref_start_time >= 0.0 and current_time >= ref_start_time + interval_s:
                    gate_open = True
                if gate_open:
                    result["takeoff_clearance_code"] = int(release_clearance_code)
                elif clearance_code in (3, 4, 5):
                    result["takeoff_clearance_code"] = 1 if role_name not in {"elementlead", "leader", "lead"} else clearance_code

        return {
            "takeoff_procedure_code": _coerce_optional_int(result.get("takeoff_procedure_code", 0), 0),
            "takeoff_clearance_code": _coerce_optional_int(result.get("takeoff_clearance_code", 0), 0),
            "takeoff_interval_s": max(0.0, _coerce_optional_float(result.get("takeoff_interval_s", 0.0), 0.0)),
            "runway_slot_code": _coerce_optional_int(result.get("runway_slot_code", 0), 0),
        }

    def _apply_slot(
        self,
        world_state: CooperativeWorldState,
        slot_state: CooperativeSlotState,
        *,
        slot_state_by_entity_id: dict[int, CooperativeSlotState] | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> None:
        loader = slot_state.loader
        if loader is None:
            return
        if overrides is None:
            overrides = dict(getattr(world_state, "leader_overrides", {}) or {})
        formation_id, form_offset_x, form_offset_y, form_offset_z = self._resolve_formation_command(
            world_state,
            slot_state,
            overrides=overrides,
        )
        takeoff_semantics = self._resolve_takeoff_semantics(
            world_state,
            slot_state,
            slot_state_by_entity_id=slot_state_by_entity_id,
            overrides=overrides,
        )
        mission_cmd = getattr(loader, "mission_cmd", None)
        if not isinstance(mission_cmd, dict):
            mission_cmd = {}
            loader.mission_cmd = mission_cmd
        mission_changed = False
        mission_changed |= _assign_mapping_value(mission_cmd, "formation_id", int(formation_id))
        mission_changed |= _assign_mapping_value(mission_cmd, "form_offset_x", float(form_offset_x))
        mission_changed |= _assign_mapping_value(mission_cmd, "form_offset_y", float(form_offset_y))
        mission_changed |= _assign_mapping_value(mission_cmd, "form_offset_z", float(form_offset_z))
        mission_changed |= _assign_mapping_value(
            mission_cmd,
            "takeoff_procedure_code",
            int(takeoff_semantics["takeoff_procedure_code"]),
        )
        mission_changed |= _assign_mapping_value(
            mission_cmd,
            "takeoff_clearance_code",
            int(takeoff_semantics["takeoff_clearance_code"]),
        )
        mission_changed |= _assign_mapping_value(
            mission_cmd,
            "takeoff_interval_s",
            float(takeoff_semantics["takeoff_interval_s"]),
        )
        mission_changed |= _assign_mapping_value(
            mission_cmd,
            "runway_slot_code",
            int(takeoff_semantics["runway_slot_code"]),
        )
        scenario_data = getattr(loader, "scenario_data", None)
        if mission_changed and isinstance(scenario_data, dict):
            scenario_data["mission_command"] = mission_cmd

        task_order = getattr(loader, "task_order", None)
        if task_order is not None:
            member_task = getattr(slot_state.control_slot, "task_order_overrides", None)
            if isinstance(member_task, dict):
                from python.rl.tasking.leader_tasking import _apply_task_order_overrides

                _apply_task_order_overrides(
                    task_order,
                    member_task,
                    default_assignee_id=int(slot_state.entity_id),
                )
            if hasattr(task_order, "takeoff_procedure_id"):
                _assign_attr_if_present(
                    task_order,
                    "takeoff_procedure_id",
                    _enum_member(
                    getattr(ef_py, "TakeoffProcedureType", None),
                    takeoff_semantics["takeoff_procedure_code"],
                    getattr(task_order, "takeoff_procedure_id", 0),
                )
                )
            if hasattr(task_order, "takeoff_clearance_id"):
                _assign_attr_if_present(
                    task_order,
                    "takeoff_clearance_id",
                    _enum_member(
                    getattr(ef_py, "TakeoffClearanceState", None),
                    takeoff_semantics["takeoff_clearance_code"],
                    getattr(task_order, "takeoff_clearance_id", 0),
                )
                )
            if hasattr(task_order, "takeoff_interval_s"):
                _assign_attr_if_present(task_order, "takeoff_interval_s", float(takeoff_semantics["takeoff_interval_s"]))
            if hasattr(task_order, "runway_slot_id"):
                _assign_attr_if_present(
                    task_order,
                    "runway_slot_id",
                    _enum_member(
                    getattr(ef_py, "RunwaySlotPosition", None),
                    takeoff_semantics["runway_slot_code"],
                    getattr(task_order, "runway_slot_id", 0),
                )
                )

        leader_intent = getattr(loader, "leader_intent", None)
        if leader_intent is not None:
            if hasattr(leader_intent, "formation_id"):
                _assign_attr_if_present(leader_intent, "formation_id", int(formation_id))
            if hasattr(leader_intent, "form_offset_x"):
                _assign_attr_if_present(leader_intent, "form_offset_x", float(form_offset_x))
            if hasattr(leader_intent, "form_offset_y"):
                _assign_attr_if_present(leader_intent, "form_offset_y", float(form_offset_y))
            if hasattr(leader_intent, "form_offset_z"):
                _assign_attr_if_present(leader_intent, "form_offset_z", float(form_offset_z))
            if hasattr(leader_intent, "takeoff_procedure_id"):
                _assign_attr_if_present(
                    leader_intent,
                    "takeoff_procedure_id",
                    _enum_member(
                    getattr(ef_py, "TakeoffProcedureType", None),
                    takeoff_semantics["takeoff_procedure_code"],
                    getattr(leader_intent, "takeoff_procedure_id", 0),
                )
                )
            if hasattr(leader_intent, "takeoff_clearance_id"):
                _assign_attr_if_present(
                    leader_intent,
                    "takeoff_clearance_id",
                    _enum_member(
                    getattr(ef_py, "TakeoffClearanceState", None),
                    takeoff_semantics["takeoff_clearance_code"],
                    getattr(leader_intent, "takeoff_clearance_id", 0),
                )
                )
            if hasattr(leader_intent, "takeoff_interval_s"):
                _assign_attr_if_present(
                    leader_intent,
                    "takeoff_interval_s",
                    float(takeoff_semantics["takeoff_interval_s"]),
                )
            if hasattr(leader_intent, "runway_slot_id"):
                _assign_attr_if_present(
                    leader_intent,
                    "runway_slot_id",
                    _enum_member(
                    getattr(ef_py, "RunwaySlotPosition", None),
                    takeoff_semantics["runway_slot_code"],
                    getattr(leader_intent, "runway_slot_id", 0),
                )
                )

        inst = getattr(slot_state, "last_inst", None)
        if inst is not None:
            ground_speed = float(getattr(inst, "ground_speed", 0.0) or 0.0)
            alt_agl = float(getattr(inst, "alt_radar", 0.0) or 0.0)
            current_time = float(slot_state.steps) * float(getattr(loader.sim, "get_time_step", lambda: 0.05)())
            clearance_code = int(takeoff_semantics["takeoff_clearance_code"])
            if clearance_code in (3, 4, 5) and ground_speed >= 35.0 and _cooperative_roll_start_time(loader) < 0.0:
                setattr(loader, "_coop_takeoff_roll_start_time_s", current_time)
            if clearance_code == 3 and ground_speed >= 35.0:
                mission_changed |= _assign_mapping_value(mission_cmd, "takeoff_clearance_code", 4)
            if mission_cmd.get("takeoff_clearance_code", 0) in (3, 4) and alt_agl >= 5.0:
                mission_changed |= _assign_mapping_value(mission_cmd, "takeoff_clearance_code", 5)
            if mission_changed and isinstance(scenario_data, dict):
                scenario_data["mission_command"] = mission_cmd

        self._apply_role_metadata(slot_state)


__all__ = [
    "ScriptedCooperativeCoordinationDirector",
    "clone_small_dict",
    "count_control_slots",
    "mission_status_success_flag",
]
