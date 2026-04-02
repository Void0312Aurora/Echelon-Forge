#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "components/physics/action.h"
#include "components/physics/instruments.h"
#include "core/engine/simulation_kernel.h"
#include "core/interfaces/observation.h"
#include "gpu/gpu_exact_world_step_contract.h"
#include "gpu/gpu_exact_world_step_first_scope_chain_cuda_runtime.h"
#include "gpu/gpu_world_batch_runtime.h"

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

struct ExactWorldStepFirstScopeChainCachedSessionStats {
    std::size_t state_count = 0;
    bool used_gpu = false;
    double prime_extract_ms = 0.0;
    double pilot_update_ms = 0.0;
    double mission_update_ms = 0.0;
    double step_total_ms = 0.0;
    double write_back_ms = 0.0;
    double chain_command_lane_ms = 0.0;
    double chain_host_to_device_ms = 0.0;
    double chain_front_kernel_ms = 0.0;
    double chain_guidance_kernel_ms = 0.0;
    double chain_tail_kernel_ms = 0.0;
    double chain_kernel_ms = 0.0;
    double chain_device_to_host_ms = 0.0;
    double chain_cpu_fallback_ms = 0.0;
    double chain_total_ms = 0.0;
};

enum class WorldBatchExactStepBackend {
    CpuSimulationKernel = 0,
    ExactFirstScopeChainCachedCpu = 1,
    ExactFirstScopeChainCachedGpu = 2,
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
    void set_exact_world_step_backend(WorldBatchExactStepBackend backend) noexcept { exact_step_backend_ = backend; }
    WorldBatchExactStepBackend exact_world_step_backend() const noexcept { return exact_step_backend_; }
    bool exact_world_step_backend_ready() const noexcept;
    void clear_exact_world_step_backend_session() noexcept;

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

    std::vector<gpu::WorldBatchStepState> extract_packed_flight_states_batch(
        const std::vector<WorldEntityRef>& refs
    ) const;
    void apply_packed_flight_states_batch(
        const std::vector<WorldEntityRef>& refs,
        const std::vector<gpu::WorldBatchStepState>& states
    );
    std::vector<gpu::WorldBatchStepState> step_packed_flight_states_experiment_batch(
        const std::vector<WorldEntityRef>& refs,
        int steps,
        bool use_cuda_graph = false,
        bool write_back = false
    );
    std::vector<gpu::ExactWorldStepStateV1> extract_exact_world_step_states_v1_batch(
        const std::vector<WorldEntityRef>& refs
    ) const;
    std::vector<gpu::ExactWorldStepStateV1> step_exact_world_step_first_scope_chain_experiment_batch(
        const std::vector<WorldEntityRef>& refs,
        bool use_gpu = true,
        bool write_back = false
    );
    void prime_exact_world_step_first_scope_chain_cached_session(
        const std::vector<WorldEntityRef>& refs
    );
    void set_pilot_actions_exact_world_step_first_scope_chain_cached_session(
        const std::vector<WorldPilotActionAssignment>& assignments
    );
    void set_mission_commands_exact_world_step_first_scope_chain_cached_session(
        const std::vector<WorldMissionCommandAssignment>& assignments
    );
    std::vector<gpu::ExactWorldStepStateV1> step_exact_world_step_first_scope_chain_cached_session(
        bool use_gpu = true,
        bool write_back = false
    );
    const ExactWorldStepFirstScopeChainCachedSessionStats&
    last_exact_world_step_first_scope_chain_cached_session_stats() const noexcept;
    void apply_exact_world_step_first_scope_chain_cached_session_to_world();
    std::vector<gpu::ExactWorldStepStateV1> extract_exact_world_step_first_scope_chain_cached_session() const;
    bool upload_exact_world_step_first_scope_chain_experiment_batch(
        const std::vector<WorldEntityRef>& refs
    );
    bool replay_exact_world_step_first_scope_chain_experiment_device_sequence();
    std::vector<gpu::ExactWorldStepStateV1> download_exact_world_step_first_scope_chain_experiment_batch(
        bool write_back = false
    );
    void apply_exact_world_step_states_v1_batch(
        const std::vector<WorldEntityRef>& refs,
        const std::vector<gpu::ExactWorldStepStateV1>& states
    );

private:
    size_t resolve_worker_threads(size_t task_count) const noexcept;
    static InstrumentState safe_get_instrument_state(const SimulationKernel& world, uint64_t entity_id);
    SimulationKernel& checked_world(size_t index);
    const SimulationKernel& checked_world(size_t index) const;
    bool exact_world_step_backend_uses_first_scope_chain_cached_session() const noexcept;
    bool exact_world_step_backend_covers_world(size_t world_index) const noexcept;
    bool exact_world_step_backend_world_dirty(size_t world_index) const noexcept;
    bool exact_world_step_first_scope_chain_cached_session_supports_resident_gpu_fast_path() const noexcept;
    void invalidate_exact_world_step_first_scope_chain_cached_session_resident_gpu_fast_path() noexcept;
    bool sync_exact_world_step_first_scope_chain_cached_session_host_from_device();
    std::vector<gpu::ExactWorldStepStateV1> step_exact_world_step_first_scope_chain_cached_session_impl(
        bool use_gpu,
        bool write_back,
        bool materialize_result
    );
    void mark_exact_world_step_backend_cached_worlds_dirty() noexcept;
    void mark_exact_world_step_backend_worlds_clean(const std::vector<size_t>& world_indices) noexcept;
    void sync_exact_world_step_backend_world_if_needed(size_t world_index);
    void sync_exact_world_step_backend_refs_if_needed(const std::vector<WorldEntityRef>& refs);

    std::vector<std::unique_ptr<SimulationKernel>> worlds_;
    size_t worker_threads_ = 1;
    WorldBatchExactStepBackend exact_step_backend_ = WorldBatchExactStepBackend::CpuSimulationKernel;
    std::vector<WorldEntityRef> first_scope_chain_cached_refs_;
    std::vector<gpu::ExactWorldStepStateV1> first_scope_chain_cached_states_;
    std::vector<bool> first_scope_chain_cached_world_dirty_;
    std::vector<gpu::ExactWorldStepFirstScopeChainCudaResidentPilotTimeProjection>
        first_scope_chain_cached_resident_pilot_time_projection_scratch_;
    bool first_scope_chain_cached_resident_gpu_uploaded_ = false;
    bool first_scope_chain_cached_resident_pilot_projection_dirty_ = false;
    bool first_scope_chain_cached_resident_full_projection_dirty_ = false;
    bool first_scope_chain_cached_device_state_pending_materialize_ = false;
    ExactWorldStepFirstScopeChainCachedSessionStats first_scope_chain_cached_session_stats_{};
    std::vector<WorldEntityRef> first_scope_chain_experiment_refs_;
};
