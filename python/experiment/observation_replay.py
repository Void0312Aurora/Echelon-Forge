"""Exact replay identity for the maintained AgentObservation projection.

Packet ids, refs and version tokens identify a transport owner, not a native
state cursor. Validate that envelope locally, then compare all declared Agent
observation values and semantic provenance. This module never reads a runtime.
"""

from __future__ import annotations

import math
import re
from types import MappingProxyType

from python.experiment.contracts import ContractError, content_digest


AGENT_OBSERVATION_FLOAT_FIELDS = (
    "sim_time",
    "x",
    "y",
    "z",
    "vx",
    "vy",
    "vz",
    "heading",
    "pitch",
    "roll",
    "speed",
    "health",
    "gear_state",
    "throttle",
    "total_reward",
)
AGENT_OBSERVATION_UINT64_FIELDS = ("id",)
AGENT_OBSERVATION_INT_FIELDS = ("missiles_remaining",)
AGENT_OBSERVATION_BOOL_FIELDS = ("can_fire",)
AGENT_OBSERVATION_SEQUENCE_FIELDS = ("contacts", "rwr_warnings", "esm_detections")
TRACK_FLOAT_FIELDS = (
    "range",
    "azimuth",
    "elevation",
    "closing_speed",
    "time_since_update",
    "quality",
    "confidence",
    "classification_confidence",
)
TRACK_UINT64_FIELDS = ("id",)
TRACK_INT_FIELDS = ("source", "classification", "status", "usability")
TRACK_BOOL_FIELDS = ("iff_known",)
RWR_FLOAT_FIELDS = ("bearing", "signal_strength")
RWR_UINT64_FIELDS = ("source_id",)
RWR_BOOL_FIELDS = ("is_lock", "is_launch")
ESM_FLOAT_FIELDS = (
    "bearing_deg",
    "signal_strength",
    "received_power_dbm",
    "sensitivity_margin_db",
    "observed_time_s",
    "age_s",
    "confidence",
)
ESM_UINT64_FIELDS = ("source_id",)
ESM_BOOL_FIELDS = ("has_rf_power", "classification_known", "is_jammer", "is_lock", "is_guidance")

OBSERVATION_REPLAY_FIELD_CATALOGUE = MappingProxyType(
    {
        "AgentObservation": (
            *AGENT_OBSERVATION_FLOAT_FIELDS,
            *AGENT_OBSERVATION_UINT64_FIELDS,
            *AGENT_OBSERVATION_INT_FIELDS,
            *AGENT_OBSERVATION_BOOL_FIELDS,
            *AGENT_OBSERVATION_SEQUENCE_FIELDS,
        ),
        "TrackData": (
            *TRACK_FLOAT_FIELDS,
            *TRACK_UINT64_FIELDS,
            *TRACK_INT_FIELDS,
            *TRACK_BOOL_FIELDS,
        ),
        "RWREvent": (*RWR_FLOAT_FIELDS, *RWR_UINT64_FIELDS, *RWR_BOOL_FIELDS),
        "ESMEvent": (*ESM_FLOAT_FIELDS, *ESM_UINT64_FIELDS, *ESM_BOOL_FIELDS),
    }
)
OBSERVATION_PACKET_FIELDS = (
    "snapshot_version",
    "barrier_id",
    "source_time_s",
    "provenance",
    "refs",
    "agent_observations",
    "instrument_states",
)
OBSERVATION_PROVENANCE_FIELDS = (
    "information_state_layer",
    "source_label",
    "maintained_status",
    "observation_packet_ids",
    "source_observation_versions",
    "diagnostics_reason",
)

_UINT64_MAX = (1 << 64) - 1
_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9_]*\Z")
_DECIMAL = r"(?:0|[1-9][0-9]*)"
_SCOPED_VERSION = re.compile(rf"branch:([A-Za-z0-9][A-Za-z0-9_.-]{{0,127}}):({_DECIMAL})\Z")


def _field(value: object, name: str) -> object:
    try:
        return getattr(value, name)
    except Exception as exc:
        raise ContractError(f"observation replay: missing or unreadable field {name!r}") from exc


def _uint64(value: object, name: str, *, nonzero: bool = False) -> int:
    if type(value) is not int or not (int(nonzero) <= value <= _UINT64_MAX):
        raise ContractError(
            f"observation replay: {name} must be a {'nonzero ' if nonzero else ''}uint64"
        )
    return value


def _float_hex(value: object, name: str) -> str:
    if type(value) is not float or not math.isfinite(value):
        raise ContractError(f"observation replay: {name} must be a finite float")
    return value.hex()


def _sequence(value: object, name: str) -> tuple[object, ...]:
    if type(value) not in (tuple, list):
        raise ContractError(f"observation replay: {name} must be a list or tuple")
    return tuple(value)


def _text(value: object, name: str) -> str:
    if type(value) is not str:
        raise ContractError(f"observation replay: {name} must be a string")
    return value


def _one_text(value: object, name: str) -> str:
    values = _sequence(value, name)
    if len(values) != 1:
        raise ContractError(f"observation replay: {name} must contain exactly one token")
    return _text(values[0], name)


def _validate_transport(provenance: object, version: int) -> None:
    packet_id = _one_text(_field(provenance, "observation_packet_ids"), "observation_packet_ids")
    source_version = _one_text(
        _field(provenance, "source_observation_versions"), "source_observation_versions"
    )
    if source_version == f"global:{version}":
        if packet_id in (f"obs:{version}", f"obs:facade:{version}"):
            return
    elif source_version == f"branch:{version}":
        if packet_id == f"obs:facade-native-branch:{version}":
            return
    else:
        matched = _SCOPED_VERSION.fullmatch(source_version)
        if matched is not None:
            scope, token_version = matched.groups()
            if token_version == str(version) and packet_id == f"obs:branch:{scope}:{version}":
                return
    raise ContractError(
        "observation replay: transport tokens do not match their local version/scope"
    )


def _values(
    value: object,
    *,
    float_fields: tuple[str, ...],
    uint64_fields: tuple[str, ...] = (),
    int_fields: tuple[str, ...] = (),
    bool_fields: tuple[str, ...] = (),
) -> dict[str, object]:
    result: dict[str, object] = {}
    for name in float_fields:
        result[name] = {"type": "f64", "hex": _float_hex(_field(value, name), name)}
    for name in uint64_fields:
        result[name] = {"type": "u64", "value": str(_uint64(_field(value, name), name))}
    for name in int_fields:
        item = _field(value, name)
        if type(item) is not int or not -(1 << 31) <= item < (1 << 31):
            raise ContractError(f"observation replay: {name} must be an int32")
        result[name] = {"type": "i32", "value": item}
    for name in bool_fields:
        item = _field(value, name)
        if type(item) is not bool:
            raise ContractError(f"observation replay: {name} must be a bool")
        result[name] = item
    return result


def observation_replay_digest(packet: object, ref: object, *, agent_id: str) -> str:
    """Validate and freeze one Agent's full observation projection as a digest.

    Scalars use their native declared types. Finite doubles are encoded with
    ``float.hex`` (including signed zero); uint64 ids use typed decimal strings
    so values beyond the experiment JSON exact-integer limit remain exact.
    Sensor ids and list order remain significant. Only the validated own id is
    replaced by the session Agent id. InstrumentState is outside this declared
    AgentObservation projection and is intentionally not compared.
    """
    if type(agent_id) is not str or _IDENTIFIER.fullmatch(agent_id) is None:
        raise ContractError("observation replay: agent_id must be a session identifier")
    refs = _sequence(_field(packet, "refs"), "refs")
    observations = _sequence(_field(packet, "agent_observations"), "agent_observations")
    if len(refs) != 1 or len(observations) != 1:
        raise ContractError(
            "observation replay: exactly one requested ref and observation required"
        )
    requested = (
        _uint64(_field(ref, "world_index"), "requested world_index"),
        _uint64(_field(ref, "entity_id"), "requested entity_id", nonzero=True),
    )
    actual = (
        _uint64(_field(refs[0], "world_index"), "packet world_index"),
        _uint64(_field(refs[0], "entity_id"), "packet entity_id", nonzero=True),
    )
    own_id = _uint64(_field(observations[0], "id"), "observation id", nonzero=True)
    if requested != actual or own_id != requested[1]:
        raise ContractError(
            "observation replay: packet ref/own id differs from requested Agent ref"
        )
    version = _uint64(_field(packet, "snapshot_version"), "snapshot_version", nonzero=True)
    if _text(_field(packet, "barrier_id"), "barrier_id") != "export":
        raise ContractError("observation replay: packet must be at the export barrier")
    source_time = _float_hex(_field(packet, "source_time_s"), "source_time_s")
    observation = observations[0]
    if source_time != _float_hex(_field(observation, "sim_time"), "sim_time"):
        raise ContractError("observation replay: source_time_s differs from observation sim_time")
    provenance = _field(packet, "provenance")
    semantics = {
        name: _text(_field(provenance, name), name)
        for name in (
            "information_state_layer",
            "source_label",
            "maintained_status",
            "diagnostics_reason",
        )
    }
    if (
        semantics["information_state_layer"] != "AgentObservation"
        or semantics["source_label"] != "facade_observation_packet"
        or semantics["maintained_status"] != "maintained"
    ):
        raise ContractError("observation replay: provenance is not maintained AgentObservation")
    _validate_transport(provenance, version)
    projected = _values(
        observation,
        float_fields=AGENT_OBSERVATION_FLOAT_FIELDS,
        int_fields=AGENT_OBSERVATION_INT_FIELDS,
        bool_fields=AGENT_OBSERVATION_BOOL_FIELDS,
    )
    projected["id"] = {"type": "session-agent", "value": agent_id}
    for name, floats, uints, ints, bools in (
        ("contacts", TRACK_FLOAT_FIELDS, TRACK_UINT64_FIELDS, TRACK_INT_FIELDS, TRACK_BOOL_FIELDS),
        ("rwr_warnings", RWR_FLOAT_FIELDS, RWR_UINT64_FIELDS, (), RWR_BOOL_FIELDS),
        ("esm_detections", ESM_FLOAT_FIELDS, ESM_UINT64_FIELDS, (), ESM_BOOL_FIELDS),
    ):
        projected[name] = [
            _values(
                item, float_fields=floats, uint64_fields=uints, int_fields=ints, bool_fields=bools
            )
            for item in _sequence(_field(observation, name), name)
        ]
    return content_digest(
        "experiment.observation-replay.v1",
        {
            "agent_id": agent_id,
            "barrier_id": "export",
            "source_time_s": {"type": "f64", "hex": source_time},
            "provenance": semantics,
            "observation": projected,
        },
    )


__all__ = [
    "observation_replay_digest",
    "OBSERVATION_REPLAY_FIELD_CATALOGUE",
    "OBSERVATION_PACKET_FIELDS",
    "OBSERVATION_PROVENANCE_FIELDS",
    "AGENT_OBSERVATION_FLOAT_FIELDS",
    "AGENT_OBSERVATION_UINT64_FIELDS",
    "AGENT_OBSERVATION_INT_FIELDS",
    "AGENT_OBSERVATION_BOOL_FIELDS",
    "AGENT_OBSERVATION_SEQUENCE_FIELDS",
    "TRACK_FLOAT_FIELDS",
    "TRACK_UINT64_FIELDS",
    "TRACK_INT_FIELDS",
    "TRACK_BOOL_FIELDS",
    "RWR_FLOAT_FIELDS",
    "RWR_UINT64_FIELDS",
    "RWR_BOOL_FIELDS",
    "ESM_FLOAT_FIELDS",
    "ESM_UINT64_FIELDS",
    "ESM_BOOL_FIELDS",
]
