#pragma once

#include <cstdint>
#include <string>

#include "components/basic/common.h"
#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/tasking/leader_intent.h"
#include "components/tasking/pilot_report.h"
#include "components/tasking/task_order.h"
#include "core/mission/episode/execution_episode_batch_prepare.h"

struct WorldEntityRef {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
};

struct WorldTerrainAssignment {
    std::uint64_t world_index = 0;
    std::string terrain_type = "legacy";
};

struct WorldWindAssignment {
    std::uint64_t world_index = 0;
    double speed_mps = 0.0;
    double dir_from_deg = 0.0;
    double shear_mps_per_km = 0.0;
};

struct WorldZoneDefinition {
    std::uint64_t world_index = 0;
    std::string name = "Zone";
    double x = 0.0;
    double y = 0.0;
    double width = 1000.0;
    double length = 1000.0;
    double heading = 0.0;
    int surface_type = 3;
};

struct WorldSpawnRequest {
    std::uint64_t world_index = 0;
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
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    PilotAction action{};
};

struct WorldMissionCommandAssignment {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    MissionCommand command{};
};

struct WorldTaskOrderAssignment {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    TaskOrder order{};
};

struct WorldLeaderIntentAssignment {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    LeaderIntent intent{};
};

struct WorldPilotReportAssignment {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    PilotReport report{};
};

struct WorldExecutionEpisodeStepRequest {
    std::uint64_t world_index = 0;
    std::uint64_t entity_id = 0;
    StepEvaluationBatchConfig config{};
    StepEvaluationBatchEnvState env_state{};
};
