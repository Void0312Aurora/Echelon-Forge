from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .components import (
    BRANCH_MEMBERSHIP_ROLES,
    DEFAULT_BRANCH_IDS,
    DROPPED_ATTRIBUTE_POLICIES,
    HELD_CAPABILITY_CLAIMS,
    PROJECTION_TARGETS,
)
from .manifest import EnvironmentManifest


BEHAVIOR_PROPERTY_KEYS = (
    "actor_classes",
    "building_height_m",
    "cover_class",
    "cover_factor",
    "damage_model",
    "fordability",
    "height_m",
    "lane_count",
    "los_opacity",
    "movement_cost",
    "movement_speed_mps",
    "passability",
    "speed_multiplier",
    "surface",
    "surface_type",
    "tree_density",
    "width_m",
)


@dataclass(frozen=True)
class EnvironmentManifestValidationResult:
    valid: bool
    fail_closed: bool
    rejection_reason: str
    errors: tuple[str, ...]


def _normalized_text(value: Any) -> str:
    return str(value or "").strip()


def _first_failure(failures: list[tuple[str, str]]) -> EnvironmentManifestValidationResult:
    if not failures:
        return EnvironmentManifestValidationResult(
            valid=True,
            fail_closed=False,
            rejection_reason="",
            errors=(),
        )
    return EnvironmentManifestValidationResult(
        valid=False,
        fail_closed=True,
        rejection_reason=failures[0][0],
        errors=tuple(message for _, message in failures),
    )


def _finite_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def _ids_are_unique(ids: list[str]) -> bool:
    return len(ids) == len(set(ids))


def validate_environment_manifest(
    manifest: EnvironmentManifest,
) -> EnvironmentManifestValidationResult:
    if not isinstance(manifest, EnvironmentManifest):
        raise TypeError("manifest must be an EnvironmentManifest")

    failures: list[tuple[str, str]] = []

    if not manifest.manifest_id:
        failures.append(
            (
                "environment_substrate_manifest_id_required",
                "manifest_id is required",
            )
        )
    if not manifest.schema_version:
        failures.append(
            (
                "environment_substrate_schema_version_required",
                "schema_version is required",
            )
        )
    if not manifest.contract_version:
        failures.append(
            (
                "environment_substrate_contract_version_required",
                "contract_version is required",
            )
        )
    if not manifest.coordinate_frame:
        failures.append(
            (
                "environment_substrate_coordinate_frame_required",
                "coordinate_frame is required",
            )
        )

    extent = manifest.region_extent
    if not all(
        _finite_number(value) for value in (extent.min_x, extent.min_y, extent.max_x, extent.max_y)
    ):
        failures.append(
            (
                "environment_substrate_invalid_extent",
                "region_extent coordinates must be finite numbers",
            )
        )
    elif extent.max_x <= extent.min_x or extent.max_y <= extent.min_y:
        failures.append(
            (
                "environment_substrate_invalid_extent",
                "region_extent max values must be greater than min values",
            )
        )

    branch_ids = [branch.branch_id for branch in manifest.branch_registry]
    component_families = [component.family for component in manifest.component_registry]
    layer_ids = [layer.layer_id for layer in manifest.layer_registry]
    projection_profile_ids = [profile.profile_id for profile in manifest.projection_profiles]

    if not branch_ids:
        failures.append(
            (
                "environment_substrate_branch_registry_required",
                "branch_registry must not be empty",
            )
        )
    if not component_families:
        failures.append(
            (
                "environment_substrate_component_registry_required",
                "component_registry must not be empty",
            )
        )
    if not layer_ids:
        failures.append(
            (
                "environment_substrate_layer_registry_required",
                "layer_registry must not be empty",
            )
        )
    if not _ids_are_unique(branch_ids):
        failures.append(
            (
                "environment_substrate_duplicate_branch",
                "branch_registry branch IDs must be unique",
            )
        )
    if not _ids_are_unique(component_families):
        failures.append(
            (
                "environment_substrate_duplicate_component",
                "component_registry families must be unique",
            )
        )
    if not _ids_are_unique(layer_ids):
        failures.append(
            (
                "environment_substrate_duplicate_layer",
                "layer_registry layer IDs must be unique",
            )
        )
    missing_default_branches = sorted(set(DEFAULT_BRANCH_IDS) - set(branch_ids))
    if missing_default_branches:
        failures.append(
            (
                "environment_substrate_required_branch_missing",
                f"branch_registry is missing {missing_default_branches}",
            )
        )

    branch_map = {branch.branch_id: branch for branch in manifest.branch_registry}
    component_map = {component.family: component for component in manifest.component_registry}
    layer_map = {layer.layer_id: layer for layer in manifest.layer_registry}
    profile_map = {profile.profile_id: profile for profile in manifest.projection_profiles}

    for branch in manifest.branch_registry:
        if not branch.branch_id:
            failures.append(
                (
                    "environment_substrate_branch_id_required",
                    "branch descriptor branch_id is required",
                )
            )
            break
        unknown_components = sorted(set(branch.allowed_components) - set(component_families))
        if unknown_components:
            failures.append(
                (
                    "environment_substrate_unknown_component",
                    f"branch {branch.branch_id} allows unknown components {unknown_components}",
                )
            )
            break
        unknown_targets = sorted(set(branch.projection_targets) - set(PROJECTION_TARGETS))
        if unknown_targets:
            failures.append(
                (
                    "environment_substrate_unsupported_target_field",
                    f"branch {branch.branch_id} uses unsupported targets {unknown_targets}",
                )
            )
            break

    for layer in manifest.layer_registry:
        if not layer.layer_id:
            failures.append(
                (
                    "environment_substrate_layer_id_required",
                    "layer descriptor layer_id is required",
                )
            )
            break
        unknown_branches = sorted(set(layer.branch_ids) - set(branch_ids))
        if unknown_branches:
            failures.append(
                (
                    "environment_substrate_unknown_branch",
                    f"layer {layer.layer_id} references unknown branches {unknown_branches}",
                )
            )
            break

    for profile in manifest.projection_profiles:
        if not profile.profile_id:
            failures.append(
                (
                    "environment_substrate_projection_profile_id_required",
                    "projection profile_id is required",
                )
            )
            break
        if profile.target not in PROJECTION_TARGETS:
            failures.append(
                (
                    "environment_substrate_unsupported_target_field",
                    f"projection target {profile.target!r} is unsupported",
                )
            )
            break
        if profile.branch_id and profile.branch_id not in branch_map:
            failures.append(
                (
                    "environment_substrate_unknown_branch",
                    f"projection profile {profile.profile_id} references unknown branch",
                )
            )
            break
        if profile.dropped_attribute_policy not in DROPPED_ATTRIBUTE_POLICIES:
            failures.append(
                (
                    "environment_substrate_dropped_attribute_policy_unsupported",
                    f"dropped attribute policy {profile.dropped_attribute_policy!r} is unsupported",
                )
            )
            break
        unknown_components = sorted(set(profile.required_components) - set(component_families))
        if unknown_components:
            failures.append(
                (
                    "environment_substrate_unknown_component",
                    f"projection profile {profile.profile_id} requires unknown components {unknown_components}",
                )
            )
            break

    object_ids = [item.object_id for item in manifest.objects]
    if not _ids_are_unique(object_ids):
        failures.append(
            (
                "environment_substrate_duplicate_object",
                "object IDs must be unique",
            )
        )

    for item in manifest.objects:
        if not item.object_id:
            failures.append(
                (
                    "environment_substrate_object_id_required",
                    "object_id is required",
                )
            )
            break
        if not item.geometry.geometry_type:
            failures.append(
                (
                    "environment_substrate_unsupported_geometry",
                    f"object {item.object_id} geometry_type is required",
                )
            )
            break
        if not isinstance(item.geometry.coordinates, dict):
            failures.append(
                (
                    "environment_substrate_unsupported_geometry",
                    f"object {item.object_id} geometry coordinates must be an object",
                )
            )
            break
        if not item.branch_membership:
            failures.append(
                (
                    "environment_substrate_branch_membership_required",
                    f"object {item.object_id} must declare branch membership",
                )
            )
            break

        item_branches: set[str] = set()
        for membership in item.branch_membership:
            if membership.branch_id not in branch_map:
                failures.append(
                    (
                        "environment_substrate_unknown_branch",
                        f"object {item.object_id} references unknown branch {membership.branch_id!r}",
                    )
                )
                break
            if membership.role not in BRANCH_MEMBERSHIP_ROLES:
                failures.append(
                    (
                        "environment_substrate_illegal_branch_combination",
                        f"object {item.object_id} has illegal branch role {membership.role!r}",
                    )
                )
                break
            branch = branch_map[membership.branch_id]
            if (
                item.geometry.geometry_type
                and branch.supported_geometry_types
                and item.geometry.geometry_type not in branch.supported_geometry_types
            ):
                failures.append(
                    (
                        "environment_substrate_unsupported_geometry",
                        f"object {item.object_id} geometry {item.geometry.geometry_type!r} is not supported by branch {branch.branch_id}",
                    )
                )
                break
            item_branches.add(membership.branch_id)
            for profile_ref in membership.projection_profile_refs:
                if profile_ref not in profile_map:
                    failures.append(
                        (
                            "environment_substrate_unknown_projection_profile",
                            f"object {item.object_id} references unknown projection profile {profile_ref!r}",
                        )
                    )
                    break
        if failures:
            break

        for layer_id in item.layer_membership:
            if layer_id not in layer_map:
                failures.append(
                    (
                        "environment_substrate_unknown_layer",
                        f"object {item.object_id} references unknown layer {layer_id!r}",
                    )
                )
                break
        if failures:
            break

        for profile_id in item.projection_profile_ids:
            if profile_id not in profile_map:
                failures.append(
                    (
                        "environment_substrate_unknown_projection_profile",
                        f"object {item.object_id} references unknown projection profile {profile_id!r}",
                    )
                )
                break
        if failures:
            break

        allowed_by_branch: set[str] = set()
        for branch_id in item_branches:
            allowed_by_branch.update(branch_map[branch_id].allowed_components)

        component_ids = [component.component_id for component in item.components]
        if not _ids_are_unique(component_ids):
            failures.append(
                (
                    "environment_substrate_duplicate_component",
                    f"object {item.object_id} has duplicate component IDs",
                )
            )
            break
        for component in item.components:
            if not component.component_id:
                failures.append(
                    (
                        "environment_substrate_component_id_required",
                        f"object {item.object_id} has a component without component_id",
                    )
                )
                break
            descriptor = component_map.get(component.family)
            if descriptor is None:
                failures.append(
                    (
                        "environment_substrate_unknown_component",
                        f"object {item.object_id} uses unknown component {component.family!r}",
                    )
                )
                break
            if allowed_by_branch and component.family not in allowed_by_branch:
                failures.append(
                    (
                        "environment_substrate_illegal_branch_combination",
                        f"component {component.family!r} is not allowed by object {item.object_id} branches",
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
                        "environment_substrate_missing_required_component_attribute",
                        f"component {component.component_id} is missing {missing_attrs}",
                    )
                )
                break
        if failures:
            break

        behavior_property_keys = sorted(
            key for key in item.properties.keys() if key in BEHAVIOR_PROPERTY_KEYS
        )
        if behavior_property_keys:
            failures.append(
                (
                    "environment_substrate_untyped_behavior_property",
                    f"object {item.object_id} puts behavior fields in properties: {behavior_property_keys}",
                )
            )
            break

    held_claims = sorted(
        claim for claim in manifest.capability_claims if claim in HELD_CAPABILITY_CLAIMS
    )
    if held_claims:
        failures.append(
            (
                "environment_substrate_held_capability_claim",
                f"manifest claims held capabilities {held_claims}",
            )
        )

    return _first_failure(failures)


__all__ = [
    "BEHAVIOR_PROPERTY_KEYS",
    "EnvironmentManifestValidationResult",
    "validate_environment_manifest",
]
