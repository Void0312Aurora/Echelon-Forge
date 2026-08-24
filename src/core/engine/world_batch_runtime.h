#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "components/physics/instruments.h"
#include "core/engine/simulation_kernel.h"
#include "core/engine/world_batch_visual_binding_compatibility_types.h"
#include "core/interfaces/observation.h"
#include "core/mission/episode/execution_episode_controller.h"
#include "runtime/contracts/world_batch_contracts.h"

struct WorldEntityKinematics {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double vx = 0.0;
    double vy = 0.0;
    double vz = 0.0;
    double heading = 0.0;
    double pitch = 0.0;
    double roll = 0.0;
};

struct WorldCompositionDiagnostics {
    std::size_t world_index = 0;
    std::string requested_manifest_sha256;
    std::string resolved_manifest_sha256;
    std::string executable_graph_sha256;
    std::array<std::uint64_t, 5> scope_generations{};
};

class WorldBatchRuntime {
  public:
    explicit WorldBatchRuntime(size_t world_count = 0);
    WorldBatchRuntime(const WorldBatchRuntime &) = delete;
    WorldBatchRuntime &operator=(const WorldBatchRuntime &) = delete;
    WorldBatchRuntime(WorldBatchRuntime &&) noexcept = default;
    WorldBatchRuntime &operator=(WorldBatchRuntime &&) noexcept = default;
    ~WorldBatchRuntime() = default;

    size_t world_count() const noexcept { return worlds_.size(); }
    void resize(size_t world_count);
    void set_worker_threads(size_t worker_threads) noexcept { worker_threads_ = worker_threads; }
    size_t worker_threads() const noexcept { return worker_threads_; }
    size_t effective_worker_threads() const noexcept;

    std::uint64_t spawn_unit_from_world_spawn_request(const WorldSpawnRequest &request);
    std::uint64_t spawn_typed_platform_unit(const TypedPlatformSpawnRequest &request);
    bool try_get_entity_kinematics(const WorldEntityRef &ref, WorldEntityKinematics *state) const;
    bool try_set_entity_kinematics(const WorldEntityRef &ref, const WorldEntityKinematics &state);
    RecentEngagementEvents export_recent_engagement_events(size_t world_index) const;
    [[nodiscard]] std::vector<WorldCompositionDiagnostics> composition_diagnostics() const;

    // Raw escape hatch only. Maintained facade code should
    // use batch-owned helper methods instead of keeping raw SimulationKernel handles.
    SimulationKernel &world_raw_quarantine(size_t index);
    const SimulationKernel &world_raw_quarantine(size_t index) const;

    void reset_batch(const std::vector<uint32_t> &seeds = {});
    void step_batch();
    void step_worlds(const std::vector<uint64_t> &world_indices);

    bool load_database(const std::string &path);
    bool load_unit_definitions(const std::string &path, std::string *error = nullptr);
    void set_time_step(double dt);
    void set_terrain_types_batch(const std::vector<WorldTerrainAssignment> &assignments);
    void set_winds_batch(const std::vector<WorldWindAssignment> &assignments);
    void set_suns_batch(const std::vector<WorldSunAssignment> &assignments);
    void clear_zones_batch(const std::vector<uint64_t> &world_indices = {});
    void add_zones_batch(const std::vector<WorldZoneDefinition> &zones);
    std::vector<uint64_t> spawn_units_batch(const std::vector<WorldSpawnRequest> &requests);
    std::vector<uint64_t>
    apply_world_setup_batch(const std::vector<uint32_t> &seeds,
                            const std::vector<WorldTerrainAssignment> &terrain_assignments,
                            const std::vector<WorldWindAssignment> &wind_assignments,
                            const std::vector<WorldZoneDefinition> &zones,
                            const std::vector<WorldSpawnRequest> &requests,
                            const std::vector<double> &time_steps = {},
                            const std::vector<WorldSunAssignment> &sun_assignments = {});
    std::vector<uint64_t> apply_world_layout(
        std::size_t world_index, std::uint32_t seed, const std::string &terrain_type,
        double wind_speed_mps, double wind_dir_from_deg, double wind_shear_mps_per_km,
        bool maritime_configured, double sea_state, double wave_heading_deg, double wave_period_s,
        const std::vector<WorldZoneDefinition> &zones,
        const std::vector<WorldSpawnRequest> &requests, const std::vector<double> &time_steps = {},
        double sun_azimuth_deg = 0.0, double sun_elevation_deg = 45.0);
    double world_time_step(std::size_t world_index) const;

    void set_pilot_actions_batch(const std::vector<WorldPilotActionAssignment> &assignments);
    std::vector<LaunchEvent>
    apply_launch_requests_batch(const std::vector<LaunchRequest> &requests);
    void set_mission_commands_batch(const std::vector<WorldMissionCommandAssignment> &assignments);
    void set_mission_commands_maintained_batch(
        const std::vector<WorldMissionCommandMaintainedAssignment> &assignments);
    std::vector<MissionCommandMaintainedBatchContract>
    get_mission_commands_maintained_batch(const std::vector<WorldEntityRef> &refs) const;
    void set_task_orders_maintained_batch(
        const std::vector<WorldTaskOrderMaintainedAssignment> &assignments);
    std::vector<TaskOrderMaintainedBatchContract>
    get_task_orders_maintained_batch(const std::vector<WorldEntityRef> &refs) const;
    void set_leader_intents_batch(const std::vector<WorldLeaderIntentAssignment> &assignments);
    void set_leader_intents_maintained_batch(
        const std::vector<WorldLeaderIntentMaintainedAssignment> &assignments);
    std::vector<LeaderIntentMaintainedBatchContract>
    get_leader_intents_maintained_batch(const std::vector<WorldEntityRef> &refs) const;
    void set_pilot_reports_batch(const std::vector<WorldPilotReportAssignment> &assignments);
    void set_pilot_reports_maintained_batch(
        const std::vector<WorldPilotReportMaintainedAssignment> &assignments);
    std::vector<PilotReportMaintainedBatchContract>
    get_pilot_reports_maintained_batch(const std::vector<WorldEntityRef> &refs) const;

    void clear_execution_episode_controller_batch() noexcept;
    void prime_execution_episode_controller_batch(const std::vector<WorldEntityRef> &refs,
                                                  const std::vector<ExecutionEpisodeState> &states);
    bool execution_episode_controller_ready(size_t world_index) const noexcept;
    std::vector<ExecutionEpisodeState>
    export_execution_episode_states_batch(const std::vector<WorldEntityRef> &refs) const;
    std::vector<ExecutionEpisodeRuntimeProducts> evaluate_execution_episode_batch(
        const std::vector<WorldExecutionEpisodeStepRequest> &requests) const;
    std::vector<ExecutionEpisodeRuntimeProducts>
    step_execution_episode_batch(const std::vector<WorldExecutionEpisodeStepRequest> &requests);
    std::vector<ExecutionEpisodeControllerStepResult> step_execution_episode_results_batch(
        const std::vector<WorldExecutionEpisodeStepRequest> &requests);

    std::vector<AgentObservation>
    get_agent_observations_batch(const std::vector<WorldEntityRef> &refs) const;
    std::vector<InstrumentState>
    get_instrument_states_batch(const std::vector<WorldEntityRef> &refs) const;
    std::vector<MissionCommand>
    get_mission_commands_batch(const std::vector<WorldEntityRef> &refs) const;
    std::vector<LeaderIntent>
    get_leader_intents_batch(const std::vector<WorldEntityRef> &refs) const;
    std::vector<PilotReport> get_pilot_reports_batch(const std::vector<WorldEntityRef> &refs) const;

    std::vector<std::vector<uint64_t>>
    get_sensor_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                   bool use_gpu = false) const;
    std::vector<std::vector<uint64_t>>
    get_visual_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                   double range_m = 25000.0, bool use_gpu = false) const;
    std::vector<std::vector<uint64_t>>
    get_comm_candidate_ids_batch(const std::vector<WorldEntityRef> &refs,
                                 bool use_gpu = false) const;
    std::vector<WorldBatchVisualBindingCompatibilityScene>
    collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(
        const std::vector<WorldEntityRef> &refs, int downsample,
        const std::vector<std::vector<uint64_t>> &candidate_ids_batch) const;
    // Raw escape hatch only. Maintained facade code should
    // own candidate-id assembly and route scene collection through the named
    // helper above instead of adding new raw-world call sites.
    std::vector<WorldBatchVisualBindingCompatibilityScene>
    collect_visual_binding_compatibility_scenes_batch(const std::vector<WorldEntityRef> &refs,
                                                      int downsample, bool use_gpu = false) const;

  private:
    size_t resolve_worker_threads(size_t task_count) const noexcept;
    static InstrumentState safe_get_instrument_state(const SimulationKernel &world,
                                                     uint64_t entity_id);
    SimulationKernel &checked_world(size_t index);
    const SimulationKernel &checked_world(size_t index) const;
    void clear_execution_episode_controller(size_t world_index) noexcept;
    ExecutionEpisodeController &checked_execution_episode_controller(size_t world_index,
                                                                     uint64_t entity_id);
    const ExecutionEpisodeController &
    checked_execution_episode_controller(size_t world_index, uint64_t entity_id) const;
    void validate_execution_episode_step_requests(
        const std::vector<WorldExecutionEpisodeStepRequest> &requests) const;

    std::vector<std::unique_ptr<SimulationKernel>> worlds_;
    std::vector<ExecutionEpisodeController> execution_episode_controllers_;
    std::vector<uint64_t> execution_episode_controller_entity_ids_;
    std::vector<bool> execution_episode_controller_active_;
    size_t worker_threads_ = 1;
};
