from __future__ import annotations

MISSION_OBS_BASIC = "basic"
MISSION_OBS_NAV_V1 = "nav_v1"
MISSION_OBS_NAV_V2 = "nav_v2"
MISSION_OBS_NAV_V2_FORMATION_V1 = "nav_v2_formation_v1"
MISSION_OBS_NAV_V2_FORMATION_ROLE_V1 = "nav_v2_formation_role_v1"
MISSION_OBS_NAV_V2_COOPERATIVE_TAKEOFF_V1 = "nav_v2_cooperative_takeoff_v1"
MISSION_OBS_NAVAL_SCREEN_STATION_V1 = "naval_screen_station_v1"
MISSION_OBS_AIR_COMBAT_C2_ROE_V1 = "air_combat_c2_roe_v1"
MISSION_OBS_AIR_COMBAT_C2_ROE_V2 = "air_combat_c2_roe_v2"

MISSION_OBS_MODE_CODE_BY_NAME = {
    MISSION_OBS_BASIC: 0,
    MISSION_OBS_NAV_V1: 1,
    MISSION_OBS_NAV_V2: 2,
    MISSION_OBS_NAV_V2_FORMATION_V1: 3,
    MISSION_OBS_NAV_V2_FORMATION_ROLE_V1: 4,
    MISSION_OBS_NAV_V2_COOPERATIVE_TAKEOFF_V1: 5,
    MISSION_OBS_NAVAL_SCREEN_STATION_V1: 6,
    MISSION_OBS_AIR_COMBAT_C2_ROE_V1: 7,
    MISSION_OBS_AIR_COMBAT_C2_ROE_V2: 8,
}

_MISSION_OBS_BASIC_FIELDS = [
    "command_code",
    "target_heading_deg",
    "target_altitude_m",
    "target_speed_mps",
]

_MISSION_OBS_NAV_V1_EXTRA_FIELDS = [
    "active_wp_idx",
    "total_wps",
    "dist_m",
    "xtk_m",
    "dtg_m",
    "direct_bearing_deg",
    "desired_leg_track_deg",
]

_MISSION_OBS_NAV_V2_EXTRA_FIELDS = [
    "selected_steerpoint",
    "steerpoint_mode_code",
    "dist_m",
    "bearing_rel_deg",
    "altitude_delta_m",
    "cdi_norm",
    "track_angle_error_deg",
    "leg_distance_remaining_m",
    "next_turn_deg",
    "distance_to_turn_m",
]

_MISSION_OBS_FORMATION_EXTRA_FIELDS = [
    "form_offset_x_m",
    "form_offset_y_m",
    "form_offset_z_m",
]

_MISSION_OBS_ROLE_EXTRA_FIELDS = [
    "self_role_code",
    "self_formation_role_code",
    "relative_slot_code",
    "reference_relative_slot_code",
]

_MISSION_OBS_COOPERATIVE_TAKEOFF_EXTRA_FIELDS = [
    "takeoff_procedure_code",
    "takeoff_clearance_code",
    "takeoff_interval_s",
    "runway_slot_code",
]

_MISSION_OBS_NAVAL_SCREEN_STATION_FIELDS = [
    "command_code",
    "target_heading_deg",
    "target_speed_mps",
    "station_radius_m",
    "station_bearing_deg",
    "station_error_m",
    "station_error_norm",
    "screen_separation_m",
    "screen_separation_error_m",
    "own_relative_x_m",
    "own_relative_y_m",
    "desired_relative_x_m",
    "desired_relative_y_m",
    "target_contact_present",
    "support_track_present",
    "report_chain_seen",
    "roe_state",
    "authorization_to_fire",
    "assigned_target_id",
    "assigned_target_source_id",
    "self_role_code",
    "relative_slot_code",
    "reference_relative_slot_code",
]

_MISSION_OBS_AIR_COMBAT_C2_ROE_FIELDS = [
    "command_code",
    "target_heading_deg",
    "target_altitude_m",
    "target_speed_mps",
    "roe_state",
    "wcs_state",
    "authorization_to_fire",
    "engagement_authority_holder_id",
    "engagement_authority_grantor_id",
    "assigned_target_id",
    "assigned_target_track_id",
    "assigned_target_source_id",
    "assigned_target_snapshot_time_s",
    "target_identity_state",
    "engage_order_state",
    "shot_policy_state",
    "shot_budget_remaining",
    "pending_assessment",
    "own_missiles_in_flight_count",
    "target_contact_present",
]

_MISSION_OBS_AIR_COMBAT_C2_ROE_V2_EXTRA_FIELDS = [
    "fire_mask_open",
    "launch_window_open",
    "quality_window_ready",
    "legal_open_age_steps",
    "legal_open_age_norm",
    "launch_window_age_steps",
    "launch_window_age_norm",
    "target_range_m",
    "target_track_age_s",
]

MISSION_OBS_FIELD_NAMES_BY_NAME = {
    MISSION_OBS_BASIC: list(_MISSION_OBS_BASIC_FIELDS),
    MISSION_OBS_NAV_V1: list(_MISSION_OBS_BASIC_FIELDS + _MISSION_OBS_NAV_V1_EXTRA_FIELDS),
    MISSION_OBS_NAV_V2: list(_MISSION_OBS_BASIC_FIELDS + _MISSION_OBS_NAV_V2_EXTRA_FIELDS),
    MISSION_OBS_NAV_V2_FORMATION_V1: list(
        _MISSION_OBS_BASIC_FIELDS + _MISSION_OBS_NAV_V2_EXTRA_FIELDS + _MISSION_OBS_FORMATION_EXTRA_FIELDS
    ),
    MISSION_OBS_NAV_V2_FORMATION_ROLE_V1: list(
        _MISSION_OBS_BASIC_FIELDS
        + _MISSION_OBS_NAV_V2_EXTRA_FIELDS
        + _MISSION_OBS_FORMATION_EXTRA_FIELDS
        + _MISSION_OBS_ROLE_EXTRA_FIELDS
    ),
    MISSION_OBS_NAV_V2_COOPERATIVE_TAKEOFF_V1: list(
        _MISSION_OBS_BASIC_FIELDS
        + _MISSION_OBS_NAV_V2_EXTRA_FIELDS
        + _MISSION_OBS_COOPERATIVE_TAKEOFF_EXTRA_FIELDS
        + _MISSION_OBS_FORMATION_EXTRA_FIELDS
        + _MISSION_OBS_ROLE_EXTRA_FIELDS
    ),
    MISSION_OBS_NAVAL_SCREEN_STATION_V1: list(_MISSION_OBS_NAVAL_SCREEN_STATION_FIELDS),
    MISSION_OBS_AIR_COMBAT_C2_ROE_V1: list(_MISSION_OBS_AIR_COMBAT_C2_ROE_FIELDS),
    MISSION_OBS_AIR_COMBAT_C2_ROE_V2: list(
        _MISSION_OBS_AIR_COMBAT_C2_ROE_FIELDS + _MISSION_OBS_AIR_COMBAT_C2_ROE_V2_EXTRA_FIELDS
    ),
}

MISSION_OBS_DIM_BY_NAME = {
    mode: len(field_names)
    for mode, field_names in MISSION_OBS_FIELD_NAMES_BY_NAME.items()
}

MISSION_OBS_FIELD_INDEX_BY_NAME = {
    mode: {field_name: idx for idx, field_name in enumerate(field_names)}
    for mode, field_names in MISSION_OBS_FIELD_NAMES_BY_NAME.items()
}

VALID_MISSION_OBS_MODES = set(MISSION_OBS_MODE_CODE_BY_NAME.keys())
BASE_MISSION_OBS_MODES = (
    MISSION_OBS_BASIC,
    MISSION_OBS_NAV_V1,
    MISSION_OBS_NAV_V2,
    MISSION_OBS_NAV_V2_FORMATION_V1,
    MISSION_OBS_NAV_V2_FORMATION_ROLE_V1,
)
COOPERATIVE_MISSION_OBS_MODES = (
    MISSION_OBS_NAV_V2_COOPERATIVE_TAKEOFF_V1,
)
NAVAL_MISSION_OBS_MODES = (
    MISSION_OBS_NAVAL_SCREEN_STATION_V1,
)
AIR_COMBAT_MISSION_OBS_MODES = (
    MISSION_OBS_AIR_COMBAT_C2_ROE_V1,
    MISSION_OBS_AIR_COMBAT_C2_ROE_V2,
)
PYTHON_OWNED_MISSION_OBS_MODES = frozenset(NAVAL_MISSION_OBS_MODES + AIR_COMBAT_MISSION_OBS_MODES)


def normalize_mission_obs_mode(mode: str | None) -> str:
    normalized = str(mode or MISSION_OBS_BASIC).strip().lower()
    if normalized == "":
        normalized = MISSION_OBS_BASIC
    if normalized not in VALID_MISSION_OBS_MODES:
        raise ValueError(f"Unknown mission observation mode: {mode!r}")
    return normalized


def mission_obs_mode_code(mode: str | None) -> int:
    return int(MISSION_OBS_MODE_CODE_BY_NAME[normalize_mission_obs_mode(mode)])


def mission_observation_python_owned(mode: str | None) -> bool:
    return normalize_mission_obs_mode(mode) in PYTHON_OWNED_MISSION_OBS_MODES


def mission_observation_dim(mode: str | None) -> int:
    return int(MISSION_OBS_DIM_BY_NAME[normalize_mission_obs_mode(mode)])


def mission_observation_field_names(mode: str | None) -> list[str]:
    return list(MISSION_OBS_FIELD_NAMES_BY_NAME[normalize_mission_obs_mode(mode)])


def mission_observation_field_index(mode: str | None, field_name: str) -> int:
    mode_norm = normalize_mission_obs_mode(mode)
    normalized_field_name = str(field_name).strip()
    try:
        return int(MISSION_OBS_FIELD_INDEX_BY_NAME[mode_norm][normalized_field_name])
    except KeyError as exc:
        raise ValueError(
            f"Unknown mission observation field {field_name!r} for mode {mode_norm!r}"
        ) from exc


def mission_observation_has_field(mode: str | None, field_name: str) -> bool:
    mode_norm = normalize_mission_obs_mode(mode)
    normalized_field_name = str(field_name).strip()
    return normalized_field_name in MISSION_OBS_FIELD_INDEX_BY_NAME[mode_norm]
