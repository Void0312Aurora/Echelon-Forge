from dataclasses import dataclass, field, fields
from types import MappingProxyType
from typing import Any

from python.scenario.compiler import (
    _build_lnav_runtime_config,
    _clone_runtime_mission_command,
    _clone_scenario_value,
    cache_runtime_waypoint_cache,
    materialize_runtime_waypoint_cache,
)
from python.tasking_contracts.bridge_views import (
    has_mission_command_dict,
    mission_command_dict,
    mission_command_view,
)
from .common import safe_json_dict_loads, stable_json_dumps


SCENARIO_LOADER_STATE_SHELL_ATTRS = frozenset(
    {
        "waypoints",
        "waypoint_idx",
        "_waypoint_prev_dist_m",
        "waypoint_total_route_length_m",
        "_waypoint_leg_origin_x",
        "_waypoint_leg_origin_y",
        "_approach_prev_dme_m",
        "_approach_prev_loc_abs",
        "_approach_prev_gs_abs",
        "post_waypoint_transition",
        "mission_phase_name",
        "task_order",
        "leader_intent",
        "pilot_report",
        "_cached_route_ref_id",
        "prev_alt",
        "prev_speed",
        "gear_bonus_awarded",
        "liftoff_awarded",
        "off_runway_steps",
        "last_reward_breakdown",
        "last_termination_reason",
    }
)

SCENARIO_LOADER_STATE_SHELL_SCENARIO_CONTENT_ADAPTER = "scenario_content_adapter_state"
SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY = "runtime_mirror_only"
SCENARIO_LOADER_STATE_SHELL_TRANSITIONAL_BEHAVIOR_MIRROR = "transitional_behavior_mirror"
SCENARIO_LOADER_STATE_SHELL_BLOCKED_OWNER_CANDIDATE = "blocked_owner_candidate"

SCENARIO_LOADER_STATE_SHELL_CLASSIFICATIONS = MappingProxyType(
    {
        "waypoints": SCENARIO_LOADER_STATE_SHELL_SCENARIO_CONTENT_ADAPTER,
        "waypoint_idx": SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
        "_waypoint_prev_dist_m": SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
        "waypoint_total_route_length_m": SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
        "_waypoint_leg_origin_x": SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
        "_waypoint_leg_origin_y": SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
        "_approach_prev_dme_m": SCENARIO_LOADER_STATE_SHELL_TRANSITIONAL_BEHAVIOR_MIRROR,
        "_approach_prev_loc_abs": SCENARIO_LOADER_STATE_SHELL_TRANSITIONAL_BEHAVIOR_MIRROR,
        "_approach_prev_gs_abs": SCENARIO_LOADER_STATE_SHELL_TRANSITIONAL_BEHAVIOR_MIRROR,
        "post_waypoint_transition": SCENARIO_LOADER_STATE_SHELL_TRANSITIONAL_BEHAVIOR_MIRROR,
        "mission_phase_name": SCENARIO_LOADER_STATE_SHELL_TRANSITIONAL_BEHAVIOR_MIRROR,
        "task_order": SCENARIO_LOADER_STATE_SHELL_BLOCKED_OWNER_CANDIDATE,
        "leader_intent": SCENARIO_LOADER_STATE_SHELL_BLOCKED_OWNER_CANDIDATE,
        "pilot_report": SCENARIO_LOADER_STATE_SHELL_BLOCKED_OWNER_CANDIDATE,
        "_cached_route_ref_id": SCENARIO_LOADER_STATE_SHELL_SCENARIO_CONTENT_ADAPTER,
        "prev_alt": SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
        "prev_speed": SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
        "gear_bonus_awarded": SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
        "liftoff_awarded": SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
        "off_runway_steps": SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
        "last_reward_breakdown": SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
        "last_termination_reason": SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
    }
)

SCENARIO_LOADER_STATE_SHELL_CLASSIFICATION_BUCKETS = frozenset(
    {
        SCENARIO_LOADER_STATE_SHELL_SCENARIO_CONTENT_ADAPTER,
        SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
        SCENARIO_LOADER_STATE_SHELL_TRANSITIONAL_BEHAVIOR_MIRROR,
        SCENARIO_LOADER_STATE_SHELL_BLOCKED_OWNER_CANDIDATE,
    }
)


@dataclass(slots=True)
class ScenarioLoaderStateShell:
    waypoints: list[dict[str, Any]] = field(default_factory=list)
    waypoint_idx: int = 0
    _waypoint_prev_dist_m: float | None = None
    waypoint_total_route_length_m: float = 0.0
    _waypoint_leg_origin_x: float = 0.0
    _waypoint_leg_origin_y: float = 0.0
    _approach_prev_dme_m: float | None = None
    _approach_prev_loc_abs: float | None = None
    _approach_prev_gs_abs: float | None = None
    post_waypoint_transition: dict[str, Any] | None = None
    mission_phase_name: str = "idle"
    task_order: Any = None
    leader_intent: Any = None
    pilot_report: Any = None
    _cached_route_ref_id: int | None = None
    prev_alt: float = 0.0
    prev_speed: float = 0.0
    gear_bonus_awarded: bool = False
    liftoff_awarded: bool = False
    off_runway_steps: int = 0
    last_reward_breakdown: dict[str, Any] = field(default_factory=dict)
    last_termination_reason: str = "idle"


def classify_scenario_loader_state_shell_attr(name: str) -> str:
    try:
        return str(SCENARIO_LOADER_STATE_SHELL_CLASSIFICATIONS[name])
    except KeyError as exc:
        raise KeyError(f"ScenarioLoader state-shell attr {name!r} is not classified") from exc


def _validate_scenario_loader_state_shell_contract() -> None:
    shell_dataclass_attrs = frozenset(field_def.name for field_def in fields(ScenarioLoaderStateShell))
    if shell_dataclass_attrs != SCENARIO_LOADER_STATE_SHELL_ATTRS:
        missing = sorted(SCENARIO_LOADER_STATE_SHELL_ATTRS - shell_dataclass_attrs)
        extra = sorted(shell_dataclass_attrs - SCENARIO_LOADER_STATE_SHELL_ATTRS)
        raise RuntimeError(
            "ScenarioLoaderStateShell dataclass fields and "
            f"SCENARIO_LOADER_STATE_SHELL_ATTRS diverged; missing={missing}, extra={extra}"
        )

    classified_attrs = frozenset(SCENARIO_LOADER_STATE_SHELL_CLASSIFICATIONS)
    if classified_attrs != SCENARIO_LOADER_STATE_SHELL_ATTRS:
        missing = sorted(SCENARIO_LOADER_STATE_SHELL_ATTRS - classified_attrs)
        extra = sorted(classified_attrs - SCENARIO_LOADER_STATE_SHELL_ATTRS)
        raise RuntimeError(
            "ScenarioLoader state-shell classification is incomplete; "
            f"missing={missing}, extra={extra}"
        )

    invalid_buckets = sorted(
        {
            classification
            for classification in SCENARIO_LOADER_STATE_SHELL_CLASSIFICATIONS.values()
            if classification not in SCENARIO_LOADER_STATE_SHELL_CLASSIFICATION_BUCKETS
        }
    )
    if invalid_buckets:
        raise RuntimeError(
            "ScenarioLoader state-shell classification uses unknown buckets; "
            f"invalid={invalid_buckets}"
        )


_validate_scenario_loader_state_shell_contract()


def make_scenario_loader_state_shell() -> ScenarioLoaderStateShell:
    return ScenarioLoaderStateShell()


def _loader_state_shell_or_loader(loader):
    state_shell = getattr(loader, "_state_shell", None)
    if state_shell is None:
        return loader
    behavior_owner = getattr(loader, "_behavior_phase_owner", None)
    if behavior_owner is None:
        return state_shell

    class _MergedLoaderStateView:
        __slots__ = ("_state_shell", "_behavior_owner")

        def __init__(self, wrapped_state_shell, wrapped_behavior_owner):
            object.__setattr__(self, "_state_shell", wrapped_state_shell)
            object.__setattr__(self, "_behavior_owner", wrapped_behavior_owner)

        def __getattr__(self, name):
            if hasattr(self._behavior_owner, name):
                return getattr(self._behavior_owner, name)
            return getattr(self._state_shell, name)

        def __setattr__(self, name, value):
            if hasattr(self._behavior_owner, name):
                setattr(self._behavior_owner, name, value)
                return
            setattr(self._state_shell, name, value)

    return _MergedLoaderStateView(state_shell, behavior_owner)


def _enum_name_or_default(value: Any, default: str = "None") -> str:
    try:
        if hasattr(value, "name"):
            name = str(value.name).strip()
            if name:
                return name
    except Exception:
        pass
    text = str(value or "").strip()
    if not text:
        return str(default)
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    return text


def _canonical_runtime_mission_command_json(
    mission_cmd: dict[str, Any],
    kernel_cmd: Any | None,
) -> dict[str, Any]:
    out = _clone_runtime_mission_command(mission_cmd)
    if kernel_cmd is None:
        return out

    scalar_int_fields = (
        ("route_ref_id", "route_ref_id"),
        ("recovery_base_id", "recovery_base_id"),
        ("recovery_runway_id", "recovery_runway_id"),
        ("takeoff_procedure_code", "takeoff_procedure_id"),
        ("takeoff_clearance_code", "takeoff_clearance_id"),
        ("runway_slot_code", "runway_slot_id"),
        ("formation_id", "formation_id"),
        ("assigned_target_id", "assigned_target_id"),
        ("reference_entity_id", "reference_entity_id"),
        ("roe_state", "roe_state"),
        ("engagement_authority_holder_id", "engagement_authority_holder_id"),
        ("engagement_authority_grantor_id", "engagement_authority_grantor_id"),
        ("threat_state", "threat_state"),
        ("embarked_helo_entity_id", "embarked_helo_entity_id"),
        ("assigned_target_track_id", "assigned_target_track_id"),
        ("assigned_target_source_id", "assigned_target_source_id"),
        ("ground_task_mode", "ground_task_mode"),
        ("objective_area_id", "objective_area_id"),
        ("objective_node_id", "objective_node_id"),
        ("ground_commander_id", "ground_commander_id"),
    )
    for out_key, attr_name in scalar_int_fields:
        if hasattr(kernel_cmd, attr_name):
            out[out_key] = int(getattr(kernel_cmd, attr_name))

    scalar_float_fields = (
        ("takeoff_interval_s", "takeoff_interval_s"),
        ("form_offset_x", "form_offset_x"),
        ("form_offset_y", "form_offset_y"),
        ("form_offset_z", "form_offset_z"),
        ("station_radius_m", "station_radius_m"),
        ("station_bearing_deg", "station_bearing_deg"),
        ("assigned_target_snapshot_time_s", "assigned_target_snapshot_time_s"),
        ("tactical_cadence_hz", "tactical_cadence_hz"),
    )
    for out_key, attr_name in scalar_float_fields:
        if hasattr(kernel_cmd, attr_name):
            out[out_key] = float(getattr(kernel_cmd, attr_name))

    scalar_bool_fields = (
        ("authorization_to_fire", "authorization_to_fire"),
        ("active", "active"),
        ("launch_helo", "launch_helo"),
        ("recover_helo", "recover_helo"),
        ("relay_oth_targeting", "relay_oth_targeting"),
    )
    for out_key, attr_name in scalar_bool_fields:
        if hasattr(kernel_cmd, attr_name):
            out[out_key] = bool(getattr(kernel_cmd, attr_name))

    preserve_semantic_recovery_approach = bool(
        str(out.get("phase_name", "") or "").strip()
        or str(out.get("landing_mode", "") or "").strip()
    )
    if hasattr(kernel_cmd, "recovery_approach_type") and not preserve_semantic_recovery_approach:
        out["recovery_approach_type"] = _enum_name_or_default(
            getattr(kernel_cmd, "recovery_approach_type"),
            str(out.get("recovery_approach_type", "None") or "None"),
        )
    return out


def _sync_command_chain_runtime_mirror(loader) -> None:
    cmd_view = mission_command_view(loader)
    leader_intent = getattr(loader, "leader_intent", None)
    if leader_intent is not None:
        try:
            leader_intent.command_code = cmd_view.int_field("command_code", 0)
        except Exception:
            pass
        try:
            leader_intent.cmd_heading_deg = cmd_view.float_field("target_heading", 0.0)
        except Exception:
            pass
        try:
            leader_intent.cmd_altitude_m = cmd_view.float_field("target_altitude", 0.0)
        except Exception:
            pass
        try:
            leader_intent.cmd_speed_mps = cmd_view.float_field("target_speed", 0.0)
        except Exception:
            pass
        if hasattr(leader_intent, "route_ref_id"):
            try:
                leader_intent.route_ref_id = cmd_view.int_field("route_ref_id", 0)
            except Exception:
                pass
        if hasattr(leader_intent, "recovery_base_id"):
            try:
                leader_intent.recovery_base_id = cmd_view.int_field("recovery_base_id", 0)
            except Exception:
                pass
        if hasattr(leader_intent, "recovery_runway_id"):
            try:
                leader_intent.recovery_runway_id = cmd_view.int_field("recovery_runway_id", 0)
            except Exception:
                pass
        if hasattr(leader_intent, "authorization_to_fire"):
            try:
                leader_intent.authorization_to_fire = cmd_view.bool_field("authorization_to_fire", False)
            except Exception:
                pass
        if hasattr(leader_intent, "threat_state"):
            try:
                leader_intent.threat_state = cmd_view.int_field("threat_state", 0)
            except Exception:
                pass
        if hasattr(leader_intent, "assigned_target_id"):
            try:
                leader_intent.assigned_target_id = cmd_view.int_field("assigned_target_id", 0)
            except Exception:
                pass
        if hasattr(leader_intent, "assigned_target_track_id"):
            try:
                leader_intent.assigned_target_track_id = cmd_view.int_field("assigned_target_track_id", 0)
            except Exception:
                pass
        if hasattr(leader_intent, "assigned_target_source_id"):
            try:
                leader_intent.assigned_target_source_id = cmd_view.int_field("assigned_target_source_id", 0)
            except Exception:
                pass
        if hasattr(leader_intent, "assigned_target_snapshot_time_s"):
            try:
                leader_intent.assigned_target_snapshot_time_s = cmd_view.float_field(
                    "assigned_target_snapshot_time_s",
                    0.0,
                )
            except Exception:
                pass

    task_order = getattr(loader, "task_order", None)
    if task_order is not None:
        try:
            task_order.target_altitude_m = cmd_view.float_field("target_altitude", 0.0)
        except Exception:
            pass
        try:
            task_order.target_speed_mps = cmd_view.float_field("target_speed", 0.0)
        except Exception:
            pass
        try:
            task_order.station_heading_deg = cmd_view.float_field("target_heading", 0.0)
        except Exception:
            pass


def build_execution_episode_state(loader):
    if not hasattr(__import__("ef_py"), "ExecutionEpisodeState"):
        raise RuntimeError("ef_py.ExecutionEpisodeState is not available")

    import ef_py

    loader_state = _loader_state_shell_or_loader(loader)
    state = ef_py.ExecutionEpisodeState()
    state.agent_id = int(loader.agent_id or 0)
    state.step_count = int(getattr(loader, "steps", 0))

    mission_cmd = mission_command_dict(loader)
    if has_mission_command_dict(loader):
        state.has_mission_command_json = True
        mission_json = _clone_runtime_mission_command(mission_cmd)
        try:
            # Deferred: `build_kernel_mission_command` stays python.rl-resident (profile dispatch).
            from python.rl.tasking.bridge import build_kernel_mission_command

            state.mission_command = build_kernel_mission_command(loader)
            state.has_mission_command = True
            mission_json = _canonical_runtime_mission_command_json(mission_cmd, state.mission_command)
        except Exception:
            state.has_mission_command = False
        state.mission_command_json = stable_json_dumps(mission_json)

    route_waypoints = []
    for wp in list(getattr(loader_state, "waypoints", []) or []):
        if not isinstance(wp, dict):
            continue
        route_wp = ef_py.SpatialRouteWaypoint()
        route_wp.x_m = float(wp.get("x", 0.0))
        route_wp.y_m = float(wp.get("y", 0.0))
        route_wp.z_m = float(wp.get("z", wp.get("altitude_m", 0.0)))
        route_wp.radius_m = float(wp.get("radius_m", 500.0))
        route_wp.altitude_m = float(wp.get("altitude_m", route_wp.z_m))
        route_wp.speed_mps = float(wp.get("speed_mps", 0.0))
        route_wp.waypoint_mode = str(wp.get("waypoint_mode", "flyby"))
        route_waypoints.append(route_wp)
    state.route_waypoints = route_waypoints
    state.waypoint_index = int(getattr(loader_state, "waypoint_idx", 0) or 0)
    state.waypoint_total_route_length_m = float(getattr(loader_state, "waypoint_total_route_length_m", 0.0))
    state.waypoint_leg_origin_x_m = float(getattr(loader_state, "_waypoint_leg_origin_x", 0.0))
    state.waypoint_leg_origin_y_m = float(getattr(loader_state, "_waypoint_leg_origin_y", 0.0))
    if getattr(loader_state, "_waypoint_prev_dist_m", None) is not None:
        state.has_waypoint_prev_dist_m = True
        state.waypoint_prev_dist_m = float(loader_state._waypoint_prev_dist_m)

    state.prev_altitude_m = float(getattr(loader_state, "prev_alt", 0.0))
    state.prev_ias_mps = float(getattr(loader_state, "prev_speed", 0.0))
    state.liftoff_awarded = bool(getattr(loader_state, "liftoff_awarded", False))
    state.gear_bonus_awarded = bool(getattr(loader_state, "gear_bonus_awarded", False))
    state.off_runway_steps = int(getattr(loader_state, "off_runway_steps", 0))

    if getattr(loader_state, "_approach_prev_dme_m", None) is not None:
        state.has_approach_prev_dme_m = True
        state.approach_prev_dme_m = float(loader_state._approach_prev_dme_m)
    if getattr(loader_state, "_approach_prev_loc_abs", None) is not None:
        state.has_approach_prev_loc_abs = True
        state.approach_prev_loc_abs = float(loader_state._approach_prev_loc_abs)
    if getattr(loader_state, "_approach_prev_gs_abs", None) is not None:
        state.has_approach_prev_gs_abs = True
        state.approach_prev_gs_abs = float(loader_state._approach_prev_gs_abs)

    post_waypoint_transition = getattr(loader_state, "post_waypoint_transition", None)
    if isinstance(post_waypoint_transition, dict) and post_waypoint_transition:
        state.has_post_waypoint_transition_json = True
        state.post_waypoint_transition_json = stable_json_dumps(
            _clone_runtime_mission_command(post_waypoint_transition)
        )
    state.mission_phase_name = str(getattr(loader_state, "mission_phase_name", "idle") or "idle")

    cached_route_ref_id = getattr(loader_state, "_cached_route_ref_id", None)
    if cached_route_ref_id is not None:
        state.has_cached_route_ref_id = True
        state.cached_route_ref_id = int(cached_route_ref_id)

    reward_breakdown = dict(getattr(loader_state, "last_reward_breakdown", {}) or {})
    state.last_termination_reason = str(getattr(loader_state, "last_termination_reason", "idle") or "idle")
    state.last_reward_total = float(reward_breakdown.get("total", 0.0))
    state.last_reward_breakdown_json = stable_json_dumps(reward_breakdown)
    return state


def _coerce_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off", ""}:
            return False
    return bool(default)


def apply_execution_episode_state(loader, state) -> None:
    import ef_py

    if not hasattr(ef_py, "ExecutionEpisodeState") or not isinstance(state, ef_py.ExecutionEpisodeState):
        raise TypeError("state must be an ef_py.ExecutionEpisodeState")

    loader.agent_id = int(state.agent_id) if int(state.agent_id) > 0 else None
    loader.steps = int(state.step_count)
    loader_state = _loader_state_shell_or_loader(loader)

    mission_cmd = None
    mission_cmd_from_json = False
    if bool(state.has_mission_command_json) and str(state.mission_command_json).strip():
        mission_cmd = safe_json_dict_loads(state.mission_command_json)
        mission_cmd_from_json = isinstance(mission_cmd, dict)
    if not isinstance(mission_cmd, dict):
        mission_cmd = {
            "command_code": int(state.mission_command.command_code),
            "target_heading": float(state.mission_command.cmd_heading_deg),
            "target_altitude": float(state.mission_command.cmd_altitude_m),
            "target_speed": float(state.mission_command.cmd_speed_mps),
            "recovery_approach_type": getattr(state.mission_command.recovery_approach_type, "name", "None"),
            "takeoff_procedure_code": int(getattr(state.mission_command, "takeoff_procedure_id", 0)),
            "takeoff_clearance_code": int(getattr(state.mission_command, "takeoff_clearance_id", 0)),
            "takeoff_interval_s": float(getattr(state.mission_command, "takeoff_interval_s", 0.0)),
            "runway_slot_code": int(getattr(state.mission_command, "runway_slot_id", 0)),
            "formation_id": int(getattr(state.mission_command, "formation_id", 0)),
            "form_offset_x": float(getattr(state.mission_command, "form_offset_x", 0.0)),
            "form_offset_y": float(getattr(state.mission_command, "form_offset_y", 0.0)),
            "form_offset_z": float(getattr(state.mission_command, "form_offset_z", 0.0)),
            "assigned_target_id": int(getattr(state.mission_command, "assigned_target_id", 0)),
            "threat_state": int(getattr(state.mission_command, "threat_state", 0)),
            "assigned_target_track_id": int(getattr(state.mission_command, "assigned_target_track_id", 0)),
            "assigned_target_source_id": int(getattr(state.mission_command, "assigned_target_source_id", 0)),
            "assigned_target_snapshot_time_s": float(
                getattr(state.mission_command, "assigned_target_snapshot_time_s", 0.0)
            ),
            "authorization_to_fire": bool(getattr(state.mission_command, "authorization_to_fire", False)),
            "active": bool(getattr(state.mission_command, "active", False)),
        }
        if hasattr(state.mission_command, "route_ref_id"):
            mission_cmd["route_ref_id"] = int(state.mission_command.route_ref_id)
        if hasattr(state.mission_command, "recovery_base_id"):
            mission_cmd["recovery_base_id"] = int(state.mission_command.recovery_base_id)
        if hasattr(state.mission_command, "recovery_runway_id"):
            mission_cmd["recovery_runway_id"] = int(state.mission_command.recovery_runway_id)
    loader_state.waypoints = []
    for route_wp in list(state.route_waypoints):
        loader_state.waypoints.append(
            {
                "x": float(route_wp.x_m),
                "y": float(route_wp.y_m),
                "z": float(route_wp.z_m),
                "radius_m": float(route_wp.radius_m),
                "altitude_m": float(route_wp.altitude_m),
                "speed_mps": float(route_wp.speed_mps),
                "waypoint_mode": str(route_wp.waypoint_mode),
            }
        )
    if loader_state.waypoints and not list(mission_cmd.get("waypoints", []) or []):
        mission_cmd["waypoints"] = _clone_scenario_value(loader_state.waypoints)

    has_cached_route_ref_id = bool(state.has_cached_route_ref_id)
    route_ref_id = int(state.cached_route_ref_id) if has_cached_route_ref_id else 0
    if route_ref_id > 0:
        mission_cmd["route_ref_id"] = int(route_ref_id)
        cache_runtime_waypoint_cache(mission_cmd, loader_state.waypoints, route_ref_id=route_ref_id)
    else:
        materialize_runtime_waypoint_cache(mission_cmd)

    if not mission_cmd_from_json:
        mission_cmd["active"] = _coerce_bool(
            mission_cmd.get("active", getattr(state.mission_command, "active", False)),
            bool(getattr(state.mission_command, "active", False)),
        )
    elif "active" in mission_cmd:
        mission_cmd["active"] = _coerce_bool(
            mission_cmd.get("active", getattr(state.mission_command, "active", False)),
            bool(getattr(state.mission_command, "active", False)),
        )

    loader.mission_cmd = mission_cmd
    if isinstance(loader.scenario_data, dict):
        loader.scenario_data["mission_command"] = loader.mission_cmd

    loader_state.waypoint_idx = int(state.waypoint_index)
    loader_state._waypoint_prev_dist_m = (
        float(state.waypoint_prev_dist_m) if bool(state.has_waypoint_prev_dist_m) else None
    )
    loader_state.waypoint_total_route_length_m = float(state.waypoint_total_route_length_m)
    loader_state._waypoint_leg_origin_x = float(state.waypoint_leg_origin_x_m)
    loader_state._waypoint_leg_origin_y = float(state.waypoint_leg_origin_y_m)

    loader_state.prev_alt = float(state.prev_altitude_m)
    loader_state.prev_speed = float(state.prev_ias_mps)
    loader_state.liftoff_awarded = bool(state.liftoff_awarded)
    loader_state.gear_bonus_awarded = bool(state.gear_bonus_awarded)
    loader_state.off_runway_steps = int(state.off_runway_steps)

    loader_state._approach_prev_dme_m = (
        float(state.approach_prev_dme_m) if bool(state.has_approach_prev_dme_m) else None
    )
    loader_state._approach_prev_loc_abs = (
        float(state.approach_prev_loc_abs) if bool(state.has_approach_prev_loc_abs) else None
    )
    loader_state._approach_prev_gs_abs = (
        float(state.approach_prev_gs_abs) if bool(state.has_approach_prev_gs_abs) else None
    )

    loader_state.post_waypoint_transition = None
    if bool(state.has_post_waypoint_transition_json) and str(state.post_waypoint_transition_json).strip():
        loader_state.post_waypoint_transition = safe_json_dict_loads(state.post_waypoint_transition_json)
    loader_state.mission_phase_name = str(state.mission_phase_name or "idle")
    loader_state._cached_route_ref_id = int(route_ref_id) if has_cached_route_ref_id else None

    reward_breakdown = safe_json_dict_loads(state.last_reward_breakdown_json)
    loader_state.last_reward_breakdown = dict(reward_breakdown or {})
    if "total" not in loader_state.last_reward_breakdown:
        loader_state.last_reward_breakdown["total"] = float(state.last_reward_total)
    loader_state.last_termination_reason = str(state.last_termination_reason or "idle")
    loader._lnav_runtime_cfg = _build_lnav_runtime_config(loader.mission_cmd)
    resolved_cached_route_ref_id = int(loader.mission_cmd.get("route_ref_id", route_ref_id))
    if has_cached_route_ref_id or resolved_cached_route_ref_id > 0:
        loader_state._cached_route_ref_id = int(resolved_cached_route_ref_id)
    else:
        loader_state._cached_route_ref_id = None
    _sync_command_chain_runtime_mirror(loader)
    loader._rebuild_spatial_geometry()
