"""Content capability bundles: versioned truth-source documents (T11 pilot).

Public API of the content capability-bundle face (this iteration):

- ``schema`` owns the ``t11.content_capability_bundle.v1`` document contract
  and its fail-closed, versioned validation diagnostics.
- ``registry`` owns the G5 registration socket and the validation-first
  ``expand_typed_platform_request`` entry. The registry starts empty;
  importing a family pilot module (``submarine``) is the opt-in.
- ``bindings_adapter`` converts expansion output to ``ef_py`` DTOs and is
  the only module that touches runtime binding shapes (never imported here).

This package is intentionally NOT imported by the maintained default spawn
path (``spawn_unit`` / ``WorldSpawnRequest`` / scenario compiler chain);
that isolation is the rollback shell, pinned by
``tests/content/capability_bundles/test_rollback_shell_guard.py``.
"""

from python.content.capability_bundles.registry import (
    FACADE_EVIDENCE_TYPED_PLATFORM_SPAWN_REQUESTS,
    REJECTION_DUPLICATE_FAMILY_REGISTRATION,
    REJECTION_FAMILY_NOT_REGISTERED,
    RESOLVED_SPAWN_PLAN_BRIDGE_STRATEGY,
    TYPED_PLATFORM_REQUEST_KIND,
    CapabilityBundleFamilyRegistry,
    ExpandedCapability,
    ExpandedCapabilityBundle,
    ExpandedResolvedSpawnPlan,
    ExpandedTypedPlatformRequest,
    SpawnPlacement,
    TypedPlatformRequestExpansion,
    expand_typed_platform_request,
    register_capability_bundle_family,
    registered_capability_bundle_families,
)
from python.content.capability_bundles.schema import (
    CONTENT_CAPABILITY_BUNDLE_SCHEMA_VERSION,
    PLATFORM_CAPABILITY_FAMILY_VOCABULARY,
    CapabilityBundleValidationDiagnostics,
    validate_capability_bundle_document,
)

__all__ = [
    "CONTENT_CAPABILITY_BUNDLE_SCHEMA_VERSION",
    "FACADE_EVIDENCE_TYPED_PLATFORM_SPAWN_REQUESTS",
    "PLATFORM_CAPABILITY_FAMILY_VOCABULARY",
    "REJECTION_DUPLICATE_FAMILY_REGISTRATION",
    "REJECTION_FAMILY_NOT_REGISTERED",
    "RESOLVED_SPAWN_PLAN_BRIDGE_STRATEGY",
    "TYPED_PLATFORM_REQUEST_KIND",
    "CapabilityBundleFamilyRegistry",
    "CapabilityBundleValidationDiagnostics",
    "ExpandedCapability",
    "ExpandedCapabilityBundle",
    "ExpandedResolvedSpawnPlan",
    "ExpandedTypedPlatformRequest",
    "SpawnPlacement",
    "TypedPlatformRequestExpansion",
    "expand_typed_platform_request",
    "register_capability_bundle_family",
    "registered_capability_bundle_families",
    "validate_capability_bundle_document",
]
