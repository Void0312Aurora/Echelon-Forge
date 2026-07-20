from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR = REPO_ROOT / "tools" / "maintenance" / "dto_schema" / "generate.py"
SCHEMAS_DIR = GENERATOR.parent / "schemas"

_BUILDER_DIR = "gym_envs/scenario_loader/_generated"

EXPECTED_REGISTRATIONS = {
  "tools/maintenance/dto_schema/schemas/effects_event_fields.py": (
    "src/runtime/contracts/detail/effects_event_fields.inc",
    f"{_BUILDER_DIR}/effects_event_fields_builder.py",
    135,
  ),
  "tools/maintenance/dto_schema/schemas/flight_shaping_shared_fields.py": (
    "src/core/mission/runtime/detail/flight_shaping_shared_fields.inc",
    f"{_BUILDER_DIR}/flight_shaping_shared_fields_builder.py",
    89,
  ),
  "tools/maintenance/dto_schema/schemas/safety_runtime_inputs_fields.py": (
    "src/core/mission/runtime/detail/safety_runtime_inputs.inc",
    f"{_BUILDER_DIR}/safety_runtime_inputs_builder.py",
    33,
  ),
  "tools/maintenance/dto_schema/schemas/safety_runtime_products_fields.py": (
    "src/core/mission/runtime/detail/safety_runtime_products.inc",
    f"{_BUILDER_DIR}/safety_runtime_products_builder.py",
    15,
  ),
  "tools/maintenance/dto_schema/schemas/objective_inputs_fields.py": (
    "src/core/mission/runtime/detail/objective_inputs.inc",
    f"{_BUILDER_DIR}/objective_inputs_builder.py",
    32,
  ),
  "tools/maintenance/dto_schema/schemas/objective_shaping_fields.py": (
    "src/core/mission/runtime/detail/objective_shaping.inc",
    f"{_BUILDER_DIR}/objective_shaping_builder.py",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/objective_products_fields.py": (
    "src/core/mission/runtime/detail/objective_products.inc",
    f"{_BUILDER_DIR}/objective_products_builder.py",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/mission_nav_inputs_fields.py": (
    "src/core/mission/runtime/detail/mission_nav_inputs.inc",
    f"{_BUILDER_DIR}/mission_nav_inputs_builder.py",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/mission_nav_products_fields.py": (
    "src/core/mission/runtime/detail/mission_nav_products.inc",
    f"{_BUILDER_DIR}/mission_nav_products_builder.py",
    19,
  ),
  "tools/maintenance/dto_schema/schemas/step_info_products_fields.py": (
    "src/core/mission/runtime/detail/step_info_products.inc",
    f"{_BUILDER_DIR}/step_info_products_builder.py",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/waypoint_reward_inputs_fields.py": (
    "src/core/mission/runtime/detail/waypoint_reward_inputs.inc",
    f"{_BUILDER_DIR}/waypoint_reward_inputs_builder.py",
    35,
  ),
  "tools/maintenance/dto_schema/schemas/waypoint_reward_products_fields.py": (
    "src/core/mission/runtime/detail/waypoint_reward_products.inc",
    f"{_BUILDER_DIR}/waypoint_reward_products_builder.py",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/approach_reward_inputs_fields.py": (
    "src/core/mission/runtime/detail/approach_reward_inputs.inc",
    f"{_BUILDER_DIR}/approach_reward_inputs_builder.py",
    38,
  ),
  "tools/maintenance/dto_schema/schemas/approach_reward_products_fields.py": (
    "src/core/mission/runtime/detail/approach_reward_products.inc",
    f"{_BUILDER_DIR}/approach_reward_products_builder.py",
    13,
  ),
  "tools/maintenance/dto_schema/schemas/platform_capability_fields.py": (
    "src/runtime/contracts/detail/platform_capability.inc",
    f"{_BUILDER_DIR}/platform_capability_builder.py",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/capability_bundle_fields.py": (
    "src/runtime/contracts/detail/capability_bundle.inc",
    f"{_BUILDER_DIR}/capability_bundle_builder.py",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/resolved_platform_spawn_plan_fields.py": (
    "src/runtime/contracts/detail/resolved_platform_spawn_plan.inc",
    f"{_BUILDER_DIR}/resolved_platform_spawn_plan_builder.py",
    16,
  ),
  "tools/maintenance/dto_schema/schemas/typed_platform_spawn_request_fields.py": (
    "src/runtime/contracts/detail/typed_platform_spawn_request.inc",
    f"{_BUILDER_DIR}/typed_platform_spawn_request_builder.py",
    19,
  ),
  "tools/maintenance/dto_schema/schemas/typed_platform_spawn_validation_result_fields.py": (
    "src/runtime/contracts/detail/typed_platform_spawn_validation_result.inc",
    f"{_BUILDER_DIR}/typed_platform_spawn_validation_result_builder.py",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/batch_reset_request_fields.py": (
    "src/runtime/facade/detail/batch_reset_request.inc",
    f"{_BUILDER_DIR}/batch_reset_request_builder.py",
    1,
  ),
  "tools/maintenance/dto_schema/schemas/world_entity_ref_fields.py": (
    "src/runtime/contracts/detail/world_entity_ref.inc",
    f"{_BUILDER_DIR}/world_entity_ref_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/world_terrain_assignment_fields.py": (
    "src/runtime/contracts/detail/world_terrain_assignment.inc",
    f"{_BUILDER_DIR}/world_terrain_assignment_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/world_wind_assignment_fields.py": (
    "src/runtime/contracts/detail/world_wind_assignment.inc",
    f"{_BUILDER_DIR}/world_wind_assignment_builder.py",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/world_zone_definition_fields.py": (
    "src/runtime/contracts/detail/world_zone_definition.inc",
    f"{_BUILDER_DIR}/world_zone_definition_builder.py",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/world_spawn_request_fields.py": (
    "src/runtime/contracts/detail/world_spawn_request.inc",
    f"{_BUILDER_DIR}/world_spawn_request_builder.py",
    20,
  ),
  "tools/maintenance/dto_schema/schemas/world_pilot_action_assignment_fields.py": (
    "src/runtime/contracts/detail/world_pilot_action_assignment.inc",
    f"{_BUILDER_DIR}/world_pilot_action_assignment_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/world_execution_episode_step_request_fields.py": (
    "src/runtime/contracts/detail/world_execution_episode_step_request.inc",
    f"{_BUILDER_DIR}/world_execution_episode_step_request_builder.py",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/batch_world_setup_request_fields.py": (
    "src/runtime/facade/detail/batch_world_setup_request.inc",
    f"{_BUILDER_DIR}/batch_world_setup_request_builder.py",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/batch_world_setup_result_fields.py": (
    "src/runtime/facade/detail/batch_world_setup_result.inc",
    f"{_BUILDER_DIR}/batch_world_setup_result_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/typed_platform_spawn_result_fields.py": (
    "src/runtime/contracts/detail/typed_platform_spawn_result.inc",
    f"{_BUILDER_DIR}/typed_platform_spawn_result_builder.py",
    14,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_capabilities_fields.py": (
    "src/runtime/facade/detail/runtime_capabilities.inc",
    f"{_BUILDER_DIR}/runtime_capabilities_builder.py",
    24,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_batch_config_fields.py": (
    "src/runtime/facade/detail/runtime_batch_config.inc",
    f"{_BUILDER_DIR}/runtime_batch_config_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_fidelity_request_fields.py": (
    "src/runtime/facade/detail/runtime_fidelity_request.inc",
    f"{_BUILDER_DIR}/runtime_fidelity_request_builder.py",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_fidelity_admission_fields.py": (
    "src/runtime/facade/detail/runtime_fidelity_admission.inc",
    f"{_BUILDER_DIR}/runtime_fidelity_admission_builder.py",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_counterfactual_snapshot_fields.py": (
    "src/runtime/facade/detail/runtime_counterfactual_snapshot.inc",
    f"{_BUILDER_DIR}/runtime_counterfactual_snapshot_builder.py",
    21,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_worldline_comparison_fields.py": (
    "src/runtime/facade/detail/runtime_worldline_comparison.inc",
    f"{_BUILDER_DIR}/runtime_worldline_comparison_builder.py",
    13,
  ),
  "tools/maintenance/dto_schema/schemas/resident_device_output_descriptor_fields.py": (
    "src/runtime/facade/detail/resident_device_output_descriptor.inc",
    f"{_BUILDER_DIR}/resident_device_output_descriptor_builder.py",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_experiment_ancestry_fields.py": (
    "src/runtime/facade/detail/runtime_experiment_ancestry.inc",
    f"{_BUILDER_DIR}/runtime_experiment_ancestry_builder.py",
    16,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_experiment_result_fields.py": (
    "src/runtime/facade/detail/runtime_experiment_result.inc",
    f"{_BUILDER_DIR}/runtime_experiment_result_builder.py",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_experiment_step_request_fields.py": (
    "src/runtime/facade/detail/runtime_experiment_step_request.inc",
    f"{_BUILDER_DIR}/runtime_experiment_step_request_builder.py",
    6,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_experiment_request_fields.py": (
    "src/runtime/facade/detail/runtime_experiment_request.inc",
    f"{_BUILDER_DIR}/runtime_experiment_request_builder.py",
    21,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_window_input_record_fields.py": (
    "src/runtime/facade/detail/runtime_window_input_record.inc",
    f"{_BUILDER_DIR}/runtime_window_input_record_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_window_scheduling_context_fields.py": (
    "src/runtime/facade/detail/runtime_window_scheduling_context.inc",
    f"{_BUILDER_DIR}/runtime_window_scheduling_context_builder.py",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_window_barrier_record_fields.py": (
    "src/runtime/facade/detail/runtime_window_barrier_record.inc",
    f"{_BUILDER_DIR}/runtime_window_barrier_record_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_window_visibility_record_fields.py": (
    "src/runtime/facade/detail/runtime_window_visibility_record.inc",
    f"{_BUILDER_DIR}/runtime_window_visibility_record_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_window_cadence_control_fields.py": (
    "src/runtime/facade/detail/runtime_window_cadence_control.inc",
    f"{_BUILDER_DIR}/runtime_window_cadence_control_builder.py",
    6,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_window_node_execution_record_fields.py": (
    "src/runtime/facade/detail/runtime_window_node_execution_record.inc",
    f"{_BUILDER_DIR}/runtime_window_node_execution_record_builder.py",
    14,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_window_cadence_fields.py": (
    "src/runtime/facade/detail/runtime_window_cadence.inc",
    f"{_BUILDER_DIR}/runtime_window_cadence_builder.py",
    5,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_window_cadence_config_fields.py": (
    "src/runtime/facade/detail/runtime_window_cadence_config.inc",
    f"{_BUILDER_DIR}/runtime_window_cadence_config_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_window_cadence_trace_record_fields.py": (
    "src/runtime/facade/detail/runtime_window_cadence_trace_record.inc",
    f"{_BUILDER_DIR}/runtime_window_cadence_trace_record_builder.py",
    15,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_window_request_fields.py": (
    "src/runtime/facade/detail/runtime_window_request.inc",
    f"{_BUILDER_DIR}/runtime_window_request_builder.py",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/runtime_window_result_fields.py": (
    "src/runtime/facade/detail/runtime_window_result.inc",
    f"{_BUILDER_DIR}/runtime_window_result_builder.py",
    10,
  ),
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
    entry["schema"]: (
      entry["output"],
      entry["python_builder"],
      entry["field_count"],
    )
    for entry in entries
  }
  assert registrations == EXPECTED_REGISTRATIONS
  assert manifest["python_builder_package_init"] == EXPECTED_PACKAGE_INIT

  all_artifacts = (
    [entry["output"] for entry in entries]
    + [entry["python_builder"] for entry in entries]
    + [EXPECTED_PACKAGE_INIT]
  )
  assert len(set(all_artifacts)) == len(all_artifacts)

  schema_modules = {
    path.relative_to(REPO_ROOT).as_posix()
    for path in SCHEMAS_DIR.glob("*.py")
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
    "tools/maintenance/dto_schema/schemas/flight_shaping_shared_fields.py"
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

  stale_builder_rel = EXPECTED_REGISTRATIONS[
    "tools/maintenance/dto_schema/schemas/safety_runtime_inputs_fields.py"
  ][1]
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
