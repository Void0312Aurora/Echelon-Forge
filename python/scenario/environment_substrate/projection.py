from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .manifest import (
    EnvironmentManifest,
    EnvironmentObject,
    EnvironmentProjectionProfile,
)
from .validation import validate_environment_manifest


@dataclass(frozen=True)
class ProjectedWorldZone:
    source_object_id: str
    name: str
    x: float
    y: float
    width: float
    length: float
    heading: float
    surface: str

    def to_metadata(self) -> dict[str, Any]:
        return {
            "source_object_id": self.source_object_id,
            "name": self.name,
            "x": float(self.x),
            "y": float(self.y),
            "width": float(self.width),
            "length": float(self.length),
            "heading": float(self.heading),
            "surface": self.surface,
        }


@dataclass(frozen=True)
class EnvironmentProjectionEvidence:
    profile_id: str
    target: str
    source_object_ids: tuple[str, ...]
    dropped_attributes: tuple[str, ...]
    simplification_method: str
    no_held_capability_release: bool = True

    def to_metadata(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "target": self.target,
            "source_object_ids": list(self.source_object_ids),
            "dropped_attributes": list(self.dropped_attributes),
            "simplification_method": self.simplification_method,
            "no_held_capability_release": bool(self.no_held_capability_release),
        }


@dataclass(frozen=True)
class EnvironmentProjectionResult:
    valid: bool
    fail_closed: bool
    rejection_reason: str
    errors: tuple[str, ...]
    zones: tuple[ProjectedWorldZone, ...] = ()
    evidence: EnvironmentProjectionEvidence | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "valid": bool(self.valid),
            "fail_closed": bool(self.fail_closed),
            "rejection_reason": self.rejection_reason,
            "errors": list(self.errors),
            "zones": [zone.to_metadata() for zone in self.zones],
            "evidence": self.evidence.to_metadata() if self.evidence else None,
        }


def _failure(reason: str, message: str) -> EnvironmentProjectionResult:
    return EnvironmentProjectionResult(
        valid=False,
        fail_closed=True,
        rejection_reason=reason,
        errors=(message,),
    )


def _find_profile(
    manifest: EnvironmentManifest,
    profile_id: str,
) -> EnvironmentProjectionProfile | None:
    for profile in manifest.projection_profiles:
        if profile.profile_id == profile_id:
            return profile
    return None


def _component_map(item: EnvironmentObject) -> dict[str, Any]:
    return {component.family: component for component in item.components}


def _has_projectable_branch(
    item: EnvironmentObject,
    profile: EnvironmentProjectionProfile,
) -> bool:
    if profile.branch_id:
        matching = [
            membership
            for membership in item.branch_membership
            if membership.branch_id == profile.branch_id
        ]
    else:
        matching = list(item.branch_membership)
    for membership in matching:
        if membership.role in ("primary", "projectable"):
            return True
        if profile.profile_id in membership.projection_profile_refs:
            return True
    return False


def _finite_float(value: Any) -> float | None:
    try:
        coerced = float(value)
    except Exception:
        return None
    if not math.isfinite(coerced):
        return None
    return coerced


def _rect_zone_from_object(
    item: EnvironmentObject,
    profile: EnvironmentProjectionProfile,
) -> ProjectedWorldZone | EnvironmentProjectionResult:
    if item.geometry.geometry_type not in profile.allowed_geometry_types:
        return _failure(
            "environment_substrate_unsupported_geometry",
            f"object {item.object_id} geometry {item.geometry.geometry_type!r} cannot project to {profile.target}",
        )
    coords = item.geometry.coordinates
    required_rect_keys = ("x", "y", "width", "length")
    rect_values: dict[str, float] = {}
    for key in required_rect_keys:
        value = _finite_float(coords.get(key))
        if value is None:
            return _failure(
                "environment_substrate_unsupported_geometry",
                f"object {item.object_id} missing finite rect coordinate {key!r}",
            )
        rect_values[key] = value
    if rect_values["width"] <= 0.0 or rect_values["length"] <= 0.0:
        return _failure(
            "environment_substrate_unsupported_geometry",
            f"object {item.object_id} width and length must be positive",
        )
    heading = _finite_float(coords.get("heading", 0.0))
    if heading is None:
        return _failure(
            "environment_substrate_unsupported_geometry",
            f"object {item.object_id} heading must be finite",
        )

    components = _component_map(item)
    missing = sorted(
        family for family in profile.required_components if family not in components
    )
    if missing:
        return _failure(
            "environment_substrate_projection_required_component_missing",
            f"object {item.object_id} is missing projection components {missing}",
        )
    extra_components = sorted(
        family for family in components.keys() if family not in profile.required_components
    )
    if extra_components and profile.dropped_attribute_policy != "record":
        return _failure(
            "environment_substrate_dropped_attribute_without_permission",
            f"object {item.object_id} would drop components {extra_components}",
        )

    surface_component = components.get("surface_material")
    if surface_component is None:
        return _failure(
            "environment_substrate_projection_required_component_missing",
            f"object {item.object_id} requires surface_material for zone projection",
        )
    if "surface_type" in surface_component.attributes and "surface" not in surface_component.attributes:
        return _failure(
            "environment_substrate_ambiguous_mapping",
            f"object {item.object_id} uses surface_type where surface is required",
        )
    surface = str(surface_component.attributes.get("surface", "")).strip()
    if not surface:
        return _failure(
            "environment_substrate_missing_required_component_attribute",
            f"object {item.object_id} surface_material.surface is required",
        )
    mapped_surface = profile.surface_code_mapping.get(surface)
    if not mapped_surface:
        return _failure(
            "environment_substrate_unknown_surface",
            f"object {item.object_id} surface {surface!r} is not mapped by profile {profile.profile_id}",
        )

    return ProjectedWorldZone(
        source_object_id=item.object_id,
        name=item.catalog_ref or item.object_id,
        x=rect_values["x"],
        y=rect_values["y"],
        width=rect_values["width"],
        length=rect_values["length"],
        heading=float(heading),
        surface=mapped_surface,
    )


def project_manifest_to_world_zone_projection(
    manifest: EnvironmentManifest,
    *,
    profile_id: str,
) -> EnvironmentProjectionResult:
    validation = validate_environment_manifest(manifest)
    if not validation.valid:
        return EnvironmentProjectionResult(
            valid=False,
            fail_closed=True,
            rejection_reason=validation.rejection_reason,
            errors=validation.errors,
        )

    profile = _find_profile(manifest, profile_id)
    if profile is None:
        return _failure(
            "environment_substrate_unknown_projection_profile",
            f"projection profile {profile_id!r} does not exist",
        )
    if profile.target != "world_zone_definition":
        return _failure(
            "environment_substrate_unsupported_target_field",
            f"G0-J projection contract supports only world_zone_definition, not {profile.target!r}",
        )

    zones: list[ProjectedWorldZone] = []
    dropped_attributes: set[str] = set()
    for item in manifest.objects:
        if profile.profile_id not in item.projection_profile_ids:
            continue
        if not _has_projectable_branch(item, profile):
            return _failure(
                "environment_substrate_illegal_branch_combination",
                f"object {item.object_id} is not projectable for {profile.profile_id}",
            )
        projected = _rect_zone_from_object(item, profile)
        if isinstance(projected, EnvironmentProjectionResult):
            return projected
        zones.append(projected)
        components = _component_map(item)
        for family in components.keys():
            if family not in profile.required_components:
                dropped_attributes.add(f"{item.object_id}:{family}")
        for key in item.properties.keys():
            dropped_attributes.add(f"{item.object_id}:properties.{key}")

    evidence = EnvironmentProjectionEvidence(
        profile_id=profile.profile_id,
        target=profile.target,
        source_object_ids=tuple(zone.source_object_id for zone in zones),
        dropped_attributes=tuple(sorted(dropped_attributes)),
        simplification_method=profile.geometry_simplification,
        no_held_capability_release=True,
    )
    return EnvironmentProjectionResult(
        valid=True,
        fail_closed=False,
        rejection_reason="",
        errors=(),
        zones=tuple(zones),
        evidence=evidence,
    )


__all__ = [
    "EnvironmentProjectionEvidence",
    "EnvironmentProjectionResult",
    "ProjectedWorldZone",
    "project_manifest_to_world_zone_projection",
]
