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
    bool supports_batch_runtime = false;
    bool supports_compiled_episode_controller = false;
    bool supports_compiled_execution_step = false;
    bool supports_gpu_visual = false;
    bool supports_gpu_observation = false;
    bool supports_gpu_flight_shaping = false;
    bool supports_device_observation_view = false;
    bool supports_resident_state = false;
    bool supports_exact_gpu_backend = false;
    bool supports_shadow_compare = false;
    std::string maintained_baseline_backend_profile_id;
    std::string maintained_baseline_parity_budget_ref;
    std::string maintained_baseline_profile_status;
    std::string device_observation_view_candidate_profile_id;
    std::string device_observation_view_rejection_reason;
    std::string exact_gpu_backend_candidate_profile_id;
    std::string exact_gpu_backend_rejection_reason;
    std::string resident_state_candidate_profile_id;
    std::string resident_state_candidate_parity_budget_ref;
    std::string resident_state_rejection_reason;
    std::string shadow_compare_candidate_profile_id;
    std::string shadow_compare_candidate_parity_budget_ref;
    std::string shadow_compare_rejection_reason;
    std::string multi_fidelity_rejection_reason;
};

struct RuntimeBatchConfig {
    std::size_t world_count = 0;
    std::size_t worker_threads = 1;
};

struct RuntimeFidelityRequest {
    std::string request_label;
    std::string backend_profile_id;
    std::string parity_budget_ref;
    std::string provider_family = "none";
    std::vector<std::string> model_family_scope;
    std::string validation_gate;
    std::vector<std::string> facade_evidence_refs;
};

struct RuntimeFidelityAdmission {
    bool admitted = false;
    bool baseline_exact_evaluation = false;
    std::string request_label;
    std::string backend_profile_id;
    std::string parity_budget_ref;
    std::string requested_provider_family = "none";
    std::string selected_provider_family = "none";
    std::string selected_stage_node_id;
    std::string rejection_reason;
    std::vector<std::string> errors;
    std::vector<std::string> evidence_refs;
};

struct RuntimeCounterfactualSnapshot {
    std::string worldline_id;
    std::string parent_worldline_id;
    std::uint64_t deterministic_seed = 0;
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double vx = 0.0;
    double vy = 0.0;
    double vz = 0.0;
    double heading = 0.0;
    double pitch = 0.0;
    double roll = 0.0;
    std::uint64_t snapshot_version = 0;
    std::string barrier_id = "counterfactual_selected_slice";
    std::string fidelity_profile_id;
    std::string provider_family;
    std::string selected_stage_node_id;
    std::string cadence_reason;
    std::vector<std::string> evidence_refs;
};

struct RuntimeWorldlineComparison {
    bool comparable = false;
    std::string comparison_id;
    std::string parent_worldline_id;
    std::string branch_worldline_id;
    std::string barrier_id = "counterfactual_selected_slice";
    double dx = 0.0;
    double dy = 0.0;
    double dz = 0.0;
    double dvx = 0.0;
    double dvy = 0.0;
    double dvz = 0.0;
    double dheading = 0.0;
    std::vector<std::string> evidence_refs;
};

struct BatchResetRequest {
    std::vector<std::uint32_t> seeds;
};

struct BatchWorldSetupRequest {
    std::vector<std::uint32_t> seeds;
    std::vector<WorldTerrainAssignment> terrain_assignments;
    std::vector<WorldWindAssignment> wind_assignments;
    std::vector<WorldZoneDefinition> zones;
    std::vector<WorldSpawnRequest> spawn_requests;
    std::vector<TypedPlatformSpawnRequest> typed_platform_spawn_requests;
    std::vector<double> time_steps;
};

struct BatchWorldSetupResult {
    std::vector<std::uint64_t> entity_ids;
    std::vector<TypedPlatformSpawnResult> typed_platform_spawn_results;
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
    std::string cadence_reason =
        "selected_slice_cadence_trace_runtime_window_wp17c";
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
    ExecutionEpisodeState state;
    WorldExecutionEpisodeStepRequest request;
    std::string observation_ref;
    std::string profile_ref;
    std::string claim_scope =
        std::string(
            runtime::counterfactual::kExperimentProfileClaimScopeDescriptive
        );
    std::vector<std::string> evidence_refs;
};

struct RuntimeExperimentRequest {
    RuntimeCounterfactualBranchRequest branch_request;
    std::vector<RuntimeExperimentStepRequest> parent_step_requests;
    std::vector<RuntimeExperimentStepRequest> branch_step_requests;
    std::vector<std::uint64_t> trace_ids;
    std::string experiment_run_id;
    std::string comparison_id;
    std::string setup_ref;
    std::string generation_ref;
    std::string generated_input_ref;
    std::string generated_input_kind =
        std::string(
            runtime::counterfactual::kScenarioGenerationKindScenarioVariation
        );
    std::string generated_input_source =
        std::string(
            runtime::counterfactual::kScenarioGenerationSourceCounterfactualBranch
        );
    std::string generated_input_generator_version =
        "RuntimeFacade.run_counterfactual_experiment.wp21";
    std::string generated_input_baseline_scenario_ref;
    std::vector<std::string> generated_input_evidence_refs;
    std::vector<std::string> capability_refs;
    bool include_observations = true;
    bool include_diagnostics_traces = true;
    bool include_generated_input_ref = true;
    bool truth_claim = false;
    bool promoted_to_support = false;
    std::vector<std::string> evidence_refs;
};

struct ObservationBatchRequest {
    std::vector<WorldEntityRef> refs;
    bool include_agent_observations = true;
    bool include_instrument_states = false;
    bool include_mission_commands = false;
    bool include_task_orders = false;
    bool include_leader_intents = false;
    bool include_pilot_reports = false;
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
    bool include_mission_commands = false;
    bool include_task_orders = false;
    bool include_leader_intents = false;
    bool include_pilot_reports = false;
};

struct DeviceResidentOutputDescriptor {
    std::vector<std::uint64_t> output_shape;
    std::string dtype;
    std::size_t element_count = 0;
    std::uint64_t source_snapshot = 0;
    std::string sync_or_export_barrier;
    std::string host_visible_availability = "unavailable";
    std::string diagnostics_label = "diagnostics_only";
    std::vector<std::string> consumer_constraints;
};

struct ObservationBatchPacket {
    std::uint64_t snapshot_version = 0;
    std::string barrier_id = "export";
    double source_time_s = 0.0;
    InformationStateSource provenance = make_information_state_source(
        kPolicyInformationStateAgentObservation,
        kPolicySourceLabelFacadeObservationPacket,
        kPolicyMaintainedStatusMaintained
    );
    std::vector<WorldEntityRef> refs;
    std::vector<AgentObservation> agent_observations;
    std::vector<InstrumentState> instrument_states;
    std::vector<MissionCommand> mission_commands;
    std::vector<TaskOrder> task_orders;
    std::vector<LeaderIntent> leader_intents;
    std::vector<PilotReport> pilot_reports;
};

struct EngagementEventPacket {
    std::uint64_t snapshot_version = 0;
    std::string barrier_id = "export";
    std::uint64_t barrier_sequence = 0;
    std::string barrier_detail = "maintained_facade_export";
    double source_time_s = 0.0;
    std::string producer_node_id;
    InformationStateSource packet_provenance = make_information_state_source(
        kPolicyInformationStateTrackState,
        kPolicySourceLabelTrackStatePacket,
        kPolicyMaintainedStatusMaintained
    );
    InformationStateSource diagnostics_provenance = make_information_state_source(
        kPolicyInformationStateDecisionBelief,
        kPolicySourceLabelWorldTruthDiagnostics,
        kPolicyMaintainedStatusDiagnosticsOnly
    );
    std::vector<EngagementEntityRef> refs;
    std::vector<std::uint64_t> trace_ids;
    std::vector<TrackPacket> track_packets;
    std::vector<LaunchRequest> launch_requests;
    std::vector<LaunchEvent> launch_events;
    std::vector<MunitionLifecyclePacket> munition_lifecycle_packets;
    std::vector<EffectsEvent> effects_events;
    std::vector<DamageReport> damage_reports;
    std::vector<DiagnosticsTrace> diagnostics_traces;
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
};

struct RuntimeExperimentAncestry {
    bool evidence_bridge_valid = false;
    bool evidence_bridge_fail_closed = false;
    std::string evidence_bridge_rejection_reason;
    std::vector<std::string> evidence_bridge_errors;
    std::string counterfactual_request_ref;
    std::string counterfactual_admission_ref;
    std::string setup_ref;
    std::string generation_ref;
    std::string replay_envelope_ref;
    std::string branch_point_ref;
    std::string generated_input_ref;
    std::string backend_profile_ref;
    std::string fidelity_profile_ref;
    std::vector<std::string> capability_refs;
    std::vector<std::string> profile_observation_refs;
    std::vector<std::string> evidence_refs;
};

struct RuntimeExperimentResult {
    bool admitted = false;
    std::string rejection_reason;
    RuntimeCounterfactualBranchResult branch_result;
    ObservationBatchPacket parent_observation_packet;
    ObservationBatchPacket branch_observation_packet;
    ExecutionBatchStepResult parent_step_result;
    ExecutionBatchStepResult branch_step_result;
    std::vector<DiagnosticsTrace> parent_diagnostics_traces;
    std::vector<DiagnosticsTrace> branch_diagnostics_traces;
    RuntimeExperimentAncestry ancestry;
    std::vector<std::string> evidence_refs;
};

struct RuntimeWindowActionRequest {
    struct CadenceControl {
        ActionHoldPolicy hold_policy{};
        bool enabled = false;
        bool has_expiry_time = false;
        double expiry_time_s = 0.0;
        std::string source_cadence_domain = "control";
        std::uint32_t source_tick = 0;
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
    RuntimeWindowActionRequest request{};
    std::string reason;
};

struct RuntimeWindowSchedulingContext {
    std::string window_id;
    std::uint64_t world_id = 0;
    double source_time_s = 0.0;
    std::uint64_t barrier_sequence = 0;
    std::string current_barrier_id;
    std::vector<RuntimeWindowInputRecord> accepted_inputs;
    std::vector<RuntimeWindowInputRecord> deferred_inputs;
    std::vector<RuntimeWindowInputRecord> rejected_inputs;
    std::vector<RuntimeWindowInputRecord> expired_inputs;
};

struct RuntimeWindowBarrierRecord {
    std::uint64_t sequence = 0;
    std::string barrier_id;
    std::string node_id;
};

struct RuntimeWindowVisibilityRecord {
    std::string barrier_id;
    std::size_t visible_input_count = 0;
};

struct RuntimeWindowNodeExecutionRecord {
    std::string node_id;
    std::string clock_domain;
    std::string read_snapshot_policy;
    std::string write_commit_policy;
    std::size_t visible_input_count = 0;
    std::string execution_state = "skipped";
    std::string decision_reason;
    std::string trigger_source;
    std::string decision_barrier_id;
    std::string clock_merge_policy;
    std::string source_snapshot_version;
    double source_time_s = 0.0;
    std::string target_window_id;
    std::vector<std::string> barrier_order;
};

struct RuntimeWindowCadence {
    std::string domain = "control";
    std::uint32_t tick_count = 1;
    double interval_s = 0.0;
    std::string merge_policy = "nested_slot";
    std::string barrier_id;
};

struct RuntimeWindowCadenceConfig {
    double window_duration_s = 0.0;
    std::vector<RuntimeWindowCadence> domains;
};

struct RuntimeWindowCadenceTraceRecord {
    std::string domain;
    std::uint32_t tick = 0;
    std::string node_id;
    std::string decision = "skipped";
    std::string decision_reason;
    std::string source;
    std::string barrier_id;
    std::string clock_domain;
    std::string clock_merge_policy;
    std::string cadence_merge_policy;
    std::string relation;
    bool held = false;
    bool expired = false;
    bool deferred = false;
    bool diagnostics_only = false;
};

struct RuntimeWindowRequest {
    std::string window_id;
    std::uint64_t world_id = 0;
    double source_time_s = 0.0;
    std::vector<RuntimeWindowActionRequest> action_requests;
    ObservationBatchRequest observation_request;
    EngagementBatchRequest engagement_request;
    RuntimeWindowCadenceConfig cadence_config;
    bool export_observation = true;
    bool export_engagement = true;
    bool export_diagnostics = true;
};

struct RuntimeWindowResult {
    RuntimeWindowSchedulingContext context;
    std::vector<RuntimeWindowBarrierRecord> barrier_trace;
    std::vector<RuntimeWindowVisibilityRecord> visibility_trace;
    std::vector<RuntimeWindowNodeExecutionRecord> executed_nodes;
    RuntimeWindowCadenceConfig cadence_config;
    std::vector<RuntimeWindowCadenceTraceRecord> cadence_trace;
    std::vector<RuntimeWindowInputRecord> injected_inputs;
    ObservationBatchPacket observation_packet;
    EngagementEventPacket engagement_packet;
    std::vector<DiagnosticsTrace> diagnostics_traces;
};
