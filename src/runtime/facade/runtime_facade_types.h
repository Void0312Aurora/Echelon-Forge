#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "components/physics/instruments.h"
#include "core/interfaces/observation.h"
#include "core/mission/episode/execution_episode_controller.h"
#include "runtime/contracts/engagement_contracts.h"
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
};

struct RuntimeBatchConfig {
    std::size_t world_count = 0;
    std::size_t worker_threads = 1;
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
    std::vector<double> time_steps;
};

struct BatchWorldSetupResult {
    std::vector<std::uint64_t> entity_ids;
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

struct ObservationBatchPacket {
    std::vector<WorldEntityRef> refs;
    std::vector<AgentObservation> agent_observations;
    std::vector<InstrumentState> instrument_states;
    std::vector<MissionCommand> mission_commands;
    std::vector<TaskOrder> task_orders;
    std::vector<LeaderIntent> leader_intents;
    std::vector<PilotReport> pilot_reports;
};

struct EngagementEventPacket {
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
    std::vector<double> rewards;
    std::vector<bool> terminated;
    std::vector<bool> truncated;
    std::vector<std::array<double, 4>> status_vectors;
    std::vector<std::string> termination_reasons;
    std::vector<std::string> reward_breakdown_jsons;
    std::vector<StepInfoProducts> step_infos;
    std::vector<bool> step_info_valid_flags;
    std::vector<bool> controller_state_changed_flags;
    ObservationBatchPacket observation_packet;
};
