#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_internal.cuh"
#include <utility>
#include <vector>
namespace runtime::cuda_resident::detail {
bool read_cuda_world_store_state(const CudaWorldStoreDeviceAllocation *allocation,
                                 CudaWorldStoreStateSnapshot *snapshot, std::string *error) {
    if (allocation == nullptr || snapshot == nullptr) {
        if (error != nullptr) {
            *error = "CUDA world store state readback requires an allocation and output";
        }
        return false;
    }
    std::vector<HostStateBlock> host_slot = make_host_slot(allocation->state_layout.slot_bytes);
    if (allocation->world_capacity != 0) {
        const cudaError_t status =
            cudaMemcpy(host_slot.data(), allocation->state_slots[allocation->active_state_slot],
                       allocation->state_layout.slot_bytes, cudaMemcpyDeviceToHost);
        if (status != cudaSuccess) {
            if (error != nullptr) {
                *error = cuda_error_message("read resident world state", status);
            }
            return false;
        }
    }

    CudaWorldStoreDeviceSnapshot lifecycle;
    if (!read_cuda_world_store_metadata(allocation, allocation->world_capacity, &lifecycle,
                                        error)) {
        return false;
    }
    if (allocation->world_capacity == 0) {
        snapshot->worlds.clear();
        if (error != nullptr) {
            error->clear();
        }
        return true;
    }

    const auto *setup_complete =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.setup_complete);
    const auto *entity_ids =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.entity_ids);
    const auto *entity_generations =
        host_field<std::uint32_t>(host_slot, allocation->state_layout.entity_generations);
    const auto *time_steps = host_field<double>(host_slot, allocation->state_layout.time_steps);
    const auto *kinematics = host_field<double>(host_slot, allocation->state_layout.kinematics);
    const auto *dynamics = host_field<double>(host_slot, allocation->state_layout.dynamics);
    const auto *phase_d_instruments =
        host_field<double>(host_slot, allocation->state_layout.phase_d_instruments);
    const auto *phase_d_observations =
        host_field<double>(host_slot, allocation->state_layout.phase_d_observations);
    const auto *phase_d_observation_ids =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.phase_d_observation_ids);
    const auto *phase_d_rewards =
        host_field<double>(host_slot, allocation->state_layout.phase_d_rewards);
    const auto *phase_d_reward_versions =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.phase_d_reward_versions);
    const auto *phase_d_termination_flags =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.phase_d_termination_flags);
    const auto *phase_d_termination_codes =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.phase_d_termination_codes);
    const auto *phase_d_event_empty =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.phase_d_event_empty);
    const auto *control_doubles =
        host_field<double>(host_slot, allocation->state_layout.control_doubles);
    const auto *control_floats =
        host_field<float>(host_slot, allocation->state_layout.control_floats);
    const auto *control_flags =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.control_flags);
    const auto *prepared_doubles =
        host_field<double>(host_slot, allocation->state_layout.prepared_doubles);
    const auto *prepared_flags =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.prepared_flags);
    const auto *phase_versions =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.phase_versions);
    const auto *clock_ticks =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.clock_ticks);
    const auto *simulation_times =
        host_field<double>(host_slot, allocation->state_layout.simulation_times);
    const auto *global_versions =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.global_versions);
    const auto *barrier_sequences =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.barrier_sequences);
    const auto *barrier_codes =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.barrier_codes);
    const auto *shard_versions =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.shard_versions);

    CudaWorldStoreStateSnapshot next_snapshot;
    next_snapshot.worlds.reserve(allocation->world_capacity);
    for (std::size_t world = 0; world < allocation->world_capacity; ++world) {
        CudaWorldResidentState state{};
        state.world_index = world;
        state.seed = lifecycle.seeds[world];
        state.reset_generation = lifecycle.reset_generations[world];
        state.setup_complete = setup_complete[world] != 0;
        state.entity_id = entity_ids[world];
        state.entity_generation = entity_generations[world];
        state.time_step_s = time_steps[world];
        state.kinematics.x = kinematics[world];
        state.kinematics.y = kinematics[allocation->world_capacity + world];
        state.kinematics.z = kinematics[2 * allocation->world_capacity + world];
        state.kinematics.vx = kinematics[3 * allocation->world_capacity + world];
        state.kinematics.vy = kinematics[4 * allocation->world_capacity + world];
        state.kinematics.vz = kinematics[5 * allocation->world_capacity + world];
        state.kinematics.heading = kinematics[6 * allocation->world_capacity + world];
        state.kinematics.pitch = kinematics[7 * allocation->world_capacity + world];
        state.kinematics.roll = kinematics[8 * allocation->world_capacity + world];
        state.dynamics.p = dynamics[kDynP * allocation->world_capacity + world];
        state.dynamics.q = dynamics[kDynQ * allocation->world_capacity + world];
        state.dynamics.r = dynamics[kDynR * allocation->world_capacity + world];
        state.dynamics.elevator_pos =
            dynamics[kDynElevatorPos * allocation->world_capacity + world];
        state.dynamics.aileron_pos = dynamics[kDynAileronPos * allocation->world_capacity + world];
        state.dynamics.rudder_pos = dynamics[kDynRudderPos * allocation->world_capacity + world];
        state.dynamics.throttle_state =
            dynamics[kDynThrottleState * allocation->world_capacity + world];
        state.dynamics.dry_thrust_state_n =
            dynamics[kDynDryThrustState * allocation->world_capacity + world];
        state.dynamics.ab_state = dynamics[kDynAbState * allocation->world_capacity + world];
        state.dynamics.current_thrust_n =
            dynamics[kDynCurrentThrust * allocation->world_capacity + world];
        state.dynamics.dynamic_pressure =
            dynamics[kDynDynamicPressure * allocation->world_capacity + world];
        state.dynamics.angle_of_attack = dynamics[kDynAlpha * allocation->world_capacity + world];
        state.dynamics.angle_of_attack_rate_dps =
            dynamics[kDynAlphaRate * allocation->world_capacity + world];
        state.dynamics.previous_angle_of_attack =
            dynamics[kDynPreviousAlpha * allocation->world_capacity + world];
        state.dynamics.sideslip_angle = dynamics[kDynBeta * allocation->world_capacity + world];
        state.dynamics.mach_number = dynamics[kDynMach * allocation->world_capacity + world];
        state.dynamics.lift_coefficient =
            dynamics[kDynLiftCoefficient * allocation->world_capacity + world];
        state.dynamics.drag_coefficient =
            dynamics[kDynDragCoefficient * allocation->world_capacity + world];
        state.dynamics.stall_progress =
            dynamics[kDynStallProgress * allocation->world_capacity + world];
        state.dynamics.gear_extension =
            dynamics[kDynGearExtension * allocation->world_capacity + world];
        state.phase_d.instrument.alt_baro_m =
            phase_d_instruments[kInstAltBaro * allocation->world_capacity + world];
        state.phase_d.instrument.alt_radar_m =
            phase_d_instruments[kInstAltRadar * allocation->world_capacity + world];
        state.phase_d.instrument.ias_mps =
            phase_d_instruments[kInstIas * allocation->world_capacity + world];
        state.phase_d.instrument.mach =
            phase_d_instruments[kInstMach * allocation->world_capacity + world];
        state.phase_d.instrument.vvi_mps =
            phase_d_instruments[kInstVvi * allocation->world_capacity + world];
        state.phase_d.instrument.pitch_deg =
            phase_d_instruments[kInstPitch * allocation->world_capacity + world];
        state.phase_d.instrument.roll_deg =
            phase_d_instruments[kInstRoll * allocation->world_capacity + world];
        state.phase_d.instrument.heading_deg =
            phase_d_instruments[kInstHeading * allocation->world_capacity + world];
        state.phase_d.instrument.aoa_deg =
            phase_d_instruments[kInstAoa * allocation->world_capacity + world];
        state.phase_d.instrument.beta_deg =
            phase_d_instruments[kInstBeta * allocation->world_capacity + world];
        state.phase_d.instrument.g_load_normal =
            phase_d_instruments[kInstGNormal * allocation->world_capacity + world];
        state.phase_d.instrument.g_load_axial =
            phase_d_instruments[kInstGAxial * allocation->world_capacity + world];
        state.phase_d.instrument.p_deg_s =
            phase_d_instruments[kInstP * allocation->world_capacity + world];
        state.phase_d.instrument.q_deg_s =
            phase_d_instruments[kInstQ * allocation->world_capacity + world];
        state.phase_d.instrument.r_deg_s =
            phase_d_instruments[kInstR * allocation->world_capacity + world];
        state.phase_d.instrument.engine_rpm_pct =
            phase_d_instruments[kInstEngineRpm * allocation->world_capacity + world];
        state.phase_d.instrument.fuel_flow_kg_h =
            phase_d_instruments[kInstFuelFlow * allocation->world_capacity + world];
        state.phase_d.instrument.throttle_pos =
            phase_d_instruments[kInstThrottle * allocation->world_capacity + world];
        state.phase_d.instrument.fuel_internal_kg =
            phase_d_instruments[kInstFuelInternal * allocation->world_capacity + world];
        state.phase_d.instrument.fuel_external_kg =
            phase_d_instruments[kInstFuelExternal * allocation->world_capacity + world];
        state.phase_d.instrument.gear_pos =
            phase_d_instruments[kInstGear * allocation->world_capacity + world];
        state.phase_d.instrument.flaps_pos =
            phase_d_instruments[kInstFlaps * allocation->world_capacity + world];
        state.phase_d.instrument.speedbrake_pos =
            phase_d_instruments[kInstSpeedbrake * allocation->world_capacity + world];
        state.phase_d.observation.id = phase_d_observation_ids[world];
        state.phase_d.observation.sim_time =
            phase_d_observations[kObsSimTime * allocation->world_capacity + world];
        state.phase_d.observation.x =
            phase_d_observations[kObsX * allocation->world_capacity + world];
        state.phase_d.observation.y =
            phase_d_observations[kObsY * allocation->world_capacity + world];
        state.phase_d.observation.z =
            phase_d_observations[kObsZ * allocation->world_capacity + world];
        state.phase_d.observation.vx =
            phase_d_observations[kObsVx * allocation->world_capacity + world];
        state.phase_d.observation.vy =
            phase_d_observations[kObsVy * allocation->world_capacity + world];
        state.phase_d.observation.vz =
            phase_d_observations[kObsVz * allocation->world_capacity + world];
        state.phase_d.observation.heading =
            phase_d_observations[kObsHeading * allocation->world_capacity + world];
        state.phase_d.observation.pitch =
            phase_d_observations[kObsPitch * allocation->world_capacity + world];
        state.phase_d.observation.roll =
            phase_d_observations[kObsRoll * allocation->world_capacity + world];
        state.phase_d.observation.speed =
            phase_d_observations[kObsSpeed * allocation->world_capacity + world];
        state.phase_d.observation.health =
            phase_d_observations[kObsHealth * allocation->world_capacity + world];
        state.phase_d.observation.gear_state =
            phase_d_observations[kObsGear * allocation->world_capacity + world];
        state.phase_d.observation.throttle =
            phase_d_observations[kObsThrottle * allocation->world_capacity + world];
        state.phase_d.observation.total_reward =
            phase_d_observations[kObsTotalReward * allocation->world_capacity + world];
        state.phase_d.reward.survival_term =
            phase_d_rewards[kRewardSurvival * allocation->world_capacity + world];
        state.phase_d.reward.speed_term =
            phase_d_rewards[kRewardSpeed * allocation->world_capacity + world];
        state.phase_d.reward.total_reward =
            phase_d_rewards[kRewardTotal * allocation->world_capacity + world];
        state.phase_d.reward.fact_snapshot_version = phase_d_reward_versions[world];
        state.phase_d.termination.terminated = phase_d_termination_flags[world] != 0;
        state.phase_d.termination.truncated = false;
        state.phase_d.termination.reason_code = static_cast<CudaResidentTerminationCode>(
            phase_d_termination_codes[world]);
        state.phase_d.termination.snapshot_version = phase_d_reward_versions[world];
        state.phase_d.events_empty = phase_d_event_empty[world] != 0;
        state.controls.stick_pitch = control_doubles[world];
        state.controls.stick_roll = control_doubles[allocation->world_capacity + world];
        state.controls.rudder = control_doubles[2 * allocation->world_capacity + world];
        state.controls.throttle = control_doubles[3 * allocation->world_capacity + world];
        state.controls.brake = control_doubles[4 * allocation->world_capacity + world];
        state.controls.gear_handle = control_floats[world];
        state.controls.flaps = control_floats[allocation->world_capacity + world];
        state.controls.speedbrake = control_floats[2 * allocation->world_capacity + world];
        state.controls.brake_left = control_flags[world] != 0;
        state.controls.brake_right = control_flags[allocation->world_capacity + world] != 0;
        state.controls.active = control_flags[2 * allocation->world_capacity + world] != 0;
        state.prepared_controls.stick_roll_filt = prepared_doubles[world];
        state.prepared_controls.stick_pitch_filt =
            prepared_doubles[allocation->world_capacity + world];
        state.prepared_controls.stick_yaw_filt =
            prepared_doubles[2 * allocation->world_capacity + world];
        state.prepared_controls.stick_yaw_cmd =
            prepared_doubles[3 * allocation->world_capacity + world];
        state.prepared_controls.valid = prepared_flags[world] != 0;
        state.prepared_controls.manual_takeover =
            prepared_flags[allocation->world_capacity + world] != 0;
        state.prepared_controls.phase_version = phase_versions[world];
        state.clock_tick = clock_ticks[world];
        state.simulation_time_s = simulation_times[world];
        state.global_version = global_versions[world];
        state.barrier_sequence = barrier_sequences[world];
        state.barrier = static_cast<CudaResidentBarrierCode>(barrier_codes[world]);
        for (std::size_t shard = 0; shard < kCudaResidentShardCount; ++shard) {
            state.shard_versions[shard] =
                shard_versions[shard * allocation->world_capacity + world];
        }
        next_snapshot.worlds.push_back(state);
    }
    *snapshot = std::move(next_snapshot);
    if (error != nullptr) {
        error->clear();
    }
    return true;
}


} // namespace runtime::cuda_resident::detail
