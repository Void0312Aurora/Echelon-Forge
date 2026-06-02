#pragma once

#include <cstdint>

#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/tasking/leader_intent.h"
#include "components/tasking/pilot_report.h"
#include "components/tasking/task_order.h"

class SimulationKernel;

class SimulationKernelCommandReadSurface final {
public:
    explicit SimulationKernelCommandReadSurface(const SimulationKernel& kernel) noexcept;

    TaskOrder get_task_order(std::uint64_t entity_id) const;
    LeaderIntent get_leader_intent(std::uint64_t entity_id) const;
    MissionCommand get_mission_command(std::uint64_t entity_id) const;
    PilotReport get_pilot_report(std::uint64_t entity_id) const;

private:
    const SimulationKernel* kernel_;
};

class SimulationKernelCommandSurface final {
public:
    explicit SimulationKernelCommandSurface(SimulationKernel& kernel) noexcept;

    void set_unit_command(
        std::uint64_t entity_id,
        double heading_deg,
        double speed_mps,
        double altitude_m
    );
    void set_unit_stick_command(
        std::uint64_t entity_id,
        double stick_roll,
        double stick_pitch,
        double throttle,
        bool gear_down
    );
    void set_unit_action(
        std::uint64_t entity_id,
        double turn_rate_cmd,
        double accel_cmd,
        double climb_rate_cmd,
        double fire_cmd,
        bool release_chaff = false,
        bool release_flare = false,
        bool jettison_tanks = false
    );
    void set_command_link(std::uint64_t entity_id, double latency_s, double drop_prob);
    void set_command_lag(
        std::uint64_t entity_id,
        double heading_tau_s,
        double speed_tau_s,
        double altitude_tau_s
    );

    void set_pilot_action(std::uint64_t entity_id, const PilotAction& action);
    void set_mission_command(std::uint64_t entity_id, const MissionCommand& cmd);
    void set_task_order(std::uint64_t entity_id, const TaskOrder& order);
    void set_leader_intent(std::uint64_t entity_id, const LeaderIntent& intent);
    void set_pilot_report(std::uint64_t entity_id, const PilotReport& report);

    TaskOrder get_task_order(std::uint64_t entity_id) const;
    LeaderIntent get_leader_intent(std::uint64_t entity_id) const;
    MissionCommand get_mission_command(std::uint64_t entity_id) const;
    PilotReport get_pilot_report(std::uint64_t entity_id) const;

private:
    SimulationKernel* kernel_;
};
