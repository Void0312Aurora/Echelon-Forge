from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any
import os
import time
import warnings

import numpy as np

try:
    import gymnasium as gym
except ModuleNotFoundError:  # pragma: no cover
    gym = None

import ef_py

from gym_envs.scenario_loader import (
    ScenarioLoader,
    normalize_execution_step_runtime_mode,
    normalize_flight_shaping_backend,
)
from gym_envs.universal_env import (
    build_step_info,
    build_step_info_minimal,
    build_universal_observation,
    downsample_visual_mean,
    make_action_space,
    make_observation_space,
    normalize_action,
)
from python.rl.leader_tasking import build_kernel_mission_command
from python.rl.multi_agent_runtime import MultiAgentControlSlot, MultiAgentWorldRuntimeView
from python.rl.sb3_vec_env_compat import (
    VecEnv,
    VecEnvIndices,
    VecEnvObs,
    VecEnvStepReturn,
    dict_to_obs,
    obs_space_info,
)
from python.rl.world_batch_vec_env import (
    _RuntimeFacadeAdapter,
    _normalize_batch_observation_backend,
    _normalize_batch_visual_backend,
)
from python.rl.wrappers import MultiTimescaleActionController
from python.scenario_compiler import ScenarioCompiler
from python.scenario_runtime import apply_world_layout_to_kernel, build_compiled_world_layout


def _copy_obs(obs: Any) -> Any:
    if isinstance(obs, dict):
        return {key: _copy_obs(value) for key, value in obs.items()}
    if isinstance(obs, tuple):
        return tuple(_copy_obs(value) for value in obs)
    return np.array(obs, copy=True)


def _count_control_slots(runtime_scenario: dict[str, Any]) -> int:
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


@dataclass
class _CooperativeWorldState:
    world_index: int
    randomization_overrides: dict[str, Any] = field(default_factory=dict)
    leader_overrides: dict[str, Any] = field(default_factory=dict)
    director: ScriptedCooperativeCoordinationDirector | None = None
    routing_loader: ScenarioLoader | None = None
    view: MultiAgentWorldRuntimeView | None = None
    slot_indices: list[int] = field(default_factory=list)
    director_dirty: bool = True

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        if overrides is None:
            self.randomization_overrides = {}
            return
        if not isinstance(overrides, dict):
            raise TypeError(f"randomization overrides must be a dict or None, got {type(overrides)}")
        self.randomization_overrides = dict(overrides)

    def set_leader_overrides(self, overrides: dict | None) -> None:
        if overrides is None:
            self.leader_overrides = {}
            self.director_dirty = True
            return
        if not isinstance(overrides, dict):
            raise TypeError(f"leader overrides must be a dict or None, got {type(overrides)}")
        self.leader_overrides = dict(overrides)
        self.director_dirty = True


@dataclass
class _CooperativeSlotState:
    slot_index: int
    local_slot_index: int
    world: _CooperativeWorldState
    control_slot: MultiAgentControlSlot
    loader: ScenarioLoader
    max_steps: int
    steps: int = 0
    last_action: np.ndarray | None = None
    last_inst: Any = None
    last_truth: Any = None
    last_obs: dict[str, np.ndarray] | None = None
    episode_return: float = 0.0
    episode_length: int = 0
    visual_cache: np.ndarray | None = None
    visual_cache_step: int = -1
    action_controller: MultiTimescaleActionController | None = None
    coop_success_latched: bool = False
    coop_completion_reason: str = ""
    coop_completion_mission_status: np.ndarray | None = None
    coop_completion_info: dict[str, Any] | None = None
    coop_completion_terminal_observation: dict[str, np.ndarray] | None = None

    @property
    def world_index(self) -> int:
        return int(self.world.world_index)

    @property
    def entity_id(self) -> int:
        return int(self.control_slot.entity_id)

    @property
    def entity_name(self) -> str:
        return str(self.control_slot.entity_name)

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        self.world.set_randomization_overrides(overrides)


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


def _mission_status_success_flag(mission_status: Any) -> bool:
    try:
        arr = np.asarray(mission_status, dtype=np.float32).reshape(-1)
    except Exception:
        return False
    return bool(arr.size >= 4 and float(arr[3]) > 0.5)


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


def _clone_small_dict(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return deepcopy(value)


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


class ScriptedCooperativeCoordinationDirector:
    """
    World-level scripted coordination director for cooperative execution.

    The director keeps the cooperative world on the existing command-chain contract:
    it post-processes per-slot `mission_cmd` / `leader_intent` / `task_order` /
    `pilot_report` state, then the vec env flushes those objects with the existing
    batch sync path.
    """

    def reset(self, world_state: _CooperativeWorldState, slot_states: list[_CooperativeSlotState]) -> None:
        self.update(world_state, slot_states, force=True)

    def update(
        self,
        world_state: _CooperativeWorldState,
        slot_states: list[_CooperativeSlotState],
        *,
        force: bool = False,
    ) -> None:
        if not isinstance(slot_states, list) or not slot_states:
            return
        if not force and not bool(getattr(world_state, "director_dirty", True)):
            return
        slot_state_by_entity_id = {int(slot_state.entity_id): slot_state for slot_state in slot_states}
        for slot_state in slot_states:
            self._apply_slot(world_state, slot_state, slot_state_by_entity_id=slot_state_by_entity_id)
        world_state.director_dirty = False

    def _resolve_formation_command(
        self,
        world_state: _CooperativeWorldState,
        slot_state: _CooperativeSlotState,
    ) -> tuple[int, float, float, float]:
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

    def _apply_role_metadata(self, slot_state: _CooperativeSlotState) -> None:
        loader = slot_state.loader
        control_slot = slot_state.control_slot
        role_code = _coerce_optional_int(control_slot.role_code, 0)
        relative_slot_code = _coerce_optional_int(control_slot.relative_slot_code, 0)
        element_id = _coerce_optional_int(control_slot.element_id or control_slot.team_id, 0)
        formation_role_name = str(control_slot.formation_role_id or "").strip()

        task_order = getattr(loader, "task_order", None)
        if task_order is not None:
            if hasattr(task_order, "role_code"):
                task_order.role_code = int(role_code)
            if hasattr(task_order, "relative_slot_code"):
                task_order.relative_slot_code = int(relative_slot_code)
            if hasattr(task_order, "element_id") and element_id > 0:
                task_order.element_id = int(element_id)
            if hasattr(task_order, "lead_aircraft_id"):
                task_order.lead_aircraft_id = int(
                    control_slot.reference_entity_id if control_slot.reference_entity_id is not None else slot_state.entity_id
                )
            if hasattr(task_order, "formation_template_id"):
                task_order.formation_template_id = int(
                    getattr(task_order, "formation_template_id", 0) or getattr(loader.leader_intent, "formation_id", 0) or 0
                )
            if hasattr(task_order, "formation_role_id") and formation_role_name and hasattr(ef_py, "FormationRole"):
                task_order.formation_role_id = _enum_member(
                    ef_py.FormationRole,
                    formation_role_name,
                    getattr(task_order, "formation_role_id", getattr(ef_py.FormationRole, "Unspecified", 0)),
                )

        leader_intent = getattr(loader, "leader_intent", None)
        if leader_intent is not None:
            if hasattr(leader_intent, "role_code"):
                leader_intent.role_code = int(role_code)
            if hasattr(leader_intent, "relative_slot_code"):
                leader_intent.relative_slot_code = int(relative_slot_code)
            if hasattr(leader_intent, "tactical_unit_id") and element_id > 0:
                leader_intent.tactical_unit_id = int(element_id)

        pilot_report = getattr(loader, "pilot_report", None)
        if pilot_report is not None:
            if hasattr(pilot_report, "role_code"):
                pilot_report.role_code = int(role_code)
            if hasattr(pilot_report, "element_id") and element_id > 0:
                pilot_report.element_id = int(element_id)
            if hasattr(pilot_report, "coordination_mode") and hasattr(task_order, "coordination_mode"):
                pilot_report.coordination_mode = getattr(task_order, "coordination_mode")
            if hasattr(pilot_report, "formation_role_id") and formation_role_name and hasattr(ef_py, "FormationRole"):
                pilot_report.formation_role_id = _enum_member(
                    ef_py.FormationRole,
                    formation_role_name,
                    getattr(pilot_report, "formation_role_id", getattr(ef_py.FormationRole, "Unspecified", 0)),
                )

    def _resolve_takeoff_semantics(
        self,
        world_state: _CooperativeWorldState,
        slot_state: _CooperativeSlotState,
        *,
        slot_state_by_entity_id: dict[int, _CooperativeSlotState] | None = None,
    ) -> dict[str, Any]:
        loader = slot_state.loader
        control_slot = slot_state.control_slot
        mission_cmd = getattr(loader, "mission_cmd", None)
        if not isinstance(mission_cmd, dict):
            mission_cmd = {}
        overrides = dict(getattr(world_state, "leader_overrides", {}) or {})

        result = {
            "takeoff_procedure_code": _coerce_optional_int(mission_cmd.get("takeoff_procedure_code", 0), 0),
            "takeoff_clearance_code": _coerce_optional_int(mission_cmd.get("takeoff_clearance_code", 0), 0),
            "takeoff_interval_s": _coerce_optional_float(mission_cmd.get("takeoff_interval_s", 0.0), 0.0),
            "runway_slot_code": _coerce_optional_int(mission_cmd.get("runway_slot_code", 0), 0),
        }

        member_cmd = _clone_small_dict(getattr(control_slot, "mission_command_overrides", None)) or {}
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
        world_state: _CooperativeWorldState,
        slot_state: _CooperativeSlotState,
        *,
        slot_state_by_entity_id: dict[int, _CooperativeSlotState] | None = None,
    ) -> None:
        loader = slot_state.loader
        if loader is None:
            return
        formation_id, form_offset_x, form_offset_y, form_offset_z = self._resolve_formation_command(world_state, slot_state)
        takeoff_semantics = self._resolve_takeoff_semantics(
            world_state,
            slot_state,
            slot_state_by_entity_id=slot_state_by_entity_id,
        )
        mission_cmd = getattr(loader, "mission_cmd", None)
        if not isinstance(mission_cmd, dict):
            mission_cmd = {}
        mission_cmd = dict(mission_cmd)
        mission_cmd["formation_id"] = int(formation_id)
        mission_cmd["form_offset_x"] = float(form_offset_x)
        mission_cmd["form_offset_y"] = float(form_offset_y)
        mission_cmd["form_offset_z"] = float(form_offset_z)
        mission_cmd["takeoff_procedure_code"] = int(takeoff_semantics["takeoff_procedure_code"])
        mission_cmd["takeoff_clearance_code"] = int(takeoff_semantics["takeoff_clearance_code"])
        mission_cmd["takeoff_interval_s"] = float(takeoff_semantics["takeoff_interval_s"])
        mission_cmd["runway_slot_code"] = int(takeoff_semantics["runway_slot_code"])
        loader.mission_cmd = mission_cmd
        if isinstance(getattr(loader, "scenario_data", None), dict):
            loader.scenario_data["mission_command"] = loader.mission_cmd

        task_order = getattr(loader, "task_order", None)
        if task_order is not None:
            member_task = getattr(slot_state.control_slot, "task_order_overrides", None)
            if isinstance(member_task, dict):
                from python.rl.leader_tasking import _apply_task_order_overrides

                _apply_task_order_overrides(
                    task_order,
                    member_task,
                    default_assignee_id=int(slot_state.entity_id),
                )
            if hasattr(task_order, "takeoff_procedure_id"):
                task_order.takeoff_procedure_id = _enum_member(
                    getattr(ef_py, "TakeoffProcedureType", None),
                    takeoff_semantics["takeoff_procedure_code"],
                    getattr(task_order, "takeoff_procedure_id", 0),
                )
            if hasattr(task_order, "takeoff_clearance_id"):
                task_order.takeoff_clearance_id = _enum_member(
                    getattr(ef_py, "TakeoffClearanceState", None),
                    takeoff_semantics["takeoff_clearance_code"],
                    getattr(task_order, "takeoff_clearance_id", 0),
                )
            if hasattr(task_order, "takeoff_interval_s"):
                task_order.takeoff_interval_s = float(takeoff_semantics["takeoff_interval_s"])
            if hasattr(task_order, "runway_slot_id"):
                task_order.runway_slot_id = _enum_member(
                    getattr(ef_py, "RunwaySlotPosition", None),
                    takeoff_semantics["runway_slot_code"],
                    getattr(task_order, "runway_slot_id", 0),
                )

        leader_intent = getattr(loader, "leader_intent", None)
        if leader_intent is not None:
            if hasattr(leader_intent, "formation_id"):
                leader_intent.formation_id = int(formation_id)
            if hasattr(leader_intent, "form_offset_x"):
                leader_intent.form_offset_x = float(form_offset_x)
            if hasattr(leader_intent, "form_offset_y"):
                leader_intent.form_offset_y = float(form_offset_y)
            if hasattr(leader_intent, "form_offset_z"):
                leader_intent.form_offset_z = float(form_offset_z)
            if hasattr(leader_intent, "takeoff_procedure_id"):
                leader_intent.takeoff_procedure_id = _enum_member(
                    getattr(ef_py, "TakeoffProcedureType", None),
                    takeoff_semantics["takeoff_procedure_code"],
                    getattr(leader_intent, "takeoff_procedure_id", 0),
                )
            if hasattr(leader_intent, "takeoff_clearance_id"):
                leader_intent.takeoff_clearance_id = _enum_member(
                    getattr(ef_py, "TakeoffClearanceState", None),
                    takeoff_semantics["takeoff_clearance_code"],
                    getattr(leader_intent, "takeoff_clearance_id", 0),
                )
            if hasattr(leader_intent, "takeoff_interval_s"):
                leader_intent.takeoff_interval_s = float(takeoff_semantics["takeoff_interval_s"])
            if hasattr(leader_intent, "runway_slot_id"):
                leader_intent.runway_slot_id = _enum_member(
                    getattr(ef_py, "RunwaySlotPosition", None),
                    takeoff_semantics["runway_slot_code"],
                    getattr(leader_intent, "runway_slot_id", 0),
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
                mission_cmd["takeoff_clearance_code"] = 4
            if mission_cmd.get("takeoff_clearance_code", 0) in (3, 4) and alt_agl >= 5.0:
                mission_cmd["takeoff_clearance_code"] = 5
            loader.mission_cmd = mission_cmd
            if isinstance(getattr(loader, "scenario_data", None), dict):
                loader.scenario_data["mission_command"] = loader.mission_cmd

        self._apply_role_metadata(slot_state)

class CooperativeWorldBatchVecEnv(VecEnv):
    """
    Multi-agent execution VecEnv for worlds that expose multiple controllable roster members.

    SB3 still sees a flat VecEnv of execution slots, while each slot actually belongs to a
    shared simulation world. All slots in the same world step together and reset together.
    """

    def __init__(
        self,
        *,
        scenario_path: str,
        n_envs: int,
        render_mode: str | None = None,
        include_visual: bool = False,
        include_proprio: bool = False,
        action_mode: str = "full",
        mission_obs_mode: str = "basic",
        visual_downsample: int = 1,
        visual_update_interval: int = 1,
        batch_observation_backend: str | None = "auto",
        batch_visual_backend: str | None = "auto",
        step_info_mode: str = "full",
        execution_step_runtime_mode: str | None = None,
        flight_shaping_backend: str | None = None,
        collect_step_timing: bool = False,
        database_path: str | None = None,
        worker_threads: int | None = None,
        action_wrapper_kwargs: dict[str, Any] | None = None,
    ) -> None:
        if gym is None:  # pragma: no cover
            raise ModuleNotFoundError(
                "CooperativeWorldBatchVecEnv requires the optional dependency 'gymnasium'. "
                "Install it (e.g. `pip install gymnasium`) to run RL training."
            )
        if render_mode not in (None,):
            raise ValueError("CooperativeWorldBatchVecEnv currently only supports render_mode=None.")
        self.scenario_path = os.path.abspath(str(scenario_path))
        self.world_count = max(1, int(n_envs))
        self.render_mode = render_mode
        self.include_visual = bool(include_visual)
        self.include_proprio = bool(include_proprio)
        self.action_mode = str(action_mode)
        self.mission_obs_mode = str(mission_obs_mode).strip().lower()
        self.visual_downsample = max(1, int(visual_downsample))
        self.visual_update_interval = max(1, int(visual_update_interval))
        self.batch_observation_backend = _normalize_batch_observation_backend(batch_observation_backend)
        self.batch_visual_backend = _normalize_batch_visual_backend(batch_visual_backend)
        self.step_info_mode = str(step_info_mode).strip().lower()
        self.execution_step_runtime_mode = (
            normalize_execution_step_runtime_mode(execution_step_runtime_mode)
            if execution_step_runtime_mode is not None
            else None
        )
        self.flight_shaping_backend = _normalize_flight_shaping_backend(flight_shaping_backend)
        self.collect_step_timing = bool(collect_step_timing)
        self._action_wrapper_kwargs = dict(action_wrapper_kwargs or {})
        if self.step_info_mode not in ("full", "terminal", "off"):
            raise ValueError(f"Unknown step_info_mode: {step_info_mode!r}")

        self._compiled_scenario = ScenarioCompiler.compile_path(self.scenario_path)
        runtime_context = self._compiled_scenario.instantiate_runtime_context()
        self.slots_per_world = int(_count_control_slots(runtime_context))
        if self.slots_per_world <= 0:
            raise RuntimeError(
                "cooperative execution requires at least one controllable roster member in the scenario"
            )

        self.num_slots = int(self.world_count) * int(self.slots_per_world)
        self._db_path = (
            os.path.abspath(database_path)
            if database_path
            else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "examples", "config", "database"))
        )
        self._runtime_adapter = _RuntimeFacadeAdapter(self.world_count)
        self._worker_threads = None if worker_threads is None else max(0, int(worker_threads))
        if self._worker_threads is not None:
            self._runtime_adapter.set_worker_threads(int(self._worker_threads))
        if not bool(self._runtime_adapter.load_database(self._db_path)):
            raise RuntimeError(f"failed to load database into RuntimeFacade: {self._db_path}")

        self.action_space = make_action_space(self.action_mode)
        self.max_contacts = 10
        self.max_rwr = 4
        self.obs_size = 42
        self.arb_height_native = 48
        self.arb_width_native = 96
        self.arb_channels = 10
        if self.arb_height_native % self.visual_downsample != 0 or self.arb_width_native % self.visual_downsample != 0:
            raise ValueError(
                f"visual_downsample={self.visual_downsample} must divide {self.arb_height_native}x{self.arb_width_native}"
            )
        self.arb_height = self.arb_height_native // self.visual_downsample
        self.arb_width = self.arb_width_native // self.visual_downsample
        self.observation_space = make_observation_space(
            action_space=self.action_space,
            mission_obs_mode=self.mission_obs_mode,
            include_visual=self.include_visual,
            include_proprio=self.include_proprio,
            arb_height=self.arb_height,
            arb_width=self.arb_width,
            arb_channels=self.arb_channels,
            obs_size=self.obs_size,
            max_contacts=self.max_contacts,
            max_rwr=self.max_rwr,
        )

        self._worlds = [
            _CooperativeWorldState(
                world_index=world_index,
                director=ScriptedCooperativeCoordinationDirector(),
            )
            for world_index in range(self.world_count)
        ]
        self._slots: list[_CooperativeSlotState | None] = [None for _ in range(self.num_slots)]
        self._actions: np.ndarray | None = None
        self._closed = False

        super().__init__(self.num_slots, self.observation_space, self.action_space)

        self.keys, shapes, dtypes = obs_space_info(self.observation_space)
        self.buf_obs = OrderedDict(
            [(key, np.zeros((self.num_envs, *tuple(shapes[key])), dtype=dtypes[key])) for key in self.keys]
        )
        self.buf_dones = np.zeros((self.num_envs,), dtype=bool)
        self.buf_rews = np.zeros((self.num_envs,), dtype=np.float32)
        self.buf_infos: list[dict[str, Any]] = [{} for _ in range(self.num_envs)]
        self.last_step_timing: dict[str, float] = {}
        self.last_reset_timing: dict[str, float] = {}
        self.last_observation_build_timing: dict[str, float] = {}

    @property
    def batch_runtime(self):
        return self._runtime_adapter

    @property
    def runtime_facade(self):
        return self._runtime_adapter.facade

    def set_randomization_overrides(self, overrides: dict | None) -> None:
        for world in self._worlds:
            world.set_randomization_overrides(overrides)

    def set_leader_overrides(self, overrides: dict | None) -> None:
        for world in self._worlds:
            world.set_leader_overrides(overrides)

    def _batch_observation_backend_mode(self) -> str:
        if self.batch_observation_backend == "auto":
            return "legacy"
        return self.batch_observation_backend

    def _batch_visual_backend_mode(self) -> str:
        if self.batch_visual_backend == "auto":
            return "compiled" if hasattr(ef_py, "compute_world_batch_visual_observation_batch_numpy") else "legacy"
        return self.batch_visual_backend

    def _slot_refs(self, slot_indices: list[int]) -> list[Any]:
        refs: list[Any] = []
        for slot_index in slot_indices:
            slot_state = self._slots[int(slot_index)]
            if slot_state is None:
                continue
            ref = ef_py.WorldEntityRef()
            ref.world_index = int(slot_state.world_index)
            ref.entity_id = int(slot_state.entity_id)
            refs.append(ref)
        return refs

    def seed(self, seed: int | None = None) -> list[int]:
        base_seed = int(seed) if seed is not None else int(np.random.randint(0, 2**31 - 1))
        seeds: list[int] = []
        for world_index in range(self.world_count):
            world_seed = int(base_seed + world_index)
            seeds.extend([world_seed] * self.slots_per_world)
        self._seeds = list(seeds)
        return list(seeds)

    def _normalize_seed(self, seed: int | None) -> int:
        if seed is None:
            seed = int(np.random.randint(0, np.iinfo(np.uint32).max, dtype=np.uint32))
        return int(seed) & 0xFFFFFFFF

    def _build_slot_loader(self, world_index: int, prepared_world, entity_id: int, seed: int) -> ScenarioLoader:
        loader = ScenarioLoader(self._runtime_adapter.world(world_index))
        loader._compiled_scenario = self._compiled_scenario
        loader._compiled_runtime_metadata = self._compiled_scenario.runtime_metadata
        loader._scenario_source_path = self.scenario_path
        if self.execution_step_runtime_mode is not None:
            loader.set_execution_step_runtime_mode(self.execution_step_runtime_mode)
        loader.set_flight_shaping_backend(self.flight_shaping_backend)
        layout = getattr(prepared_world, "layout", None)
        entities = dict(getattr(prepared_world, "entities", {}) or {})
        active_roster = list(getattr(prepared_world, "active_roster", []) or [])

        loader._prepare_load_seed(seed)
        # Each slot loader must own an isolated runtime scenario copy.
        # Cooperative slots live in the same world and share kernel state, but they should not
        # mutate one another's route randomization / mission-command dictionaries through a shared
        # Python object graph during reset/finalize.
        loader._begin_loaded_world(scenario_data=deepcopy(layout.scenario_data))
        loader.rotate_mission_heading_with_world = bool(getattr(layout, "rotate_mission_heading_with_world", False))
        loader.world_yaw_deg = float(getattr(layout, "world_yaw_deg", 0.0))
        loader.world_yaw_origin_x = float(getattr(layout, "world_yaw_origin_x", 0.0))
        loader.world_yaw_origin_y = float(getattr(layout, "world_yaw_origin_y", 0.0))
        loader.entities = entities
        loader.active_roster = active_roster
        loader.agent_id = int(entity_id)
        loader._finalize_loaded_world(sync_to_kernel=True)
        return loader

    def _build_slot_state(
        self,
        *,
        slot_index: int,
        local_slot_index: int,
        world: _CooperativeWorldState,
        control_slot: MultiAgentControlSlot,
        loader: ScenarioLoader,
    ) -> _CooperativeSlotState:
        slot_state = _CooperativeSlotState(
            slot_index=int(slot_index),
            local_slot_index=int(local_slot_index),
            world=world,
            control_slot=control_slot,
            loader=loader,
            max_steps=int(loader.get_max_steps()),
        )
        if self._action_wrapper_kwargs:
            slot_state.action_controller = MultiTimescaleActionController(
                action_space=self.action_space,
                loader_getter=lambda loader=loader: loader,
                dt_getter=lambda loader=loader: float(loader.sim.get_time_step()),
                **self._action_wrapper_kwargs,
            )
        return slot_state

    def _refresh_visual_batch(self, indices: list[int] | None = None) -> None:
        if not self.include_visual:
            return
        target_indices = list(range(self.num_slots)) if indices is None else [int(i) for i in indices]
        refresh_indices: list[int] = []
        refs: list[Any] = []
        for slot_index in target_indices:
            slot_state = self._slots[int(slot_index)]
            if slot_state is None:
                continue
            need_refresh = (
                slot_state.visual_cache is None
                or self.visual_update_interval <= 1
                or slot_state.steps <= 0
                or (int(slot_state.steps) - int(slot_state.visual_cache_step)) >= self.visual_update_interval
            )
            if not need_refresh:
                continue
            refresh_indices.append(int(slot_index))
            ref = ef_py.WorldEntityRef()
            ref.world_index = int(slot_state.world_index)
            ref.entity_id = int(slot_state.entity_id)
            refs.append(ref)

        if not refresh_indices:
            return

        backend = self._batch_visual_backend_mode()
        if backend == "legacy" or not hasattr(ef_py, "compute_world_batch_visual_observation_batch_numpy"):
            for slot_index in refresh_indices:
                slot_state = self._slots[int(slot_index)]
                if slot_state is None:
                    continue
                world = self._runtime_adapter.world(slot_state.world_index)
                if self.visual_downsample > 1 and hasattr(world, "get_visual_observation_downsampled"):
                    visual_raw = world.get_visual_observation_downsampled(int(slot_state.entity_id), self.visual_downsample)
                    visual = np.asarray(visual_raw, dtype=np.float32)
                    if visual.ndim == 1:
                        visual = visual.reshape(self.arb_height, self.arb_width, self.arb_channels)
                    slot_state.visual_cache = visual
                else:
                    visual_raw = world.get_visual_observation(int(slot_state.entity_id))
                    visual = np.asarray(visual_raw, dtype=np.float32)
                    if visual.ndim == 1:
                        visual = visual.reshape(self.arb_height_native, self.arb_width_native, self.arb_channels)
                    slot_state.visual_cache = downsample_visual_mean(visual, self.visual_downsample)
                slot_state.visual_cache_step = int(slot_state.steps)
            return

        visuals = self._runtime_adapter.compute_visual_observation_batch_numpy(
            refs,
            int(self.visual_downsample),
            backend == "gpu_host",
        )
        visuals = np.asarray(visuals, dtype=np.float32)
        for batch_idx, slot_index in enumerate(refresh_indices):
            slot_state = self._slots[int(slot_index)]
            if slot_state is None:
                continue
            slot_state.visual_cache = np.asarray(visuals[batch_idx], dtype=np.float32)
            slot_state.visual_cache_step = int(slot_state.steps)

    def _observation_timing_snapshot(self) -> dict[str, float]:
        timing = getattr(self, "last_observation_build_timing", None)
        if not isinstance(timing, dict):
            return {}
        return {
            f"obs_{str(key)}": float(value)
            for key, value in timing.items()
            if isinstance(value, (int, float))
        }

    def _prepare_step_evaluations_batch(
        self,
        target_indices: list[int],
        truth_batch: list[Any],
        inst_batch: list[Any],
        inst_out: np.ndarray,
        ils_batch: np.ndarray,
        mission_inputs_batch: list[Any],
    ) -> list[dict[str, Any]] | None:
        if (
            not target_indices
            or not hasattr(ef_py, "prepare_step_evaluations_batch")
            or not hasattr(ef_py, "compute_execution_episode_runtime_batch")
        ):
            return None

        first_slot = self._slots[int(target_indices[0])]
        if first_slot is None or not hasattr(first_slot.loader, "_build_step_evaluation_batch_env_state"):
            return None

        def _config_tuple(slot_state: _CooperativeSlotState) -> tuple[float, float, float, float]:
            return (
                float(slot_state.loader.mission_cmd.get("target_altitude", 0.0)),
                float(slot_state.loader.mission_cmd.get("target_speed", 0.0)),
                float(slot_state.loader.mission_cmd.get("target_heading", 0.0)),
                float(getattr(slot_state.loader.sim, "get_time_step", lambda: 0.05)()),
            )

        ref_cfg = _config_tuple(first_slot)
        for slot_index in target_indices[1:]:
            slot_state = self._slots[int(slot_index)]
            if slot_state is None or _config_tuple(slot_state) != ref_cfg:
                return None

        config = ef_py.StepEvaluationBatchConfig()
        config.target_altitude_m = float(ref_cfg[0])
        config.target_speed_mps = float(ref_cfg[1])
        config.target_heading_deg = float(ref_cfg[2])
        config.time_step_s = float(ref_cfg[3])

        env_states = []
        prepared_entries: list[dict[str, Any] | None] = []
        for batch_idx, slot_index in enumerate(target_indices):
            slot_state = self._slots[int(slot_index)]
            if slot_state is None:
                return None
            state, prepared = slot_state.loader._build_step_evaluation_batch_env_state(
                truth=truth_batch[batch_idx],
                inst_obj=inst_batch[batch_idx],
                inst_vec=np.asarray(inst_out[batch_idx], dtype=np.float32),
                ils_vec=np.asarray(ils_batch[batch_idx], dtype=np.float32),
                steps=int(slot_state.steps),
                max_steps=int(slot_state.max_steps),
                mission_obs_mode=self.mission_obs_mode,
                mission_observation_inputs=mission_inputs_batch[batch_idx],
                return_prepared=True,
            )
            env_states.append(state)
            prepared_entries.append(prepared if isinstance(prepared, dict) else None)

        runtime_inputs_batch = ef_py.prepare_step_evaluations_batch(config, env_states)
        frame_products_batch = ef_py.compute_execution_episode_runtime_batch(runtime_inputs_batch)

        results: list[dict[str, Any]] = []
        for batch_idx, frame_products in enumerate(frame_products_batch):
            slot_state = self._slots[int(target_indices[batch_idx])]
            if slot_state is None:
                continue
            prepared = prepared_entries[batch_idx] if batch_idx < len(prepared_entries) else None
            result: dict[str, Any]
            if isinstance(prepared, dict):
                result = {
                    "truth_obj": truth_batch[batch_idx],
                    "inst_obj": inst_batch[batch_idx],
                    "steps": int(slot_state.steps),
                    "max_steps": int(slot_state.max_steps),
                    "mission_obs_mode": "" if self.mission_obs_mode is None else str(self.mission_obs_mode),
                    "frame_products": frame_products,
                    **prepared,
                }
                cache = getattr(slot_state.loader, "_runtime_eval_cache", None)
                if isinstance(cache, dict):
                    cache["step_evaluation"] = result
            else:
                result = {"frame_products": frame_products}
            results.append(result)
        return results

    def _build_observations_from_cached_state(self, indices: list[int] | None = None) -> list[dict[str, np.ndarray]]:
        target_indices = list(range(self.num_slots)) if indices is None else [int(i) for i in indices]
        if not target_indices:
            return []
        if self.include_visual:
            self._refresh_visual_batch(target_indices)

        backend = self._batch_observation_backend_mode()
        if backend == "legacy" or not hasattr(ef_py, "compute_execution_observation_batch_numpy"):
            self.last_observation_build_timing = {
                "mission_input_build_ms": 0.0,
                "execution_observation_batch_ms": 0.0,
                "step_eval_prepare_ms": 0.0,
            }
            obs_batch: list[dict[str, np.ndarray]] = []
            for slot_index in target_indices:
                slot_state = self._slots[int(slot_index)]
                if slot_state is None or slot_state.last_inst is None or slot_state.last_truth is None:
                    raise RuntimeError(f"cooperative slot {slot_index} has no cached state for observation build")
                obs = build_universal_observation(
                    slot_state.loader,
                    slot_state.last_inst,
                    slot_state.last_truth,
                    mission_obs_mode=self.mission_obs_mode,
                    max_contacts=self.max_contacts,
                    max_rwr=self.max_rwr,
                    include_proprio=self.include_proprio,
                    last_action=slot_state.last_action,
                    action_space=self.action_space,
                    steps=int(slot_state.steps),
                    max_steps=int(slot_state.max_steps),
                )
                if self.include_visual:
                    obs["visual"] = np.asarray(slot_state.visual_cache, dtype=np.float32, copy=False)
                obs_batch.append(obs)
            return obs_batch

        inst_batch: list[Any] = []
        truth_batch: list[Any] = []
        mission_inputs_batch: list[Any] = []
        ils_batch = np.zeros((len(target_indices), 4), dtype=np.float32)
        mission_input_t0 = time.perf_counter()
        for batch_idx, slot_index in enumerate(target_indices):
            slot_state = self._slots[int(slot_index)]
            if slot_state is None or slot_state.last_inst is None or slot_state.last_truth is None:
                raise RuntimeError(f"cooperative slot {slot_index} has no cached state for observation build")
            inst = slot_state.last_inst
            truth = slot_state.last_truth
            if hasattr(slot_state.loader, "reset_runtime_eval_cache"):
                try:
                    slot_state.loader.reset_runtime_eval_cache()
                except Exception:
                    pass
            inst_batch.append(inst)
            truth_batch.append(truth)
            mission_inputs_batch.append(
                slot_state.loader._build_mission_observation_runtime_inputs(
                    self.mission_obs_mode,
                    truth=truth,
                    inst=inst,
                )
            )
            ils_vec = slot_state.loader.get_ils_observation(float(truth.x), float(truth.y), float(inst.alt_baro))
            ils_batch[batch_idx, :] = np.asarray(ils_vec[:4], dtype=np.float32)
        mission_input_build_ms = (time.perf_counter() - mission_input_t0) * 1000.0

        execution_obs_t0 = time.perf_counter()
        inst_out, contacts_out, rwr_out, mission_out = ef_py.compute_execution_observation_batch_numpy(
            inst_batch,
            truth_batch,
            mission_inputs_batch,
            ils_batch,
            int(self.max_contacts),
            int(self.max_rwr),
            backend == "gpu_host",
        )
        execution_observation_batch_ms = (time.perf_counter() - execution_obs_t0) * 1000.0
        inst_out = np.asarray(inst_out, dtype=np.float32)
        contacts_out = np.asarray(contacts_out, dtype=np.float32)
        rwr_out = np.asarray(rwr_out, dtype=np.float32)
        mission_out = np.asarray(mission_out, dtype=np.float32)

        step_eval_prepare_ms = 0.0
        step_eval_batch: list[dict[str, Any]] | None = None
        if len(target_indices) > 0:
            try:
                prep_t0 = time.perf_counter()
                step_eval_batch = self._prepare_step_evaluations_batch(
                    target_indices,
                    truth_batch,
                    inst_batch,
                    inst_out,
                    ils_batch,
                    mission_inputs_batch,
                )
                step_eval_prepare_ms = (time.perf_counter() - prep_t0) * 1000.0
            except Exception:
                step_eval_batch = None
                step_eval_prepare_ms = 0.0
        self.last_observation_build_timing = {
            "mission_input_build_ms": float(mission_input_build_ms),
            "execution_observation_batch_ms": float(execution_observation_batch_ms),
            "step_eval_prepare_ms": float(step_eval_prepare_ms),
        }

        obs_batch: list[dict[str, np.ndarray]] = []
        for batch_idx, slot_index in enumerate(target_indices):
            slot_state = self._slots[int(slot_index)]
            if slot_state is None:
                continue
            inst_vec = np.asarray(inst_out[batch_idx], dtype=np.float32)
            miss_vec = np.asarray(mission_out[batch_idx], dtype=np.float32)
            if step_eval_batch is not None and batch_idx < len(step_eval_batch):
                step_eval = step_eval_batch[batch_idx]
            else:
                try:
                    step_eval = slot_state.loader._prepare_step_evaluation(
                        truth=truth_batch[batch_idx],
                        inst_obj=inst_batch[batch_idx],
                        inst_vec=inst_vec,
                        ils_vec=np.asarray(ils_batch[batch_idx], dtype=np.float32),
                        steps=int(slot_state.steps),
                        max_steps=int(slot_state.max_steps),
                        mission_obs_mode=self.mission_obs_mode,
                    )
                except Exception:
                    step_eval = None
            if isinstance(step_eval, dict):
                frame_products = step_eval.get("frame_products")
                if frame_products is not None and bool(getattr(frame_products, "mission_observation_evaluated", False)):
                    miss_vec = np.asarray(frame_products.mission_observation.values, dtype=np.float32)
            obs = {
                "instruments": inst_vec,
                "contacts": np.asarray(contacts_out[batch_idx], dtype=np.float32).reshape(int(self.max_contacts), 5),
                "rwr": np.asarray(rwr_out[batch_idx], dtype=np.float32).reshape(int(self.max_rwr), 4),
                "mission": miss_vec,
            }
            if self.include_proprio:
                if slot_state.last_action is None:
                    proprio = np.zeros((int(self.action_space.shape[0]),), dtype=np.float32)
                else:
                    proprio = np.asarray(slot_state.last_action, dtype=np.float32).reshape(-1)
                obs["proprio"] = proprio
            if self.include_visual:
                obs["visual"] = np.asarray(slot_state.visual_cache, dtype=np.float32, copy=False)
            obs_batch.append(obs)
        return obs_batch

    def _build_slot_observation(
        self,
        slot_state: _CooperativeSlotState,
        *,
        inst: Any,
        truth: Any,
    ) -> dict[str, np.ndarray]:
        obs = build_universal_observation(
            slot_state.loader,
            inst,
            truth,
            mission_obs_mode=self.mission_obs_mode,
            max_contacts=self.max_contacts,
            max_rwr=self.max_rwr,
            include_proprio=self.include_proprio,
            last_action=slot_state.last_action,
            action_space=self.action_space,
            steps=int(slot_state.steps),
            max_steps=int(slot_state.max_steps),
        )
        if self.include_visual:
            obs["visual"] = np.asarray(slot_state.visual_cache, dtype=np.float32, copy=False)
        return obs

    def _world_slot_states(self, world: _CooperativeWorldState) -> list[_CooperativeSlotState]:
        slot_states: list[_CooperativeSlotState] = []
        for slot_index in list(world.slot_indices):
            slot_state = self._slots[slot_index]
            if slot_state is not None:
                slot_states.append(slot_state)
        return slot_states

    def _sync_command_chain_batch(self, world_indices: list[int] | None = None) -> None:
        target_world_indices = list(range(self.world_count)) if world_indices is None else [int(i) for i in world_indices]
        mission_assignments = []
        task_assignments = []
        intent_assignments = []
        report_assignments = []
        for world_index in target_world_indices:
            world = self._worlds[world_index]
            for slot_index in world.slot_indices:
                slot_state = self._slots[slot_index]
                if slot_state is None:
                    continue
                loader = slot_state.loader

                mission_assign = ef_py.WorldMissionCommandAssignment()
                mission_assign.world_index = int(world_index)
                mission_assign.entity_id = int(slot_state.entity_id)
                mission_assign.command = build_kernel_mission_command(loader)
                mission_assignments.append(mission_assign)

                if getattr(loader, "task_order", None) is not None:
                    task_assign = ef_py.WorldTaskOrderAssignment()
                    task_assign.world_index = int(world_index)
                    task_assign.entity_id = int(slot_state.entity_id)
                    task_assign.order = loader.task_order
                    task_assignments.append(task_assign)

                if getattr(loader, "leader_intent", None) is not None:
                    intent_assign = ef_py.WorldLeaderIntentAssignment()
                    intent_assign.world_index = int(world_index)
                    intent_assign.entity_id = int(slot_state.entity_id)
                    intent_assign.intent = loader.leader_intent
                    intent_assignments.append(intent_assign)

                if getattr(loader, "pilot_report", None) is not None:
                    report_assign = ef_py.WorldPilotReportAssignment()
                    report_assign.world_index = int(world_index)
                    report_assign.entity_id = int(slot_state.entity_id)
                    report_assign.report = loader.pilot_report
                    report_assignments.append(report_assign)

        if mission_assignments:
            self._runtime_adapter.set_mission_commands_batch(mission_assignments)
        if task_assignments:
            self._runtime_adapter.set_task_orders_batch(task_assignments)
        if intent_assignments:
            self._runtime_adapter.set_leader_intents_batch(intent_assignments)
        if report_assignments:
            self._runtime_adapter.set_pilot_reports_batch(report_assignments)

    def _reset_world(self, world_index: int, seed: int | None) -> list[dict[str, np.ndarray]]:
        total_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        normalized_seed = self._normalize_seed(seed)
        world = self._worlds[int(world_index)]
        layout_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        layout = build_compiled_world_layout(
            self._compiled_scenario,
            seed=normalized_seed,
            randomization_overrides=dict(world.randomization_overrides) or None,
        )
        layout_build_ms = (time.perf_counter() - layout_t0) * 1000.0 if self.collect_step_timing else 0.0
        apply_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        applied_world = apply_world_layout_to_kernel(self._runtime_adapter.world(int(world_index)), layout)
        kernel_apply_ms = (time.perf_counter() - apply_t0) * 1000.0 if self.collect_step_timing else 0.0
        active_roster = list(getattr(applied_world, "active_roster", []) or [])
        if len(active_roster) != self.slots_per_world:
            raise RuntimeError(
                f"cooperative world {world_index} roster size changed from {self.slots_per_world} to {len(active_roster)}"
            )

        world.routing_loader = None
        world.view = None
        world.slot_indices = []
        base_slot_index = int(world_index) * int(self.slots_per_world)

        for local_slot_index, member in enumerate(active_roster):
            loader = self._build_slot_loader(
                int(world_index),
                applied_world,
                int(member.entity_id),
                normalized_seed,
            )
            control_slot = MultiAgentControlSlot(
                world_index=int(world_index),
                entity_id=int(member.entity_id),
                entity_name=str(member.entity_name),
                roster_index=int(local_slot_index),
                team_id=None if member.team_id is None else int(member.team_id),
                element_id=None if member.element_id is None else int(member.element_id),
                role_code=None if member.role_code is None else int(member.role_code),
                formation_role_id=None if member.formation_role_id is None else str(member.formation_role_id),
                relative_slot_code=None if member.relative_slot_code is None else int(member.relative_slot_code),
                policy_route=None if member.policy_route is None else str(member.policy_route),
                reference_entity_id=None if member.reference_entity_id is None else int(member.reference_entity_id),
                reference_entity_name=(
                    None if member.reference_entity_name is None else str(member.reference_entity_name)
                ),
                mission_command_overrides=_clone_small_dict(getattr(member, "mission_command_overrides", None)),
                task_order_overrides=_clone_small_dict(getattr(member, "task_order_overrides", None)),
            )
            slot_index = int(base_slot_index + local_slot_index)
            slot_state = self._build_slot_state(
                slot_index=slot_index,
                local_slot_index=local_slot_index,
                world=world,
                control_slot=control_slot,
                loader=loader,
            )
            slot_state.visual_cache = None
            slot_state.visual_cache_step = -1
            self._slots[slot_index] = slot_state
            world.slot_indices.append(slot_index)
            if world.routing_loader is None:
                world.routing_loader = loader

        if world.routing_loader is None:
            raise RuntimeError(f"world {world_index} has no cooperative routing loader")

        world.view = MultiAgentWorldRuntimeView(
            runtime=self._runtime_adapter,
            loader=world.routing_loader,
            world_index=int(world_index),
            action_space=self.action_space,
            action_mode=self.action_mode,
            mission_obs_mode=self.mission_obs_mode,
            include_proprio=self.include_proprio,
            max_contacts=self.max_contacts,
            max_rwr=self.max_rwr,
        )
        world.director_dirty = True
        refs = self._slot_refs(list(world.slot_indices))
        truth_list, inst_list = self._runtime_adapter.read_truth_and_instruments(refs)
        for local_slot_index, slot_index in enumerate(world.slot_indices):
            slot_state = self._slots[slot_index]
            if slot_state is None:
                continue
            slot_state.last_truth = truth_list[local_slot_index] if local_slot_index < len(truth_list) else None
            slot_state.last_inst = inst_list[local_slot_index] if local_slot_index < len(inst_list) else None
        if world.director is not None:
            world.director.reset(world, self._world_slot_states(world))

        obs_batch: list[dict[str, np.ndarray]] = []
        obs_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        for slot_index in world.slot_indices:
            slot_state = self._slots[slot_index]
            if slot_state is None:
                continue
            slot_state.steps = 0
            slot_state.loader.steps = 0
            slot_state.last_action = None
            slot_state.episode_return = 0.0
            slot_state.episode_length = 0
            slot_state.coop_success_latched = False
            slot_state.coop_completion_reason = ""
            slot_state.coop_completion_mission_status = None
            slot_state.coop_completion_info = None
            slot_state.coop_completion_terminal_observation = None
        obs_batch = self._build_observations_from_cached_state(list(world.slot_indices))
        for local_slot_index, slot_index in enumerate(world.slot_indices):
            slot_state = self._slots[slot_index]
            if slot_state is None:
                continue
            obs = obs_batch[local_slot_index]
            slot_state.last_obs = obs
            if slot_state.action_controller is not None:
                slot_state.action_controller.reset_state(_copy_obs(obs))
        if self.collect_step_timing:
            self.last_reset_timing = {
                "layout_build_ms": float(layout_build_ms),
                "kernel_apply_ms": float(kernel_apply_ms),
                "obs_build_ms": float((time.perf_counter() - obs_t0) * 1000.0),
                "total_ms": float((time.perf_counter() - total_t0) * 1000.0),
            }
        return obs_batch

    def reset(self) -> VecEnvObs:
        total_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        for world_index in range(self.world_count):
            world_seed = self._seeds[int(world_index * self.slots_per_world)]
            obs_batch = self._reset_world(world_index, seed=world_seed)
            for local_slot_index, obs in enumerate(obs_batch):
                slot_index = int(world_index * self.slots_per_world + local_slot_index)
                slot_state = self._slots[slot_index]
                if slot_state is None:
                    continue
                self.reset_infos[slot_index] = {
                    "world_index": int(world_index),
                    "entity_id": int(slot_state.entity_id),
                    "entity_name": str(slot_state.entity_name),
                }
                if self.collect_step_timing:
                    self.reset_infos[slot_index]["timing"] = dict(self.last_reset_timing)
                self._save_obs(slot_index, obs)
        if self.collect_step_timing:
            self.last_reset_timing["total_reset_ms"] = float((time.perf_counter() - total_t0) * 1000.0)
        self._reset_seeds()
        self._reset_options()
        return self._obs_from_buf()

    def _prepare_slot_action(
        self,
        slot_state: _CooperativeSlotState,
        action: np.ndarray,
    ) -> tuple[np.ndarray, Any]:
        effective_action = normalize_action(
            action,
            action_space=self.action_space,
            action_mode=self.action_mode,
        )
        prepared = None
        if slot_state.action_controller is not None:
            prepared = slot_state.action_controller.prepare_action(effective_action)
            effective_action = np.asarray(prepared.action, dtype=np.float32).reshape(-1)
        slot_state.last_action = np.asarray(effective_action, dtype=np.float32, copy=True)
        return slot_state.last_action, prepared

    def _neutral_hold_action(self, slot_state: _CooperativeSlotState) -> np.ndarray:
        action = np.zeros(self.action_space.shape, dtype=np.float32)
        if self.action_mode == "full":
            inst = slot_state.last_inst
            throttle = 0.0
            gear = 0.0
            flaps = 0.0
            speedbrake = 0.0
            if inst is not None:
                try:
                    throttle = float(np.clip(getattr(inst, "throttle_pos", 0.0), 0.0, 1.0))
                except Exception:
                    throttle = 0.0
                try:
                    gear = float(np.clip(getattr(inst, "gear_pos", 0.0), 0.0, 1.0))
                except Exception:
                    gear = 0.0
                try:
                    flaps = float(np.clip(getattr(inst, "flaps_pos", 0.0), 0.0, 1.0))
                except Exception:
                    flaps = 0.0
                try:
                    speedbrake = float(np.clip(getattr(inst, "speedbrake_pos", 0.0), 0.0, 1.0))
                except Exception:
                    speedbrake = 0.0
            action[3] = throttle
            action[4] = gear
            action[5] = np.clip(0.5 + 0.5 * flaps, 0.0, 1.0)
            action[6] = np.clip(0.5 + 0.5 * speedbrake, 0.0, 1.0)
        return normalize_action(action, action_space=self.action_space, action_mode=self.action_mode)

    def step_async(self, actions: np.ndarray) -> None:
        action_arr = np.asarray(actions, dtype=np.float32)
        if self.num_envs == 1 and action_arr.ndim == 1:
            action_arr = action_arr.reshape(1, -1)
        self._actions = action_arr

    def step_wait(self) -> VecEnvStepReturn:
        if self._actions is None:
            raise RuntimeError("step_async() must be called before step_wait().")

        total_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        sync_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        self._sync_command_chain_batch()
        command_sync_ms = (time.perf_counter() - sync_t0) * 1000.0 if self.collect_step_timing else 0.0

        prepared_by_slot: dict[int, Any] = {}
        action_prepare_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        for world in self._worlds:
            if world.view is None:
                raise RuntimeError(f"world {world.world_index} has not been reset")
            actions_by_entity_id: dict[int, np.ndarray] = {}
            inst_by_entity_id: dict[int, Any] = {}
            for slot_index in world.slot_indices:
                slot_state = self._slots[slot_index]
                if slot_state is None:
                    continue
                if bool(slot_state.coop_success_latched):
                    effective_action = self._neutral_hold_action(slot_state)
                    prepared = None
                    slot_state.last_action = np.asarray(effective_action, dtype=np.float32, copy=True)
                else:
                    effective_action, prepared = self._prepare_slot_action(slot_state, self._actions[slot_index])
                actions_by_entity_id[int(slot_state.entity_id)] = effective_action
                inst_by_entity_id[int(slot_state.entity_id)] = slot_state.last_inst
                prepared_by_slot[int(slot_index)] = prepared
            world.view.apply_actions(actions_by_entity_id, inst_by_entity_id=inst_by_entity_id)
        action_prepare_ms = (time.perf_counter() - action_prepare_t0) * 1000.0 if self.collect_step_timing else 0.0

        step_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        self._runtime_adapter.step_worlds(list(range(self.world_count)))
        batch_step_ms = (time.perf_counter() - step_t0) * 1000.0 if self.collect_step_timing else 0.0

        # Refresh per-slot state first, then update the per-slot behavior layers, then sync the
        # command chain back to the kernel for the next world step.
        state_read_ms = 0.0
        behavior_update_ms = 0.0
        for world in self._worlds:
            if world.view is None:
                continue
            read_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            refs = self._slot_refs(list(world.slot_indices))
            truth_list, inst_list = self._runtime_adapter.read_truth_and_instruments(refs)
            for local_slot_index, slot_index in enumerate(world.slot_indices):
                slot_state = self._slots[slot_index]
                if slot_state is None:
                    continue
                slot_state.last_truth = truth_list[local_slot_index] if local_slot_index < len(truth_list) else None
                slot_state.last_inst = inst_list[local_slot_index] if local_slot_index < len(inst_list) else None
            if self.collect_step_timing:
                state_read_ms += (time.perf_counter() - read_t0) * 1000.0
            behavior_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            for slot_index in world.slot_indices:
                slot_state = self._slots[slot_index]
                if slot_state is None:
                    continue
                slot_state.steps += 1
                slot_state.loader.steps = int(slot_state.steps)
                sim_time = float(slot_state.steps) * float(self._runtime_adapter.world(slot_state.world_index).get_time_step())
                slot_state.loader.update_behaviors(
                    sim_time,
                    truth=slot_state.last_truth,
                    inst=slot_state.last_inst,
                    sync_to_kernel=False,
                )
            if world.director is not None:
                world.director.update(world, self._world_slot_states(world), force=True)
            if self.collect_step_timing:
                behavior_update_ms += (time.perf_counter() - behavior_t0) * 1000.0
        sync_t0 = time.perf_counter() if self.collect_step_timing else 0.0
        self._sync_command_chain_batch()
        if self.collect_step_timing:
            command_sync_ms += (time.perf_counter() - sync_t0) * 1000.0

        rewards = np.zeros((self.num_envs,), dtype=np.float32)
        dones = np.zeros((self.num_envs,), dtype=bool)
        infos: list[dict[str, Any]] = [{} for _ in range(self.num_envs)]

        obs_build_ms = 0.0
        reward_info_ms = 0.0
        for world in self._worlds:
            world_done = False
            world_success = True
            world_failure = False
            world_timeout = False
            slot_results: list[tuple[int, dict[str, np.ndarray], float, bool, bool, dict[str, Any], float, int]] = []
            obs_by_slot_index: dict[int, dict[str, np.ndarray]] = {}
            obs_t0 = time.perf_counter() if self.collect_step_timing else 0.0
            world_obs_batch = self._build_observations_from_cached_state(list(world.slot_indices))
            if self.collect_step_timing:
                obs_build_ms += (time.perf_counter() - obs_t0) * 1000.0
            for local_slot_index, slot_index in enumerate(world.slot_indices):
                if local_slot_index < len(world_obs_batch):
                    obs_by_slot_index[int(slot_index)] = world_obs_batch[local_slot_index]
            for slot_index in world.slot_indices:
                slot_state = self._slots[slot_index]
                if slot_state is None:
                    continue
                obs = obs_by_slot_index[int(slot_index)]
                reward_t0 = time.perf_counter() if self.collect_step_timing else 0.0
                if bool(slot_state.coop_success_latched) and slot_state.coop_completion_mission_status is not None:
                    reward = 0.0
                    terminated = False
                    truncated = False
                    mission_status = np.asarray(slot_state.coop_completion_mission_status, dtype=np.float32)
                    info = dict(slot_state.coop_completion_info or {})
                else:
                    cache = getattr(slot_state.loader, "_runtime_eval_cache", None)
                    cached_step_eval = cache.get("step_evaluation") if isinstance(cache, dict) else None
                    reward, terminated, truncated, mission_status = slot_state.loader.compute_full_step(
                        obs,
                        self._runtime_adapter.world(slot_state.world_index),
                        slot_state.steps,
                        slot_state.max_steps,
                        truth=slot_state.last_truth,
                        inst_state=slot_state.last_inst,
                        step_evaluation=cached_step_eval if isinstance(cached_step_eval, dict) else None,
                    )
                    if self.step_info_mode == "off" or (
                        self.step_info_mode == "terminal" and not bool(terminated or truncated)
                    ):
                        info = build_step_info_minimal(
                            slot_state.loader,
                            mission_status=mission_status,
                            terminated=bool(terminated),
                            truncated=bool(truncated),
                        )
                    else:
                        info = build_step_info(
                            slot_state.loader,
                            self._runtime_adapter.world(slot_state.world_index),
                            int(slot_state.entity_id),
                            mission_status=mission_status,
                            terminated=bool(terminated),
                            truncated=bool(truncated),
                            inst_now=slot_state.last_inst,
                            truth_now=slot_state.last_truth,
                        )
                if self.collect_step_timing:
                    reward_info_ms += (time.perf_counter() - reward_t0) * 1000.0

                prepared = prepared_by_slot.get(int(slot_index))
                if slot_state.action_controller is not None and prepared is not None:
                    obs, reward, info = slot_state.action_controller.finalize_step_result(obs, reward, info, prepared)
                slot_state.last_obs = obs
                slot_state.episode_return += float(reward)
                slot_state.episode_length += 1

                success = _mission_status_success_flag(mission_status)
                truncated = bool(truncated)
                terminated = bool(terminated)
                reason = str(info.get("termination_reason", "") or "").strip().lower()
                failure = bool(terminated and not success)
                timeout = bool(truncated and not terminated)

                if success and not bool(slot_state.coop_success_latched):
                    slot_state.coop_success_latched = True
                    slot_state.coop_completion_reason = str(info.get("termination_reason", "") or "success_waypoint")
                    slot_state.coop_completion_mission_status = np.asarray(mission_status, dtype=np.float32, copy=True)
                    slot_state.coop_completion_info = dict(info)
                    slot_state.coop_completion_terminal_observation = _copy_obs(obs)
                elif bool(slot_state.coop_success_latched):
                    success = True
                    terminated = False
                    truncated = False
                    failure = False
                    timeout = False

                if bool(slot_state.coop_success_latched):
                    info["coop_slot_success_latched"] = 1.0
                    info["coop_slot_complete"] = 1.0
                else:
                    info["coop_slot_success_latched"] = 0.0
                    info["coop_slot_complete"] = 0.0
                info["coop_slot_terminal_success"] = float(success)
                info["coop_slot_terminal_failure"] = float(failure)
                info["coop_slot_terminal_timeout"] = float(timeout)
                if success and slot_state.coop_completion_reason:
                    info["termination_reason"] = slot_state.coop_completion_reason

                world_success = bool(world_success and success)
                world_failure = bool(world_failure or failure)
                world_timeout = bool(world_timeout or timeout)
                slot_results.append(
                    (
                        slot_index,
                        obs,
                        float(reward),
                        bool(terminated),
                        bool(truncated),
                        info,
                        float(slot_state.episode_return),
                        int(slot_state.episode_length),
                    )
                )

            if not slot_results:
                continue

            world_done = bool(world_failure or world_timeout or world_success)
            if world_done:
                terminal_obs = {}
                for slot_index, obs, *_rest in slot_results:
                    slot_state = self._slots[slot_index]
                    if slot_state is not None and slot_state.coop_completion_terminal_observation is not None:
                        terminal_obs[int(slot_index)] = _copy_obs(slot_state.coop_completion_terminal_observation)
                    else:
                        terminal_obs[int(slot_index)] = _copy_obs(obs)
                reset_obs_batch = self._reset_world(world.world_index, seed=None)
                reset_by_local_slot = {
                    int(local_slot_index): obs
                    for local_slot_index, obs in enumerate(reset_obs_batch)
                }

            for slot_index, obs, reward, terminated, truncated, info, episode_return, episode_length in slot_results:
                slot_state = self._slots[slot_index]
                if slot_state is None:
                    continue
                rewards[slot_index] = float(reward)
                infos[slot_index] = dict(info)
                infos[slot_index]["world_index"] = int(slot_state.world_index)
                infos[slot_index]["slot_index"] = int(slot_state.slot_index)
                infos[slot_index]["local_slot_index"] = int(slot_state.local_slot_index)
                infos[slot_index]["slots_per_world"] = int(self.slots_per_world)
                infos[slot_index]["entity_id"] = int(slot_state.entity_id)
                infos[slot_index]["entity_name"] = str(slot_state.entity_name)
                infos[slot_index]["formation_role_id"] = (
                    None
                    if slot_state.control_slot.formation_role_id is None
                    else str(slot_state.control_slot.formation_role_id)
                )
                infos[slot_index]["role_code"] = (
                    None if slot_state.control_slot.role_code is None else int(slot_state.control_slot.role_code)
                )
                infos[slot_index]["relative_slot_code"] = (
                    None
                    if slot_state.control_slot.relative_slot_code is None
                    else int(slot_state.control_slot.relative_slot_code)
                )
                infos[slot_index]["world_done"] = float(bool(world_done))
                infos[slot_index]["world_success"] = float(bool(world_success))
                infos[slot_index]["world_failure"] = float(bool(world_failure))
                infos[slot_index]["world_timeout"] = float(bool(world_timeout))
                slot_completed = bool(float(infos[slot_index].get("coop_slot_complete", 0.0)) > 0.5)
                infos[slot_index]["shared_world_reset"] = float(
                    bool(world_done and not slot_completed and not (world_failure or world_timeout or (terminated or truncated)))
                )
                infos[slot_index]["policy_route"] = (
                    None if slot_state.control_slot.policy_route is None else str(slot_state.control_slot.policy_route)
                )
                if world_done:
                    infos[slot_index]["terminal_observation"] = terminal_obs[int(slot_index)]
                    infos[slot_index]["TimeLimit.truncated"] = bool(world_timeout)
                    infos[slot_index]["episode"] = {
                        "r": round(float(episode_return), 6),
                        "l": int(episode_length),
                    }
                    dones[slot_index] = True
                    reset_obs = reset_by_local_slot[int(slot_state.local_slot_index)]
                    self._save_obs(slot_index, reset_obs)
                else:
                    infos[slot_index]["TimeLimit.truncated"] = False
                    dones[slot_index] = False
                    self._save_obs(slot_index, obs)

        if self.collect_step_timing:
            self.last_step_timing = {
                "action_prepare_ms": float(action_prepare_ms),
                "batch_step_ms": float(batch_step_ms),
                "state_read_ms": float(state_read_ms),
                "behavior_update_ms": float(behavior_update_ms),
                "command_sync_ms": float(command_sync_ms),
                "obs_build_ms": float(obs_build_ms),
                "reward_info_ms": float(reward_info_ms),
                "total_ms": float((time.perf_counter() - total_t0) * 1000.0),
            }
            self.last_step_timing.update(self._observation_timing_snapshot())
            for info in infos:
                info["timing"] = dict(self.last_step_timing)
        else:
            self.last_step_timing = {}
        self.buf_rews[:] = rewards
        self.buf_dones[:] = dones
        self.buf_infos = infos
        self._actions = None
        return self._obs_from_buf(), np.copy(self.buf_rews), np.copy(self.buf_dones), list(self.buf_infos)

    def close(self) -> None:
        self._actions = None
        self._closed = True

    def get_images(self) -> list[np.ndarray | None]:
        if self.render_mode != "rgb_array":
            warnings.warn(
                f"The render mode is {self.render_mode}, but this method assumes it is `rgb_array` to obtain images."
            )
        return [None for _ in range(self.num_envs)]

    def get_attr(self, attr_name: str, indices: VecEnvIndices = None) -> list[Any]:
        if attr_name == "render_mode" and any(slot_state is None for slot_state in self._slots):
            return [self.render_mode for _ in self._get_indices(indices)]
        target_slots = self._get_target_slots(indices)
        values = []
        for slot_state in target_slots:
            if hasattr(slot_state, attr_name):
                values.append(getattr(slot_state, attr_name))
            elif hasattr(slot_state.loader, attr_name):
                values.append(getattr(slot_state.loader, attr_name))
            elif hasattr(slot_state.world, attr_name):
                values.append(getattr(slot_state.world, attr_name))
            else:
                raise AttributeError(attr_name)
        return values

    def set_attr(self, attr_name: str, value: Any, indices: VecEnvIndices = None) -> None:
        for slot_state in self._get_target_slots(indices):
            if hasattr(slot_state, attr_name):
                setattr(slot_state, attr_name, value)
            elif hasattr(slot_state.loader, attr_name):
                setattr(slot_state.loader, attr_name, value)
            elif hasattr(slot_state.world, attr_name):
                setattr(slot_state.world, attr_name, value)
            else:
                raise AttributeError(attr_name)

    def env_method(self, method_name: str, *method_args, indices: VecEnvIndices = None, **method_kwargs) -> list[Any]:
        if all(slot_state is None for slot_state in self._slots):
            world_results = []
            for world_index in self._get_indices(indices):
                if world_index < 0 or world_index >= len(self._worlds):
                    continue
                world = self._worlds[int(world_index)]
                if hasattr(world, method_name):
                    method = getattr(world, method_name)
                    world_results.append(method(*method_args, **method_kwargs))
                    continue
                if hasattr(self, method_name):
                    method = getattr(self, method_name)
                    world_results.append(method(*method_args, indices=[int(world_index)], **method_kwargs))
                    continue
                raise RuntimeError(f"cooperative slot {world_index} is not initialized")
            if world_results:
                return world_results
        results = []
        for slot_state in self._get_target_slots(indices):
            if hasattr(slot_state, method_name):
                method = getattr(slot_state, method_name)
            elif hasattr(slot_state.loader, method_name):
                method = getattr(slot_state.loader, method_name)
            elif hasattr(slot_state.world, method_name):
                method = getattr(slot_state.world, method_name)
            else:
                raise AttributeError(method_name)
            results.append(method(*method_args, **method_kwargs))
        return results

    def env_is_wrapped(self, wrapper_class: type[gym.Wrapper], indices: VecEnvIndices = None) -> list[bool]:
        _ = wrapper_class
        return [False for _ in self._get_indices(indices)]

    def _get_target_slots(self, indices: VecEnvIndices) -> list[_CooperativeSlotState]:
        slots: list[_CooperativeSlotState] = []
        for index in self._get_indices(indices):
            slot_state = self._slots[int(index)]
            if slot_state is None:
                raise RuntimeError(f"cooperative slot {index} is not initialized")
            slots.append(slot_state)
        return slots

    def _save_obs(self, env_idx: int, obs: VecEnvObs) -> None:
        for key in self.keys:
            if key is None:
                self.buf_obs[key][env_idx] = obs
            else:
                self.buf_obs[key][env_idx] = obs[key]  # type: ignore[index]

    def _obs_from_buf(self) -> VecEnvObs:
        return dict_to_obs(self.observation_space, deepcopy(self.buf_obs))

    def slot_control_slots(self) -> list[MultiAgentControlSlot]:
        out: list[MultiAgentControlSlot] = []
        for slot_state in self._slots:
            if slot_state is not None:
                out.append(slot_state.control_slot)
        return out

    def slot_indices_by_policy_route(self) -> dict[str, list[int]]:
        out: dict[str, list[int]] = {}
        for slot_state in self._slots:
            if slot_state is None:
                continue
            route = str(slot_state.control_slot.policy_route or "default")
            out.setdefault(route, []).append(int(slot_state.slot_index))
        return out


def _normalize_flight_shaping_backend(value: str | None) -> str:
    backend = "auto" if value is None else normalize_flight_shaping_backend(value)
    if backend in ("auto", "legacy", "compiled", "gpu_host"):
        return backend
    raise ValueError(f"Unknown flight_shaping_backend: {value!r}")
