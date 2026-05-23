#include "simulation_kernel.h"

#include "components/command/command_link.h"
#include "components/command/command_link_qos.h"
#include "components/command/legacy_command.h"
#include "components/command/legacy_command_bridge.h"
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

inline double current_world_time_seconds(const flecs::world& world) {
    const ecs_world_info_t* info = ecs_get_world_info(world.c_ptr());
    return info ? static_cast<double>(info->world_time_total) : 0.0;
}

inline bool command_link_requires_delivery_queue(const CommandLink* link) {
    return link && (link->latency_s > 0.0 || link->drop_prob > 0.0);
}

template <typename WorldT>
flecs::entity resolve_valid_entity_or_warn(WorldT& world, uint64_t entity_id, const char* operation) {
    auto entity = world.entity(entity_id);
    if (!entity.is_valid()) {
        spdlog::warn("Attempted to {} for invalid entity ID: {}", operation, entity_id);
        return flecs::entity::null();
    }
    return entity;
}

template <typename ComponentT>
void set_active_component(flecs::entity entity, const ComponentT& value) {
    ComponentT next = value;
    next.active = true;
    entity.set<ComponentT>(next);
}

template <typename ComponentT>
ComponentT get_component_or_default(flecs::entity entity) {
    if (const ComponentT* value = entity.get<ComponentT>()) {
        return *value;
    }
    return ComponentT{};
}

inline bool entity_is_ship(flecs::entity entity) {
    const KeyEntity* key = entity.get<KeyEntity>();
    return key && (key->type == UnitType::Ship || key->type == UnitType::Submarine);
}

inline MissionCommand ship_mission_command_from_unit_command(
    flecs::entity entity,
    double heading_deg,
    double speed_mps,
    double altitude_m
) {
    MissionCommand mission{};

    const MissionCommand* existing = entity.get<MissionCommand>();
    if (existing != nullptr) {
        mission.roe_state = existing->roe_state;
        mission.engagement_authority_holder_id = existing->engagement_authority_holder_id;
        mission.engagement_authority_grantor_id = existing->engagement_authority_grantor_id;
        mission.assigned_target_id = existing->assigned_target_id;
        mission.authorization_to_fire = existing->authorization_to_fire;
    }

    mission.cmd_heading_deg = heading_deg;
    mission.cmd_speed_mps = speed_mps;
    mission.cmd_altitude_m = altitude_m;
    mission.active = true;
    return mission;
}

void queue_or_refresh_pending_action_command(
    flecs::entity entity,
    const ActionCommand& value,
    double deliver_time
) {
    ActionCommand next = value;
    next.active = true;

    if (PendingActionCommand* pending = entity.get_mut<PendingActionCommand>()) {
        pending->command = next;
        refresh_pending_action_command_typed_air_control_bridge(*pending);
        pending->deliver_time = deliver_time;
        pending->active = true;
        return;
    }

    entity.set<PendingActionCommand>(
        make_pending_action_command(next, deliver_time, true)
    );
}

inline void queue_or_refresh_pending_movement_command(
    flecs::entity entity,
    const PendingMissionControlCommand& value,
    double deliver_time
) {
    if (PendingMovementCommand* pending = entity.get_mut<PendingMovementCommand>()) {
        pending->typed_command = value;
        refresh_pending_movement_command_diagnostics_shell(*pending);
        pending->deliver_time = deliver_time;
        pending->active = true;
        return;
    }

    entity.set<PendingMovementCommand>(
        make_pending_movement_command(value, deliver_time, true)
    );
}

inline MissionCommandEnqueueResult queue_pending_mission_command(
    flecs::entity entity,
    const MissionCommand& value,
    double current_time,
    double latency_s
) {
    PendingMissionCommand* pending = entity.get_mut<PendingMissionCommand>();
    if (!pending) {
        entity.set<PendingMissionCommand>(make_pending_mission_command());
        pending = entity.get_mut<PendingMissionCommand>();
    }

    MissionCommandPendingQueue* queue = entity.get_mut<MissionCommandPendingQueue>();
    if (!queue) {
        entity.set<MissionCommandPendingQueue>(make_mission_command_pending_queue());
        queue = entity.get_mut<MissionCommandPendingQueue>();
    }

    if (!pending || !queue) {
        return MissionCommandEnqueueResult::Dropped;
    }
    return enqueue_pending_mission_command(*pending, *queue, value, current_time, latency_s);
}

inline void warn_if_mission_command_queue_dropped(
    flecs::entity entity,
    MissionCommandEnqueueResult enqueue_result,
    const MissionCommand& command
) {
    if (enqueue_result != MissionCommandEnqueueResult::Dropped) {
        return;
    }
    spdlog::warn(
        "Dropped mission command for entity {} because the pending mission queue is full; command_code={}, priority={}",
        entity.id(),
        command.command_code,
        mission_command_queue_priority(command)
    );
}
} // namespace


void SimulationKernel::set_unit_command(uint64_t entity_id, double heading_deg, double speed_mps, double altitude_m) {
    auto e = resolve_valid_entity_or_warn(ecs, entity_id, "set command");
    if (e.is_valid()) {
        if (entity_is_ship(e)) {
            const MissionCommand mission =
                ship_mission_command_from_unit_command(e, heading_deg, speed_mps, altitude_m);
            const CommandLink* link = e.get<CommandLink>();
            if (command_link_requires_delivery_queue(link)) {
                const double current_time = current_world_time_seconds(ecs);
                if (!e.has<MissionCommand>()) {
                    e.set<MissionCommand>({});
                }
                uint64_t seed = static_cast<uint64_t>(current_time * 1000.0) ^
                                (entity_id * 0xd6e8feb86659fd93ULL) ^ 0x13579bdfULL;
                double roll = deterministic_uniform01(seed);
                if (roll >= link->drop_prob) {
                    const auto enqueue_result =
                        queue_pending_mission_command(e, mission, current_time, link->latency_s);
                    warn_if_mission_command_queue_dropped(e, enqueue_result, mission);
                }
            } else {
                e.set<MissionCommand>(mission);
            }
            return;
        }

        const CommandLink* link = e.get<CommandLink>();
        if (command_link_requires_delivery_queue(link)) {
            const double current_time = current_world_time_seconds(ecs);
            uint64_t seed = static_cast<uint64_t>(current_time * 1000.0) ^
                            (entity_id * 0xbf58476d1ce4e5b9ULL) ^ 0x12345678ULL;
            double roll = deterministic_uniform01(seed);
            if (roll >= link->drop_prob) {
                ensure_mission_command_control_state(e);
                queue_or_refresh_pending_movement_command(
                    e,
                    make_pending_mission_control_command(
                        heading_deg,
                        speed_mps,
                        altitude_m,
                        true
                    ),
                    current_time + link->latency_s
                );
            }
        } else {
            set_compatibility_autopilot_control_target(
                e,
                heading_deg,
                speed_mps,
                altitude_m
            );
        }
    }
}

void SimulationKernel::set_unit_stick_command(uint64_t entity_id, double stick_roll, double stick_pitch, double throttle, bool gear_down) {
    auto e = resolve_valid_entity_or_warn(ecs, entity_id, "set stick command");
    if (e.is_valid()) {
        set_quarantined_compatibility_stick_movement_command(
            e,
            std::clamp(stick_roll, -1.0, 1.0),
            std::clamp(stick_pitch, -1.0, 1.0),
            std::clamp(throttle, 0.0, 1.0),
            gear_down
        );
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
    auto e = resolve_valid_entity_or_warn(ecs, entity_id, "set action");
    if (e.is_valid()) {
        auto clamp_cmd = [](double v) { return std::clamp(v, -1.0, 1.0); };
        double fire = std::clamp(fire_cmd, 0.0, 1.0);
        const ActionCommand next = make_action_command(
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
        );
        const CommandLink* link = e.get<CommandLink>();
        if (command_link_requires_delivery_queue(link)) {
            const double current_time = current_world_time_seconds(ecs);
            ensure_mission_command_control_state(e);
            if (!e.has<ActionCommand>()) {
                e.set<ActionCommand>(make_action_command());
            }
            uint64_t seed = static_cast<uint64_t>(current_time * 1000.0) ^
                            (entity_id * 0x94d049bb133111ebULL) ^ 0x87654321ULL;
            double roll = deterministic_uniform01(seed);
            if (roll >= link->drop_prob) {
                // PendingActionCommand remains a quarantined legacy transport shell in this slice.
                queue_or_refresh_pending_action_command(
                    e,
                    next,
                    current_time + link->latency_s
                );
            }
        } else {
            e.set<ActionCommand>(next);
            refresh_compatibility_typed_air_control_from_action_command(
                e,
                next
            );
        }
    }
}

void SimulationKernel::set_command_link(uint64_t entity_id, double latency_s, double drop_prob) {
    auto e = resolve_valid_entity_or_warn(ecs, entity_id, "set command link");
    if (!e.is_valid()) {
        return;
    }
    if (auto* link = e.get_mut<CommandLink>()) {
        link->latency_s = std::max(0.0, latency_s);
        link->drop_prob = std::clamp(drop_prob, 0.0, 1.0);
    } else {
        e.set<CommandLink>({std::max(0.0, latency_s), std::clamp(drop_prob, 0.0, 1.0)});
        if (!e.has<PendingMovementCommand>()) {
            e.set<PendingMovementCommand>(make_pending_movement_command());
        }
        if (!e.has<PendingActionCommand>()) {
            e.set<PendingActionCommand>(make_pending_action_command());
        }
        if (!e.has<PendingMissionCommand>()) {
            e.set<PendingMissionCommand>(make_pending_mission_command());
        }
        if (!e.has<MissionCommandPendingQueue>()) {
            e.set<MissionCommandPendingQueue>(make_mission_command_pending_queue());
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
    auto e = resolve_valid_entity_or_warn(ecs, entity_id, "set action space config");
    if (!e.is_valid()) {
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
    auto e = resolve_valid_entity_or_warn(ecs, entity_id, "set command lag");
    if (!e.is_valid()) {
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
    auto e = resolve_valid_entity_or_warn(ecs, entity_id, "set pilot action");
    if (e.is_valid()) {
        set_active_component(e, action);
    }
}

void SimulationKernel::set_mission_command(uint64_t entity_id, const MissionCommand& cmd) {
    auto e = resolve_valid_entity_or_warn(ecs, entity_id, "set mission command");
    if (e.is_valid()) {
        const CommandLink* link = e.get<CommandLink>();
        if (command_link_requires_delivery_queue(link)) {
            const double current_time = current_world_time_seconds(ecs);
            if (!e.has<MissionCommand>()) {
                e.set<MissionCommand>({});
            }
            uint64_t seed = static_cast<uint64_t>(current_time * 1000.0) ^
                            (entity_id * 0xd6e8feb86659fd93ULL) ^ 0x13579bdfULL;
            double roll = deterministic_uniform01(seed);
            if (roll >= link->drop_prob) {
                const auto enqueue_result =
                    queue_pending_mission_command(e, cmd, current_time, link->latency_s);
                warn_if_mission_command_queue_dropped(e, enqueue_result, cmd);
            }
            return;
        }

        set_active_component(e, cmd);
    }
}

void SimulationKernel::set_task_order(uint64_t entity_id, const TaskOrder& order) {
    auto e = resolve_valid_entity_or_warn(ecs, entity_id, "set task order");
    if (e.is_valid()) {
        set_active_component(e, order);
    }
}

void SimulationKernel::set_leader_intent(uint64_t entity_id, const LeaderIntent& intent) {
    auto e = resolve_valid_entity_or_warn(ecs, entity_id, "set leader intent");
    if (e.is_valid()) {
        set_active_component(e, intent);
    }
}

void SimulationKernel::set_pilot_report(uint64_t entity_id, const PilotReport& report) {
    auto e = resolve_valid_entity_or_warn(ecs, entity_id, "set pilot report");
    if (e.is_valid()) {
        set_active_component(e, report);
    }
}

TaskOrder SimulationKernel::get_task_order(uint64_t entity_id) const {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        return get_component_or_default<TaskOrder>(e);
    }
    return {};
}

LeaderIntent SimulationKernel::get_leader_intent(uint64_t entity_id) const {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        return get_component_or_default<LeaderIntent>(e);
    }
    return {};
}

MissionCommand SimulationKernel::get_mission_command(uint64_t entity_id) const {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        return get_component_or_default<MissionCommand>(e);
    }
    return {};
}

PilotReport SimulationKernel::get_pilot_report(uint64_t entity_id) const {
    auto e = ecs.entity(entity_id);
    if (e.is_valid()) {
        return get_component_or_default<PilotReport>(e);
    }
    return {};
}
