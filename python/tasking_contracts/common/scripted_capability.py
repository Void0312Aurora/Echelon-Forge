"""Validation for additive scripted-capability scenario metadata.

The manifest describes evidence posture; it is not a runtime capability grant.
Domain runtimes, scenario loading, and report generation remain owners of their
respective behavior and evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


SCRIPTED_CAPABILITY_VERSION = "scripted_capability.v1"
SCRIPTED_CAPABILITY_LABELS = frozenset(
    {"held", "bounded_adapter", "playable_candidate", "playable"}
)
SCRIPTED_CAPABILITY_LIFECYCLES = frozenset({"reset_decide_close", "task_status_shell"})


@dataclass(frozen=True)
class ScriptedCapabilityManifest:
    version: str
    domain: str
    label: str
    model_id: str | None
    role_id: str
    lifecycle: str
    evidence_refs: tuple[str, ...]
    deferred_claims: tuple[str, ...]

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ScriptedCapabilityManifest":
        if not isinstance(raw, Mapping):
            raise TypeError("scripted capability manifest must be a mapping")
        version = str(raw.get("version", "")).strip()
        if version != SCRIPTED_CAPABILITY_VERSION:
            raise ValueError(f"unsupported scripted capability version: {version!r}")
        domain = str(raw.get("domain", "")).strip().lower()
        if not domain:
            raise ValueError("scripted capability domain must be non-empty")
        label = str(raw.get("label", "")).strip().lower()
        if label not in SCRIPTED_CAPABILITY_LABELS:
            raise ValueError(f"unknown scripted capability label: {label!r}")
        model_raw = raw.get("model_id")
        model_id = None if model_raw is None else str(model_raw).strip()
        if label != "held" and not model_id:
            raise ValueError("non-held scripted capability requires model_id")
        role_id = str(raw.get("role_id", "")).strip()
        if not role_id:
            raise ValueError("scripted capability role_id must be non-empty")
        lifecycle = str(raw.get("lifecycle", "")).strip()
        if lifecycle not in SCRIPTED_CAPABILITY_LIFECYCLES:
            raise ValueError(f"unknown scripted capability lifecycle: {lifecycle!r}")
        evidence_refs = _string_tuple(raw.get("evidence_refs"), "evidence_refs")
        if not evidence_refs:
            raise ValueError("scripted capability evidence_refs must be non-empty")
        deferred_claims = _string_tuple(raw.get("deferred_claims"), "deferred_claims")
        return cls(
            version=version,
            domain=domain,
            label=label,
            model_id=model_id,
            role_id=role_id,
            lifecycle=lifecycle,
            evidence_refs=evidence_refs,
            deferred_claims=deferred_claims,
        )


def _string_tuple(raw: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(raw, (list, tuple)):
        raise TypeError(f"scripted capability {field_name} must be a list")
    values = tuple(str(value).strip() for value in raw)
    if any(not value for value in values):
        raise ValueError(f"scripted capability {field_name} cannot contain blank values")
    return values


def parse_scripted_capability(raw_scenario: Mapping[str, Any]) -> ScriptedCapabilityManifest:
    if not isinstance(raw_scenario, Mapping):
        raise TypeError("scenario must be a mapping")
    raw_manifest = raw_scenario.get("scripted_capability")
    if not isinstance(raw_manifest, Mapping):
        raise ValueError("scenario is missing scripted_capability manifest")
    return ScriptedCapabilityManifest.from_mapping(raw_manifest)


def resolve_scripted_model_id(
    manifest: ScriptedCapabilityManifest,
    *,
    expected_domain: str,
    expected_role_id: str,
) -> str:
    """Validate a runtime consumer against a scenario capability declaration.

    The manifest remains evidence metadata; this helper only prevents a
    consumer from silently selecting a model for the wrong domain, role, or
    lifecycle. A ``held`` capability is never admissible to a runtime model
    entry point.
    """

    if not isinstance(manifest, ScriptedCapabilityManifest):
        raise TypeError("manifest must be a ScriptedCapabilityManifest")
    domain = str(expected_domain).strip().lower()
    role_id = str(expected_role_id).strip()
    if manifest.domain != domain:
        raise ValueError(
            f"scripted capability domain {manifest.domain!r} does not match {domain!r}"
        )
    if manifest.role_id != role_id:
        raise ValueError(
            f"scripted capability role {manifest.role_id!r} does not match {role_id!r}"
        )
    if manifest.label == "held":
        raise ValueError("held scripted capability cannot be routed to a runtime model")
    if manifest.lifecycle != "reset_decide_close":
        raise ValueError(
            "runtime scripted capability requires reset_decide_close lifecycle"
        )
    if not manifest.model_id:
        raise ValueError("runtime scripted capability requires model_id")
    return manifest.model_id


__all__ = [
    "SCRIPTED_CAPABILITY_LABELS",
    "SCRIPTED_CAPABILITY_LIFECYCLES",
    "SCRIPTED_CAPABILITY_VERSION",
    "ScriptedCapabilityManifest",
    "parse_scripted_capability",
    "resolve_scripted_model_id",
]
