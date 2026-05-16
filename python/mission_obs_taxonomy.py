from __future__ import annotations

MISSION_OBS_BASIC = "basic"
MISSION_OBS_NAV_V1 = "nav_v1"
MISSION_OBS_NAV_V2 = "nav_v2"
MISSION_OBS_NAV_V2_FORMATION_V1 = "nav_v2_formation_v1"
MISSION_OBS_NAV_V2_FORMATION_ROLE_V1 = "nav_v2_formation_role_v1"
MISSION_OBS_NAV_V2_COOPERATIVE_TAKEOFF_V1 = "nav_v2_cooperative_takeoff_v1"

MISSION_OBS_MODE_CODE_BY_NAME = {
    MISSION_OBS_BASIC: 0,
    MISSION_OBS_NAV_V1: 1,
    MISSION_OBS_NAV_V2: 2,
    MISSION_OBS_NAV_V2_FORMATION_V1: 3,
    MISSION_OBS_NAV_V2_FORMATION_ROLE_V1: 4,
    MISSION_OBS_NAV_V2_COOPERATIVE_TAKEOFF_V1: 5,
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


def normalize_mission_obs_mode(mode: str | None) -> str:
    normalized = str(mode or MISSION_OBS_BASIC).strip().lower()
    if normalized == "":
        normalized = MISSION_OBS_BASIC
    if normalized not in VALID_MISSION_OBS_MODES:
        raise ValueError(f"Unknown mission observation mode: {mode!r}")
    return normalized


def mission_obs_mode_code(mode: str | None) -> int:
    return int(MISSION_OBS_MODE_CODE_BY_NAME[normalize_mission_obs_mode(mode)])


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
