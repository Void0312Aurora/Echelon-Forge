"""Versioned schema and fail-closed validation for content capability bundles.

This module owns the ``t11.content_capability_bundle.v1`` document contract:
a content-side JSON document that declares one platform's capability bundle
as a truth source (T11 pilot, this iteration). Validation is fail-closed and
mirrors the WP14-A capability-bundle rejection vocabulary of
``src/runtime/contracts/platform_capability_contracts.h`` where the checks
coincide, and adds content-level rejection reasons (schema version, platform
family, reference definition) that only exist on the content face.

Every diagnostics object carries the schema version token so consumers can
tell which contract revision produced a rejection.

Standard library only; no ``ef_py`` import.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Mapping, Optional, Sequence, Tuple

CONTENT_CAPABILITY_BUNDLE_SCHEMA_VERSION = "t11.content_capability_bundle.v1"

# The maintained WP14-A capability family vocabulary
# (platform_capability_contracts.h, platform_capability_family_vocabulary()).
PLATFORM_CAPABILITY_FAMILY_VOCABULARY: Tuple[str, ...] = (
    "mobility",
    "sensing",
    "communication",
    "launching",
    "survivability",
    "command",
    "doctrine",
)

# Content-level rejection reasons (new in this contract).
REJECTION_SCHEMA_VERSION_UNSUPPORTED = "content_capability_bundle_schema_version_unsupported"
REJECTION_DOCUMENT_NOT_OBJECT = "content_capability_bundle_document_must_be_object"
REJECTION_PLATFORM_FAMILY_REQUIRED = "content_capability_bundle_platform_family_required"
REJECTION_REFERENCE_DEFINITION_REQUIRED = (
    "content_capability_bundle_reference_definition_required"
)
REJECTION_DEFINITION_REF_REQUIRED = "content_capability_bundle_definition_ref_required"

# Bundle-shape rejection reasons reused verbatim from the WP14-A vocabulary
# so content-face diagnostics stay aligned with the runtime validators.
REJECTION_MISSING_BUNDLE_ID = "platform_capability_bundle_id_required"
REJECTION_MISSING_SOURCE_TYPE_NAME = "platform_capability_bundle_source_type_name_required"
REJECTION_MISSING_CAPABILITIES = "platform_capability_bundle_requires_capabilities"
REJECTION_DUPLICATE_CAPABILITY_ID = "platform_capability_bundle_duplicate_capability_id"
REJECTION_MISSING_TEMPLATE_EVIDENCE = "platform_capability_bundle_template_evidence_required"
REJECTION_MISSING_BUNDLE_EVIDENCE = "platform_capability_bundle_evidence_required"
REJECTION_MISSING_CAPABILITY_ID = "platform_capability_id_required"
REJECTION_MISSING_CAPABILITY_FAMILY = "platform_capability_family_required"
REJECTION_UNSUPPORTED_CAPABILITY_FAMILY = "platform_capability_family_not_maintained"
REJECTION_MISSING_CAPABILITY_TYPE = "platform_capability_type_required"
REJECTION_MISSING_CAPABILITY_EVIDENCE = "platform_capability_evidence_required"


@dataclass
class CapabilityBundleValidationDiagnostics:
    """Fail-closed, versioned validation diagnostics for a bundle document."""

    schema_version: str = CONTENT_CAPABILITY_BUNDLE_SCHEMA_VERSION
    valid: bool = False
    fail_closed: bool = False
    rejection_reason: str = ""
    errors: List[str] = field(default_factory=list)

    def reject(self, reason: str) -> None:
        self.valid = False
        self.fail_closed = True
        if not self.rejection_reason:
            self.rejection_reason = reason

    def add_error(self, error: str) -> None:
        self.errors.append(error)


def _is_blank(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip()


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _contains_blank(values: Sequence[str]) -> bool:
    return any(not item.strip() for item in values)


def _reject(
    diagnostics: CapabilityBundleValidationDiagnostics, reason: str, error: str
) -> CapabilityBundleValidationDiagnostics:
    diagnostics.reject(reason)
    diagnostics.add_error(error)
    return diagnostics


def _validate_capability_entry(
    diagnostics: CapabilityBundleValidationDiagnostics,
    index: int,
    capability: Any,
) -> Optional[CapabilityBundleValidationDiagnostics]:
    label = f"capabilities[{index}]"
    if not isinstance(capability, Mapping):
        return _reject(
            diagnostics,
            REJECTION_MISSING_CAPABILITY_ID,
            f"{label} must be an object",
        )
    if _is_blank(capability.get("capability_id")):
        return _reject(
            diagnostics,
            REJECTION_MISSING_CAPABILITY_ID,
            f"{label}: capability_id is required",
        )
    if _is_blank(capability.get("family")):
        return _reject(
            diagnostics,
            REJECTION_MISSING_CAPABILITY_FAMILY,
            f"{label}: family is required",
        )
    if capability["family"] not in PLATFORM_CAPABILITY_FAMILY_VOCABULARY:
        return _reject(
            diagnostics,
            REJECTION_UNSUPPORTED_CAPABILITY_FAMILY,
            f"{label}: family must be one of the maintained platform capability families",
        )
    if _is_blank(capability.get("capability_type")):
        return _reject(
            diagnostics,
            REJECTION_MISSING_CAPABILITY_TYPE,
            f"{label}: capability_type is required",
        )
    evidence_refs = capability.get("evidence_refs")
    if not _is_string_list(evidence_refs) or not evidence_refs or _contains_blank(evidence_refs):
        return _reject(
            diagnostics,
            REJECTION_MISSING_CAPABILITY_EVIDENCE,
            f"{label}: evidence_refs is required and cannot contain blank entries",
        )
    return None


def validate_capability_bundle_document(
    document: Any,
) -> CapabilityBundleValidationDiagnostics:
    """Validate one content capability-bundle document, fail-closed.

    The rejection order mirrors ``validate_capability_bundle`` in
    ``platform_capability_contracts.h`` for the shared checks; content-level
    checks (schema version, platform family, reference definition) run first
    because they gate which contract the rest of the document is read under.
    """

    diagnostics = CapabilityBundleValidationDiagnostics()

    if not isinstance(document, Mapping):
        return _reject(
            diagnostics,
            REJECTION_DOCUMENT_NOT_OBJECT,
            "capability bundle document must be a JSON object",
        )
    if document.get("schema_version") != CONTENT_CAPABILITY_BUNDLE_SCHEMA_VERSION:
        return _reject(
            diagnostics,
            REJECTION_SCHEMA_VERSION_UNSUPPORTED,
            "schema_version must be "
            f"{CONTENT_CAPABILITY_BUNDLE_SCHEMA_VERSION!r}, "
            f"got {document.get('schema_version')!r}",
        )
    if _is_blank(document.get("platform_family")):
        return _reject(
            diagnostics,
            REJECTION_PLATFORM_FAMILY_REQUIRED,
            "platform_family is required",
        )
    if _is_blank(document.get("reference_definition_path")):
        return _reject(
            diagnostics,
            REJECTION_REFERENCE_DEFINITION_REQUIRED,
            "reference_definition_path is required",
        )
    if _is_blank(document.get("definition_ref")):
        return _reject(
            diagnostics,
            REJECTION_DEFINITION_REF_REQUIRED,
            "definition_ref is required",
        )
    if _is_blank(document.get("bundle_id")):
        return _reject(diagnostics, REJECTION_MISSING_BUNDLE_ID, "bundle_id is required")
    if _is_blank(document.get("source_type_name")):
        return _reject(
            diagnostics,
            REJECTION_MISSING_SOURCE_TYPE_NAME,
            "source_type_name is required",
        )

    capabilities = document.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        return _reject(
            diagnostics,
            REJECTION_MISSING_CAPABILITIES,
            "capabilities cannot be empty",
        )
    capability_ids = [
        capability.get("capability_id")
        for capability in capabilities
        if isinstance(capability, Mapping) and not _is_blank(capability.get("capability_id"))
    ]
    if len(capability_ids) != len(set(capability_ids)):
        return _reject(
            diagnostics,
            REJECTION_DUPLICATE_CAPABILITY_ID,
            "capability identifiers must be unique within a bundle",
        )
    if _is_blank(document.get("template_evidence_ref")):
        return _reject(
            diagnostics,
            REJECTION_MISSING_TEMPLATE_EVIDENCE,
            "template_evidence_ref is required",
        )
    evidence_refs = document.get("evidence_refs")
    if not _is_string_list(evidence_refs) or not evidence_refs or _contains_blank(evidence_refs):
        return _reject(
            diagnostics,
            REJECTION_MISSING_BUNDLE_EVIDENCE,
            "evidence_refs is required and cannot contain blank entries",
        )

    for index, capability in enumerate(capabilities):
        rejected = _validate_capability_entry(diagnostics, index, capability)
        if rejected is not None:
            return rejected

    diagnostics.valid = True
    return diagnostics
