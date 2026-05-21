from __future__ import annotations

import json
import os
import tempfile

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

from python.scenario.compiler import (  # noqa: E402
    build_scenario_generation_request_artifact,
    ScenarioCompiler,
    ScenarioGenerationEvidenceRef,
    ScenarioGenerationRequest,
    validate_scenario_generation_request,
)


def _sample_scenario() -> dict:
    return {
        "scenario_name": "wp15_generation_surface_test",
        "environment": {
            "time_step": 0.05,
            "max_steps": 8,
            "terrain_type": "flat",
            "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
        },
        "entities": [
            {
                "name": "Blue_F16",
                "type": "F-16C_Block50",
                "side": "Blue",
                "pos": [0.0, 0.0, 1200.0],
                "vel": [0.0, 180.0, 0.0],
                "heading": 90.0,
                "is_agent": True,
            }
        ],
        "mission_command": {
            "command_code": 3,
            "target_heading": 90.0,
            "target_altitude": 1200.0,
            "target_speed": 180.0,
        },
        "objectives": [],
        "rewards": {"survival": 0.0},
    }


def _valid_request() -> ScenarioGenerationRequest:
    return ScenarioGenerationRequest(
        request_id="scenario-gen:req-001",
        request_version="1",
        generation_kind="adversary_placement",
        source="counterfactual_branch",
        generator_version="generator.v1.2.0",
        deterministic_seed=17,
        baseline_scenario_ref="scenario:wp15_generation_surface_test",
        replay_envelope_ref="replay:deterministic:17",
        branch_point_ref="branch:barrier:3",
        capability_refs=("capability_bundle:blue_air_training",),
        evidence_refs=(
            ScenarioGenerationEvidenceRef(
                ref_id="scenario:wp15_generation_surface_test",
                evidence_kind="baseline_scenario",
                provenance_label="baseline",
            ),
            ScenarioGenerationEvidenceRef(
                ref_id="replay:deterministic:17",
                evidence_kind="replay_envelope",
                provenance_label="replay",
            ),
            ScenarioGenerationEvidenceRef(
                ref_id="branch:barrier:3",
                evidence_kind="branch_point",
                provenance_label="branch",
            ),
        ),
    )


def test_wp15_generation_request_validates_and_exports_metadata_deterministically() -> None:
    request = _valid_request()

    validation = validate_scenario_generation_request(request)

    assert validation.valid
    assert not validation.fail_closed
    assert validation.rejection_reason == ""
    assert request.to_metadata() == {
        "request_id": "scenario-gen:req-001",
        "request_version": "1",
        "contract_version": "wp15.scenario_generation_request.v1",
        "generation_kind": "adversary_placement",
        "source": "counterfactual_branch",
        "generator_version": "generator.v1.2.0",
        "deterministic_seed": 17,
        "baseline_scenario_ref": "scenario:wp15_generation_surface_test",
        "replay_envelope_ref": "replay:deterministic:17",
        "branch_point_ref": "branch:barrier:3",
        "capability_refs": ["capability_bundle:blue_air_training"],
        "evidence_refs": [
            {
                "ref_id": "scenario:wp15_generation_surface_test",
                "evidence_kind": "baseline_scenario",
                "provenance_label": "baseline",
            },
            {
                "ref_id": "branch:barrier:3",
                "evidence_kind": "branch_point",
                "provenance_label": "branch",
            },
            {
                "ref_id": "replay:deterministic:17",
                "evidence_kind": "replay_envelope",
                "provenance_label": "replay",
            },
        ],
    }


def test_wp15_generation_request_rejects_missing_required_fields_fail_closed() -> None:
    missing_source = ScenarioGenerationRequest(
        request_id="scenario-gen:req-001a",
        generation_kind="scenario_variation",
        source="",
        generator_version="generator.v1.2.0",
        deterministic_seed=0,
        baseline_scenario_ref="scenario:wp15_generation_surface_test",
        replay_envelope_ref="replay:deterministic:17",
        evidence_refs=(
            ScenarioGenerationEvidenceRef(
                ref_id="scenario:wp15_generation_surface_test",
                evidence_kind="baseline_scenario",
            ),
        ),
    )

    validation = validate_scenario_generation_request(missing_source)

    assert not validation.valid
    assert validation.fail_closed
    assert validation.rejection_reason == "scenario_generation_source_required"

    missing_baseline = ScenarioGenerationRequest(
        request_id="scenario-gen:req-001b",
        generation_kind="scenario_variation",
        source="curriculum_generation",
        generator_version="generator.v1.2.0",
        deterministic_seed=0,
        baseline_scenario_ref="",
        replay_envelope_ref="replay:deterministic:17",
        evidence_refs=(
            ScenarioGenerationEvidenceRef(
                ref_id="scenario:wp15_generation_surface_test",
                evidence_kind="baseline_scenario",
            ),
        ),
    )

    validation = validate_scenario_generation_request(missing_baseline)

    assert not validation.valid
    assert validation.fail_closed
    assert (
        validation.rejection_reason
        == "scenario_generation_baseline_scenario_required"
    )

    missing_seed = ScenarioGenerationRequest(
        request_id="scenario-gen:req-002",
        generation_kind="scenario_variation",
        source="curriculum_generation",
        generator_version="generator.v1.2.0",
        deterministic_seed=-1,
        baseline_scenario_ref="scenario:wp15_generation_surface_test",
        replay_envelope_ref="replay:deterministic:17",
        evidence_refs=(
            ScenarioGenerationEvidenceRef(
                ref_id="scenario:wp15_generation_surface_test",
                evidence_kind="baseline_scenario",
            ),
        ),
    )

    validation = validate_scenario_generation_request(missing_seed)

    assert not validation.valid
    assert validation.fail_closed
    assert validation.rejection_reason == "scenario_generation_seed_required"
    assert "deterministic_seed must be a non-negative integer" in validation.errors

    missing_generator_version = ScenarioGenerationRequest(
        request_id="scenario-gen:req-003",
        generation_kind="scenario_variation",
        source="curriculum_generation",
        generator_version="",
        deterministic_seed=0,
        baseline_scenario_ref="scenario:wp15_generation_surface_test",
        replay_envelope_ref="replay:deterministic:17",
        evidence_refs=(
            ScenarioGenerationEvidenceRef(
                ref_id="scenario:wp15_generation_surface_test",
                evidence_kind="baseline_scenario",
            ),
        ),
    )

    validation = validate_scenario_generation_request(missing_generator_version)

    assert not validation.valid
    assert validation.fail_closed
    assert (
        validation.rejection_reason
        == "scenario_generation_generator_version_required"
    )

    missing_evidence = ScenarioGenerationRequest(
        request_id="scenario-gen:req-004",
        generation_kind="scenario_variation",
        source="curriculum_generation",
        generator_version="generator.v1.2.0",
        deterministic_seed=0,
        baseline_scenario_ref="scenario:wp15_generation_surface_test",
        replay_envelope_ref="replay:deterministic:17",
        evidence_refs=(),
    )

    validation = validate_scenario_generation_request(missing_evidence)

    assert not validation.valid
    assert validation.fail_closed
    assert validation.rejection_reason == "scenario_generation_evidence_required"

    missing_lineage = ScenarioGenerationRequest(
        request_id="scenario-gen:req-004b",
        generation_kind="scenario_variation",
        source="curriculum_generation",
        generator_version="generator.v1.2.0",
        deterministic_seed=0,
        baseline_scenario_ref="scenario:wp15_generation_surface_test",
        evidence_refs=(
            ScenarioGenerationEvidenceRef(
                ref_id="scenario:wp15_generation_surface_test",
                evidence_kind="baseline_scenario",
            ),
        ),
    )

    validation = validate_scenario_generation_request(missing_lineage)

    assert not validation.valid
    assert validation.fail_closed
    assert validation.rejection_reason == "scenario_generation_lineage_ref_required"


def test_wp15_generation_request_rejects_unsupported_kind_source_and_evidence_kind() -> None:
    unsupported_kind = ScenarioGenerationRequest(
        request_id="scenario-gen:req-005",
        generation_kind="broad_generator_runtime",
        source="counterfactual_branch",
        generator_version="generator.v1.2.0",
        deterministic_seed=2,
        baseline_scenario_ref="scenario:wp15_generation_surface_test",
        replay_envelope_ref="replay:deterministic:17",
        evidence_refs=(
            ScenarioGenerationEvidenceRef(
                ref_id="scenario:wp15_generation_surface_test",
                evidence_kind="baseline_scenario",
            ),
        ),
    )
    validation = validate_scenario_generation_request(unsupported_kind)
    assert not validation.valid
    assert validation.fail_closed
    assert validation.rejection_reason == "scenario_generation_kind_unsupported"

    unsupported_source = ScenarioGenerationRequest(
        request_id="scenario-gen:req-006",
        generation_kind="scenario_variation",
        source="runtime_mutation",
        generator_version="generator.v1.2.0",
        deterministic_seed=2,
        baseline_scenario_ref="scenario:wp15_generation_surface_test",
        replay_envelope_ref="replay:deterministic:17",
        evidence_refs=(
            ScenarioGenerationEvidenceRef(
                ref_id="scenario:wp15_generation_surface_test",
                evidence_kind="baseline_scenario",
            ),
        ),
    )
    validation = validate_scenario_generation_request(unsupported_source)
    assert not validation.valid
    assert validation.fail_closed
    assert validation.rejection_reason == "scenario_generation_source_unsupported"

    unsupported_evidence_kind = ScenarioGenerationRequest(
        request_id="scenario-gen:req-007",
        generation_kind="scenario_variation",
        source="curriculum_generation",
        generator_version="generator.v1.2.0",
        deterministic_seed=2,
        baseline_scenario_ref="scenario:wp15_generation_surface_test",
        replay_envelope_ref="replay:deterministic:17",
        evidence_refs=(
            ScenarioGenerationEvidenceRef(
                ref_id="scenario:wp15_generation_surface_test",
                evidence_kind="unsupported_truth_claim",
            ),
        ),
    )
    validation = validate_scenario_generation_request(unsupported_evidence_kind)
    assert not validation.valid
    assert validation.fail_closed
    assert (
        validation.rejection_reason
        == "scenario_generation_evidence_kind_unsupported"
    )

    missing_provenance = ScenarioGenerationRequest(
        request_id="scenario-gen:req-008",
        generation_kind="scenario_variation",
        source="curriculum_generation",
        generator_version="generator.v1.2.0",
        deterministic_seed=2,
        baseline_scenario_ref="scenario:wp15_generation_surface_test",
        replay_envelope_ref="replay:deterministic:17",
        evidence_refs=(
            ScenarioGenerationEvidenceRef(
                ref_id="scenario:wp15_generation_surface_test",
                evidence_kind="baseline_scenario",
            ),
        ),
    )
    validation = validate_scenario_generation_request(missing_provenance)
    assert not validation.valid
    assert validation.fail_closed
    assert (
        validation.rejection_reason
        == "scenario_generation_evidence_provenance_required"
    )


def test_wp15_generation_request_artifact_stays_metadata_only_and_does_not_mutate_baseline() -> None:
    ScenarioCompiler.clear_cache()
    fd, scenario_path = tempfile.mkstemp(
        prefix="wp15_generation_surface_",
        suffix=".json",
        dir=tempfile.gettempdir(),
    )
    os.close(fd)
    try:
        with open(scenario_path, "w", encoding="utf-8") as handle:
            json.dump(_sample_scenario(), handle, ensure_ascii=True)

        compiled = ScenarioCompiler.compile_path(scenario_path)
        baseline_before = compiled.instantiate_runtime()
        request = _valid_request()

        artifact = build_scenario_generation_request_artifact(
            request,
            compiled_scenario=compiled,
        )
        metadata = artifact.to_metadata()

        assert metadata["artifact_kind"] == "scenario_generation_request_metadata"
        assert not metadata["authoritative_state_mutation_allowed"]
        assert metadata["baseline_scenario"]["scenario_name"] == compiled.scenario_name
        assert metadata["baseline_scenario"]["entity_count"] == compiled.entity_count

        metadata["request"]["generator_version"] = "mutated"
        metadata["evidence_metadata"][0]["ref_id"] = "mutated"
        metadata["baseline_scenario"]["scenario_name"] = "mutated"

        baseline_after = compiled.instantiate_runtime()
        assert baseline_after == baseline_before
        assert compiled.merged_scenario_data["scenario_name"] == "wp15_generation_surface_test"
        assert artifact.request.generator_version == "generator.v1.2.0"
        assert artifact.request.evidence_refs[0].ref_id == "scenario:wp15_generation_surface_test"
        assert artifact.baseline_scenario_name == compiled.scenario_name
    finally:
        try:
            os.unlink(scenario_path)
        except OSError:
            pass
        ScenarioCompiler.clear_cache()
