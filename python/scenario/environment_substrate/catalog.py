from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterable

from .components import (
    BRANCH_MEMBERSHIP_ROLES,
    DROPPED_ATTRIBUTE_POLICIES,
    HELD_CAPABILITY_CLAIMS,
    EnvironmentBranchDescriptor,
    EnvironmentComponentDescriptor,
    EnvironmentLayerDescriptor,
    default_branch_registry,
    default_component_registry,
    default_layer_registry,
)
from .manifest import (
    EnvironmentBranchMembership,
    EnvironmentComponent,
    EnvironmentManifest,
)


ENVIRONMENT_SUBSTRATE_CATALOG_CONTRACT_VERSION = "environment_substrate.g0_k.catalog.v1"

DEFAULT_CATALOG_PROVENANCE_REQUIREMENTS = (
    "catalog_id",
    "catalog_schema_version",
    "generator_id",
    "generator_version",
    "request_id",
    "source_inputs",
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


def _ids_are_unique(ids: list[str]) -> bool:
    return len(ids) == len(set(ids))


def _provenance_value_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (tuple, list, dict, set)):
        return bool(value)
    return True


@dataclass(frozen=True)
class EnvironmentCatalogDescriptor:
    catalog_id: str
    schema_version: str
    branch_membership: tuple[EnvironmentBranchMembership, ...]
    layer_membership: tuple[str, ...]
    geometry_types: tuple[str, ...]
    required_components: tuple[str, ...]
    component_templates: tuple[EnvironmentComponent, ...]
    optional_components: tuple[str, ...] = ()
    minimum_realism_grade: str = "G1"
    consumer_tags: tuple[str, ...] = ()
    projection_profile_refs: tuple[str, ...] = ()
    dropped_attribute_policy: str = "reject"
    provenance_requirements: tuple[str, ...] = DEFAULT_CATALOG_PROVENANCE_REQUIREMENTS
    forbidden_capability_claims: tuple[str, ...] = HELD_CAPABILITY_CLAIMS
    capability_claims: tuple[str, ...] = ()
    schema_root_kind: str = "catalog_recipe"

    def __post_init__(self) -> None:
        object.__setattr__(self, "catalog_id", _normalized_text(self.catalog_id))
        object.__setattr__(self, "schema_version", _normalized_text(self.schema_version))
        memberships = []
        for membership in self.branch_membership:
            if isinstance(membership, EnvironmentBranchMembership):
                memberships.append(membership)
            elif isinstance(membership, dict):
                memberships.append(EnvironmentBranchMembership(**membership))
            else:
                raise TypeError(
                    "branch_membership entries must be EnvironmentBranchMembership or dict"
                )
        object.__setattr__(self, "branch_membership", tuple(memberships))
        object.__setattr__(
            self,
            "layer_membership",
            _normalized_unique_texts(self.layer_membership),
        )
        object.__setattr__(
            self,
            "geometry_types",
            _normalized_unique_texts(self.geometry_types),
        )
        object.__setattr__(
            self,
            "required_components",
            _normalized_unique_texts(self.required_components),
        )
        templates = []
        for component in self.component_templates:
            if isinstance(component, EnvironmentComponent):
                templates.append(component)
            elif isinstance(component, dict):
                templates.append(EnvironmentComponent(**component))
            else:
                raise TypeError("component_templates entries must be EnvironmentComponent or dict")
        object.__setattr__(self, "component_templates", tuple(templates))
        object.__setattr__(
            self,
            "optional_components",
            _normalized_unique_texts(self.optional_components),
        )
        object.__setattr__(
            self,
            "minimum_realism_grade",
            _normalized_text(self.minimum_realism_grade),
        )
        object.__setattr__(
            self,
            "consumer_tags",
            _normalized_unique_texts(self.consumer_tags),
        )
        object.__setattr__(
            self,
            "projection_profile_refs",
            _normalized_unique_texts(self.projection_profile_refs),
        )
        object.__setattr__(
            self,
            "dropped_attribute_policy",
            _normalized_text(self.dropped_attribute_policy),
        )
        object.__setattr__(
            self,
            "provenance_requirements",
            _normalized_unique_texts(self.provenance_requirements),
        )
        object.__setattr__(
            self,
            "forbidden_capability_claims",
            _normalized_unique_texts(self.forbidden_capability_claims),
        )
        object.__setattr__(
            self,
            "capability_claims",
            _normalized_unique_texts(self.capability_claims),
        )
        object.__setattr__(
            self,
            "schema_root_kind",
            _normalized_text(self.schema_root_kind),
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "schema_version": self.schema_version,
            "contract_version": ENVIRONMENT_SUBSTRATE_CATALOG_CONTRACT_VERSION,
            "schema_root_kind": self.schema_root_kind,
            "branch_membership": [
                membership.to_metadata() for membership in self.branch_membership
            ],
            "layer_membership": list(self.layer_membership),
            "geometry_types": list(self.geometry_types),
            "required_components": list(self.required_components),
            "optional_components": list(self.optional_components),
            "component_templates": [
                component.to_metadata() for component in self.component_templates
            ],
            "minimum_realism_grade": self.minimum_realism_grade,
            "consumer_tags": list(self.consumer_tags),
            "projection_profile_refs": list(self.projection_profile_refs),
            "dropped_attribute_policy": self.dropped_attribute_policy,
            "provenance_requirements": list(self.provenance_requirements),
            "forbidden_capability_claims": list(self.forbidden_capability_claims),
            "capability_claims": list(self.capability_claims),
        }


@dataclass(frozen=True)
class EnvironmentCatalogValidationResult:
    valid: bool
    fail_closed: bool
    rejection_reason: str
    errors: tuple[str, ...]


def _first_failure(failures: list[tuple[str, str]]) -> EnvironmentCatalogValidationResult:
    if not failures:
        return EnvironmentCatalogValidationResult(
            valid=True,
            fail_closed=False,
            rejection_reason="",
            errors=(),
        )
    return EnvironmentCatalogValidationResult(
        valid=False,
        fail_closed=True,
        rejection_reason=failures[0][0],
        errors=tuple(message for _, message in failures),
    )


def _descriptor_maps(
    branch_registry: Iterable[EnvironmentBranchDescriptor] | None,
    component_registry: Iterable[EnvironmentComponentDescriptor] | None,
    layer_registry: Iterable[EnvironmentLayerDescriptor] | None,
) -> tuple[
    dict[str, EnvironmentBranchDescriptor],
    dict[str, EnvironmentComponentDescriptor],
    dict[str, EnvironmentLayerDescriptor],
]:
    branches = tuple(branch_registry or default_branch_registry())
    components = tuple(component_registry or default_component_registry())
    layers = tuple(layer_registry or default_layer_registry())
    return (
        {branch.branch_id: branch for branch in branches},
        {component.family: component for component in components},
        {layer.layer_id: layer for layer in layers},
    )


def validate_environment_catalog_descriptors(
    catalogs: Iterable[EnvironmentCatalogDescriptor],
    *,
    branch_registry: Iterable[EnvironmentBranchDescriptor] | None = None,
    component_registry: Iterable[EnvironmentComponentDescriptor] | None = None,
    layer_registry: Iterable[EnvironmentLayerDescriptor] | None = None,
) -> EnvironmentCatalogValidationResult:
    catalog_tuple = tuple(catalogs)
    branch_map, component_map, layer_map = _descriptor_maps(
        branch_registry,
        component_registry,
        layer_registry,
    )
    failures: list[tuple[str, str]] = []

    catalog_ids = [catalog.catalog_id for catalog in catalog_tuple]
    if not _ids_are_unique(catalog_ids):
        failures.append(
            (
                "environment_substrate_catalog_duplicate_id",
                "catalog IDs must be unique",
            )
        )

    for catalog in catalog_tuple:
        if not catalog.catalog_id:
            failures.append(("environment_substrate_catalog_id_required", "catalog_id is required"))
            break
        if not catalog.schema_version:
            failures.append(
                (
                    "environment_substrate_catalog_schema_version_required",
                    f"catalog {catalog.catalog_id} schema_version is required",
                )
            )
            break
        if catalog.schema_root_kind != "catalog_recipe":
            failures.append(
                (
                    "environment_substrate_catalog_feature_schema_root_rejected",
                    f"catalog {catalog.catalog_id} is not a catalog recipe",
                )
            )
            break
        if catalog.dropped_attribute_policy not in DROPPED_ATTRIBUTE_POLICIES:
            failures.append(
                (
                    "environment_substrate_dropped_attribute_policy_unsupported",
                    f"catalog {catalog.catalog_id} uses unsupported dropped attribute policy",
                )
            )
            break
        if not catalog.branch_membership:
            failures.append(
                (
                    "environment_substrate_catalog_branch_layer_mismatch",
                    f"catalog {catalog.catalog_id} needs branch membership",
                )
            )
            break
        if not catalog.layer_membership:
            failures.append(
                (
                    "environment_substrate_catalog_branch_layer_mismatch",
                    f"catalog {catalog.catalog_id} needs layer membership",
                )
            )
            break
        if not catalog.geometry_types:
            failures.append(
                (
                    "environment_substrate_unsupported_geometry",
                    f"catalog {catalog.catalog_id} needs geometry types",
                )
            )
            break

        catalog_branches = {membership.branch_id for membership in catalog.branch_membership}
        allowed_components: set[str] = set()
        supported_geometry_types: set[str] = set()
        for membership in catalog.branch_membership:
            branch = branch_map.get(membership.branch_id)
            if branch is None:
                failures.append(
                    (
                        "environment_substrate_unknown_branch",
                        f"catalog {catalog.catalog_id} references unknown branch {membership.branch_id!r}",
                    )
                )
                break
            if membership.role not in BRANCH_MEMBERSHIP_ROLES:
                failures.append(
                    (
                        "environment_substrate_illegal_branch_combination",
                        f"catalog {catalog.catalog_id} has illegal branch role {membership.role!r}",
                    )
                )
                break
            allowed_components.update(branch.allowed_components)
            supported_geometry_types.update(branch.supported_geometry_types)
        if failures:
            break

        for layer_id in catalog.layer_membership:
            layer = layer_map.get(layer_id)
            if layer is None:
                failures.append(
                    (
                        "environment_substrate_unknown_layer",
                        f"catalog {catalog.catalog_id} references unknown layer {layer_id!r}",
                    )
                )
                break
            if set(layer.branch_ids).isdisjoint(catalog_branches):
                failures.append(
                    (
                        "environment_substrate_catalog_branch_layer_mismatch",
                        f"layer {layer_id!r} does not admit catalog {catalog.catalog_id} branches",
                    )
                )
                break
        if failures:
            break

        unsupported_geometry = sorted(set(catalog.geometry_types) - supported_geometry_types)
        if unsupported_geometry:
            failures.append(
                (
                    "environment_substrate_unsupported_geometry",
                    f"catalog {catalog.catalog_id} uses unsupported geometry {unsupported_geometry}",
                )
            )
            break

        all_components = set(catalog.required_components) | set(catalog.optional_components)
        unknown_components = sorted(all_components - set(component_map))
        if unknown_components:
            failures.append(
                (
                    "environment_substrate_unknown_component",
                    f"catalog {catalog.catalog_id} references unknown components {unknown_components}",
                )
            )
            break
        illegal_components = sorted(all_components - allowed_components)
        if illegal_components:
            failures.append(
                (
                    "environment_substrate_catalog_branch_layer_mismatch",
                    f"catalog {catalog.catalog_id} components are not allowed by branches {illegal_components}",
                )
            )
            break

        template_families = [component.family for component in catalog.component_templates]
        if not _ids_are_unique(
            [component.component_id for component in catalog.component_templates]
        ):
            failures.append(
                (
                    "environment_substrate_duplicate_component",
                    f"catalog {catalog.catalog_id} has duplicate component templates",
                )
            )
            break
        missing_required = sorted(set(catalog.required_components) - set(template_families))
        if missing_required:
            failures.append(
                (
                    "environment_substrate_catalog_required_component_missing",
                    f"catalog {catalog.catalog_id} lacks templates {missing_required}",
                )
            )
            break
        for component in catalog.component_templates:
            descriptor = component_map.get(component.family)
            if descriptor is None:
                failures.append(
                    (
                        "environment_substrate_unknown_component",
                        f"catalog {catalog.catalog_id} has unknown template {component.family!r}",
                    )
                )
                break
            missing_attrs = sorted(
                attr
                for attr in descriptor.required_attributes
                if attr not in component.attributes
                or component.attributes.get(attr) is None
                or (
                    isinstance(component.attributes.get(attr), str)
                    and not component.attributes[attr].strip()
                )
            )
            if missing_attrs:
                failures.append(
                    (
                        "environment_substrate_catalog_required_component_missing",
                        f"catalog {catalog.catalog_id} template {component.family!r} is missing {missing_attrs}",
                    )
                )
                break
        if failures:
            break

        held_claims = sorted(
            claim for claim in catalog.capability_claims if claim in HELD_CAPABILITY_CLAIMS
        )
        if held_claims:
            failures.append(
                (
                    "environment_substrate_catalog_forbidden_capability_claim",
                    f"catalog {catalog.catalog_id} claims held capabilities {held_claims}",
                )
            )
            break

    return _first_failure(failures)


def validate_environment_catalog_admission(
    manifest: EnvironmentManifest,
    catalogs: Iterable[EnvironmentCatalogDescriptor],
) -> EnvironmentCatalogValidationResult:
    if not isinstance(manifest, EnvironmentManifest):
        raise TypeError("manifest must be an EnvironmentManifest")

    catalog_tuple = tuple(catalogs)
    catalog_validation = validate_environment_catalog_descriptors(
        catalog_tuple,
        branch_registry=manifest.branch_registry,
        component_registry=manifest.component_registry,
        layer_registry=manifest.layer_registry,
    )
    if not catalog_validation.valid:
        return catalog_validation

    catalog_map = {catalog.catalog_id: catalog for catalog in catalog_tuple}
    failures: list[tuple[str, str]] = []

    for catalog_ref in manifest.catalogs:
        if catalog_ref not in catalog_map:
            failures.append(
                (
                    "environment_substrate_catalog_ref_unknown",
                    f"manifest references unknown catalog {catalog_ref!r}",
                )
            )
            break
    if failures:
        return _first_failure(failures)

    for item in manifest.objects:
        catalog = catalog_map.get(item.catalog_ref)
        if catalog is None:
            failures.append(
                (
                    "environment_substrate_catalog_ref_unknown",
                    f"object {item.object_id} references unknown catalog {item.catalog_ref!r}",
                )
            )
            break
        if item.geometry.geometry_type not in catalog.geometry_types:
            failures.append(
                (
                    "environment_substrate_unsupported_geometry",
                    f"object {item.object_id} geometry is not admitted by {catalog.catalog_id}",
                )
            )
            break
        catalog_branches = {membership.branch_id for membership in catalog.branch_membership}
        object_branches = {membership.branch_id for membership in item.branch_membership}
        unknown_branches = sorted(object_branches - catalog_branches)
        if unknown_branches:
            failures.append(
                (
                    "environment_substrate_catalog_branch_layer_mismatch",
                    f"object {item.object_id} uses branches not admitted by catalog {unknown_branches}",
                )
            )
            break
        unknown_layers = sorted(set(item.layer_membership) - set(catalog.layer_membership))
        if unknown_layers:
            failures.append(
                (
                    "environment_substrate_catalog_branch_layer_mismatch",
                    f"object {item.object_id} uses layers not admitted by catalog {unknown_layers}",
                )
            )
            break
        item_component_families = {component.family for component in item.components}
        missing_components = sorted(set(catalog.required_components) - item_component_families)
        if missing_components:
            failures.append(
                (
                    "environment_substrate_catalog_required_component_missing",
                    f"object {item.object_id} is missing catalog components {missing_components}",
                )
            )
            break
        allowed_components = set(catalog.required_components) | set(catalog.optional_components)
        extra_components = sorted(item_component_families - allowed_components)
        if extra_components:
            failures.append(
                (
                    "environment_substrate_catalog_branch_layer_mismatch",
                    f"object {item.object_id} has components not admitted by catalog {extra_components}",
                )
            )
            break
        missing_provenance = sorted(
            key
            for key in catalog.provenance_requirements
            if not _provenance_value_present(item.provenance.get(key))
        )
        if missing_provenance:
            failures.append(
                (
                    "environment_substrate_catalog_provenance_required",
                    f"object {item.object_id} is missing catalog provenance {missing_provenance}",
                )
            )
            break
        if item.provenance.get("catalog_id") != item.catalog_ref:
            failures.append(
                (
                    "environment_substrate_catalog_provenance_mismatch",
                    f"object {item.object_id} catalog provenance does not match {item.catalog_ref}",
                )
            )
            break
        if item.provenance.get("catalog_schema_version") != catalog.schema_version:
            failures.append(
                (
                    "environment_substrate_catalog_provenance_mismatch",
                    f"object {item.object_id} catalog schema provenance does not match {catalog.schema_version}",
                )
            )
            break
        if (
            item.provenance.get("generator_id") != manifest.generation.generator_id
            or item.provenance.get("generator_version") != manifest.generation.generator_version
        ):
            failures.append(
                (
                    "environment_substrate_catalog_provenance_mismatch",
                    f"object {item.object_id} generator provenance does not match manifest generation",
                )
            )
            break

    return _first_failure(failures)


def default_environment_catalog_descriptors() -> tuple[EnvironmentCatalogDescriptor, ...]:
    return (
        EnvironmentCatalogDescriptor(
            catalog_id="catalog:deterministic_hardstand_surface",
            schema_version="1",
            branch_membership=(
                EnvironmentBranchMembership(branch_id="terrain", role="projectable"),
            ),
            layer_membership=("terrain_surface", "infrastructure_network"),
            geometry_types=("rect",),
            required_components=("surface_material",),
            optional_components=("network",),
            component_templates=(
                EnvironmentComponent(
                    component_id="component-template:hardstand-surface",
                    family="surface_material",
                    attributes={"surface": "Concrete", "roughness": 0.1},
                ),
            ),
            consumer_tags=("terrain_manifest",),
        ),
        EnvironmentCatalogDescriptor(
            catalog_id="catalog:deterministic_village_house",
            schema_version="1",
            branch_membership=(
                EnvironmentBranchMembership(branch_id="terrain", role="metadata_only"),
            ),
            layer_membership=("built_structure",),
            geometry_types=("polygon",),
            required_components=("structure",),
            optional_components=("surface_material",),
            component_templates=(
                EnvironmentComponent(
                    component_id="component-template:village-house-structure",
                    family="structure",
                    attributes={
                        "footprint": "polygon",
                        "height_m": 5.5,
                        "material": "brick",
                    },
                ),
            ),
            consumer_tags=("terrain_manifest",),
        ),
        EnvironmentCatalogDescriptor(
            catalog_id="catalog:deterministic_fog_bank",
            schema_version="1",
            branch_membership=(
                EnvironmentBranchMembership(
                    branch_id="atmosphere_weather",
                    role="metadata_only",
                ),
            ),
            layer_membership=("atmosphere_weather",),
            geometry_types=("polygon",),
            required_components=("weather_effect",),
            optional_components=("atmospheric_profile",),
            component_templates=(
                EnvironmentComponent(
                    component_id="component-template:fog-weather",
                    family="weather_effect",
                    attributes={"phenomenon": "fog", "visibility_m": 1200.0},
                ),
            ),
            consumer_tags=("weather_manifest",),
        ),
    )


__all__ = [
    "DEFAULT_CATALOG_PROVENANCE_REQUIREMENTS",
    "ENVIRONMENT_SUBSTRATE_CATALOG_CONTRACT_VERSION",
    "EnvironmentCatalogDescriptor",
    "EnvironmentCatalogValidationResult",
    "default_environment_catalog_descriptors",
    "validate_environment_catalog_admission",
    "validate_environment_catalog_descriptors",
]
