from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from tools.maintenance.dto_schema import generate


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR = REPO_ROOT / "tools" / "maintenance" / "dto_schema" / "generate.py"
SCHEMAS_DIR = GENERATOR.parent / "schemas"

_BUILDER_DIR = "gym_envs/scenario_loader/_generated"

EXPECTED_REGISTRATIONS = {
  "tools/maintenance/dto_schema/schemas/damage/effects_event_fields.py": (
    "src/runtime/contracts/detail/damage/effects_event_fields.inc",
    f"{_BUILDER_DIR}/effects_event_fields_builder.py",
    135,
  ),
  "tools/maintenance/dto_schema/schemas/learning/flight_shaping_shared_fields.py": (
    "src/core/mission/runtime/detail/flight_shaping_shared_fields.inc",
    f"{_BUILDER_DIR}/flight_shaping_shared_fields_builder.py",
    89,
  ),
  "tools/maintenance/dto_schema/schemas/learning/safety_runtime_inputs_fields.py": (
    "src/core/mission/runtime/detail/safety_runtime_inputs.inc",
    f"{_BUILDER_DIR}/safety_runtime_inputs_builder.py",
    33,
  ),
  "tools/maintenance/dto_schema/schemas/learning/safety_runtime_products_fields.py": (
    "src/core/mission/runtime/detail/safety_runtime_products.inc",
    f"{_BUILDER_DIR}/safety_runtime_products_builder.py",
    15,
  ),
  "tools/maintenance/dto_schema/schemas/learning/objective_inputs_fields.py": (
    "src/core/mission/runtime/detail/objective_inputs.inc",
    f"{_BUILDER_DIR}/objective_inputs_builder.py",
    32,
  ),
  "tools/maintenance/dto_schema/schemas/learning/objective_shaping_fields.py": (
    "src/core/mission/runtime/detail/objective_shaping.inc",
    f"{_BUILDER_DIR}/objective_shaping_builder.py",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/learning/objective_products_fields.py": (
    "src/core/mission/runtime/detail/objective_products.inc",
    f"{_BUILDER_DIR}/objective_products_builder.py",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/learning/mission_nav_inputs_fields.py": (
    "src/core/mission/runtime/detail/mission_nav_inputs.inc",
    f"{_BUILDER_DIR}/mission_nav_inputs_builder.py",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/learning/mission_nav_products_fields.py": (
    "src/core/mission/runtime/detail/mission_nav_products.inc",
    f"{_BUILDER_DIR}/mission_nav_products_builder.py",
    19,
  ),
  "tools/maintenance/dto_schema/schemas/learning/step_info_products_fields.py": (
    "src/core/mission/runtime/detail/step_info_products.inc",
    f"{_BUILDER_DIR}/step_info_products_builder.py",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/learning/waypoint_reward_inputs_fields.py": (
    "src/core/mission/runtime/detail/waypoint_reward_inputs.inc",
    f"{_BUILDER_DIR}/waypoint_reward_inputs_builder.py",
    35,
  ),
  "tools/maintenance/dto_schema/schemas/learning/waypoint_reward_products_fields.py": (
    "src/core/mission/runtime/detail/waypoint_reward_products.inc",
    f"{_BUILDER_DIR}/waypoint_reward_products_builder.py",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/learning/approach_reward_inputs_fields.py": (
    "src/core/mission/runtime/detail/approach_reward_inputs.inc",
    f"{_BUILDER_DIR}/approach_reward_inputs_builder.py",
    38,
  ),
  "tools/maintenance/dto_schema/schemas/learning/approach_reward_products_fields.py": (
    "src/core/mission/runtime/detail/approach_reward_products.inc",
    f"{_BUILDER_DIR}/approach_reward_products_builder.py",
    13,
  ),
  "tools/maintenance/dto_schema/schemas/platform/platform_capability_fields.py": (
    "src/runtime/contracts/detail/platform/platform_capability.inc",
    f"{_BUILDER_DIR}/platform_capability_builder.py",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/platform/capability_bundle_fields.py": (
    "src/runtime/contracts/detail/platform/capability_bundle.inc",
    f"{_BUILDER_DIR}/capability_bundle_builder.py",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/platform/resolved_platform_spawn_plan_fields.py": (
    "src/runtime/contracts/detail/platform/resolved_platform_spawn_plan.inc",
    f"{_BUILDER_DIR}/resolved_platform_spawn_plan_builder.py",
    16,
  ),
  "tools/maintenance/dto_schema/schemas/platform/typed_platform_spawn_request_fields.py": (
    "src/runtime/contracts/detail/platform/typed_platform_spawn_request.inc",
    f"{_BUILDER_DIR}/typed_platform_spawn_request_builder.py",
    19,
  ),
  "tools/maintenance/dto_schema/schemas/platform/typed_platform_spawn_validation_result_fields.py": (
    "src/runtime/contracts/detail/platform/typed_platform_spawn_validation_result.inc",
    f"{_BUILDER_DIR}/typed_platform_spawn_validation_result_builder.py",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/batch/batch_reset_request_fields.py": (
    "src/runtime/facade/detail/batch/batch_reset_request.inc",
    f"{_BUILDER_DIR}/batch_reset_request_builder.py",
    1,
  ),
  "tools/maintenance/dto_schema/schemas/platform/world_entity_ref_fields.py": (
    "src/runtime/contracts/detail/platform/world_entity_ref.inc",
    f"{_BUILDER_DIR}/world_entity_ref_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/platform/world_terrain_assignment_fields.py": (
    "src/runtime/contracts/detail/platform/world_terrain_assignment.inc",
    f"{_BUILDER_DIR}/world_terrain_assignment_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/platform/world_wind_assignment_fields.py": (
    "src/runtime/contracts/detail/platform/world_wind_assignment.inc",
    f"{_BUILDER_DIR}/world_wind_assignment_builder.py",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/platform/world_zone_definition_fields.py": (
    "src/runtime/contracts/detail/platform/world_zone_definition.inc",
    f"{_BUILDER_DIR}/world_zone_definition_builder.py",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/platform/world_spawn_request_fields.py": (
    "src/runtime/contracts/detail/platform/world_spawn_request.inc",
    f"{_BUILDER_DIR}/world_spawn_request_builder.py",
    20,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_pilot_action_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_pilot_action_assignment.inc",
    f"{_BUILDER_DIR}/world_pilot_action_assignment_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/batch/world_execution_episode_step_request_fields.py": (
    "src/runtime/contracts/detail/tasking/world_execution_episode_step_request.inc",
    f"{_BUILDER_DIR}/world_execution_episode_step_request_builder.py",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/batch/batch_world_setup_request_fields.py": (
    "src/runtime/facade/detail/batch/batch_world_setup_request.inc",
    f"{_BUILDER_DIR}/batch_world_setup_request_builder.py",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/batch/batch_world_setup_result_fields.py": (
    "src/runtime/facade/detail/batch/batch_world_setup_result.inc",
    f"{_BUILDER_DIR}/batch_world_setup_result_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/platform/typed_platform_spawn_result_fields.py": (
    "src/runtime/contracts/detail/platform/typed_platform_spawn_result.inc",
    f"{_BUILDER_DIR}/typed_platform_spawn_result_builder.py",
    14,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_capabilities_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_capabilities.inc",
    f"{_BUILDER_DIR}/runtime_capabilities_builder.py",
    24,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_batch_config_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_batch_config.inc",
    f"{_BUILDER_DIR}/runtime_batch_config_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_fidelity_request_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_fidelity_request.inc",
    f"{_BUILDER_DIR}/runtime_fidelity_request_builder.py",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_fidelity_admission_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_fidelity_admission.inc",
    f"{_BUILDER_DIR}/runtime_fidelity_admission_builder.py",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_counterfactual_snapshot_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_counterfactual_snapshot.inc",
    f"{_BUILDER_DIR}/runtime_counterfactual_snapshot_builder.py",
    21,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_worldline_comparison_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_worldline_comparison.inc",
    f"{_BUILDER_DIR}/runtime_worldline_comparison_builder.py",
    13,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/resident_device_output_descriptor_fields.py": (
    "src/runtime/facade/detail/runtime/resident_device_output_descriptor.inc",
    f"{_BUILDER_DIR}/resident_device_output_descriptor_builder.py",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_experiment_ancestry_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_experiment_ancestry.inc",
    f"{_BUILDER_DIR}/runtime_experiment_ancestry_builder.py",
    16,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_experiment_result_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_experiment_result.inc",
    f"{_BUILDER_DIR}/runtime_experiment_result_builder.py",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_experiment_step_request_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_experiment_step_request.inc",
    f"{_BUILDER_DIR}/runtime_experiment_step_request_builder.py",
    6,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_experiment_request_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_experiment_request.inc",
    f"{_BUILDER_DIR}/runtime_experiment_request_builder.py",
    21,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_input_record_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_input_record.inc",
    f"{_BUILDER_DIR}/runtime_window_input_record_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_scheduling_context_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_scheduling_context.inc",
    f"{_BUILDER_DIR}/runtime_window_scheduling_context_builder.py",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_barrier_record_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_barrier_record.inc",
    f"{_BUILDER_DIR}/runtime_window_barrier_record_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_visibility_record_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_visibility_record.inc",
    f"{_BUILDER_DIR}/runtime_window_visibility_record_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_cadence_control_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_cadence_control.inc",
    f"{_BUILDER_DIR}/runtime_window_cadence_control_builder.py",
    6,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_node_execution_record_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_node_execution_record.inc",
    f"{_BUILDER_DIR}/runtime_window_node_execution_record_builder.py",
    14,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_cadence_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_cadence.inc",
    f"{_BUILDER_DIR}/runtime_window_cadence_builder.py",
    5,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_cadence_config_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_cadence_config.inc",
    f"{_BUILDER_DIR}/runtime_window_cadence_config_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_cadence_trace_record_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_cadence_trace_record.inc",
    f"{_BUILDER_DIR}/runtime_window_cadence_trace_record_builder.py",
    15,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_request_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_request.inc",
    f"{_BUILDER_DIR}/runtime_window_request_builder.py",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/window/runtime_window_result_fields.py": (
    "src/runtime/facade/detail/window/runtime_window_result.inc",
    f"{_BUILDER_DIR}/runtime_window_result_builder.py",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/learning/reward_term_fields.py": (
    "src/runtime/contracts/detail/learning/reward_term.inc",
    f"{_BUILDER_DIR}/reward_term_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/learning/reward_report_fields.py": (
    "src/runtime/contracts/detail/learning/reward_report.inc",
    f"{_BUILDER_DIR}/reward_report_builder.py",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/learning/termination_spec_fields.py": (
    "src/runtime/contracts/detail/learning/termination_spec.inc",
    f"{_BUILDER_DIR}/termination_spec_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/learning/observation_view_spec_fields.py": (
    "src/runtime/contracts/detail/learning/observation_view_spec.inc",
    f"{_BUILDER_DIR}/observation_view_spec_builder.py",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/learning/observation_view_compatibility_report_fields.py": (
    "src/runtime/contracts/detail/learning/observation_view_compatibility_report.inc",
    f"{_BUILDER_DIR}/observation_view_compatibility_report_builder.py",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/batch/observation_batch_request_fields.py": (
    "src/runtime/facade/detail/batch/observation_batch_request.inc",
    f"{_BUILDER_DIR}/observation_batch_request_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/batch/tasking_batch_request_fields.py": (
    "src/runtime/facade/detail/batch/tasking_batch_request.inc",
    f"{_BUILDER_DIR}/tasking_batch_request_builder.py",
    5,
  ),
  "tools/maintenance/dto_schema/schemas/batch/execution_batch_step_request_fields.py": (
    "src/runtime/facade/detail/batch/execution_batch_step_request.inc",
    f"{_BUILDER_DIR}/execution_batch_step_request_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/batch/observation_batch_packet_fields.py": (
    "src/runtime/facade/detail/batch/observation_batch_packet.inc",
    f"{_BUILDER_DIR}/observation_batch_packet_builder.py",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/batch/tasking_batch_packet_fields.py": (
    "src/runtime/facade/detail/batch/tasking_batch_packet.inc",
    f"{_BUILDER_DIR}/tasking_batch_packet_builder.py",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_world_layout_request_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_world_layout_request.inc",
    f"{_BUILDER_DIR}/runtime_world_layout_request_builder.py",
    15,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_world_layout_result_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_world_layout_result.inc",
    f"{_BUILDER_DIR}/runtime_world_layout_result_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_counterfactual_branch_request_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_counterfactual_branch_request.inc",
    f"{_BUILDER_DIR}/runtime_counterfactual_branch_request_builder.py",
    19,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_counterfactual_restore_request_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_counterfactual_restore_request.inc",
    f"{_BUILDER_DIR}/runtime_counterfactual_restore_request_builder.py",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_counterfactual_restore_result_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_counterfactual_restore_result.inc",
    f"{_BUILDER_DIR}/runtime_counterfactual_restore_result_builder.py",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/runtime/runtime_counterfactual_branch_result_fields.py": (
    "src/runtime/facade/detail/runtime/runtime_counterfactual_branch_result.inc",
    f"{_BUILDER_DIR}/runtime_counterfactual_branch_result_builder.py",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/engagement_entity_ref_fields.py": (
    "src/runtime/contracts/detail/engagement/engagement_entity_ref.inc",
    f"{_BUILDER_DIR}/engagement_entity_ref_builder.py",
    2,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/lethality_chain_header_fields.py": (
    "src/runtime/contracts/detail/engagement/lethality_chain_header.inc",
    f"{_BUILDER_DIR}/lethality_chain_header_builder.py",
    18,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/nearest_approach_event_fields.py": (
    "src/runtime/contracts/detail/engagement/nearest_approach_event.inc",
    f"{_BUILDER_DIR}/nearest_approach_event_builder.py",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/fuze_evaluation_event_fields.py": (
    "src/runtime/contracts/detail/engagement/fuze_evaluation_event.inc",
    f"{_BUILDER_DIR}/fuze_evaluation_event_builder.py",
    25,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/warhead_mechanism_event_fields.py": (
    "src/runtime/contracts/detail/engagement/warhead_mechanism_event.inc",
    f"{_BUILDER_DIR}/warhead_mechanism_event_builder.py",
    12,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/spatial_coverage_event_fields.py": (
    "src/runtime/contracts/detail/engagement/spatial_coverage_event.inc",
    f"{_BUILDER_DIR}/spatial_coverage_event_builder.py",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/damage/component_load_event_fields.py": (
    "src/runtime/contracts/detail/damage/component_load_event.inc",
    f"{_BUILDER_DIR}/component_load_event_builder.py",
    23,
  ),
  "tools/maintenance/dto_schema/schemas/damage/component_damage_event_fields.py": (
    "src/runtime/contracts/detail/damage/component_damage_event.inc",
    f"{_BUILDER_DIR}/component_damage_event_builder.py",
    10,
  ),
  "tools/maintenance/dto_schema/schemas/damage/platform_consequence_event_fields.py": (
    "src/runtime/contracts/detail/damage/platform_consequence_event.inc",
    f"{_BUILDER_DIR}/platform_consequence_event_builder.py",
    29,
  ),
  "tools/maintenance/dto_schema/schemas/damage/structural_breakup_event_fields.py": (
    "src/runtime/contracts/detail/damage/structural_breakup_event.inc",
    f"{_BUILDER_DIR}/structural_breakup_event_builder.py",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/damage/lifecycle_transition_event_fields.py": (
    "src/runtime/contracts/detail/damage/lifecycle_transition_event.inc",
    f"{_BUILDER_DIR}/lifecycle_transition_event_builder.py",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/damage/training_projection_event_fields.py": (
    "src/runtime/contracts/detail/damage/training_projection_event.inc",
    f"{_BUILDER_DIR}/training_projection_event_builder.py",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/damage/component_mechanism_load_row_fields.py": (
    "src/runtime/contracts/detail/damage/component_mechanism_load_row.inc",
    f"{_BUILDER_DIR}/component_mechanism_load_row_builder.py",
    24,
  ),
  "tools/maintenance/dto_schema/schemas/damage/component_response_row_fields.py": (
    "src/runtime/contracts/detail/damage/component_response_row.inc",
    f"{_BUILDER_DIR}/component_response_row_builder.py",
    34,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/track_packet_fields.py": (
    "src/runtime/contracts/detail/engagement/track_packet.inc",
    f"{_BUILDER_DIR}/track_packet_builder.py",
    14,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/launch_request_fields.py": (
    "src/runtime/contracts/detail/engagement/launch_request.inc",
    f"{_BUILDER_DIR}/launch_request_builder.py",
    12,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/launch_event_fields.py": (
    "src/runtime/contracts/detail/engagement/launch_event.inc",
    f"{_BUILDER_DIR}/launch_event_builder.py",
    12,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/munition_lifecycle_packet_fields.py": (
    "src/runtime/contracts/detail/engagement/munition_lifecycle_packet.inc",
    f"{_BUILDER_DIR}/munition_lifecycle_packet_builder.py",
    17,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_approach_fact_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_approach_fact.inc",
    f"{_BUILDER_DIR}/kill_chain_approach_fact_builder.py",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_fuze_decision_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_fuze_decision.inc",
    f"{_BUILDER_DIR}/kill_chain_fuze_decision_builder.py",
    13,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_component_load_fact_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_component_load_fact.inc",
    f"{_BUILDER_DIR}/kill_chain_component_load_fact_builder.py",
    22,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_warhead_load_field_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_warhead_load_field.inc",
    f"{_BUILDER_DIR}/kill_chain_warhead_load_field_builder.py",
    24,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_target_susceptibility_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_target_susceptibility.inc",
    f"{_BUILDER_DIR}/kill_chain_target_susceptibility_builder.py",
    13,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_component_response_fact_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_component_response_fact.inc",
    f"{_BUILDER_DIR}/kill_chain_component_response_fact_builder.py",
    34,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_consequence_projection_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_consequence_projection.inc",
    f"{_BUILDER_DIR}/kill_chain_consequence_projection_builder.py",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/kill_chain/kill_chain_runtime_facade_fields.py": (
    "src/runtime/contracts/detail/kill_chain/kill_chain_runtime_facade.inc",
    f"{_BUILDER_DIR}/kill_chain_runtime_facade_builder.py",
    12,
  ),
  "tools/maintenance/dto_schema/schemas/damage/damage_report_fields.py": (
    "src/runtime/contracts/detail/damage/damage_report.inc",
    f"{_BUILDER_DIR}/damage_report_builder.py",
    19,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/diagnostics_trace_fields.py": (
    "src/runtime/contracts/detail/engagement/diagnostics_trace.inc",
    f"{_BUILDER_DIR}/diagnostics_trace_builder.py",
    16,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/engagement_batch_request_fields.py": (
    "src/runtime/facade/detail/batch/engagement_batch_request.inc",
    f"{_BUILDER_DIR}/engagement_batch_request_builder.py",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/engagement_event_packet_fields.py": (
    "src/runtime/facade/detail/batch/engagement_event_packet.inc",
    f"{_BUILDER_DIR}/engagement_event_packet_builder.py",
    27,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_mission_command_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_mission_command_assignment.inc",
    f"{_BUILDER_DIR}/world_mission_command_assignment_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/mission_command_maintained_batch_contract_fields.py": (
    "src/runtime/contracts/detail/tasking/mission_command_maintained_batch_contract.inc",
    f"{_BUILDER_DIR}/mission_command_maintained_batch_contract_builder.py",
    7,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_mission_command_maintained_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_mission_command_maintained_assignment.inc",
    f"{_BUILDER_DIR}/world_mission_command_maintained_assignment_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/task_order_air_tasking_identity_directive_fields.py": (
    "src/runtime/contracts/detail/tasking/task_order_air_tasking_identity_directive.inc",
    f"{_BUILDER_DIR}/task_order_air_tasking_identity_directive_builder.py",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/task_order_air_stationing_directive_fields.py": (
    "src/runtime/contracts/detail/tasking/task_order_air_stationing_directive.inc",
    f"{_BUILDER_DIR}/task_order_air_stationing_directive_builder.py",
    17,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/task_order_air_formation_directive_fields.py": (
    "src/runtime/contracts/detail/tasking/task_order_air_formation_directive.inc",
    f"{_BUILDER_DIR}/task_order_air_formation_directive_builder.py",
    8,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/task_order_naval_stationing_directive_fields.py": (
    "src/runtime/contracts/detail/tasking/task_order_naval_stationing_directive.inc",
    f"{_BUILDER_DIR}/task_order_naval_stationing_directive_builder.py",
    1,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/task_order_maintained_batch_contract_fields.py": (
    "src/runtime/contracts/detail/tasking/task_order_maintained_batch_contract.inc",
    f"{_BUILDER_DIR}/task_order_maintained_batch_contract_builder.py",
    9,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_task_order_maintained_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_task_order_maintained_assignment.inc",
    f"{_BUILDER_DIR}/world_task_order_maintained_assignment_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_leader_intent_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_leader_intent_assignment.inc",
    f"{_BUILDER_DIR}/world_leader_intent_assignment_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/leader_intent_maintained_batch_contract_fields.py": (
    "src/runtime/contracts/detail/tasking/leader_intent_maintained_batch_contract.inc",
    f"{_BUILDER_DIR}/leader_intent_maintained_batch_contract_builder.py",
    11,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_leader_intent_maintained_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_leader_intent_maintained_assignment.inc",
    f"{_BUILDER_DIR}/world_leader_intent_maintained_assignment_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_pilot_report_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_pilot_report_assignment.inc",
    f"{_BUILDER_DIR}/world_pilot_report_assignment_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/pilot_report_maintained_batch_contract_fields.py": (
    "src/runtime/contracts/detail/tasking/pilot_report_maintained_batch_contract.inc",
    f"{_BUILDER_DIR}/pilot_report_maintained_batch_contract_builder.py",
    4,
  ),
  "tools/maintenance/dto_schema/schemas/tasking/world_pilot_report_maintained_assignment_fields.py": (
    "src/runtime/contracts/detail/tasking/world_pilot_report_maintained_assignment.inc",
    f"{_BUILDER_DIR}/world_pilot_report_maintained_assignment_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/engagement/recent_engagement_events_fields.py": (
    "src/runtime/contracts/detail/engagement/recent_engagement_events.inc",
    f"{_BUILDER_DIR}/recent_engagement_events_builder.py",
    14,
  ),
  "tools/maintenance/dto_schema/schemas/scenario/scenario_generation_evidence_ref_fields.py": (
    "src/runtime/contracts/detail/scenario/scenario_generation_evidence_ref.inc",
    f"{_BUILDER_DIR}/scenario_generation_evidence_ref_builder.py",
    3,
  ),
  "tools/maintenance/dto_schema/schemas/scenario/scenario_generation_request_metadata_fields.py": (
    "src/runtime/contracts/detail/scenario/scenario_generation_request_metadata.inc",
    f"{_BUILDER_DIR}/scenario_generation_request_metadata_builder.py",
    13,
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

  stale_builder_rel = EXPECTED_REGISTRATIONS[
    "tools/maintenance/dto_schema/schemas/learning/safety_runtime_inputs_fields.py"
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

  The classification is exercised with injected normalizers so the expected
  behavior of both filesystem regimes is pinned on every platform, instead
  of depending on the case sensitivity of the checkout's own filesystem.
  """
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

  # Case-insensitive regime (str.lower stands in for os.path.normcase on
  # Windows): the variant folds onto the managed artifact, so it is a case
  # mismatch and must not appear among deletable orphans.
  unexpected, mismatched = generate.classify_generated_files(
    owned, [variant, rogue], normalize=str.lower
  )
  assert unexpected == (rogue,)
  assert mismatched == ((variant, exact),)

  # Case-sensitive regime (identity normalizer): the variant is a genuinely
  # distinct file, hence a plain orphan.
  unexpected, mismatched = generate.classify_generated_files(
    owned, [variant, rogue], normalize=str
  )
  assert unexpected == tuple(sorted([variant, rogue]))
  assert mismatched == ()


def test_check_and_write_fail_closed_on_case_mismatch(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  capsys: pytest.CaptureFixture[str],
) -> None:
  """An injected case mismatch makes --check fail and --write refuse deletion."""
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
