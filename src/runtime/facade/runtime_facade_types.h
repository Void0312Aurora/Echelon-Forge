#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "components/physics/instruments.h"
#include "core/interfaces/observation.h"
#include "core/mission/execution_episode_controller.h"
#include "runtime/contracts/world_batch_contracts.h"

struct RuntimeCapabilities {
    bool supports_batch_runtime = true;
    bool supports_compiled_episode_controller = true;
    bool supports_compiled_execution_step = true;
    bool supports_gpu_visual = true;
    bool supports_gpu_observation = true;
    bool supports_gpu_flight_shaping = true;
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
