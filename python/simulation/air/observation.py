"""Native-to-scripted Air observation projection.

This adapter consumes the maintained ``RuntimeFacade`` DTOs and produces the
small dictionary expected by the neutral Air scripted execution model.  It is
kept under ``python.simulation`` so neither the simulator nor a scripted
provider has to import an RL environment.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from python.mission_obs_taxonomy import (
    MISSION_OBS_NAV_V2_COOPERATIVE_TAKEOFF_V1,
    mission_observation_dim,
    mission_observation_field_index,
)


AIR_SCRIPTED_MISSION_MODE = MISSION_OBS_NAV_V2_COOPERATIVE_TAKEOFF_V1
AIR_SCRIPTED_MAX_CONTACTS = 8
AIR_SCRIPTED_MAX_RWR = 8


def build_air_instrument_vector(
    instrument_state: Any,
    *,
    ils: Sequence[float] = (0.0, 0.0, 0.0, 0.0),
) -> np.ndarray:
    """Project a native InstrumentState to the maintained Air vector."""

    def value(name: str, default: float = 0.0) -> float:
        try:
            return float(getattr(instrument_state, name))
        except (AttributeError, TypeError, ValueError):
            return float(default)

    vector = [
        value("ias"),
        value("mach"),
        value("alt_baro"),
        value("alt_radar"),
        value("vvi"),
        value("aoa"),
        value("beta"),
        value("pitch"),
        value("roll"),
        value("heading"),
        value("g_load"),
        value("g_load_axial"),
        value("p"),
        value("q"),
        value("r"),
        value("engine_rpm"),
        value("fuel_internal") + value("fuel_external"),
        value("fuel_flow"),
        value("gear_pos"),
        value("flaps_pos"),
        value("speedbrake_pos"),
        value("cmd_heading"),
        value("cmd_alt"),
        value("cmd_speed"),
        value("lat"),
        value("lon"),
        value("vn"),
        value("ve"),
        value("vd"),
        value("ground_speed"),
        value("ground_track"),
        value("wind_speed"),
        value("wind_dir"),
        value("oat", 15.0),
        value("gps_available", 1.0),
        value("position_uncertainty", 10.0),
        value("rwr_active"),
        value("missiles_remaining"),
    ]
    vector.extend(float(item) for item in tuple(ils)[:4])
    vector.extend([0.0] * max(0, 4 - len(tuple(ils)[:4])))
    return np.nan_to_num(np.asarray(vector, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)


def build_air_contact_matrix(observation: Any, *, max_contacts: int = AIR_SCRIPTED_MAX_CONTACTS) -> np.ndarray:
    """Project native contact DTOs to ``(range, azimuth, elevation, closure, age)``."""

    out = np.zeros((int(max_contacts), 5), dtype=np.float32)
    for index, contact in enumerate(list(getattr(observation, "contacts", ()) or ())[: int(max_contacts)]):
        out[index] = [
            _float_field(contact, "range"),
            _float_field(contact, "azimuth"),
            _float_field(contact, "elevation"),
            _float_field(contact, "closing_speed"),
            _float_field(contact, "time_since_update"),
        ]
    return out


def build_air_rwr_matrix(observation: Any, *, max_rwr: int = AIR_SCRIPTED_MAX_RWR) -> np.ndarray:
    """Project native RWR warning DTOs to ``(bearing, strength, lock, launch)``."""

    out = np.zeros((int(max_rwr), 4), dtype=np.float32)
    for index, warning in enumerate(list(getattr(observation, "rwr_warnings", ()) or ())[: int(max_rwr)]):
        out[index] = [
            _float_field(warning, "bearing"),
            _float_field(warning, "signal_strength"),
            _bool_field(warning, "is_lock"),
            _bool_field(warning, "is_launch"),
        ]
    return out


def build_air_mission_vector(
    command: Any,
    *,
    mode: str = AIR_SCRIPTED_MISSION_MODE,
    mission_facts: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """Project a maintained mission command into a named-field Air vector."""

    vector = np.zeros((int(mission_observation_dim(mode)),), dtype=np.float32)

    def set_field(name: str, value: Any) -> None:
        try:
            index = mission_observation_field_index(mode, name)
        except ValueError:
            return
        if index < vector.size:
            vector[index] = _numeric(value)

    set_field("command_code", _field(command, "command_code"))
    set_field("target_heading_deg", _field(command, "cmd_heading_deg"))
    set_field("target_altitude_m", _field(command, "cmd_altitude_m"))
    set_field("target_speed_mps", _field(command, "cmd_speed_mps"))
    set_field("roe_state", _field(command, "roe_state"))
    set_field("authorization_to_fire", _field(command, "authorization_to_fire"))
    set_field("assigned_target_id", _field(command, "assigned_target_id"))
    set_field("assigned_target_track_id", _field(command, "assigned_target_track_id"))
    set_field("assigned_target_source_id", _field(command, "assigned_target_source_id"))
    set_field("engagement_authority_holder_id", _field(command, "engagement_authority_holder_id"))
    set_field("engagement_authority_grantor_id", _field(command, "engagement_authority_grantor_id"))
    set_field("takeoff_procedure_code", _field(command, "takeoff_procedure_id"))
    set_field("takeoff_clearance_code", _field(command, "takeoff_clearance_id"))
    set_field("takeoff_interval_s", _field(command, "takeoff_interval_s"))
    set_field("runway_slot_code", _field(command, "runway_slot_id"))
    set_field("form_offset_x_m", _field(command, "form_offset_x"))
    set_field("form_offset_y_m", _field(command, "form_offset_y"))
    set_field("form_offset_z_m", _field(command, "form_offset_z"))
    for name, value in (mission_facts or {}).items():
        set_field(str(name), value)
    return vector


def build_air_scripted_observation(
    observation: Any,
    instrument_state: Any,
    command: Any = None,
    *,
    mode: str = AIR_SCRIPTED_MISSION_MODE,
    ils: Sequence[float] = (0.0, 0.0, 0.0, 0.0),
    max_contacts: int = AIR_SCRIPTED_MAX_CONTACTS,
    max_rwr: int = AIR_SCRIPTED_MAX_RWR,
    mission_facts: Mapping[str, Any] | None = None,
) -> dict[str, np.ndarray]:
    """Build the neutral scripted Air observation dictionary."""

    return {
        "instruments": build_air_instrument_vector(instrument_state, ils=ils),
        "contacts": build_air_contact_matrix(observation, max_contacts=max_contacts),
        "rwr": build_air_rwr_matrix(observation, max_rwr=max_rwr),
        "mission": build_air_mission_vector(command, mode=mode, mission_facts=mission_facts),
    }


def _field(value: Any, name: str, default: Any = 0.0) -> Any:
    if value is None:
        return default
    for candidate in (value, getattr(value, "shared_core", None), getattr(value, "air_takeoff", None), getattr(value, "air_formation", None)):
        if candidate is not None and hasattr(candidate, name):
            return getattr(candidate, name)
    return default


def _numeric(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        try:
            return float(getattr(value, "value"))
        except (AttributeError, TypeError, ValueError):
            return 0.0


def _float_field(value: Any, name: str) -> float:
    return _numeric(getattr(value, name, 0.0))


def _bool_field(value: Any, name: str) -> float:
    return 1.0 if bool(getattr(value, name, False)) else 0.0


__all__ = [
    "AIR_SCRIPTED_MAX_CONTACTS",
    "AIR_SCRIPTED_MAX_RWR",
    "AIR_SCRIPTED_MISSION_MODE",
    "build_air_contact_matrix",
    "build_air_instrument_vector",
    "build_air_mission_vector",
    "build_air_rwr_matrix",
    "build_air_scripted_observation",
]
