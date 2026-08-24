from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FACADE = REPO_ROOT / "src/runtime/facade"
FIXTURES = REPO_ROOT / "tests/architecture/composition/fixtures"


def _read(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def _json(path: Path) -> dict:
  return json.loads(_read(path))


def test_facade_routes_default_backend_construction_through_native_provider() -> None:
  facade_source = _read(FACADE / "runtime_facade.cpp")
  facade_header = _read(FACADE / "runtime_facade.h")
  provider_header = _read(FACADE / "internal/world_batch_backend_provider.h")
  provider_source = _read(FACADE / "internal/world_batch_backend_provider.cpp")
  composition_provider_source = _read(
    REPO_ROOT / "src/runtime/providers/default_simulation_provider_catalog.cpp"
  )

  assert "FlecsCpuBackend" not in facade_source
  assert "FlecsCpuBackend" not in facade_header
  assert 'internal/flecs_cpu_backend.h' not in facade_source
  assert 'internal/world_batch_backend_provider.h' in facade_source
  assert "materialize_default_world_batch_backend" in facade_source
  assert "std::make_unique<FlecsCpuBackend>" in provider_source
  assert "world_batch_backend_contracts::kDefaultProviderId" in provider_header
  assert "world_batch_backend_contracts::kDefaultProviderId" in composition_provider_source
  assert 'constexpr std::string_view kBackendProviderId = "builtin.backend.flecs_cpu"' not in (
    composition_provider_source
  )


def test_backend_provider_contract_has_default_and_negative_capability_fixtures() -> None:
  schema = _json(
    REPO_ROOT
    / "src/runtime/contracts/composition/runtime_backend_provider_request.v1.schema.json"
  )
  default = _json(FIXTURES / "default_backend_provider_request.v1.json")
  matrix = _json(FIXTURES / "invalid_backend_provider_request_matrix.v1.json")

  assert schema["$id"] == "echelon_forge.runtime_backend_provider_request.v1"
  assert schema["additionalProperties"] is False
  assert set(schema["required"]) == {
    "schema_version",
    "backend_profile_id",
    "provider_id",
    "provider_implementation_version",
    "required_capabilities",
  }
  assert default == {
    "backend_profile_id": "cpu_exact.reference",
    "provider_id": "builtin.backend.flecs_cpu",
    "provider_implementation_version": "1.0.0",
    "required_capabilities": ["runtime.cpu_exact"],
    "schema_version": "echelon_forge.runtime_backend_provider_request.v1",
  }

  cases = {case["case_id"]: case for case in matrix["cases"]}
  assert {
    "unknown_schema",
    "unknown_profile",
    "diagnostics_profile",
    "gpu_exact_candidate",
    "resident_state_candidate",
    "shadow_compare_candidate",
    "unknown_provider",
    "provider_version_mismatch",
    "capability_required",
    "capability_duplicate",
    "capability_not_admitted",
  } == set(cases)
  assert cases["diagnostics_profile"]["expected_error"] == (
    "backend_provider.profile_not_maintained"
  )
  assert cases["gpu_exact_candidate"]["expected_error"] == (
    "backend_provider.profile_not_maintained"
  )
  assert cases["resident_state_candidate"]["expected_error"] == (
    "backend_provider.profile_not_maintained"
  )
  assert cases["shadow_compare_candidate"]["expected_error"] == (
    "backend_provider.profile_not_maintained"
  )
  assert cases["provider_version_mismatch"]["expected_error"] == (
    "backend_provider.provider_version_mismatch"
  )


def test_backend_provider_header_does_not_depend_on_engine_or_cuda_owners() -> None:
  header = _read(FACADE / "internal/world_batch_backend_provider.h")
  source = _read(FACADE / "internal/world_batch_backend_provider.cpp")

  assert 'core/engine/' not in header
  assert 'cuda_resident' not in header
  assert 'cuda_resident' not in source
  assert "kBackendProfileIdCpuExactReference" in source
  assert "is_maintained_backend_profile" in source


def test_generated_default_backend_request_stays_bound_to_the_resolved_manifest() -> None:
  generator = _read(REPO_ROOT / "tools/maintenance/simulation_composition_contract.py")
  generated = _read(
    REPO_ROOT
    / "src/runtime/contracts/composition/default_compatibility_manifest.v1.generated.h"
  )
  source = _read(FACADE / "internal/world_batch_backend_provider.cpp")

  for token in (
    "kDefaultBackendProfileId",
    "kDefaultBackendProviderId",
    "kDefaultBackendImplementationVersion",
    "kDefaultBackendRequiredCapabilities",
  ):
    assert token in generator
    assert token in generated
  assert "kDefaultBackendProfileId" in source
  assert "kDefaultBackendProviderId" in source
  assert "kDefaultBackendImplementationVersion" in source
  assert "kDefaultBackendRequiredCapabilities" in source
  assert "provider->implementation_version != request.provider_implementation_version" in source
