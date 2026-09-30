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
)
from python.simulation.air.tasking import apply_task_order_overrides as _apply_task_order_overrides
from python.tasking_contracts.common.mission_defs import (
    COMMAND_CODE_LANDING,
    LANDING_PHASE_NAMES,
    TAKEOFF_PHASE_NAMES,
    command_code_for_phase_name,
    is_landing_command_code,
    parse_command_code,
)
from python.tasking_contracts.air.tasking.c2_manager import ScriptedC2TaskManager as _ScriptedC2TaskManager
from python.tasking_contracts.air.tasking.leader_phase_policy import (
    LeaderPhaseInput,
    LeaderPhasePolicy,
    ScriptedLeaderPhasePolicy,
)
from python.tasking_contracts.air.tasking.leader_approach_policy import (
    LeaderApproachInput,
    LeaderApproachPolicy,
    ScriptedLeaderApproachPolicy,
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
        departure_route_alt_agl_m: float = 140.0,
        phase_policy: LeaderPhasePolicy | None = None,
        approach_policy: LeaderApproachPolicy | None = None,
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
        self.departure_route_alt_agl_m = max(self.rollout_alt_agl_m, float(departure_route_alt_agl_m))
        self.phase_policy = phase_policy or ScriptedLeaderPhasePolicy()
        if not isinstance(self.phase_policy, LeaderPhasePolicy):
            raise TypeError("phase_policy must implement LeaderPhasePolicy")
        self.approach_policy = approach_policy or ScriptedLeaderApproachPolicy()
        if not isinstance(self.approach_policy, LeaderApproachPolicy):
            raise TypeError("approach_policy must implement LeaderApproachPolicy")

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

        phase_name = self.phase_policy.decide(
            LeaderPhaseInput(
                command_code=cmd_code,
                on_ground=on_ground,
                ground_speed_mps=ground_speed,
                altitude_agl_m=alt_agl,
                dme_m=dme_m,
                remaining_waypoints=remaining_waypoints,
                total_waypoints=len(waypoints),
                terminal_waypoint_count=self.terminal_waypoint_count,
                scramble_ground_speed_max_mps=self.scramble_ground_speed_max_mps,
                departure_route_alt_agl_m=self.departure_route_alt_agl_m,
                landing_final_dme_m=self.landing_final_dme_m,
                landing_final_alt_agl_m=self.landing_final_alt_agl_m,
            )
        ).phase_name
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
            and str(getattr(loader, "c2_task_name", "")).strip().upper() == _ScriptedC2TaskManager.TASK_RECOVER_LAND
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
        current_command_code = mission_command_view(loader).int_field("command_code", 0)
        raw_post_command_code = post.get("command_code")
        post_command_code = parse_command_code(
            raw_post_command_code,
            default=COMMAND_CODE_LANDING,
        )
        if raw_post_command_code is not None and post_command_code is None:
            return False
        if c2_task_name and c2_task_name != _ScriptedC2TaskManager.TASK_RECOVER_LAND:
            return False
        if is_landing_command_code(current_command_code) or not is_landing_command_code(post_command_code):
            return False
        post_transition_ready = False
        if c2_task_name == _ScriptedC2TaskManager.TASK_RECOVER_LAND and remaining_waypoints <= 0:
            ready = getattr(loader, "_post_waypoint_transition_ready", None)
            post_transition_ready = bool(ready()) if callable(ready) else False

        heading_err = 0.0
        try:
            beacon = loader._nearest_ils_beacon(float(getattr(truth, "x", 0.0)), float(getattr(truth, "y", 0.0)))
        except Exception:
            beacon = None
        if beacon is not None:
            runway_heading = float(beacon.get("heading", 0.0))
            heading_err = abs((heading_deg - runway_heading + 180.0) % 360.0 - 180.0)

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

        return self.approach_policy.decide(
            LeaderApproachInput(
                post_transition_pending=True,
                c2_task_allows_approach=(
                    not c2_task_name or c2_task_name == _ScriptedC2TaskManager.TASK_RECOVER_LAND
                ),
                c2_recovery_task=c2_task_name == _ScriptedC2TaskManager.TASK_RECOVER_LAND,
                current_command_code=current_command_code,
                post_transition_command_code=post_command_code,
                remaining_waypoints=int(remaining_waypoints),
                terminal_waypoint_count=self.terminal_waypoint_count,
                post_transition_ready=post_transition_ready,
                altitude_agl_m=float(alt_agl_m),
                rollout_alt_agl_m=self.rollout_alt_agl_m,
                max_altitude_agl_m=self.approach_arm_alt_agl_max_m,
                ils_valid=bool(ils_valid),
                dme_m=float(dme_m),
                max_dme_m=self.approach_arm_dme_m,
                localizer_abs=float(loc_abs),
                max_localizer_abs=self.approach_arm_loc_abs_max,
                glide_slope_abs=float(gs_abs),
                max_glide_slope_abs=self.approach_arm_gs_abs_max,
                runway_heading_error_deg=float(heading_err),
                max_runway_heading_error_deg=self.approach_arm_heading_error_deg_max,
                runway_frame_valid=bool(valid_runway_frame),
                require_runway_frame=self.approach_arm_require_runway_frame,
                runway_along_m=float(along_m),
                min_runway_along_m=self.approach_arm_along_min_m,
                runway_cross_m=float(cross_m),
                max_runway_cross_abs_m=self.approach_arm_cross_abs_max_m,
            )
        ).arm
