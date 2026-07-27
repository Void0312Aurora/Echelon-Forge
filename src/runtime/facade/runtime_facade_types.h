#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "components/physics/instruments.h"
#include "core/interfaces/observation.h"
#include "core/mission/episode/execution_episode_controller.h"
#include "runtime/contracts/counterfactual_replay_contracts.h"
#include "runtime/contracts/engagement_contracts.h"
#include "runtime/contracts/policy_contracts.h"
#include "runtime/contracts/runtime_dto_contracts.h"
#include "runtime/contracts/world_batch_contracts.h"

struct RuntimeCapabilities {
#define EF_RUNTIME_CAPABILITIES_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_capabilities.inc"
};

struct RuntimeBatchConfig {
#define EF_RUNTIME_BATCH_CONFIG_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_batch_config.inc"
};

struct RuntimeFidelityRequest {
#define EF_RUNTIME_FIDELITY_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_fidelity_request.inc"
};

struct RuntimeFidelityAdmission {
#define EF_RUNTIME_FIDELITY_ADMISSION_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_fidelity_admission.inc"
};

struct RuntimeCounterfactualSnapshot {
#define EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(type, name, default_value)                        \
    type name = default_value;
#include "runtime/facade/detail/runtime_counterfactual_snapshot.inc"
};

struct RuntimeWorldlineComparison {
#define EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_worldline_comparison.inc"
};

struct BatchResetRequest {
#define EF_BATCH_RESET_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch_reset_request.inc"
};

struct BatchWorldSetupRequest {
#define EF_BATCH_WORLD_SETUP_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch_world_setup_request.inc"
};

struct BatchWorldSetupResult {
#define EF_BATCH_WORLD_SETUP_RESULT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/batch_world_setup_result.inc"
};

struct RuntimeWorldLayoutRequest {
#define EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_world_layout_request.inc"
};

struct RuntimeWorldLayoutResult {
#define EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_world_layout_result.inc"
};

struct RuntimeCounterfactualBranchRequest {
#define EF_RUNTIME_COUNTERFACTUAL_BRANCH_REQUEST_FIELD(type, name, default_value)                  \
    type name = default_value;
#include "runtime/facade/detail/runtime_counterfactual_branch_request.inc"
};

struct RuntimeCounterfactualRestoreRequest {
#define EF_RUNTIME_COUNTERFACTUAL_RESTORE_REQUEST_FIELD(type, name, default_value)                 \
    type name = default_value;
#include "runtime/facade/detail/runtime_counterfactual_restore_request.inc"
};

struct RuntimeCounterfactualRestoreResult {
#define EF_RUNTIME_COUNTERFACTUAL_RESTORE_RESULT_FIELD(type, name, default_value)                  \
    type name = default_value;
#include "runtime/facade/detail/runtime_counterfactual_restore_result.inc"
};

struct RuntimeCounterfactualBranchResult {
#define EF_RUNTIME_COUNTERFACTUAL_BRANCH_RESULT_FIELD(type, name, default_value)                   \
    type name = default_value;
#include "runtime/facade/detail/runtime_counterfactual_branch_result.inc"
};

struct RuntimeExperimentStepRequest {
#define EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(type, name, default_value)                        \
    type name = default_value;
#include "runtime/facade/detail/runtime_experiment_step_request.inc"
};

struct RuntimeExperimentRequest {
#define EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_experiment_request.inc"
};

struct ObservationBatchRequest {
#define EF_OBSERVATION_BATCH_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/observation_batch_request.inc"
};

struct TaskingBatchRequest {
#define EF_TASKING_BATCH_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/tasking_batch_request.inc"
};

struct EngagementBatchRequest {
#define EF_ENGAGEMENT_BATCH_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/engagement_batch_request.inc"
};

struct ExecutionBatchStepRequest {
#define EF_EXECUTION_BATCH_STEP_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/execution_batch_step_request.inc"
};

struct DeviceResidentOutputDescriptor {
#define EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(type, name, default_value)                      \
    type name = default_value;
#include "runtime/facade/detail/resident_device_output_descriptor.inc"
};

struct ObservationBatchPacket {
#define EF_OBSERVATION_BATCH_PACKET_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/observation_batch_packet.inc"
};

struct EngagementEventPacket {
#define EF_ENGAGEMENT_EVENT_PACKET_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/engagement_event_packet.inc"
};

struct TaskingBatchPacket {
#define EF_TASKING_BATCH_PACKET_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/tasking_batch_packet.inc"
};

struct ExecutionBatchStepResult {
    std::vector<ExecutionEpisodeControllerStepResult> step_results;
    std::vector<ExecutionEpisodeState> execution_episode_states;
    std::vector<double> rewards;
    std::vector<bool> terminated;
    std::vector<bool> truncated;
    std::vector<std::array<double, 4>> status_vectors;
    std::vector<std::string> termination_reasons;
    std::vector<TerminationSpec> termination_specs;
    std::vector<std::string> reward_breakdown_jsons;
    std::vector<RewardReport> reward_reports;
    std::vector<StepInfoProducts> step_infos;
    std::vector<bool> step_info_valid_flags;
    std::vector<bool> controller_state_changed_flags;
    ObservationBatchPacket observation_packet;
    TaskingBatchPacket tasking_packet;
};

struct RuntimeExperimentAncestry {
#define EF_RUNTIME_EXPERIMENT_ANCESTRY_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_experiment_ancestry.inc"
};

struct RuntimeExperimentResult {
#define EF_RUNTIME_EXPERIMENT_RESULT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_experiment_result.inc"
};

struct RuntimeWindowActionRequest {
    struct CadenceControl {
#define EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD(type, name, default_value)                         \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_cadence_control.inc"
    };

    ActionIntentPacket action_intent{};
    std::string source_layer = "facade";
    std::string input_snapshot_version;
    struct ClockDomainMetadata {
        std::string source_clock_domain = "outer_window";
        std::string relation = "nested";
        std::string clock_merge_policy;
        double source_time_s = 0.0;
        bool has_source_time = false;
        std::string source_snapshot_version;
        std::string target_window_id;
        std::vector<std::string> barrier_order;
        bool diagnostics_only = false;
        std::string diagnostics_reason;
    } clock_domain_metadata{};
    CadenceControl cadence_control{};
};

struct RuntimeWindowInputRecord {
#define EF_RUNTIME_WINDOW_INPUT_RECORD_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_window_input_record.inc"
};

struct RuntimeWindowSchedulingContext {
#define EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(type, name, default_value)                      \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_scheduling_context.inc"
};

struct RuntimeWindowBarrierRecord {
#define EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_window_barrier_record.inc"
};

struct RuntimeWindowVisibilityRecord {
#define EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD(type, name, default_value)                       \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_visibility_record.inc"
};

struct RuntimeWindowNodeExecutionRecord {
#define EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(type, name, default_value)                   \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_node_execution_record.inc"
};

struct RuntimeWindowCadence {
#define EF_RUNTIME_WINDOW_CADENCE_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_window_cadence.inc"
};

struct RuntimeWindowCadenceConfig {
#define EF_RUNTIME_WINDOW_CADENCE_CONFIG_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_window_cadence_config.inc"
};

struct RuntimeWindowCadenceTraceRecord {
#define EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(type, name, default_value)                    \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_cadence_trace_record.inc"
};

struct RuntimeWindowRequest {
#define EF_RUNTIME_WINDOW_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_window_request.inc"
};

struct RuntimeWindowResult {
#define EF_RUNTIME_WINDOW_RESULT_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_window_result.inc"
};
