"""Registration socket and expansion entry for content capability bundles.

Extension is registration (G5): a platform family attaches by calling
``register_capability_bundle_family`` with an expander callable; nothing in
this module special-cases a concrete family. The registry starts empty --
opting in means importing the family's pilot module (for this iteration,
``python.content.capability_bundles.submarine``). The maintained default
path never imports this package, so removing it (and its registrations)
cannot affect ``spawn_unit`` behaviour: that is the rollback shell.

``expand_typed_platform_request`` is validation-first: the versioned schema
diagnostics gate expansion, and an unregistered family fails closed with a
content-level rejection reason carried in the same versioned diagnostics
shape.

Standard library only; no ``ef_py`` import. The expansion output is a plain
dataclass tree mirroring the runtime ``TypedPlatformSpawnRequest`` DTO;
converting it to ``ef_py`` DTOs is owned by ``bindings_adapter``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from python.content.capability_bundles.schema import (
    CapabilityBundleValidationDiagnostics,
    validate_capability_bundle_document,
)

REJECTION_FAMILY_NOT_REGISTERED = "content_capability_bundle_family_not_registered"
REJECTION_DUPLICATE_FAMILY_REGISTRATION = (
    "content_capability_bundle_family_already_registered"
)

# Vocabulary shared with the runtime contracts (WP14-A).
TYPED_PLATFORM_REQUEST_KIND = "typed_platform_request"
RESOLVED_SPAWN_PLAN_BRIDGE_STRATEGY = "resolved_spawn_plan_bridge"
FACADE_EVIDENCE_TYPED_PLATFORM_SPAWN_REQUESTS = (
    "BatchWorldSetupRequest.typed_platform_spawn_requests"
)


@dataclass(frozen=True)
class SpawnPlacement:
    """Kinematic placement for one expansion request (site-provided)."""

    world_index: int = 0
    side: str = "blue"
    entity_name: str = ""
    is_agent: bool = False
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    heading: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0


@dataclass(frozen=True)
class ExpandedCapability:
    capability_id: str
    family: str
    capability_type: str
    implementation_ref: str
    evidence_refs: Tuple[str, ...]
    required: bool = True
    supported: bool = True
    unsupported_reason: str = ""


@dataclass(frozen=True)
class ExpandedCapabilityBundle:
    bundle_id: str
    source_type_name: str
    capabilities: Tuple[ExpandedCapability, ...]
    template_evidence_ref: str
    evidence_refs: Tuple[str, ...]
    type_name_projection_preserved: bool = False
    diagnostics_reason: str = ""


@dataclass(frozen=True)
class ExpandedResolvedSpawnPlan:
    plan_id: str
    source_request_kind: str
    source_type_name: str
    capability_bundle_id: str
    resolved_platform_definition_ref: str
    materialization_strategy: str
    template_evidence_ref: str
    resolution_evidence_ref: str
    materialization_evidence_ref: str
    evidence_refs: Tuple[str, ...]
    resolved_capabilities: Tuple[ExpandedCapability, ...]
    type_name_projection_preserved: bool = False
    admitted: bool = True
    rejection_reason: str = ""
    diagnostics_reason: str = ""


@dataclass(frozen=True)
class ExpandedTypedPlatformRequest:
    """Plain mirror of the runtime ``TypedPlatformSpawnRequest`` DTO."""

    request_id: str
    source_type_name: str
    placement: SpawnPlacement
    capability_bundle: ExpandedCapabilityBundle
    resolved_spawn_plan: ExpandedResolvedSpawnPlan
    facade_evidence_refs: Tuple[str, ...]
    type_name_projection_preserved: bool = False


FamilyExpander = Callable[
    [Mapping[str, Any], str, SpawnPlacement], ExpandedTypedPlatformRequest
]


class CapabilityBundleFamilyRegistry:
    """Fail-fast registration socket for platform-family bundle expanders."""

    def __init__(self) -> None:
        self._expanders: Dict[str, FamilyExpander] = {}

    def register(self, platform_family: str, expander: FamilyExpander) -> None:
        if not isinstance(platform_family, str) or not platform_family.strip():
            raise ValueError("platform_family must be a non-empty string")
        if platform_family in self._expanders:
            raise ValueError(
                f"{REJECTION_DUPLICATE_FAMILY_REGISTRATION}: {platform_family!r}"
            )
        self._expanders[platform_family] = expander

    def registered_families(self) -> Tuple[str, ...]:
        return tuple(sorted(self._expanders))

    def find(self, platform_family: str) -> Optional[FamilyExpander]:
        return self._expanders.get(platform_family)


_DEFAULT_REGISTRY = CapabilityBundleFamilyRegistry()


def register_capability_bundle_family(
    platform_family: str,
    expander: FamilyExpander,
    *,
    registry: Optional[CapabilityBundleFamilyRegistry] = None,
) -> None:
    (registry or _DEFAULT_REGISTRY).register(platform_family, expander)


def registered_capability_bundle_families(
    *, registry: Optional[CapabilityBundleFamilyRegistry] = None
) -> Tuple[str, ...]:
    return (registry or _DEFAULT_REGISTRY).registered_families()


@dataclass
class TypedPlatformRequestExpansion:
    """Result of one validation-first expansion attempt."""

    diagnostics: CapabilityBundleValidationDiagnostics
    request: Optional[ExpandedTypedPlatformRequest] = None
    warnings: List[str] = field(default_factory=list)


def expand_typed_platform_request(
    document: Mapping[str, Any],
    request_id: str,
    placement: SpawnPlacement,
    *,
    registry: Optional[CapabilityBundleFamilyRegistry] = None,
) -> TypedPlatformRequestExpansion:
    """Expand one bundle document into a typed platform request, fail-closed.

    Validation first: schema diagnostics gate the expansion. An unregistered
    ``platform_family`` fails closed (the registry is the G5 opt-in socket).
    """

    diagnostics = validate_capability_bundle_document(document)
    if not diagnostics.valid:
        return TypedPlatformRequestExpansion(diagnostics=diagnostics)

    platform_family = str(document["platform_family"])
    expander = (registry or _DEFAULT_REGISTRY).find(platform_family)
    if expander is None:
        diagnostics.reject(REJECTION_FAMILY_NOT_REGISTERED)
        diagnostics.add_error(
            f"platform_family {platform_family!r} has no registered capability "
            "bundle expander; import the family's pilot module to opt in"
        )
        return TypedPlatformRequestExpansion(diagnostics=diagnostics)

    request = expander(document, request_id, placement)
    return TypedPlatformRequestExpansion(diagnostics=diagnostics, request=request)
