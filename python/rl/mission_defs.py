from __future__ import annotations


COMMAND_CODE_IDLE = 0
COMMAND_CODE_TAKEOFF = 1
COMMAND_CODE_VECTOR = 2
COMMAND_CODE_ROUTE = 3
COMMAND_CODE_LANDING = 4

COMMAND_NAME_TO_CODE = {
    "idle": COMMAND_CODE_IDLE,
    "takeoff": COMMAND_CODE_TAKEOFF,
    "vector": COMMAND_CODE_VECTOR,
    "route": COMMAND_CODE_ROUTE,
    "landing": COMMAND_CODE_LANDING,
}

TAKEOFF_PHASE_NAMES = {"scramble", "takeoff", "departure"}
CRUISE_PHASE_NAMES = {"transit_to_station", "establish_cap", "on_station", "reposition", "rtb"}
LANDING_PHASE_NAMES = {"approach_armed", "landing_final", "rollout"}


def normalize_phase_name(phase_name: str | None) -> str:
    return str(phase_name or "").strip().lower()


def normalize_command_code(command_code: int | float | str | None, default: int = COMMAND_CODE_IDLE) -> int:
    try:
        return int(command_code)
    except Exception:
        return int(default)


def is_route_command_code(command_code: int | float | str | None) -> bool:
    return normalize_command_code(command_code) == COMMAND_CODE_ROUTE


def is_landing_command_code(command_code: int | float | str | None) -> bool:
    return normalize_command_code(command_code) == COMMAND_CODE_LANDING


def is_takeoff_phase_name(phase_name: str | None) -> bool:
    return normalize_phase_name(phase_name) in TAKEOFF_PHASE_NAMES


def is_cruise_phase_name(phase_name: str | None) -> bool:
    return normalize_phase_name(phase_name) in CRUISE_PHASE_NAMES


def is_landing_phase_name(phase_name: str | None) -> bool:
    return normalize_phase_name(phase_name) in LANDING_PHASE_NAMES


def command_code_for_phase_name(
    phase_name: str | None,
    *,
    has_waypoints: bool,
    mission_cmd_code: int,
) -> int:
    phase = normalize_phase_name(phase_name)
    if phase in TAKEOFF_PHASE_NAMES:
        return COMMAND_CODE_TAKEOFF
    if phase in LANDING_PHASE_NAMES:
        return COMMAND_CODE_LANDING
    if has_waypoints or is_route_command_code(mission_cmd_code):
        return COMMAND_CODE_ROUTE
    return COMMAND_CODE_VECTOR


def scripted_mode_for_phase_name(phase_name: str | None) -> str | None:
    phase = normalize_phase_name(phase_name)
    if not phase:
        return None
    if phase in TAKEOFF_PHASE_NAMES:
        return "takeoff"
    if phase in LANDING_PHASE_NAMES:
        return "landing_ils"
    if phase in CRUISE_PHASE_NAMES:
        return "stable_flight"
    return None


def scripted_mode_for_command_code(
    command_code: int | float | str | None,
    *,
    alt_agl_m: float | None = None,
    takeoff_transition_alt_agl_m: float | None = None,
) -> str | None:
    code = normalize_command_code(command_code, default=COMMAND_CODE_IDLE)
    if code == COMMAND_CODE_LANDING:
        return "landing_ils"
    if code in (COMMAND_CODE_VECTOR, COMMAND_CODE_ROUTE):
        return "stable_flight"
    if code == COMMAND_CODE_TAKEOFF:
        if (
            alt_agl_m is not None
            and takeoff_transition_alt_agl_m is not None
            and float(alt_agl_m) >= float(takeoff_transition_alt_agl_m)
        ):
            return "stable_flight"
        return "takeoff"
    return None
