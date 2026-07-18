import math

import numpy as np

from python.rl.control.mission_defs import is_landing_command_code
from python.rl.tasking.bridge import has_mission_command_dict, mission_command_view, resolve_loader_time_step
from python.scenario.compiler import (
    _build_lnav_runtime_config,
    _clone_runtime_mission_command,
    _normalize_runtime_mission_command,
    materialize_runtime_waypoint_cache,
)


def landing_post_transition_terminal_ready(loader) -> bool:
    if loader.agent_id is None:
        return False
    try:
        truth = loader.get_policy_agent_observation(loader.agent_id)
    except Exception:
        truth = None
    try:
        inst = loader.get_policy_instrument_state(loader.agent_id)
    except Exception:
        inst = None
    if truth is None or inst is None:
        return False

    valid_runway_frame = False
    along_m = 0.0
    cross_m = 0.0
    runway_len_m = 0.0
    try:
        valid_runway_frame, along_m, cross_m, runway_len_m, _rw_wid = loader.get_runway_local_frame(
            float(getattr(truth, "x", 0.0)),
            float(getattr(truth, "y", 0.0)),
        )
    except Exception:
        valid_runway_frame = False
    if not bool(valid_runway_frame):
        return False
    post = loader.post_waypoint_transition if isinstance(loader.post_waypoint_transition, dict) else {}
    threshold_arming_window_m = float(post.get("terminal_ready_threshold_window_m", 1000.0))
    threshold_arming_window_m = float(np.clip(threshold_arming_window_m, 500.0, 6000.0))
    min_along_m = -0.5 * max(float(runway_len_m), 0.0) - threshold_arming_window_m
    if float(along_m) < float(min_along_m):
        return False
    max_cross_m = float(post.get("terminal_ready_cross_m_max", 3500.0))
    max_cross_m = float(np.clip(max_cross_m, 1000.0, 8000.0))
    if abs(float(cross_m)) > max_cross_m:
        return False

    try:
        beacon = loader._nearest_ils_beacon(float(getattr(truth, "x", 0.0)), float(getattr(truth, "y", 0.0)))
    except Exception:
        beacon = None
    if beacon is None:
        return False
    runway_heading_err_deg = abs(
        (float(getattr(inst, "heading", 0.0)) - float(beacon.get("heading", 0.0)) + 180.0) % 360.0 - 180.0
    )
    if runway_heading_err_deg > 85.0:
        return False

    try:
        ils = loader.get_ils_observation(
            float(getattr(truth, "x", 0.0)),
            float(getattr(truth, "y", 0.0)),
            float(getattr(inst, "alt_baro", 0.0)),
        )
    except Exception:
        return False
    dme_m = float(ils[3]) if len(ils) >= 4 else float("inf")
    max_dme_m = float(post.get("terminal_ready_dme_m_max", 18000.0))
    max_dme_m = float(np.clip(max_dme_m, 6000.0, 40000.0))
    return dme_m <= max_dme_m


def post_waypoint_transition_ready(loader) -> bool:
    if not isinstance(loader.post_waypoint_transition, dict) or not loader.post_waypoint_transition:
        return False
    next_cmd_code = int(loader.post_waypoint_transition.get("command_code", 4))
    if not is_landing_command_code(next_cmd_code):
        return True

    c2_task_name = str(getattr(loader, "c2_task_name", "")).strip().upper()
    if not c2_task_name:
        return landing_post_transition_terminal_ready(loader)
    if bool(getattr(loader, "c2_transitioned", False)):
        return False
    if c2_task_name != "TASK_RECOVER_LAND":
        return False
    if loader.waypoints and int(getattr(loader, "waypoint_idx", 0) or 0) >= len(loader.waypoints):
        return True
    return landing_post_transition_terminal_ready(loader)


def apply_pending_landing_vector(loader, *, sync_to_kernel: bool = True) -> bool:
    post = loader.post_waypoint_transition
    if not isinstance(post, dict) or not post:
        return False
    next_cmd_code = int(post.get("command_code", 4))
    if not is_landing_command_code(next_cmd_code):
        return False
    if loader.waypoints and int(getattr(loader, "waypoint_idx", 0) or 0) < len(loader.waypoints):
        return False
    if not has_mission_command_dict(loader):
        return False
    if loader.agent_id is None:
        return False
    try:
        truth = loader.get_policy_agent_observation(loader.agent_id)
    except Exception:
        truth = None
    if truth is None:
        return False
    try:
        beacon = loader._nearest_ils_beacon(float(getattr(truth, "x", 0.0)), float(getattr(truth, "y", 0.0)))
    except Exception:
        beacon = None
    if not isinstance(beacon, dict):
        return False

    runway_heading_deg = float(beacon.get("heading", 0.0)) % 360.0
    runway_heading_rad = math.radians(runway_heading_deg)
    fwd_x = math.sin(runway_heading_rad)
    fwd_y = math.cos(runway_heading_rad)
    intercept_before_threshold_m = float(post.get("approach_arm_before_threshold_m", 1600.0))
    intercept_before_threshold_m = float(np.clip(intercept_before_threshold_m, 1000.0, 5000.0))
    intercept_x = float(beacon.get("thr_x", 0.0)) - fwd_x * intercept_before_threshold_m
    intercept_y = float(beacon.get("thr_y", 0.0)) - fwd_y * intercept_before_threshold_m

    dx = intercept_x - float(getattr(truth, "x", 0.0))
    dy = intercept_y - float(getattr(truth, "y", 0.0))
    if dx * dx + dy * dy <= 1.0:
        desired_heading_deg = runway_heading_deg
    else:
        desired_heading_deg = math.degrees(math.atan2(dx, dy)) % 360.0

    loader.mission_cmd["target_heading"] = float(desired_heading_deg)
    if sync_to_kernel:
        loader._sync_kernel_mission_command()
    return True


def maybe_activate_post_waypoint_transition(loader, *, sync_to_kernel: bool = True) -> dict | None:
    if not isinstance(loader.post_waypoint_transition, dict) or not loader.post_waypoint_transition:
        return None
    if loader.waypoints and int(getattr(loader, "waypoint_idx", 0) or 0) < len(loader.waypoints):
        return None
    if not post_waypoint_transition_ready(loader):
        apply_pending_landing_vector(loader, sync_to_kernel=sync_to_kernel)
        return None
    return activate_post_waypoint_transition(loader, sync_to_kernel=sync_to_kernel)


def defer_landing_post_transition_until_next_update(loader) -> bool:
    if not isinstance(loader.post_waypoint_transition, dict) or not loader.post_waypoint_transition:
        return False
    next_cmd_code = int(loader.post_waypoint_transition.get("command_code", 4))
    if not is_landing_command_code(next_cmd_code):
        return False
    scenario_data = getattr(loader, "scenario_data", {}) or {}
    c2_cfg = scenario_data.get("c2_logic", None) if isinstance(scenario_data, dict) else None
    if isinstance(c2_cfg, dict) and c2_cfg:
        return True
    return bool(str(getattr(loader, "c2_task_name", "")).strip())


def activate_post_waypoint_transition(loader, *, sync_to_kernel: bool = True) -> dict | None:
    if not isinstance(loader.post_waypoint_transition, dict) or not loader.post_waypoint_transition:
        return None

    cmd_view = mission_command_view(loader)
    next_cmd = _clone_runtime_mission_command(loader.post_waypoint_transition)
    if not isinstance(next_cmd, dict):
        return None

    target_heading = float(next_cmd.get("target_heading", cmd_view.float_field("target_heading", 0.0)))
    if loader.rotate_mission_heading_with_world and abs(float(loader.world_yaw_deg)) > 1.0e-6:
        target_heading = (target_heading + float(loader.world_yaw_deg)) % 360.0

    loader.mission_cmd = {
        "command_code": int(next_cmd.get("command_code", 4)),
        "target_heading": float(target_heading),
        "target_altitude": float(next_cmd.get("target_altitude", cmd_view.float_field("target_altitude", 0.0))),
        "target_speed": float(next_cmd.get("target_speed", cmd_view.float_field("target_speed", 0.0))),
    }

    for key, value in next_cmd.items():
        if key in ("command_code", "target_heading", "target_altitude", "target_speed", "transition_reward"):
            continue
        loader.mission_cmd[key] = value

    loader.mission_cmd = _normalize_runtime_mission_command(loader.mission_cmd, loader._task_order_spec())
    materialize_runtime_waypoint_cache(loader.mission_cmd)
    loader.scenario_data["mission_command"] = loader.mission_cmd
    loader._lnav_runtime_cfg = _build_lnav_runtime_config(loader.mission_cmd)

    loader.post_waypoint_transition = None
    loader.mission_phase_name = (
        str(next_cmd.get("phase_name", next_cmd.get("landing_mode", "post_waypoint"))).strip() or "post_waypoint"
    )
    leader_intent = getattr(loader, "leader_intent", None)
    if leader_intent is not None:
        try:
            leader_intent.command_code = int(loader.mission_cmd.get("command_code", 0))
        except Exception:
            pass
        try:
            leader_intent.cmd_heading_deg = float(loader.mission_cmd.get("target_heading", 0.0))
        except Exception:
            pass
        try:
            leader_intent.cmd_altitude_m = float(loader.mission_cmd.get("target_altitude", 0.0))
        except Exception:
            pass
        try:
            leader_intent.cmd_speed_mps = float(loader.mission_cmd.get("target_speed", 0.0))
        except Exception:
            pass
        if hasattr(leader_intent, "route_ref_id"):
            try:
                leader_intent.route_ref_id = int(loader.mission_cmd.get("route_ref_id", 0))
            except Exception:
                pass
        if hasattr(leader_intent, "recovery_base_id"):
            try:
                leader_intent.recovery_base_id = int(loader.mission_cmd.get("recovery_base_id", 0))
            except Exception:
                pass
        if hasattr(leader_intent, "recovery_runway_id"):
            try:
                leader_intent.recovery_runway_id = int(loader.mission_cmd.get("recovery_runway_id", 0))
            except Exception:
                pass
        if hasattr(leader_intent, "authorization_to_fire"):
            try:
                leader_intent.authorization_to_fire = bool(loader.mission_cmd.get("authorization_to_fire", False))
            except Exception:
                pass
    loader.waypoints = []
    loader.waypoint_idx = 0
    loader._waypoint_prev_dist_m = None
    loader.waypoint_total_route_length_m = 0.0
    loader._cached_route_ref_id = None
    loader._approach_prev_dme_m = None
    loader._approach_prev_loc_abs = None
    loader._approach_prev_gs_abs = None
    loader._rebuild_spatial_geometry()
    if sync_to_kernel:
        loader._sync_kernel_mission_command()
    return next_cmd


def update_behaviors(loader, sim_time, *, truth=None, inst=None, sync_to_kernel: bool = True):
    loader._apply_waypoint_guidance_update(truth=truth, inst=inst)
    loader._update_command_chain(sim_time, truth=truth, inst=inst, sync_to_kernel=False)
    if not loader._defer_landing_post_transition_until_next_update():
        loader._maybe_activate_post_waypoint_transition(sync_to_kernel=False)
    loader.update_scripted_opponents(float(sim_time))
    if sync_to_kernel:
        loader._sync_kernel_mission_command()
        loader._sync_kernel_command_chain()


def update_nonhierarchical_behaviors(loader, *, truth=None, inst=None, sync_to_kernel: bool = True):
    dt = float(resolve_loader_time_step(loader, default=0.05))
    sim_time = float(getattr(loader, "steps", 0)) * float(dt)
    update_behaviors(loader, sim_time, truth=truth, inst=inst, sync_to_kernel=sync_to_kernel)
