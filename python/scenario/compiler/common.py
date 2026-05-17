from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import ef_py


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_SCALAR_TYPES = (str, int, float, bool, type(None))

_OBJECTIVE_PROPERTY_MAP = {
    "altitude": ef_py.ConditionalObjectiveProperty.Altitude,
    "altitude_agl": ef_py.ConditionalObjectiveProperty.AltitudeAGL,
    "speed": ef_py.ConditionalObjectiveProperty.Speed,
    "ground_speed": ef_py.ConditionalObjectiveProperty.GroundSpeed,
    "gear": ef_py.ConditionalObjectiveProperty.Gear,
    "heading_error_deg": ef_py.ConditionalObjectiveProperty.HeadingErrorDeg,
    "command_code": ef_py.ConditionalObjectiveProperty.CommandCode,
    "ground_track_error_deg": ef_py.ConditionalObjectiveProperty.GroundTrackErrorDeg,
    "runway_cross_abs_m": ef_py.ConditionalObjectiveProperty.RunwayCrossAbsM,
    "runway_from_threshold_m": ef_py.ConditionalObjectiveProperty.RunwayFromThresholdM,
    "on_runway_geom": ef_py.ConditionalObjectiveProperty.OnRunwayGeom,
    "on_runway": ef_py.ConditionalObjectiveProperty.OnRunway,
    "on_ground": ef_py.ConditionalObjectiveProperty.OnGround,
    "sink_rate_abs_mps": ef_py.ConditionalObjectiveProperty.SinkRateAbsMps,
    "vertical_speed_abs_mps": ef_py.ConditionalObjectiveProperty.SinkRateAbsMps,
    "ils_localizer_abs": ef_py.ConditionalObjectiveProperty.IlsLocalizerAbs,
    "ils_glideslope_abs": ef_py.ConditionalObjectiveProperty.IlsGlideslopeAbs,
    "dme_m": ef_py.ConditionalObjectiveProperty.DmeM,
    "heading": ef_py.ConditionalObjectiveProperty.Heading,
    "x": ef_py.ConditionalObjectiveProperty.X,
    "y": ef_py.ConditionalObjectiveProperty.Y,
    "self_active": ef_py.ConditionalObjectiveProperty.SelfActive,
    "target_active": ef_py.ConditionalObjectiveProperty.TargetActive,
    "self_health": ef_py.ConditionalObjectiveProperty.SelfHealth,
    "target_health": ef_py.ConditionalObjectiveProperty.TargetHealth,
    "missiles_remaining": ef_py.ConditionalObjectiveProperty.MissilesRemaining,
    "target_range_m": ef_py.ConditionalObjectiveProperty.TargetRangeM,
}

_OBJECTIVE_OP_MAP = {
    ">=": ef_py.ConditionalObjectiveOp.GreaterEqual,
    ">": ef_py.ConditionalObjectiveOp.GreaterThan,
    "<=": ef_py.ConditionalObjectiveOp.LessEqual,
    "<": ef_py.ConditionalObjectiveOp.LessThan,
}

_OBJECTIVE_DYNAMIC_TARGET_MAP = {
    "CMD_ALT": (ef_py.ConditionalObjectiveTargetKind.CommandAltitude, 0.95),
    "CMD_ALTITUDE": (ef_py.ConditionalObjectiveTargetKind.CommandAltitude, 0.95),
    "CMD_SPEED": (ef_py.ConditionalObjectiveTargetKind.CommandSpeed, 0.90),
    "CMD_HDG": (ef_py.ConditionalObjectiveTargetKind.CommandHeading, 1.0),
    "CMD_HEADING": (ef_py.ConditionalObjectiveTargetKind.CommandHeading, 1.0),
}

_SURFACE_TYPE_MAP = {
    "Concrete": 0,
    "Asphalt": 1,
    "HardPacked": 2,
    "SoftDirt": 3,
    "Water": 4,
    "Obstacle": 5,
}


def _mtime_ns(path: str) -> int:
    return int(os.stat(path).st_mtime_ns)


def _coerce_nonnegative_int(value: Any, default: int = 0) -> int:
    try:
        out = int(value)
    except Exception:
        return int(default)
    return out if out >= 0 else int(default)


def _normalize_waypoint_mode(mode_value: Any) -> str:
    mode = str(mode_value if mode_value is not None else "flyby").strip().lower()
    if mode in ("fly-over", "fly_over", "overfly"):
        return "flyover"
    if mode in ("flyby", "flyover"):
        return mode
    return "flyby"


def _canonical_recovery_approach_name(value: Any, *, landing_mode: str = "") -> str:
    default_by_mode = {
        "ils": "ILS",
        "ils_final": "ILS",
        "visual": "Visual",
        "overhead": "Overhead",
        "tacan": "TACAN",
    }
    default_name = default_by_mode.get(str(landing_mode or "").strip().lower(), "StraightIn")
    if value is None:
        return default_name
    try:
        if hasattr(value, "name"):
            value = value.name
    except Exception:
        pass
    if isinstance(value, str):
        key = str(value).strip().lower()
        mapping = {
            "": default_name,
            "none": "None",
            "straightin": "StraightIn",
            "straight_in": "StraightIn",
            "ils": "ILS",
            "ils_final": "ILS",
            "visual": "Visual",
            "overhead": "Overhead",
            "tacan": "TACAN",
        }
        return mapping.get(key, default_name)
    mapping_by_int = {
        0: "None",
        1: "StraightIn",
        2: "ILS",
        3: "Visual",
        4: "Overhead",
        5: "TACAN",
    }
    return mapping_by_int.get(_coerce_nonnegative_int(value, 0), default_name)


def _stable_ref_id(payload: Any) -> int:
    try:
        text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except Exception:
        text = repr(payload)
    digest = hashlib.sha1(text.encode("utf-8")).digest()
    ref_id = int.from_bytes(digest[:8], "big", signed=False)
    return ref_id if ref_id > 0 else 1


__all__ = [
    "REPO_ROOT",
    "_SCALAR_TYPES",
    "_OBJECTIVE_PROPERTY_MAP",
    "_OBJECTIVE_OP_MAP",
    "_OBJECTIVE_DYNAMIC_TARGET_MAP",
    "_SURFACE_TYPE_MAP",
    "_mtime_ns",
    "_coerce_nonnegative_int",
    "_normalize_waypoint_mode",
    "_canonical_recovery_approach_name",
    "_stable_ref_id",
]
