#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/tasking/leader_intent.h"
#include "components/tasking/pilot_report.h"
#include "components/tasking/task_order.h"
#include "components/physics/instruments.h"
#include "core/engine/simulation_kernel.h"
#include "core/interfaces/observation.h"
#include "core/mission/execution_episode_controller.h"

struct WorldEntityRef {
    uint64_t world_index = 0;
    uint64_t entity_id = 0;
};

struct WorldTerrainAssignment {
    uint64_t world_index = 0;
    std::string terrain_type = "legacy";
};

struct WorldWindAssignment {
    uint64_t world_index = 0;
    double speed_mps = 0.0;
    double dir_from_deg = 0.0;
    double shear_mps_per_km = 0.0;
};

struct WorldZoneDefinition {
    uint64_t world_index = 0;
    std::string name = "Zone";
    double x = 0.0;
    double y = 0.0;
    double width = 1000.0;
    double length = 1000.0;
    double heading = 0.0;
    int surface_type = 3;
};

struct WorldSpawnRequest {
    uint64_t world_index = 0;
    Side side = Side::Neutral;
    std::string type_name;
    std::string entity_name;
    bool is_agent = false;
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double heading = 0.0;
    double pitch = 0.0;
    double roll = 0.0;
    double vx = 0.0;
    double vy = 0.0;
    double vz = 0.0;
};

struct WorldPilotActionAssignment {
    uint64_t world_index = 0;
    uint64_t entity_id = 0;
    PilotAction action{};
};

struct WorldMissionCommandAssignment {
    uint64_t world_index = 0;
    uint64_t entity_id = 0;
    MissionCommand command{};
};

struct WorldTaskOrderAssignment {
    uint64_t world_index = 0;
    uint64_t entity_id = 0;
    TaskOrder order{};
};

struct WorldLeaderIntentAssignment {
    uint64_t world_index = 0;
    uint64_t entity_id = 0;
    LeaderIntent intent{};
};

struct WorldPilotReportAssignment {
    uint64_t world_index = 0;
    uint64_t entity_id = 0;
    PilotReport report{};
};

struct WorldExecutionEpisodeStepRequest {
    uint64_t world_index = 0;
    uint64_t entity_id = 0;
    StepEvaluationBatchConfig config{};
    StepEvaluationBatchEnvState env_state{};
};

class WorldBatchRuntime {
public:
    explicit WorldBatchRuntime(size_t world_count = 0);
    WorldBatchRuntime(const WorldBatchRuntime&) = delete;
    WorldBatchRuntime& operator=(const WorldBatchRuntime&) = delete;
    WorldBatchRuntime(WorldBatchRuntime&&) noexcept = default;
    WorldBatchRuntime& operator=(WorldBatchRuntime&&) noexcept = default;
    ~WorldBatchRuntime() = default;

    size_t world_count() const noexcept { return worlds_.size(); }
    void resize(size_t world_count);
    void set_worker_threads(size_t worker_threads) noexcept { worker_threads_ = worker_threads; }
    size_t worker_threads() const noexcept { return worker_threads_; }
    size_t effective_worker_threads() const noexcept;

    SimulationKernel& world(size_t index);
    const SimulationKernel& world(size_t index) const;

    void reset_batch(const std::vector<uint32_t>& seeds = {});
    void step_batch();
    void step_worlds(const std::vector<uint64_t>& world_indices);

    bool load_database(const std::string& path);
    bool load_unit_definitions(const std::string& path, std::string* error = nullptr);
    void set_time_step(double dt);
    void set_terrain_types_batch(const std::vector<WorldTerrainAssignment>& assignments);
    void set_winds_batch(const std::vector<WorldWindAssignment>& assignments);
    void clear_zones_batch(const std::vector<uint64_t>& world_indices = {});
    void add_zones_batch(const std::vector<WorldZoneDefinition>& zones);
    std::vector<uint64_t> spawn_units_batch(const std::vector<WorldSpawnRequest>& requests);
    std::vector<uint64_t> apply_world_setup_batch(
        const std::vector<uint32_t>& seeds,
        const std::vector<WorldTerrainAssignment>& terrain_assignments,
        const std::vector<WorldWindAssignment>& wind_assignments,
        const std::vector<WorldZoneDefinition>& zones,
        const std::vector<WorldSpawnRequest>& requests,
        const std::vector<double>& time_steps = {}
    );

    void set_pilot_actions_batch(const std::vector<WorldPilotActionAssignment>& assignments);
    void set_mission_commands_batch(const std::vector<WorldMissionCommandAssignment>& assignments);
    void set_task_orders_batch(const std::vector<WorldTaskOrderAssignment>& assignments);
    void set_leader_intents_batch(const std::vector<WorldLeaderIntentAssignment>& assignments);
    void set_pilot_reports_batch(const std::vector<WorldPilotReportAssignment>& assignments);

    void clear_execution_episode_controller_batch() noexcept;
    void prime_execution_episode_controller_batch(
        const std::vector<WorldEntityRef>& refs,
        const std::vector<ExecutionEpisodeState>& states
    );
    bool execution_episode_controller_ready(size_t world_index) const noexcept;
    std::vector<ExecutionEpisodeState> export_execution_episode_states_batch(
        const std::vector<WorldEntityRef>& refs
    ) const;
    std::vector<ExecutionEpisodeRuntimeProducts> evaluate_execution_episode_batch(
        const std::vector<WorldExecutionEpisodeStepRequest>& requests
    ) const;
    std::vector<ExecutionEpisodeRuntimeProducts> step_execution_episode_batch(
        const std::vector<WorldExecutionEpisodeStepRequest>& requests
    );
    std::vector<ExecutionEpisodeControllerStepResult> step_execution_episode_results_batch(
        const std::vector<WorldExecutionEpisodeStepRequest>& requests
    );

    std::vector<AgentObservation> get_agent_observations_batch(const std::vector<WorldEntityRef>& refs) const;
    std::vector<InstrumentState> get_instrument_states_batch(const std::vector<WorldEntityRef>& refs) const;
    std::vector<MissionCommand> get_mission_commands_batch(const std::vector<WorldEntityRef>& refs) const;
    std::vector<TaskOrder> get_task_orders_batch(const std::vector<WorldEntityRef>& refs) const;
    std::vector<LeaderIntent> get_leader_intents_batch(const std::vector<WorldEntityRef>& refs) const;
    std::vector<PilotReport> get_pilot_reports_batch(const std::vector<WorldEntityRef>& refs) const;

    std::vector<std::vector<uint64_t>> get_sensor_candidate_ids_batch(
        const std::vector<WorldEntityRef>& refs,
        bool use_gpu = false
    ) const;
    std::vector<std::vector<uint64_t>> get_visual_candidate_ids_batch(
        const std::vector<WorldEntityRef>& refs,
        double range_m = 25000.0,
        bool use_gpu = false
    ) const;
    std::vector<std::vector<uint64_t>> get_comm_candidate_ids_batch(
        const std::vector<WorldEntityRef>& refs,
        bool use_gpu = false
    ) const;

private:
    size_t resolve_worker_threads(size_t task_count) const noexcept;
    static InstrumentState safe_get_instrument_state(const SimulationKernel& world, uint64_t entity_id);
    SimulationKernel& checked_world(size_t index);
    const SimulationKernel& checked_world(size_t index) const;
    ExecutionEpisodeController& checked_execution_episode_controller(size_t world_index, uint64_t entity_id);
    const ExecutionEpisodeController& checked_execution_episode_controller(size_t world_index, uint64_t entity_id) const;
    void validate_execution_episode_step_requests(
        const std::vector<WorldExecutionEpisodeStepRequest>& requests
    ) const;

    std::vector<std::unique_ptr<SimulationKernel>> worlds_;
    std::vector<ExecutionEpisodeController> execution_episode_controllers_;
    std::vector<uint64_t> execution_episode_controller_entity_ids_;
    std::vector<bool> execution_episode_controller_active_;
    size_t worker_threads_ = 1;
};
