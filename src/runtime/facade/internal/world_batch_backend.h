#pragma once

#include <cstddef>
#include <cstdint>
#include <array>
#include <optional>
#include <string>
#include <vector>

#include "runtime/facade/runtime_facade_types.h"

class IWorldBatchCompatibilityPort;

namespace runtime::backend {

// Synchronous non-owning view over an existing batch vector. RuntimeFacade
// keeps the source vector alive for the virtual call; a backend that queues
// work beyond the call boundary must make its own explicit copy.
template <typename T> class VectorBatchView {
  public:
    VectorBatchView() = default;
    VectorBatchView(const std::vector<T> &values) noexcept : values_(&values) {}
    VectorBatchView(std::vector<T> &&) = delete;
    VectorBatchView(const std::vector<T> &&) = delete;

    const std::vector<T> &get() const noexcept {
        static const std::vector<T> empty_values;
        return values_ == nullptr ? empty_values : *values_;
    }

    bool empty() const noexcept { return get().empty(); }

  private:
    const std::vector<T> *values_ = nullptr;
};

struct Configuration {
    std::size_t world_count = 0;
    std::size_t worker_threads = 1;
    std::size_t effective_worker_threads = 1;
};

struct ConfigureRequest {
    std::optional<std::size_t> world_count;
    std::optional<std::size_t> worker_threads;
};

enum class ContentKind : std::uint8_t {
    Database,
    UnitDefinitions,
};

struct ContentRequest {
    ContentKind kind = ContentKind::Database;
    const std::string *path = nullptr;
};

struct ContentResult {
    bool loaded = false;
    std::string error;
};

struct ResetRequest {
    VectorBatchView<std::uint32_t> seeds;
};

enum class SetupKind : std::uint8_t {
    Batch,
    Layout,
    WorldSpawn,
    TypedPlatformSpawn,
};

struct SetupRequest {
    SetupKind kind = SetupKind::Batch;
    VectorBatchView<std::uint32_t> seeds;
    VectorBatchView<WorldTerrainAssignment> terrain_assignments;
    VectorBatchView<WorldWindAssignment> wind_assignments;
    VectorBatchView<WorldZoneDefinition> zones;
    VectorBatchView<WorldSpawnRequest> spawn_requests;
    VectorBatchView<double> time_steps;
    VectorBatchView<WorldSunAssignment> sun_assignments;

    std::size_t world_index = 0;
    std::uint32_t seed = 0;
    const std::string *terrain_type = nullptr;
    double wind_speed_mps = 0.0;
    double wind_dir_from_deg = 0.0;
    double wind_shear_mps_per_km = 0.0;
    bool maritime_configured = false;
    double sea_state = 0.0;
    double wave_heading_deg = 0.0;
    double wave_period_s = 8.0;
    double sun_azimuth_deg = 0.0;
    double sun_elevation_deg = 45.0;

    const WorldSpawnRequest *world_spawn_request = nullptr;
    const TypedPlatformSpawnRequest *typed_platform_spawn_request = nullptr;
};

struct SetupResult {
    std::vector<std::uint64_t> entity_ids;
};

struct EntityKinematics {
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

struct EntityKinematicsWrite {
    WorldEntityRef ref{};
    EntityKinematics state{};
};

struct InputBatch {
    std::optional<EntityKinematicsWrite> kinematics_write;
    VectorBatchView<WorldPilotActionAssignment> pilot_actions;
    VectorBatchView<LaunchRequest> launch_requests;
    VectorBatchView<WorldMissionCommandMaintainedAssignment> mission_commands;
    VectorBatchView<WorldTaskOrderMaintainedAssignment> task_orders;
    VectorBatchView<WorldLeaderIntentMaintainedAssignment> leader_intents;
    VectorBatchView<WorldPilotReportMaintainedAssignment> pilot_reports;
};

struct InputResult {
    std::optional<bool> kinematics_write_result;
    std::vector<LaunchEvent> launch_events;
};

enum class AdvanceKind : std::uint8_t {
    WorldBatch,
};

struct AdvanceRequest {
    AdvanceKind kind = AdvanceKind::WorldBatch;
};

struct AdvanceResult {};

struct EvaluationRequest {};

struct EvaluationResult {};

struct EntityKinematicsRead {
    WorldEntityRef ref{};
    bool found = false;
    EntityKinematics state{};
};

struct ExportRequest {
    VectorBatchView<WorldEntityRef> refs;
    const WorldEntityRef *kinematics_ref = nullptr;
    std::optional<std::size_t> world_index;
    bool include_kinematics = false;
    bool include_recent_engagement_events = false;
    bool include_world_time_step = false;
    bool include_agent_observations = false;
    bool include_instrument_states = false;
    bool include_mission_commands = false;
    bool include_task_orders = false;
    bool include_leader_intents = false;
    bool include_pilot_reports = false;
};

struct ExportResult {
    std::vector<EntityKinematicsRead> kinematics;
    ::RecentEngagementEvents recent_engagement_events;
    double world_time_step = 0.0;
    std::vector<AgentObservation> agent_observations;
    std::vector<InstrumentState> instrument_states;
    std::vector<MissionCommandMaintainedBatchContract> mission_commands;
    std::vector<TaskOrderMaintainedBatchContract> task_orders;
    std::vector<LeaderIntentMaintainedBatchContract> leader_intents;
    std::vector<PilotReportMaintainedBatchContract> pilot_reports;
};

struct Diagnostics {
    std::string backend_id;
    std::size_t world_count = 0;
    struct WorldComposition {
        std::size_t world_index = 0;
        std::string requested_manifest_sha256;
        std::string resolved_manifest_sha256;
        std::string executable_graph_sha256;
        std::array<std::uint64_t, 5> scope_generations{};
    };
    std::vector<WorldComposition> world_compositions;
};

} // namespace runtime::backend

// Internal semantic execution seam. Public facade methods translate into a
// small set of backend-neutral configure/reset/setup/inject/evaluate/advance/export
// operations. Backend-private worlds, component handles, helper-selection
// flags, and device pointers do not cross this boundary.
class IWorldBatchBackend {
  public:
    virtual ~IWorldBatchBackend() = default;

    virtual runtime::backend::Configuration configuration() const noexcept = 0;
    virtual void configure(const runtime::backend::ConfigureRequest &request) = 0;
    virtual runtime::backend::ContentResult
    load_content(const runtime::backend::ContentRequest &request) = 0;
    virtual void reset(const runtime::backend::ResetRequest &request) = 0;
    virtual runtime::backend::SetupResult setup(const runtime::backend::SetupRequest &request) = 0;
    virtual runtime::backend::InputResult inject(const runtime::backend::InputBatch &input) = 0;
    virtual runtime::backend::EvaluationResult
    evaluate(const runtime::backend::EvaluationRequest &request) const = 0;
    virtual runtime::backend::AdvanceResult
    advance(const runtime::backend::AdvanceRequest &request) = 0;
    virtual runtime::backend::ExportResult
    export_state(const runtime::backend::ExportRequest &request) const = 0;
    virtual runtime::backend::Diagnostics diagnostics() const = 0;

    // Quarantined adapter for legacy CPU/GPU-helper compatibility APIs. It is
    // optional and is not part of the semantic contract a resident backend
    // must implement.
    virtual const IWorldBatchCompatibilityPort *compatibility_port() const noexcept {
        return nullptr;
    }
};
