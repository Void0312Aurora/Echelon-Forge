from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterable

from .components import (
    ENVIRONMENT_SUBSTRATE_CONTRACT_VERSION,
    EnvironmentBranchDescriptor,
    EnvironmentComponentDescriptor,
    EnvironmentLayerDescriptor,
    default_branch_registry,
    default_component_registry,
    default_layer_registry,
)


def _clone(value: Any) -> Any:
    return deepcopy(value)


def _normalized_text(value: Any) -> str:
    return str(value or "").strip()


def _normalized_unique_texts(values: Iterable[Any]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        text = _normalized_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return tuple(sorted(normalized))


def _normalize_descriptor_tuple(
    values: Iterable[Any],
    descriptor_type: type,
) -> tuple[Any, ...]:
    normalized = []
    for value in values:
        if isinstance(value, descriptor_type):
            normalized.append(value)
        elif isinstance(value, dict):
            normalized.append(descriptor_type(**value))
        else:
            raise TypeError(
                f"registry entries must be {descriptor_type.__name__} or dict"
            )
    return tuple(normalized)


@dataclass(frozen=True)
class EnvironmentRegionExtent:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "min_x", float(self.min_x))
        object.__setattr__(self, "min_y", float(self.min_y))
        object.__setattr__(self, "max_x", float(self.max_x))
        object.__setattr__(self, "max_y", float(self.max_y))

    def to_metadata(self) -> dict[str, float]:
        return {
            "min_x": float(self.min_x),
            "min_y": float(self.min_y),
            "max_x": float(self.max_x),
            "max_y": float(self.max_y),
        }


@dataclass(frozen=True)
class EnvironmentGenerationMetadata:
    generator_id: str
    generator_version: str
    deterministic_seed: int
    source_inputs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "generator_id", _normalized_text(self.generator_id))
        object.__setattr__(
            self,
            "generator_version",
            _normalized_text(self.generator_version),
        )
        object.__setattr__(
            self,
            "deterministic_seed",
            int(self.deterministic_seed),
        )
        object.__setattr__(
            self,
            "source_inputs",
            _normalized_unique_texts(self.source_inputs),
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "generator_id": self.generator_id,
            "generator_version": self.generator_version,
            "deterministic_seed": int(self.deterministic_seed),
            "source_inputs": list(self.source_inputs),
        }


@dataclass(frozen=True)
class EnvironmentBranchMembership:
    branch_id: str
    role: str
    component_refs: tuple[str, ...] = ()
    projection_profile_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch_id", _normalized_text(self.branch_id))
        object.__setattr__(self, "role", _normalized_text(self.role))
        object.__setattr__(
            self,
            "component_refs",
            _normalized_unique_texts(self.component_refs),
        )
        object.__setattr__(
            self,
            "projection_profile_refs",
            _normalized_unique_texts(self.projection_profile_refs),
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "role": self.role,
            "component_refs": list(self.component_refs),
            "projection_profile_refs": list(self.projection_profile_refs),
        }


@dataclass(frozen=True)
class EnvironmentGeometry:
    geometry_type: str
    coordinates: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "geometry_type", _normalized_text(self.geometry_type))
        object.__setattr__(self, "coordinates", _clone(self.coordinates))

    def to_metadata(self) -> dict[str, Any]:
        return {
            "geometry_type": self.geometry_type,
            "coordinates": _clone(self.coordinates),
        }


@dataclass(frozen=True)
class EnvironmentComponent:
    component_id: str
    family: str
    attributes: dict[str, Any]
    schema_version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "component_id", _normalized_text(self.component_id))
        object.__setattr__(self, "family", _normalized_text(self.family))
        object.__setattr__(self, "schema_version", _normalized_text(self.schema_version))
        object.__setattr__(self, "attributes", _clone(self.attributes))

    def to_metadata(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "family": self.family,
            "schema_version": self.schema_version,
            "attributes": _clone(self.attributes),
        }


@dataclass(frozen=True)
class EnvironmentProjectionProfile:
    profile_id: str
    target: str
    branch_id: str = ""
    allowed_geometry_types: tuple[str, ...] = ()
    required_components: tuple[str, ...] = ()
    surface_code_mapping: dict[str, str] = field(default_factory=dict)
    geometry_simplification: str = "none"
    dropped_attribute_policy: str = "reject"

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", _normalized_text(self.profile_id))
        object.__setattr__(self, "target", _normalized_text(self.target))
        object.__setattr__(self, "branch_id", _normalized_text(self.branch_id))
        object.__setattr__(
            self,
            "allowed_geometry_types",
            _normalized_unique_texts(self.allowed_geometry_types),
        )
        object.__setattr__(
            self,
            "required_components",
            _normalized_unique_texts(self.required_components),
        )
        mapping = {
            _normalized_text(key): _normalized_text(value)
            for key, value in dict(self.surface_code_mapping).items()
            if _normalized_text(key) and _normalized_text(value)
        }
        object.__setattr__(self, "surface_code_mapping", dict(sorted(mapping.items())))
        object.__setattr__(
            self,
            "geometry_simplification",
            _normalized_text(self.geometry_simplification),
        )
        object.__setattr__(
            self,
            "dropped_attribute_policy",
            _normalized_text(self.dropped_attribute_policy),
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "target": self.target,
            "branch_id": self.branch_id,
            "allowed_geometry_types": list(self.allowed_geometry_types),
            "required_components": list(self.required_components),
            "surface_code_mapping": dict(self.surface_code_mapping),
            "geometry_simplification": self.geometry_simplification,
            "dropped_attribute_policy": self.dropped_attribute_policy,
        }


@dataclass(frozen=True)
class EnvironmentObject:
    object_id: str
    catalog_ref: str
    geometry: EnvironmentGeometry
    branch_membership: tuple[EnvironmentBranchMembership, ...]
    components: tuple[EnvironmentComponent, ...]
    layer_membership: tuple[str, ...] = ()
    projection_profile_ids: tuple[str, ...] = ()
    properties: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "object_id", _normalized_text(self.object_id))
        object.__setattr__(self, "catalog_ref", _normalized_text(self.catalog_ref))
        geometry = self.geometry
        if isinstance(geometry, dict):
            geometry = EnvironmentGeometry(**geometry)
        if not isinstance(geometry, EnvironmentGeometry):
            raise TypeError("geometry must be EnvironmentGeometry or dict")
        object.__setattr__(self, "geometry", geometry)
        memberships = []
        for membership in self.branch_membership:
            if isinstance(membership, EnvironmentBranchMembership):
                memberships.append(membership)
            elif isinstance(membership, dict):
                memberships.append(EnvironmentBranchMembership(**membership))
            else:
                raise TypeError("branch_membership entries must be membership objects or dict")
        object.__setattr__(self, "branch_membership", tuple(memberships))
        components = []
        for component in self.components:
            if isinstance(component, EnvironmentComponent):
                components.append(component)
            elif isinstance(component, dict):
                components.append(EnvironmentComponent(**component))
            else:
                raise TypeError("components entries must be EnvironmentComponent or dict")
        object.__setattr__(self, "components", tuple(components))
        object.__setattr__(
            self,
            "layer_membership",
            _normalized_unique_texts(self.layer_membership),
        )
        object.__setattr__(
            self,
            "projection_profile_ids",
            _normalized_unique_texts(self.projection_profile_ids),
        )
        object.__setattr__(self, "properties", _clone(self.properties))
        object.__setattr__(self, "provenance", _clone(self.provenance))

    def to_metadata(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "catalog_ref": self.catalog_ref,
            "geometry": self.geometry.to_metadata(),
            "branch_membership": [
                membership.to_metadata() for membership in self.branch_membership
            ],
            "components": [component.to_metadata() for component in self.components],
            "layer_membership": list(self.layer_membership),
            "projection_profile_ids": list(self.projection_profile_ids),
            "properties": _clone(self.properties),
            "provenance": _clone(self.provenance),
        }


@dataclass(frozen=True)
class EnvironmentManifest:
    manifest_id: str
    schema_version: str
    coordinate_frame: str
    region_extent: EnvironmentRegionExtent
    generation: EnvironmentGenerationMetadata
    objects: tuple[EnvironmentObject, ...]
    branch_registry: tuple[EnvironmentBranchDescriptor, ...] = field(
        default_factory=default_branch_registry
    )
    component_registry: tuple[EnvironmentComponentDescriptor, ...] = field(
        default_factory=default_component_registry
    )
    layer_registry: tuple[EnvironmentLayerDescriptor, ...] = field(
        default_factory=default_layer_registry
    )
    projection_profiles: tuple[EnvironmentProjectionProfile, ...] = ()
    catalogs: tuple[str, ...] = ()
    relationships: tuple[dict[str, Any], ...] = ()
    validation_evidence: tuple[dict[str, Any], ...] = ()
    capability_claims: tuple[str, ...] = ()
    contract_version: str = ENVIRONMENT_SUBSTRATE_CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "manifest_id", _normalized_text(self.manifest_id))
        object.__setattr__(self, "schema_version", _normalized_text(self.schema_version))
        object.__setattr__(
            self,
            "coordinate_frame",
            _normalized_text(self.coordinate_frame),
        )
        extent = self.region_extent
        if isinstance(extent, dict):
            extent = EnvironmentRegionExtent(**extent)
        if not isinstance(extent, EnvironmentRegionExtent):
            raise TypeError("region_extent must be EnvironmentRegionExtent or dict")
        object.__setattr__(self, "region_extent", extent)
        generation = self.generation
        if isinstance(generation, dict):
            generation = EnvironmentGenerationMetadata(**generation)
        if not isinstance(generation, EnvironmentGenerationMetadata):
            raise TypeError("generation must be EnvironmentGenerationMetadata or dict")
        object.__setattr__(self, "generation", generation)
        object.__setattr__(
            self,
            "branch_registry",
            _normalize_descriptor_tuple(
                self.branch_registry,
                EnvironmentBranchDescriptor,
            ),
        )
        object.__setattr__(
            self,
            "component_registry",
            _normalize_descriptor_tuple(
                self.component_registry,
                EnvironmentComponentDescriptor,
            ),
        )
        object.__setattr__(
            self,
            "layer_registry",
            _normalize_descriptor_tuple(
                self.layer_registry,
                EnvironmentLayerDescriptor,
            ),
        )
        objects = []
        for item in self.objects:
            if isinstance(item, EnvironmentObject):
                objects.append(item)
            elif isinstance(item, dict):
                objects.append(EnvironmentObject(**item))
            else:
                raise TypeError("objects entries must be EnvironmentObject or dict")
        object.__setattr__(self, "objects", tuple(objects))
        profiles = []
        for profile in self.projection_profiles:
            if isinstance(profile, EnvironmentProjectionProfile):
                profiles.append(profile)
            elif isinstance(profile, dict):
                profiles.append(EnvironmentProjectionProfile(**profile))
            else:
                raise TypeError(
                    "projection_profiles entries must be EnvironmentProjectionProfile or dict"
                )
        object.__setattr__(self, "projection_profiles", tuple(profiles))
        object.__setattr__(self, "catalogs", _normalized_unique_texts(self.catalogs))
        object.__setattr__(
            self,
            "relationships",
            tuple(_clone(relationship) for relationship in self.relationships),
        )
        object.__setattr__(
            self,
            "validation_evidence",
            tuple(_clone(evidence) for evidence in self.validation_evidence),
        )
        object.__setattr__(
            self,
            "capability_claims",
            _normalized_unique_texts(self.capability_claims),
        )
        object.__setattr__(self, "contract_version", _normalized_text(self.contract_version))

    def to_metadata(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
            "coordinate_frame": self.coordinate_frame,
            "region_extent": self.region_extent.to_metadata(),
            "branch_registry": [
                branch.to_metadata() for branch in self.branch_registry
            ],
            "component_registry": [
                component.to_metadata() for component in self.component_registry
            ],
            "layer_registry": [layer.to_metadata() for layer in self.layer_registry],
            "generation": self.generation.to_metadata(),
            "catalogs": list(self.catalogs),
            "objects": [item.to_metadata() for item in self.objects],
            "relationships": [_clone(relationship) for relationship in self.relationships],
            "projection_profiles": [
                profile.to_metadata() for profile in self.projection_profiles
            ],
            "validation_evidence": [
                _clone(evidence) for evidence in self.validation_evidence
            ],
            "capability_claims": list(self.capability_claims),
        }


def build_deterministic_environment_fixture() -> EnvironmentManifest:
    projection_profile = EnvironmentProjectionProfile(
        profile_id="terrain-rect-surface-v1",
        target="world_zone_definition",
        branch_id="terrain",
        allowed_geometry_types=("rect",),
        required_components=("surface_material",),
        surface_code_mapping={
            "Asphalt": "Asphalt",
            "Concrete": "Concrete",
            "HardPacked": "HardPacked",
            "SoftDirt": "SoftDirt",
            "Water": "Water",
        },
        geometry_simplification="rectangle_only",
        dropped_attribute_policy="reject",
    )
    hardstand = EnvironmentObject(
        object_id="envobj:test-hardstand",
        catalog_ref="catalog:port_hardstand",
        geometry=EnvironmentGeometry(
            geometry_type="rect",
            coordinates={
                "x": 250.0,
                "y": -125.0,
                "width": 80.0,
                "length": 140.0,
                "heading": 15.0,
            },
        ),
        branch_membership=(
            EnvironmentBranchMembership(
                branch_id="terrain",
                role="projectable",
                projection_profile_refs=("terrain-rect-surface-v1",),
            ),
        ),
        layer_membership=("terrain_surface", "infrastructure_network"),
        components=(
            EnvironmentComponent(
                component_id="component:test-hardstand-surface",
                family="surface_material",
                attributes={"surface": "Concrete", "roughness": 0.1},
            ),
        ),
        projection_profile_ids=("terrain-rect-surface-v1",),
        provenance={"source": "deterministic_g0_j_fixture"},
    )
    village = EnvironmentObject(
        object_id="envobj:test-village-house",
        catalog_ref="catalog:village_house_light",
        geometry=EnvironmentGeometry(
            geometry_type="polygon",
            coordinates={
                "points": [
                    [300.0, 300.0],
                    [312.0, 300.0],
                    [312.0, 310.0],
                    [300.0, 310.0],
                ]
            },
        ),
        branch_membership=(
            EnvironmentBranchMembership(branch_id="terrain", role="metadata_only"),
        ),
        layer_membership=("built_structure",),
        components=(
            EnvironmentComponent(
                component_id="component:test-house-structure",
                family="structure",
                attributes={
                    "footprint": "polygon",
                    "height_m": 5.5,
                    "material": "brick",
                },
            ),
        ),
        provenance={"source": "deterministic_g0_j_fixture"},
    )
    return EnvironmentManifest(
        manifest_id="envmanifest:g0-j-static-fixture",
        schema_version="1",
        coordinate_frame="local_enu_m",
        region_extent=EnvironmentRegionExtent(-1000.0, -1000.0, 1000.0, 1000.0),
        generation=EnvironmentGenerationMetadata(
            generator_id="manual_static_fixture",
            generator_version="g0-j.20260605",
            deterministic_seed=20260605,
            source_inputs=("docs/systems/environment/reviews/environment_substrate_g0_closure_20260606",),
        ),
        catalogs=("catalog:port_hardstand", "catalog:village_house_light"),
        objects=(hardstand, village),
        projection_profiles=(projection_profile,),
    )


__all__ = [
    "EnvironmentBranchMembership",
    "EnvironmentComponent",
    "EnvironmentGenerationMetadata",
    "EnvironmentGeometry",
    "EnvironmentManifest",
    "EnvironmentObject",
    "EnvironmentProjectionProfile",
    "EnvironmentRegionExtent",
    "build_deterministic_environment_fixture",
]
