#include "core/engine/simulation_kernel_command_surface.h"

#include "core/engine/simulation_kernel.h"

SimulationKernelCommandReadSurface::SimulationKernelCommandReadSurface(
    const SimulationKernel& kernel
) noexcept
    : kernel_(&kernel) {}

TaskOrder SimulationKernelCommandReadSurface::get_task_order(std::uint64_t entity_id) const {
    return kernel_->get_task_order(entity_id);
}

LeaderIntent SimulationKernelCommandReadSurface::get_leader_intent(std::uint64_t entity_id) const {
    return kernel_->get_leader_intent(entity_id);
}

MissionCommand SimulationKernelCommandReadSurface::get_mission_command(std::uint64_t entity_id) const {
    return kernel_->get_mission_command(entity_id);
}

PilotReport SimulationKernelCommandReadSurface::get_pilot_report(std::uint64_t entity_id) const {
    return kernel_->get_pilot_report(entity_id);
}

SimulationKernelCommandSurface::SimulationKernelCommandSurface(SimulationKernel& kernel) noexcept
    : kernel_(&kernel) {}

void SimulationKernelCommandSurface::set_unit_command(
    std::uint64_t entity_id,
    double heading_deg,
    double speed_mps,
    double altitude_m
) {
    kernel_->set_unit_command(entity_id, heading_deg, speed_mps, altitude_m);
}

void SimulationKernelCommandSurface::set_unit_stick_command(
    std::uint64_t entity_id,
    double stick_roll,
    double stick_pitch,
    double throttle,
    bool gear_down
) {
    kernel_->set_unit_stick_command(entity_id, stick_roll, stick_pitch, throttle, gear_down);
}

void SimulationKernelCommandSurface::set_unit_action(
    std::uint64_t entity_id,
    double turn_rate_cmd,
    double accel_cmd,
    double climb_rate_cmd,
    double fire_cmd,
    bool release_chaff,
    bool release_flare,
    bool jettison_tanks
) {
    kernel_->set_unit_action(
        entity_id,
        turn_rate_cmd,
        accel_cmd,
        climb_rate_cmd,
        fire_cmd,
        release_chaff,
        release_flare,
        jettison_tanks
    );
}

void SimulationKernelCommandSurface::set_command_link(
    std::uint64_t entity_id,
    double latency_s,
    double drop_prob
) {
    kernel_->set_command_link(entity_id, latency_s, drop_prob);
}

void SimulationKernelCommandSurface::set_command_lag(
    std::uint64_t entity_id,
    double heading_tau_s,
    double speed_tau_s,
    double altitude_tau_s
) {
    kernel_->set_command_lag(entity_id, heading_tau_s, speed_tau_s, altitude_tau_s);
}

void SimulationKernelCommandSurface::set_pilot_action(
    std::uint64_t entity_id,
    const PilotAction& action
) {
    kernel_->set_pilot_action(entity_id, action);
}

void SimulationKernelCommandSurface::set_mission_command(
    std::uint64_t entity_id,
    const MissionCommand& cmd
) {
    kernel_->set_mission_command(entity_id, cmd);
}

void SimulationKernelCommandSurface::set_task_order(std::uint64_t entity_id, const TaskOrder& order) {
    kernel_->set_task_order(entity_id, order);
}

void SimulationKernelCommandSurface::set_leader_intent(
    std::uint64_t entity_id,
    const LeaderIntent& intent
) {
    kernel_->set_leader_intent(entity_id, intent);
}

void SimulationKernelCommandSurface::set_pilot_report(
    std::uint64_t entity_id,
    const PilotReport& report
) {
    kernel_->set_pilot_report(entity_id, report);
}

TaskOrder SimulationKernelCommandSurface::get_task_order(std::uint64_t entity_id) const {
    return kernel_->get_task_order(entity_id);
}

LeaderIntent SimulationKernelCommandSurface::get_leader_intent(std::uint64_t entity_id) const {
    return kernel_->get_leader_intent(entity_id);
}

MissionCommand SimulationKernelCommandSurface::get_mission_command(std::uint64_t entity_id) const {
    return kernel_->get_mission_command(entity_id);
}

PilotReport SimulationKernelCommandSurface::get_pilot_report(std::uint64_t entity_id) const {
    return kernel_->get_pilot_report(entity_id);
}
