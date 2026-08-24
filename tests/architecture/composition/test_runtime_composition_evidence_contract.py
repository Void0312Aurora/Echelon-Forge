from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import jsonschema

from tools.maintenance import runtime_composition_evidence_contract as evidence


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "tests/architecture/composition/fixtures"


def _read(name: str) -> dict:
  return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _set_pointer(value: object, pointer: str, replacement: object) -> None:
  parts = pointer.strip("/").split("/")
  parent = value
  for part in parts[:-1]:
    parent = parent[int(part)] if isinstance(parent, list) else parent[part]
  if isinstance(parent, list):
    parent[int(parts[-1])] = replacement
  else:
    parent[parts[-1]] = replacement


def _inputs() -> tuple[dict, ...]:
  return tuple(
    _read(name)
    for name in (
      "default_runtime_composition_request.v1.json",
      "default_admitted_catalog_lock.v1.json",
      "default_runtime_profile_projection.v1.json",
      "default_backend_provider_request.v1.json",
      "default_compatibility_manifest.resolved.json",
    )
  )


def test_default_evidence_fixture_schema_and_generated_header_are_fresh() -> None:
  actual = _read("default_runtime_composition_evidence.v1.json")
  expected = evidence.build_evidence(*_inputs())
  assert actual == expected
  assert evidence.validate_evidence(actual, *_inputs()) == []
  schema = evidence.evidence_schema()
  jsonschema.Draft202012Validator(schema).validate(actual)
  assert evidence.SCHEMA_PATH.read_text(encoding="utf-8") == evidence._pretty(schema)
  assert evidence.GENERATED_HEADER_PATH.read_text(encoding="utf-8") == evidence.generated_header(
    expected
  )


def test_executable_graph_hash_joins_owner_registry_83_plus_2_plus_34() -> None:
  resolved = _inputs()[-1]
  payload = evidence._graph_payload(resolved)
  assert len(payload["component_contributions"]) == 83
  assert len(payload["kernel_system_contributions"]) == 2
  assert len(payload["resolved_system_contributions"]) == 34
  assert [row["contribution_id"] for row in payload["kernel_system_contributions"]] == [
    "builtin.kernel.system.rwr_reset",
    "builtin.kernel.system.esm_reset",
  ]
  assert evidence.executable_graph_sha256(resolved) == _read(
    "default_runtime_composition_evidence.v1.json"
  )["executable_graph_sha256"]


def test_provider_input_permutation_does_not_change_evidence_identity() -> None:
  request, lock, projection, backend, resolved = _inputs()
  candidate = deepcopy(resolved)
  candidate["manifest"]["providers"].reverse()
  assert evidence.build_evidence(request, lock, projection, backend, candidate) == evidence.build_evidence(
    request, lock, projection, backend, resolved
  )


def test_invalid_evidence_matrix_rejects_every_identity_surface() -> None:
  actual = _read("default_runtime_composition_evidence.v1.json")
  matrix = _read("invalid_runtime_composition_evidence_matrix.v1.json")
  schema_validator = jsonschema.Draft202012Validator(evidence.evidence_schema())
  for case in matrix["cases"]:
    candidate = deepcopy(actual)
    _set_pointer(candidate, case["path"], case["value"])
    issues = evidence.validate_evidence(candidate, *_inputs())
    assert any(issue.code == case["code"] for issue in issues), (case, issues)
    if case["id"] in {"duplicate-scope", "non-ascii-instance", "generation-overflow"}:
      assert list(schema_validator.iter_errors(candidate))


def test_runtime_evidence_generator_has_no_private_catalog_or_runtime_fixture_read() -> None:
  source = evidence.Path(evidence.__file__).read_text(encoding="utf-8").lower()
  assert "node_modules" not in source
  assert "runtime/facade" not in source
  assert "kdefaultprovider" not in source
  assert "tests/architecture/composition/fixtures" in source
  runtime_sources = "\n".join(
    path.read_text(encoding="utf-8").lower()
    for path in (
      REPO_ROOT / "src/runtime/facade/runtime_facade_composition_evidence.cpp",
      REPO_ROOT / "src/runtime/composition/runtime_composition_evidence_contract.cpp",
    )
  )
  assert "tests/architecture" not in runtime_sources
  assert "std::ifstream" not in runtime_sources


def test_host_identity_has_no_binding_selectable_factory_or_passkey() -> None:
  header = (REPO_ROOT / "src/runtime/facade/runtime_facade.h").read_text(encoding="utf-8")
  assert "RuntimeFacadeHostContext" not in header
  assert "RuntimeFacadePythonHostToken" not in header
  assert "make_runtime_facade_for_python" not in header
  assert "mint_runtime_facade_python" not in header
  assert "AttestedHost" not in header
  assert "friend void bind_runtime" not in header


def test_validator_rejects_malformed_world_and_scope_types_without_throwing() -> None:
  actual = _read("default_runtime_composition_evidence.v1.json")

  invalid_world = deepcopy(actual)
  invalid_world["world_instances"][0]["world_index"] = []
  issues = evidence.validate_evidence(invalid_world, *_inputs())
  assert any(issue.code == "evidence.invalid_world_instances" for issue in issues)

  invalid_scope = deepcopy(actual)
  invalid_scope["world_instances"][0]["scope_generations"][0]["scope"] = []
  issues = evidence.validate_evidence(invalid_scope, *_inputs())
  assert any(issue.code == "evidence.invalid_scope_generation" for issue in issues)

  overflow_generation = deepcopy(actual)
  overflow_generation["world_instances"][0]["scope_generations"][0]["generation"] = (
    evidence.MAX_INT64 + 1
  )
  issues = evidence.validate_evidence(overflow_generation, *_inputs())
  assert any(issue.code == "evidence.invalid_scope_generation" for issue in issues)


def test_self_hashed_non_ascii_instance_is_rejected_consistently() -> None:
  candidate = evidence.build_evidence(*_inputs())
  candidate["world_instances"][0]["scope_generations"][0]["instance_id"] = (
    "composition:1/world:0/applicatión"
  )
  candidate = evidence._normalize(candidate)
  candidate["canonical_json"] = evidence.low_level.canonical_json_bytes(
    evidence._payload(candidate)
  ).decode("utf-8")
  candidate["evidence_sha256"] = evidence.low_level.canonical_sha256(
    evidence._payload(candidate)
  )

  issues = evidence.validate_evidence(candidate, *_inputs())
  assert any(issue.code == "evidence.non_ascii_string" for issue in issues)
  assert list(jsonschema.Draft202012Validator(evidence.evidence_schema()).iter_errors(candidate))
