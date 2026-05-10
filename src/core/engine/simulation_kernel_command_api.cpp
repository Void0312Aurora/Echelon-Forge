#include "simulation_kernel.h"

#include "components/command/command_link.h"
#include "components/command/legacy_command.h"
#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/tasking/leader_intent.h"
#include "components/tasking/pilot_report.h"
#include "components/tasking/task_order.h"

#include <spdlog/spdlog.h>

#include <algorithm>
#include <cstdint>

namespace {
uint64_t splitmix64(uint64_t seed) {
    uint64_t z = seed + 0x9e3779b97f4a7c15ULL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

double deterministic_uniform01(uint64_t seed) {
    uint64_t z = splitmix64(seed);
    return (z >> 11) * (1.0 / 9007199254740992.0);
}
} // namespace


void SimulationKernel::set_unit_command(uint64_t entity_id, double heading_deg, double speed_mps, double altitude_m) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
        double current_time = info ? (double)info->world_time_total : 0.0;
        const CommandLink* link = e.get<CommandLink>();
        if (link && (link->latency_s > 0.0 || link->drop_prob > 0.0)) {
            uint64_t seed = static_cast<uint64_t>(current_time * 1000.0) ^
                            (entity_id * 0xbf58476d1ce4e5b9ULL) ^ 0x12345678ULL;
            double roll = deterministic_uniform01(seed);
            if (roll >= link->drop_prob) {
                PendingMovementCommand pending{{heading_deg,
                                                speed_mps,
                                                altitude_m,
                                                false, // use_stick_control
                                                0.0,   // stick_roll
                                                0.0,   // stick_pitch
                                                0.0,   // throttle_cmd
                                                true,  // gear_handle
                                                true   // active
                                               },
                                               current_time + link->latency_s,
                                               true};
                e.set<PendingMovementCommand>(pending);
            }
        } else {
            e.set<MovementCommand>({
                heading_deg,
                speed_mps,
                altitude_m,
                false, // use_stick_control
                0.0,   // stick_roll
                0.0,   // stick_pitch
                0.0,   // throttle_cmd
                true,  // gear_handle
                true   // active
            });
            if (!e.has<LaggedCommand>()) {
                e.set<LaggedCommand>({heading_deg, speed_mps, altitude_m, true});
            }
        }
    } else {
        spdlog::warn("Attempted to set command for invalid entity ID: {}", entity_id);
    }
}

void SimulationKernel::set_unit_stick_command(uint64_t entity_id, double stick_roll, double stick_pitch, double throttle, bool gear_down) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
        double current_time = info ? (double)info->world_time_total : 0.0;
        
        // Stick commands override Autopilot commands
        // We set use_stick_control = true
        // and fill the stick inputs (mapped to MovementCommand fields)
        if (e.has<MovementCommand>()) {
             MovementCommand* cmd = e.get_mut<MovementCommand>();
             cmd->use_stick_control = true;
             cmd->stick_roll = std::clamp(stick_roll, -1.0, 1.0);
             cmd->stick_pitch = std::clamp(stick_pitch, -1.0, 1.0);
             cmd->throttle_cmd = std::clamp(throttle, 0.0, 1.0);
             cmd->gear_handle = gear_down;
             cmd->active = true;
        } else {
             // Create if missing
             e.set<MovementCommand>({
                 0.0, 0.0, 0.0, // Autopilot defaults (ignored)
                 true, // use_stick_control
                 std::clamp(stick_roll, -1.0, 1.0),
                 std::clamp(stick_pitch, -1.0, 1.0),
                 std::clamp(throttle, 0.0, 1.0),
                 gear_down, // gear_handle
                 true // active
             });
        }
    } else {
        spdlog::warn("Attempted to set stick command for invalid entity ID: {}", entity_id);
    }
}

void SimulationKernel::set_unit_action(uint64_t entity_id,
                                       double turn_rate_cmd,
                                       double accel_cmd,
                                       double climb_rate_cmd,
                                       double fire_cmd,
                                       bool release_chaff,
                                       bool release_flare,
                                       bool jettison_tanks) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        auto clamp_cmd = [](double v) { return std::clamp(v, -1.0, 1.0); };
        double fire = std::clamp(fire_cmd, 0.0, 1.0);
        const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
        double current_time = info ? (double)info->world_time_total : 0.0;
        const CommandLink* link = e.get<CommandLink>();
        if (link && (link->latency_s > 0.0 || link->drop_prob > 0.0)) {
            if (!e.has<ActionCommand>()) {
                e.set<ActionCommand>({0.0, 0.0, 0.0, 0.0, false});
            }
            uint64_t seed = static_cast<uint64_t>(current_time * 1000.0) ^
                            (entity_id * 0x94d049bb133111ebULL) ^ 0x87654321ULL;
            double roll = deterministic_uniform01(seed);
            if (roll >= link->drop_prob) {
                PendingActionCommand pending{{
                                                clamp_cmd(turn_rate_cmd),
                                                clamp_cmd(accel_cmd),
                                                clamp_cmd(climb_rate_cmd),
                                                fire,
                                                release_chaff,
                                                release_flare,
                                                jettison_tanks,
                                                false, // send_msg
                                                0,     // msg_type
                                                0,     // msg_recipient
                                                0,     // msg_arg
                                                true   // active
                                            },
                                            current_time + link->latency_s,
                                            true};
                e.set<PendingActionCommand>(pending);
            }
        } else {
            e.set<ActionCommand>({
                clamp_cmd(turn_rate_cmd),
                clamp_cmd(accel_cmd),
                clamp_cmd(climb_rate_cmd),
                fire,
                release_chaff,
                release_flare,
                jettison_tanks,
                false, // send_msg
                0,     // msg_type
                0,     // msg_recipient
                0,     // msg_arg
                true   // active
            });
        }
    } else {
        spdlog::warn("Attempted to set action for invalid entity ID: {}", entity_id);
    }
}

void SimulationKernel::set_command_link(uint64_t entity_id, double latency_s, double drop_prob) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) {
        spdlog::warn("Attempted to set command link for invalid entity ID: {}", entity_id);
        return;
    }
    if (auto* link = e.get_mut<CommandLink>()) {
        link->latency_s = std::max(0.0, latency_s);
        link->drop_prob = std::clamp(drop_prob, 0.0, 1.0);
    } else {
        e.set<CommandLink>({std::max(0.0, latency_s), std::clamp(drop_prob, 0.0, 1.0)});
        if (!e.has<PendingMovementCommand>()) {
            e.set<PendingMovementCommand>({{0.0, 0.0, 0.0, false}, 0.0, false});
        }
        if (!e.has<PendingActionCommand>()) {
            e.set<PendingActionCommand>({{0.0, 0.0, 0.0, 0.0, false}, 0.0, false});
        }
        if (!e.has<PendingMissionCommand>()) {
            e.set<PendingMissionCommand>({{}, 0.0, false});
        }
    }
}

void SimulationKernel::set_action_space_config(uint64_t entity_id,
                                               double max_turn_rate_deg_s,
                                               double max_accel_mps2,
                                               double max_climb_rate_mps,
                                               double min_speed_mps,
                                               double max_speed_mps,
                                               double min_alt_m,
                                               double max_alt_m) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) {
        spdlog::warn("Attempted to set action space config for invalid entity ID: {}", entity_id);
        return;
    }

    ActionSpaceConfig cfg;
    cfg.max_turn_rate_deg_s = std::max(0.0, max_turn_rate_deg_s);
    cfg.max_accel_mps2 = std::max(0.0, max_accel_mps2);
    cfg.max_climb_rate_mps = std::max(0.0, max_climb_rate_mps);

    cfg.min_speed_mps = std::max(0.0, min_speed_mps);
    cfg.max_speed_mps = std::max(cfg.min_speed_mps, max_speed_mps);

    cfg.min_alt_m = min_alt_m;
    cfg.max_alt_m = std::max(cfg.min_alt_m, max_alt_m);

    e.set<ActionSpaceConfig>(cfg);
}

void SimulationKernel::set_command_lag(uint64_t entity_id,
                                       double heading_tau_s,
                                       double speed_tau_s,
                                       double altitude_tau_s) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) {
        spdlog::warn("Attempted to set command lag for invalid entity ID: {}", entity_id);
        return;
    }

    e.set<CommandLag>(
        {std::max(0.0, heading_tau_s), std::max(0.0, speed_tau_s), std::max(0.0, altitude_tau_s)});
}

void SimulationKernel::send_message_command(uint64_t entity_id, uint64_t recipient_id, int msg_type, uint64_t msg_arg) {
    auto e = ecs.entity(entity_id);
    if (!e.is_valid()) return;

    ActionCommand* cmd = e.get_mut<ActionCommand>();
    if (cmd) {
        cmd->send_msg = true;
        cmd->msg_recipient = recipient_id;
        cmd->msg_type = msg_type;
        cmd->msg_arg = msg_arg;
        cmd->active = true;
    }
}


void SimulationKernel::set_pilot_action(uint64_t entity_id, const PilotAction& action) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        e.set<PilotAction>(action);
        // Ensure legacy compatibility or active flag management if needed
        PilotAction* pa = e.get_mut<PilotAction>();
        pa->active = true;
    } else {
        spdlog::warn("Attempted to set pilot action for invalid entity ID: {}", entity_id);
    }
}

void SimulationKernel::set_mission_command(uint64_t entity_id, const MissionCommand& cmd) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
        double current_time = info ? (double)info->world_time_total : 0.0;
        const CommandLink* link = e.get<CommandLink>();
        if (link && (link->latency_s > 0.0 || link->drop_prob > 0.0)) {
            if (!e.has<MissionCommand>()) {
                e.set<MissionCommand>({});
            }
            uint64_t seed = static_cast<uint64_t>(current_time * 1000.0) ^
                            (entity_id * 0xd6e8feb86659fd93ULL) ^ 0x13579bdfULL;
            double roll = deterministic_uniform01(seed);
            if (roll >= link->drop_prob) {
                MissionCommand pending_cmd = cmd;
                pending_cmd.active = true;
                e.set<PendingMissionCommand>({pending_cmd, current_time + link->latency_s, true});
            }
            return;
        }

        MissionCommand next = cmd;
        next.active = true;
        e.set<MissionCommand>(next);
    } else {
        spdlog::warn("Attempted to set mission command for invalid entity ID: {}", entity_id);
    }
}

void SimulationKernel::set_task_order(uint64_t entity_id, const TaskOrder& order) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        TaskOrder next = order;
        next.active = true;
        e.set<TaskOrder>(next);
    } else {
        spdlog::warn("Attempted to set task order for invalid entity ID: {}", entity_id);
    }
}

void SimulationKernel::set_leader_intent(uint64_t entity_id, const LeaderIntent& intent) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        LeaderIntent next = intent;
        next.active = true;
        e.set<LeaderIntent>(next);
    } else {
        spdlog::warn("Attempted to set leader intent for invalid entity ID: {}", entity_id);
    }
}

void SimulationKernel::set_pilot_report(uint64_t entity_id, const PilotReport& report) {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        PilotReport next = report;
        next.active = true;
        e.set<PilotReport>(next);
    } else {
        spdlog::warn("Attempted to set pilot report for invalid entity ID: {}", entity_id);
    }
}

TaskOrder SimulationKernel::get_task_order(uint64_t entity_id) const {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const TaskOrder* order = e.get<TaskOrder>()) {
            return *order;
        }
    }
    return TaskOrder{};
}

LeaderIntent SimulationKernel::get_leader_intent(uint64_t entity_id) const {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const LeaderIntent* intent = e.get<LeaderIntent>()) {
            return *intent;
        }
    }
    return LeaderIntent{};
}

MissionCommand SimulationKernel::get_mission_command(uint64_t entity_id) const {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const MissionCommand* cmd = e.get<MissionCommand>()) {
            return *cmd;
        }
    }
    return MissionCommand{};
}

PilotReport SimulationKernel::get_pilot_report(uint64_t entity_id) const {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        if (const PilotReport* report = e.get<PilotReport>()) {
            return *report;
        }
    }
    return PilotReport{};
}
