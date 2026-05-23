from __future__ import annotations

from typing import Any

import ef_py
import numpy as np

from python.rl.control.mission_defs import (
    COMMAND_CODE_LANDING,
    COMMAND_CODE_ROUTE,
    COMMAND_CODE_TAKEOFF,
    COMMAND_CODE_VECTOR,
    normalize_phase_name,
)
from python.rl.tasking.bridge import (
    get_policy_agent_observation,
    get_policy_instrument_state,
    infer_recovery_approach_type,
    infer_recovery_base_id,
    infer_recovery_runway_id,
    infer_route_ref_id,
    is_patrol_task,
    is_recover_task,
    resolve_loader_time_step,
)

from ..common import LeaderActionMapping, wrap_deg
from ..contracts import clone_leader_intent, clone_pilot_report, clone_task_order


def decode_action(env: Any, action: np.ndarray) -> LeaderActionMapping:
    phase_val = float(np.clip(float(action[0]), -1.0, 1.0))
    if abs(phase_val) <= env.teacher_keep_deadband:
        bucket = "teacher"
    elif phase_val <= -0.60:
        bucket = "takeoff"
    elif phase_val <= -0.20:
        bucket = "route"
    elif phase_val <= 0.20:
        bucket = "teacher"
    elif phase_val <= 0.60:
        bucket = "rtb"
    elif phase_val <= 0.85:
        bucket = "approach"
    else:
        bucket = "abort"

    report_val = float(np.clip(float(action[4]), -1.0, 1.0))
    if abs(report_val) <= 0.20:
        report_bucket = "auto"
    elif report_val <= -0.60:
        report_bucket = "wilco"
    elif report_val <= -0.20:
        report_bucket = "on_station"
    elif report_val <= 0.20:
        report_bucket = "auto"
    elif report_val <= 0.60:
        report_bucket = "rtb"
    elif report_val <= 0.85:
        report_bucket = "bingo"
    else:
        report_bucket = "unable"

    return LeaderActionMapping(
        phase_bucket=str(bucket),
        heading_bias_deg=float(np.clip(float(action[1]), -1.0, 1.0)) * env.heading_bias_limit_deg,
        altitude_bias_m=float(np.clip(float(action[2]), -1.0, 1.0)) * env.altitude_bias_limit_m,
        speed_bias_mps=float(np.clip(float(action[3]), -1.0, 1.0)) * env.speed_bias_limit_mps,
        report_bucket=str(report_bucket),
        report_status_value=float(0.5 * (float(np.clip(float(action[5]), -1.0, 1.0)) + 1.0)),
    )


def mapping_has_bias(mapping: LeaderActionMapping) -> bool:
    return (
        abs(float(mapping.heading_bias_deg)) > 1e-6
        or abs(float(mapping.altitude_bias_m)) > 1e-6
        or abs(float(mapping.speed_bias_mps)) > 1e-6
    )


def zero_mapping_biases(mapping: LeaderActionMapping) -> LeaderActionMapping:
    return LeaderActionMapping(
        phase_bucket=str(mapping.phase_bucket),
        heading_bias_deg=0.0,
        altitude_bias_m=0.0,
        speed_bias_mps=0.0,
        report_bucket=str(mapping.report_bucket),
        report_status_value=float(mapping.report_status_value),
    )


def bucket_allows_command_bias(phase_bucket: str) -> bool:
    """
    Leader actions should primarily choose mission mode / phase timing.

    Keep continuous heading/altitude/speed trims only on route-like buckets,
    where the command semantics are still "track / stage reference". Teacher,
    takeoff, approach, and abort should not act like a generic vector editor.
    """

    return str(phase_bucket).strip().lower() in {"route", "rtb"}


def station_metrics(
    env: Any,
    loader: Any,
    *,
    truth: Any = None,
    inst: Any = None,
) -> dict[str, float | bool]:
    manager = getattr(env, "_c2_manager", None)
    if manager is not None and hasattr(manager, "_station_metrics"):
        try:
            metrics = manager._station_metrics(loader, truth=truth, inst=inst)
        except Exception:
            metrics = None
        if isinstance(metrics, dict):
            return metrics

    if truth is None or inst is None:
        try:
            inst_now, truth_now = env._current_execution_runtime_state()
        except Exception:
            inst_now, truth_now = None, None
        if truth is None:
            truth = truth_now
        if inst is None:
            inst = inst_now
    if truth is None:
        try:
            truth = get_policy_agent_observation(loader)
        except Exception:
            truth = None
    if inst is None:
        try:
            inst = get_policy_instrument_state(loader)
        except Exception:
            inst = None
    if truth is None or inst is None:
        return {"near_station": False, "anchor_dist_m": float("inf")}

    task = getattr(loader, "task_order", None)
    anchor_x = float(getattr(task, "anchor_x_m", 0.0) if task is not None else 0.0)
    anchor_y = float(getattr(task, "anchor_y_m", 0.0) if task is not None else 0.0)
    dx = anchor_x - float(getattr(truth, "x", 0.0))
    dy = anchor_y - float(getattr(truth, "y", 0.0))
    anchor_dist_m = float(np.hypot(dx, dy))
    station_radius_m = float(
        max(1000.0, getattr(task, "station_radius_m", 12000.0) if task is not None else 12000.0)
    )
    near_station = anchor_dist_m <= station_radius_m
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
            alt_ok = alt_lo <= alt_baro <= alt_hi
        if spd_hi > spd_lo + 1.0:
            spd_ok = spd_lo <= ias <= spd_hi
    return {
        "near_station": bool(near_station and alt_ok and spd_ok),
        "anchor_dist_m": float(anchor_dist_m),
    }


def resolve_report_type(env: Any, mapping: LeaderActionMapping, *, phase_bucket: str):
    report_bucket = str(mapping.report_bucket)
    if report_bucket == "wilco":
        return getattr(ef_py.CommMsgType, "REP_WILCO")
    if report_bucket == "on_station":
        return getattr(ef_py.CommMsgType, "REP_ON_STATION")
    if report_bucket == "rtb":
        return getattr(ef_py.CommMsgType, "REP_RTB")
    if report_bucket == "bingo":
        return getattr(ef_py.CommMsgType, "WARN_BINGO")
    if report_bucket == "unable":
        return getattr(ef_py.CommMsgType, "REP_UNABLE")

    loader = env.unwrapped.loader
    c2_task_name = str(getattr(loader, "c2_task_name", "")).strip().upper()
    task = getattr(loader, "task_order", None)
    if is_patrol_task(task, task_name=c2_task_name, loader=loader):
        try:
            metrics = station_metrics(env, loader)
        except Exception:
            metrics = {"near_station": False}
        if bool(metrics.get("near_station", False)):
            return getattr(ef_py.CommMsgType, "REP_ON_STATION")
    if is_recover_task(task, task_name=c2_task_name, loader=loader):
        return getattr(ef_py.CommMsgType, "REP_RTB")
    if phase_bucket in {"rtb", "approach"}:
        return getattr(ef_py.CommMsgType, "REP_RTB")
    if phase_bucket == "abort":
        return getattr(ef_py.CommMsgType, "REP_UNABLE")
    if phase_bucket == "teacher":
        report = getattr(loader, "pilot_report", None)
        if report is not None and bool(getattr(report, "active", False)):
            baseline_type = getattr(report, "report_type", getattr(ef_py.CommMsgType, "None"))
            if int(baseline_type) != int(getattr(ef_py.CommMsgType, "None")):
                return baseline_type
    return getattr(ef_py.CommMsgType, "REP_WILCO")


def fuel_margin_state(env: Any, task: Any, inst: Any) -> tuple[float, float]:
    _ = env
    fuel_total_kg = float(
        max(0.0, getattr(inst, "fuel_internal", 0.0) + getattr(inst, "fuel_external", 0.0))
    )
    bingo_kg = float(max(0.0, getattr(task, "fuel_bingo_override_kg", 0.0) if task is not None else 0.0))
    if bingo_kg <= 1.0:
        return fuel_total_kg, 1.0
    margin_frac = float(np.clip((fuel_total_kg - bingo_kg) / max(bingo_kg, 1.0), -1.0, 2.0))
    return fuel_total_kg, margin_frac


def terminal_context(env: Any) -> dict[str, float | bool | str]:
    loader = env.unwrapped.loader
    inst, truth = env._current_execution_runtime_state()
    if inst is None or truth is None:
        inst, truth = env._capture_execution_runtime_state()
    phase_name = normalize_phase_name(getattr(loader, "mission_phase_name", ""))
    ils = np.asarray(
        loader.get_ils_observation(
            float(getattr(truth, "x", 0.0)),
            float(getattr(truth, "y", 0.0)),
            float(getattr(inst, "alt_baro", 0.0)),
        ),
        dtype=np.float32,
    ).reshape(-1)
    valid_rf, along_m, cross_m, _rw_len, _rw_wid = loader.get_runway_local_frame(
        float(getattr(truth, "x", 0.0)),
        float(getattr(truth, "y", 0.0)),
    )
    runway_heading_err = 0.0
    try:
        beacon = loader._nearest_ils_beacon(
            float(getattr(truth, "x", 0.0)),
            float(getattr(truth, "y", 0.0)),
        )
        if beacon is not None:
            runway_heading_err = wrap_deg(
                float(getattr(inst, "heading", 0.0)) - float(beacon.get("heading", 0.0))
            )
    except Exception:
        runway_heading_err = 0.0
    return {
        "phase_name": str(phase_name),
        "alt_agl_m": float(getattr(inst, "alt_radar", 0.0)),
        "dme_m": float(ils[3]) if ils.size >= 4 else 0.0,
        "loc_dev": float(ils[1]) if ils.size >= 2 else 0.0,
        "gs_dev": float(ils[2]) if ils.size >= 3 else 0.0,
        "valid_runway_frame": bool(valid_rf),
        "along_m": float(along_m if valid_rf else 0.0),
        "cross_m": float(cross_m if valid_rf else 0.0),
        "runway_heading_err_deg": float(runway_heading_err),
    }


def terminal_feasible(env: Any, baseline: dict[str, Any], terminal_ctx: dict[str, Any]) -> bool:
    phase_name = str(terminal_ctx.get("phase_name", ""))
    if phase_name in {"approach_armed", "landing_final", "rollout", "abort"}:
        return True
    if int(baseline.get("command_code", 0)) == COMMAND_CODE_LANDING:
        return True
    loader = env.unwrapped.loader
    task = getattr(loader, "task_order", None)
    if (
        is_recover_task(
            task,
            task_name=str(getattr(loader, "c2_task_name", "")).strip().upper(),
            phase_name=phase_name,
            loader=loader,
        )
        and not has_active_waypoints(env)
    ):
        return True
    if not bool(terminal_ctx.get("valid_runway_frame", False)):
        return False
    dme_m = abs(float(terminal_ctx.get("dme_m", 0.0)))
    cross_m = abs(float(terminal_ctx.get("cross_m", 0.0)))
    heading_err = abs(float(terminal_ctx.get("runway_heading_err_deg", 180.0)))
    along_m = float(terminal_ctx.get("along_m", 0.0))
    return bool(
        along_m >= -1000.0
        and dme_m <= env.approach_gate_distance_m
        and cross_m <= env.approach_gate_cross_m
        and heading_err <= env.approach_gate_heading_error_deg
    )


def landing_reference_command(env: Any) -> tuple[float, float, float] | None:
    loader = env.unwrapped.loader
    post = None
    try:
        scenario_data = getattr(loader, "scenario_data", {}) or {}
        mission_cfg = scenario_data.get("mission_command", {}) if isinstance(scenario_data, dict) else {}
        if isinstance(mission_cfg, dict):
            post = mission_cfg.get("post_waypoint_transition", None)
    except Exception:
        post = None
    if not isinstance(post, dict) or not post:
        post = getattr(loader, "post_waypoint_transition", None)
    if not isinstance(post, dict) or not post:
        return None

    target_heading = float(post.get("target_heading", loader.mission_cmd.get("target_heading", 0.0)))
    if bool(getattr(loader, "rotate_mission_heading_with_world", False)) and abs(
        float(getattr(loader, "world_yaw_deg", 0.0))
    ) > 1.0e-6:
        target_heading = (target_heading + float(getattr(loader, "world_yaw_deg", 0.0))) % 360.0
    target_altitude = float(post.get("target_altitude", loader.mission_cmd.get("target_altitude", 0.0)))
    target_speed = float(post.get("target_speed", loader.mission_cmd.get("target_speed", 0.0)))
    return float(target_heading), float(target_altitude), float(target_speed)


def has_active_waypoints(env: Any) -> bool:
    loader = env.unwrapped.loader
    waypoints = list(getattr(loader, "waypoints", []) or [])
    if not waypoints:
        return False
    waypoint_idx = int(getattr(loader, "waypoint_idx", 0) or 0)
    return 0 <= waypoint_idx < len(waypoints)


def sanitize_action_mapping(
    env: Any,
    *,
    mapping: LeaderActionMapping,
    baseline: dict[str, Any],
) -> tuple[LeaderActionMapping, dict[str, Any]]:
    term_ctx = terminal_context(env)
    phase_name = str(term_ctx.get("phase_name", ""))
    alt_agl_m = float(term_ctx.get("alt_agl_m", 0.0))
    requested_bucket = str(mapping.phase_bucket)
    applied_bucket = requested_bucket
    reason = ""
    feasible = terminal_feasible(env, baseline, term_ctx)
    bias_guarded = False
    bias_guard_reason = ""
    loader = env.unwrapped.loader
    c2_task_name = str(getattr(loader, "c2_task_name", "")).strip().upper()
    task = getattr(loader, "task_order", None)
    recovery_vector_state = (
        is_recover_task(task, task_name=c2_task_name, phase_name=phase_name, loader=loader)
        and not has_active_waypoints(env)
        and not feasible
    )

    critical_takeoff = (
        phase_name in {"scramble", "takeoff", "departure"}
        and alt_agl_m < env.scripted_transition_alt_agl_m
    )

    if requested_bucket in {"route", "rtb", "approach", "abort"} and critical_takeoff:
        applied_bucket = "teacher"
        reason = "departure_low_altitude"
    elif requested_bucket == "approach" and has_active_waypoints(env):
        applied_bucket = "teacher"
        reason = "approach_before_route_complete"
    elif requested_bucket == "approach" and not feasible:
        applied_bucket = "teacher"
        reason = "approach_not_feasible"
    elif requested_bucket in {"route", "rtb"} and recovery_vector_state:
        applied_bucket = "teacher"
        reason = "recovery_vector_teacher"
    elif (
        requested_bucket == "abort"
        and phase_name not in {"approach_armed", "landing_final", "rollout", "abort"}
        and not feasible
    ):
        applied_bucket = "teacher"
        reason = "abort_not_terminal"

    sanitized_mapping = mapping
    if critical_takeoff and mapping_has_bias(mapping):
        sanitized_mapping = zero_mapping_biases(
            LeaderActionMapping(
                phase_bucket=str(applied_bucket),
                heading_bias_deg=float(mapping.heading_bias_deg),
                altitude_bias_m=float(mapping.altitude_bias_m),
                speed_bias_mps=float(mapping.speed_bias_mps),
                report_bucket=str(mapping.report_bucket),
                report_status_value=float(mapping.report_status_value),
            )
        )
        bias_guarded = True
        bias_guard_reason = "departure_low_altitude"
    elif applied_bucket != requested_bucket:
        sanitized_mapping = LeaderActionMapping(
            phase_bucket=str(applied_bucket),
            heading_bias_deg=float(mapping.heading_bias_deg),
            altitude_bias_m=float(mapping.altitude_bias_m),
            speed_bias_mps=float(mapping.speed_bias_mps),
            report_bucket=str(mapping.report_bucket),
            report_status_value=float(mapping.report_status_value),
        )

    if mapping_has_bias(sanitized_mapping) and not bucket_allows_command_bias(applied_bucket):
        sanitized_mapping = zero_mapping_biases(sanitized_mapping)
        bias_guarded = True
        if not bias_guard_reason:
            bias_guard_reason = f"{str(applied_bucket)}_disallows_bias"

    if applied_bucket == requested_bucket:
        return sanitized_mapping, {
            "requested_bucket": requested_bucket,
            "guarded": False,
            "reason": "",
            "bias_guarded": bias_guarded,
            "bias_guard_reason": bias_guard_reason,
            "terminal_feasible": feasible,
        }
    return sanitized_mapping, {
        "requested_bucket": requested_bucket,
        "guarded": True,
        "reason": reason,
        "bias_guarded": bias_guarded,
        "bias_guard_reason": bias_guard_reason,
        "terminal_feasible": feasible,
    }


def apply_leader_command(env: Any, *, mapping: LeaderActionMapping, baseline: dict[str, Any]) -> None:
    loader = env.unwrapped.loader
    task = clone_task_order(getattr(loader, "task_order", None))
    intent = clone_leader_intent(getattr(loader, "leader_intent", None))
    report = clone_pilot_report(getattr(loader, "pilot_report", None))
    cmd_code = int(baseline.get("command_code", loader.mission_cmd.get("command_code", 0)))
    phase_id = int(baseline.get("phase_id", getattr(ef_py.LeaderPhase, "Idle")))
    heading_deg = float(baseline.get("heading_deg", loader.mission_cmd.get("target_heading", 0.0)))
    altitude_m = float(baseline.get("altitude_m", loader.mission_cmd.get("target_altitude", 0.0)))
    speed_mps = float(baseline.get("speed_mps", loader.mission_cmd.get("target_speed", 0.0)))
    baseline_is_landing = int(cmd_code) == COMMAND_CODE_LANDING
    active_waypoints = has_active_waypoints(env)
    route_ref_id = int(getattr(intent, "route_ref_id", 0) or infer_route_ref_id(loader))
    recovery_base_id = int(getattr(intent, "recovery_base_id", 0) or infer_recovery_base_id(loader, task=task))
    recovery_runway_id = int(
        getattr(intent, "recovery_runway_id", 0) or infer_recovery_runway_id(loader, task=task)
    )
    recovery_approach_type = getattr(
        intent,
        "recovery_approach_type",
        infer_recovery_approach_type(loader, task=task),
    )

    if mapping.phase_bucket == "takeoff":
        cmd_code = COMMAND_CODE_TAKEOFF
        phase_id = int(getattr(ef_py.LeaderPhase, "Takeoff"))
    elif mapping.phase_bucket == "route":
        if not baseline_is_landing:
            cmd_code = COMMAND_CODE_ROUTE
            phase_id = int(getattr(ef_py.LeaderPhase, "TransitToStation"))
            route_ref_id = int(infer_route_ref_id(loader)) if int(cmd_code) == COMMAND_CODE_ROUTE else 0
    elif mapping.phase_bucket == "rtb":
        if not baseline_is_landing:
            cmd_code = COMMAND_CODE_ROUTE
            phase_id = int(getattr(ef_py.LeaderPhase, "RTB"))
            route_ref_id = int(infer_route_ref_id(loader)) if int(cmd_code) == COMMAND_CODE_ROUTE else 0
    elif mapping.phase_bucket == "approach":
        cmd_code = COMMAND_CODE_LANDING
        phase_id = int(getattr(ef_py.LeaderPhase, "ApproachArmed"))
        recovery_base_id = int(infer_recovery_base_id(loader, task=task))
        recovery_runway_id = int(infer_recovery_runway_id(loader, task=task))
        recovery_approach_type = infer_recovery_approach_type(loader, task=task)
    elif mapping.phase_bucket == "abort":
        cmd_code = COMMAND_CODE_VECTOR
        phase_id = int(getattr(ef_py.LeaderPhase, "Abort"))
        if isinstance(loader.mission_cmd, dict):
            baseline_altitude = loader.mission_cmd.get("target_altitude", altitude_m)
        else:
            baseline_altitude = getattr(loader.mission_cmd, "target_altitude", altitude_m)
        altitude_m = max(altitude_m, float(baseline_altitude))

    report_type = resolve_report_type(env, mapping, phase_bucket=str(mapping.phase_bucket))

    if cmd_code == COMMAND_CODE_LANDING:
        landing_ref = landing_reference_command(env)
        if landing_ref is not None:
            heading_deg, altitude_m, speed_mps = landing_ref
        speed_mps = min(speed_mps, max(70.0, float(loader.mission_cmd.get("target_speed", speed_mps))))
        altitude_m = min(altitude_m, max(0.0, float(loader.mission_cmd.get("target_altitude", altitude_m))))
    elif bucket_allows_command_bias(mapping.phase_bucket):
        heading_deg = float((heading_deg + mapping.heading_bias_deg + 360.0) % 360.0)
        altitude_m = clip_altitude(env, task, altitude_m + mapping.altitude_bias_m)
        speed_mps = clip_speed(env, task, speed_mps + mapping.speed_bias_mps)

    if (
        int(cmd_code) == COMMAND_CODE_ROUTE
        and not active_waypoints
        and is_recover_task(
            task,
            task_name=str(getattr(loader, "c2_task_name", "")).strip().upper(),
            phase_name=str(getattr(loader, "mission_phase_name", "") or ""),
            loader=loader,
        )
    ):
        landing_ref = landing_reference_command(env)
        if landing_ref is not None:
            heading_deg = float(landing_ref[0])

    if int(cmd_code) == COMMAND_CODE_ROUTE and not active_waypoints:
        route_ref_id = 0

    intent.phase_id = phase_enum_for_id(env, int(phase_id))
    intent.command_code = int(cmd_code)
    intent.route_ref_id = int(route_ref_id if int(cmd_code) == COMMAND_CODE_ROUTE else 0)
    intent.recovery_base_id = int(recovery_base_id)
    intent.recovery_runway_id = int(recovery_runway_id)
    intent.recovery_approach_type = recovery_approach_type
    intent.cmd_heading_deg = float(heading_deg)
    intent.cmd_altitude_m = float(altitude_m)
    intent.cmd_speed_mps = float(speed_mps)
    intent.approach_armed = bool(cmd_code == COMMAND_CODE_LANDING)
    intent.commit_to_land = bool(cmd_code == COMMAND_CODE_LANDING and mapping.phase_bucket == "approach")
    intent.abort_flag = bool(mapping.phase_bucket == "abort")
    intent.active = True

    sim_time_s = float(env.unwrapped.steps) * float(resolve_loader_time_step(loader, default=0.05))

    report.report_type = report_type
    report.task_id = int(getattr(task, "task_id", 0))
    report.phase_id = int(phase_enum_for_id(env, int(phase_id)))
    report.sender_id = int(getattr(loader, "agent_id", 0) or 0)
    report.timestamp_s = float(sim_time_s)
    inst_now, truth_now = env._current_execution_runtime_state()
    if int(report_type) == int(getattr(ef_py.CommMsgType, "WARN_BINGO")):
        _fuel_total_kg, fuel_margin_frac = fuel_margin_state(env, task, inst_now)
        report.status_value = float(fuel_margin_frac)
    else:
        report.status_value = float(mapping.report_status_value)
    report.active = True
    if truth_now is not None:
        report.location_x_m = float(getattr(truth_now, "x", 0.0))
        report.location_y_m = float(getattr(truth_now, "y", 0.0))
        report.location_z_m = float(getattr(truth_now, "z", 0.0))

    loader.mission_cmd["command_code"] = int(cmd_code)
    loader.mission_cmd["route_ref_id"] = int(route_ref_id)
    loader.mission_cmd["recovery_base_id"] = int(recovery_base_id)
    loader.mission_cmd["recovery_runway_id"] = int(recovery_runway_id)
    loader.mission_cmd["recovery_approach_type"] = int(recovery_approach_type)
    loader.mission_cmd["target_heading"] = float(heading_deg)
    loader.mission_cmd["target_altitude"] = float(altitude_m)
    loader.mission_cmd["target_speed"] = float(speed_mps)
    loader.mission_phase_name = phase_name_for_id(env, int(phase_id), fallback=mapping.phase_bucket)

    env._bridge.set_state(task_order=task, leader_intent=intent, pilot_report=report)
    env._bridge.update(loader, sim_time_s=sim_time_s)
    if bool(getattr(env, "_defer_kernel_command_sync", False)):
        env._kernel_command_sync_dirty = True
    else:
        try:
            loader._sync_kernel_mission_command()
        except Exception:
            pass
    env._sync_bridge_from_loader()
    env._last_leader_mode = str(mapping.phase_bucket)


def clip_altitude(env: Any, task: ef_py.TaskOrder, altitude_m: float) -> float:
    _ = env
    lo = float(getattr(task, "altitude_block_min_m", 0.0))
    hi = float(getattr(task, "altitude_block_max_m", 0.0))
    if hi > lo + 1.0:
        return float(np.clip(altitude_m, lo, hi))
    return float(np.clip(altitude_m, 0.0, 12000.0))


def clip_speed(env: Any, task: ef_py.TaskOrder, speed_mps: float) -> float:
    _ = env
    lo = float(getattr(task, "speed_min_mps", 0.0))
    hi = float(getattr(task, "speed_max_mps", 0.0))
    if hi > lo + 1.0:
        return float(np.clip(speed_mps, max(40.0, lo), hi))
    return float(np.clip(speed_mps, 60.0, 320.0))


def phase_name_for_id(env: Any, phase_id: int, *, fallback: str) -> str:
    _ = env
    mapping = {
        int(getattr(ef_py.LeaderPhase, "Idle")): "idle",
        int(getattr(ef_py.LeaderPhase, "Scramble")): "scramble",
        int(getattr(ef_py.LeaderPhase, "Takeoff")): "takeoff",
        int(getattr(ef_py.LeaderPhase, "Departure")): "departure",
        int(getattr(ef_py.LeaderPhase, "TransitToStation")): "transit_to_station",
        int(getattr(ef_py.LeaderPhase, "EstablishCAP")): "establish_cap",
        int(getattr(ef_py.LeaderPhase, "OnStation")): "on_station",
        int(getattr(ef_py.LeaderPhase, "Reposition")): "reposition",
        int(getattr(ef_py.LeaderPhase, "RTB")): "rtb",
        int(getattr(ef_py.LeaderPhase, "ApproachArmed")): "approach_armed",
        int(getattr(ef_py.LeaderPhase, "LandingFinal")): "landing_final",
        int(getattr(ef_py.LeaderPhase, "Rollout")): "rollout",
        int(getattr(ef_py.LeaderPhase, "Abort")): "abort",
    }
    return str(mapping.get(int(phase_id), str(fallback or "idle")))


def phase_enum_for_id(env: Any, phase_id: int):
    phase_name = phase_name_for_id(env, phase_id, fallback="idle")
    attr_map = {
        "idle": "Idle",
        "scramble": "Scramble",
        "takeoff": "Takeoff",
        "departure": "Departure",
        "transit_to_station": "TransitToStation",
        "establish_cap": "EstablishCAP",
        "on_station": "OnStation",
        "reposition": "Reposition",
        "rtb": "RTB",
        "approach_armed": "ApproachArmed",
        "landing_final": "LandingFinal",
        "rollout": "Rollout",
        "abort": "Abort",
    }
    return getattr(ef_py.LeaderPhase, attr_map.get(phase_name, "Idle"))


def current_command_tuple(env: Any) -> tuple[int, float, float, float]:
    loader = env.unwrapped.loader
    return (
        int(loader.mission_cmd.get("command_code", 0)),
        float(loader.mission_cmd.get("target_heading", 0.0)),
        float(loader.mission_cmd.get("target_altitude", 0.0)),
        float(loader.mission_cmd.get("target_speed", 0.0)),
    )
