"""Qualification bridge from generic force packages to the maintained CSG compiler.

The bridge compares organization identity with an existing scenario expansion.
CSG remains the owner of geometry, embarked inventory and native scenario
materialization; this module never creates entities or installs relationships.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from python.scenario.compiler import CompiledScenario

from .force_package import (
    AssemblyReference,
    CompiledForcePackage,
    ForcePackage,
    ForcePackageError,
    compile_force_package,
)


@dataclass(frozen=True)
class CsgForcePackageQualification:
    package_ref: str
    package_identity_digest: str
    csg_schema: str
    group_id: str
    entity_bindings: tuple[tuple[str, str], ...]
    scenario_digest: str
    embarked_inventory_digest: str
    geometry_digest: str
    compiled_relationships_digest: str
    evidence_refs: tuple[str, ...]


class _CompiledScenarioLoader(Protocol):
    def load_compiled_scenario(self, compiled_scenario: CompiledScenario, seed: int = 42) -> Any: ...


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def _csg_entities(compiled_scenario: CompiledScenario, group_id: str) -> dict[str, dict[str, Any]]:
    entities = compiled_scenario.merged_scenario_data.get("entities", [])
    result: dict[str, dict[str, Any]] = {}
    for entity in entities:
        if not isinstance(entity, dict) or not isinstance(entity.get("csg_member"), dict) or entity["csg_member"].get("group_id") != group_id:
            continue
        name = str(entity.get("name", "")).strip()
        if not name or name in result:
            raise ForcePackageError("force.csg_entity_name_duplicate")
        result[name] = entity
    if not result:
        raise ForcePackageError("force.csg_entities_required")
    return result


def _compiled_relationships_digest(compiled: CompiledForcePackage) -> str:
    return _digest([relationship.__dict__ for relationship in compiled.relationships])


def qualify_force_package_against_csg(
    *,
    package: ForcePackage,
    packages: Mapping[str, ForcePackage],
    assemblies: Mapping[str, AssemblyReference],
    role_capabilities: Mapping[str, frozenset[str]],
    scenario: CompiledScenario,
    group_id: str,
    entity_bindings: Mapping[str, str],
    assembly_type_names: Mapping[str, str],
) -> CsgForcePackageQualification:
    """Compare one compiled package with the existing CSG expansion.

    The caller supplies explicit links from scoped organization IDs to existing
    scenario names, and from assembly IDs to native type names. No domain naming
    or capability inference is introduced into the generic package compiler.
    """

    compiled: CompiledForcePackage = compile_force_package(
        package,
        packages=packages,
        assemblies=assemblies,
        role_capabilities=role_capabilities,
    )
    if not scenario.is_fresh():
        raise ForcePackageError("force.csg_scenario_stale")
    meta = scenario.merged_scenario_data.get("meta", {})
    csg_meta = meta.get("csg", {}) if isinstance(meta, dict) else {}
    if not isinstance(csg_meta, dict) or csg_meta.get("schema") != "csg.group_composition.v2":
        raise ForcePackageError("force.csg_schema_not_maintained")
    if scenario.runtime_metadata.meta_config.get("csg") != csg_meta:
        raise ForcePackageError("force.csg_runtime_metadata_mismatch")
    groups = [group for group in csg_meta.get("groups", []) if isinstance(group, dict) and group.get("group_id") == group_id]
    if len(groups) != 1:
        raise ForcePackageError(f"force.csg_group_unknown_or_duplicate:groups.{group_id}")
    group = groups[0]
    if group.get("side") != package.side:
        raise ForcePackageError("force.csg_group_side_mismatch")
    guide = group.get("guide")
    ships = group.get("ships")
    inventory = group.get("embarked_inventory")
    if not isinstance(guide, dict) or not isinstance(ships, list) or not isinstance(inventory, list):
        raise ForcePackageError("force.csg_group_metadata_incomplete")
    declared_entity_names = {
        name
        for row in ships
        if isinstance(row, dict)
        for name in row.get("entity_names", [])
        if isinstance(name, str) and name.strip()
    }
    frame = "geodetic" if "geo" in group["guide"] else "local_enu"
    for instance in compiled.package_instances:
        if instance.reference_frame != frame or instance.anchor_ref != group_id:
            raise ForcePackageError(f"force.csg_frame_anchor_mismatch:packages.{instance.instance_id}")
    csg_entities = _csg_entities(scenario, group_id)
    if set(csg_entities) != declared_entity_names:
        raise ForcePackageError("force.csg_group_entity_metadata_mismatch")
    ship_member_ids = {row.get("member_id") for row in ships if isinstance(row, dict)}
    for row in inventory:
        if not isinstance(row, dict) or row.get("embarked_on") not in ship_member_ids:
            raise ForcePackageError("force.csg_inventory_host_unknown")
        if not isinstance(row.get("count"), int) or isinstance(row["count"], bool) or row["count"] < 0:
            raise ForcePackageError("force.csg_inventory_count_invalid")
    if set(entity_bindings) != {entity.entity_id for entity in compiled.entities}:
        raise ForcePackageError("force.csg_binding_scope_mismatch:entity_bindings")
    if len(set(entity_bindings.values())) != len(entity_bindings):
        raise ForcePackageError("force.csg_binding_duplicate:entity_bindings")
    if set(entity_bindings.values()) != set(csg_entities):
        raise ForcePackageError("force.csg_entity_set_mismatch:entity_bindings")
    for generic in compiled.entities:
        name = entity_bindings[generic.entity_id]
        csg_entity = csg_entities[name]
        member = csg_entity.get("csg_member")
        if not isinstance(member, dict) or not isinstance(csg_entity.get("pos"), list) or len(csg_entity["pos"]) != 3:
            raise ForcePackageError(f"force.csg_entity_metadata_incomplete:{name}")
        if generic.member_ref not in assembly_type_names:
            raise ForcePackageError(f"force.csg_assembly_type_unknown:members.{generic.entity_id}")
        if (
            assembly_type_names[generic.member_ref] != csg_entity.get("type")
            or generic.role != member.get("role")
            or generic.side != csg_entity.get("side")
        ):
            raise ForcePackageError(f"force.csg_entity_projection_mismatch:{name}")

    geometry = csg_meta.get("geometry", {})
    scenario_digest = _digest(scenario.merged_scenario_data)
    relationships_digest = _compiled_relationships_digest(compiled)
    return CsgForcePackageQualification(
        package_ref=compiled.package_ref,
        package_identity_digest=compiled.identity_digest,
        csg_schema=csg_meta["schema"],
        group_id=group_id,
        entity_bindings=tuple(sorted(entity_bindings.items())),
        scenario_digest=scenario_digest,
        embarked_inventory_digest=_digest(group.get("embarked_inventory", [])),
        geometry_digest=_digest(geometry),
        compiled_relationships_digest=relationships_digest,
        evidence_refs=(
            f"force.package:{compiled.package_ref}",
            f"force.identity:{compiled.identity_digest}",
            f"force.relationships:{relationships_digest}",
            "scenario.csg.group_composition.v2",
            f"scenario.identity:{scenario_digest}",
            f"scenario.csg.geometry:{_digest(geometry)}",
        ),
    )


def load_qualified_csg_scenario(
    loader: _CompiledScenarioLoader,
    *,
    scenario: CompiledScenario,
    qualifications: Sequence[CsgForcePackageQualification],
    compiled_packages: Mapping[str, CompiledForcePackage],
    seed: int = 42,
) -> Any:
    """Validate the qualified snapshot, then delegate to the maintained loader.

    Every CSG group must have a qualification result bound to the independently
    compiled package identity supplied by the caller. No positions, entities,
    inventories or relationship authority are synthesized by this bridge.
    """
    if not scenario.is_fresh():
        raise ForcePackageError("force.csg_scenario_stale")
    meta = scenario.merged_scenario_data.get("meta", {})
    csg_meta = meta.get("csg", {}) if isinstance(meta, dict) else {}
    if not isinstance(csg_meta, dict):
        raise ForcePackageError("force.csg_schema_not_maintained")
    if csg_meta.get("schema") != "csg.group_composition.v2":
        raise ForcePackageError("force.csg_schema_not_maintained")
    if scenario.runtime_metadata.meta_config.get("csg") != csg_meta:
        raise ForcePackageError("force.csg_runtime_metadata_mismatch")
    groups = {group["group_id"]: group for group in csg_meta["groups"]}
    qualified_ids = [qualification.group_id for qualification in qualifications]
    if not qualified_ids or len(set(qualified_ids)) != len(qualified_ids) or set(qualified_ids) != set(groups):
        raise ForcePackageError("force.csg_qualification_scope_mismatch")
    if not isinstance(compiled_packages, Mapping) or not compiled_packages:
        raise ForcePackageError("force.csg_compiled_package_scope_required")
    package_refs = {qualification.package_ref for qualification in qualifications}
    if set(compiled_packages) != package_refs:
        raise ForcePackageError("force.csg_compiled_package_scope_mismatch")
    scenario_digest = _digest(scenario.merged_scenario_data)
    geometry_digest = _digest(csg_meta["geometry"])
    for qualification in qualifications:
        compiled = compiled_packages.get(qualification.package_ref)
        if (
            compiled is None
            or compiled.identity_digest != qualification.package_identity_digest
            or _compiled_relationships_digest(compiled)
            != qualification.compiled_relationships_digest
        ):
            raise ForcePackageError("force.csg_compiled_package_identity_mismatch")
        group = groups[qualification.group_id]
        if (
            qualification.csg_schema != csg_meta["schema"]
            or qualification.scenario_digest != scenario_digest
            or qualification.geometry_digest != geometry_digest
            or qualification.embarked_inventory_digest != _digest(group["embarked_inventory"])
            or {name for _, name in qualification.entity_bindings}
            != set(_csg_entities(scenario, qualification.group_id))
        ):
            raise ForcePackageError("force.csg_qualification_snapshot_mismatch")
    return loader.load_compiled_scenario(scenario, seed=seed)


__all__ = ["CsgForcePackageQualification", "qualify_force_package_against_csg", "load_qualified_csg_scenario"]
