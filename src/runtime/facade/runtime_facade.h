#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "runtime/facade/runtime_facade_types.h"

class IWorldBatchBackend;
struct WorldBatchVisualBindingCompatibilityScene;
struct RecentEngagementEvents;

class RuntimeFacade {
  public:
    explicit RuntimeFacade(std::size_t world_count = 0);
    explicit RuntimeFacade(const RuntimeBatchConfig &config);
    RuntimeFacade(RuntimeFacade &&) noexcept;
    RuntimeFacade &operator=(RuntimeFacade &&) noexcept;
    RuntimeFacade(const RuntimeFacade &) = delete;
    RuntimeFacade &operator=(const RuntimeFacade &) = delete;
    ~RuntimeFacade();

    void configure_batch(const RuntimeBatchConfig &config);
    RuntimeBatchConfig batch_config() const noexcept;
    RuntimeCapabilities capabilities() const noexcept;
    RuntimeBackendAdmission admit_backend_request(const RuntimeBackendRequest &request) const;
    RuntimeFidelityAdmission admit_fidelity_request(const RuntimeFidelityRequest &request) const;

    std::size_t world_count() const noexcept;
    void resize(std::size_t world_count);
    void set_worker_threads(std::size_t worker_threads) noexcept;
    std::size_t worker_threads() const noexcept;
    std::size_t effective_worker_threads() const noexcept;

    bool load_database(const std::string &path);
    bool load_unit_definitions(const std::string &path, std::string *error = nullptr);

    void reset_batch(const BatchResetRequest &request = {});
    std::vector<uint64_t>
    apply_world_setup_batch(const std::vector<uint32_t> &seeds,
                            const std::vector<WorldTerrainAssignment> &terrain_assignments,
                            const std::vector<WorldWindAssignment> &wind_assignments,
                            const std::vector<WorldZoneDefinition> &zones,
                            const std::vector<WorldSpawnRequest> &requests,
                            const std::vector<double> &time_steps = {},
                            const std::vector<WorldSunAssignment> &sun_assignments = {});
    BatchWorldSetupResult apply_world_setup(const BatchWorldSetupRequest &request);
    RuntimeWorldLayoutResult apply_world_layout(const RuntimeWorldLayoutRequest &request);
    double world_time_step(std::size_t world_index) const;
    std::vector<std::vector<std::uint64_t>>
    get_sensor_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                   bool use_gpu = false) const;
    std::vector<std::vector<std::uint64_t>>
    get_visual_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                   double range_m = 25000.0, bool use_gpu = false) const;
    std::vector<std::vector<std::uint64_t>>
    get_comm_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                 bool use_gpu = false) const;
    // Maintained facade-owned wrapper. Candidate-id assembly stays at the
    // facade boundary while raw scene assembly remains in a named compatibility
    // helper beneath the runtime quarantine surface.
    std::vector<WorldBatchVisualBindingCompatibilityScene>
    collect_visual_binding_compatibility_scenes_batch(const std::vector<WorldEntityRef> &refs,
                                                      int downsample, bool use_gpu = false) const;
    void set_pilot_actions_batch(const std::vector<WorldPilotActionAssignment> &assignments);
    std::vector<LaunchEvent>
    apply_launch_requests_batch(const std::vector<LaunchRequest> &requests);
    void set_mission_commands_maintained_batch(
        const std::vector<WorldMissionCommandMaintainedAssignment> &assignments);
    void set_task_orders_maintained_batch(
        const std::vector<WorldTaskOrderMaintainedAssignment> &assignments);
    std::vector<TaskOrderMaintainedBatchContract>
    get_task_orders_maintained_batch(const std::vector<WorldEntityRef> &refs) const;
    void set_leader_intents_maintained_batch(
        const std::vector<WorldLeaderIntentMaintainedAssignment> &assignments);
    void set_pilot_reports_maintained_batch(
        const std::vector<WorldPilotReportMaintainedAssignment> &assignments);
    void step_batch();
    std::vector<AgentObservation>
    get_agent_observations_batch(const std::vector<WorldEntityRef> &refs) const;
    std::vector<InstrumentState>
    get_instrument_states_batch(const std::vector<WorldEntityRef> &refs) const;
    std::vector<MissionCommandMaintainedBatchContract>
    get_mission_commands_maintained_batch(const std::vector<WorldEntityRef> &refs) const;
    std::vector<LeaderIntentMaintainedBatchContract>
    get_leader_intents_maintained_batch(const std::vector<WorldEntityRef> &refs) const;
    std::vector<PilotReportMaintainedBatchContract>
    get_pilot_reports_maintained_batch(const std::vector<WorldEntityRef> &refs) const;
    ObservationBatchPacket export_observation_packet(const std::vector<WorldEntityRef> &refs) const;
    ObservationBatchPacket export_observation_packet(const ObservationBatchRequest &request) const;
    TaskingBatchPacket export_tasking_packet(const TaskingBatchRequest &request) const;
    EngagementEventPacket
    export_engagement_event_packet(const EngagementBatchRequest &request) const;
    std::vector<DiagnosticsTrace>
    export_diagnostics_traces(const EngagementBatchRequest &request) const;
    RuntimeWindowResult run_window(const RuntimeWindowRequest &request);

  private:
    RecentEngagementEvents export_recent_engagement_events_for_world(std::size_t world_index) const;
    std::vector<WorldBatchVisualBindingCompatibilityScene>
    collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(
        const std::vector<WorldEntityRef> &refs,
        const std::vector<std::vector<std::uint64_t>> &candidate_ids_batch, int downsample) const;
    ObservationBatchPacket build_observation_packet(const ObservationBatchRequest &request) const;
    TaskingBatchPacket build_tasking_packet(const TaskingBatchRequest &request) const;

    // Single execution owner. The maintained implementation is
    // FlecsCpuBackend, but the facade depends only on the internal backend SPI.
    std::unique_ptr<IWorldBatchBackend> runtime_;
};
