"""Qualification bridge from generic force packages to the maintained CSG compiler.

The bridge compares organization identity with an existing scenario expansion.
CSG remains the owner of geometry, embarked inventory and native scenario
materialization; this module never creates entities or installs relationships.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

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
    evidence_refs: tuple[str, ...]


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def _csg_entities(compiled_scenario: CompiledScenario, group_id: str) -> dict[str, dict[str, Any]]:
    entities = compiled_scenario.merged_scenario_data.get("entities", [])
    result: dict[str, dict[str, Any]] = {}
    for entity in entities:
        if not isinstance(entity, dict) or entity.get("csg_member", {}).get("group_id") != group_id:
            continue
        name = str(entity.get("name", "")).strip()
        if not name or name in result:
            raise ForcePackageError("force.csg_entity_name_duplicate")
        result[name] = entity
    if not result:
        raise ForcePackageError("force.csg_entities_required")
    return result


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
    csg_meta = scenario.merged_scenario_data.get("meta", {}).get("csg", {})
    if not isinstance(csg_meta, dict) or csg_meta.get("schema") != "csg.group_composition.v2":
        raise ForcePackageError("force.csg_schema_not_maintained")
    groups = [group for group in csg_meta.get("groups", []) if group.get("group_id") == group_id]
    if len(groups) != 1:
        raise ForcePackageError(f"force.csg_group_unknown_or_duplicate:groups.{group_id}")
    group = groups[0]
    frame = "geodetic" if "geo" in group["guide"] else "local_enu"
    for instance in compiled.package_instances:
        if instance.reference_frame != frame or instance.anchor_ref != group_id:
            raise ForcePackageError(f"force.csg_frame_anchor_mismatch:packages.{instance.instance_id}")
    csg_entities = _csg_entities(scenario, group_id)
    if set(entity_bindings) != {entity.entity_id for entity in compiled.entities}:
        raise ForcePackageError("force.csg_binding_scope_mismatch:entity_bindings")
    if len(set(entity_bindings.values())) != len(entity_bindings):
        raise ForcePackageError("force.csg_binding_duplicate:entity_bindings")
    if set(entity_bindings.values()) != set(csg_entities):
        raise ForcePackageError("force.csg_entity_set_mismatch:entity_bindings")
    for generic in compiled.entities:
        name = entity_bindings[generic.entity_id]
        csg_entity = csg_entities[name]
        member = csg_entity["csg_member"]
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
    return CsgForcePackageQualification(
        package_ref=compiled.package_ref,
        package_identity_digest=compiled.identity_digest,
        csg_schema=csg_meta["schema"],
        group_id=group_id,
        entity_bindings=tuple(sorted(entity_bindings.items())),
        scenario_digest=scenario_digest,
        embarked_inventory_digest=_digest(group.get("embarked_inventory", [])),
        geometry_digest=_digest(geometry),
        evidence_refs=(
            f"force.package:{compiled.package_ref}",
            f"force.identity:{compiled.identity_digest}",
            "scenario.csg.group_composition.v2",
            f"scenario.identity:{scenario_digest}",
            f"scenario.csg.geometry:{_digest(geometry)}",
        ),
    )


__all__ = ["CsgForcePackageQualification", "qualify_force_package_against_csg"]
