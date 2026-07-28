from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

from python.scenario.compiler import ( # noqa: E402
  SCENARIO_GENERATION_INTERVENTION_MUTATION_BOUNDARY,
  ScenarioCompiler,
  ScenarioGenerationEvidenceRef,
  ScenarioGenerationInterventionSpec,
  ScenarioGenerationRequest,
  ScenarioGenerationVariationSpec,
  build_scenario_generation_request_artifact,
  build_scenario_generation_runtime_artifact,
  validate_scenario_generation_request,
  validate_scenario_generation_runtime_inputs,
)
from python.scenario.runtime import ( # noqa: E402
  BatchWorldApplyBuffer,
  build_batch_world_setup_request,
  build_compiled_world_layout,
)


def _metadata_request_sample_scenario() -> dict:
  return {
    "scenario_name": "generation_surface_test",
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


def _valid_metadata_request() -> ScenarioGenerationRequest:
  return ScenarioGenerationRequest(
    request_id="scenario-gen:req-001",
    request_version="1",
    generation_kind="adversary_placement",
    source="counterfactual_branch",
    generator_version="generator.v1.2.0",
    deterministic_seed=17,
    baseline_scenario_ref="scenario:generation_surface_test",
    replay_envelope_ref="replay:deterministic:17",
    branch_point_ref="branch:barrier:3",
    capability_refs=("capability_bundle:blue_air_training",),
    evidence_refs=(
      ScenarioGenerationEvidenceRef(
        ref_id="scenario:generation_surface_test",
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


def _sample_scenario() -> dict:
  return {
    "scenario_name": "generation_runtime_test",
    "environment": {
      "time_step": 0.05,
      "max_steps": 8,
      "terrain_type": "flat",
      "wind": {"speed_mps": 5.0, "dir_from_deg": 90.0, "shear_mps_per_km": 0.0},
      "zones": [
        {
          "name": "primary",
          "x": 0.0,
          "y": 0.0,
          "width": 5000.0,
          "length": 5000.0,
          "heading": 0.0,
          "surface_type": "Concrete",
        }
      ],
    },
    "entities": [
      {
        "name": "Blue_F16",
        "type": "F-16C_Block50",
        "side": "Blue",
        "pos": [0.0, 1500.0, 1200.0],
        "vel": [0.0, 180.0, 0.0],
        "heading": 90.0,
        "is_agent": True,
      },
      {
        "name": "Red_F16",
        "type": "F-16C_Block50",
        "side": "Red",
        "pos": [12000.0, -2500.0, 1000.0],
        "vel": [0.0, -165.0, 0.0],
        "heading": 270.0,
        "is_agent": False,
      },
    ],
    "mission_command": {
      "command_code": 3,
      "target_heading": 90.0,
      "target_altitude": 1200.0,
      "target_speed": 180.0,
    },
    "meta": {"tags": ["baseline"], "source": "unit-test"},
    "objectives": [],
    "rewards": {"survival": 0.0},
  }


def _request(seed: int) -> ScenarioGenerationRequest:
  return ScenarioGenerationRequest(
    request_id="scenario-gen:counterfactual:req-001",
    request_version="2",
    generation_kind="scenario_variation",
    source="counterfactual_branch",
    generator_version="generator.counterfactual.v1",
    deterministic_seed=seed,
    baseline_scenario_ref="scenario:generation_runtime_test",
    replay_envelope_ref="replay:baseline:21",
    branch_point_ref="branch:baseline:21",
    capability_refs=(
      "capability_bundle:blue_air_training",
      "resolved_spawn_plan:f16c_block50",
    ),
    evidence_refs=(
      ScenarioGenerationEvidenceRef(
        ref_id="scenario:generation_runtime_test",
        evidence_kind="baseline_scenario",
        provenance_label="baseline",
      ),
      ScenarioGenerationEvidenceRef(
        ref_id="replay:baseline:21",
        evidence_kind="replay_envelope",
        provenance_label="replay",
      ),
      ScenarioGenerationEvidenceRef(
        ref_id="branch:baseline:21",
        evidence_kind="branch_point",
        provenance_label="branch",
      ),
    ),
  )


def _variation_specs() -> tuple[ScenarioGenerationVariationSpec, ...]:
  return (
    ScenarioGenerationVariationSpec(
      variation_id="blue-altitude",
      target_path=("entities", 0, "pos", 2),
      operation="uniform_float",
      minimum_value=950.0,
      maximum_value=1450.0,
      precision_digits=3,
    ),
    ScenarioGenerationVariationSpec(
      variation_id="red-offset-y",
      target_path=("entities", 1, "pos", 1),
      operation="uniform_float",
      minimum_value=-4000.0,
      maximum_value=-1500.0,
      precision_digits=3,
    ),
    ScenarioGenerationVariationSpec(
      variation_id="target-speed",
      target_path=("mission_command", "target_speed"),
      operation="uniform_int",
      minimum_value=160,
      maximum_value=220,
    ),
    ScenarioGenerationVariationSpec(
      variation_id="scenario-tag",
      target_path=("meta", "source"),
      operation="choice",
      choices=("seed.a", "seed.b", "seed.c"),
    ),
  )


def _intervention_specs() -> tuple[ScenarioGenerationInterventionSpec, ...]:
  return (
    ScenarioGenerationInterventionSpec(
      intervention_id="cmd-variant-001",
      intervention_kind="command_variant",
      target_entity_ref="Blue_F16",
      evidence_refs=("review_note:counterfactual-review",),
      payload={"command_field": "target_speed", "intent": "counterfactual_probe"},
      mutation_boundary=SCENARIO_GENERATION_INTERVENTION_MUTATION_BOUNDARY,
    ),
  )


def _declared_target_paths() -> set[str]:
  return {
    "entities[0].pos[2]",
    "entities[1].pos[1]",
    "mission_command.target_speed",
    "meta.source",
    "meta.generated_interventions",
    "meta.generated_interventions[0].deterministic_seed",
  }


def _flatten_changes(before: object, after: object, prefix: str = "") -> list[str]:
  if type(before) != type(after):
    return [prefix or "<root>"]
  if isinstance(before, dict):
    keys = set(before.keys()) | set(after.keys())
    changes: list[str] = []
    for key in sorted(keys):
      child_prefix = key if not prefix else f"{prefix}.{key}"
      if key not in before or key not in after:
        changes.append(child_prefix)
        continue
      changes.extend(_flatten_changes(before[key], after[key], child_prefix))
    return changes
  if isinstance(before, list):
    if len(before) != len(after):
      return [prefix or "<root>"]
    changes: list[str] = []
    for index, (before_item, after_item) in enumerate(zip(before, after)):
      child_prefix = f"{prefix}[{index}]" if prefix else f"[{index}]"
      changes.extend(_flatten_changes(before_item, after_item, child_prefix))
    return changes
  if before != after:
    return [prefix or "<root>"]
  return []


def test_wp15_generation_request_validates_and_exports_metadata_deterministically() -> None:
  request = _valid_metadata_request()

  validation = validate_scenario_generation_request(request)

  assert validation.valid
  assert not validation.fail_closed
  assert validation.rejection_reason == ""
  assert request.to_metadata() == {
    "request_id": "scenario-gen:req-001",
    "request_version": "1",
    "contract_version": "scenario_generation_request.v1",
    "generation_kind": "adversary_placement",
    "source": "counterfactual_branch",
    "generator_version": "generator.v1.2.0",
    "deterministic_seed": 17,
    "baseline_scenario_ref": "scenario:generation_surface_test",
    "replay_envelope_ref": "replay:deterministic:17",
    "branch_point_ref": "branch:barrier:3",
    "capability_refs": ["capability_bundle:blue_air_training"],
    "evidence_refs": [
      {
        "ref_id": "scenario:generation_surface_test",
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
    baseline_scenario_ref="scenario:generation_surface_test",
    replay_envelope_ref="replay:deterministic:17",
    evidence_refs=(
      ScenarioGenerationEvidenceRef(
        ref_id="scenario:generation_surface_test",
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
        ref_id="scenario:generation_surface_test",
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
    baseline_scenario_ref="scenario:generation_surface_test",
    replay_envelope_ref="replay:deterministic:17",
    evidence_refs=(
      ScenarioGenerationEvidenceRef(
        ref_id="scenario:generation_surface_test",
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
    baseline_scenario_ref="scenario:generation_surface_test",
    replay_envelope_ref="replay:deterministic:17",
    evidence_refs=(
      ScenarioGenerationEvidenceRef(
        ref_id="scenario:generation_surface_test",
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
    baseline_scenario_ref="scenario:generation_surface_test",
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
    baseline_scenario_ref="scenario:generation_surface_test",
    evidence_refs=(
      ScenarioGenerationEvidenceRef(
        ref_id="scenario:generation_surface_test",
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
    baseline_scenario_ref="scenario:generation_surface_test",
    replay_envelope_ref="replay:deterministic:17",
    evidence_refs=(
      ScenarioGenerationEvidenceRef(
        ref_id="scenario:generation_surface_test",
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
    baseline_scenario_ref="scenario:generation_surface_test",
    replay_envelope_ref="replay:deterministic:17",
    evidence_refs=(
      ScenarioGenerationEvidenceRef(
        ref_id="scenario:generation_surface_test",
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
    baseline_scenario_ref="scenario:generation_surface_test",
    replay_envelope_ref="replay:deterministic:17",
    evidence_refs=(
      ScenarioGenerationEvidenceRef(
        ref_id="scenario:generation_surface_test",
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
    baseline_scenario_ref="scenario:generation_surface_test",
    replay_envelope_ref="replay:deterministic:17",
    evidence_refs=(
      ScenarioGenerationEvidenceRef(
        ref_id="scenario:generation_surface_test",
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
    prefix="generation_surface_",
    suffix=".json",
    dir=tempfile.gettempdir(),
  )
  os.close(fd)
  try:
    with open(scenario_path, "w", encoding="utf-8") as handle:
      json.dump(_metadata_request_sample_scenario(), handle, ensure_ascii=True)

    compiled = ScenarioCompiler.compile_path(scenario_path)
    baseline_before = compiled.instantiate_runtime()
    request = _valid_metadata_request()

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
    assert compiled.merged_scenario_data["scenario_name"] == "generation_surface_test"
    assert artifact.request.generator_version == "generator.v1.2.0"
    assert artifact.request.evidence_refs[0].ref_id == "scenario:generation_surface_test"
    assert artifact.baseline_scenario_name == compiled.scenario_name
  finally:
    try:
      os.unlink(scenario_path)
    except OSError:
      pass
    ScenarioCompiler.clear_cache()


def test_wp21_generation_runtime_validates_inputs_fail_closed() -> None:
  request = _request(17)
  validation = validate_scenario_generation_runtime_inputs(
    request,
    baseline_setup_ref="",
    baseline_scenario_data=_sample_scenario(),
    variations=_variation_specs(),
  )

  assert not validation.valid
  assert validation.fail_closed
  assert (
    validation.rejection_reason
    == "scenario_generation_runtime_baseline_setup_ref_required"
  )


def test_wp21_generation_runtime_is_byte_identical_for_same_request_seed_and_baseline() -> None:
  baseline = _sample_scenario()
  baseline_before = deepcopy(baseline)
  artifact_a = build_scenario_generation_runtime_artifact(
    _request(17),
    baseline_setup_ref="setup:baseline:21",
    baseline_scenario_data=baseline,
    variations=_variation_specs(),
    interventions=_intervention_specs(),
  )
  artifact_b = build_scenario_generation_runtime_artifact(
    _request(17),
    baseline_setup_ref="setup:baseline:21",
    baseline_scenario_data=baseline,
    variations=_variation_specs(),
    interventions=_intervention_specs(),
  )

  assert artifact_a.to_canonical_bytes() == artifact_b.to_canonical_bytes()
  assert artifact_a.to_metadata() == artifact_b.to_metadata()
  assert baseline == baseline_before


def test_wp21_generation_runtime_changes_only_declared_variation_fields_across_seeds() -> None:
  baseline = _sample_scenario()
  artifact_a = build_scenario_generation_runtime_artifact(
    _request(17),
    baseline_setup_ref="setup:baseline:21",
    baseline_scenario_data=baseline,
    variations=_variation_specs(),
    interventions=_intervention_specs(),
  )
  artifact_b = build_scenario_generation_runtime_artifact(
    _request(18),
    baseline_setup_ref="setup:baseline:21",
    baseline_scenario_data=baseline,
    variations=_variation_specs(),
    interventions=_intervention_specs(),
  )

  assert artifact_a.to_canonical_bytes() != artifact_b.to_canonical_bytes()
  changed_paths = set(
    _flatten_changes(
      artifact_a.instantiate_generated_scenario(),
      artifact_b.instantiate_generated_scenario(),
    )
  )
  assert changed_paths
  assert changed_paths <= _declared_target_paths()
  assert artifact_a.to_metadata()["lineage"] == artifact_b.to_metadata()["lineage"]
  assert artifact_a.to_metadata()["baseline"] == artifact_b.to_metadata()["baseline"]


def test_wp21_generation_runtime_preserves_compiled_scenario_and_runtime_copies() -> None:
  ScenarioCompiler.clear_cache()
  compiled = ScenarioCompiler.compile_data(_sample_scenario())
  baseline_merged_before = deepcopy(compiled.merged_scenario_data)
  runtime_before = compiled.instantiate_runtime()
  runtime_context_before = compiled.instantiate_runtime_context()

  artifact = build_scenario_generation_runtime_artifact(
    _request(23),
    baseline_setup_ref="setup:baseline:compiled",
    compiled_scenario=compiled,
    variations=_variation_specs(),
    interventions=_intervention_specs(),
  )

  generated = artifact.instantiate_generated_scenario()
  generated["entities"][0]["pos"][2] = -1.0
  generated["meta"]["generated_interventions"][0]["payload"]["command_field"] = "mutated"

  runtime_after = compiled.instantiate_runtime()
  runtime_context_after = compiled.instantiate_runtime_context()
  assert compiled.merged_scenario_data == baseline_merged_before
  assert runtime_after == runtime_before
  assert runtime_context_after == runtime_context_before
  assert artifact.generated_scenario_data["entities"][0]["pos"][2] != -1.0
  assert (
    artifact.generated_scenario_data["meta"]["generated_interventions"][0]["payload"]["command_field"]
    == "target_speed"
  )


def test_wp21_generation_runtime_compiles_and_feeds_setup_request_without_loader_boundary() -> None:
  artifact = build_scenario_generation_runtime_artifact(
    _request(31),
    baseline_setup_ref="setup:baseline:31",
    baseline_scenario_data=_sample_scenario(),
    variations=_variation_specs(),
    interventions=_intervention_specs(),
  )

  compiled = artifact.compile_generated_scenario()
  layout = build_compiled_world_layout(compiled, seed=artifact.request.deterministic_seed)
  buffer = BatchWorldApplyBuffer(world_count=1)
  terrain_assignments, wind_assignments, sun_assignments, zone_defs, spawn_requests = (
    buffer.prepare([layout])
  )

  request = build_batch_world_setup_request(
    seeds=[artifact.request.deterministic_seed],
    terrain_assignments=terrain_assignments,
    wind_assignments=wind_assignments,
    zones=zone_defs,
    spawn_requests=spawn_requests,
    time_steps=[0.0 if layout.time_step_s is None else float(layout.time_step_s)],
    sun_assignments=sun_assignments,
  )

  assert compiled.scenario_name == "generation_runtime_test"
  assert (
    artifact.generated_scenario_data["meta"]["generated_interventions"][0]["mutation_boundary"]
    == "setup_admission_only"
  )
  assert request is not None
  assert list(request.seeds) == [31]
  assert len(list(request.terrain_assignments)) == 1
  assert len(list(request.wind_assignments)) == 1
  assert len(list(request.sun_assignments)) == 1
  assert len(list(request.zones)) == len(layout.zones)
  assert len(list(request.spawn_requests)) == len(layout.spawns)
  assert list(request.time_steps) == [0.05]
  assert list(request.spawn_requests)[0].entity_name == "Blue_F16"
