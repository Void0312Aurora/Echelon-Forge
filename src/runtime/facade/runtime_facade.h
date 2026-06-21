#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "runtime/facade/runtime_facade_types.h"

class WorldBatchRuntime;
struct WorldBatchVisualBindingCompatibilityScene;
struct RecentEngagementEvents;

class RuntimeFacade {
public:
    explicit RuntimeFacade(std::size_t world_count = 0);
    explicit RuntimeFacade(const RuntimeBatchConfig& config);
    RuntimeFacade(RuntimeFacade&&) noexcept;
    RuntimeFacade& operator=(RuntimeFacade&&) noexcept;
    RuntimeFacade(const RuntimeFacade&) = delete;
    RuntimeFacade& operator=(const RuntimeFacade&) = delete;
    ~RuntimeFacade();

    void configure_batch(const RuntimeBatchConfig& config);
    RuntimeBatchConfig batch_config() const noexcept;
    RuntimeCapabilities capabilities() const noexcept;
    RuntimeFidelityAdmission admit_fidelity_request(
        const RuntimeFidelityRequest& request
    ) const;
    RuntimeCounterfactualSnapshot snapshot_counterfactual_entity(
        const WorldEntityRef& ref,
        const RuntimeFidelityAdmission& fidelity_admission,
        const std::string& cadence_reason,
        const std::vector<std::string>& evidence_refs
    );
    RuntimeCounterfactualRestoreResult restore_counterfactual_snapshot(
        const RuntimeCounterfactualRestoreRequest& request
    );
    RuntimeCounterfactualBranchResult run_counterfactual_branch(
        const RuntimeCounterfactualBranchRequest& request
    );
    RuntimeExperimentResult run_counterfactual_experiment(
        const RuntimeExperimentRequest& request
    );

    std::size_t world_count() const noexcept;
    void resize(std::size_t world_count);
    void set_worker_threads(std::size_t worker_threads) noexcept;
    std::size_t worker_threads() const noexcept;
    std::size_t effective_worker_threads() const noexcept;

    bool load_database(const std::string& path);
    bool load_unit_definitions(const std::string& path, std::string* error = nullptr);

    void reset_batch(const BatchResetRequest& request = {});
    std::vector<uint64_t> apply_world_setup_batch(
        const std::vector<uint32_t>& seeds,
        const std::vector<WorldTerrainAssignment>& terrain_assignments,
        const std::vector<WorldWindAssignment>& wind_assignments,
        const std::vector<WorldZoneDefinition>& zones,
        const std::vector<WorldSpawnRequest>& requests,
        const std::vector<double>& time_steps = {}
    );
    BatchWorldSetupResult apply_world_setup(const BatchWorldSetupRequest& request);
    RuntimeWorldLayoutResult apply_world_layout(const RuntimeWorldLayoutRequest& request);
    double world_time_step(std::size_t world_index) const;
    std::vector<std::vector<std::uint64_t>> get_sensor_candidate_ids_batch(
        const std::vector<WorldEntityRef>& refs,
        bool use_gpu = false
    ) const;
    std::vector<std::vector<std::uint64_t>> get_visual_candidate_ids_batch(
        const std::vector<WorldEntityRef>& refs,
        double range_m = 25000.0,
        bool use_gpu = false
    ) const;
    std::vector<std::vector<std::uint64_t>> get_comm_candidate_ids_batch(
        const std::vector<WorldEntityRef>& refs,
        bool use_gpu = false
    ) const;
    // Maintained facade-owned wrapper. Candidate-id assembly stays at the
    // facade boundary while raw scene assembly remains in a named compatibility
    // helper beneath the runtime quarantine surface.
    std::vector<WorldBatchVisualBindingCompatibilityScene>
    collect_visual_binding_compatibility_scenes_batch(
        const std::vector<WorldEntityRef>& refs,
        int downsample,
        bool use_gpu = false
    ) const;
    void set_pilot_actions_batch(const std::vector<WorldPilotActionAssignment>& assignments);
    std::vector<LaunchEvent> apply_launch_requests_batch(const std::vector<LaunchRequest>& requests);
    void set_mission_commands_maintained_batch(
        const std::vector<WorldMissionCommandMaintainedAssignment>& assignments
    );
    void set_task_orders_maintained_batch(
        const std::vector<WorldTaskOrderMaintainedAssignment>& assignments
    );
    std::vector<TaskOrderMaintainedBatchContract> get_task_orders_maintained_batch(
        const std::vector<WorldEntityRef>& refs
    ) const;
    void set_leader_intents_maintained_batch(
        const std::vector<WorldLeaderIntentMaintainedAssignment>& assignments
    );
    void set_pilot_reports_maintained_batch(
        const std::vector<WorldPilotReportMaintainedAssignment>& assignments
    );
    void step_batch();
    void clear_execution_episode_batch() noexcept;
    void prime_execution_episode_batch(
        const std::vector<WorldEntityRef>& refs,
        const std::vector<ExecutionEpisodeState>& states
    );
    bool execution_episode_ready(std::size_t world_index) const noexcept;
    std::vector<ExecutionEpisodeState> export_execution_episode_states(
        const std::vector<WorldEntityRef>& refs
    ) const;

    std::vector<ExecutionEpisodeRuntimeProducts> evaluate_execution_batch(
        const std::vector<WorldExecutionEpisodeStepRequest>& requests
    ) const;
    std::vector<ExecutionEpisodeRuntimeProducts> step_execution_products_batch(
        const std::vector<WorldExecutionEpisodeStepRequest>& requests
    );
    ExecutionBatchStepResult step_execution_batch(const ExecutionBatchStepRequest& request);
    std::vector<AgentObservation> get_agent_observations_batch(const std::vector<WorldEntityRef>& refs) const;
    std::vector<InstrumentState> get_instrument_states_batch(const std::vector<WorldEntityRef>& refs) const;
    std::vector<MissionCommandMaintainedBatchContract>
    get_mission_commands_maintained_batch(const std::vector<WorldEntityRef>& refs) const;
    std::vector<LeaderIntentMaintainedBatchContract>
    get_leader_intents_maintained_batch(const std::vector<WorldEntityRef>& refs) const;
    std::vector<PilotReportMaintainedBatchContract>
    get_pilot_reports_maintained_batch(const std::vector<WorldEntityRef>& refs) const;
    ObservationBatchPacket export_observation_packet(const std::vector<WorldEntityRef>& refs) const;
    ObservationBatchPacket export_observation_packet(const ObservationBatchRequest& request) const;
    TaskingBatchPacket export_tasking_packet(const TaskingBatchRequest& request) const;
    EngagementEventPacket export_engagement_event_packet(const EngagementBatchRequest& request) const;
    std::vector<DiagnosticsTrace> export_diagnostics_traces(const EngagementBatchRequest& request) const;
    RuntimeWindowResult run_window(const RuntimeWindowRequest& request);

private:
    bool counterfactual_world_index_valid(std::uint64_t world_index) const noexcept;
    bool apply_counterfactual_delta(
        const WorldEntityRef& ref,
        const RuntimeCounterfactualBranchRequest& request
    );
    bool restore_counterfactual_entity(
        const WorldEntityRef& target_ref,
        const RuntimeCounterfactualSnapshot& snapshot
    );
    RecentEngagementEvents export_recent_engagement_events_for_world(
        std::size_t world_index
    ) const;
    std::vector<WorldBatchVisualBindingCompatibilityScene>
    collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(
        const std::vector<WorldEntityRef>& refs,
        const std::vector<std::vector<std::uint64_t>>& candidate_ids_batch,
        int downsample
    ) const;
    ObservationBatchPacket build_observation_packet(
        const ObservationBatchRequest& request
    ) const;
    TaskingBatchPacket build_tasking_packet(const TaskingBatchRequest& request) const;
    void register_counterfactual_worldline_snapshot(
        const RuntimeCounterfactualSnapshot& snapshot
    );

    struct CounterfactualWorldlineRegistry;
    std::unique_ptr<WorldBatchRuntime> runtime_;
    std::unique_ptr<CounterfactualWorldlineRegistry> counterfactual_worldlines_;
};
