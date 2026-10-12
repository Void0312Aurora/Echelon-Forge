"""Bridge a resolved platform assembly into the maintained typed spawn DTO.

The bridge is deliberately content-side and opt-in.  It turns the already
validated platform blueprint plan into the plain ``ExpandedTypedPlatformRequest``
tree owned by the capability-bundle registry; ``bindings_adapter`` remains the
only module that knows how to construct ``ef_py`` objects.  Native materialization
and the existing ``DefaultUnitFactory`` remain authoritative.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from python.content.capability_bundles.registry import (
    ExpandedCapability,
    ExpandedCapabilityBundle,
    ExpandedResolvedSpawnPlan,
    ExpandedTypedPlatformRequest,
    SpawnPlacement,
)
from python.content.platform_blueprint import (
    LegacyUnitProjection,
    ModuleRecord,
    PlatformAssemblyError,
    PlatformBlueprint,
    ModuleSelection,
    ResolvedPlatformSpawnPlan,
    SCHEMA_VERSION,
    lower_to_legacy_unit_definition,
    resolve_platform_assembly,
)
from python.content.capability_bundles.schema import PLATFORM_CAPABILITY_FAMILY_VOCABULARY
from python.experiment.composition import thaw_json_value


_NATIVE_CAPABILITY_FAMILIES = frozenset(PLATFORM_CAPABILITY_FAMILY_VOCABULARY)


def _field(value: Any, name: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _capability_identity(value: Any) -> tuple[Any, ...]:
    return (
        _field(value, "family"),
        _field(value, "capability_type"),
        _field(value, "implementation_ref"),
        _field(value, "required"),
        _field(value, "supported"),
    )


def validate_factory_resolved_capability_plan(
    expanded: ExpandedResolvedSpawnPlan,
    factory_plan: Any,
) -> None:
    """Compare content lowering with a plan already resolved by the factory.

    The factory remains authoritative. This function only checks the shared
    identity and capability projection that a typed request claims to carry.
    Source-kind and materialization-strategy labels may differ between the
    typed bridge and the factory's maintained projection.
    """

    if not _field(factory_plan, "source_type_name"):
        raise PlatformAssemblyError("platform.factory_plan_source_type_missing")
    if _field(factory_plan, "source_type_name") != expanded.source_type_name:
        raise PlatformAssemblyError("platform.factory_plan_source_type_name_mismatch")
    if _field(factory_plan, "admitted") is not True:
        raise PlatformAssemblyError("platform.factory_plan_not_admitted")
    factory_capabilities = _field(factory_plan, "resolved_capabilities")
    if not isinstance(factory_capabilities, (list, tuple)):
        raise PlatformAssemblyError("platform.factory_plan_capabilities_missing")
    expected_capabilities = tuple(
        sorted(_capability_identity(capability) for capability in expanded.resolved_capabilities)
    )
    actual_capabilities = tuple(sorted(_capability_identity(capability) for capability in factory_capabilities))
    if actual_capabilities != expected_capabilities:
        raise PlatformAssemblyError("platform.factory_plan_capability_semantics_mismatch")


def _module_index(modules: Mapping[str, ModuleRecord]) -> dict[str, ModuleRecord]:
    indexed: dict[str, ModuleRecord] = {}
    for module in modules.values():
        ref = f"{module.module_id}@{module.version}"
        if ref in indexed and indexed[ref] != module:
            raise PlatformAssemblyError(f"platform.native_module_reference_ambiguous:{ref}")
        indexed[ref] = module
    return indexed


def _evidence_refs(
    *,
    plan: ResolvedPlatformSpawnPlan,
    slot: str,
    module: ModuleRecord,
) -> tuple[str, ...]:
    refs = list(module.evidence_refs)
    refs.extend(
        (
            f"platform.blueprint:{plan.blueprint_ref}",
            f"platform.assembly:{plan.assembly_id}",
            f"platform.identity:{plan.identity_digest}",
            f"platform.module:{slot}:{module.module_id}@{module.version}",
            f"platform.module_digest:{slot}:{module.content_digest}",
        )
    )
    return tuple(dict.fromkeys(refs))


def to_expanded_typed_platform_request(
    *,
    plan: ResolvedPlatformSpawnPlan,
    blueprint: PlatformBlueprint,
    modules: Mapping[str, ModuleRecord],
    projection: LegacyUnitProjection,
    source_type_name: str,
    request_id: str,
    placement: SpawnPlacement,
    factory_plan: Any | None = None,
) -> ExpandedTypedPlatformRequest:
    """Project one resolved assembly into the maintained typed request shape.

    Bind the canonical plan to one unchanged legacy definition snapshot. A plan
    that changes that definition must first use legacy lowering and loading;
    typed metadata alone cannot apply module or parameter changes. The caller
    must load this exact source snapshot through the existing native loader.
    These content declarations do not prove that a behavior model executes.
    """

    if not source_type_name.strip():
        raise PlatformAssemblyError("platform.native_source_type_name_required")
    if projection.definition.get("name") != source_type_name:
        raise PlatformAssemblyError("platform.native_source_definition_name_mismatch")
    if not request_id.strip():
        raise PlatformAssemblyError("platform.native_request_id_required")
    expected_blueprint_ref = f"{blueprint.blueprint_id}@{blueprint.version}"
    if plan.blueprint_ref != expected_blueprint_ref:
        raise PlatformAssemblyError("platform.blueprint_version_mismatch")
    if plan.schema_version != SCHEMA_VERSION:
        raise PlatformAssemblyError("platform.schema_version_mismatch")
    if plan.platform_family != blueprint.platform_family:
        raise PlatformAssemblyError("platform.platform_family_mismatch")

    expected_slots = dict(blueprint.slots)
    selected_slots = dict(plan.modules)
    if set(selected_slots) != set(expected_slots):
        raise PlatformAssemblyError("platform.native_slot_cardinality_mismatch")
    indexed_modules = _module_index(modules)

    capabilities: list[ExpandedCapability] = []
    seen_capability_ids: set[str] = set()
    resolved_families: set[str] = set()
    for slot, module_ref in plan.modules:
        module = indexed_modules.get(module_ref)
        if module is None:
            raise PlatformAssemblyError(f"platform.native_module_unknown:{slot}:{module_ref}")
        if module.kind != expected_slots[slot]:
            raise PlatformAssemblyError(
                f"platform.native_module_kind_mismatch:{slot}:{module.kind}!={expected_slots[slot]}"
            )
        if not module.native_ref.strip() or not module.content_digest.strip():
            raise PlatformAssemblyError(f"platform.native_module_evidence_missing:{slot}:{module_ref}")
        if dict(plan.module_digests).get(slot) != module.content_digest:
            raise PlatformAssemblyError(f"platform.native_module_digest_mismatch:{slot}")
        if dict(plan.native_module_refs).get(slot) != module.native_ref:
            raise PlatformAssemblyError(f"platform.native_module_reference_mismatch:{slot}")

        for family in sorted(module.capabilities):
            if family not in _NATIVE_CAPABILITY_FAMILIES:
                raise PlatformAssemblyError(
                    f"platform.native_capability_family_unsupported:{slot}:{family}"
                )
            capability_id = f"{plan.assembly_id}:{slot}:{family}"
            if capability_id in seen_capability_ids:
                raise PlatformAssemblyError(
                    f"platform.native_capability_id_duplicate:{capability_id}"
                )
            seen_capability_ids.add(capability_id)
            resolved_families.add(family)
            capabilities.append(
                ExpandedCapability(
                    capability_id=capability_id,
                    family=family,
                    capability_type=module.kind,
                    implementation_ref=module.native_ref,
                    evidence_refs=_evidence_refs(plan=plan, slot=slot, module=module),
                    required=family in blueprint.required_capabilities,
                    supported=True,
                )
            )

    if resolved_families != set(plan.capabilities):
        raise PlatformAssemblyError("platform.native_capability_set_mismatch")
    if not capabilities:
        raise PlatformAssemblyError("platform.native_capabilities_required")

    canonical_plan = resolve_platform_assembly(
        assembly_id=plan.assembly_id,
        blueprint=blueprint,
        selections=tuple(ModuleSelection(slot, ref) for slot, ref in plan.modules),
        modules=indexed_modules,
        parameter_overrides=dict(plan.parameter_overrides),
    )
    if canonical_plan != plan:
        raise PlatformAssemblyError("platform.native_plan_identity_mismatch")
    lowered = lower_to_legacy_unit_definition(plan, projection, modules=modules)
    if lowered != thaw_json_value(projection.definition):
        raise PlatformAssemblyError("platform.native_definition_projection_mismatch")
    definition_digest = hashlib.sha256(
        json.dumps(
            lowered, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    ).hexdigest()
    request_digest = hashlib.sha256(
        f"{plan.identity_digest}:{definition_digest}".encode("utf-8")
    ).hexdigest()
    capabilities_tuple = tuple(capabilities)
    bundle_id = f"platform.bundle.{request_digest}"
    plan_id = f"platform.spawn.{request_digest}"
    plan_evidence = (
        f"platform.blueprint:{plan.blueprint_ref}",
        f"platform.assembly:{plan.assembly_id}",
        f"platform.identity:{plan.identity_digest}",
        f"platform.definition:{source_type_name}:{definition_digest}",
    )
    bundle = ExpandedCapabilityBundle(
        bundle_id=bundle_id,
        source_type_name=source_type_name,
        capabilities=capabilities_tuple,
        template_evidence_ref=plan_evidence[0],
        evidence_refs=plan_evidence,
        type_name_projection_preserved=False,
        diagnostics_reason="platform_blueprint_to_typed_capability_bundle",
    )
    resolved_plan = ExpandedResolvedSpawnPlan(
        plan_id=plan_id,
        source_request_kind="typed_platform_request",
        source_type_name=source_type_name,
        capability_bundle_id=bundle_id,
        resolved_platform_definition_ref=f"{source_type_name}#{definition_digest}",
        materialization_strategy="resolved_spawn_plan_bridge",
        template_evidence_ref=plan_evidence[0],
        resolution_evidence_ref=plan_evidence[2],
        materialization_evidence_ref="RuntimeFacade.apply_world_setup.maintained_typed_setup",
        evidence_refs=plan_evidence,
        resolved_capabilities=capabilities_tuple,
        type_name_projection_preserved=False,
        admitted=True,
        diagnostics_reason="platform_blueprint_to_native_typed_spawn_plan",
    )
    if factory_plan is not None:
        validate_factory_resolved_capability_plan(resolved_plan, factory_plan)
    return ExpandedTypedPlatformRequest(
        request_id=request_id,
        source_type_name=source_type_name,
        placement=placement,
        capability_bundle=bundle,
        resolved_spawn_plan=resolved_plan,
        facade_evidence_refs=(
            "BatchWorldSetupRequest.typed_platform_spawn_requests",
            "platform_blueprint.native_typed_plan_adapter",
        ),
        type_name_projection_preserved=False,
    )


__all__ = [
    "to_expanded_typed_platform_request",
    "validate_factory_resolved_capability_plan",
]
