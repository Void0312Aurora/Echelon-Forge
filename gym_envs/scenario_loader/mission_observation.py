import numpy as np
import ef_py

from python.mission_obs_taxonomy import mission_obs_mode_code, mission_observation_python_owned
from python.scenario.runtime import find_active_roster_member
from python.rl.tasking.bridge import loader_owned_runtime_view, mission_command_view

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


def python_owned_mission_observation_mode(mode: str | None) -> bool:
    return mission_observation_python_owned(mode)


def build_mission_observation_runtime_inputs(loader, mode: str, *, truth=None, inst=None):
    if python_owned_mission_observation_mode(mode):
        return None
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


def _target_track(truth, target_id: int):
    if truth is None or int(target_id) <= 0:
        return None
    for track in getattr(truth, "contacts", []) or []:
        try:
            if int(getattr(track, "id", 0)) == int(target_id):
                return track
        except Exception:
            continue
    return None


def _air_combat_c2_roe_vector(loader, *, truth=None, inst=None) -> np.ndarray:
    _ = inst
    if truth is None:
        try:
            truth = loader.get_policy_agent_observation(loader.agent_id)
        except Exception:
            truth = None
    cmd_view = mission_command_view(loader)

    assigned_target_id = int(cmd_view.int_field("assigned_target_id", 0))
    target_id = assigned_target_id if assigned_target_id > 0 else int(getattr(loader, "primary_target_id", 0) or 0)
    target_track = _target_track(truth, target_id)
    target_contact_present = 1.0 if target_track is not None else 0.0
    track_identity = int(getattr(target_track, "classification", 0) or 0) if target_track is not None else 0
    target_identity = cmd_view.int_field(
        "target_identity_state",
        cmd_view.int_field("threat_state", track_identity),
    )

    return np.array(
        [
            float(cmd_view.int_field("command_code", 0)),
            float(cmd_view.float_field("target_heading", 0.0)),
            float(cmd_view.float_field("target_altitude", 0.0)),
            float(cmd_view.float_field("target_speed", 0.0)),
            float(cmd_view.int_field("roe_state", 0)),
            float(cmd_view.int_field("wcs_state", 1)),
            1.0 if bool(cmd_view.bool_field("authorization_to_fire", False)) else 0.0,
            float(cmd_view.int_field("engagement_authority_holder_id", 0)),
            float(cmd_view.int_field("engagement_authority_grantor_id", 0)),
            float(assigned_target_id),
            float(cmd_view.int_field("assigned_target_track_id", 0)),
            float(cmd_view.int_field("assigned_target_source_id", 0)),
            float(cmd_view.float_field("assigned_target_snapshot_time_s", 0.0)),
            float(target_identity),
            float(cmd_view.int_field("engage_order_state", 0)),
            float(cmd_view.int_field("shot_policy_state", 0)),
            float(cmd_view.int_field("shot_budget_remaining", 0)),
            1.0 if bool(cmd_view.bool_field("pending_assessment", False)) else 0.0,
            float(cmd_view.int_field("own_missiles_in_flight_count", 0)),
            float(target_contact_present),
        ],
        dtype=np.float32,
    )


def _support_entity_ids(loader) -> list[int]:
    agent_id = int(getattr(loader, "agent_id", 0) or 0)
    out: list[int] = []
    for member in list(getattr(loader, "active_roster", []) or []):
        try:
            entity_id = int(getattr(member, "entity_id", 0) or 0)
            if entity_id <= 0 or entity_id == agent_id:
                continue
            reference_id = int(getattr(member, "reference_entity_id", 0) or 0)
            if reference_id == agent_id or not bool(getattr(member, "is_agent", True)):
                out.append(entity_id)
        except Exception:
            continue
    return out


def _support_has_target_track(runtime_view, support_ids: list[int], target_id: int) -> bool:
    if int(target_id) <= 0:
        return False
    for entity_id in support_ids:
        try:
            obs = runtime_view.get_agent_observation(int(entity_id))
        except Exception:
            continue
        if _target_track(obs, int(target_id)) is not None:
            return True
    return False


def _support_received_target_report(runtime_view, support_ids: list[int], target_id: int) -> bool:
    if int(target_id) <= 0:
        return False
    for entity_id in support_ids:
        messages = runtime_view.call_optional("get_unit_messages", int(entity_id), default=[]) or []
        for msg in messages:
            try:
                if int(getattr(msg, "entity_ref", 0)) == int(target_id):
                    return True
            except Exception:
                continue
    return False


def _first_support_position(runtime_view, support_ids: list[int]) -> tuple[float, float] | None:
    for entity_id in support_ids:
        try:
            pos = runtime_view.get_unit_position(int(entity_id))
        except Exception:
            continue
        if pos is None or len(pos) < 2:
            continue
        return float(pos[0]), float(pos[1])
    return None


def _naval_screen_station_vector(loader, *, truth=None, inst=None) -> np.ndarray:
    _ = inst
    if truth is None:
        try:
            truth = loader.get_policy_agent_observation(loader.agent_id)
        except Exception:
            truth = None
    task = getattr(loader, "task_order", None)
    cmd_view = mission_command_view(loader)
    mission_cmd = getattr(loader, "mission_cmd", {}) if isinstance(getattr(loader, "mission_cmd", {}), dict) else {}
    runtime_view = loader_owned_runtime_view(loader)

    station_radius_m = float(
        getattr(task, "station_radius_m", 0.0)
        if task is not None
        else cmd_view.float_field("station_radius_m", 0.0)
    )
    station_bearing_deg = float(
        getattr(task, "station_heading_deg", 0.0)
        if task is not None
        else cmd_view.float_field("station_bearing_deg", cmd_view.float_field("target_heading", 0.0))
    )
    support_ids = _support_entity_ids(loader)
    ref_pos = _first_support_position(runtime_view, support_ids)
    own_x = float(getattr(truth, "x", 0.0)) if truth is not None else 0.0
    own_y = float(getattr(truth, "y", 0.0)) if truth is not None else 0.0
    own_relative_x_m = 0.0
    own_relative_y_m = 0.0
    desired_relative_x_m = 0.0
    desired_relative_y_m = 0.0
    station_error_m = 0.0
    separation_m = 0.0
    separation_error_m = 0.0
    if ref_pos is not None:
        ref_x, ref_y = ref_pos
        own_relative_x_m = own_x - ref_x
        own_relative_y_m = own_y - ref_y
        heading_rad = np.deg2rad(station_bearing_deg)
        desired_relative_x_m = float(np.sin(heading_rad) * station_radius_m)
        desired_relative_y_m = float(np.cos(heading_rad) * station_radius_m)
        station_error_m = float(
            np.hypot(desired_relative_x_m - own_relative_x_m, desired_relative_y_m - own_relative_y_m)
        )
        separation_m = float(np.hypot(own_relative_x_m, own_relative_y_m))
        separation_error_m = float(separation_m - station_radius_m)

    target_id = int(getattr(loader, "primary_target_id", 0) or mission_cmd.get("assigned_target_id", 0) or 0)
    target_contact_present = 1.0 if _target_track(truth, target_id) is not None else 0.0
    support_track_present = 1.0 if _support_has_target_track(runtime_view, support_ids, target_id) else 0.0
    report_chain_seen = 1.0 if _support_received_target_report(runtime_view, support_ids, target_id) else 0.0
    if report_chain_seen <= 0.0 and support_track_present > 0.0:
        report_chain_seen = 0.5

    station_norm = max(1.0, station_radius_m)
    member = find_active_roster_member(getattr(loader, "active_roster", None), entity_id=getattr(loader, "agent_id", 0))
    ref_member = None
    if member is not None and getattr(member, "reference_entity_id", None) is not None:
        ref_member = find_active_roster_member(
            getattr(loader, "active_roster", None),
            entity_id=int(member.reference_entity_id),
        )

    return np.array(
        [
            float(cmd_view.int_field("command_code", 0)),
            float(cmd_view.float_field("target_heading", 0.0)),
            float(cmd_view.float_field("target_speed", 0.0)),
            float(station_radius_m),
            float(station_bearing_deg),
            float(station_error_m),
            float(station_error_m / station_norm),
            float(separation_m),
            float(separation_error_m),
            float(own_relative_x_m),
            float(own_relative_y_m),
            float(desired_relative_x_m),
            float(desired_relative_y_m),
            float(target_contact_present),
            float(support_track_present),
            float(report_chain_seen),
            float(cmd_view.int_field("roe_state", 0)),
            1.0 if bool(cmd_view.bool_field("authorization_to_fire", False)) else 0.0,
            float(target_id),
            float(cmd_view.int_field("assigned_target_source_id", 0)),
            float(getattr(member, "role_code", 0) or 0),
            float(getattr(member, "relative_slot_code", 0) or 0),
            float(getattr(ref_member, "relative_slot_code", 0) or 0),
        ],
        dtype=np.float32,
    )


def get_python_owned_mission_observation(loader, mode: str, *, truth=None, inst=None):
    mode_norm = str(mode).strip().lower()
    if mode_norm == "naval_screen_station_v1":
        return _naval_screen_station_vector(loader, truth=truth, inst=inst)
    if mode_norm == "air_combat_c2_roe_v1":
        return _air_combat_c2_roe_vector(loader, truth=truth, inst=inst)
    raise ValueError(f"Unknown Python-owned mission observation mode: {mode!r}")


def get_mission_observation(loader, mode: str = "basic", *, truth=None, inst=None):
    mode_norm = str(mode).strip().lower()
    _ = mission_observation_mode_code(mode_norm)
    if python_owned_mission_observation_mode(mode_norm):
        return get_python_owned_mission_observation(loader, mode_norm, truth=truth, inst=inst)

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
