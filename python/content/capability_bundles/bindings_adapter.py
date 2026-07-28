"""Adapter: ExpandedTypedPlatformRequest -> ``ef_py`` runtime DTOs.

Kept separate from the content-face modules so that the content package
stays standard-library only (importing ``python.content.capability_bundles``
never pulls the runtime bindings). The ``ef_py`` module object is passed in
by the caller, which keeps this module import-clean too and makes the
conversion a pure function of its inputs.
"""

from __future__ import annotations

from typing import Any

from python.content.capability_bundles.registry import (
    ExpandedCapability,
    ExpandedCapabilityBundle,
    ExpandedResolvedSpawnPlan,
    ExpandedTypedPlatformRequest,
)

_SIDE_TOKENS = ("blue", "red")


def _to_side(ef_py: Any, side: str) -> Any:
    token = side.strip().lower()
    if token == "blue":
        return ef_py.Side.Blue
    if token == "red":
        return ef_py.Side.Red
    raise ValueError(f"side must be one of {_SIDE_TOKENS}, got {side!r}")


def _to_capability(ef_py: Any, capability: ExpandedCapability) -> Any:
    dto = ef_py.PlatformCapability()
    dto.capability_id = capability.capability_id
    dto.family = capability.family
    dto.capability_type = capability.capability_type
    dto.implementation_ref = capability.implementation_ref
    dto.evidence_refs = list(capability.evidence_refs)
    dto.required = capability.required
    dto.supported = capability.supported
    dto.unsupported_reason = capability.unsupported_reason
    return dto


def _to_capability_bundle(ef_py: Any, bundle: ExpandedCapabilityBundle) -> Any:
    dto = ef_py.CapabilityBundle()
    dto.bundle_id = bundle.bundle_id
    dto.source_type_name = bundle.source_type_name
    dto.capabilities = [
        _to_capability(ef_py, capability) for capability in bundle.capabilities
    ]
    dto.template_evidence_ref = bundle.template_evidence_ref
    dto.evidence_refs = list(bundle.evidence_refs)
    dto.type_name_projection_preserved = bundle.type_name_projection_preserved
    dto.diagnostics_reason = bundle.diagnostics_reason
    return dto


def _to_resolved_spawn_plan(ef_py: Any, plan: ExpandedResolvedSpawnPlan) -> Any:
    dto = ef_py.ResolvedPlatformSpawnPlan()
    dto.plan_id = plan.plan_id
    dto.source_request_kind = plan.source_request_kind
    dto.source_type_name = plan.source_type_name
    dto.capability_bundle_id = plan.capability_bundle_id
    dto.resolved_platform_definition_ref = plan.resolved_platform_definition_ref
    dto.materialization_strategy = plan.materialization_strategy
    dto.template_evidence_ref = plan.template_evidence_ref
    dto.resolution_evidence_ref = plan.resolution_evidence_ref
    dto.materialization_evidence_ref = plan.materialization_evidence_ref
    dto.evidence_refs = list(plan.evidence_refs)
    dto.resolved_capabilities = [
        _to_capability(ef_py, capability) for capability in plan.resolved_capabilities
    ]
    dto.type_name_projection_preserved = plan.type_name_projection_preserved
    dto.admitted = plan.admitted
    dto.rejection_reason = plan.rejection_reason
    dto.diagnostics_reason = plan.diagnostics_reason
    return dto


def to_typed_platform_spawn_request(
    ef_py: Any, expanded: ExpandedTypedPlatformRequest
) -> Any:
    """Convert one expanded request into an ``ef_py.TypedPlatformSpawnRequest``."""

    placement = expanded.placement
    request = ef_py.TypedPlatformSpawnRequest()
    request.world_index = placement.world_index
    request.side = _to_side(ef_py, placement.side)
    request.request_id = expanded.request_id
    request.source_type_name = expanded.source_type_name
    request.entity_name = placement.entity_name
    request.is_agent = placement.is_agent
    request.x = placement.x
    request.y = placement.y
    request.z = placement.z
    request.heading = placement.heading
    request.pitch = placement.pitch
    request.roll = placement.roll
    request.vx = placement.vx
    request.vy = placement.vy
    request.vz = placement.vz
    request.capability_bundle = _to_capability_bundle(ef_py, expanded.capability_bundle)
    request.resolved_spawn_plan = _to_resolved_spawn_plan(
        ef_py, expanded.resolved_spawn_plan
    )
    request.facade_evidence_refs = list(expanded.facade_evidence_refs)
    request.type_name_projection_preserved = expanded.type_name_projection_preserved
    return request
