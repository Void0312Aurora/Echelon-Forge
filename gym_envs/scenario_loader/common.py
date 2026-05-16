import json
import os

import ef_py


LEGACY_EXECUTION_STEP_RUNTIME_MODES = {"legacy", "python", "off", "0", "false"}
LEGACY_FLIGHT_SHAPING_BACKENDS = {"legacy", "python", "off", "0", "false"}

OBJECTIVE_PROPERTY_MAP = {
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
}

OBJECTIVE_OP_MAP = {
    ">=": ef_py.ConditionalObjectiveOp.GreaterEqual,
    ">": ef_py.ConditionalObjectiveOp.GreaterThan,
    "<=": ef_py.ConditionalObjectiveOp.LessEqual,
    "<": ef_py.ConditionalObjectiveOp.LessThan,
}

OBJECTIVE_DYNAMIC_TARGET_MAP = {
    "CMD_ALT": (ef_py.ConditionalObjectiveTargetKind.CommandAltitude, 0.95),
    "CMD_ALTITUDE": (ef_py.ConditionalObjectiveTargetKind.CommandAltitude, 0.95),
    "CMD_SPEED": (ef_py.ConditionalObjectiveTargetKind.CommandSpeed, 0.90),
    "CMD_HDG": (ef_py.ConditionalObjectiveTargetKind.CommandHeading, 1.0),
    "CMD_HEADING": (ef_py.ConditionalObjectiveTargetKind.CommandHeading, 1.0),
}


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
    raw_mode = os.environ.get("CMO_EXECUTION_STEP_RUNTIME", "compiled") if mode is None else mode
    normalized = str(raw_mode).strip().lower()
    if normalized in LEGACY_EXECUTION_STEP_RUNTIME_MODES:
        return "legacy"
    if normalized in {"", "compiled", "on", "1", "true"}:
        return "compiled"
    return normalized


def execution_step_runtime_mode_enabled(mode: str | None) -> bool:
    return normalize_execution_step_runtime_mode(mode) != "legacy"


def normalize_flight_shaping_backend(backend: str | None) -> str:
    raw_backend = os.environ.get("CMO_FLIGHT_SHAPING_BACKEND", "auto") if backend is None else backend
    normalized = str(raw_backend).strip().lower()
    if normalized in LEGACY_FLIGHT_SHAPING_BACKENDS:
        return "legacy"
    if normalized in {"", "auto"}:
        return "auto"
    return normalized


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
