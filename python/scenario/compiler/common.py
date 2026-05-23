from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator, Mapping
from typing import Any

import ef_py


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_SCALAR_TYPES = (str, int, float, bool, type(None))

class _LazyEfEnumMap(Mapping[str, object]):
    def __init__(self, enum_owner_name: str, entries: dict[str, object]):
        self._enum_owner_name = str(enum_owner_name)
        self._entries = dict(entries)

    def _enum_owner(self) -> object:
        owner = getattr(ef_py, self._enum_owner_name, None)
        if owner is None:
            raise AttributeError(
                f"ef_py is missing {self._enum_owner_name}; "
                "scenario compiler objective metadata requires the maintained build binding"
            )
        return owner

    def _resolve_value(self, raw: object) -> object:
        if isinstance(raw, tuple):
            return tuple(self._resolve_value(item) for item in raw)
        if isinstance(raw, str):
            return getattr(self._enum_owner(), raw)
        return raw

    def __getitem__(self, key: str) -> object:
        return self._resolve_value(self._entries[key])

    def __iter__(self) -> Iterator[str]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def get(self, key: str, default: object = None) -> object:
        if key not in self._entries:
            return default
        return self[key]


_OBJECTIVE_PROPERTY_MAP = _LazyEfEnumMap(
    "ConditionalObjectiveProperty",
    {
        "altitude": "Altitude",
        "altitude_agl": "AltitudeAGL",
        "speed": "Speed",
        "ground_speed": "GroundSpeed",
        "gear": "Gear",
        "heading_error_deg": "HeadingErrorDeg",
        "command_code": "CommandCode",
        "ground_track_error_deg": "GroundTrackErrorDeg",
        "runway_cross_abs_m": "RunwayCrossAbsM",
        "runway_from_threshold_m": "RunwayFromThresholdM",
        "on_runway_geom": "OnRunwayGeom",
        "on_runway": "OnRunway",
        "on_ground": "OnGround",
        "sink_rate_abs_mps": "SinkRateAbsMps",
        "vertical_speed_abs_mps": "SinkRateAbsMps",
        "ils_localizer_abs": "IlsLocalizerAbs",
        "ils_glideslope_abs": "IlsGlideslopeAbs",
        "dme_m": "DmeM",
        "heading": "Heading",
        "x": "X",
        "y": "Y",
        "self_active": "SelfActive",
        "target_active": "TargetActive",
        "self_health": "SelfHealth",
        "target_health": "TargetHealth",
        "missiles_remaining": "MissilesRemaining",
        "target_range_m": "TargetRangeM",
    },
)

_OBJECTIVE_OP_MAP = _LazyEfEnumMap(
    "ConditionalObjectiveOp",
    {
        ">=": "GreaterEqual",
        ">": "GreaterThan",
        "<=": "LessEqual",
        "<": "LessThan",
    },
)

_OBJECTIVE_DYNAMIC_TARGET_MAP = _LazyEfEnumMap(
    "ConditionalObjectiveTargetKind",
    {
        "CMD_ALT": ("CommandAltitude", 0.95),
        "CMD_ALTITUDE": ("CommandAltitude", 0.95),
        "CMD_SPEED": ("CommandSpeed", 0.90),
        "CMD_HDG": ("CommandHeading", 1.0),
        "CMD_HEADING": ("CommandHeading", 1.0),
    },
)

_SURFACE_TYPE_MAP = {
    "Concrete": 0,
    "Asphalt": 1,
    "HardPacked": 2,
    "SoftDirt": 3,
    "Water": 4,
    "Obstacle": 5,
}

DEFAULT_TERRAIN_TYPE = "flat"
TERRAIN_TYPE_SOURCE_EXPLICIT = "explicit_schema"
TERRAIN_TYPE_SOURCE_DEFAULT = "default_mainline"
TERRAIN_TYPE_SOURCE_COMPATIBILITY = "explicit_legacy_compatibility"


def _normalize_terrain_type_value(
    terrain_type: Any,
    *,
    default: str = DEFAULT_TERRAIN_TYPE,
) -> str:
    normalized = str(default if terrain_type is None else terrain_type).strip()
    return normalized or str(default)


def _terrain_type_source_for_value(terrain_type: str) -> str:
    normalized = str(terrain_type).strip().lower()
    if normalized in {"legacy", "hill", "gaussian_hill", "mountain"}:
        return TERRAIN_TYPE_SOURCE_COMPATIBILITY
    return TERRAIN_TYPE_SOURCE_EXPLICIT


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


def _resolve_environment_terrain_type(
    env_cfg: dict[str, Any] | None,
    *,
    default: str = DEFAULT_TERRAIN_TYPE,
) -> str:
    return resolve_environment_terrain_config(env_cfg, default=default)[0]


def resolve_environment_terrain_config(
    env_cfg: dict[str, Any] | None,
    *,
    default: str = DEFAULT_TERRAIN_TYPE,
) -> tuple[str, str]:
    if not isinstance(env_cfg, dict):
        env_cfg = {}
    if "terrain_type" not in env_cfg:
        return _normalize_terrain_type_value(default, default=default), TERRAIN_TYPE_SOURCE_DEFAULT
    terrain_type = _normalize_terrain_type_value(env_cfg.get("terrain_type"), default=default)
    return terrain_type, _terrain_type_source_for_value(terrain_type)


__all__ = [
    "REPO_ROOT",
    "_SCALAR_TYPES",
    "_OBJECTIVE_PROPERTY_MAP",
    "_OBJECTIVE_OP_MAP",
    "_OBJECTIVE_DYNAMIC_TARGET_MAP",
    "_SURFACE_TYPE_MAP",
    "DEFAULT_TERRAIN_TYPE",
    "TERRAIN_TYPE_SOURCE_EXPLICIT",
    "TERRAIN_TYPE_SOURCE_DEFAULT",
    "TERRAIN_TYPE_SOURCE_COMPATIBILITY",
    "_normalize_terrain_type_value",
    "_terrain_type_source_for_value",
    "_mtime_ns",
    "_coerce_nonnegative_int",
    "_normalize_waypoint_mode",
    "_canonical_recovery_approach_name",
    "_stable_ref_id",
    "_resolve_environment_terrain_type",
    "resolve_environment_terrain_config",
]
