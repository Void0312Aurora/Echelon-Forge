from __future__ import annotations

import pytest

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402

from python.mechanisms import (  # noqa: E402
  MechanismSpec,
  PortSpec,
  compile_mechanism_graph,
  project_stage_manifest_qualification,
)


def _valid_platform_capability() -> object:
  capability = ef_py.PlatformCapability()
  capability.capability_id = "mobility:F-16C_Block50"
  capability.family = "mobility"
  capability.capability_type = "fixed_wing_flight"
  capability.implementation_ref = "DefaultUnitFactory"
  capability.evidence_refs = ["unit_definition:F-16C_Block50"]
  capability.required = True
  capability.supported = True
  return capability


def _valid_capability_bundle(capability: object) -> object:
  bundle = ef_py.CapabilityBundle()
  bundle.bundle_id = "bundle:F-16C_Block50"
  bundle.source_type_name = "F-16C_Block50"
  bundle.capabilities = [capability]
  bundle.template_evidence_ref = "template:F-16C_Block50"
  bundle.evidence_refs = ["content:type_name:F-16C_Block50"]
  bundle.type_name_projection_preserved = True
  return bundle


def _valid_resolved_spawn_plan(capability: object) -> object:
  plan = ef_py.ResolvedPlatformSpawnPlan()
  plan.plan_id = "plan:typed-spawn:lead"
  plan.source_request_kind = "typed_platform_request"
  plan.source_type_name = "F-16C_Block50"
  plan.capability_bundle_id = "bundle:F-16C_Block50"
  plan.resolved_platform_definition_ref = "definition:F-16C_Block50"
  plan.materialization_strategy = "resolved_spawn_plan_bridge"
  plan.template_evidence_ref = "template:F-16C_Block50"
  plan.resolution_evidence_ref = "resolver:type-name"
  plan.materialization_evidence_ref = "materialization:factory-bridge"
  plan.evidence_refs = ["resolved:typed-spawn:lead"]
  plan.resolved_capabilities = [capability]
  plan.type_name_projection_preserved = True
  plan.admitted = True
  return plan


def _valid_typed_platform_spawn_request() -> object:
  capability = _valid_platform_capability()
  request = ef_py.TypedPlatformSpawnRequest()
  request.world_index = 0
  request.side = ef_py.Side.Blue
  request.request_id = "typed-spawn:lead"
  request.source_type_name = "F-16C_Block50"
  request.entity_name = "Lead"
  request.is_agent = True
  request.x = -1400.0
  request.y = 0.0
  request.z = 1200.0
  request.heading = 90.0
  request.vy = 180.0
  request.capability_bundle = _valid_capability_bundle(capability)
  request.resolved_spawn_plan = _valid_resolved_spawn_plan(capability)
  request.facade_evidence_refs = [
    "BatchWorldSetupRequest.typed_platform_spawn_requests"
  ]
  request.type_name_projection_preserved = True
  return request


def test_typed_platform_spawn_dtos_are_python_constructible_and_round_trip() -> None:
  assert hasattr(ef_py, "PlatformCapability")
  assert hasattr(ef_py, "CapabilityBundle")
  assert hasattr(ef_py, "ResolvedPlatformSpawnPlan")
  assert hasattr(ef_py, "TypedPlatformSpawnRequest")
  assert hasattr(ef_py, "TypedPlatformSpawnValidationResult")
  assert hasattr(ef_py, "validate_typed_platform_spawn_request")

  request = _valid_typed_platform_spawn_request()

  assert request.request_id == "typed-spawn:lead"
  assert request.source_type_name == "F-16C_Block50"
  assert request.capability_bundle.bundle_id == "bundle:F-16C_Block50"
  assert request.capability_bundle.source_type_name == "F-16C_Block50"
  assert list(request.capability_bundle.capabilities)[0].family == "mobility"
  assert request.resolved_spawn_plan.source_request_kind == "typed_platform_request"
  assert list(request.facade_evidence_refs) == [
    "BatchWorldSetupRequest.typed_platform_spawn_requests"
  ]

  setup = ef_py.BatchWorldSetupRequest()
  legacy_spawn = ef_py.WorldSpawnRequest()
  legacy_spawn.type_name = "F-16C_Block50"
  setup.spawn_requests = [legacy_spawn]
  setup.typed_platform_spawn_requests = [request]

  assert list(setup.spawn_requests)[0].type_name == "F-16C_Block50"
  assert list(setup.typed_platform_spawn_requests)[0].request_id == "typed-spawn:lead"


def test_valid_typed_platform_spawn_request_validates_in_python() -> None:
  result = ef_py.validate_typed_platform_spawn_request(
    _valid_typed_platform_spawn_request()
  )

  assert bool(result.valid)
  assert not bool(result.fail_closed)
  assert result.rejection_reason == ""
  assert list(result.errors) == []


def test_typed_platform_spawn_request_fails_closed_for_missing_fields() -> None:
  missing_request_id = _valid_typed_platform_spawn_request()
  missing_request_id.request_id = ""

  result = ef_py.validate_typed_platform_spawn_request(missing_request_id)

  assert not bool(result.valid)
  assert bool(result.fail_closed)
  assert result.rejection_reason == "typed_platform_spawn_request_id_required"
  assert "request_id is required" in list(result.errors)

  missing_evidence = _valid_typed_platform_spawn_request()
  missing_evidence.facade_evidence_refs = []

  result = ef_py.validate_typed_platform_spawn_request(missing_evidence)

  assert not bool(result.valid)
  assert bool(result.fail_closed)
  assert result.rejection_reason == "typed_platform_spawn_evidence_required"


@pytest.mark.parametrize("field,value", [
  ("implementation_ref", "drifted"),
  ("capability_type", "drifted"),
  ("family", "sensing"),
  ("requires_capability_ids", ["drifted"]),
  ("evidence_refs", ["drifted"]),
  ("required", False),
])
def test_typed_platform_spawn_request_fails_closed_for_plan_bundle_capability_drift(field, value) -> None:
  request = _valid_typed_platform_spawn_request()
  setattr(request.resolved_spawn_plan.resolved_capabilities[0], field, value)

  result = ef_py.validate_typed_platform_spawn_request(request)

  assert not bool(result.valid)
  assert bool(result.fail_closed)
  assert result.rejection_reason == "typed_platform_spawn_resolved_plan_invalid"
  assert any(
    "preserve source and capability bundle identity" in error
    for error in result.errors
  )


def test_rejected_plan_keeps_its_specific_reason_when_capability_payload_is_not_admitted() -> None:
  request = _valid_typed_platform_spawn_request()
  request.resolved_spawn_plan.admitted = False
  request.resolved_spawn_plan.rejection_reason = "fixture.required_capability_unsupported"
  request.resolved_spawn_plan.resolved_capabilities = []

  result = ef_py.validate_typed_platform_spawn_request(request)

  assert bool(result.valid)
  request.type_name_projection_preserved = False
  request.capability_bundle.type_name_projection_preserved = False
  request.resolved_spawn_plan.type_name_projection_preserved = False
  setup = ef_py.BatchWorldSetupRequest()
  setup.seeds = [123]
  setup.time_steps = [0.05]
  setup.typed_platform_spawn_requests = [request]
  maintained = ef_py.RuntimeFacade(1).apply_world_setup(setup).typed_platform_spawn_results[0]
  assert not bool(maintained.admitted)
  assert not bool(maintained.materialized)
  assert maintained.rejection_reason == "typed_platform_spawn_resolved_plan_invalid"
  assert any(
    "fixture.required_capability_unsupported" in error
    for error in maintained.errors
  )


def test_capabilities_match_by_unique_id_despite_traversal_order() -> None:
  request = _valid_typed_platform_spawn_request()
  mobility = _valid_platform_capability()
  sensing = _valid_platform_capability()
  sensing.capability_id = "sensing:F-16C_Block50"
  sensing.family = "sensing"
  request.capability_bundle.capabilities = [mobility, sensing]
  request.resolved_spawn_plan.resolved_capabilities = [sensing, mobility]

  assert bool(ef_py.validate_typed_platform_spawn_request(request).valid)
  request.resolved_spawn_plan.resolved_capabilities = [mobility, mobility]
  assert not bool(ef_py.validate_typed_platform_spawn_request(request).valid)


def test_legacy_world_spawn_request_type_name_path_remains_python_mainline_surface() -> None:
  legacy_spawn = ef_py.WorldSpawnRequest()
  legacy_spawn.world_index = 0
  legacy_spawn.side = ef_py.Side.Blue
  legacy_spawn.type_name = "DDG-51_Flight_I_USS_Arleigh_Burke"
  legacy_spawn.entity_name = "Burke"
  legacy_spawn.z = 0.0
  legacy_spawn.heading = 90.0
  legacy_spawn.vx = 10.29

  assert legacy_spawn.type_name == "DDG-51_Flight_I_USS_Arleigh_Burke"
  assert not hasattr(legacy_spawn, "source_type_name")
  assert not hasattr(legacy_spawn, "resolved_spawn_plan")


def test_world_batch_exposes_native_factory_resolved_plan_read_only() -> None:
  runtime = ef_py.WorldBatchRuntime(1)
  initial_generation = runtime.batch_generation()
  assert initial_generation > 0
  plan = runtime.resolve_factory_platform_spawn_plan(0, "Aircraft")

  assert plan.admitted
  assert plan.source_type_name == "Aircraft"
  assert plan.type_name_projection_preserved
  assert plan.materialization_strategy == "factory_projection_materialization"
  assert list(plan.resolved_capabilities)

  missing = runtime.resolve_factory_platform_spawn_plan(0, "Missing_Type")
  assert not missing.admitted
  assert missing.rejection_reason == "resolved_platform_spawn_plan_type_name_not_found"
  assert runtime.batch_healthy()
  runtime.reset_batch([31])
  assert runtime.batch_generation() == initial_generation + 1


def test_world_batch_exposes_maintained_native_stage_manifest_snapshot() -> None:
  runtime = ef_py.WorldBatchRuntime(1)
  manifests = runtime.maintained_stage_node_manifests()

  assert len(manifests) >= 3
  assert all(
    manifest.facade_visibility not in {"adapter_projection", "diagnostics_only"}
    for manifest in manifests
  )
  launch = next(manifest for manifest in manifests if manifest.node_id == "fire_control_launch.v1")
  assert launch.owner_module == "src/core/engine/simulation_kernel_weapon_api.cpp"
  assert launch.input_packets
  assert launch.required_barriers
  assert runtime.batch_healthy()


def test_native_stage_manifest_snapshot_projects_without_synthetic_fields() -> None:
  runtime = ef_py.WorldBatchRuntime(1)
  manifests = runtime.maintained_stage_node_manifests()
  selected = manifests[:3]
  graph = compile_mechanism_graph(
    "native-runtime-snapshot-projection",
    {
      manifest.node_id: MechanismSpec(
        f"native.{manifest.node_id}",
        "1",
        outputs=(PortSpec("packet", "NativePacket.v1"),),
        implementation_ref=f"native.{manifest.node_id}",
      )
      for manifest in selected
    },
    (),
  )

  projection = project_stage_manifest_qualification(
    graph,
    node_stage_bindings={manifest.node_id: manifest.node_id for manifest in selected},
    stage_manifests={manifest.node_id: manifest for manifest in selected},
  )

  assert projection.qualification_only
  assert not projection.executable
  assert len(projection.node_contracts) == len(selected)
  assert all("native_system" not in item.owner_contract for item in projection.node_contracts)
