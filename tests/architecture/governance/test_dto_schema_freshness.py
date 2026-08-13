from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR = REPO_ROOT / "tools" / "maintenance" / "dto_schema" / "generate.py"
SCHEMAS_DIR = GENERATOR.parent / "schemas"

_BUILDER_DIR = "gym_envs/scenario_loader/_generated"

_SAFETY_SCHEMA = (
  "tools/maintenance/dto_schema/schemas/learning/safety_runtime_inputs_fields.py"
)

# Every registered schema renders one .inc fragment, so the pinned pair is
# (fragment, field count). The Python builder half is whitelisted instead
# (python_builder.BUILDER_SCHEMA_NAMES), so it is pinned separately below and
# the manifest reports a null builder for every schema outside the whitelist.
EXPECTED_REGISTRATIONS = {
  "tools/maintenance/dto_schema/schemas/damage/effects_event_fields.py": (
    "src/runtime/contracts/detail/damage/effects_event_fields.inc",
    135,
  ),
  "tools/maintenance/dto_schema/schemas/learning/flight_shaping_shared_fields.py": (
    "src/core/mission/runtime/detail/flight_shaping_shared_fields.inc",
    89,
  ),
  "tools/maintenance/dto_schema/schemas/learning/safety_runtime_inputs_fields.py": (
    "src/core/mission/runtime/detail/safety_runtime_inputs.inc",
    33,
  ),
  "tools/maintenance/dto_schema/schemas/learning/safety_runtime_products_fields.py": (
    "src/core/mission/runtime/detail/safety_runtime_products.inc",
    15,
  ),
  "tools/maintenance/dto_schema/schemas/learning/objective_inputs_fields.py": (
    "src/core/mission/runtime/detail/objective_inputs.inc",
    32,
  ),
  "tools/maintenance/dto_schema/schemas/learning/objective_shaping_fields.py": (
    "src/core/mission/runtime/detail/objective_shaping.inc",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/learning/objective_products_fields.py": (
    "src/core/mission/runtime/detail/objective_products.inc",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/learning/mission_nav_inputs_fields.py": (
    "src/core/mission/runtime/detail/mission_nav_inputs.inc",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/learning/mission_nav_products_fields.py": (
    "src/core/mission/runtime/detail/mission_nav_products.inc",
    19,
  ),
  "tools/maintenance/dto_schema/schemas/learning/step_info_products_fields.py": (
    "src/core/mission/runtime/detail/step_info_products.inc",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/learning/waypoint_reward_inputs_fields.py": (
    "src/core/mission/runtime/detail/waypoint_reward_inputs.inc",
    35,
  ),
  "tools/maintenance/dto_schema/schemas/learning/waypoint_reward_products_fields.py": (
    "src/core/mission/runtime/detail/waypoint_reward_products.inc",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/learning/approach_reward_inputs_fields.py": (
    "src/core/mission/runtime/detail/approach_reward_inputs.inc",
    38,
  ),
  "tools/maintenance/dto_schema/schemas/learning/approach_reward_products_fields.py": (
    "src/core/mission/runtime/detail/approach_reward_products.inc",
    13,
  ),
  "tools/maintenance/dto_schema/schemas/platform/platform_capability_fields.py": (
    "src/runtime/contracts/detail/platform/platform_capability.inc",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/platform/capability_bundle_fields.py": (
    "src/runtime/contracts/detail/platform/capability_bundle.inc",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/platform/resolved_platform_spawn_plan_fields.py": (
    "src/runtime/contracts/detail/platform/resolved_platform_spawn_plan.inc",
    16,
  ),
  "tools/maintenance/dto_schema/schemas/platform/typed_platform_spawn_request_fields.py": (
    "src/runtime/contracts/detail/platform/typed_platform_spawn_request.inc",
    19,
  ),
  "tools/maintenance/dto_schema/schemas/platform/typed_platform_spawn_validation_result_fields.py": (
    "src/runtime/contracts/detail/platform/typed_platform_spawn_validation_result.inc",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/batch/batch_reset_request_fields.py": (
    "src/runtime/facade/detail/batch/batch_reset_request.inc",
    1,
  ),
  "tools/maintenance/dto_schema/schemas/platform/world_entity_ref_fields.py": (
    "src/runtime/contracts/detail/platform/world_entity_ref.inc",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/platform/world_terrain_assignment_fields.py": (
    "src/runtime/contracts/detail/platform/world_terrain_assignment.inc",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/platform/world_wind_assignment_fields.py": (
    "src/runtime/contracts/detail/platform/world_wind_assignment.inc",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/platform/world_zone_definition_fields.py": (
    "src/runtime/contracts/detail/platform/world_zone_definition.inc",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/platform/world_spawn_request_fields.py": (
    "src/runtime/contracts/detail/platform/world_spawn_request.inc",
    20,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_pilot_action_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_pilot_action_assignment.inc",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/batch/batch_world_setup_request_fields.py": (
    "src/runtime/facade/detail/batch/batch_world_setup_request.inc",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/batch/batch_world_setup_result_fields.py": (
    "src/runtime/facade/detail/batch/batch_world_setup_result.inc",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/platform/typed_platform_spawn_result_fields.py": (
    "src/runtime/contracts/detail/platform/typed_platform_spawn_result.inc",
    14,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_capabilities_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_capabilities.inc",
    24,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_batch_config_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_batch_config.inc",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_fidelity_request_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_fidelity_request.inc",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_fidelity_admission_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_fidelity_admission.inc",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/resident_device_output_descriptor_fields.py": (
    "src/runtime/facade/detail/runtime/resident_device_output_descriptor.inc",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_input_record_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_input_record.inc",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_scheduling_context_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_scheduling_context.inc",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_barrier_record_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_barrier_record.inc",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_visibility_record_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_visibility_record.inc",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_cadence_control_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_cadence_control.inc",
    6,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_node_execution_record_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_node_execution_record.inc",
    14,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_cadence_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_cadence.inc",
    5,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_cadence_config_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_cadence_config.inc",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_cadence_trace_record_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_cadence_trace_record.inc",
    15,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_request_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_request.inc",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_result_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_result.inc",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/learning/reward_term_fields.py": (
    "src/runtime/contracts/detail/learning/reward_term.inc",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/learning/reward_report_fields.py": (
    "src/runtime/contracts/detail/learning/reward_report.inc",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/learning/termination_spec_fields.py": (
    "src/runtime/contracts/detail/learning/termination_spec.inc",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/learning/observation_view_spec_fields.py": (
    "src/runtime/contracts/detail/learning/observation_view_spec.inc",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/learning/observation_view_compatibility_report_fields.py": (
    "src/runtime/contracts/detail/learning/observation_view_compatibility_report.inc",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/batch/observation_batch_request_fields.py": (
    "src/runtime/facade/detail/batch/observation_batch_request.inc",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/batch/tasking_batch_request_fields.py": (
    "src/runtime/facade/detail/batch/tasking_batch_request.inc",
    5,
  ),
  "tools/maintenance/dto_schema/schemas/batch/observation_batch_packet_fields.py": (
    "src/runtime/facade/detail/batch/observation_batch_packet.inc",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/batch/tasking_batch_packet_fields.py": (
    "src/runtime/facade/detail/batch/tasking_batch_packet.inc",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_world_layout_request_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_world_layout_request.inc",
    15,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_world_layout_result_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_world_layout_result.inc",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/engagement_entity_ref_fields.py": (
    "src/runtime/contracts/detail/engagement/engagement_entity_ref.inc",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/lethality_chain_header_fields.py": (
    "src/runtime/contracts/detail/engagement/lethality_chain_header.inc",
    18,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/nearest_approach_event_fields.py": (
    "src/runtime/contracts/detail/engagement/nearest_approach_event.inc",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/fuze_evaluation_event_fields.py": (
    "src/runtime/contracts/detail/engagement/fuze_evaluation_event.inc",
    25,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/warhead_mechanism_event_fields.py": (
    "src/runtime/contracts/detail/engagement/warhead_mechanism_event.inc",
    12,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/spatial_coverage_event_fields.py": (
    "src/runtime/contracts/detail/engagement/spatial_coverage_event.inc",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/damage/component_load_event_fields.py": (
    "src/runtime/contracts/detail/damage/component_load_event.inc",
    23,
  ),
  "tools/maintenance/dto_schema/schemas/damage/component_damage_event_fields.py": (
    "src/runtime/contracts/detail/damage/component_damage_event.inc",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/damage/platform_consequence_event_fields.py": (
    "src/runtime/contracts/detail/damage/platform_consequence_event.inc",
    29,
  ),
  "tools/maintenance/dto_schema/schemas/damage/structural_breakup_event_fields.py": (
    "src/runtime/contracts/detail/damage/structural_breakup_event.inc",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/damage/lifecycle_transition_event_fields.py": (
    "src/runtime/contracts/detail/damage/lifecycle_transition_event.inc",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/damage/training_projection_event_fields.py": (
    "src/runtime/contracts/detail/damage/training_projection_event.inc",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/damage/component_mechanism_load_row_fields.py": (
    "src/runtime/contracts/detail/damage/component_mechanism_load_row.inc",
    24,
  ),
  "tools/maintenance/dto_schema/schemas/damage/component_response_row_fields.py": (
    "src/runtime/contracts/detail/damage/component_response_row.inc",
    34,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/track_packet_fields.py": (
    "src/runtime/contracts/detail/engagement/track_packet.inc",
    14,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/launch_request_fields.py": (
    "src/runtime/contracts/detail/engagement/launch_request.inc",
    12,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/launch_event_fields.py": (
    "src/runtime/contracts/detail/engagement/launch_event.inc",
    12,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/munition_lifecycle_packet_fields.py": (
    "src/runtime/contracts/detail/engagement/munition_lifecycle_packet.inc",
    17,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_approach_fact_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_approach_fact.inc",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_fuze_decision_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_fuze_decision.inc",
    13,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_component_load_fact_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_component_load_fact.inc",
    22,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_warhead_load_field_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_warhead_load_field.inc",
    24,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_target_susceptibility_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_target_susceptibility.inc",
    13,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_component_response_fact_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_component_response_fact.inc",
    34,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_consequence_projection_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_consequence_projection.inc",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_runtime_facade_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_runtime_facade.inc",
    12,
  ),
  "tools/maintenance/dto_schema/schemas/damage/damage_report_fields.py": (
    "src/runtime/contracts/detail/damage/damage_report.inc",
    19,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/diagnostics_trace_fields.py": (
    "src/runtime/contracts/detail/engagement/diagnostics_trace.inc",
    16,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/engagement_batch_request_fields.py": (
    "src/runtime/facade/detail/batch/engagement_batch_request.inc",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/engagement_event_packet_fields.py": (
    "src/runtime/facade/detail/batch/engagement_event_packet.inc",
    27,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_mission_command_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_mission_command_assignment.inc",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/mission_command_maintained_batch_contract_fields.py": (
    "src/runtime/contracts/detail/tasking/mission_command_maintained_batch_contract.inc",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_mission_command_maintained_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_mission_command_maintained_assignment.inc",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/task_order_air_tasking_identity_directive_fields.py": (
    "src/runtime/contracts/detail/tasking/task_order_air_tasking_identity_directive.inc",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/task_order_air_stationing_directive_fields.py": (
    "src/runtime/contracts/detail/tasking/task_order_air_stationing_directive.inc",
    17,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/task_order_air_formation_directive_fields.py": (
    "src/runtime/contracts/detail/tasking/task_order_air_formation_directive.inc",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/task_order_naval_stationing_directive_fields.py": (
    "src/runtime/contracts/detail/tasking/task_order_naval_stationing_directive.inc",
    1,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/task_order_maintained_batch_contract_fields.py": (
    "src/runtime/contracts/detail/tasking/task_order_maintained_batch_contract.inc",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_task_order_maintained_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_task_order_maintained_assignment.inc",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_leader_intent_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_leader_intent_assignment.inc",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/leader_intent_maintained_batch_contract_fields.py": (
    "src/runtime/contracts/detail/tasking/leader_intent_maintained_batch_contract.inc",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_leader_intent_maintained_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_leader_intent_maintained_assignment.inc",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_pilot_report_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_pilot_report_assignment.inc",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/pilot_report_maintained_batch_contract_fields.py": (
    "src/runtime/contracts/detail/tasking/pilot_report_maintained_batch_contract.inc",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_pilot_report_maintained_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_pilot_report_maintained_assignment.inc",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/recent_engagement_events_fields.py": (
    "src/runtime/contracts/detail/engagement/recent_engagement_events.inc",
    14,
  ),
}

EXPECTED_PYTHON_BUILDERS = {
  _SAFETY_SCHEMA: f"{_BUILDER_DIR}/safety_runtime_inputs_builder.py",
}

EXPECTED_PACKAGE_INIT = f"{_BUILDER_DIR}/__init__.py"


def _run_generator(*args: str) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [sys.executable, str(GENERATOR), *args],
    cwd=REPO_ROOT,
    check=False,
    capture_output=True,
    text=True,
  )


def test_dto_schema_generated_outputs_are_fresh_and_registered(
  tmp_path: Path,
) -> None:
  check_result = _run_generator("--check")
  assert check_result.returncode == 0, (
    "DTO schema outputs are stale or the generator failed:\n"
    f"{check_result.stdout}{check_result.stderr}"
  )

  manifest_result = _run_generator("--manifest")
  assert manifest_result.returncode == 0, (
    "DTO schema manifest generation failed:\n"
    f"{manifest_result.stdout}{manifest_result.stderr}"
  )
  manifest = json.loads(manifest_result.stdout)
  entries = manifest["schemas"]

  registrations = {
    entry["schema"]: (entry["output"], entry["field_count"])
    for entry in entries
  }
  assert registrations == EXPECTED_REGISTRATIONS
  assert manifest["python_builder_package_init"] == EXPECTED_PACKAGE_INIT

  # The builder half is a whitelist, not a projection of the registry: a
  # schema outside it renders an .inc and reports a null builder. Asserting
  # the null set explicitly means a builder silently regrowing for an
  # unlisted schema fails here rather than only in the orphan scan.
  builders = {
    entry["schema"]: entry["python_builder"]
    for entry in entries
    if entry["python_builder"] is not None
  }
  assert builders == EXPECTED_PYTHON_BUILDERS
  assert manifest["python_builder_schemas"] == ["safety_runtime_inputs"]

  all_artifacts = (
    [entry["output"] for entry in entries]
    + list(EXPECTED_PYTHON_BUILDERS.values())
    + [EXPECTED_PACKAGE_INIT]
  )
  assert len(set(all_artifacts)) == len(all_artifacts)

  schema_modules = {
    path.relative_to(REPO_ROOT).as_posix()
    for path in SCHEMAS_DIR.rglob("*.py")
    if path.name != "__init__.py"
  }
  assert schema_modules == set(registrations)
  assert all(REPO_ROOT.joinpath(path).is_file() for path in all_artifacts)

  isolated_root = tmp_path / "checkout"
  for path in all_artifacts:
    source = REPO_ROOT / path
    target = isolated_root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())

  clean_result = _run_generator("--check", "--repo-root", str(isolated_root))
  assert clean_result.returncode == 0, (
    "isolated artifact copy should be fresh; a stale entry here means the "
    "manifest does not register every generated artifact:\n"
    f"{clean_result.stdout}{clean_result.stderr}"
  )

  stale_inc_path = isolated_root / EXPECTED_REGISTRATIONS[
    "tools/maintenance/dto_schema/schemas/learning/flight_shaping_shared_fields.py"
  ][0]
  original_inc = stale_inc_path.read_bytes()
  modified_inc = original_inc.replace(
    b"EF_FLIGHT_SHAPING_FIELD(double, altitude_progress_weight, 0.0)",
    b"EF_FLIGHT_SHAPING_FIELD(double, altitude_progress_weight, 1.0)",
    1,
  )
  assert modified_inc != original_inc
  stale_inc_path.write_bytes(modified_inc)

  stale_result = _run_generator("--check", "--repo-root", str(isolated_root))
  assert stale_result.returncode == 1
  assert (
    "stale: src/core/mission/runtime/detail/flight_shaping_shared_fields.inc"
    in stale_result.stdout
  )
  assert "-EF_FLIGHT_SHAPING_FIELD(double, altitude_progress_weight, 1.0)" in (
    stale_result.stdout
  )
  stale_inc_path.write_bytes(original_inc)

  stale_builder_rel = EXPECTED_PYTHON_BUILDERS[_SAFETY_SCHEMA]
  stale_builder_path = isolated_root / stale_builder_rel
  original_builder = stale_builder_path.read_bytes()
  stale_builder_path.write_bytes(original_builder + b"# drift\n")

  stale_builder_result = _run_generator(
    "--check", "--repo-root", str(isolated_root)
  )
  assert stale_builder_result.returncode == 1
  assert f"stale: {stale_builder_rel}" in stale_builder_result.stdout
  assert "-# drift" in stale_builder_result.stdout
  stale_builder_path.write_bytes(original_builder)

  restored_result = _run_generator("--check", "--repo-root", str(isolated_root))
  assert restored_result.returncode == 0

  # The generated package directory is fully generator-owned: a *.py file no
  # registered schema owns fails --check and is removed by --write.
  rogue_rel = f"{_BUILDER_DIR}/rogue_orphan_builder.py"
  rogue_path = isolated_root / rogue_rel
  rogue_path.write_bytes(b"# rogue\n")

  unexpected_result = _run_generator(
    "--check", "--repo-root", str(isolated_root)
  )
  assert unexpected_result.returncode == 1
  assert f"unexpected: {rogue_rel}" in unexpected_result.stdout

  write_result = _run_generator("--write", "--repo-root", str(isolated_root))
  assert write_result.returncode == 0
  assert f"removed: {rogue_rel}" in write_result.stdout
  assert not rogue_path.exists()

  final_result = _run_generator("--check", "--repo-root", str(isolated_root))
  assert final_result.returncode == 0


def test_classify_generated_files_case_handling() -> None:
  """Case-variant spellings of managed artifacts are never deletable orphans.

  The default classification folds case unconditionally (str.casefold):
  Python cannot tell from a path string whether the underlying filesystem
  folds case (os.path.normcase stays the identity on a POSIX Python even
  over case-insensitive APFS), so a case variant of a managed artifact must
  never reach the --write deletion loop on any platform. The strict
  identity regime remains available to callers that inject it explicitly.
  """
  from tools.maintenance.dto_schema import generate

  owned = {
    f"{_BUILDER_DIR}/alpha_builder.py",
    f"{_BUILDER_DIR}/__init__.py",
  }
  exact = f"{_BUILDER_DIR}/alpha_builder.py"
  variant = f"{_BUILDER_DIR}/Alpha_Builder.py"
  rogue = f"{_BUILDER_DIR}/rogue_builder.py"

  # Exact spellings are owned regardless of normalizer.
  for normalize in (str.lower, str):
    unexpected, mismatched = generate.classify_generated_files(
      owned, [exact, f"{_BUILDER_DIR}/__init__.py"], normalize=normalize
    )
    assert unexpected == ()
    assert mismatched == ()

  # Default regime (str.casefold on every platform): the variant folds onto
  # the managed artifact, so it is a protected case mismatch and never a
  # deletable orphan -- on a case-insensitive filesystem unlinking it would
  # destroy the managed file itself.
  unexpected, mismatched = generate.classify_generated_files(
    owned, [variant, rogue]
  )
  assert unexpected == (rogue,)
  assert mismatched == ((variant, exact),)

  # An injected case-insensitive normalizer classifies the same way.
  unexpected, mismatched = generate.classify_generated_files(
    owned, [variant, rogue], normalize=str.lower
  )
  assert unexpected == (rogue,)
  assert mismatched == ((variant, exact),)

  # Strict regime only by explicit injection (identity normalizer): the
  # variant is then treated as a genuinely distinct file, hence an orphan.
  unexpected, mismatched = generate.classify_generated_files(
    owned, [variant, rogue], normalize=str
  )
  assert unexpected == tuple(sorted([variant, rogue]))
  assert mismatched == ()


def test_scan_generated_package_matches_py_suffix_case_insensitively(
  tmp_path: Path,
) -> None:
  """A stale builder cannot dodge the scan through an upper-case extension."""
  from tools.maintenance.dto_schema import generate

  package_dir = tmp_path / _BUILDER_DIR
  package_dir.mkdir(parents=True)
  (package_dir / "ROGUE.PY").write_bytes(b"# rogue\n")

  unexpected, mismatched = generate.scan_generated_package((), tmp_path)
  assert unexpected == (f"{_BUILDER_DIR}/ROGUE.PY",)
  assert mismatched == ()


def test_check_and_write_fail_closed_on_case_mismatch(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  capsys: pytest.CaptureFixture[str],
) -> None:
  """An injected case mismatch makes --check fail and --write refuse deletion."""
  from tools.maintenance.dto_schema import generate

  actual = f"{_BUILDER_DIR}/Alpha_Builder.py"
  registered = f"{_BUILDER_DIR}/alpha_builder.py"
  monkeypatch.setattr(
    generate,
    "scan_generated_package",
    lambda registrations, output_root: ((), ((actual, registered),)),
  )

  # Lay out the only registration-independent artifact so the mismatch is
  # the sole failure source for --check.
  init_path = tmp_path / EXPECTED_PACKAGE_INIT
  init_path.parent.mkdir(parents=True, exist_ok=True)
  init_path.write_bytes(generate.python_builder.render_package_init_bytes())

  assert generate.check_outputs((), tmp_path) == 1
  check_out = capsys.readouterr().out
  assert f"case-mismatch: {actual}" in check_out
  assert registered in check_out

  # write_outputs must refuse deletion (nothing to unlink here: attempting
  # one would raise FileNotFoundError) and exit nonzero.
  assert generate.write_outputs((), tmp_path) == 1
  write_out = capsys.readouterr().out
  assert f"case mismatch (not removed): {actual}" in write_out
  assert "refusing to delete" in write_out


def test_registry_and_schema_directory_must_agree(
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  """Every command refuses to run when schemas/ and SCHEMA_MODULES diverge."""
  from tools.maintenance.dto_schema import generate

  unregistered, missing = generate.registry_inconsistencies(
    generate.SCHEMA_MODULES, generate.SCHEMAS_DIR
  )
  assert unregistered == ()
  assert missing == ()

  original = generate.SCHEMA_MODULES

  monkeypatch.setattr(generate, "SCHEMA_MODULES", original[:-1])
  with pytest.raises(ValueError, match="not in SCHEMA_MODULES"):
    generate.load_schemas()

  phantom = f"{generate.SCHEMAS_PACKAGE}.phantom_missing_fields"
  monkeypatch.setattr(generate, "SCHEMA_MODULES", original + (phantom,))
  with pytest.raises(ValueError, match="missing on disk"):
    generate.load_schemas()
