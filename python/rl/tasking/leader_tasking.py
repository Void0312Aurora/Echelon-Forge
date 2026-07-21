from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import ef_py
from python.angles import wrap_signed_deg
from python.coercion import coerce_nonnegative_int
from python.rl.tasking.bridge import (
    build_kernel_mission_command as _bridge_build_kernel_mission_command,
    get_policy_agent_observation,
    get_policy_instrument_state,
    has_active_waypoint_leg as _bridge_has_active_waypoint_leg,
    infer_recovery_approach_type as _bridge_infer_recovery_approach_type,
    infer_recovery_base_id as _bridge_infer_recovery_base_id,
    infer_recovery_runway_id as _bridge_infer_recovery_runway_id,
    infer_route_ref_id as _bridge_infer_route_ref_id,
    landing_reference_heading_deg as _bridge_landing_reference_heading_deg,
    mission_command_view,
    sync_loader_command_chain,
)
from .common_core_profile import (
    apply_leader_intent_common_core_defaults,
    apply_pilot_report_common_core_defaults,
    apply_task_order_common_core_defaults,
    apply_task_order_common_core_spec,
)
from python.rl.control.mission_defs import (
    COMMAND_CODE_LANDING,
    LANDING_PHASE_NAMES,
    TAKEOFF_PHASE_NAMES,
    command_code_for_phase_name,
    is_landing_command_code,
)

# G4 information-state declaration (architecture design doc §3/§15; facility in
# python/architecture/information_layer.py). This module is the scripted C2/leader
# director (RuleBasedLeaderPhaseManager / ScriptedC2TaskManager): a maintained
# doctrine that consumes own-ship authoritative truth (x/y/z/heading via the
# get_policy_agent_observation seam, plus instrument via get_policy_instrument_state)
# to form tasking intent and deliver leader/mission commands. Task orders, leader
# intent and pilot reports are tasking/command artifacts, not an information layer,
# so PRODUCED is empty. Declaring it is neutral (python.architecture), but the
# reads are kept: routing them through gym_envs.observation_view would add a
# python.rl -> gym_envs reverse dependency, so this is declared-but-open
# (t8_g4_truth_leak_inventory.md §7, TL16) and NOT ban-gated. Pure metadata; no
# runtime cost.
INFORMATION_LAYER_CONSUMED = ("World Truth",)
INFORMATION_LAYER_PRODUCED = ()
SEMANTIC_STAGE = ("P2 TaskingIntent", "P3 CommandDelivery")

# Local names preserved as thin aliases; semantics owned by python.angles/python.coercion.
_wrap_deg = wrap_signed_deg
_coerce_nonnegative_int = coerce_nonnegative_int


def _coerce_positive_int(raw_value: Any) -> int:
    value = _coerce_nonnegative_int(raw_value)
    return value if value > 0 else 0


def _recovery_approach_none() -> Any:
    namespace = getattr(ef_py, "RecoveryApproachType", None)
    if namespace is None:
        return 0
    return getattr(namespace, "None", 0)


def _takeoff_procedure_unspecified() -> Any:
    namespace = getattr(ef_py, "TakeoffProcedureType", None)
    if namespace is None:
        return 0
    return getattr(namespace, "Unspecified", 0)


def _takeoff_clearance_unspecified() -> Any:
    namespace = getattr(ef_py, "TakeoffClearanceState", None)
    if namespace is None:
        return 0
    return getattr(namespace, "Unspecified", 0)


def _runway_slot_unspecified() -> Any:
    namespace = getattr(ef_py, "RunwaySlotPosition", None)
    if namespace is None:
        return 0
    return getattr(namespace, "Unspecified", 0)


def _recovery_approach_type_or_default(raw_value: Any, default_value: Any) -> Any:
    namespace = getattr(ef_py, "RecoveryApproachType", None)
    if namespace is None:
        if raw_value is None:
            return default_value
        return _coerce_nonnegative_int(raw_value)
    try:
        default_member = namespace(int(default_value))
    except Exception:
        default_member = default_value
    if raw_value is None:
        return default_member
    if isinstance(raw_value, str):
        text = str(raw_value).strip()
        if not text:
            return default_member
        direct = getattr(namespace, text, None)
        if direct is not None:
            return direct
        normalized = text.replace("_", "").replace(" ", "").lower()
        for name in dir(namespace):
            if name.startswith("_"):
                continue
            if name.replace("_", "").lower() == normalized:
                return getattr(namespace, name)
        return default_member
    try:
        return namespace(int(raw_value))
    except Exception:
        return default_member


def _takeoff_procedure_or_default(raw_value: Any, default_value: Any) -> Any:
    namespace = getattr(ef_py, "TakeoffProcedureType", None)
    if namespace is None:
        if raw_value is None:
            return default_value
        return _coerce_nonnegative_int(raw_value)
    return _enum_or_default(namespace, raw_value, default_value)


def _takeoff_clearance_or_default(raw_value: Any, default_value: Any) -> Any:
    namespace = getattr(ef_py, "TakeoffClearanceState", None)
    if namespace is None:
        if raw_value is None:
            return default_value
        return _coerce_nonnegative_int(raw_value)
    return _enum_or_default(namespace, raw_value, default_value)


def _runway_slot_or_default(raw_value: Any, default_value: Any) -> Any:
    namespace = getattr(ef_py, "RunwaySlotPosition", None)
    if namespace is None:
        if raw_value is None:
            return default_value
        return _coerce_nonnegative_int(raw_value)
    return _enum_or_default(namespace, raw_value, default_value)


def _landing_mode_to_recovery_approach_type(landing_mode: Any, default_value: Any) -> Any:
    mode = str(landing_mode or "").strip().lower()
    if not mode:
        return default_value
    namespace = getattr(ef_py, "RecoveryApproachType", None)
    if namespace is None:
        mapping = {
            "straight_in": 1,
            "ils_final": 2,
            "ils": 2,
            "visual": 3,
            "overhead": 4,
            "tacan": 5,
        }
        return int(mapping.get(mode, _coerce_nonnegative_int(default_value)))
    mapping = {
        "straight_in": getattr(namespace, "StraightIn", default_value),
        "ils_final": getattr(namespace, "ILS", default_value),
        "ils": getattr(namespace, "ILS", default_value),
        "visual": getattr(namespace, "Visual", default_value),
        "overhead": getattr(namespace, "Overhead", default_value),
        "tacan": getattr(namespace, "TACAN", default_value),
    }
    return mapping.get(mode, default_value)


def _scenario_task_order_cfg(loader: Any) -> dict[str, Any] | None:
    scenario_data = getattr(loader, "scenario_data", {}) or {}
    if not isinstance(scenario_data, dict):
        return None
    task_order = scenario_data.get("task_order", None)
    return task_order if isinstance(task_order, dict) else None


def _scenario_mission_cfg(loader: Any) -> dict[str, Any] | None:
    scenario_data = getattr(loader, "scenario_data", {}) or {}
    if not isinstance(scenario_data, dict):
        return None
    mission_cfg = scenario_data.get("mission_command", None)
    return mission_cfg if isinstance(mission_cfg, dict) else None


def _mission_cmd_dict(loader: Any) -> dict[str, Any]:
    return mission_command_view(loader).payload


def _post_transition_cfg(loader: Any) -> dict[str, Any] | None:
    post = getattr(loader, "post_waypoint_transition", None)
    if isinstance(post, dict) and post:
        return post
    mission_cfg = _scenario_mission_cfg(loader)
    if not isinstance(mission_cfg, dict):
        return None
    post = mission_cfg.get("post_waypoint_transition", None)
    return post if isinstance(post, dict) and post else None


def _stable_ref_id(payload: Any) -> int:
    try:
        text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except Exception:
        text = repr(payload)
    digest = hashlib.sha1(text.encode("utf-8")).digest()
    ref_id = int.from_bytes(digest[:8], "big", signed=False)
    return ref_id if ref_id > 0 else 1


def infer_route_ref_id(loader: Any) -> int:
    return _bridge_infer_route_ref_id(loader)


def has_active_waypoint_leg(loader: Any) -> bool:
    return _bridge_has_active_waypoint_leg(loader)


def infer_recovery_base_id(loader: Any, task: Any | None = None) -> int:
    return _bridge_infer_recovery_base_id(loader, task=task)


def infer_recovery_runway_id(loader: Any, task: Any | None = None) -> int:
    return _bridge_infer_recovery_runway_id(loader, task=task)


def infer_recovery_approach_type(loader: Any, task: Any | None = None) -> Any:
    return _bridge_infer_recovery_approach_type(loader, task=task)


def _landing_reference_heading_deg(loader: Any, default_heading_deg: float) -> float:
    return _bridge_landing_reference_heading_deg(loader, default_heading_deg)


def build_kernel_mission_command(loader: Any) -> ef_py.MissionCommand:
    return _bridge_build_kernel_mission_command(loader)


def _enum_or_default(namespace: Any, raw_value: Any, default_value: Any) -> Any:
    if raw_value is None:
        return default_value
    if isinstance(raw_value, str):
        return getattr(namespace, str(raw_value), default_value)
    try:
        return namespace(int(raw_value))
    except Exception:
        pass
    try:
        return int(raw_value)
    except Exception:
        return default_value


def _apply_task_order_overrides(
    order: ef_py.TaskOrder,
    order_spec: dict[str, Any] | None,
    *,
    default_assignee_id: int,
) -> ef_py.TaskOrder:
    if not isinstance(order_spec, dict):
        return order

    order.active = bool(order_spec.get("active", True))
    if "task_id" in order_spec:
        order.task_id = int(order_spec.get("task_id", order.task_id))
    if "task_type" in order_spec:
        order.task_type = _enum_or_default(ef_py.TaskType, order_spec.get("task_type"), order.task_type)
    if "priority" in order_spec:
        order.priority = int(order_spec.get("priority", order.priority))
    if "issuer_id" in order_spec:
        order.issuer_id = int(order_spec.get("issuer_id", order.issuer_id))
    order.assignee_id = int(order_spec.get("assignee_id", default_assignee_id))
    if "issue_time_s" in order_spec:
        order.issue_time_s = float(order_spec.get("issue_time_s", order.issue_time_s))

    for name in (
        "anchor_x_m",
        "anchor_y_m",
        "anchor_z_m",
        "station_radius_m",
        "station_leg_length_m",
        "station_heading_deg",
        "altitude_block_min_m",
        "altitude_block_max_m",
        "target_altitude_m",
        "speed_min_mps",
        "speed_max_mps",
        "target_speed_mps",
        "on_station_time_s",
        "fuel_bingo_override_kg",
    ):
        if name in order_spec:
            setattr(order, name, float(order_spec.get(name, getattr(order, name))))

    for name in ("entry_condition_code", "exit_condition_code", "recovery_base_id", "recovery_runway_id"):
        if name in order_spec:
            setattr(order, name, int(order_spec.get(name, getattr(order, name))))

    if "station_type" in order_spec:
        order.station_type = _enum_or_default(ef_py.StationType, order_spec.get("station_type"), order.station_type)
    if "recovery_approach_type" in order_spec and hasattr(order, "recovery_approach_type"):
        order.recovery_approach_type = _recovery_approach_type_or_default(
            order_spec.get("recovery_approach_type", getattr(order, "recovery_approach_type", _recovery_approach_none())),
            getattr(order, "recovery_approach_type", _recovery_approach_none()),
        )
    apply_task_order_common_core_spec(order, order_spec)
    return order


class RuleBasedLeaderPhaseManager:
    """
    Minimal scripted C2/leader bridge for the single-aircraft CAP bootstrap.
    """

    def __init__(
        self,
        *,
        terminal_waypoint_count: int = 2,
        approach_arm_dme_m: float = 12000.0,
        approach_arm_alt_agl_max_m: float = 1400.0,
        approach_arm_loc_abs_max: float = 0.55,
        approach_arm_gs_abs_max: float = 1.25,
        approach_arm_heading_error_deg_max: float = 45.0,
        approach_arm_require_runway_frame: bool = True,
        approach_arm_along_min_m: float = -1000.0,
        approach_arm_cross_abs_max_m: float = 3500.0,
        landing_final_dme_m: float = 3500.0,
        landing_final_alt_agl_m: float = 140.0,
        rollout_alt_agl_m: float = 5.0,
        scramble_ground_speed_max_mps: float = 15.0,
    ):
        self.terminal_waypoint_count = max(0, int(terminal_waypoint_count))
        self.approach_arm_dme_m = float(approach_arm_dme_m)
        self.approach_arm_alt_agl_max_m = float(approach_arm_alt_agl_max_m)
        self.approach_arm_loc_abs_max = float(approach_arm_loc_abs_max)
        self.approach_arm_gs_abs_max = float(approach_arm_gs_abs_max)
        self.approach_arm_heading_error_deg_max = float(approach_arm_heading_error_deg_max)
        self.approach_arm_require_runway_frame = bool(approach_arm_require_runway_frame)
        self.approach_arm_along_min_m = float(approach_arm_along_min_m)
        self.approach_arm_cross_abs_max_m = float(approach_arm_cross_abs_max_m)
        self.landing_final_dme_m = float(landing_final_dme_m)
        self.landing_final_alt_agl_m = float(landing_final_alt_agl_m)
        self.rollout_alt_agl_m = float(rollout_alt_agl_m)
        self.scramble_ground_speed_max_mps = float(scramble_ground_speed_max_mps)

    def reset(
        self,
        loader: Any,
        sim_time_s: float = 0.0,
        *,
        truth: Any = None,
        inst: Any = None,
        sync_to_kernel: bool = True,
    ) -> None:
        loader.task_order = self._build_task_order(loader, sim_time_s=sim_time_s)
        loader.leader_intent = ef_py.LeaderIntent()
        loader.pilot_report = self._make_report(
            loader,
            report_type=ef_py.CommMsgType.REP_WILCO,
            sim_time_s=sim_time_s,
            truth=truth,
        )
        self.update(loader, sim_time_s=sim_time_s, truth=truth, inst=inst, sync_to_kernel=sync_to_kernel)

    def update(
        self,
        loader: Any,
        sim_time_s: float = 0.0,
        *,
        truth: Any = None,
        inst: Any = None,
        sync_to_kernel: bool = True,
    ) -> None:
        if getattr(loader, "agent_id", None) is None:
            return

        if getattr(loader, "task_order", None) is None:
            loader.task_order = self._build_task_order(loader, sim_time_s=sim_time_s)

        cmd_view = mission_command_view(loader)
        if truth is None:
            truth = get_policy_agent_observation(loader)
        if inst is None:
            inst = get_policy_instrument_state(loader)

        alt_agl = float(getattr(inst, "alt_radar", 0.0))
        ground_speed = float(getattr(inst, "ground_speed", 0.0))
        heading_deg = float(getattr(inst, "heading", getattr(truth, "heading", 0.0)))

        ils_vec = loader.get_ils_observation(
            float(getattr(truth, "x", 0.0)),
            float(getattr(truth, "y", 0.0)),
            float(getattr(inst, "alt_baro", 0.0)),
        )
        ils_valid = float(ils_vec[0]) > 0.5 if len(ils_vec) >= 1 else False
        loc_abs = abs(float(ils_vec[1])) if len(ils_vec) >= 2 else float("inf")
        gs_abs = abs(float(ils_vec[2])) if len(ils_vec) >= 3 else float("inf")
        dme_m = float(ils_vec[3]) if len(ils_vec) >= 4 else float("inf")

        waypoints = list(getattr(loader, "waypoints", []) or [])
        waypoint_idx = int(getattr(loader, "waypoint_idx", 0))
        remaining_waypoints = max(0, len(waypoints) - waypoint_idx)
        active_waypoint_leg = remaining_waypoints > 0
        cmd_code = cmd_view.int_field("command_code", 0)
        on_ground = alt_agl <= self.rollout_alt_agl_m

        if self._should_arm_approach(
            loader=loader,
            truth=truth,
            alt_agl_m=alt_agl,
            heading_deg=heading_deg,
            ils_valid=ils_valid,
            loc_abs=loc_abs,
            gs_abs=gs_abs,
            dme_m=dme_m,
            remaining_waypoints=remaining_waypoints,
        ):
            transitioned = None
            if hasattr(loader, "_maybe_activate_post_waypoint_transition"):
                transitioned = loader._maybe_activate_post_waypoint_transition(sync_to_kernel=sync_to_kernel)
            elif hasattr(loader, "_activate_post_waypoint_transition"):
                transitioned = loader._activate_post_waypoint_transition(sync_to_kernel=sync_to_kernel)
            if transitioned is not None:
                cmd_code = mission_command_view(loader).int_field("command_code", cmd_code)

        phase_name = self._infer_phase_name(
            cmd_code=cmd_code,
            on_ground=on_ground,
            ground_speed_mps=ground_speed,
            alt_agl_m=alt_agl,
            dme_m=dme_m,
            remaining_waypoints=remaining_waypoints,
            total_waypoints=len(waypoints),
        )
        loader.mission_phase_name = phase_name

        intent = ef_py.LeaderIntent()
        intent.active = True
        intent.phase_id = self._phase_enum_for_name(phase_name)
        intent.command_code = int(
            command_code_for_phase_name(
                phase_name,
                has_waypoints=bool(waypoints),
                mission_cmd_code=cmd_code,
            )
        )
        task = getattr(loader, "task_order", None)
        route_ref_id = infer_route_ref_id(loader)
        recovery_base_id = infer_recovery_base_id(loader, task=task)
        recovery_runway_id = infer_recovery_runway_id(loader, task=task)
        recovery_approach_type = _recovery_approach_type_or_default(
            infer_recovery_approach_type(loader, task=task),
            _recovery_approach_none(),
        )
        intent.route_ref_id = int(route_ref_id if int(intent.command_code) == 3 and active_waypoint_leg else 0)
        intent.recovery_base_id = int(recovery_base_id)
        intent.recovery_runway_id = int(recovery_runway_id)
        intent.recovery_approach_type = recovery_approach_type
        intent.takeoff_procedure_id = _takeoff_procedure_or_default(
            getattr(task, "takeoff_procedure_id", None) if task is not None else None,
            _takeoff_procedure_unspecified(),
        )
        intent.takeoff_clearance_id = _takeoff_clearance_or_default(
            getattr(task, "takeoff_clearance_id", None) if task is not None else None,
            _takeoff_clearance_unspecified(),
        )
        intent.takeoff_interval_s = float(getattr(task, "takeoff_interval_s", 0.0)) if task is not None else 0.0
        intent.runway_slot_id = _runway_slot_or_default(
            getattr(task, "runway_slot_id", None) if task is not None else None,
            _runway_slot_unspecified(),
        )
        intent.cmd_heading_deg = cmd_view.float_field("target_heading", 0.0)
        if (
            int(intent.command_code) == 3
            and not active_waypoint_leg
            and str(getattr(loader, "c2_task_name", "")).strip().upper() == ScriptedC2TaskManager.TASK_RECOVER_LAND
        ):
            intent.cmd_heading_deg = _landing_reference_heading_deg(loader, intent.cmd_heading_deg)
        intent.cmd_altitude_m = cmd_view.float_field("target_altitude", 0.0)
        intent.cmd_speed_mps = cmd_view.float_field("target_speed", 0.0)
        intent.approach_armed = phase_name in LANDING_PHASE_NAMES
        intent.commit_to_land = phase_name in {"landing_final", "rollout"}
        intent.abort_flag = False
        apply_leader_intent_common_core_defaults(
            intent,
            order=task,
            task_name=str(getattr(loader, "c2_task_name", "") or "").strip().upper() or None,
            phase_name=phase_name,
            default_tactical_unit_id=int(getattr(loader, "agent_id", 0) or 0),
        )
        loader.leader_intent = intent

        prev_report = getattr(loader, "pilot_report", None)
        none_msg = getattr(ef_py.CommMsgType, "None")
        prev_type = getattr(prev_report, "report_type", none_msg) if prev_report is not None else none_msg
        if (phase_name == "rtb" or phase_name in LANDING_PHASE_NAMES) and prev_type != ef_py.CommMsgType.REP_RTB:
            loader.pilot_report = self._make_report(
                loader,
                report_type=ef_py.CommMsgType.REP_RTB,
                sim_time_s=sim_time_s,
                truth=truth,
            )
        elif prev_report is None:
            loader.pilot_report = self._make_report(
                loader,
                report_type=ef_py.CommMsgType.REP_WILCO,
                sim_time_s=sim_time_s,
                truth=truth,
            )

    def sync_to_kernel(self, loader: Any) -> None:
        if getattr(loader, "agent_id", None) is None:
            return
        sync_loader_command_chain(loader)

    def _build_task_order(self, loader: Any, sim_time_s: float = 0.0) -> ef_py.TaskOrder:
        order = ef_py.TaskOrder()
        cmd_view = mission_command_view(loader)
        order.active = True
        order.task_id = 1
        order.task_type = ef_py.TaskType.CAPMission if getattr(loader, "waypoints", None) else ef_py.TaskType.CAP
        order.priority = 1
        order.issuer_id = 0
        order.assignee_id = int(getattr(loader, "agent_id", 0) or 0)
        order.issue_time_s = float(sim_time_s)

        waypoints = list(getattr(loader, "waypoints", []) or [])
        if waypoints:
            anchor_idx = max(0, min(len(waypoints) - 1, len(waypoints) // 2))
            anchor = waypoints[anchor_idx]
            order.anchor_x_m = float(anchor.get("x", 0.0))
            order.anchor_y_m = float(anchor.get("y", 0.0))
            order.anchor_z_m = float(anchor.get("z", anchor.get("altitude_m", cmd_view.float_field("target_altitude", 0.0))))
            order.station_type = ef_py.StationType.RouteCAP
            if len(waypoints) >= 2:
                first = waypoints[0]
                last = waypoints[-1]
                dx = float(last.get("x", 0.0)) - float(first.get("x", 0.0))
                dy = float(last.get("y", 0.0)) - float(first.get("y", 0.0))
                order.station_leg_length_m = float(math.hypot(dx, dy))
        else:
            order.station_type = ef_py.StationType.Orbit

        order.target_altitude_m = cmd_view.float_field("target_altitude", 0.0)
        order.target_speed_mps = cmd_view.float_field("target_speed", 0.0)
        order.altitude_block_min_m = max(0.0, order.target_altitude_m - 500.0)
        order.altitude_block_max_m = max(order.altitude_block_min_m, order.target_altitude_m + 500.0)
        order.speed_min_mps = max(0.0, order.target_speed_mps - 40.0)
        order.speed_max_mps = max(order.speed_min_mps, order.target_speed_mps + 40.0)
        order = _apply_task_order_overrides(
            order,
            _scenario_task_order_cfg(loader),
            default_assignee_id=int(getattr(loader, "agent_id", 0) or 0),
        )
        if hasattr(order, "recovery_base_id") and int(getattr(order, "recovery_base_id", 0)) <= 0:
            order.recovery_base_id = int(infer_recovery_base_id(loader, task=order))
        if hasattr(order, "recovery_runway_id") and int(getattr(order, "recovery_runway_id", 0)) <= 0:
            order.recovery_runway_id = int(infer_recovery_runway_id(loader, task=order))
        if hasattr(order, "recovery_approach_type"):
            current = _recovery_approach_type_or_default(
                getattr(order, "recovery_approach_type", _recovery_approach_none()),
                _recovery_approach_none(),
            )
            if int(current) == int(_recovery_approach_none()):
                order.recovery_approach_type = _recovery_approach_type_or_default(
                    infer_recovery_approach_type(loader, task=order),
                    _recovery_approach_none(),
                )
        apply_task_order_common_core_defaults(
            order,
            task_name=str(getattr(loader, "c2_task_name", "") or "").strip().upper() or None,
        )
        return order

    def _make_report(self, loader: Any, *, report_type: Any, sim_time_s: float, truth: Any = None) -> ef_py.PilotReport:
        report = ef_py.PilotReport()
        report.active = True
        report.report_type = report_type
        report.sender_id = int(getattr(loader, "agent_id", 0) or 0)
        task = getattr(loader, "task_order", None)
        report.task_id = int(getattr(task, "task_id", 0))
        report.phase_id = int(self._phase_enum_for_name(getattr(loader, "mission_phase_name", "idle")))
        report.timestamp_s = float(sim_time_s)
        try:
            if truth is None:
                truth = get_policy_agent_observation(loader)
            report.location_x_m = float(getattr(truth, "x", 0.0))
            report.location_y_m = float(getattr(truth, "y", 0.0))
            report.location_z_m = float(getattr(truth, "z", 0.0))
        except Exception:
            pass
        apply_pilot_report_common_core_defaults(
            report,
            order=task,
            task_name=str(getattr(loader, "c2_task_name", "") or "").strip().upper() or None,
            phase_name=str(getattr(loader, "mission_phase_name", "idle") or "idle"),
            default_tactical_unit_id=int(getattr(loader, "agent_id", 0) or 0),
        )
        return report

    def _infer_phase_name(
        self,
        *,
        cmd_code: int,
        on_ground: bool,
        ground_speed_mps: float,
        alt_agl_m: float,
        dme_m: float,
        remaining_waypoints: int,
        total_waypoints: int,
    ) -> str:
        if is_landing_command_code(cmd_code):
            if on_ground:
                return "rollout"
            if dme_m <= self.landing_final_dme_m or alt_agl_m <= self.landing_final_alt_agl_m:
                return "landing_final"
            return "approach_armed"

        if on_ground:
            if ground_speed_mps <= self.scramble_ground_speed_max_mps:
                return "scramble"
            return "takeoff"

        if remaining_waypoints > max(self.terminal_waypoint_count, 2):
            if total_waypoints > 0 and remaining_waypoints == total_waypoints:
                return "departure"
            return "transit_to_station"
        if remaining_waypoints > 0:
            return "rtb"
        return "rtb"

    def _phase_enum_for_name(self, phase_name: str) -> Any:
        mapping = {
            "idle": ef_py.LeaderPhase.Idle,
            "scramble": ef_py.LeaderPhase.Scramble,
            "takeoff": ef_py.LeaderPhase.Takeoff,
            "departure": ef_py.LeaderPhase.Departure,
            "transit_to_station": ef_py.LeaderPhase.TransitToStation,
            "establish_cap": ef_py.LeaderPhase.EstablishCAP,
            "on_station": ef_py.LeaderPhase.OnStation,
            "reposition": ef_py.LeaderPhase.Reposition,
            "rtb": ef_py.LeaderPhase.RTB,
            "approach_armed": ef_py.LeaderPhase.ApproachArmed,
            "landing_final": ef_py.LeaderPhase.LandingFinal,
            "rollout": ef_py.LeaderPhase.Rollout,
            "abort": ef_py.LeaderPhase.Abort,
        }
        return mapping.get(str(phase_name).strip().lower(), ef_py.LeaderPhase.Idle)

    def _should_arm_approach(
        self,
        *,
        loader: Any,
        truth: Any,
        alt_agl_m: float,
        heading_deg: float,
        ils_valid: bool,
        loc_abs: float,
        gs_abs: float,
        dme_m: float,
        remaining_waypoints: int,
    ) -> bool:
        post = getattr(loader, "post_waypoint_transition", None)
        if not isinstance(post, dict) or not post:
            return False
        c2_task_name = str(getattr(loader, "c2_task_name", "")).strip().upper()
        if c2_task_name and c2_task_name != ScriptedC2TaskManager.TASK_RECOVER_LAND:
            return False
        if is_landing_command_code(mission_command_view(loader).int_field("command_code", 0)):
            return False
        if not is_landing_command_code(post.get("command_code", COMMAND_CODE_LANDING)):
            return False
        if c2_task_name == ScriptedC2TaskManager.TASK_RECOVER_LAND and remaining_waypoints <= 0:
            return True
        if remaining_waypoints > self.terminal_waypoint_count:
            return False
        if alt_agl_m <= self.rollout_alt_agl_m:
            return False
        if not ils_valid:
            return False
        if dme_m > self.approach_arm_dme_m:
            return False
        if alt_agl_m > self.approach_arm_alt_agl_max_m:
            return False
        if loc_abs > self.approach_arm_loc_abs_max:
            return False
        if gs_abs > self.approach_arm_gs_abs_max:
            return False

        try:
            beacon = loader._nearest_ils_beacon(float(getattr(truth, "x", 0.0)), float(getattr(truth, "y", 0.0)))
        except Exception:
            beacon = None
        if beacon is not None:
            runway_heading = float(beacon.get("heading", 0.0))
            heading_err = abs((heading_deg - runway_heading + 180.0) % 360.0 - 180.0)
            if heading_err > self.approach_arm_heading_error_deg_max:
                return False

        valid_runway_frame = False
        along_m = 0.0
        cross_m = 0.0
        try:
            valid_runway_frame, along_m, cross_m, _rw_len, _rw_wid = loader.get_runway_local_frame(
                float(getattr(truth, "x", 0.0)),
                float(getattr(truth, "y", 0.0)),
            )
        except Exception:
            valid_runway_frame = False

        if self.approach_arm_require_runway_frame and not bool(valid_runway_frame):
            return False
        if bool(valid_runway_frame):
            if float(along_m) < self.approach_arm_along_min_m:
                return False
            if abs(float(cross_m)) > self.approach_arm_cross_abs_max_m:
                return False
        return True


class ScriptedC2TaskManager:
    """
    Scripted C2 task-state manager.

    The C2 layer is allowed to consume:
    - shared situation data (ownship state / recovery geometry / fuel)
    - leader pilot reports

    It is *not* allowed to directly author low-level mission commands. Those remain the
    responsibility of the leader layer.
    """

    TASK_IDLE = "TASK_IDLE"
    TASK_SCRAMBLE = "TASK_SCRAMBLE"
    TASK_CAP = "TASK_CAP"
    TASK_RTB = "TASK_RTB"
    TASK_RECOVER_LAND = "TASK_RECOVER_LAND"

    def __init__(
        self,
        *,
        scramble_complete_alt_agl_m: float = 120.0,
        scramble_complete_ground_speed_mps: float = 65.0,
        station_entry_radius_scale: float = 1.25,
        station_entry_altitude_slack_m: float = 250.0,
        station_entry_speed_slack_mps: float = 20.0,
        auto_rtb_on_station_complete: bool = True,
        recover_arm_dme_m: float = 18000.0,
        recover_arm_alt_agl_max_m: float = 1800.0,
        recover_arm_loc_abs_max: float = 0.8,
        recover_arm_gs_abs_max: float = 1.5,
        recover_arm_require_runway_frame: bool = True,
        recover_arm_along_min_m: float = -1000.0,
        recover_arm_cross_abs_max_m: float = 3500.0,
        recover_arm_heading_abs_max_deg: float = 85.0,
    ):
        self.scramble_complete_alt_agl_m = float(scramble_complete_alt_agl_m)
        self.scramble_complete_ground_speed_mps = float(scramble_complete_ground_speed_mps)
        self.station_entry_radius_scale = float(station_entry_radius_scale)
        self.station_entry_altitude_slack_m = float(station_entry_altitude_slack_m)
        self.station_entry_speed_slack_mps = float(station_entry_speed_slack_mps)
        self.auto_rtb_on_station_complete = bool(auto_rtb_on_station_complete)
        self.recover_arm_dme_m = float(recover_arm_dme_m)
        self.recover_arm_alt_agl_max_m = float(recover_arm_alt_agl_max_m)
        self.recover_arm_loc_abs_max = float(recover_arm_loc_abs_max)
        self.recover_arm_gs_abs_max = float(recover_arm_gs_abs_max)
        self.recover_arm_require_runway_frame = bool(recover_arm_require_runway_frame)
        self.recover_arm_along_min_m = float(recover_arm_along_min_m)
        self.recover_arm_cross_abs_max_m = float(recover_arm_cross_abs_max_m)
        self.recover_arm_heading_abs_max_deg = float(recover_arm_heading_abs_max_deg)
        self.current_task_name = self.TASK_SCRAMBLE
        self.station_entry_time_s: float | None = None

    @staticmethod
    def task_name_to_id(task_name: str | None) -> int:
        mapping = {
            ScriptedC2TaskManager.TASK_IDLE: 0,
            ScriptedC2TaskManager.TASK_SCRAMBLE: 1,
            ScriptedC2TaskManager.TASK_CAP: 2,
            ScriptedC2TaskManager.TASK_RTB: 3,
            ScriptedC2TaskManager.TASK_RECOVER_LAND: 4,
        }
        return int(mapping.get(str(task_name or "").strip().upper(), 0))

    def _apply_loader_state(
        self,
        loader: Any,
        *,
        task_name: str,
        sim_time_s: float,
        transitioned: bool,
        transition_reason: str,
        report_valid: bool,
        report_reason: str,
    ) -> dict[str, Any]:
        loader.c2_task_name = str(task_name)
        loader.c2_task_id = int(self.task_name_to_id(task_name))
        loader.c2_transitioned = bool(transitioned)
        loader.c2_transition_reason = str(transition_reason)
        loader.c2_last_update_s = float(sim_time_s)
        loader.c2_report_valid = bool(report_valid)
        loader.c2_report_reason = str(report_reason)
        if self.station_entry_time_s is None:
            loader.c2_on_station_elapsed_s = 0.0
        else:
            loader.c2_on_station_elapsed_s = max(0.0, float(sim_time_s) - float(self.station_entry_time_s))
        return {
            "task_name": str(task_name),
            "task_id": int(self.task_name_to_id(task_name)),
            "transitioned": bool(transitioned),
            "transition_reason": str(transition_reason),
            "report_valid": bool(report_valid),
            "report_reason": str(report_reason),
            "on_station_elapsed_s": float(getattr(loader, "c2_on_station_elapsed_s", 0.0)),
        }

    def reset(self, loader: Any, sim_time_s: float = 0.0, *, truth: Any = None, inst: Any = None, sync_to_kernel: bool = True) -> dict[str, Any]:
        _ = (truth, inst, sync_to_kernel)
        scenario_data = getattr(loader, "scenario_data", {}) or {}
        meta = scenario_data.get("meta", {}) if isinstance(scenario_data, dict) else {}
        init_task = meta.get("initial_c2_task", self.TASK_SCRAMBLE) if isinstance(meta, dict) else self.TASK_SCRAMBLE
        self.current_task_name = str(init_task or self.TASK_SCRAMBLE).strip().upper()
        self.station_entry_time_s = None
        self._retask_order(loader, task_name=self.current_task_name, sim_time_s=float(sim_time_s))
        return self._apply_loader_state(
            loader,
            task_name=self.current_task_name,
            sim_time_s=float(sim_time_s),
            transitioned=False,
            transition_reason="reset",
            report_valid=False,
            report_reason="",
        )

    def _task_cfg(self, loader: Any) -> dict[str, Any]:
        scenario_data = getattr(loader, "scenario_data", {}) or {}
        cfg = scenario_data.get("c2_logic", {}) if isinstance(scenario_data, dict) else {}
        return cfg if isinstance(cfg, dict) else {}

    def _scenario_task_order_cfg(self, loader: Any) -> dict[str, Any] | None:
        scenario_data = getattr(loader, "scenario_data", {}) or {}
        if not isinstance(scenario_data, dict):
            return None
        order_cfg = scenario_data.get("task_order", None)
        return order_cfg if isinstance(order_cfg, dict) else None

    @staticmethod
    def _has_route_waypoints(loader: Any) -> bool:
        return bool(list(getattr(loader, "waypoints", []) or []))

    @staticmethod
    def _landing_post_transition_pending(loader: Any) -> bool:
        post = getattr(loader, "post_waypoint_transition", None)
        if not isinstance(post, dict) or not post:
            return False
        return bool(is_landing_command_code(post.get("command_code", COMMAND_CODE_LANDING)))

    def _route_exhausted_for_recovery(self, loader: Any) -> bool:
        if not self._landing_post_transition_pending(loader):
            return False
        waypoints = list(getattr(loader, "waypoints", []) or [])
        if not waypoints:
            return False
        waypoint_idx = int(getattr(loader, "waypoint_idx", 0) or 0)
        return waypoint_idx >= len(waypoints)

    def _active_waypoint_targets(self, loader: Any) -> tuple[float, float, float | None, float | None]:
        cmd_view = mission_command_view(loader)
        target_altitude_m = cmd_view.float_field("target_altitude", 0.0)
        target_speed_mps = cmd_view.float_field("target_speed", 0.0)
        anchor_x_m = None
        anchor_y_m = None
        waypoints = list(getattr(loader, "waypoints", []) or [])
        waypoint_idx = int(getattr(loader, "waypoint_idx", 0) or 0)
        if 0 <= waypoint_idx < len(waypoints):
            wp = waypoints[waypoint_idx]
            target_altitude_m = float(wp.get("altitude_m", target_altitude_m))
            target_speed_mps = float(wp.get("speed_mps", target_speed_mps))
            anchor_x_m = float(wp.get("x", 0.0))
            anchor_y_m = float(wp.get("y", 0.0))
        return target_altitude_m, target_speed_mps, anchor_x_m, anchor_y_m

    @staticmethod
    def _retarget_block(
        order: Any,
        *,
        target_attr: str,
        min_attr: str,
        max_attr: str,
        target_value: float,
        default_lower_margin: float,
        default_upper_margin: float,
        floor_value: float = 0.0,
    ) -> None:
        current_target = float(getattr(order, target_attr, target_value))
        current_min = float(getattr(order, min_attr, floor_value))
        current_max = float(getattr(order, max_attr, floor_value))

        if current_max > current_min + 1.0e-6:
            lower_margin = max(0.0, current_target - current_min)
            upper_margin = max(0.0, current_max - current_target)
        else:
            lower_margin = max(0.0, float(default_lower_margin))
            upper_margin = max(0.0, float(default_upper_margin))

        target_value = float(target_value)
        setattr(order, target_attr, target_value)
        new_min = max(float(floor_value), target_value - lower_margin)
        new_max = max(new_min, target_value + upper_margin)
        setattr(order, min_attr, float(new_min))
        setattr(order, max_attr, float(new_max))

    def _retask_order(self, loader: Any, *, task_name: str, sim_time_s: float) -> None:
        order = getattr(loader, "task_order", None)
        if order is None:
            return

        task_name = str(task_name).strip().upper()
        task_type_by_name = {
            self.TASK_IDLE: getattr(ef_py.TaskType, "Idle"),
            self.TASK_SCRAMBLE: getattr(ef_py.TaskType, "Scramble"),
            self.TASK_CAP: getattr(ef_py.TaskType, "CAP"),
            self.TASK_RTB: getattr(ef_py.TaskType, "RTB"),
            self.TASK_RECOVER_LAND: getattr(ef_py.TaskType, "RecoverLand"),
        }
        order.task_type = task_type_by_name.get(task_name, getattr(order, "task_type", getattr(ef_py.TaskType, "Idle")))

        if task_name in (self.TASK_SCRAMBLE, self.TASK_CAP):
            scenario_order_cfg = self._scenario_task_order_cfg(loader)
            if isinstance(scenario_order_cfg, dict) and scenario_order_cfg:
                _apply_task_order_overrides(
                    order,
                    scenario_order_cfg,
                    default_assignee_id=int(getattr(loader, "agent_id", 0) or 0),
                )
                order.issue_time_s = float(sim_time_s)
            order.task_type = task_type_by_name.get(task_name, getattr(order, "task_type", getattr(ef_py.TaskType, "Idle")))
            if self._has_route_waypoints(loader):
                target_altitude_m, target_speed_mps, _anchor_x_m, _anchor_y_m = self._active_waypoint_targets(loader)
                # Route-driven CAP missions inherit the live leg altitude/speed target
                # while preserving the task block half-widths from the authored order.
                self._retarget_block(
                    order,
                    target_attr="target_altitude_m",
                    min_attr="altitude_block_min_m",
                    max_attr="altitude_block_max_m",
                    target_value=float(target_altitude_m),
                    default_lower_margin=500.0,
                    default_upper_margin=500.0,
                    floor_value=0.0,
                )
                self._retarget_block(
                    order,
                    target_attr="target_speed_mps",
                    min_attr="speed_min_mps",
                    max_attr="speed_max_mps",
                    target_value=float(target_speed_mps),
                    default_lower_margin=40.0,
                    default_upper_margin=40.0,
                    floor_value=40.0,
                )
            apply_task_order_common_core_defaults(
                order,
                task_name=task_name,
                force_task_family=True,
                force_coordination_mode=True,
            )
            return

        target_altitude_m, target_speed_mps, anchor_x_m, anchor_y_m = self._active_waypoint_targets(loader)

        if anchor_x_m is not None:
            order.anchor_x_m = float(anchor_x_m)
        if anchor_y_m is not None:
            order.anchor_y_m = float(anchor_y_m)
        order.anchor_z_m = float(target_altitude_m)
        order.target_altitude_m = float(target_altitude_m)
        order.target_speed_mps = float(target_speed_mps)
        order.issue_time_s = float(sim_time_s)

        if task_name == self.TASK_RTB:
            order.altitude_block_min_m = max(0.0, float(target_altitude_m) - 500.0)
            order.altitude_block_max_m = max(float(order.altitude_block_min_m), float(target_altitude_m) + 500.0)
            order.speed_min_mps = max(40.0, float(target_speed_mps) - 40.0)
            order.speed_max_mps = max(float(order.speed_min_mps), float(target_speed_mps) + 40.0)
            apply_task_order_common_core_defaults(
                order,
                task_name=task_name,
                force_task_family=True,
                force_coordination_mode=True,
            )
            return

        if task_name == self.TASK_RECOVER_LAND:
            order.altitude_block_min_m = 0.0
            order.altitude_block_max_m = max(350.0, float(target_altitude_m) + 350.0)
            order.speed_min_mps = max(55.0, float(target_speed_mps) - 20.0)
            order.speed_max_mps = max(float(order.speed_min_mps), float(target_speed_mps) + 20.0)
            apply_task_order_common_core_defaults(
                order,
                task_name=task_name,
                force_task_family=True,
                force_coordination_mode=True,
            )
            return

        apply_task_order_common_core_defaults(
            order,
            task_name=task_name,
            force_task_family=True,
            force_coordination_mode=True,
        )

    def _fuel_margin_frac(self, loader: Any, *, inst: Any = None) -> tuple[float, float]:
        if inst is None:
            inst = get_policy_instrument_state(loader)
        fuel_total_kg = (
            float(max(0.0, getattr(inst, "fuel_internal", 0.0) + getattr(inst, "fuel_external", 0.0)))
            if inst is not None
            else 0.0
        )
        task = getattr(loader, "task_order", None)
        bingo_kg = float(max(0.0, getattr(task, "fuel_bingo_override_kg", 0.0) if task is not None else 0.0))
        if bingo_kg <= 1.0:
            return fuel_total_kg, 1.0
        return fuel_total_kg, float((fuel_total_kg - bingo_kg) / max(bingo_kg, 1.0))

    def _station_metrics(self, loader: Any, *, truth: Any = None, inst: Any = None) -> dict[str, float | bool]:
        task = getattr(loader, "task_order", None)
        if truth is None:
            truth = get_policy_agent_observation(loader)
        if inst is None:
            inst = get_policy_instrument_state(loader)
        if truth is None or inst is None:
            return {"near_station": False, "anchor_dist_m": float("inf")}
        anchor_x = float(getattr(task, "anchor_x_m", 0.0) if task is not None else 0.0)
        anchor_y = float(getattr(task, "anchor_y_m", 0.0) if task is not None else 0.0)
        dx = anchor_x - float(getattr(truth, "x", 0.0))
        dy = anchor_y - float(getattr(truth, "y", 0.0))
        anchor_dist_m = float(math.hypot(dx, dy))
        station_radius_m = float(max(1000.0, getattr(task, "station_radius_m", 12000.0) if task is not None else 12000.0))
        near_station = anchor_dist_m <= station_radius_m * max(1.0, self.station_entry_radius_scale)
        alt_ok = True
        spd_ok = True
        if task is not None:
            alt_baro = float(getattr(inst, "alt_baro", 0.0))
            ias = float(getattr(inst, "ias", 0.0))
            alt_lo = float(getattr(task, "altitude_block_min_m", 0.0))
            alt_hi = float(getattr(task, "altitude_block_max_m", 0.0))
            spd_lo = float(getattr(task, "speed_min_mps", 0.0))
            spd_hi = float(getattr(task, "speed_max_mps", 0.0))
            if alt_hi > alt_lo + 1.0:
                alt_ok = (alt_lo - self.station_entry_altitude_slack_m) <= alt_baro <= (alt_hi + self.station_entry_altitude_slack_m)
            if spd_hi > spd_lo + 1.0:
                spd_ok = (spd_lo - self.station_entry_speed_slack_mps) <= ias <= (spd_hi + self.station_entry_speed_slack_mps)
        return {
            "near_station": bool(near_station and alt_ok and spd_ok),
            "anchor_dist_m": float(anchor_dist_m),
        }

    def _recovery_ready(self, loader: Any, *, truth: Any = None, inst: Any = None) -> bool:
        if truth is None:
            truth = get_policy_agent_observation(loader)
        if inst is None:
            inst = get_policy_instrument_state(loader)
        if truth is None or inst is None:
            return False
        try:
            ils = loader.get_ils_observation(
                float(getattr(truth, "x", 0.0)),
                float(getattr(truth, "y", 0.0)),
                float(getattr(inst, "alt_baro", 0.0)),
            )
        except Exception:
            return False
        ils_valid = float(ils[0]) > 0.5 if len(ils) >= 1 else False
        loc_abs = abs(float(ils[1])) if len(ils) >= 2 else float("inf")
        gs_abs = abs(float(ils[2])) if len(ils) >= 3 else float("inf")
        dme_m = float(ils[3]) if len(ils) >= 4 else float("inf")
        alt_agl_m = float(getattr(inst, "alt_radar", 0.0))
        cfg = self._task_cfg(loader)

        recover_arm_dme_m = float(cfg.get("recover_arm_dme_m", self.recover_arm_dme_m))
        recover_arm_alt_agl_max_m = float(cfg.get("recover_arm_alt_agl_max_m", self.recover_arm_alt_agl_max_m))
        recover_arm_loc_abs_max = float(cfg.get("recover_arm_loc_abs_max", self.recover_arm_loc_abs_max))
        recover_arm_gs_abs_max = float(cfg.get("recover_arm_gs_abs_max", self.recover_arm_gs_abs_max))
        recover_arm_require_runway_frame = bool(
            cfg.get("recover_arm_require_runway_frame", self.recover_arm_require_runway_frame)
        )
        recover_arm_along_min_m = float(cfg.get("recover_arm_along_min_m", self.recover_arm_along_min_m))
        recover_arm_cross_abs_max_m = float(cfg.get("recover_arm_cross_abs_max_m", self.recover_arm_cross_abs_max_m))
        recover_arm_heading_abs_max_deg = float(
            cfg.get("recover_arm_heading_abs_max_deg", self.recover_arm_heading_abs_max_deg)
        )

        valid_runway_frame = False
        along_m = 0.0
        cross_m = 0.0
        try:
            valid_runway_frame, along_m, cross_m, _rw_len, _rw_wid = loader.get_runway_local_frame(
                float(getattr(truth, "x", 0.0)),
                float(getattr(truth, "y", 0.0)),
            )
        except Exception:
            valid_runway_frame = False

        if recover_arm_require_runway_frame and not bool(valid_runway_frame):
            return False
        if bool(valid_runway_frame):
            if float(along_m) < recover_arm_along_min_m:
                return False
            if abs(float(cross_m)) > recover_arm_cross_abs_max_m:
                return False

        try:
            beacon = loader._nearest_ils_beacon(float(getattr(truth, "x", 0.0)), float(getattr(truth, "y", 0.0)))
        except Exception:
            beacon = None
        if beacon is None:
            return False
        runway_heading_err_deg = abs(
            _wrap_deg(float(getattr(inst, "heading", 0.0)) - float(beacon.get("heading", 0.0)))
        )
        return bool(
            ils_valid
            and dme_m <= recover_arm_dme_m
            and alt_agl_m <= recover_arm_alt_agl_max_m
            and loc_abs <= recover_arm_loc_abs_max
            and gs_abs <= recover_arm_gs_abs_max
            and runway_heading_err_deg <= recover_arm_heading_abs_max_deg
        )

    def _report_assessment(self, loader: Any, *, truth: Any = None, inst: Any = None) -> tuple[bool, str]:
        report = getattr(loader, "pilot_report", None)
        if report is None or not bool(getattr(report, "active", False)):
            return False, "no_report"
        task = getattr(loader, "task_order", None)
        report_type = int(getattr(report, "report_type", getattr(ef_py.CommMsgType, "None")))
        if report_type == int(getattr(ef_py.CommMsgType, "REP_ON_STATION")):
            metrics = self._station_metrics(loader, truth=truth, inst=inst)
            return (bool(metrics["near_station"]), "on_station" if bool(metrics["near_station"]) else "station_not_reached")
        if report_type == int(getattr(ef_py.CommMsgType, "REP_RTB")):
            return True, "rtb_report"
        if report_type == int(getattr(ef_py.CommMsgType, "WARN_BINGO")):
            _fuel_total_kg, margin = self._fuel_margin_frac(loader, inst=inst)
            return (bool(margin <= 0.15), "bingo_report" if margin <= 0.15 else "fuel_not_bingo")
        if report_type == int(getattr(ef_py.CommMsgType, "REP_UNABLE")):
            return True, "unable_report"
        if report_type == int(getattr(ef_py.CommMsgType, "REP_WILCO")):
            return True, "wilco_report"
        return False, "unsupported_report"

    def update(self, loader: Any, sim_time_s: float = 0.0, *, truth: Any = None, inst: Any = None, sync_to_kernel: bool = True) -> dict[str, Any]:
        _ = sync_to_kernel
        cfg = self._task_cfg(loader)
        report_valid, report_reason = self._report_assessment(loader, truth=truth, inst=inst)
        report = getattr(loader, "pilot_report", None)
        report_type = int(getattr(report, "report_type", getattr(ef_py.CommMsgType, "None"))) if report is not None else int(getattr(ef_py.CommMsgType, "None"))

        if inst is None:
            inst = get_policy_instrument_state(loader)
        alt_agl_m = float(getattr(inst, "alt_radar", 0.0)) if inst is not None else 0.0
        ground_speed_mps = float(getattr(inst, "ground_speed", 0.0)) if inst is not None else 0.0

        task = getattr(loader, "task_order", None)
        on_station_time_s = float(getattr(task, "on_station_time_s", 0.0) if task is not None else 0.0)
        transitioned = False
        reason = ""
        current = str(self.current_task_name)

        if current == self.TASK_SCRAMBLE:
            if alt_agl_m >= float(cfg.get("scramble_complete_alt_agl_m", self.scramble_complete_alt_agl_m)) and ground_speed_mps >= float(cfg.get("scramble_complete_ground_speed_mps", self.scramble_complete_ground_speed_mps)):
                current = self.TASK_CAP
                transitioned = True
                reason = "scramble_complete"

        elif current == self.TASK_CAP:
            metrics = self._station_metrics(loader, truth=truth, inst=inst)
            if bool(metrics["near_station"]):
                if self.station_entry_time_s is None:
                    self.station_entry_time_s = float(sim_time_s)
            else:
                self.station_entry_time_s = None
            if report_type in (
                int(getattr(ef_py.CommMsgType, "REP_RTB")),
                int(getattr(ef_py.CommMsgType, "WARN_BINGO")),
                int(getattr(ef_py.CommMsgType, "REP_UNABLE")),
            ) and report_valid:
                current = self.TASK_RTB
                transitioned = True
                reason = report_reason
            elif bool(cfg.get("auto_rtb_on_station_complete", self.auto_rtb_on_station_complete)) and self.station_entry_time_s is not None and on_station_time_s > 1.0:
                elapsed = max(0.0, float(sim_time_s) - float(self.station_entry_time_s))
                if elapsed >= on_station_time_s:
                    current = self.TASK_RTB
                    transitioned = True
                    reason = "station_time_complete"

        elif current == self.TASK_RTB:
            if self._route_exhausted_for_recovery(loader):
                current = self.TASK_RECOVER_LAND
                transitioned = True
                reason = "route_exhausted_recovery_final"
            elif self._recovery_ready(loader, truth=truth, inst=inst) and report_type in (
                int(getattr(ef_py.CommMsgType, "REP_RTB")),
                int(getattr(ef_py.CommMsgType, "WARN_BINGO")),
                int(getattr(ef_py.CommMsgType, "REP_UNABLE")),
            ):
                current = self.TASK_RECOVER_LAND
                transitioned = True
                reason = "recovery_window_open"

        self.current_task_name = str(current)
        self._retask_order(loader, task_name=self.current_task_name, sim_time_s=float(sim_time_s))
        return self._apply_loader_state(
            loader,
            task_name=self.current_task_name,
            sim_time_s=float(sim_time_s),
            transitioned=transitioned,
            transition_reason=reason,
            report_valid=report_valid,
            report_reason=report_reason,
        )
