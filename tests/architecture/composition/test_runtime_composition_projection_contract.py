from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from tools.maintenance import runtime_composition_projection_contract as projection
from tools.maintenance import simulation_composition_contract as low_level


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "tests/architecture/composition/fixtures"
REQUEST = FIXTURES / "default_runtime_composition_request.v1.json"
LOCK = FIXTURES / "default_admitted_catalog_lock.v1.json"
MATRIX = FIXTURES / "invalid_projection_matrix.v1.json"
REQUEST_SCHEMA = REPO_ROOT / "src/runtime/contracts/composition/runtime_composition_request.v1.schema.json"
LOCK_SCHEMA = REPO_ROOT / "src/runtime/contracts/composition/admitted_catalog_lock.v1.schema.json"
AUTHORITY_SCHEMA = REPO_ROOT / "src/runtime/contracts/composition/owner_authority_registry.v1.schema.json"
CPP_HEADER = REPO_ROOT / "src/runtime/contracts/runtime_composition_projection_contract.h"
AUTHORITY = FIXTURES / "owner_authority_registry.v1.json"


def _read(path: Path) -> dict:
  return json.loads(path.read_text(encoding="utf-8"))


def _set_pointer(value: dict, pointer: str, replacement: object) -> None:
  parts = pointer.strip("/").split("/")
  parent: object = value
  for part in parts[:-1]:
    parent = parent[int(part)] if isinstance(parent, list) else parent[part]
  if isinstance(parent, list):
    parent[int(parts[-1])] = replacement
  else:
    parent[parts[-1]] = replacement


def test_generated_request_lock_schemas_and_fixtures_are_fresh() -> None:
  request = projection._normalize_request(projection.default_request())
  lock = projection.build_catalog_lock(request, projection.default_entries())
  assert REQUEST_SCHEMA.read_text(encoding="utf-8") == projection._pretty(projection.request_schema())
  assert LOCK_SCHEMA.read_text(encoding="utf-8") == projection._pretty(projection.lock_schema())
  assert AUTHORITY_SCHEMA.read_text(encoding="utf-8") == projection._pretty(projection.authority_registry_schema())
  assert REQUEST.read_text(encoding="utf-8") == projection._pretty(request)
  assert LOCK.read_text(encoding="utf-8") == projection._pretty(lock)
  assert AUTHORITY.read_text(encoding="utf-8") == projection._pretty(projection.default_authority_registry())


def test_request_and_lock_identity_roundtrip() -> None:
  request = _read(REQUEST)
  lock = _read(LOCK)
  authority = _read(AUTHORITY)
  assert projection.validate_request(request) == []
  assert projection.validate_authority_registry(authority) == []
  assert projection.validate_catalog_lock(lock) == []
  assert projection.request_identity(request) == lock["request_sha256"]
  assert projection.catalog_lock_identity(lock) == lock["lock_sha256"]
  assert projection.validate_catalog_lock(lock, request=request) == []

  mismatched = deepcopy(request)
  mismatched["request_id"] = "other.experiment"
  assert any(
    issue.code == "projection.request_identity_mismatch"
    for issue in projection.validate_catalog_lock(lock, request=mismatched)
  )


def test_catalog_lock_is_owner_derived_and_permutation_stable() -> None:
  request = projection.default_request()
  entries = projection.default_entries()
  expected = projection.build_catalog_lock(request, entries)
  reversed_lock = projection.build_catalog_lock(request, list(reversed(entries)))
  assert expected == reversed_lock
  assert {row["category"] for row in expected["category_authorities"]} == set(projection.CATEGORIES)
  for entry in expected["entries"]:
    authority = next(row for row in expected["category_authorities"] if row["category"] == entry["category"])
    assert authority["owner_id"] == entry["owner_id"]


def test_catalog_lock_builder_rejects_owner_authority_forgery() -> None:
  request = projection.default_request()
  forged = deepcopy(projection.default_entries())
  forged[0]["owner_id"] = "owner.attacker"
  forged[0]["descriptor_id"] = "attacker.model"
  forged[0]["implementation_id"] = "attacker.impl"
  try:
    projection.build_catalog_lock(request, forged)
  except projection.ContractError as error:
    assert any(issue.code == "projection.owner_authority_mismatch" for issue in error.issues)
  else:
    raise AssertionError("forged owner authority must fail closed")


def test_catalog_lock_builder_rejects_malformed_entries_without_key_errors() -> None:
  request = projection.default_request()
  malformed = [{"category": "model"}]
  try:
    projection.build_catalog_lock(request, malformed)
  except projection.ContractError as error:
    assert any(issue.code == "projection.invalid_entry" for issue in error.issues)
  else:
    raise AssertionError("malformed catalog entries must fail closed")

  malformed = deepcopy(projection.default_entries()[:1])
  malformed[0]["category"] = []
  try:
    projection.build_catalog_lock(request, malformed)
  except projection.ContractError as error:
    assert any(issue.code == "projection.invalid_entry" for issue in error.issues)
  else:
    raise AssertionError("type-invalid catalog entries must fail closed")


def test_request_bound_lock_requires_complete_categories_and_capabilities() -> None:
  request = projection.default_request()
  partial = projection.build_catalog_lock(request, projection.default_entries())
  partial["entries"] = partial["entries"][:-1]
  assert any(
    issue.code == "projection.missing_category"
    for issue in projection.validate_catalog_lock(partial, request=request)
  )

  missing_capability = projection.build_catalog_lock(request, projection.default_entries())
  system_entry = next(entry for entry in missing_capability["entries"] if entry["category"] == "system")
  system_entry["capabilities"].remove("deterministic.step")
  assert any(
    issue.code == "projection.unmet_capability"
    for issue in projection.validate_catalog_lock(missing_capability, request=request)
  )


def test_native_and_cordis_provenance_require_artifact_hashes() -> None:
  lock = _read(LOCK)
  for artifact_kind in ("native_package", "cordis_package"):
    candidate = deepcopy(lock)
    candidate["entries"][0]["provenance"] = {
      "artifact_kind": artifact_kind,
      "artifact_identity": "package.identity",
      "artifact_sha256": None,
    }
    issues = projection.validate_catalog_lock(candidate)
    assert any(issue.code == "projection.provenance_hash_required" for issue in issues)


def test_catalog_lock_validator_rejects_wrong_scalar_shapes_without_crashing() -> None:
  lock = _read(LOCK)
  lock["entries"][0]["descriptor_id"] = []
  issues = projection.validate_catalog_lock(lock)
  assert any(issue.code == "projection.invalid_identifier" for issue in issues)

  lock = _read(LOCK)
  lock["entries"][0]["capabilities"] = "not-an-array"
  issues = projection.validate_catalog_lock(lock)
  assert any(issue.code == "projection.invalid_json_type" for issue in issues)


def test_request_string_arrays_fail_closed_before_identity_normalization() -> None:
  request = projection.default_request()
  request["required_capabilities"] = ["é", "e\u0301"]
  issues = projection.validate_request(request)
  assert any(issue.code == "projection.invalid_string_value" for issue in issues)
  assert any(issue.code == "projection.duplicate_value" for issue in issues)

  request = projection.default_request()
  request["required_policies"] = [""]
  assert any(issue.code == "projection.invalid_string_value" for issue in projection.validate_request(request))


def test_request_nested_shape_and_configuration_parity_fail_closed() -> None:
  request = projection.default_request()
  request["intent"]["extra"] = True
  assert any(issue.code == "projection.unexpected_field" for issue in projection.validate_request(request))

  request = projection.default_request()
  request["configuration"] = {"label": "é"}
  assert any(issue.code == "projection.invalid_string_value" for issue in projection.validate_request(request))

  request = projection.default_request()
  nested: object = 0
  for _ in range(1200):
    nested = {"nested": nested}
  request["configuration"] = nested
  assert any(issue.code == "projection.configuration_depth_exceeded" for issue in projection.validate_request(request))


def test_authority_registry_rejects_malformed_category_without_crashing() -> None:
  registry = projection.default_authority_registry()
  registry["categories"][0]["category"] = []
  issues = projection.validate_authority_registry(registry)
  assert any(issue.code == "projection.invalid_authority" for issue in issues)


def test_invalid_projection_matrix_fails_closed_with_stable_codes() -> None:
  matrix = _read(MATRIX)
  request_base = _read(REQUEST)
  lock_base = _read(LOCK)
  for case in matrix["cases"]:
    candidate = deepcopy(request_base if case["artifact"] == "request" else lock_base)
    _set_pointer(candidate, case["path"], case["value"])
    issues = (
      projection.validate_request(candidate)
      if case["artifact"] == "request"
      else projection.validate_catalog_lock(candidate)
    )
    assert any(issue.code == case["code"] for issue in issues), (case, issues)


def test_request_contract_is_host_neutral_and_does_not_lower_p1b() -> None:
  schema_text = REQUEST_SCHEMA.read_text(encoding="utf-8").lower()
  assert "node" not in schema_text
  assert "cordis" not in schema_text
  low_level_text = (REPO_ROOT / "tools/maintenance/simulation_composition_contract.py").read_text(
    encoding="utf-8"
  )
  assert "RuntimeCompositionRequest" not in low_level_text
  assert "AdmittedCatalogLock" not in low_level_text
  assert not hasattr(low_level, "lower_runtime_request")


def test_cpp_value_contract_mirrors_projection_identity() -> None:
  header = CPP_HEADER.read_text(encoding="utf-8")
  for token in (
    "kRuntimeCompositionRequestSchemaVersion",
    "kAdmittedCatalogLockSchemaVersion",
    "kOwnerAuthorityRegistrySchemaVersion",
    "kOwnerAuthorityRegistryId",
    "struct RuntimeCompositionRequest",
    "struct AdmittedCatalogEntry",
    "struct AdmittedCatalogLock",
    "kCanonicalizationId",
    "kHashAlgorithm",
  ):
    assert token in header
  assert projection.CANONICALIZATION_ID in header
  assert projection.HASH_ALGORITHM in header
