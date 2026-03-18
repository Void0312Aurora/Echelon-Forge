from __future__ import annotations

import math
from typing import Any

import ef_py
from python.rl.mission_defs import (
    COMMAND_CODE_LANDING,
    LANDING_PHASE_NAMES,
    TAKEOFF_PHASE_NAMES,
    command_code_for_phase_name,
    is_landing_command_code,
)


def build_kernel_mission_command(loader: Any) -> ef_py.MissionCommand:
    """
    Build the kernel-facing MissionCommand from the latest leader intent first,
    falling back to the loader's mission_cmd dictionary for legacy fields.
    """
    cmd = ef_py.MissionCommand()
    cmd.active = True

    mission_cmd = getattr(loader, "mission_cmd", {}) or {}
    leader_intent = getattr(loader, "leader_intent", None)

    cmd.command_code = int(getattr(leader_intent, "command_code", mission_cmd.get("command_code", 0)))
    cmd.cmd_heading_deg = float(getattr(leader_intent, "cmd_heading_deg", mission_cmd.get("target_heading", 0.0)))
    cmd.cmd_altitude_m = float(getattr(leader_intent, "cmd_altitude_m", mission_cmd.get("target_altitude", 0.0)))
    cmd.cmd_speed_mps = float(getattr(leader_intent, "cmd_speed_mps", mission_cmd.get("target_speed", 0.0)))
    cmd.formation_id = int(getattr(leader_intent, "formation_id", 0))
    cmd.form_offset_x = float(getattr(leader_intent, "form_offset_x", 0.0))
    cmd.form_offset_y = float(getattr(leader_intent, "form_offset_y", 0.0))
    cmd.form_offset_z = float(getattr(leader_intent, "form_offset_z", 0.0))
    cmd.assigned_target_id = int(getattr(leader_intent, "assigned_target_id", 0))
    cmd.authorization_to_fire = bool(getattr(leader_intent, "authorization_to_fire", False))
    return cmd


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
        self.landing_final_dme_m = float(landing_final_dme_m)
        self.landing_final_alt_agl_m = float(landing_final_alt_agl_m)
        self.rollout_alt_agl_m = float(rollout_alt_agl_m)
        self.scramble_ground_speed_max_mps = float(scramble_ground_speed_max_mps)

    def reset(self, loader: Any, sim_time_s: float = 0.0) -> None:
        loader.task_order = self._build_task_order(loader, sim_time_s=sim_time_s)
        loader.leader_intent = ef_py.LeaderIntent()
        loader.pilot_report = self._make_report(
            loader,
            report_type=ef_py.CommMsgType.REP_WILCO,
            sim_time_s=sim_time_s,
        )
        self.update(loader, sim_time_s=sim_time_s)

    def update(self, loader: Any, sim_time_s: float = 0.0) -> None:
        if getattr(loader, "agent_id", None) is None:
            return

        if getattr(loader, "task_order", None) is None:
            loader.task_order = self._build_task_order(loader, sim_time_s=sim_time_s)

        truth = loader.sim.get_agent_observation(loader.agent_id)
        inst = loader.sim.get_instrument_state(loader.agent_id)

        alt_agl = float(getattr(inst, "alt_radar", 0.0))
        ground_speed = float(getattr(inst, "ground_speed", 0.0))
        heading_deg = float(getattr(truth, "heading", 0.0))

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
        cmd_code = int(getattr(loader, "mission_cmd", {}).get("command_code", 0))
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
            loader._activate_post_waypoint_transition()
            cmd_code = int(getattr(loader, "mission_cmd", {}).get("command_code", cmd_code))

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
        intent.cmd_heading_deg = float(getattr(loader, "mission_cmd", {}).get("target_heading", 0.0))
        intent.cmd_altitude_m = float(getattr(loader, "mission_cmd", {}).get("target_altitude", 0.0))
        intent.cmd_speed_mps = float(getattr(loader, "mission_cmd", {}).get("target_speed", 0.0))
        intent.approach_armed = phase_name in LANDING_PHASE_NAMES
        intent.commit_to_land = phase_name in {"landing_final", "rollout"}
        intent.abort_flag = False
        loader.leader_intent = intent

        prev_report = getattr(loader, "pilot_report", None)
        none_msg = getattr(ef_py.CommMsgType, "None")
        prev_type = getattr(prev_report, "report_type", none_msg) if prev_report is not None else none_msg
        if phase_name in LANDING_PHASE_NAMES and prev_type != ef_py.CommMsgType.REP_RTB:
            loader.pilot_report = self._make_report(
                loader,
                report_type=ef_py.CommMsgType.REP_RTB,
                sim_time_s=sim_time_s,
            )
        elif prev_report is None:
            loader.pilot_report = self._make_report(
                loader,
                report_type=ef_py.CommMsgType.REP_WILCO,
                sim_time_s=sim_time_s,
            )

    def sync_to_kernel(self, loader: Any) -> None:
        if getattr(loader, "agent_id", None) is None:
            return
        try:
            if getattr(loader, "task_order", None) is not None and hasattr(loader.sim, "set_task_order"):
                loader.sim.set_task_order(loader.agent_id, loader.task_order)
        except Exception:
            pass
        try:
            if getattr(loader, "leader_intent", None) is not None and hasattr(loader.sim, "set_leader_intent"):
                loader.sim.set_leader_intent(loader.agent_id, loader.leader_intent)
        except Exception:
            pass
        try:
            if getattr(loader, "pilot_report", None) is not None and hasattr(loader.sim, "set_pilot_report"):
                loader.sim.set_pilot_report(loader.agent_id, loader.pilot_report)
        except Exception:
            pass

    def _build_task_order(self, loader: Any, sim_time_s: float = 0.0) -> ef_py.TaskOrder:
        order = ef_py.TaskOrder()
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
            order.anchor_z_m = float(anchor.get("z", anchor.get("altitude_m", getattr(loader, "mission_cmd", {}).get("target_altitude", 0.0))))
            order.station_type = ef_py.StationType.RouteCAP
            if len(waypoints) >= 2:
                first = waypoints[0]
                last = waypoints[-1]
                dx = float(last.get("x", 0.0)) - float(first.get("x", 0.0))
                dy = float(last.get("y", 0.0)) - float(first.get("y", 0.0))
                order.station_leg_length_m = float(math.hypot(dx, dy))
        else:
            order.station_type = ef_py.StationType.Orbit

        order.target_altitude_m = float(getattr(loader, "mission_cmd", {}).get("target_altitude", 0.0))
        order.target_speed_mps = float(getattr(loader, "mission_cmd", {}).get("target_speed", 0.0))
        order.altitude_block_min_m = max(0.0, order.target_altitude_m - 500.0)
        order.altitude_block_max_m = max(order.altitude_block_min_m, order.target_altitude_m + 500.0)
        order.speed_min_mps = max(0.0, order.target_speed_mps - 40.0)
        order.speed_max_mps = max(order.speed_min_mps, order.target_speed_mps + 40.0)
        return order

    def _make_report(self, loader: Any, *, report_type: Any, sim_time_s: float) -> ef_py.PilotReport:
        report = ef_py.PilotReport()
        report.active = True
        report.report_type = report_type
        report.sender_id = int(getattr(loader, "agent_id", 0) or 0)
        report.task_id = int(getattr(getattr(loader, "task_order", None), "task_id", 0))
        report.phase_id = int(self._phase_enum_for_name(getattr(loader, "mission_phase_name", "idle")))
        report.timestamp_s = float(sim_time_s)
        try:
            truth = loader.sim.get_agent_observation(loader.agent_id)
            report.location_x_m = float(getattr(truth, "x", 0.0))
            report.location_y_m = float(getattr(truth, "y", 0.0))
            report.location_z_m = float(getattr(truth, "z", 0.0))
        except Exception:
            pass
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
        if is_landing_command_code(getattr(loader, "mission_cmd", {}).get("command_code", 0)):
            return False
        if not is_landing_command_code(post.get("command_code", COMMAND_CODE_LANDING)):
            return False
        if remaining_waypoints > self.terminal_waypoint_count:
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
        return True
