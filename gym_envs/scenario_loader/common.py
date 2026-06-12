import json
from collections.abc import Iterator, Mapping

import ef_py

class _LazyEfEnumMap(Mapping[str, object]):
    def __init__(self, enum_owner_name: str, entries: dict[str, object]):
        self._enum_owner_name = str(enum_owner_name)
        self._entries = dict(entries)

    def _enum_owner(self) -> object:
        owner = getattr(ef_py, self._enum_owner_name, None)
        if owner is None:
            raise AttributeError(
                f"ef_py is missing {self._enum_owner_name}; "
                "objective runtime surfaces require the maintained build binding"
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


OBJECTIVE_PROPERTY_MAP = _LazyEfEnumMap(
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

OBJECTIVE_OP_MAP = _LazyEfEnumMap(
    "ConditionalObjectiveOp",
    {
        ">=": "GreaterEqual",
        ">": "GreaterThan",
        "<=": "LessEqual",
        "<": "LessThan",
    },
)

OBJECTIVE_DYNAMIC_TARGET_MAP = _LazyEfEnumMap(
    "ConditionalObjectiveTargetKind",
    {
        "CMD_ALT": ("CommandAltitude", 0.95),
        "CMD_ALTITUDE": ("CommandAltitude", 0.95),
        "CMD_SPEED": ("CommandSpeed", 0.90),
        "CMD_HDG": ("CommandHeading", 1.0),
        "CMD_HEADING": ("CommandHeading", 1.0),
    },
)


def coerce_nonnegative_int(value, default: int = 0) -> int:
    try:
        out = int(value)
    except Exception:
        return int(default)
    return out if out >= 0 else int(default)


def formation_role_code_from_member(member) -> int:
    if member is None:
        return 0
    raw = getattr(member, "formation_role_id", None)
    if raw is None:
        return 0
    text = str(raw).strip()
    if not text:
        return 0
    if hasattr(ef_py, "FormationRole"):
        return int(getattr(ef_py.FormationRole, text, getattr(ef_py.FormationRole, "Unspecified", 0)))
    return 0


def normalize_execution_step_runtime_mode(mode: str | None) -> str:
    if mode is None:
        return "compiled"
    normalized = str(mode).strip().lower()
    if normalized == "legacy":
        raise ValueError("execution_step_runtime_mode='legacy' has been removed from scenario runtime inputs")
    if normalized in {"", "compiled"}:
        return "compiled"
    raise ValueError(f"Unknown execution_step_runtime_mode: {mode!r}")


def execution_step_runtime_mode_enabled(mode: str | None) -> bool:
    normalize_execution_step_runtime_mode(mode)
    return True


def normalize_flight_shaping_backend(backend: str | None) -> str:
    raw_backend = "auto" if backend is None else backend
    normalized = str(raw_backend).strip().lower()
    if normalized == "legacy":
        raise ValueError("flight_shaping_backend='legacy' has been removed from scenario runtime inputs")
    if normalized in {"", "auto"}:
        return "auto"
    if normalized in {"compiled", "gpu_host"}:
        return normalized
    raise ValueError(f"Unknown flight_shaping_backend: {raw_backend!r}")


def stable_json_dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def safe_json_dict_loads(raw: str | None) -> dict | None:
    if raw is None:
        return None
    try:
        data = json.loads(str(raw))
    except Exception:
        return None
    return data if isinstance(data, dict) else None
