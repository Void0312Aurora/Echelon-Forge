from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

SIMULATION_KERNEL_HEADER = REPO_ROOT / "src" / "core" / "engine" / "simulation_kernel.h"
WORLD_BATCH_HEADER = REPO_ROOT / "src" / "core" / "engine" / "world_batch_runtime.h"
WORLD_BATCH_SOURCE = REPO_ROOT / "src" / "core" / "engine" / "world_batch_runtime.cpp"
WORLD_BATCH_CONTRACTS = REPO_ROOT / "src" / "runtime" / "contracts" / "world_batch_contracts.h"
RUNTIME_FACADE_HEADER = REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.h"
RUNTIME_FACADE_SOURCE = REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.cpp"
RUNTIME_FACADE_SOURCE_FILES = (
  REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_world_setup.cpp",
  REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_counterfactual.cpp",
  REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_config.cpp",
  REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_query.cpp",
  REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_command_api.cpp",
  REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_execution.cpp",
  REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_packet.cpp",
  REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.cpp",
  REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_internal.h",
)
RUNTIME_FACADE_TYPES = REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade_types.h"
BINDINGS_CORE = REPO_ROOT / "src" / "interfaces" / "python" / "bindings_core.cpp"
BINDINGS_RUNTIME = REPO_ROOT / "src" / "interfaces" / "python" / "bindings_runtime.cpp"
SCENARIO_WORLD_SETUP = REPO_ROOT / "python" / "scenario" / "runtime" / "world_setup.py"
RL_WORLD_BATCH_ADAPTER = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "adapter.py"
EXAMPLES_CONFIG = REPO_ROOT / "examples" / "config"


def _text(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def _runtime_facade_source_text() -> str:
  return "\n".join(path.read_text(encoding="utf-8") for path in RUNTIME_FACADE_SOURCE_FILES)


def test_wp14_boundary_guard_no_public_spawn_platform_surface_exists() -> None:
  for path in (
    SIMULATION_KERNEL_HEADER,
    WORLD_BATCH_HEADER,
    RUNTIME_FACADE_HEADER,
    BINDINGS_CORE,
    BINDINGS_RUNTIME,
    SCENARIO_WORLD_SETUP,
    RL_WORLD_BATCH_ADAPTER,
  ):
    text = _text(path)
    assert "spawn_platform" not in text, (
      "WP14 first slice must not expose a public spawn_platform path; "
      f"found forbidden token in {path.relative_to(REPO_ROOT).as_posix()}"
    )


def test_wp14_boundary_guard_runtime_capabilities_remains_backend_fidelity_only() -> None:
  header = _text(RUNTIME_FACADE_TYPES)
  struct_start = header.index("struct RuntimeCapabilities")
  struct_end = header.index("};", struct_start)
  runtime_capabilities_block = header[struct_start:struct_end]

  for required in (
    "supports_batch_runtime",
    "supports_compiled_episode_controller",
    "supports_gpu_visual",
    "supports_exact_gpu_backend",
    "multi_fidelity_rejection_reason",
  ):
    assert required in runtime_capabilities_block

  for forbidden in (
    "Capability",
    "CapabilityBundle",
    "ResolvedPlatformSpawnPlan",
    "TypedPlatformSpawnRequest",
    "typed_platform_spawn_requests",
    "source_type_name",
    "capability_bundle",
    "resolved_spawn_plan",
    "type_name_projection_preserved",
    "platform capability",
  ):
    assert forbidden not in runtime_capabilities_block, (
      "RuntimeCapabilities must stay reserved for backend/fidelity query fields; "
      f"found platform token {forbidden!r} inside RuntimeCapabilities"
    )

  binding_source = _text(BINDINGS_RUNTIME)
  runtime_caps_binding_start = binding_source.index('nb::class_<RuntimeCapabilities>(m, "RuntimeCapabilities")')
  runtime_batch_config_start = binding_source.index('nb::class_<RuntimeBatchConfig>(m, "RuntimeBatchConfig")')
  runtime_capabilities_binding_block = binding_source[
    runtime_caps_binding_start:runtime_batch_config_start
  ]

  for forbidden in (
    "capability_bundle",
    "resolved_spawn_plan",
    "typed_platform_spawn_requests",
    "source_type_name",
  ):
    assert forbidden not in runtime_capabilities_binding_block, (
      "RuntimeCapabilities Python binding must not grow platform capability fields; "
      f"found {forbidden!r} in RuntimeCapabilities binding block"
    )


def test_wp14_boundary_guard_legacy_type_name_spawn_surfaces_remain_present() -> None:
  kernel_header = _text(SIMULATION_KERNEL_HEADER)
  world_batch_contracts = _text(WORLD_BATCH_CONTRACTS)
  bindings_core = _text(BINDINGS_CORE)
  facade_types = _text(RUNTIME_FACADE_TYPES)

  assert re.search(
    r"flecs::entity\s+spawn_unit\(Side side,\s+const std::string\s*&\s*unit_name,",
    kernel_header,
  )
  assert "std::string type_name;" in world_batch_contracts
  spawn_unit_binding = bindings_core.split('"Spawn a unit by name with orientation and return its Entity ID"', 1)[1]
  spawn_unit_binding = spawn_unit_binding.split('"Spawn a default unit for the given UnitType', 1)[0]
  assert 'nb::arg("side")' in spawn_unit_binding
  assert 'nb::arg("type_name")' in spawn_unit_binding
  assert "std::vector<WorldSpawnRequest> spawn_requests;" in facade_types


def test_wp14_boundary_guard_examples_and_scenario_python_schema_stay_on_legacy_spawn_requests() -> None:
  scenario_world_setup = _text(SCENARIO_WORLD_SETUP)
  adapter = _text(RL_WORLD_BATCH_ADAPTER)

  assert "typed_platform_spawn_requests" not in scenario_world_setup, (
    "Scenario Python setup layer must not migrate to typed_platform_spawn_requests "
    "in the first WP14 slice"
  )
  assert "TypedPlatformSpawnRequest" not in scenario_world_setup
  assert "CapabilityBundle" not in scenario_world_setup
  assert "ResolvedPlatformSpawnPlan" not in scenario_world_setup

  assert "typed_platform_spawn_requests" not in adapter, (
    "RL world-batch adapter must not migrate to typed platform spawn schema "
    "in the first WP14 slice"
  )
  assert "spawn_platform" not in adapter

  for path in EXAMPLES_CONFIG.rglob("*"):
    if not path.is_file():
      continue
    if path.suffix.lower() not in {".json", ".yaml", ".yml", ".md"}:
      continue
    text = _text(path)
    assert "typed_platform_spawn_requests" not in text, (
      "examples/config must stay on the legacy scenario schema in the first WP14 slice; "
      f"found typed platform token in {path.relative_to(REPO_ROOT).as_posix()}"
    )
    assert "spawn_platform" not in text, (
      "examples/config must not introduce spawn_platform schema in the first WP14 slice; "
      f"found forbidden token in {path.relative_to(REPO_ROOT).as_posix()}"
    )


def test_wp20_boundary_guard_typed_platform_spawn_publicization_stays_validation_first() -> None:
  facade_header = _text(RUNTIME_FACADE_HEADER)
  facade_source = _runtime_facade_source_text()
  world_batch_header = _text(WORLD_BATCH_HEADER)
  world_batch_source = _text(WORLD_BATCH_SOURCE)
  facade_types = _text(RUNTIME_FACADE_TYPES)

  assert "std::vector<uint64_t> apply_world_setup_batch(" in facade_header
  assert "const std::vector<WorldSpawnRequest>& requests," in facade_header
  assert "std::vector<WorldSpawnRequest> spawn_requests;" in facade_types
  assert "std::vector<TypedPlatformSpawnRequest> typed_platform_spawn_requests;" in facade_types, (
    "WP20 validation-first publicization must remain additive on BatchWorldSetupRequest "
    "instead of replacing legacy spawn_requests"
  )

  apply_world_setup_block = facade_source[
    facade_source.index("BatchWorldSetupResult RuntimeFacade::apply_world_setup("):
    facade_source.index("void RuntimeFacade::set_pilot_actions_batch(")
  ]
  assert "request.spawn_requests" in apply_world_setup_block
  if "typed_platform_spawn_requests" in apply_world_setup_block:
    for required in (
      "validate_typed_platform_spawn_request",
      "facade_evidence_refs",
      "type_name_projection_preserved",
    ):
      assert required in facade_source, (
        "RuntimeFacade::apply_world_setup may only publicize typed platform spawns "
        "through an explicit validation-first evidence gate; "
        f"missing {required!r}"
      )

  assert re.search(
    r"spawn_units_batch\(\s*const\s+std::vector<WorldSpawnRequest>\s*&\s*requests\s*\)",
    world_batch_source,
  )
  assert "std::uint64_t spawn_typed_platform_unit(" in world_batch_header, (
    "WP22 maintained typed setup promotion requires a batch-owned typed spawn helper "
    "instead of rematerializing maintained requests into WorldSpawnRequest"
  )
  assert "spawn_typed_platform_unit(" in world_batch_source
  assert re.search(
    r"const\s+TypedPlatformSpawnRequest\s*&\s*request",
    world_batch_source,
  )
  assert "request.source_type_name" in world_batch_source
  assert "WorldSpawnRequest legacy" not in world_batch_source, (
    "The batch-owned maintained typed helper must not rebuild a WorldSpawnRequest"
  )


def test_wp14_boundary_guard_additive_dto_validation_stays_fail_closed_without_runtime_gate() -> None:
  world_batch_contracts = _text(WORLD_BATCH_CONTRACTS)

  for token in (
    "validate_typed_platform_spawn_request",
    "typed_platform_spawn_requires_typed_platform_request_kind",
    "typed_platform_spawn_requires_resolved_spawn_plan",
    "typed_platform_spawn_requires_type_name_projection_path",
    "typed_platform_spawn_resolved_plan_invalid",
    "typed_platform_spawn_evidence_required",
  ):
    assert token in world_batch_contracts

  validate_block = world_batch_contracts[
    world_batch_contracts.index("validate_typed_platform_spawn_request("):
    world_batch_contracts.index("struct WorldPilotActionAssignment")
  ]
  for required in (
    "source_type_name",
    "capability_bundle",
    "resolved_spawn_plan",
    "facade_evidence_refs",
    "type_name_projection_preserved",
  ):
    assert required in validate_block, (
      "Typed platform spawn validation must remain declarative and preserve the WP20 "
      f"type-name projection/evidence path; missing {required!r}"
    )
  for forbidden in (
    "spawn_unit(",
    "spawn_units_batch(",
    "apply_world_setup_batch(",
    "SimulationKernel",
    "WorldBatchRuntime",
    "RuntimeFacade",
  ):
    assert forbidden not in validate_block, (
      "Typed platform spawn request validation must stay declarative/fail-closed "
      f"and not materialize runtime behavior; found {forbidden!r}"
    )


def test_wp22_boundary_guard_typed_setup_surface_classifier_distinguishes_maintained_from_type_name_projection() -> None:
  world_batch_contracts = _text(WORLD_BATCH_CONTRACTS)

  for required in (
    "TypedPlatformSetupSurfaceEvidence",
    "classify_typed_platform_spawn_setup_surface",
    "validate_maintained_typed_platform_spawn_request",
    "kTypedPlatformSetupSurfaceMaintainedTypedSetup",
    "kTypedPlatformSetupSurfaceTypeNameProjectionRequest",
    "kTypedPlatformSetupSurfaceMixedTypedProjectionBridge",
    "kTypedPlatformSpawnRejectionMaintainedTypedSetupRequired",
    "kTypedPlatformSpawnRejectionTypeNameProjectionRequest",
    "kTypedPlatformSpawnRejectionMixedSetupSurface",
  ):
    assert required in world_batch_contracts

  classify_block = world_batch_contracts[
    world_batch_contracts.index(
      "classify_typed_platform_spawn_setup_surface("
    ):
    world_batch_contracts.index(
      "validate_typed_platform_spawn_request("
    )
  ]
  for required in (
    "typed_platform_request",
    "type_name_projection",
    "resolved_spawn_plan_bridge",
    "factory_projection_materialization",
    "type_name_projection_preserved",
  ):
    assert required in classify_block, (
      "WP22 typed setup surface evidence must classify maintained typed setup "
      f"separately from type-name projection requests; missing {required!r}"
    )


def test_wp22_boundary_guard_runtime_facade_promotes_maintained_typed_setup_without_type_name_projection_rematerialization() -> None:
  facade_source = _runtime_facade_source_text()

  apply_world_setup_block = facade_source[
    facade_source.index(
      "materialize_type_name_projection_typed_platform_spawn_request("
    ):
    facade_source.index("single_world_counterfactual_setup(")
  ]

  assert "validate_maintained_typed_platform_spawn_request" in apply_world_setup_block
  assert "materialize_maintained_typed_platform_spawn_request" in apply_world_setup_block
  assert "spawn_typed_request_through_maintained_path" in apply_world_setup_block
  assert "RuntimeFacade.apply_world_setup.maintained_typed_setup" in apply_world_setup_block
  assert "RuntimeFacade.apply_world_setup.maintained_typed_materialized" in apply_world_setup_block

  maintained_block = apply_world_setup_block[
    apply_world_setup_block.index(
      "materialize_maintained_typed_platform_spawn_request("
    ):
    apply_world_setup_block.index(
      "materialize_typed_platform_spawn_request("
    )
  ]
  for forbidden in (
    "world_spawn_request_from_type_name_projection",
    "spawn_world_request_through_type_name_projection",
    "RuntimeFacade.apply_world_setup.type_name_projection_materialization",
    "WorldSpawnRequest",
  ):
    assert forbidden not in maintained_block, (
      "Maintained typed setup must not rematerialize through the type-name projection request shape; "
      f"found forbidden marker {forbidden!r}"
    )

  projection_block = apply_world_setup_block[
    apply_world_setup_block.index(
      "materialize_type_name_projection_typed_platform_spawn_request("
    ):
    apply_world_setup_block.index(
      "materialize_maintained_typed_platform_spawn_request("
    )
  ]
  for required in (
    "world_spawn_request_from_type_name_projection",
    "spawn_world_request_through_type_name_projection",
    "RuntimeFacade.apply_world_setup.type_name_projection_materialization",
    "RuntimeFacade.apply_world_setup.type_name_projection_typed_platform_spawn_bridge",
  ):
    assert required in projection_block, (
      "Explicit type_name projection typed setup must retain the named type-name projection bridge; "
      f"missing {required!r}"
    )
