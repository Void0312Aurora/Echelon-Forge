from __future__ import annotations

import copy

import pytest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.scenario.compiler import ScenarioCompiler, _SURFACE_TYPE_MAP # noqa: E402
from python.scenario.environment_substrate import ( # noqa: E402
  ENVIRONMENT_SUBSTRATE_ENVIRONMENT_KEY,
  ENVIRONMENT_SUBSTRATE_INGESTION_EVIDENCE_KEY,
  ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_PAYLOADS_KEY,
  EnvironmentComponent,
  EnvironmentManifest,
  build_deterministic_environment_fixture,
  build_world_zone_projection_setup_payload,
  canonical_environment_bytes,
  ingest_projection_setup_payloads_into_scenario,
  project_manifest_to_compatibility_setup,
  validate_environment_manifest,
)


def _fixture() -> EnvironmentManifest:
  manifest = build_deterministic_environment_fixture()
  assert validate_environment_manifest(manifest).valid
  return manifest


def _manifest_from_metadata(metadata: dict) -> EnvironmentManifest:
  return EnvironmentManifest(**copy.deepcopy(metadata))


def _payload() -> dict:
  result = build_world_zone_projection_setup_payload(
    _fixture(),
    profile_id="terrain-rect-surface-v1",
  )
  assert result.valid
  assert result.payload is not None
  return result.payload.to_metadata()


def _scenario_with_projection_payload(payload: dict) -> dict:
  return {
    "scenario_name": "environment_substrate_projection_ingestion_test",
    "environment": {
      "time_step": 0.05,
      "max_steps": 10,
      "terrain_type": "flat",
      "wind": {
        "speed_mps": 0.0,
        "dir_from_deg": 0.0,
        "shear_mps_per_km": 0.0,
      },
      ENVIRONMENT_SUBSTRATE_ENVIRONMENT_KEY: {
        ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_PAYLOADS_KEY: [payload],
      },
    },
    "mission_command": {
      "command_code": 0,
      "target_heading": 0.0,
      "target_altitude": 0.0,
      "target_speed": 0.0,
    },
    "entities": [],
    "objectives": [],
    "rewards": {"survival": 0.0},
  }


def test_g0_j_projection_contract_emits_explicit_world_zone_evidence() -> None:
  fixture = build_deterministic_environment_fixture()

  projection = project_manifest_to_compatibility_setup(
    fixture,
    profile_id="terrain-rect-surface-v1",
  )

  assert projection.valid
  assert not projection.fail_closed
  assert projection.rejection_reason == ""
  assert len(projection.zones) == 1
  assert projection.zones[0].source_object_id == "envobj:test-hardstand"
  assert projection.zones[0].surface == "Concrete"
  assert projection.evidence is not None
  assert projection.evidence.no_held_capability_release
  assert projection.evidence.source_object_ids == ("envobj:test-hardstand",)
  assert projection.evidence.dropped_attributes == ()


def test_g0_j_projection_rejects_rich_components_without_dropped_attribute_permission() -> None:
  metadata = build_deterministic_environment_fixture().to_metadata()
  metadata["objects"][0]["components"].append(
    {
      "component_id": "component:test-hardstand-road-network",
      "family": "network",
      "schema_version": "1",
      "attributes": {
        "width_m": 6.0,
        "connectivity": "local_track",
        "surface_class": "concrete",
      },
    }
  )
  manifest = _manifest_from_metadata(metadata)

  projection = project_manifest_to_compatibility_setup(
    manifest,
    profile_id="terrain-rect-surface-v1",
  )

  assert not projection.valid
  assert projection.fail_closed
  assert (
    projection.rejection_reason
    == "environment_substrate_dropped_attribute_without_permission"
  )
  assert "network" in projection.errors[0]


def test_g0_j_projection_rejects_misspelled_surface_type_instead_of_defaulting() -> None:
  metadata = build_deterministic_environment_fixture().to_metadata()
  metadata["objects"][0]["components"][0]["attributes"] = {"surface_type": "Concrete"}
  manifest = _manifest_from_metadata(metadata)

  projection = project_manifest_to_compatibility_setup(
    manifest,
    profile_id="terrain-rect-surface-v1",
  )

  assert not projection.valid
  assert projection.fail_closed
  assert (
    projection.rejection_reason
    == "environment_substrate_missing_required_component_attribute"
  )


def test_g0_j_projection_rejects_non_rect_geometry_for_world_zone_target() -> None:
  metadata = build_deterministic_environment_fixture().to_metadata()
  metadata["objects"][0]["geometry"] = {
    "geometry_type": "polygon",
    "coordinates": {
      "points": [
        [0.0, 0.0],
        [100.0, 0.0],
        [100.0, 100.0],
        [0.0, 100.0],
      ]
    },
  }
  manifest = _manifest_from_metadata(metadata)

  projection = project_manifest_to_compatibility_setup(
    manifest,
    profile_id="terrain-rect-surface-v1",
  )

  assert not projection.valid
  assert projection.fail_closed
  assert projection.rejection_reason == "environment_substrate_unsupported_geometry"


def test_g0_j_projection_rejects_unreleased_runtime_targets() -> None:
  metadata = build_deterministic_environment_fixture().to_metadata()
  metadata["projection_profiles"][0]["target"] = "weather_runtime"
  manifest = _manifest_from_metadata(metadata)

  projection = project_manifest_to_compatibility_setup(
    manifest,
    profile_id="terrain-rect-surface-v1",
  )

  assert not projection.valid
  assert projection.fail_closed
  assert projection.rejection_reason == "environment_substrate_unsupported_target_field"


def test_g0_l_world_zone_projection_setup_payload_is_deterministic_and_inert() -> None:
  manifest = _fixture()

  result_a = build_world_zone_projection_setup_payload(
    manifest,
    profile_id="terrain-rect-surface-v1",
  )
  result_b = build_world_zone_projection_setup_payload(
    manifest,
    profile_id="terrain-rect-surface-v1",
  )

  assert result_a.valid
  assert not result_a.fail_closed
  assert result_a.payload is not None
  assert canonical_environment_bytes(result_a.to_metadata()) == canonical_environment_bytes(
    result_b.to_metadata()
  )
  payload = result_a.payload.to_metadata()
  assert payload["target"] == "world_zone_definition"
  assert payload["no_held_capability_release"] is True
  assert payload["zones"] == [
    {
      "name": "catalog:port_hardstand",
      "x": 250.0,
      "y": -125.0,
      "width": 80.0,
      "length": 140.0,
      "heading": 15.0,
      "surface": "Concrete",
    }
  ]
  assert payload["zone_evidence"][0]["source_manifest_id"] == manifest.manifest_id
  assert payload["zone_evidence"][0]["source_object_id"] == "envobj:test-hardstand"
  assert payload["zone_evidence"][0]["catalog_ref"] == "catalog:port_hardstand"
  assert payload["zone_evidence"][0]["component_ids"] == [
    "component:test-hardstand-surface"
  ]
  assert "world_index" not in payload["zones"][0]


def test_g0_l_projection_setup_rejects_unknown_profile_before_payload_creation() -> None:
  result = build_world_zone_projection_setup_payload(
    _fixture(),
    profile_id="terrain-zone-missing",
  )

  assert not result.valid
  assert result.fail_closed
  assert result.payload is None
  assert result.rejection_reason == "environment_substrate_unknown_projection_profile"


def test_g0_l_projection_setup_rejects_invalid_runtime_surface_code() -> None:
  metadata = _fixture().to_metadata()
  metadata["projection_profiles"][0]["surface_code_mapping"]["Concrete"] = "Mud"
  manifest = EnvironmentManifest(**metadata)

  result = build_world_zone_projection_setup_payload(
    manifest,
    profile_id="terrain-rect-surface-v1",
  )

  assert not result.valid
  assert result.fail_closed
  assert result.payload is None
  assert (
    result.rejection_reason
    == "environment_substrate_projection_invalid_surface_code"
  )


def test_g0_l_projection_setup_rejects_dropped_rich_attributes_even_when_recorded() -> None:
  metadata = _fixture().to_metadata()
  metadata["projection_profiles"][0]["dropped_attribute_policy"] = "record"
  metadata["objects"][0]["components"].append(
    EnvironmentComponent(
      component_id="component:test-hardstand-network",
      family="network",
      attributes={
        "width_m": 5.0,
        "connectivity": "local",
        "surface_class": "hardstand",
      },
    ).to_metadata()
  )
  manifest = EnvironmentManifest(**metadata)

  result = build_world_zone_projection_setup_payload(
    manifest,
    profile_id="terrain-rect-surface-v1",
  )

  assert not result.valid
  assert result.fail_closed
  assert result.payload is None
  assert (
    result.rejection_reason
    == "environment_substrate_projection_derived_product_forbidden"
  )


def test_g0_l_projection_setup_rejects_held_runtime_claims_through_manifest_validation() -> None:
  metadata = _fixture().to_metadata()
  metadata["capability_claims"] = ["movement"]
  manifest = EnvironmentManifest(**metadata)

  result = build_world_zone_projection_setup_payload(
    manifest,
    profile_id="terrain-rect-surface-v1",
  )

  assert not result.valid
  assert result.fail_closed
  assert result.payload is None
  assert result.rejection_reason == "environment_substrate_held_capability_claim"


def test_g0_l_f_ingests_projection_payload_before_layout_metadata() -> None:
  scenario = _scenario_with_projection_payload(_payload())

  compiled = ScenarioCompiler.compile_data(scenario)

  env_cfg = compiled.merged_scenario_data["environment"]
  substrate_cfg = env_cfg[ENVIRONMENT_SUBSTRATE_ENVIRONMENT_KEY]
  assert ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_PAYLOADS_KEY not in substrate_cfg
  assert len(env_cfg["zones"]) == 1
  assert env_cfg["zones"][0] == {
    "name": "catalog:port_hardstand",
    "x": 250.0,
    "y": -125.0,
    "width": 80.0,
    "length": 140.0,
    "heading": 15.0,
    "surface": "Concrete",
  }
  assert len(substrate_cfg[ENVIRONMENT_SUBSTRATE_INGESTION_EVIDENCE_KEY]) == 1
  assert substrate_cfg[ENVIRONMENT_SUBSTRATE_INGESTION_EVIDENCE_KEY][0][
    "no_runtime_setup_application"
  ] is True

  layout_zone = compiled.runtime_metadata.layout_template.zones[0]
  assert layout_zone.name == "catalog:port_hardstand"
  assert layout_zone.surface_type == _SURFACE_TYPE_MAP["Concrete"]
  assert layout_zone.surface_type != _SURFACE_TYPE_MAP["SoftDirt"]
  assert compiled.zone_count == 1


def test_g0_l_f_ingestion_leaves_scenarios_without_payloads_unchanged() -> None:
  scenario = {
    "scenario_name": "environment_substrate_no_payload_test",
    "environment": {"zones": []},
  }
  result = ingest_projection_setup_payloads_into_scenario(scenario)

  assert result.valid
  assert not result.fail_closed
  assert result.ingested_zone_count == 0
  assert result.scenario_data == scenario
  assert result.scenario_data is not scenario


def test_g0_l_f_ingestion_rejects_invalid_surface_before_compiler_defaulting() -> None:
  payload = _payload()
  payload["zones"][0]["surface"] = "Mud"
  scenario = _scenario_with_projection_payload(payload)

  with pytest.raises(
    ValueError,
    match="environment_substrate_projection_ingestion_surface_invalid",
  ):
    ScenarioCompiler.compile_data(scenario)


def test_g0_l_f_ingestion_rejects_runtime_world_index_payloads() -> None:
  payload = _payload()
  payload["zones"][0]["world_index"] = 7
  result = ingest_projection_setup_payloads_into_scenario(
    _scenario_with_projection_payload(payload)
  )

  assert not result.valid
  assert result.fail_closed
  assert (
    result.rejection_reason
    == "environment_substrate_projection_ingestion_world_index_forbidden"
  )


def test_g0_l_f_ingestion_rejects_existing_zone_name_conflicts() -> None:
  payload = _payload()
  scenario = _scenario_with_projection_payload(copy.deepcopy(payload))
  scenario["environment"]["zones"] = [copy.deepcopy(payload["zones"][0])]

  result = ingest_projection_setup_payloads_into_scenario(scenario)

  assert not result.valid
  assert result.fail_closed
  assert (
    result.rejection_reason
    == "environment_substrate_projection_ingestion_zone_name_conflict"
  )
