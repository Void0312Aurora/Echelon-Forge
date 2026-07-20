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
#define EF_RUNTIME_COUNTERFACTUAL_SNAPSHOT_FIELD(type, name, default_value) \
    type name = default_value;
#include "runtime/facade/detail/runtime_counterfactual_snapshot.inc"
};

struct RuntimeWorldlineComparison {
#define EF_RUNTIME_WORLDLINE_COMPARISON_FIELD(type, name, default_value) \
    type name = default_value;
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
    std::uint64_t world_index = 0;
    std::uint32_t seed = 42;
    std::string terrain_type;
    double wind_speed_mps = 0.0;
    double wind_dir_from_deg = 0.0;
    double wind_shear_mps_per_km = 0.0;
    bool maritime_configured = false;
    double sea_state = 0.0;
    double wave_heading_deg = 0.0;
    double wave_period_s = 8.0;
    std::vector<WorldZoneDefinition> zones;
    std::vector<WorldSpawnRequest> spawn_requests;
    std::vector<double> time_steps;
};

struct RuntimeWorldLayoutResult {
    std::uint64_t world_index = 0;
    std::vector<std::uint64_t> entity_ids;
};

struct RuntimeCounterfactualBranchRequest {
    BatchWorldSetupRequest baseline_setup;
    WorldEntityRef entity_ref;
    RuntimeFidelityRequest fidelity_request;
    std::uint64_t deterministic_seed = 0;
    std::string replay_envelope_id;
    std::string branch_point_id;
    std::string branch_worldline_id;
    std::string parent_worldline_id;
    std::string restore_barrier_id = "counterfactual_selected_slice";
    std::string cadence_reason = "selected_slice_cadence_trace_runtime_window";
    double mutation_dx = 0.0;
    double mutation_dy = 0.0;
    double mutation_dz = 0.0;
    double mutation_dvx = 0.0;
    double mutation_dvy = 0.0;
    double mutation_dvz = 0.0;
    double mutation_dheading = 0.0;
    bool allow_raw_authoritative_state_mutation = false;
    std::vector<std::string> evidence_refs;
};

struct RuntimeCounterfactualRestoreRequest {
    RuntimeCounterfactualSnapshot snapshot;
    std::string expected_worldline_id;
    std::string target_worldline_id;
    std::uint64_t target_deterministic_seed = 0;
    WorldEntityRef target_entity_ref;
    std::string restore_barrier_id = "counterfactual_selected_slice";
    bool allow_raw_authoritative_state_mutation = false;
    bool request_full_clone = false;
    bool request_resident_state_restore = false;
    bool request_exact_gpu_restore = false;
    std::vector<std::string> evidence_refs;
};

struct RuntimeCounterfactualRestoreResult {
    bool restored = false;
    std::string rejection_reason;
    RuntimeCounterfactualSnapshot restored_snapshot;
    std::vector<std::string> evidence_refs;
};

struct RuntimeCounterfactualBranchResult {
    bool admitted = false;
    std::string rejection_reason;
    RuntimeFidelityAdmission fidelity_admission;
    RuntimeCounterfactualSnapshot parent_snapshot;
    RuntimeCounterfactualSnapshot branch_snapshot;
    RuntimeWorldlineComparison comparison;
    RuntimeCounterfactualRestoreResult restore_result;
    std::vector<std::string> evidence_refs;
};

struct RuntimeExperimentStepRequest {
#define EF_RUNTIME_EXPERIMENT_STEP_REQUEST_FIELD(type, name, default_value) \
    type name = default_value;
#include "runtime/facade/detail/runtime_experiment_step_request.inc"
};

struct RuntimeExperimentRequest {
#define EF_RUNTIME_EXPERIMENT_REQUEST_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_experiment_request.inc"
};

struct ObservationBatchRequest {
    std::vector<WorldEntityRef> refs;
    bool include_agent_observations = true;
    bool include_instrument_states = false;
};

struct TaskingBatchRequest {
    std::vector<WorldEntityRef> refs;
    bool include_mission_command_contracts = false;
    bool include_task_order_contracts = false;
    bool include_leader_intent_contracts = false;
    bool include_pilot_report_contracts = false;
};

struct EngagementBatchRequest {
    std::vector<EngagementEntityRef> refs;
    std::vector<std::uint64_t> trace_ids;
    bool include_track_packets = true;
    bool include_launch_requests = true;
    bool include_launch_events = true;
    bool include_munition_lifecycle_packets = true;
    bool include_effects_events = true;
    bool include_damage_reports = true;
    bool include_diagnostics_traces = true;
};

struct ExecutionBatchStepRequest {
    std::vector<WorldExecutionEpisodeStepRequest> step_requests;
    bool include_agent_observations = true;
    bool include_instrument_states = false;
};

struct DeviceResidentOutputDescriptor {
#define EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(type, name, default_value) \
    type name = default_value;
#include "runtime/facade/detail/resident_device_output_descriptor.inc"
};

struct ObservationBatchPacket {
    std::uint64_t snapshot_version = 0;
    std::string barrier_id = "export";
    double source_time_s = 0.0;
    InformationStateSource provenance = make_information_state_source(
        kPolicyInformationStateAgentObservation, kPolicySourceLabelFacadeObservationPacket,
        kPolicyMaintainedStatusMaintained);
    std::vector<WorldEntityRef> refs;
    std::vector<AgentObservation> agent_observations;
    std::vector<InstrumentState> instrument_states;
};

struct EngagementEventPacket {
    std::uint64_t snapshot_version = 0;
    std::string barrier_id = "export";
    std::uint64_t barrier_sequence = 0;
    std::string barrier_detail = "maintained_facade_export";
    double source_time_s = 0.0;
    std::string producer_node_id;
    InformationStateSource packet_provenance = make_information_state_source(
        kPolicyInformationStateTrackState, kPolicySourceLabelTrackStatePacket,
        kPolicyMaintainedStatusMaintained);
    InformationStateSource diagnostics_provenance = make_information_state_source(
        kPolicyInformationStateDecisionBelief, kPolicySourceLabelWorldTruthDiagnostics,
        kPolicyMaintainedStatusDiagnosticsOnly);
    std::vector<EngagementEntityRef> refs;
    std::vector<std::uint64_t> trace_ids;
    std::vector<TrackPacket> track_packets;
    std::vector<LaunchRequest> launch_requests;
    std::vector<LaunchEvent> launch_events;
    std::vector<MunitionLifecyclePacket> munition_lifecycle_packets;
    std::vector<EffectsEvent> effects_events;
    std::vector<NearestApproachEvent> nearest_approach_events;
    std::vector<FuzeEvaluationEvent> fuze_evaluation_events;
    std::vector<WarheadMechanismEvent> warhead_mechanism_events;
    std::vector<SpatialCoverageEvent> spatial_coverage_events;
    std::vector<ComponentLoadEvent> component_load_events;
    std::vector<ComponentDamageEvent> component_damage_events;
    std::vector<PlatformConsequenceEvent> platform_consequence_events;
    std::vector<StructuralBreakupEvent> structural_breakup_events;
    std::vector<LifecycleTransitionEvent> lifecycle_transition_events;
    std::vector<TrainingProjectionEvent> training_projection_events;
    std::vector<DamageReport> damage_reports;
    std::vector<DiagnosticsTrace> diagnostics_traces;
};

struct TaskingBatchPacket {
    std::uint64_t snapshot_version = 0;
    std::string barrier_id = "tasking_export";
    double source_time_s = 0.0;
    InformationStateSource provenance = make_information_state_source(
        kPolicyInformationStateDecisionBelief, "facade_tasking_packet",
        kPolicyMaintainedStatusAdapterProjection);
    std::vector<WorldEntityRef> refs;
    std::vector<MissionCommandMaintainedBatchContract> mission_command_contracts;
    std::vector<TaskOrderMaintainedBatchContract> task_order_contracts;
    std::vector<LeaderIntentMaintainedBatchContract> leader_intent_contracts;
    std::vector<PilotReportMaintainedBatchContract> pilot_report_contracts;
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
#define EF_RUNTIME_WINDOW_CADENCE_CONTROL_FIELD(type, name, default_value) \
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
#define EF_RUNTIME_WINDOW_SCHEDULING_CONTEXT_FIELD(type, name, default_value) \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_scheduling_context.inc"
};

struct RuntimeWindowBarrierRecord {
#define EF_RUNTIME_WINDOW_BARRIER_RECORD_FIELD(type, name, default_value) \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_barrier_record.inc"
};

struct RuntimeWindowVisibilityRecord {
#define EF_RUNTIME_WINDOW_VISIBILITY_RECORD_FIELD(type, name, default_value) \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_visibility_record.inc"
};

struct RuntimeWindowNodeExecutionRecord {
#define EF_RUNTIME_WINDOW_NODE_EXECUTION_RECORD_FIELD(type, name, default_value) \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_node_execution_record.inc"
};

struct RuntimeWindowCadence {
#define EF_RUNTIME_WINDOW_CADENCE_FIELD(type, name, default_value) type name = default_value;
#include "runtime/facade/detail/runtime_window_cadence.inc"
};

struct RuntimeWindowCadenceConfig {
#define EF_RUNTIME_WINDOW_CADENCE_CONFIG_FIELD(type, name, default_value) \
    type name = default_value;
#include "runtime/facade/detail/runtime_window_cadence_config.inc"
};

struct RuntimeWindowCadenceTraceRecord {
#define EF_RUNTIME_WINDOW_CADENCE_TRACE_RECORD_FIELD(type, name, default_value) \
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
