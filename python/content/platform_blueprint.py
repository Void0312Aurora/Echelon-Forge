"""Qualification-only platform blueprint and assembly resolver.

The resolver lowers a versioned platform assembly into a deterministic plan
for the existing native factory.  It does not create ECS entities, replace
UnitDefinition, or admit a new production content path.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from python.json_value import freeze_json_mapping, thaw_json_value

SCHEMA_VERSION = "echelon_forge.platform_assembly.v1"


class PlatformAssemblyError(ValueError):
    """Raised for malformed authoring documents."""


def _optional_nonnegative_number(value: Any, label: str) -> float | None:
    if value is None:
        return None
    try:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError
        normalized = float(value)
        if not math.isfinite(normalized) or normalized < 0.0:
            raise ValueError
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"{label} must be finite and non-negative") from exc
    return normalized if normalized else 0.0


def _physical_total(values: Sequence[float]) -> float:
    try:
        return math.fsum(values)
    except OverflowError:
        # Every declared budget is finite, so overflow must fail its bound.
        return math.inf


@dataclass(frozen=True)
class ModuleRecord:
    module_id: str
    kind: str
    capabilities: frozenset[str] = frozenset()
    version: str = "1"
    evidence_refs: tuple[str, ...] = ()
    content_digest: str = ""
    native_ref: str = ""
    mass_kg: float | None = None
    power_draw_kw: float | None = None
    mount_classes: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.module_id.strip() or not self.kind.strip() or not self.version.strip():
            raise ValueError("module_id, kind, and version are required")
        if not self.evidence_refs or any(not ref.strip() for ref in self.evidence_refs):
            raise ValueError("module evidence_refs are required")
        for label, value in (("mass_kg", self.mass_kg), ("power_draw_kw", self.power_draw_kw)):
            object.__setattr__(self, label, _optional_nonnegative_number(value, f"module {label}"))
        object.__setattr__(self, "mount_classes", frozenset(self.mount_classes))
        if any(not isinstance(mount, str) or not mount.strip() for mount in self.mount_classes):
            raise ValueError("module mount classes must be non-empty")


@dataclass(frozen=True)
class HardpointContract:
    """Qualification contract for one loadout station."""

    hardpoint_id: str
    mount_class: str
    capacity_kg: float | None = None
    allowed_kinds: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.hardpoint_id.strip() or not self.mount_class.strip():
            raise ValueError("hardpoint identity and mount_class are required")
        object.__setattr__(
            self,
            "capacity_kg",
            _optional_nonnegative_number(self.capacity_kg, "hardpoint capacity_kg"),
        )
        object.__setattr__(self, "allowed_kinds", frozenset(self.allowed_kinds))
        if any(not isinstance(kind, str) or not kind.strip() for kind in self.allowed_kinds):
            raise ValueError("hardpoint allowed_kinds must be non-empty strings")


@dataclass(frozen=True)
class LoadoutSelection:
    """One explicit module assignment to a declared hardpoint."""

    hardpoint_id: str
    module_ref: str
    quantity: int = 1

    def __post_init__(self) -> None:
        if not self.hardpoint_id.strip() or not self.module_ref.strip():
            raise ValueError("loadout hardpoint_id and module_ref are required")
        if (
            isinstance(self.quantity, bool)
            or not isinstance(self.quantity, int)
            or self.quantity <= 0
        ):
            raise ValueError("loadout quantity must be a positive integer")


@dataclass(frozen=True)
class PlatformBlueprint:
    blueprint_id: str
    version: str
    platform_family: str
    slots: tuple[tuple[str, str], ...]
    required_capabilities: frozenset[str] = frozenset()
    override_types: tuple[tuple[str, str], ...] = ()
    override_ranges: tuple[tuple[str, float, float], ...] = ()
    mass_limit_kg: float | None = None
    power_budget_kw: float | None = None
    slot_mount_requirements: tuple[tuple[str, str], ...] = ()
    hardpoints: tuple[HardpointContract, ...] = ()

    def __post_init__(self) -> None:
        if (
            not self.blueprint_id.strip()
            or not self.version.strip()
            or not self.platform_family.strip()
        ):
            raise ValueError("blueprint identity and platform_family are required")
        slot_names = [name for name, _ in self.slots]
        if len(slot_names) != len(set(slot_names)):
            raise ValueError("blueprint slots must be unique")
        if any(not name.strip() or not kind.strip() for name, kind in self.slots):
            raise ValueError("blueprint slot names and kinds are required")
        override_names = [name for name, _ in self.override_types]
        if len(override_names) != len(set(override_names)):
            raise ValueError("blueprint override fields must be unique")
        if any(
            kind not in {"float", "int", "string", "boolean"} for _, kind in self.override_types
        ):
            raise ValueError("unsupported blueprint override type")
        range_names = [name for name, _, _ in self.override_ranges]
        if len(range_names) != len(set(range_names)):
            raise ValueError("blueprint override ranges must be unique")
        for name, low, high in self.override_ranges:
            if (
                dict(self.override_types).get(name) not in {"float", "int"}
                or not math.isfinite(low)
                or not math.isfinite(high)
                or low > high
            ):
                raise ValueError(
                    "override range must name an allowlisted field with finite ordered bounds"
                )
        for label, value in (("mass_limit_kg", self.mass_limit_kg), ("power_budget_kw", self.power_budget_kw)):
            object.__setattr__(self, label, _optional_nonnegative_number(value, label))
        object.__setattr__(self, "slot_mount_requirements", tuple((slot, mount) for slot, mount in self.slot_mount_requirements))
        mount_slots = [slot for slot, _ in self.slot_mount_requirements]
        if len(mount_slots) != len(set(mount_slots)):
            raise ValueError("slot mount requirements must be unique")
        if any(slot not in dict(self.slots) or not isinstance(mount, str) or not mount.strip() for slot, mount in self.slot_mount_requirements):
            raise ValueError("slot mount requirements must reference known slots")
        hardpoints = tuple(self.hardpoints)
        if any(not isinstance(item, HardpointContract) for item in hardpoints):
            raise TypeError("hardpoints must contain HardpointContract values")
        if len({item.hardpoint_id for item in hardpoints}) != len(hardpoints):
            raise ValueError("blueprint hardpoints must be unique")
        object.__setattr__(self, "hardpoints", hardpoints)

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
    module_digests: tuple[tuple[str, str], ...] = ()
    native_module_refs: tuple[tuple[str, str], ...] = ()
    module_physical_parameters: tuple[tuple[str, float | None, float | None, tuple[str, ...]], ...] = ()
    loadout: tuple[tuple[str, str, int], ...] = ()
    loadout_module_digests: tuple[tuple[str, str], ...] = ()
    loadout_native_refs: tuple[tuple[str, str], ...] = ()
    loadout_physical_parameters: tuple[
        tuple[str, float | None, float | None, tuple[str, ...], int], ...
    ] = ()

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
            "module_digests": dict(self.module_digests),
            "native_module_refs": dict(self.native_module_refs),
            "module_physical_parameters": [
                {
                    "slot": slot,
                    "mass_kg": mass,
                    "power_draw_kw": power,
                    "mount_classes": list(mounts),
                }
                for slot, mass, power, mounts in self.module_physical_parameters
            ],
            "loadout": [
                {"hardpoint_id": hardpoint, "module_ref": module, "quantity": quantity}
                for hardpoint, module, quantity in self.loadout
            ],
            "loadout_module_digests": dict(self.loadout_module_digests),
            "loadout_native_refs": dict(self.loadout_native_refs),
            "loadout_physical_parameters": [
                {
                    "hardpoint_id": hardpoint,
                    "mass_kg": mass,
                    "power_draw_kw": power,
                    "mount_classes": list(mounts),
                    "quantity": quantity,
                }
                for hardpoint, mass, power, mounts, quantity in self.loadout_physical_parameters
            ],
        }


def _check_override(value: Any, expected: str) -> bool:
    if expected == "float":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )
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
    loadout: Sequence[LoadoutSelection] = (),
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
            errors.append(
                f"platform.module_kind_mismatch:{path}.module_ref:{selection.module_ref}:{module.kind}!={expected_kind}"
            )
            continue
        selected[selection.slot] = module
    missing_slots = sorted(set(expected_slots) - set(selected))
    errors.extend(f"platform.required_slot_missing:modules.{slot}" for slot in missing_slots)
    hardpoints = {item.hardpoint_id: item for item in blueprint.hardpoints}
    selected_loadout: dict[str, tuple[ModuleRecord, int]] = {}
    if loadout and not hardpoints:
        errors.append("platform.loadout_hardpoints_undeclared")
    for index, selection in enumerate(loadout):
        path = f"loadout[{index}]"
        if selection.hardpoint_id in selected_loadout:
            errors.append(
                f"platform.duplicate_hardpoint:{path}.hardpoint_id:{selection.hardpoint_id}"
            )
            continue
        hardpoint = hardpoints.get(selection.hardpoint_id)
        if hardpoint is None:
            errors.append(
                f"platform.unknown_hardpoint:{path}.hardpoint_id:{selection.hardpoint_id}"
            )
            continue
        module = modules.get(selection.module_ref)
        if module is None:
            errors.append(
                f"platform.loadout_module_unknown:{path}.module_ref:{selection.module_ref}"
            )
            continue
        if hardpoint.allowed_kinds and module.kind not in hardpoint.allowed_kinds:
            errors.append(
                f"platform.loadout_kind_mismatch:{path}.module_ref:{selection.module_ref}:{module.kind}"
            )
        if hardpoint.mount_class not in module.mount_classes:
            errors.append(
                f"platform.loadout_mount_class_mismatch:{path}:{hardpoint.mount_class}"
            )
        if hardpoint.capacity_kg is not None:
            if module.mass_kg is None:
                errors.append(f"platform.loadout_physical_metadata_missing:{path}:mass_kg")
            elif module.mass_kg * selection.quantity > hardpoint.capacity_kg:
                errors.append(
                    f"platform.loadout_capacity_exceeded:{path}:"
                    f"{module.mass_kg * selection.quantity}>{hardpoint.capacity_kg}"
                )
        selected_loadout[selection.hardpoint_id] = (module, selection.quantity)
    all_capabilities = frozenset().union(
        *(module.capabilities for module in selected.values()),
        *(module.capabilities for module, _ in selected_loadout.values()),
    )
    missing_capabilities = sorted(blueprint.required_capabilities - all_capabilities)
    errors.extend(
        f"platform.required_capability_missing:capabilities.{capability}"
        for capability in missing_capabilities
    )
    mount_requirements = dict(blueprint.slot_mount_requirements)
    if blueprint.mass_limit_kg is not None:
        missing_mass = sorted(slot for slot, module in selected.items() if module.mass_kg is None)
        errors.extend(f"platform.physical_metadata_missing:modules.{slot}:physical.mass_kg" for slot in missing_mass)
        loadout_missing_mass = sorted(
            hardpoint
            for hardpoint, (module, _) in selected_loadout.items()
            if module.mass_kg is None
        )
        errors.extend(
            f"platform.physical_metadata_missing:loadout.{hardpoint}:physical.mass_kg"
            for hardpoint in loadout_missing_mass
        )
        if not missing_mass and not loadout_missing_mass:
            total_mass_kg = _physical_total(
                [module.mass_kg for _, module in sorted(selected.items())]
                + [module.mass_kg * quantity for module, quantity in selected_loadout.values()]
            )
            if total_mass_kg > blueprint.mass_limit_kg:
                errors.append(
                    f"platform.mass_limit_exceeded:physical.mass_kg:{total_mass_kg}>{blueprint.mass_limit_kg}"
                )
    if blueprint.power_budget_kw is not None:
        missing_power = sorted(slot for slot, module in selected.items() if module.power_draw_kw is None)
        errors.extend(f"platform.physical_metadata_missing:modules.{slot}:physical.power_draw_kw" for slot in missing_power)
        loadout_missing_power = sorted(
            hardpoint
            for hardpoint, (module, _) in selected_loadout.items()
            if module.power_draw_kw is None
        )
        errors.extend(
            f"platform.physical_metadata_missing:loadout.{hardpoint}:physical.power_draw_kw"
            for hardpoint in loadout_missing_power
        )
        if not missing_power and not loadout_missing_power:
            total_power_draw_kw = _physical_total(
                [module.power_draw_kw for _, module in sorted(selected.items())]
                + [module.power_draw_kw * quantity for module, quantity in selected_loadout.values()]
            )
            if total_power_draw_kw > blueprint.power_budget_kw:
                errors.append(
                    f"platform.power_budget_exceeded:physical.power_draw_kw:{total_power_draw_kw}>{blueprint.power_budget_kw}"
                )
    for slot, required_mount in mount_requirements.items():
        module = selected.get(slot)
        if module is not None and required_mount not in module.mount_classes:
            errors.append(
                f"platform.mount_class_mismatch:modules.{slot}:{required_mount}"
            )

    overrides = dict(parameter_overrides or {})
    ranges = {name: (low, high) for name, low, high in blueprint.override_ranges}
    for name, value in overrides.items():
        expected_type = blueprint.override_type(name)
        if expected_type is None:
            errors.append(f"platform.override_not_allowlisted:parameter_overrides.{name}")
        elif not _check_override(value, expected_type):
            errors.append(
                f"platform.override_type_mismatch:parameter_overrides.{name}:{expected_type}"
            )
        elif name in ranges and not ranges[name][0] <= value <= ranges[name][1]:
            errors.append(f"platform.override_out_of_bounds:parameter_overrides.{name}")
    if errors:
        raise PlatformAssemblyError("; ".join(errors))

    normalized_modules = tuple(
        sorted((slot, selected[slot].module_id + "@" + selected[slot].version) for slot in selected)
    )
    normalized_overrides = tuple(sorted(overrides.items()))
    capabilities = tuple(sorted(all_capabilities))
    module_digests = tuple(
        sorted((slot, module.content_digest) for slot, module in selected.items())
    )
    native_module_refs = tuple(
        sorted((slot, module.native_ref) for slot, module in selected.items())
    )
    module_physical_parameters = tuple(
        sorted(
            (
                slot,
                module.mass_kg,
                module.power_draw_kw,
                tuple(sorted(module.mount_classes)),
            )
            for slot, module in selected.items()
        )
    )
    normalized_loadout = tuple(
        sorted(
            (hardpoint, module.module_id + "@" + module.version, quantity)
            for hardpoint, (module, quantity) in selected_loadout.items()
        )
    )
    loadout_module_digests = tuple(
        sorted(
            (hardpoint, module.content_digest)
            for hardpoint, (module, _) in selected_loadout.items()
        )
    )
    loadout_native_refs = tuple(
        sorted(
            (hardpoint, module.native_ref)
            for hardpoint, (module, _) in selected_loadout.items()
        )
    )
    loadout_physical_parameters = tuple(
        sorted(
            (
                hardpoint,
                module.mass_kg,
                module.power_draw_kw,
                tuple(sorted(module.mount_classes)),
                quantity,
            )
            for hardpoint, (module, quantity) in selected_loadout.items()
        )
    )
    identity_payload = {
        "schema_version": SCHEMA_VERSION,
        "assembly_id": assembly_id,
        "blueprint_ref": f"{blueprint.blueprint_id}@{blueprint.version}",
        "platform_family": blueprint.platform_family,
        "modules": normalized_modules,
        "parameter_overrides": normalized_overrides,
        "capabilities": capabilities,
        "module_digests": module_digests,
        "native_module_refs": native_module_refs,
        "module_physical_parameters": module_physical_parameters,
        "loadout": normalized_loadout,
        "loadout_module_digests": loadout_module_digests,
        "loadout_native_refs": loadout_native_refs,
        "loadout_physical_parameters": loadout_physical_parameters,
        "blueprint_contract": {
            "slots": sorted(blueprint.slots),
            "override_types": sorted(blueprint.override_types),
            "override_ranges": sorted(blueprint.override_ranges),
            "required_capabilities": sorted(blueprint.required_capabilities),
            "mass_limit_kg": blueprint.mass_limit_kg,
            "power_budget_kw": blueprint.power_budget_kw,
            "slot_mount_requirements": sorted(blueprint.slot_mount_requirements),
            "hardpoints": [
                {
                    "hardpoint_id": item.hardpoint_id,
                    "mount_class": item.mount_class,
                    "capacity_kg": item.capacity_kg,
                    "allowed_kinds": sorted(item.allowed_kinds),
                }
                for item in sorted(blueprint.hardpoints, key=lambda value: value.hardpoint_id)
            ],
        },
    }
    digest = hashlib.sha256(
        json.dumps(
            identity_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
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
        module_digests=module_digests,
        native_module_refs=native_module_refs,
        module_physical_parameters=module_physical_parameters,
        loadout=normalized_loadout,
        loadout_module_digests=loadout_module_digests,
        loadout_native_refs=loadout_native_refs,
        loadout_physical_parameters=loadout_physical_parameters,
    )


@dataclass(frozen=True)
class LegacyUnitProjection:
    """Explicit adapter to one existing native UnitDefinition shape; no inheritance."""

    blueprint_ref: str
    definition: Mapping[str, Any]
    slot_paths: tuple[tuple[str, str], ...] = ()
    override_paths: tuple[tuple[str, str], ...] = ()
    loadout_paths: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "definition", freeze_json_mapping(self.definition))
        for paths in (self.slot_paths, self.override_paths, self.loadout_paths):
            if len(dict(paths)) != len(paths) or len({path for _, path in paths}) != len(paths):
                raise ValueError("projection paths must be unique")


def lower_to_legacy_unit_definition(
    plan: ResolvedPlatformSpawnPlan,
    projection: LegacyUnitProjection,
    *,
    modules: Mapping[str, ModuleRecord],
) -> dict[str, Any]:
    """Validate all mappings, then return JSON for the existing native loader.

    This is a qualification authoring adapter. Native parsing, capability
    validation and DefaultUnitFactory still decide whether the unit may spawn.
    """
    if projection.blueprint_ref != plan.blueprint_ref:
        raise PlatformAssemblyError("platform.blueprint_version_mismatch")
    document = thaw_json_value(projection.definition)
    slots = dict(projection.slot_paths)
    overrides = dict(projection.override_paths)
    loadout_paths = dict(projection.loadout_paths)
    if set(slots) != {slot for slot, _ in plan.modules}:
        raise PlatformAssemblyError("platform.native_slot_projection_incomplete")
    by_ref = {f"{m.module_id}@{m.version}": m for m in modules.values()}
    for module in modules.values():
        if by_ref[f"{module.module_id}@{module.version}"] != module:
            raise PlatformAssemblyError("platform.native_module_reference_ambiguous")
    physical_by_slot = {entry[0]: entry[1:] for entry in plan.module_physical_parameters}
    if len(physical_by_slot) != len(plan.module_physical_parameters) or set(physical_by_slot) != set(slots):
        raise PlatformAssemblyError("platform.native_module_physical_projection_incomplete")

    def assign(path: str, value: Any) -> None:
        parts = path.split(".")
        target = document
        for part in parts[:-1]:
            if not isinstance(target, dict) or part not in target:
                raise PlatformAssemblyError(f"platform.native_field_unknown:{path}")
            target = target[part]
        if not isinstance(target, dict) or parts[-1] not in target:
            raise PlatformAssemblyError(f"platform.native_field_unknown:{path}")
        target[parts[-1]] = value

    for slot, ref in plan.modules:
        module = by_ref.get(ref)
        if module is None or not module.native_ref or not module.content_digest:
            raise PlatformAssemblyError(
                f"platform.native_module_evidence_missing:modules.{slot}:{ref}"
            )
        if (
            dict(plan.module_digests).get(slot) != module.content_digest
            or dict(plan.native_module_refs).get(slot) != module.native_ref
        ):
            raise PlatformAssemblyError(f"platform.native_module_identity_mismatch:modules.{slot}")
        actual_physical = (module.mass_kg, module.power_draw_kw, tuple(sorted(module.mount_classes)))
        if actual_physical != physical_by_slot[slot]:
            raise PlatformAssemblyError(f"platform.native_module_physical_mismatch:modules.{slot}")
        assign(slots[slot], module.native_ref)
    physical_by_loadout = {
        entry[0]: entry[1:] for entry in plan.loadout_physical_parameters
    }
    if len(physical_by_loadout) != len(plan.loadout_physical_parameters):
        raise PlatformAssemblyError("platform.native_loadout_physical_projection_duplicate")
    for hardpoint, ref, quantity in plan.loadout:
        if hardpoint not in loadout_paths:
            raise PlatformAssemblyError(
                f"platform.native_loadout_projection_missing:{hardpoint}"
            )
        module = by_ref.get(ref)
        if module is None or not module.native_ref or not module.content_digest:
            raise PlatformAssemblyError(
                f"platform.native_loadout_module_evidence_missing:{hardpoint}:{ref}"
            )
        if (
            dict(plan.loadout_module_digests).get(hardpoint) != module.content_digest
            or dict(plan.loadout_native_refs).get(hardpoint) != module.native_ref
        ):
            raise PlatformAssemblyError(
                f"platform.native_loadout_module_identity_mismatch:{hardpoint}"
            )
        expected_physical = physical_by_loadout.get(hardpoint)
        actual_physical = (
            module.mass_kg,
            module.power_draw_kw,
            tuple(sorted(module.mount_classes)),
            quantity,
        )
        if expected_physical != actual_physical:
            raise PlatformAssemblyError(
                f"platform.native_loadout_module_physical_mismatch:{hardpoint}"
            )
        stores = [module.native_ref] * quantity
        assign(loadout_paths[hardpoint], stores[0] if quantity == 1 else stores)
    for name, value in plan.parameter_overrides:
        if name not in overrides:
            raise PlatformAssemblyError(f"platform.native_override_projection_missing:{name}")
        assign(overrides[name], value)
    if not isinstance(document.get("name"), str) or not isinstance(document.get("type"), str):
        raise PlatformAssemblyError("platform.native_unit_identity_missing")
    # Reject invalid JSON before returning anything to a native caller.
    json.dumps(document, allow_nan=False)
    return document


__all__ = [
    "HardpointContract",
    "LoadoutSelection",
    "ModuleRecord",
    "LegacyUnitProjection",
    "ModuleSelection",
    "PlatformAssemblyError",
    "PlatformBlueprint",
    "ResolvedPlatformSpawnPlan",
    "SCHEMA_VERSION",
    "resolve_platform_assembly",
    "lower_to_legacy_unit_definition",
]
