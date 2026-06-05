from __future__ import annotations

import copy

import pytest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.scenario.compiler import ScenarioCompiler, _SURFACE_TYPE_MAP  # noqa: E402
from python.scenario.environment_substrate import (  # noqa: E402
    ENVIRONMENT_SUBSTRATE_ENVIRONMENT_KEY,
    ENVIRONMENT_SUBSTRATE_INGESTION_EVIDENCE_KEY,
    ENVIRONMENT_SUBSTRATE_PROJECTION_SETUP_PAYLOADS_KEY,
    EnvironmentManifest,
    build_deterministic_environment_fixture,
    build_world_zone_projection_setup_payload,
    ingest_projection_setup_payloads_into_scenario,
    validate_environment_manifest,
)


def _fixture() -> EnvironmentManifest:
    manifest = build_deterministic_environment_fixture()
    assert validate_environment_manifest(manifest).valid
    return manifest


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
