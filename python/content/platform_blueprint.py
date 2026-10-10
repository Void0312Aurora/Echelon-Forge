"""Qualification-only platform blueprint and assembly resolver.

The resolver lowers a versioned platform assembly into a deterministic plan
for the existing native factory.  It does not create ECS entities, replace
UnitDefinition, or admit a new production content path.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "echelon_forge.platform_assembly.v1"


class PlatformAssemblyError(ValueError):
    """Raised for malformed authoring documents."""


@dataclass(frozen=True)
class ModuleRecord:
    module_id: str
    kind: str
    capabilities: frozenset[str] = frozenset()
    version: str = "1"
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.module_id.strip() or not self.kind.strip() or not self.version.strip():
            raise ValueError("module_id, kind, and version are required")
        if not self.evidence_refs or any(not ref.strip() for ref in self.evidence_refs):
            raise ValueError("module evidence_refs are required")


@dataclass(frozen=True)
class PlatformBlueprint:
    blueprint_id: str
    version: str
    platform_family: str
    slots: tuple[tuple[str, str], ...]
    required_capabilities: frozenset[str] = frozenset()
    override_types: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.blueprint_id.strip() or not self.version.strip() or not self.platform_family.strip():
            raise ValueError("blueprint identity and platform_family are required")
        slot_names = [name for name, _ in self.slots]
        if len(slot_names) != len(set(slot_names)):
            raise ValueError("blueprint slots must be unique")
        if any(not name.strip() or not kind.strip() for name, kind in self.slots):
            raise ValueError("blueprint slot names and kinds are required")
        override_names = [name for name, _ in self.override_types]
        if len(override_names) != len(set(override_names)):
            raise ValueError("blueprint override fields must be unique")

    def expected_kind(self, slot: str) -> str | None:
        return dict(self.slots).get(slot)

    def override_type(self, name: str) -> str | None:
        return dict(self.override_types).get(name)


@dataclass(frozen=True)
class ModuleSelection:
    slot: str
    module_ref: str


@dataclass(frozen=True)
class ResolvedPlatformSpawnPlan:
    schema_version: str
    assembly_id: str
    blueprint_ref: str
    platform_family: str
    modules: tuple[tuple[str, str], ...]
    parameter_overrides: tuple[tuple[str, Any], ...]
    capabilities: tuple[str, ...]
    identity_digest: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "assembly_id": self.assembly_id,
            "blueprint_ref": self.blueprint_ref,
            "platform_family": self.platform_family,
            "modules": [{"slot": slot, "module_ref": module} for slot, module in self.modules],
            "parameter_overrides": dict(self.parameter_overrides),
            "capabilities": list(self.capabilities),
            "identity_digest": self.identity_digest,
        }


def _check_override(value: Any, expected: str) -> bool:
    if expected == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    return False


def resolve_platform_assembly(
    *,
    assembly_id: str,
    blueprint: PlatformBlueprint,
    selections: Sequence[ModuleSelection],
    modules: Mapping[str, ModuleRecord],
    parameter_overrides: Mapping[str, Any] | None = None,
) -> ResolvedPlatformSpawnPlan:
    """Resolve an assembly before publication to the native factory."""

    if not assembly_id.strip():
        raise PlatformAssemblyError("assembly_id is required")
    expected_slots = dict(blueprint.slots)
    selected: dict[str, ModuleRecord] = {}
    errors: list[str] = []
    for index, selection in enumerate(selections):
        path = f"modules[{index}]"
        if selection.slot in selected:
            errors.append(f"platform.duplicate_slot:{path}.slot:{selection.slot}")
            continue
        expected_kind = expected_slots.get(selection.slot)
        if expected_kind is None:
            errors.append(f"platform.unknown_slot:{path}.slot:{selection.slot}")
            continue
        module = modules.get(selection.module_ref)
        if module is None:
            errors.append(f"platform.module_unknown:{path}.module_ref:{selection.module_ref}")
            continue
        if module.kind != expected_kind:
            errors.append(f"platform.module_kind_mismatch:{path}.module_ref:{selection.module_ref}:{module.kind}!={expected_kind}")
            continue
        selected[selection.slot] = module
    missing_slots = sorted(set(expected_slots) - set(selected))
    errors.extend(f"platform.required_slot_missing:modules.{slot}" for slot in missing_slots)
    all_capabilities = frozenset().union(*(module.capabilities for module in selected.values()))
    missing_capabilities = sorted(blueprint.required_capabilities - all_capabilities)
    errors.extend(f"platform.required_capability_missing:capabilities.{capability}" for capability in missing_capabilities)

    overrides = dict(parameter_overrides or {})
    for name, value in overrides.items():
        expected_type = blueprint.override_type(name)
        if expected_type is None:
            errors.append(f"platform.override_not_allowlisted:parameter_overrides.{name}")
        elif not _check_override(value, expected_type):
            errors.append(f"platform.override_type_mismatch:parameter_overrides.{name}:{expected_type}")
    if errors:
        raise PlatformAssemblyError("; ".join(errors))

    normalized_modules = tuple(sorted((slot, selected[slot].module_id + "@" + selected[slot].version) for slot in selected))
    normalized_overrides = tuple(sorted(overrides.items()))
    capabilities = tuple(sorted(all_capabilities))
    identity_payload = {
        "schema_version": SCHEMA_VERSION,
        "assembly_id": assembly_id,
        "blueprint_ref": f"{blueprint.blueprint_id}@{blueprint.version}",
        "platform_family": blueprint.platform_family,
        "modules": normalized_modules,
        "parameter_overrides": normalized_overrides,
        "capabilities": capabilities,
    }
    digest = hashlib.sha256(
        json.dumps(identity_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return ResolvedPlatformSpawnPlan(
        schema_version=SCHEMA_VERSION,
        assembly_id=assembly_id,
        blueprint_ref=f"{blueprint.blueprint_id}@{blueprint.version}",
        platform_family=blueprint.platform_family,
        modules=normalized_modules,
        parameter_overrides=normalized_overrides,
        capabilities=capabilities,
        identity_digest=digest,
    )


__all__ = [
    "ModuleRecord",
    "ModuleSelection",
    "PlatformAssemblyError",
    "PlatformBlueprint",
    "ResolvedPlatformSpawnPlan",
    "SCHEMA_VERSION",
    "resolve_platform_assembly",
]
