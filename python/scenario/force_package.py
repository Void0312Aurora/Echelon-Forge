"""Qualification-only recursive force-package compiler.

Force packages describe organization and placement references.  The compiler
expands them into deterministic scenario entities but never creates native ECS
entities or grants task authority; those remain owned by existing scenario and
Joint contracts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "echelon_forge.force_package.v1"
_SUPPORTED_FRAMES = frozenset({"local_enu", "geodetic"})
_ALLOWED_RELATIONSHIPS = frozenset({"membership", "task_authority", "communication"})


class ForcePackageError(ValueError):
    """Raised when a package cannot be safely expanded."""


@dataclass(frozen=True)
class PackageMember:
    member_id: str
    ref_kind: str
    ref: str
    role: str
    side: str | None = None

    def __post_init__(self) -> None:
        if not all(isinstance(value, str) and value.strip() for value in (self.member_id, self.ref_kind, self.ref, self.role)):
            raise ValueError("member_id, ref_kind, ref, and role are required")
        if self.ref_kind not in {"package", "assembly"}:
            raise ValueError("ref_kind must be package or assembly")
        if self.side is not None and not self.side.strip():
            raise ValueError("side must be non-empty when supplied")


@dataclass(frozen=True)
class PackageRelationship:
    relationship_type: str
    source: str
    target: str

    def __post_init__(self) -> None:
        if self.relationship_type not in _ALLOWED_RELATIONSHIPS:
            raise ValueError(f"unsupported relationship type: {self.relationship_type!r}")
        if not self.source.strip() or not self.target.strip():
            raise ValueError("relationship endpoints are required")


@dataclass(frozen=True)
class ForcePackage:
    package_id: str
    version: str
    side: str
    members: tuple[PackageMember, ...]
    reference_frame: str = "local_enu"
    anchor_ref: str = ""
    relationships: tuple[PackageRelationship, ...] = ()
    provenance_ref: str = ""

    def __post_init__(self) -> None:
        if not self.package_id.strip() or not self.version.strip() or not self.side.strip():
            raise ValueError("package identity and side are required")
        if self.reference_frame not in _SUPPORTED_FRAMES:
            raise ValueError(f"unsupported reference_frame: {self.reference_frame!r}")
        ids = [member.member_id for member in self.members]
        if len(ids) != len(set(ids)):
            raise ValueError("package member IDs must be unique")

    @property
    def ref(self) -> str:
        return f"{self.package_id}@{self.version}"


@dataclass(frozen=True)
class AssemblyReference:
    assembly_id: str
    side: str
    capabilities: frozenset[str]


@dataclass(frozen=True)
class FlattenedEntity:
    entity_id: str
    package_ref: str
    member_ref: str
    role: str
    side: str
    provenance: tuple[str, ...]


@dataclass(frozen=True)
class CompiledForcePackage:
    schema_version: str
    package_ref: str
    entities: tuple[FlattenedEntity, ...]
    identity_digest: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "package_ref": self.package_ref,
            "entities": [entity.__dict__ for entity in self.entities],
            "identity_digest": self.identity_digest,
        }


def compile_force_package(
    root: ForcePackage,
    *,
    packages: Mapping[str, ForcePackage],
    assemblies: Mapping[str, AssemblyReference],
    role_capabilities: Mapping[str, frozenset[str]],
) -> CompiledForcePackage:
    """Expand a finite package DAG before scenario/native publication."""

    registry = dict(packages)
    registry.setdefault(root.ref, root)
    errors: list[str] = []
    entities: list[FlattenedEntity] = []
    visited: set[str] = set()

    def visit(package: ForcePackage, path: tuple[str, ...], stack: tuple[str, ...]) -> None:
        if package.ref in stack:
            errors.append(f"force.membership_cycle:packages.{package.ref}")
            return
        if package.ref in visited:
            return
        visited.add(package.ref)
        member_ids = {member.member_id for member in package.members}
        relationship_types: set[str] = set()
        for relationship in package.relationships:
            relationship_types.add(relationship.relationship_type)
            if relationship.source not in member_ids or relationship.target not in member_ids:
                errors.append(f"force.relationship_endpoint_unknown:packages.{package.ref}.{relationship.source}->{relationship.target}")
        for member in package.members:
            member_path = path + (member.member_id,)
            if member.ref_kind == "package":
                child = registry.get(member.ref)
                if child is None:
                    errors.append(f"force.package_unknown:members.{'.'.join(member_path)}")
                    continue
                if member.side is not None and member.side != package.side:
                    errors.append(f"force.side_conflict:members.{'.'.join(member_path)}")
                required = role_capabilities.get(member.role)
                if required is None:
                    errors.append(f"force.role_unknown:members.{'.'.join(member_path)}")
                visit(child, member_path, stack + (package.ref,))
                continue
            assembly = assemblies.get(member.ref)
            if assembly is None:
                errors.append(f"force.assembly_unknown:members.{'.'.join(member_path)}")
                continue
            if assembly.side != package.side or (member.side is not None and member.side != assembly.side):
                errors.append(f"force.side_conflict:members.{'.'.join(member_path)}")
            required = role_capabilities.get(member.role)
            if required is None:
                errors.append(f"force.role_unknown:members.{'.'.join(member_path)}")
            elif not required.issubset(assembly.capabilities):
                errors.append(f"force.role_capability_missing:members.{'.'.join(member_path)}")
            entities.append(
                FlattenedEntity(
                    entity_id="/".join(member_path),
                    package_ref=package.ref,
                    member_ref=assembly.assembly_id,
                    role=member.role,
                    side=assembly.side,
                    provenance=member_path,
                )
            )
        if relationship_types and "membership" not in relationship_types:
            # Membership is implicit in package expansion; command/communications
            # edges are explicit and never inferred from nesting.
            return

    visit(root, (root.package_id,), ())
    if errors:
        raise ForcePackageError("; ".join(sorted(set(errors))))
    entities.sort(key=lambda entity: entity.entity_id)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "package_ref": root.ref,
        "entities": [entity.__dict__ for entity in entities],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return CompiledForcePackage(SCHEMA_VERSION, root.ref, tuple(entities), digest)


__all__ = [
    "AssemblyReference",
    "CompiledForcePackage",
    "FlattenedEntity",
    "ForcePackage",
    "ForcePackageError",
    "PackageMember",
    "PackageRelationship",
    "SCHEMA_VERSION",
    "compile_force_package",
]
