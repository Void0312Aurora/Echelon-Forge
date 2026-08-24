from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from tools.maintenance import runtime_profile_projection_contract as profile


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "tests/architecture/composition/fixtures"
SCHEMA = REPO_ROOT / "src/runtime/contracts/composition/runtime_profile_projection.v1.schema.json"


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


def _inputs() -> tuple[dict, dict, dict, dict]:
  return (
    _read("default_runtime_composition_request.v1.json"),
    _read("default_admitted_catalog_lock.v1.json"),
    _read("default_compatibility_manifest.requested.json"),
    _read("default_compatibility_manifest.resolved.json"),
  )


def test_default_profile_projection_fixture_is_owner_derived_and_fresh() -> None:
  request, lock, requested, resolved = _inputs()
  expected = profile.build_profile_projection(request, lock, requested, resolved)
  actual = _read("default_runtime_profile_projection.v1.json")
  assert actual == expected
  assert profile.validate_profile_projection(actual, request, lock, requested, resolved) == []
  assert len(actual["catalog_entries"]) == 6
  assert len(actual["component_contributions"]) == 83
  assert len(actual["system_contributions"]) == 34
  assert actual["required_capabilities"] == ["deterministic.step", "runtime.world_batch.cpu"]
  assert SCHEMA.read_text(encoding="utf-8") == profile._pretty(profile.profile_schema())


def test_profile_projection_identity_is_catalog_permutation_stable() -> None:
  request, lock, requested, resolved = _inputs()
  expected = profile.build_profile_projection(request, lock, requested, resolved)
  permuted_lock = deepcopy(lock)
  permuted_lock["entries"].reverse()
  for entry in permuted_lock["entries"]:
    entry["capabilities"].reverse()
  assert profile.validate_profile_projection(expected, request, permuted_lock, requested, resolved) == []
  assert profile.build_profile_projection(request, permuted_lock, requested, resolved) == expected


def test_profile_name_is_only_an_alias_for_capabilities_and_policies() -> None:
  request, lock, requested, resolved = _inputs()
  candidate = deepcopy(request)
  candidate["requested_profile"]["profile_id"] = "builtin.air_compatibility"
  assert any(
    issue.code == "profile.unadmitted"
    for issue in profile.validate_profile_projection(
      _read("default_runtime_profile_projection.v1.json"), candidate, lock, requested, resolved
    )
  )

  candidate = deepcopy(request)
  candidate["required_capabilities"] = ["domain.air"]
  assert any(
    issue.code == "profile.capability_policy_mismatch"
    for issue in profile.validate_profile_projection(
      _read("default_runtime_profile_projection.v1.json"), candidate, lock, requested, resolved
    )
  )


def test_profile_projection_rejects_catalog_or_execution_graph_forgery() -> None:
  request, lock, requested, resolved = _inputs()
  actual = _read("default_runtime_profile_projection.v1.json")
  matrix = _read("invalid_profile_projection_matrix.v1.json")
  for case in matrix["cases"]:
    candidate = deepcopy(actual)
    _set_pointer(candidate, case["path"], case["value"])
    issues = profile.validate_profile_projection(candidate, request, lock, requested, resolved)
    assert any(issue.code == case["code"] for issue in issues), (case, issues)


def test_profile_projection_has_no_private_host_or_domain_pipeline() -> None:
  source = (REPO_ROOT / "tools/maintenance/runtime_profile_projection_contract.py").read_text(
    encoding="utf-8"
  ).lower()
  assert "node_modules" not in source
  assert "new context" not in source
  assert "air_profile" not in source
  assert "naval_profile" not in source
  assert "ground_profile" not in source
