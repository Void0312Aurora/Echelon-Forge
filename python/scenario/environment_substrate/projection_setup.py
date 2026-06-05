from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .manifest import EnvironmentManifest
from .projection import project_manifest_to_compatibility_setup


ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_CONTRACT_VERSION = (
    "environment_substrate.g0_l.projection_setup.v1"
)

WORLD_ZONE_DEFINITION_SURFACE_CODES = (
    "Asphalt",
    "Concrete",
    "HardPacked",
    "Obstacle",
    "SoftDirt",
    "Water",
)


def _clone(value: Any) -> Any:
    return deepcopy(value)


@dataclass(frozen=True)
class EnvironmentProjectionSetupPayload:
    manifest_id: str
    profile_id: str
    target: str
    zones: tuple[dict[str, Any], ...]
    zone_evidence: tuple[dict[str, Any], ...]
    projection_evidence: dict[str, Any]
    contract_version: str = ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_CONTRACT_VERSION
    no_held_capability_release: bool = True

    def to_metadata(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "manifest_id": self.manifest_id,
            "profile_id": self.profile_id,
            "target": self.target,
            "zones": [_clone(zone) for zone in self.zones],
            "zone_evidence": [_clone(evidence) for evidence in self.zone_evidence],
            "projection_evidence": _clone(self.projection_evidence),
            "no_held_capability_release": bool(self.no_held_capability_release),
        }


@dataclass(frozen=True)
class EnvironmentProjectionSetupResult:
    valid: bool
    fail_closed: bool
    rejection_reason: str
    errors: tuple[str, ...]
    payload: EnvironmentProjectionSetupPayload | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "valid": bool(self.valid),
            "fail_closed": bool(self.fail_closed),
            "rejection_reason": self.rejection_reason,
            "errors": list(self.errors),
            "payload": self.payload.to_metadata() if self.payload else None,
        }


def _failure(reason: str, message: str) -> EnvironmentProjectionSetupResult:
    return EnvironmentProjectionSetupResult(
        valid=False,
        fail_closed=True,
        rejection_reason=reason,
        errors=(message,),
    )


def build_world_zone_projection_setup_payload(
    manifest: EnvironmentManifest,
    *,
    profile_id: str,
) -> EnvironmentProjectionSetupResult:
    projection = project_manifest_to_compatibility_setup(
        manifest,
        profile_id=profile_id,
    )
    if not projection.valid:
        return EnvironmentProjectionSetupResult(
            valid=False,
            fail_closed=True,
            rejection_reason=projection.rejection_reason,
            errors=projection.errors,
        )
    if projection.evidence is None or not projection.evidence.no_held_capability_release:
        return _failure(
            "environment_substrate_projection_evidence_required",
            "projection setup payload requires no-held-capability evidence",
        )
    if projection.evidence.target != "world_zone_definition":
        return _failure(
            "environment_substrate_projection_target_not_accepted",
            f"projection setup payload does not accept {projection.evidence.target!r}",
        )
    if projection.evidence.dropped_attributes:
        return _failure(
            "environment_substrate_projection_derived_product_forbidden",
            "projection setup payload accepts surface-only zones with no dropped rich attributes",
        )

    object_map = {item.object_id: item for item in manifest.objects}
    projected_source_ids = tuple(zone.source_object_id for zone in projection.zones)
    if tuple(projection.evidence.source_object_ids) != projected_source_ids:
        return _failure(
            "environment_substrate_projection_evidence_required",
            "projection source object evidence must match projected zones",
        )

    zones: list[dict[str, Any]] = []
    zone_evidence: list[dict[str, Any]] = []
    for zone in projection.zones:
        if zone.surface not in WORLD_ZONE_DEFINITION_SURFACE_CODES:
            return _failure(
                "environment_substrate_projection_invalid_surface_code",
                f"surface {zone.surface!r} is not an accepted world zone surface code",
            )
        source_object = object_map.get(zone.source_object_id)
        if source_object is None:
            return _failure(
                "environment_substrate_projection_provenance_required",
                f"source object {zone.source_object_id!r} is not present in manifest",
            )
        zones.append(
            {
                "name": zone.name,
                "x": float(zone.x),
                "y": float(zone.y),
                "width": float(zone.width),
                "length": float(zone.length),
                "heading": float(zone.heading),
                "surface": zone.surface,
            }
        )
        zone_evidence.append(
            {
                "source_manifest_id": manifest.manifest_id,
                "source_object_id": source_object.object_id,
                "catalog_ref": source_object.catalog_ref,
                "profile_id": projection.evidence.profile_id,
                "target": projection.evidence.target,
                "branch_membership": [
                    membership.to_metadata()
                    for membership in source_object.branch_membership
                ],
                "layer_membership": list(source_object.layer_membership),
                "component_ids": [
                    component.component_id for component in source_object.components
                ],
                "object_provenance": _clone(source_object.provenance),
                "no_held_capability_release": True,
            }
        )

    payload = EnvironmentProjectionSetupPayload(
        manifest_id=manifest.manifest_id,
        profile_id=projection.evidence.profile_id,
        target=projection.evidence.target,
        zones=tuple(zones),
        zone_evidence=tuple(zone_evidence),
        projection_evidence=projection.evidence.to_metadata(),
    )
    return EnvironmentProjectionSetupResult(
        valid=True,
        fail_closed=False,
        rejection_reason="",
        errors=(),
        payload=payload,
    )


__all__ = [
    "ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_CONTRACT_VERSION",
    "WORLD_ZONE_DEFINITION_SURFACE_CODES",
    "EnvironmentProjectionSetupPayload",
    "EnvironmentProjectionSetupResult",
    "build_world_zone_projection_setup_payload",
]
