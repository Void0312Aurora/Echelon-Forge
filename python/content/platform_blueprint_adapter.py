"""Bridge a resolved platform assembly into the maintained typed spawn DTO.

The bridge is deliberately content-side and opt-in.  It turns the already
validated platform blueprint plan into the plain ``ExpandedTypedPlatformRequest``
tree owned by the capability-bundle registry; ``bindings_adapter`` remains the
only module that knows how to construct ``ef_py`` objects.  Native materialization
and the existing ``DefaultUnitFactory`` remain authoritative.
"""

from __future__ import annotations

from typing import Mapping

from python.content.capability_bundles.registry import (
    ExpandedCapability,
    ExpandedCapabilityBundle,
    ExpandedResolvedSpawnPlan,
    ExpandedTypedPlatformRequest,
    SpawnPlacement,
)
from python.content.platform_blueprint import (
    ModuleRecord,
    PlatformAssemblyError,
    PlatformBlueprint,
    ResolvedPlatformSpawnPlan,
)


_NATIVE_CAPABILITY_FAMILIES = frozenset(
    {
        "mobility",
        "sensing",
        "communication",
        "launching",
        "survivability",
        "command",
        "doctrine",
    }
)


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
    source_type_name: str,
    request_id: str,
    placement: SpawnPlacement,
) -> ExpandedTypedPlatformRequest:
    """Project one resolved assembly into the maintained typed request shape.

    The checks here are the last content-side checks before native publication:
    slot cardinality, module digest/reference identity, and the native capability
    family vocabulary.  The function does not load content or create entities.
    """

    if not source_type_name.strip():
        raise PlatformAssemblyError("platform.native_source_type_name_required")
    if not request_id.strip():
        raise PlatformAssemblyError("platform.native_request_id_required")
    expected_blueprint_ref = f"{blueprint.blueprint_id}@{blueprint.version}"
    if plan.blueprint_ref != expected_blueprint_ref:
        raise PlatformAssemblyError("platform.blueprint_version_mismatch")

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
        if not module.native_ref or not module.content_digest:
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

    capabilities_tuple = tuple(capabilities)
    bundle_id = f"platform.bundle.{plan.identity_digest}"
    plan_id = f"platform.spawn.{plan.identity_digest}"
    plan_evidence = (
        f"platform.blueprint:{plan.blueprint_ref}",
        f"platform.assembly:{plan.assembly_id}",
        f"platform.identity:{plan.identity_digest}",
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
        resolved_platform_definition_ref=f"{plan.blueprint_ref}#{plan.assembly_id}",
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


__all__ = ["to_expanded_typed_platform_request"]
