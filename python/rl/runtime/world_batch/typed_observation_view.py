"""Admission contract for the I87 typed observation data-flow pilot.

The pilot is deliberately bounded to the standard world-batch execution-
observation builder.  It consumes the T1-generated ``ObservationViewSpec``
export before reading the existing typed ``ObservationBatchPacket`` payload;
it does not change the TL13 loader seam or the default observation path.

``required_fields == []`` and ``optional_fields == []`` have one narrow meaning
in this pilot: the export is *structural-only*.  The field catalogue is
unspecified here and remains owned by the existing observation implementation.
Empty lists are therefore neither a wildcard nor a claim that the observation
has zero fields.  The pilot performs no field filtering and makes no
field-level checkpoint compatibility promise.  A future non-empty catalogue
fails closed until an explicit catalogue owner and projection rule land.
"""

from __future__ import annotations

from typing import Any


MAINTAINED_VIEW_ID = "gym_envs.observation_view"
MAINTAINED_SCHEMA_MAJOR = 1
MAINTAINED_PRODUCED_LAYERS = ("Agent Observation",)
MAINTAINED_CONSUMED_LAYERS = (
    "World Truth",
    "Track State",
    "Shared Tactical Picture",
)
MAINTAINED_SEMANTIC_STAGES = ("P10 ObservationExport",)


def _schema_major(version: Any) -> int | None:
    text = str(version)
    major_text, separator, minor_text = text.partition(".")
    if not separator or not major_text.isdecimal() or not minor_text.isdecimal():
        return None
    return int(major_text)


def typed_observation_view_admission_violations(spec: Any) -> list[str]:
    """Return fail-closed admission violations for one runtime-exported spec."""

    violations: list[str] = []
    if spec is None:
        return ["typed observation view spec is missing"]

    schema_version = getattr(spec, "schema_version", None)
    schema_major = _schema_major(schema_version)
    if schema_major != MAINTAINED_SCHEMA_MAJOR:
        violations.append(
            "schema_version must be a valid 1.x version for the I87 pilot, "
            f"got {schema_version!r}"
        )

    view_id = str(getattr(spec, "view_id", ""))
    if view_id != MAINTAINED_VIEW_ID:
        violations.append(
            f"view_id must be {MAINTAINED_VIEW_ID!r}, got {view_id!r}"
        )

    produced = tuple(getattr(spec, "information_layer_produced", ()) or ())
    if produced != MAINTAINED_PRODUCED_LAYERS:
        violations.append(
            "information_layer_produced must be exactly "
            f"{MAINTAINED_PRODUCED_LAYERS!r}, got {produced!r}"
        )

    consumed = tuple(getattr(spec, "information_layer_consumed", ()) or ())
    if consumed != MAINTAINED_CONSUMED_LAYERS:
        violations.append(
            "information_layer_consumed must be exactly "
            f"{MAINTAINED_CONSUMED_LAYERS!r}, got {consumed!r}"
        )

    stages = tuple(getattr(spec, "semantic_stage", ()) or ())
    if stages != MAINTAINED_SEMANTIC_STAGES:
        violations.append(
            f"semantic_stage must be exactly {MAINTAINED_SEMANTIC_STAGES!r}, "
            f"got {stages!r}"
        )

    required_fields = tuple(getattr(spec, "required_fields", ()) or ())
    optional_fields = tuple(getattr(spec, "optional_fields", ()) or ())
    if required_fields:
        violations.append(
            "required_fields must stay empty in the structural-only I87 pilot; "
            "a non-empty catalogue needs an explicit owner and projection rule"
        )
    if optional_fields:
        violations.append(
            "optional_fields must stay empty in the structural-only I87 pilot; "
            "a non-empty catalogue needs an explicit owner and projection rule"
        )
    return violations


def admit_typed_observation_view_spec(spec: Any) -> Any:
    """Return ``spec`` after admission, or raise before payload consumption."""

    violations = typed_observation_view_admission_violations(spec)
    if violations:
        raise RuntimeError(
            "typed observation view admission failed: " + "; ".join(violations)
        )
    return spec


__all__ = [
    "MAINTAINED_CONSUMED_LAYERS",
    "MAINTAINED_PRODUCED_LAYERS",
    "MAINTAINED_SCHEMA_MAJOR",
    "MAINTAINED_SEMANTIC_STAGES",
    "MAINTAINED_VIEW_ID",
    "admit_typed_observation_view_spec",
    "typed_observation_view_admission_violations",
]
