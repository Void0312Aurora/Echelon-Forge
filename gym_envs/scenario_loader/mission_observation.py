import numpy as np
import ef_py

from python.mission_obs_taxonomy import mission_obs_mode_code
from python.scenario.runtime import find_active_roster_member
from python.rl.tasking.bridge import mission_command_view

from .common import formation_role_code_from_member


def mission_nav_inputs(loader, truth, inst, route_result):
    if route_result is None or not bool(getattr(route_result, "valid", False)):
        return None
    idx = int(getattr(route_result, "idx", -1))
    if idx < 0 or idx >= len(loader.waypoints):
        return None

    wp = loader.waypoints[idx]
    inputs = ef_py.MissionNavInputs()
    inputs.own_altitude_m = float(getattr(truth, "z", 0.0))
    inputs.truth_heading_deg = float(getattr(truth, "heading", 0.0))
    inputs.truth_speed_mps = float(getattr(truth, "speed", 0.0))
    inputs.inst_heading_deg = float("nan")
    inputs.inst_ground_track_deg = float("nan")
    inputs.inst_ias_mps = float("nan")
    if inst is not None:
        inputs.inst_heading_deg = loader._instrument_scalar(inst, "heading", 9)
        inputs.inst_ground_track_deg = loader._instrument_scalar(inst, "ground_track", 30)
        inputs.inst_ias_mps = loader._instrument_scalar(inst, "ias", 0)
    inputs.waypoint_altitude_m = float(loader._slot_target_altitude_for_waypoint(wp))
    inputs.cdi_full_scale_m = float(loader._lnav_runtime_cfg.cdi_full_scale_m)
    return inputs


def build_mission_nav_products(loader, route_result, truth, inst):
    inputs = mission_nav_inputs(loader, truth, inst, route_result)
    if inputs is None:
        return None
    products = ef_py.compute_waypoint_mission_nav(route_result, inputs)
    if not bool(getattr(products, "valid", False)):
        return None
    return {
        "active_wp_idx": float(products.active_wp_idx),
        "total_wps": float(products.total_wps),
        "selected_steerpoint": float(products.selected_steerpoint),
        "steerpoint_mode_code": float(products.steerpoint_mode_code),
        "dist_m": float(products.dist_m),
        "xtk_m": float(products.xtk_m),
        "dtg_m": float(products.dtg_m),
        "direct_bearing_deg": float(products.direct_bearing_deg),
        "desired_leg_track_deg": float(products.desired_leg_track_deg),
        "bearing_rel_deg": float(products.bearing_rel_deg),
        "altitude_delta_m": float(products.altitude_delta_m),
        "cdi_norm": float(products.cdi_norm),
        "track_angle_error_deg": float(products.track_angle_error_deg),
        "next_turn_deg": float(products.next_turn_deg),
        "distance_to_turn_m": float(products.distance_to_turn_m),
    }


def cached_waypoint_nav_products(loader, *, truth=None, inst=None):
    cache = getattr(loader, "_runtime_eval_cache", None)
    route_key_ready = isinstance(cache, dict) and "route_guidance_key" in cache
    route_key = cache.get("route_guidance_key") if route_key_ready else None
    if route_key_ready and cache.get("waypoint_nav_products_key") == route_key:
        cached_products = cache.get("waypoint_nav_products")
        return cached_products if cached_products is not None else None

    route_result = loader._query_route_guidance_result(truth=truth, inst=inst)
    route_key_ready = isinstance(cache, dict) and "route_guidance_key" in cache
    route_key = cache.get("route_guidance_key") if route_key_ready else None
    if route_result is None:
        if route_key_ready:
            cache["waypoint_nav_products_key"] = route_key
            cache["waypoint_nav_products"] = None
        return None

    products = build_mission_nav_products(loader, route_result, truth, inst)
    if route_key_ready:
        cache["waypoint_nav_products_key"] = route_key
        cache["waypoint_nav_products"] = products
    return products


def mission_observation_mode_code(mode: str) -> int:
    return int(mission_obs_mode_code(mode))


def build_mission_observation_runtime_inputs(loader, mode: str, *, truth=None, inst=None):
    cmd_view = mission_command_view(loader)
    inputs = ef_py.MissionObservationInputs()
    inputs.mode_code = int(mission_observation_mode_code(mode))
    inputs.command_code = float(cmd_view.int_field("command_code", 0))
    inputs.target_heading_deg = float(cmd_view.float_field("target_heading", 0.0))
    route_target_altitude_m = loader._current_route_target_altitude_m(truth=truth, inst=inst)
    inputs.target_altitude_m = float(
        cmd_view.float_field("target_altitude", 0.0) if route_target_altitude_m is None else route_target_altitude_m
    )
    inputs.target_speed_mps = float(cmd_view.float_field("target_speed", 0.0))
    inputs.takeoff_procedure_code = float(cmd_view.int_field("takeoff_procedure_code", 0))
    inputs.takeoff_clearance_code = float(cmd_view.int_field("takeoff_clearance_code", 0))
    inputs.takeoff_interval_s = float(cmd_view.float_field("takeoff_interval_s", 0.0))
    inputs.runway_slot_code = float(cmd_view.int_field("runway_slot_code", 0))
    inputs.form_offset_x = float(cmd_view.float_field("form_offset_x", 0.0))
    inputs.form_offset_y = float(cmd_view.float_field("form_offset_y", 0.0))
    inputs.form_offset_z = float(cmd_view.float_field("form_offset_z", 0.0))
    if int(inputs.mode_code) in (4, 5):
        member = find_active_roster_member(getattr(loader, "active_roster", None), entity_id=loader.agent_id)
        ref_member = None
        if member is not None and getattr(member, "reference_entity_id", None) is not None:
            ref_member = find_active_roster_member(
                getattr(loader, "active_roster", None),
                entity_id=int(member.reference_entity_id),
            )
        inputs.self_role_code = float(getattr(member, "role_code", 0) or 0)
        inputs.self_formation_role_code = float(formation_role_code_from_member(member))
        inputs.relative_slot_code = float(getattr(member, "relative_slot_code", 0) or 0)
        inputs.reference_relative_slot_code = float(getattr(ref_member, "relative_slot_code", 0) or 0)

    if int(inputs.mode_code) == 0:
        return inputs

    if truth is None:
        try:
            truth = loader.get_policy_agent_observation(loader.agent_id)
        except Exception:
            truth = None
    if inst is None:
        try:
            inst = loader.get_policy_instrument_state(loader.agent_id)
        except Exception:
            inst = None
    if truth is not None:
        route_result = loader._query_route_guidance_result(truth=truth, inst=inst)
        if route_result is not None:
            nav_inputs = mission_nav_inputs(loader, truth, inst, route_result)
            if nav_inputs is not None:
                inputs.has_route_guidance = True
                inputs.route_guidance = route_result
                inputs.nav_inputs = nav_inputs
    return inputs


def compiled_mission_observation_enabled(loader) -> bool:
    return bool(getattr(loader, "use_compiled_execution_step_runtime", True)) and hasattr(
        ef_py, "MissionObservationInputs"
    ) and hasattr(ef_py, "compute_mission_observation")


def compute_mission_observation_products(loader, mode: str, *, truth=None, inst=None):
    inputs = build_mission_observation_runtime_inputs(loader, mode, truth=truth, inst=inst)
    return ef_py.compute_mission_observation(inputs)


def get_waypoint_nav_products(loader, *, truth=None, inst=None):
    if truth is None:
        try:
            truth = loader.get_policy_agent_observation(loader.agent_id)
        except Exception:
            return None
    if inst is None:
        try:
            inst = loader.get_policy_instrument_state(loader.agent_id)
        except Exception:
            inst = None
    return cached_waypoint_nav_products(loader, truth=truth, inst=inst)


def _role_vector(loader):
    member = find_active_roster_member(getattr(loader, "active_roster", None), entity_id=loader.agent_id)
    ref_member = None
    if member is not None and getattr(member, "reference_entity_id", None) is not None:
        ref_member = find_active_roster_member(
            getattr(loader, "active_roster", None),
            entity_id=int(member.reference_entity_id),
        )
    return np.array(
        [
            float(getattr(member, "role_code", 0) or 0),
            float(formation_role_code_from_member(member)),
            float(getattr(member, "relative_slot_code", 0) or 0),
            float(getattr(ref_member, "relative_slot_code", 0) or 0),
        ],
        dtype=np.float32,
    )


def _formation_vector(loader):
    return np.array(
        [
            float(loader.mission_cmd.get("form_offset_x", 0.0)),
            float(loader.mission_cmd.get("form_offset_y", 0.0)),
            float(loader.mission_cmd.get("form_offset_z", 0.0)),
        ],
        dtype=np.float32,
    )


def _takeoff_vector(loader):
    return np.array(
        [
            float(loader.mission_cmd.get("takeoff_procedure_code", 0.0)),
            float(loader.mission_cmd.get("takeoff_clearance_code", 0.0)),
            float(loader.mission_cmd.get("takeoff_interval_s", 0.0)),
            float(loader.mission_cmd.get("runway_slot_code", 0.0)),
        ],
        dtype=np.float32,
    )


def get_mission_observation(loader, mode: str = "basic", *, truth=None, inst=None):
    mode_norm = str(mode).strip().lower()
    _ = mission_observation_mode_code(mode_norm)
    if compiled_mission_observation_enabled(loader):
        cached = loader._get_cached_step_evaluation(truth=truth, inst_obj=inst, mission_obs_mode=mode_norm)
        if isinstance(cached, dict):
            frame_products = cached.get("frame_products")
            if frame_products is not None and bool(getattr(frame_products, "mission_observation_evaluated", False)):
                return np.asarray(frame_products.mission_observation.values, dtype=np.float32)
        products = compute_mission_observation_products(loader, mode_norm, truth=truth, inst=inst)
        return np.asarray(products.values, dtype=np.float32)

    base = np.array(
        [
            float(loader.mission_cmd["command_code"]),
            float(loader.mission_cmd["target_heading"]),
            float(loader.mission_cmd["target_altitude"]),
            float(loader.mission_cmd["target_speed"]),
        ],
        dtype=np.float32,
    )
    if mode_norm in ("", "basic"):
        return base

    products = get_waypoint_nav_products(loader, truth=truth, inst=inst)
    if products is None:
        nav_zeros = np.zeros((7 if mode_norm == "nav_v1" else 10,), dtype=np.float32)
        if mode_norm in ("nav_v2_formation_v1", "nav_v2_formation_role_v1", "nav_v2_cooperative_takeoff_v1"):
            formation = _formation_vector(loader)
            if mode_norm in ("nav_v2_formation_role_v1", "nav_v2_cooperative_takeoff_v1"):
                role = _role_vector(loader)
                if mode_norm == "nav_v2_cooperative_takeoff_v1":
                    return np.concatenate([base, nav_zeros, _takeoff_vector(loader), formation, role], axis=0)
                return np.concatenate([base, nav_zeros, formation, role], axis=0)
            return np.concatenate([base, nav_zeros, formation], axis=0)
        return np.concatenate([base, nav_zeros], axis=0)

    if mode_norm == "nav_v1":
        nav = np.array(
            [
                float(products["active_wp_idx"]),
                float(products["total_wps"]),
                float(products["dist_m"]),
                float(products["xtk_m"]),
                float(products["dtg_m"]),
                float(products["direct_bearing_deg"]),
                float(products["desired_leg_track_deg"]),
            ],
            dtype=np.float32,
        )
        return np.concatenate([base, nav], axis=0)

    nav2 = np.array(
        [
            float(products["selected_steerpoint"]),
            float(products["steerpoint_mode_code"]),
            float(products["dist_m"]),
            float(products["bearing_rel_deg"]),
            float(products["altitude_delta_m"]),
            float(products["cdi_norm"]),
            float(products["track_angle_error_deg"]),
            float(products["dtg_m"]),
            float(products["next_turn_deg"]),
            float(products["distance_to_turn_m"]),
        ],
        dtype=np.float32,
    )
    if mode_norm in ("nav_v2_formation_v1", "nav_v2_formation_role_v1", "nav_v2_cooperative_takeoff_v1"):
        formation = _formation_vector(loader)
        if mode_norm in ("nav_v2_formation_role_v1", "nav_v2_cooperative_takeoff_v1"):
            role = _role_vector(loader)
            if mode_norm == "nav_v2_cooperative_takeoff_v1":
                return np.concatenate([base, nav2, _takeoff_vector(loader), formation, role], axis=0)
            return np.concatenate([base, nav2, formation, role], axis=0)
        return np.concatenate([base, nav2, formation], axis=0)
    return np.concatenate([base, nav2], axis=0)
