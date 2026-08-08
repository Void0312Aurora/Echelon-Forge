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
    const auto *projected_instruments =
        host_field<double>(host_slot, allocation->state_layout.projected_instruments);
    const auto *projected_observations =
        host_field<double>(host_slot, allocation->state_layout.projected_observations);
    const auto *projected_observation_ids =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.projected_observation_ids);
    const auto *projected_rewards =
        host_field<double>(host_slot, allocation->state_layout.projected_rewards);
    const auto *projected_reward_versions =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.projected_reward_versions);
    const auto *projected_termination_flags =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.projected_termination_flags);
    const auto *projected_termination_codes =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.projected_termination_codes);
    const auto *projected_event_empty =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.projected_event_empty);
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
    const auto *prepared_control_versions =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.prepared_control_versions);
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
        state.observation_projection.instrument.alt_baro_m =
            projected_instruments[kInstAltBaro * allocation->world_capacity + world];
        state.observation_projection.instrument.alt_radar_m =
            projected_instruments[kInstAltRadar * allocation->world_capacity + world];
        state.observation_projection.instrument.ias_mps =
            projected_instruments[kInstIas * allocation->world_capacity + world];
        state.observation_projection.instrument.mach =
            projected_instruments[kInstMach * allocation->world_capacity + world];
        state.observation_projection.instrument.vvi_mps =
            projected_instruments[kInstVvi * allocation->world_capacity + world];
        state.observation_projection.instrument.pitch_deg =
            projected_instruments[kInstPitch * allocation->world_capacity + world];
        state.observation_projection.instrument.roll_deg =
            projected_instruments[kInstRoll * allocation->world_capacity + world];
        state.observation_projection.instrument.heading_deg =
            projected_instruments[kInstHeading * allocation->world_capacity + world];
        state.observation_projection.instrument.aoa_deg =
            projected_instruments[kInstAoa * allocation->world_capacity + world];
        state.observation_projection.instrument.beta_deg =
            projected_instruments[kInstBeta * allocation->world_capacity + world];
        state.observation_projection.instrument.g_load_normal =
            projected_instruments[kInstGNormal * allocation->world_capacity + world];
        state.observation_projection.instrument.g_load_axial =
            projected_instruments[kInstGAxial * allocation->world_capacity + world];
        state.observation_projection.instrument.p_deg_s =
            projected_instruments[kInstP * allocation->world_capacity + world];
        state.observation_projection.instrument.q_deg_s =
            projected_instruments[kInstQ * allocation->world_capacity + world];
        state.observation_projection.instrument.r_deg_s =
            projected_instruments[kInstR * allocation->world_capacity + world];
        state.observation_projection.instrument.engine_rpm_pct =
            projected_instruments[kInstEngineRpm * allocation->world_capacity + world];
        state.observation_projection.instrument.fuel_flow_kg_h =
            projected_instruments[kInstFuelFlow * allocation->world_capacity + world];
        state.observation_projection.instrument.throttle_pos =
            projected_instruments[kInstThrottle * allocation->world_capacity + world];
        state.observation_projection.instrument.fuel_internal_kg =
            projected_instruments[kInstFuelInternal * allocation->world_capacity + world];
        state.observation_projection.instrument.fuel_external_kg =
            projected_instruments[kInstFuelExternal * allocation->world_capacity + world];
        state.observation_projection.instrument.gear_pos =
            projected_instruments[kInstGear * allocation->world_capacity + world];
        state.observation_projection.instrument.flaps_pos =
            projected_instruments[kInstFlaps * allocation->world_capacity + world];
        state.observation_projection.instrument.speedbrake_pos =
            projected_instruments[kInstSpeedbrake * allocation->world_capacity + world];
        state.observation_projection.observation.id = projected_observation_ids[world];
        state.observation_projection.observation.sim_time =
            projected_observations[kObsSimTime * allocation->world_capacity + world];
        state.observation_projection.observation.x =
            projected_observations[kObsX * allocation->world_capacity + world];
        state.observation_projection.observation.y =
            projected_observations[kObsY * allocation->world_capacity + world];
        state.observation_projection.observation.z =
            projected_observations[kObsZ * allocation->world_capacity + world];
        state.observation_projection.observation.vx =
            projected_observations[kObsVx * allocation->world_capacity + world];
        state.observation_projection.observation.vy =
            projected_observations[kObsVy * allocation->world_capacity + world];
        state.observation_projection.observation.vz =
            projected_observations[kObsVz * allocation->world_capacity + world];
        state.observation_projection.observation.heading =
            projected_observations[kObsHeading * allocation->world_capacity + world];
        state.observation_projection.observation.pitch =
            projected_observations[kObsPitch * allocation->world_capacity + world];
        state.observation_projection.observation.roll =
            projected_observations[kObsRoll * allocation->world_capacity + world];
        state.observation_projection.observation.speed =
            projected_observations[kObsSpeed * allocation->world_capacity + world];
        state.observation_projection.observation.health =
            projected_observations[kObsHealth * allocation->world_capacity + world];
        state.observation_projection.observation.gear_state =
            projected_observations[kObsGear * allocation->world_capacity + world];
        state.observation_projection.observation.throttle =
            projected_observations[kObsThrottle * allocation->world_capacity + world];
        state.observation_projection.observation.total_reward =
            projected_observations[kObsTotalReward * allocation->world_capacity + world];
        state.observation_projection.reward.survival_term =
            projected_rewards[kRewardSurvival * allocation->world_capacity + world];
        state.observation_projection.reward.speed_term =
            projected_rewards[kRewardSpeed * allocation->world_capacity + world];
        state.observation_projection.reward.total_reward =
            projected_rewards[kRewardTotal * allocation->world_capacity + world];
        state.observation_projection.reward.fact_snapshot_version =
            projected_reward_versions[world];
        state.observation_projection.termination.terminated =
            projected_termination_flags[world] != 0;
        state.observation_projection.termination.truncated = false;
        state.observation_projection.termination.reason_code =
            static_cast<CudaResidentTerminationCode>(projected_termination_codes[world]);
        state.observation_projection.termination.snapshot_version =
            projected_reward_versions[world];
        state.observation_projection.events_empty = projected_event_empty[world] != 0;
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
        state.prepared_controls.control_version = prepared_control_versions[world];
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
