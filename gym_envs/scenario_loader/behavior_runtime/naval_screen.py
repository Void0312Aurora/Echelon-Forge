from __future__ import annotations

import math
from typing import Any

import ef_py
from python.rl.tasking.bridge import (
    has_mission_command_dict,
    loader_owned_raw_sim_compat,
    mission_command_dict,
    resolve_loader_time_step,
)


def _wrap_heading_deg(angle_deg: float) -> float:
    return float(angle_deg % 360.0)


def _heading_error_deg(target_deg: float, current_deg: float) -> float:
    delta = _wrap_heading_deg(target_deg) - _wrap_heading_deg(current_deg)
    while delta > 180.0:
        delta -= 360.0
    while delta < -180.0:
        delta += 360.0
    return float(delta)


def _bearing_deg(dx: float, dy: float, fallback_deg: float) -> float:
    if abs(dx) < 1.0e-9 and abs(dy) < 1.0e-9:
        return _wrap_heading_deg(fallback_deg)
    return _wrap_heading_deg(math.degrees(math.atan2(dx, dy)))


def _intercept_bearing_deg(
    own_x: float,
    own_y: float,
    target_x: float,
    target_y: float,
    target_vx: float,
    target_vy: float,
    own_speed_mps: float,
    fallback_deg: float,
) -> float:
    rel_x = float(target_x) - float(own_x)
    rel_y = float(target_y) - float(own_y)
    if math.hypot(rel_x, rel_y) < 1.0e-6:
        return _wrap_heading_deg(fallback_deg)

    speed = max(0.1, float(own_speed_mps))
    target_speed_sq = float(target_vx) * float(target_vx) + float(target_vy) * float(target_vy)
    rel_dot_v = rel_x * float(target_vx) + rel_y * float(target_vy)
    rel_sq = rel_x * rel_x + rel_y * rel_y
    a = target_speed_sq - speed * speed
    b = 2.0 * rel_dot_v
    c = rel_sq

    intercept_time_s = None
    if abs(a) < 1.0e-9:
        if abs(b) > 1.0e-9:
            candidate = -c / b
            if candidate > 0.0:
                intercept_time_s = candidate
    else:
        disc = b * b - 4.0 * a * c
        if disc >= 0.0:
            sqrt_disc = math.sqrt(disc)
            roots = [(-b - sqrt_disc) / (2.0 * a), (-b + sqrt_disc) / (2.0 * a)]
            positive_roots = [root for root in roots if root > 0.0]
            if positive_roots:
                intercept_time_s = min(positive_roots)

    if intercept_time_s is None:
        intercept_time_s = min(360.0, max(0.0, math.sqrt(rel_sq) / speed))
    else:
        intercept_time_s = min(360.0, intercept_time_s)

    lead_x = float(target_x) + float(target_vx) * intercept_time_s
    lead_y = float(target_y) + float(target_vy) * intercept_time_s
    return _bearing_deg(lead_x - float(own_x), lead_y - float(own_y), fallback_deg)


def _read_naval_screen_reference_motion(loader: Any, entity_id: int) -> tuple[Any, Any] | None:
    compat = loader_owned_raw_sim_compat(loader)
    try:
        ref_pos = compat.get_unit_position(int(entity_id))
        ref_vel = compat.get_unit_velocity(int(entity_id))
    except Exception:
        return None
    if ref_pos is None or ref_vel is None or len(ref_pos) < 2 or len(ref_vel) < 2:
        return None
    return ref_pos, ref_vel


def _prefer_last_active_naval_screen_reference(
    loader: Any,
    *,
    reference_entity_id: int,
    last_reference_entity_id: int,
) -> tuple[int, tuple[Any, Any] | None]:
    if last_reference_entity_id <= 0 or reference_entity_id == last_reference_entity_id:
        return int(reference_entity_id), _read_naval_screen_reference_motion(loader, reference_entity_id)
    compat = loader_owned_raw_sim_compat(loader)
    try:
        if compat.is_unit_active(last_reference_entity_id):
            motion = _read_naval_screen_reference_motion(loader, last_reference_entity_id)
            if motion is not None:
                return int(last_reference_entity_id), motion
    except Exception:
        pass
    return int(reference_entity_id), _read_naval_screen_reference_motion(loader, reference_entity_id)


def apply_naval_screen_station_hold(loader: Any, *, truth: Any = None) -> None:
    task = getattr(loader, "task_order", None)
    mission_cmd = mission_command_dict(loader)
    if task is None or not has_mission_command_dict(loader):
        return
    result = compute_naval_screen_station_hold(loader, truth=truth)
    if result is None:
        return

    loader._naval_screen_last_reference_id = int(result["reference_entity_id"])
    loader._naval_screen_last_heading_deg = float(result["target_heading_deg"])
    loader._naval_screen_last_speed_mps = float(result["target_speed_mps"])
    loader._naval_screen_use_direct_command = bool(result.get("use_direct_command", 0.0))

    task.anchor_x_m = float(result["desired_x"])
    task.anchor_y_m = float(result["desired_y"])
    task.anchor_z_m = 0.0
    task.target_heading_deg = float(result["target_heading_deg"])
    task.target_speed_mps = float(result["target_speed_mps"])
    task.target_altitude_m = 0.0

    mission_cmd["target_heading"] = float(result["target_heading_deg"])
    mission_cmd["target_speed"] = float(result["target_speed_mps"])
    mission_cmd["target_altitude"] = 0.0


def compute_naval_screen_station_hold(loader: Any, *, truth: Any = None) -> dict[str, float] | None:
    task = getattr(loader, "task_order", None)
    mission_cmd = mission_command_dict(loader)
    if task is None or not has_mission_command_dict(loader):
        return None
    try:
        if int(getattr(task, "task_family", 0)) != int(getattr(ef_py.TaskFamily, "Escort")):
            return None
        if int(getattr(task, "coordination_mode", 0)) != int(getattr(ef_py.CoordinationMode, "Screen")):
            return None
    except Exception:
        return None

    member = None
    try:
        member = loader.get_active_roster_member(entity_id=loader.agent_id)
    except Exception:
        member = None
    if member is None:
        return None

    reference_entity_id = int(getattr(member, "reference_entity_id", 0) or 0)
    if reference_entity_id <= 0:
        active_roster = list(getattr(loader, "active_roster", []) or [])
        for other in active_roster:
            if int(getattr(other, "entity_id", 0) or 0) == int(getattr(member, "entity_id", 0) or 0):
                continue
            other_reference_id = int(getattr(other, "reference_entity_id", 0) or 0)
            if other_reference_id == int(getattr(member, "entity_id", 0) or 0):
                reference_entity_id = int(getattr(other, "entity_id", 0) or 0)
                break
    if reference_entity_id <= 0:
        return None

    try:
        own_truth = truth if truth is not None else loader.get_policy_agent_observation(loader.agent_id)
    except Exception:
        return None

    if own_truth is None:
        return None

    last_reference_entity_id = int(getattr(loader, "_naval_screen_last_reference_id", 0) or 0)
    reference_entity_id, reference_motion = _prefer_last_active_naval_screen_reference(
        loader,
        reference_entity_id=reference_entity_id,
        last_reference_entity_id=last_reference_entity_id,
    )
    if reference_motion is None:
        return None
    ref_pos, ref_vel = reference_motion

    station_radius_m = float(max(1000.0, getattr(task, "station_radius_m", 0.0) or 0.0))
    station_heading_deg = float(getattr(task, "station_heading_deg", mission_cmd.get("target_heading", 0.0)) or 0.0)
    ref_speed_mps = float(math.hypot(float(ref_vel[0]), float(ref_vel[1])))
    ref_heading_deg = float(_bearing_deg(float(ref_vel[0]), float(ref_vel[1]), station_heading_deg))

    heading_rad = math.radians(station_heading_deg)
    desired_x = float(ref_pos[0]) + math.sin(heading_rad) * station_radius_m
    desired_y = float(ref_pos[1]) + math.cos(heading_rad) * station_radius_m

    dx = float(desired_x) - float(getattr(own_truth, "x", 0.0))
    dy = float(desired_y) - float(getattr(own_truth, "y", 0.0))
    range_error_m = math.hypot(dx, dy)
    rel_dx = float(getattr(own_truth, "x", 0.0)) - float(ref_pos[0])
    rel_dy = float(getattr(own_truth, "y", 0.0)) - float(ref_pos[1])
    separation_m = math.hypot(rel_dx, rel_dy)
    own_heading_deg = float(getattr(own_truth, "heading", station_heading_deg))
    own_speed_mps = float(getattr(own_truth, "speed", mission_cmd.get("target_speed", ref_speed_mps)) or ref_speed_mps)

    speed_min_mps = float(getattr(task, "speed_min_mps", mission_cmd.get("target_speed", ref_speed_mps)) or 0.0)
    speed_max_mps = float(getattr(task, "speed_max_mps", max(speed_min_mps, mission_cmd.get("target_speed", ref_speed_mps))) or speed_min_mps)
    hold_deadband_m = max(250.0, station_radius_m * 0.02)
    heading_deadband_m = max(150.0, hold_deadband_m * 0.5)
    capture_radius_m = max(1800.0, station_radius_m * 0.12)
    recover_exit_radius_m = max(750.0, min(capture_radius_m * 0.55, station_radius_m * 0.08))
    recover_handoff_radius_m = max(recover_exit_radius_m, hold_deadband_m * 3.8)
    recover_handoff_separation_m = max(hold_deadband_m, hold_deadband_m * 3.8)
    recover_active = bool(getattr(loader, "_naval_screen_use_direct_command", False))
    use_direct_command = False
    speed_gain = 0.0015
    max_speed_bias_mps = 1.5
    desired_station_bearing_deg = float(_bearing_deg(dx, dy, own_heading_deg))
    can_handoff_to_station_hold = range_error_m <= recover_handoff_radius_m
    if range_error_m > capture_radius_m or (
        recover_active
        and (
            not can_handoff_to_station_hold
            and range_error_m > recover_exit_radius_m
            or separation_m < station_radius_m - recover_handoff_separation_m
        )
    ):
        separation_error_m = separation_m - station_radius_m
        desired_speed_mps = min(max(ref_speed_mps, speed_min_mps), speed_max_mps)
        if separation_error_m < -hold_deadband_m:
            closing_bias_mps = max(
                0.5,
                min(
                    speed_max_mps - ref_speed_mps,
                    max(0.0, (-separation_error_m - hold_deadband_m) * 0.0012),
                ),
            )
            desired_speed_mps = min(max(ref_speed_mps + closing_bias_mps, speed_min_mps), speed_max_mps)
        elif separation_error_m > hold_deadband_m:
            desired_speed_mps = min(max(ref_speed_mps + 0.75, speed_min_mps), speed_max_mps)
        desired_heading_deg = _intercept_bearing_deg(
            float(getattr(own_truth, "x", 0.0)),
            float(getattr(own_truth, "y", 0.0)),
            desired_x,
            desired_y,
            float(ref_vel[0]),
            float(ref_vel[1]),
            desired_speed_mps,
            ref_heading_deg,
        )
        use_direct_command = True
        target_heading_deg = desired_heading_deg
        target_speed_mps = desired_speed_mps
    else:
        if range_error_m <= hold_deadband_m:
            desired_speed_mps = ref_speed_mps
        else:
            speed_error_m = range_error_m - hold_deadband_m
            speed_correction = max(-max_speed_bias_mps, min(max_speed_bias_mps, speed_error_m * speed_gain))
            desired_speed_mps = ref_speed_mps + speed_correction
        desired_speed_mps = min(max(desired_speed_mps, speed_min_mps), max(speed_min_mps, speed_max_mps))

        if range_error_m <= heading_deadband_m:
            desired_heading_deg = station_heading_deg
        else:
            desired_heading_deg = desired_station_bearing_deg

        dt = max(0.05, float(resolve_loader_time_step(loader, default=0.5)))

        max_heading_step_deg = max(2.5, 12.0 * dt)
        max_speed_step_mps = max(0.25, 1.6 * dt)
        last_heading_raw = getattr(loader, "_naval_screen_last_heading_deg", None)
        last_speed_raw = getattr(loader, "_naval_screen_last_speed_mps", None)
        last_heading_deg = own_heading_deg if last_heading_raw is None else float(last_heading_raw)
        last_speed_mps = own_speed_mps if last_speed_raw is None else float(last_speed_raw)
        heading_step = max(-max_heading_step_deg, min(max_heading_step_deg, _heading_error_deg(desired_heading_deg, last_heading_deg)))
        target_heading_deg = _wrap_heading_deg(last_heading_deg + heading_step)

        speed_delta = max(-max_speed_step_mps, min(max_speed_step_mps, desired_speed_mps - last_speed_mps))
        target_speed_mps = min(max(last_speed_mps + speed_delta, speed_min_mps), max(speed_min_mps, speed_max_mps))

    return {
        "reference_entity_id": float(reference_entity_id),
        "desired_x": float(desired_x),
        "desired_y": float(desired_y),
        "station_heading_deg": float(station_heading_deg),
        "target_heading_deg": float(target_heading_deg),
        "target_speed_mps": float(target_speed_mps),
        "use_direct_command": 1.0 if use_direct_command else 0.0,
    }
