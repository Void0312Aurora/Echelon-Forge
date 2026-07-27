"""T11 pilot (this iteration): content capability-bundle schema gates.

Pins, without runtime bindings:

1. the versioned validation diagnostics of the
   ``t11.content_capability_bundle.v1`` contract (version token always
   carried; fail-closed rejection vocabulary),
2. the G5 registration socket (fresh registries start empty; duplicate
   registration fails fast; the ``submarine`` family attaches only by
   importing its pilot module),
3. UnitDefinition-level parity: the pilot bundle document declares exactly
   the capability composition the runtime factory would project from the
   reference ``Kilo_Class_MVP`` definition (bounded-submarine derivation),
   field-for-field including evidence-reference order.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from python.content.capability_bundles import (
  CONTENT_CAPABILITY_BUNDLE_SCHEMA_VERSION,
  CapabilityBundleFamilyRegistry,
  SpawnPlacement,
  expand_typed_platform_request,
  registered_capability_bundle_families,
  validate_capability_bundle_document,
)
from python.content.capability_bundles.registry import (
  REJECTION_FAMILY_NOT_REGISTERED,
)
from python.content.capability_bundles.schema import (
  REJECTION_MISSING_BUNDLE_EVIDENCE,
  REJECTION_MISSING_CAPABILITIES,
  REJECTION_MISSING_CAPABILITY_EVIDENCE,
  REJECTION_MISSING_UNSUPPORTED_REASON,
  REJECTION_REQUIRED_TYPE,
  REJECTION_SCHEMA_VERSION_UNSUPPORTED,
  REJECTION_SUPPORTED_TYPE,
  REJECTION_UNSUPPORTED_REASON_TYPE,
  REJECTION_UNSUPPORTED_CAPABILITY_FAMILY,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
BUNDLE_DOCUMENT_PATH = (
  REPO_ROOT
  / "python"
  / "content"
  / "capability_bundles"
  / "data"
  / "submarine"
  / "kilo_class_mvp.bundle.json"
)
REFERENCE_DEFINITION_PATH = (
  REPO_ROOT / "examples" / "config" / "database" / "ships" / "units" / "kilo_class_mvp.json"
)


def _load_bundle_document() -> dict:
  return json.loads(BUNDLE_DOCUMENT_PATH.read_text(encoding="utf-8"))


def _load_reference_definition() -> dict:
  return json.loads(REFERENCE_DEFINITION_PATH.read_text(encoding="utf-8"))


def _placement() -> SpawnPlacement:
  return SpawnPlacement(world_index=0, side="blue", x=1.0, y=2.0, z=0.0)


def test_pilot_bundle_document_validates_with_versioned_diagnostics() -> None:
  diagnostics = validate_capability_bundle_document(_load_bundle_document())

  assert diagnostics.valid
  assert not diagnostics.fail_closed
  assert diagnostics.rejection_reason == ""
  assert diagnostics.errors == []
  assert diagnostics.schema_version == CONTENT_CAPABILITY_BUNDLE_SCHEMA_VERSION
  assert diagnostics.schema_version == "t11.content_capability_bundle.v1"


def test_schema_version_gate_fails_closed_and_still_carries_version_token() -> None:
  document = _load_bundle_document()
  document["schema_version"] = "t11.content_capability_bundle.v999"

  diagnostics = validate_capability_bundle_document(document)

  assert not diagnostics.valid
  assert diagnostics.fail_closed
  assert diagnostics.rejection_reason == REJECTION_SCHEMA_VERSION_UNSUPPORTED
  assert diagnostics.schema_version == CONTENT_CAPABILITY_BUNDLE_SCHEMA_VERSION

  document.pop("schema_version")
  diagnostics = validate_capability_bundle_document(document)
  assert not diagnostics.valid
  assert diagnostics.rejection_reason == REJECTION_SCHEMA_VERSION_UNSUPPORTED


def test_bundle_shape_rejections_reuse_the_wp14a_vocabulary() -> None:
  document = _load_bundle_document()
  document["capabilities"] = []
  diagnostics = validate_capability_bundle_document(document)
  assert not diagnostics.valid
  assert diagnostics.rejection_reason == REJECTION_MISSING_CAPABILITIES

  document = _load_bundle_document()
  document["capabilities"][0]["family"] = "teleportation"
  diagnostics = validate_capability_bundle_document(document)
  assert not diagnostics.valid
  assert diagnostics.rejection_reason == REJECTION_UNSUPPORTED_CAPABILITY_FAMILY

  document = _load_bundle_document()
  document["capabilities"][0]["evidence_refs"] = []
  diagnostics = validate_capability_bundle_document(document)
  assert not diagnostics.valid
  assert diagnostics.rejection_reason == REJECTION_MISSING_CAPABILITY_EVIDENCE

  document = _load_bundle_document()
  document["evidence_refs"] = [" "]
  diagnostics = validate_capability_bundle_document(document)
  assert not diagnostics.valid
  assert diagnostics.rejection_reason == REJECTION_MISSING_BUNDLE_EVIDENCE


@pytest.mark.parametrize("invalid", ["true", 1, None])
def test_required_rejects_non_boolean_json_values(invalid: object) -> None:
  document = _load_bundle_document()
  document["capabilities"][0]["required"] = invalid
  diagnostics = validate_capability_bundle_document(document)
  assert diagnostics.rejection_reason == REJECTION_REQUIRED_TYPE
  assert diagnostics.fail_closed


@pytest.mark.parametrize("invalid", ["false", 0, None])
def test_supported_rejects_non_boolean_json_values(invalid: object) -> None:
  document = _load_bundle_document()
  document["capabilities"][0]["supported"] = invalid
  diagnostics = validate_capability_bundle_document(document)
  assert diagnostics.rejection_reason == REJECTION_SUPPORTED_TYPE
  assert diagnostics.fail_closed


@pytest.mark.parametrize("invalid", [1, 0.0, None, []])
def test_unsupported_reason_rejects_non_string_json_values(invalid: object) -> None:
  document = _load_bundle_document()
  entry = document["capabilities"][0]
  entry["supported"] = False
  entry["unsupported_reason"] = invalid
  diagnostics = validate_capability_bundle_document(document)
  assert diagnostics.rejection_reason == REJECTION_UNSUPPORTED_REASON_TYPE
  assert diagnostics.fail_closed


def test_unsupported_capability_requires_non_blank_reason() -> None:
  document = _load_bundle_document()
  entry = document["capabilities"][0]
  entry["supported"] = False
  entry["unsupported_reason"] = "  "
  diagnostics = validate_capability_bundle_document(document)
  assert diagnostics.rejection_reason == REJECTION_MISSING_UNSUPPORTED_REASON
  assert diagnostics.fail_closed


def test_validated_capability_flags_are_copied_without_coercion() -> None:
  import python.content.capability_bundles.submarine  # noqa: F401

  document = _load_bundle_document()
  entry = document["capabilities"][0]
  entry["required"] = False
  entry["supported"] = False
  entry["unsupported_reason"] = "pilot backend unavailable"
  expansion = expand_typed_platform_request(
    document, "content-typed:strict-flags", _placement()
  )
  assert expansion.diagnostics.valid
  assert expansion.request is not None
  capability = expansion.request.capability_bundle.capabilities[0]
  assert capability.required is False
  assert capability.supported is False
  assert capability.unsupported_reason == "pilot backend unavailable"


def test_registry_is_an_empty_opt_in_socket_until_a_family_registers() -> None:
  fresh = CapabilityBundleFamilyRegistry()
  assert fresh.registered_families() == ()

  expansion = expand_typed_platform_request(
    _load_bundle_document(), "content-typed:unregistered", _placement(), registry=fresh
  )

  assert expansion.request is None
  assert not expansion.diagnostics.valid
  assert expansion.diagnostics.fail_closed
  assert expansion.diagnostics.rejection_reason == REJECTION_FAMILY_NOT_REGISTERED
  assert expansion.diagnostics.schema_version == CONTENT_CAPABILITY_BUNDLE_SCHEMA_VERSION


def test_duplicate_family_registration_fails_fast() -> None:
  fresh = CapabilityBundleFamilyRegistry()
  fresh.register("submarine", lambda document, request_id, placement: None)

  with pytest.raises(ValueError, match="already_registered"):
    fresh.register("submarine", lambda document, request_id, placement: None)


def test_importing_the_submarine_pilot_module_registers_the_family() -> None:
  import python.content.capability_bundles.submarine # noqa: F401

  assert "submarine" in registered_capability_bundle_families()


def test_submarine_expansion_produces_maintained_typed_setup_semantics() -> None:
  import python.content.capability_bundles.submarine # noqa: F401

  expansion = expand_typed_platform_request(
    _load_bundle_document(), "content-typed:kilo", _placement()
  )

  assert expansion.diagnostics.valid
  request = expansion.request
  assert request is not None
  assert request.source_type_name == "Kilo_Class_MVP"
  assert request.resolved_spawn_plan.source_request_kind == "typed_platform_request"
  assert request.resolved_spawn_plan.materialization_strategy == "resolved_spawn_plan_bridge"
  assert request.type_name_projection_preserved is False
  assert request.capability_bundle.type_name_projection_preserved is False
  assert request.resolved_spawn_plan.type_name_projection_preserved is False
  assert request.resolved_spawn_plan.admitted is True
  assert request.capability_bundle.bundle_id == request.resolved_spawn_plan.capability_bundle_id
  assert (
    "BatchWorldSetupRequest.typed_platform_spawn_requests" in request.facade_evidence_refs
  )
  assert len(request.capability_bundle.capabilities) == 6


def test_bundle_document_matches_the_reference_definition_field_for_field() -> None:
  """UnitDefinition-level parity: content truth == factory projection facts."""

  from python.content.capability_bundles.submarine import (
    derive_submarine_capability_bundle_facts,
    make_bundle_id,
    make_capability_id,
    make_definition_ref,
    make_evidence_ref,
  )

  document = _load_bundle_document()
  definition = _load_reference_definition()
  type_name = definition["name"]
  assert document["source_type_name"] == type_name

  facts = derive_submarine_capability_bundle_facts(definition)
  assert facts, "bounded derivation produced no capabilities"

  declared = document["capabilities"]
  assert len(declared) == len(facts)
  for entry, (family, capability_type, evidence_types) in zip(declared, facts):
    assert entry["capability_id"] == make_capability_id(type_name, capability_type)
    assert entry["family"] == family
    assert entry["capability_type"] == capability_type
    assert entry["implementation_ref"] == make_definition_ref(type_name)
    assert entry["evidence_refs"] == [
      make_evidence_ref(type_name, evidence_type) for evidence_type in evidence_types
    ]
    assert entry.get("required", True) is True
    assert entry.get("supported", True) is True

  assert document["bundle_id"] == make_bundle_id(type_name)
  assert document["definition_ref"] == make_definition_ref(type_name)
  assert document["template_evidence_ref"] == make_evidence_ref(type_name, "bundle_template")

  expected_evidence = [
    make_evidence_ref(type_name, "bundle_template"),
    make_evidence_ref(type_name, "definition_snapshot"),
  ]
  for _, _, evidence_types in facts:
    for evidence_type in evidence_types:
      evidence_ref = make_evidence_ref(type_name, evidence_type)
      if evidence_ref not in expected_evidence:
        expected_evidence.append(evidence_ref)
  assert document["evidence_refs"] == expected_evidence


def test_bounded_derivation_fails_closed_outside_the_submarine_family() -> None:
  from python.content.capability_bundles.submarine import (
    derive_submarine_capability_bundle_facts,
  )

  definition = _load_reference_definition()

  wrong_type = copy.deepcopy(definition)
  wrong_type["type"] = "Ship"
  with pytest.raises(ValueError, match="Submarine"):
    derive_submarine_capability_bundle_facts(wrong_type)

  out_of_family = copy.deepcopy(definition)
  out_of_family["airframe"] = {"empty_mass_kg": 1.0}
  with pytest.raises(ValueError, match="outside the bounded submarine"):
    derive_submarine_capability_bundle_facts(out_of_family)


def test_sensor_refs_loader_branch_matches_cpp_presence_and_array_semantics() -> None:
  from python.content.capability_bundles.submarine import (
    derive_submarine_capability_bundle_facts,
  )

  base = {"type": "Submarine", "sensor": {"range_m": 1.0}}

  empty_array = {**base, "sensor_refs": []}
  empty_types = {
    capability_type
    for _, capability_type, _ in derive_submarine_capability_bundle_facts(empty_array)
  }
  assert "sensor_refs" not in empty_types
  assert "inline_sensor" not in empty_types

  non_array = {**base, "sensor_refs": "not-an-array"}
  non_array_types = {
    capability_type
    for _, capability_type, _ in derive_submarine_capability_bundle_facts(non_array)
  }
  assert "sensor_refs" not in non_array_types
  assert "inline_sensor" in non_array_types

  non_empty_array = {**base, "sensor_refs": ["AN/BPS-5"]}
  non_empty_types = {
    capability_type
    for _, capability_type, _ in derive_submarine_capability_bundle_facts(non_empty_array)
  }
  assert "sensor_refs" in non_empty_types
  assert "inline_sensor" not in non_empty_types

  non_string_array = {"type": "Submarine", "sensor": {"range_m": 1.0}, "sensor_refs": [1, None, True]}
  non_string_types = {
    capability_type
    for _, capability_type, _ in derive_submarine_capability_bundle_facts(non_string_array)
  }
  assert "sensor_refs" not in non_string_types
  assert "inline_sensor" not in non_string_types
