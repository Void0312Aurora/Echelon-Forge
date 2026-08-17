from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import random
import re
import shutil

import pytest

from tests.architecture.helpers import REPO_ROOT, compile_cpp_snippet
from tools.maintenance import simulation_composition_contract as contract


CONTRACT_HEADER = REPO_ROOT / "src/runtime/contracts/simulation_composition_contract.h"
SCHEMA = REPO_ROOT / (
  "src/runtime/contracts/composition/"
  "simulation_composition_manifest.v1.schema.json"
)
FIXTURES = REPO_ROOT / "tests/architecture/composition/fixtures"
REQUESTED = FIXTURES / "default_compatibility_manifest.requested.json"
RESOLVED = FIXTURES / "default_compatibility_manifest.resolved.json"
INVALID_MATRIX = FIXTURES / "invalid_manifest_matrix.v1.json"
SYSTEM_REGISTRATION = REPO_ROOT / "src/core/engine/simulation_kernel_systems.cpp"


def _read_json(path: Path) -> dict:
  return json.loads(path.read_text(encoding="utf-8"))


def _pretty(value: object) -> str:
  return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _pointer_parent(value: object, pointer: str) -> tuple[object, str]:
  parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]
  current = value
  for part in parts[:-1]:
    current = current[int(part)] if isinstance(current, list) else current[part]
  return current, parts[-1]


def _matching_row(rows: list[dict], match: dict) -> dict:
  matches = [row for row in rows if all(row.get(key) == value for key, value in match.items())]
  assert len(matches) == 1, (match, matches)
  return matches[0]


def _apply_invalid_case(base: dict, case: dict) -> dict:
  manifest = deepcopy(base)
  parent, key = _pointer_parent(manifest, case["path"])
  operation = case["operation"]
  if operation == "replace":
    if isinstance(parent, list):
      parent[int(key)] = deepcopy(case["value"])
    else:
      parent[key] = deepcopy(case["value"])
  elif operation == "append_copy":
    assert isinstance(parent, list)
    parent.append(deepcopy(parent[int(key)]))
  elif operation == "remove_matching":
    rows = parent[key]
    row = _matching_row(rows, case["match"])
    rows.remove(row)
  elif operation == "append_matching_copy":
    rows = parent[key]
    rows.append(deepcopy(_matching_row(rows, case["match"])))
  elif operation == "replace_matching_field":
    row = _matching_row(parent[key], case["match"])
    row[case["target_field"]] = deepcopy(case["value"])
  elif operation == "append_matching_field":
    row = _matching_row(parent[key], case["match"])
    row[case["target_field"]].append(deepcopy(case["value"]))
  else:
    raise AssertionError(operation)
  return manifest


def test_generated_schema_and_default_fixtures_are_fresh() -> None:
  requested = contract.normalize_manifest(contract.default_compatibility_manifest())
  assert SCHEMA.read_text(encoding="utf-8") == _pretty(contract.manifest_schema())
  assert REQUESTED.read_text(encoding="utf-8") == _pretty(requested)
  assert RESOLVED.read_text(encoding="utf-8") == _pretty(contract.resolve_manifest(requested))


def test_manifest_schema_is_closed_host_neutral_and_integer_canonical() -> None:
  schema = _read_json(SCHEMA)
  assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
  assert schema["additionalProperties"] is False
  assert set(schema["required"]) == {
    "schema_version",
    "composition_id",
    "contract_versions",
    "requested_profile",
    "plugins",
    "providers",
    "service_bindings",
    "component_contributions",
    "system_contributions",
    "backend_request",
    "scope_policies",
    "reconfiguration_policy",
    "evidence_policy",
    "compatibility_claims",
  }
  canonical_types = {
    branch.get("type")
    for branch in schema["$defs"]["canonical_value"]["oneOf"]
    if isinstance(branch.get("type"), str)
  }
  assert "number" not in canonical_types
  assert "integer" in canonical_types
  serialized = SCHEMA.read_text(encoding="utf-8").lower()
  for forbidden in ("flecs", "napi", "nanobind", "javascript_object", "c++ pointer"):
    assert forbidden not in serialized


def test_cpp_contract_declares_same_versions_services_scopes_and_errors() -> None:
  header = CONTRACT_HEADER.read_text(encoding="utf-8")
  for token in (
    contract.SCHEMA_VERSION,
    contract.RESOLVED_SCHEMA_VERSION,
    contract.COMPOSITION_CONTRACT_VERSION,
    contract.RESOLVER_CONTRACT_VERSION,
    contract.CANONICALIZATION_ID,
    *contract.SCOPE_ORDER,
    *contract.SERVICE_KEYS,
    *contract.ERROR_CODES,
  ):
    assert f'"{token}"' in header
  for declaration in (
    "struct CompositionPluginDescriptor",
    "struct CompositionProviderDescriptor",
    "struct CompositionServiceBinding",
    "struct CompositionSystemContribution",
    "struct SimulationCompositionManifest",
    "struct ResolvedSimulationComposition",
    "constexpr bool can_supply_scope",
  ):
    assert declaration in header
  lowered = header.lower()
  for forbidden in ("#include <flecs", "#include <nlohmann", "node_api", "nanobind"):
    assert forbidden not in lowered


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ is not available on this host")
def test_cpp_contract_header_compiles_as_a_standalone_value_contract() -> None:
  source = r"""
    #include "runtime/contracts/simulation_composition_contract.h"
    int main() {
      using namespace runtime::composition_contracts;
      static_assert(can_supply_scope(CompositionScope::application, CompositionScope::episode));
      static_assert(!can_supply_scope(CompositionScope::episode, CompositionScope::world));
      SimulationCompositionManifest manifest{};
      manifest.schema_version = std::string(kManifestSchemaVersion);
      return manifest.schema_version.empty();
    }
  """
  result = compile_cpp_snippet(source, binary_prefix="simulation_composition_contract")
  assert result.returncode == 0, result.stderr


def test_default_compatibility_fixture_is_valid_and_resolves() -> None:
  requested = _read_json(REQUESTED)
  assert contract.validate_manifest(requested) == []
  resolved = contract.resolve_manifest(requested)
  assert resolved == _read_json(RESOLVED)
  assert len(requested["providers"]) == 11
  assert len(requested["component_contributions"]) == 82
  assert len(requested["system_contributions"]) == 34
  assert len(resolved["provider_construction_order"]) == 11
  assert len(resolved["system_registration_order"]) == 34


def test_default_fixture_tracks_current_component_and_system_registration() -> None:
  requested = _read_json(REQUESTED)
  source = SYSTEM_REGISTRATION.read_text(encoding="utf-8")
  source_without_line_comments = re.sub(r"//[^\n]*", "", source)
  component_names = re.findall(r"ecs\.component<([^>]+)>\(\);", source_without_line_comments)
  assert len(component_names) == 82
  assert set(component_names) == {
    row["component_id"] for row in requested["component_contributions"]
  }

  system_block = source.split("Register Systems IN ORDER", 1)[1]
  system_block = re.sub(r"//[^\n]*", "", system_block)
  system_block = system_block.split("ecs.set<EffectsModelRef>", 1)[0]
  registration_calls = re.findall(
    r"((?:flight_dynamics::)?register_[a-z0-9_]+)\s*\(", system_block
  )
  assert len(registration_calls) == 34
  normalized_calls = [name.replace("::", ".") for name in registration_calls]
  by_factory = {
    row["registration_factory_id"]: row["contribution_id"]
    for row in requested["system_contributions"]
  }
  assert set(normalized_calls) == set(by_factory)
  assert _read_json(RESOLVED)["system_registration_order"] == [
    by_factory[name] for name in normalized_calls
  ]


def test_every_required_service_has_one_explicit_scope_safe_binding() -> None:
  requested = _read_json(REQUESTED)
  providers = {row["provider_id"]: row for row in requested["providers"]}
  systems = {row["contribution_id"]: row for row in requested["system_contributions"]}
  groups: dict[tuple[str, str, str], list[dict]] = {}
  for binding in requested["service_bindings"]:
    groups.setdefault(
      (binding["consumer_kind"], binding["consumer_id"], binding["service_key"]), []
    ).append(binding)
  for provider_id, provider in providers.items():
    for service in provider["required_services"]:
      rows = groups[("provider", provider_id, service)]
      assert len(rows) == 1
      supplier = providers[rows[0]["provider_id"]]
      assert contract._scope_can_supply(supplier["scope"], provider["scope"])
  for system_id, system in systems.items():
    for service in system["required_services"]:
      assert len(groups[("system", system_id, service)]) == 1


def test_resolution_is_permutation_stable() -> None:
  baseline = _read_json(REQUESTED)
  expected = contract.resolve_manifest(baseline)
  list_fields = (
    "plugins",
    "providers",
    "service_bindings",
    "component_contributions",
    "system_contributions",
    "scope_policies",
    "compatibility_claims",
  )
  nested_set_fields = (
    "host_support",
    "required_capabilities",
    "conflicts",
    "offered_services",
    "required_services",
    "after_provider_ids",
    "required_components",
    "provided_components",
    "semantic_stage_ids",
    "executable_node_ids",
    "read_state_shards",
    "write_state_shards",
    "required_barriers",
    "after",
    "before",
  )
  for seed in range(32):
    rng = random.Random(seed)
    candidate = deepcopy(baseline)
    for field in list_fields:
      rng.shuffle(candidate[field])
    for collection in (candidate["plugins"], candidate["providers"], candidate["system_contributions"]):
      for row in collection:
        for field in nested_set_fields:
          if field in row:
            rng.shuffle(row[field])
    rng.shuffle(candidate["backend_request"]["required_capabilities"])
    rng.shuffle(candidate["reconfiguration_policy"]["allowed_barriers"])
    assert contract.resolve_manifest(candidate) == expected


def test_resolved_hash_excludes_only_its_own_field() -> None:
  resolved = _read_json(RESOLVED)
  payload = dict(resolved)
  claimed_hash = payload.pop("resolved_manifest_sha256")
  assert claimed_hash == contract.canonical_sha256(payload)
  assert resolved["requested_manifest_sha256"] == contract.canonical_sha256(
    resolved["manifest"]
  )
  assert re.fullmatch(r"[0-9a-f]{64}", claimed_hash)


def test_invalid_manifest_matrix_fails_closed_with_stable_codes() -> None:
  base = _read_json(REQUESTED)
  matrix = _read_json(INVALID_MATRIX)
  assert matrix["schema_version"] == (
    "echelon_forge.simulation_composition_invalid_matrix.v1"
  )
  assert matrix["base_fixture"] == REQUESTED.name
  assert len(matrix["cases"]) >= 10
  for case in matrix["cases"]:
    candidate = _apply_invalid_case(base, case)
    codes = {issue.code for issue in contract.validate_manifest(candidate)}
    assert case["expected_code"] in codes, (case["case_id"], sorted(codes))
    with pytest.raises(contract.ContractError):
      contract.resolve_manifest(candidate)


def test_scope_hierarchy_and_reconfiguration_policy_are_explicit() -> None:
  requested = _read_json(REQUESTED)
  scopes = requested["scope_policies"]
  assert [row["scope"] for row in scopes] == list(contract.SCOPE_ORDER)
  assert {row["scope"]: row["parent_scope"] for row in scopes} == contract.SCOPE_PARENT
  assert requested["reconfiguration_policy"] == {
    "active_episode_change": "forbidden",
    "allowed_barriers": ["episode_end", "pre_run", "world_rebuild"],
    "truth_affecting_change": "rebuild_scope_generation",
  }


def test_backend_request_is_bound_to_the_semantic_backend_service() -> None:
  requested = _read_json(REQUESTED)
  backend = requested["backend_request"]
  assert backend["backend_profile_id"] == "cpu_exact.reference"
  provider = next(
    row for row in requested["providers"] if row["provider_id"] == backend["provider_id"]
  )
  assert contract.BACKEND_SERVICE_KEY in provider["offered_services"]
  assert "CudaResidentBackend" not in REQUESTED.read_text(encoding="utf-8")
