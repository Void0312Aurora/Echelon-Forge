#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_internal.cuh"
#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_math.cuh"

#include "runtime/contracts/cuda_resident_observation_projection_fixture_contract.h"

#include <cmath>
namespace runtime::cuda_resident::detail {
namespace {
__global__ void instrument_projection_kernel(std::size_t world_capacity, const double *kinematics,
                                             const double *dynamics,
                                             const double *flight_dynamics_forces,
                                             double *instruments, std::uint32_t *status) {
    const std::size_t world = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world >= world_capacity) return;
    const double z = kinematics[2 * world_capacity + world];
    const double vx = kinematics[3 * world_capacity + world];
    const double vy = kinematics[4 * world_capacity + world];
    const double vz = kinematics[5 * world_capacity + world];
    const double heading = kinematics[6 * world_capacity + world];
    const double pitch = kinematics[7 * world_capacity + world];
    const double roll = kinematics[8 * world_capacity + world];
    const double qbar = dynamics[kDynDynamicPressure * world_capacity + world];
    const double mach = dynamics[kDynMach * world_capacity + world];
    const double alpha = dynamics[kDynAlpha * world_capacity + world];
    const double beta = dynamics[kDynBeta * world_capacity + world];
    const double p = dynamics[kDynP * world_capacity + world];
    const double q_rate = dynamics[kDynQ * world_capacity + world];
    const double r = dynamics[kDynR * world_capacity + world];
    const double mass =
        kFlightDynamicsEmptyMassKg + kFlightDynamicsFuelMassKg + kFlightDynamicsStoresMassKg;
    const FlightDynamicsRotation rotation = flight_dynamics_rotation(heading, pitch, roll);
    double body_x = 0.0;
    double body_y = 0.0;
    double body_z = 0.0;
    flight_dynamics_world_to_body(flight_dynamics_forces[kForceX * world_capacity + world],
                                  flight_dynamics_forces[kForceY * world_capacity + world],
                                  flight_dynamics_forces[kForceZ * world_capacity + world] +
                                      mass * kFlightDynamicsGravityMps2,
                                  rotation, &body_x, &body_y, &body_z);
    const double g_normal = body_z / (mass * kFlightDynamicsGravityMps2);
    const double g_axial = body_x / (mass * kFlightDynamicsGravityMps2);
    const double ias = sqrt(fmax(0.0, 2.0 * qbar / kFlightDynamicsSeaLevelDensityKgM3));
    const double p_deg = flight_dynamics_rad_to_deg(p);
    const double q_deg = flight_dynamics_rad_to_deg(q_rate);
    const double r_deg = flight_dynamics_rad_to_deg(r);
    instruments[kInstAltBaro * world_capacity + world] = z;
    instruments[kInstAltRadar * world_capacity + world] = z;
    instruments[kInstIas * world_capacity + world] = ias;
    instruments[kInstMach * world_capacity + world] = mach;
    instruments[kInstVvi * world_capacity + world] = vz;
    instruments[kInstPitch * world_capacity + world] = pitch;
    instruments[kInstRoll * world_capacity + world] = roll;
    instruments[kInstHeading * world_capacity + world] = heading;
    instruments[kInstAoa * world_capacity + world] = alpha;
    instruments[kInstBeta * world_capacity + world] = beta;
    instruments[kInstGNormal * world_capacity + world] = g_normal;
    instruments[kInstGAxial * world_capacity + world] = g_axial;
    instruments[kInstP * world_capacity + world] = p_deg;
    instruments[kInstQ * world_capacity + world] = q_deg;
    instruments[kInstR * world_capacity + world] = r_deg;
    bool invalid = !isfinite(vx) || !isfinite(vy) || !isfinite(ias) || !isfinite(p_deg) ||
                   !isfinite(q_deg) || !isfinite(r_deg) || !isfinite(g_normal) ||
                   !isfinite(g_axial);
    if (invalid) atomicExch(status, 1U);
}

__global__ void configuration_projection_kernel(std::size_t world_capacity, const double *dynamics,
                                                const double *control_doubles,
                                                const float *control_floats, double *instruments,
                                                std::uint32_t *status) {
    const std::size_t world = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world >= world_capacity) return;
    const double engine_rpm = dynamics[kDynThrottleState * world_capacity + world] * 100.0 +
                              dynamics[kDynAbState * world_capacity + world] * 10.0;
    const double fuel_flow = dynamics[kDynCurrentThrust * world_capacity + world] *
                             kObservationProjectionFuelFlowTsfcNhPerN;
    const double throttle = control_doubles[3 * world_capacity + world];
    const double gear = dynamics[kDynGearExtension * world_capacity + world];
    const double flaps = static_cast<double>(control_floats[world_capacity + world]);
    const double speedbrake = static_cast<double>(control_floats[2 * world_capacity + world]);
    instruments[kInstEngineRpm * world_capacity + world] = engine_rpm;
    instruments[kInstFuelFlow * world_capacity + world] = fuel_flow;
    instruments[kInstThrottle * world_capacity + world] = throttle;
    instruments[kInstFuelInternal * world_capacity + world] = kFlightDynamicsFuelMassKg;
    instruments[kInstFuelExternal * world_capacity + world] = 0.0;
    instruments[kInstGear * world_capacity + world] = gear;
    instruments[kInstFlaps * world_capacity + world] = flaps;
    instruments[kInstSpeedbrake * world_capacity + world] = speedbrake;
    if (!isfinite(engine_rpm) || !isfinite(fuel_flow) || !isfinite(throttle) || !isfinite(gear) ||
        !isfinite(flaps) || !isfinite(speedbrake)) {
        atomicExch(status, 1U);
    }
}

__global__ void episode_projection_kernel(
    std::size_t world_capacity, const double *time_steps, const double *simulation_times,
    const double *kinematics, const double *dynamics, const double *instruments,
    const std::uint64_t *entity_ids, const std::uint64_t *global_versions, double *observations,
    std::uint64_t *observation_ids, double *rewards, std::uint64_t *reward_versions,
    std::uint8_t *termination_flags, std::uint8_t *termination_codes, std::uint8_t *event_empty,
    std::uint32_t *status) {
    const std::size_t world = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world >= world_capacity) return;
    const double dt = static_cast<double>(static_cast<float>(time_steps[world]));
    const double x = kinematics[0 * world_capacity + world];
    const double y = kinematics[1 * world_capacity + world];
    const double z = kinematics[2 * world_capacity + world];
    const double vx = kinematics[3 * world_capacity + world];
    const double vy = kinematics[4 * world_capacity + world];
    const double vz = kinematics[5 * world_capacity + world];
    const double heading = kinematics[6 * world_capacity + world];
    const double pitch = kinematics[7 * world_capacity + world];
    const double roll = kinematics[8 * world_capacity + world];
    const double speed = sqrt(fmax(0.0, vx * vx + vy * vy + vz * vz));
    const double survival = kObservationProjectionSurvivalReward;
    const double speed_term = speed * kObservationProjectionSpeedRewardWeight;
    const double total = survival + speed_term;
    const bool finite = isfinite(dt) && isfinite(x) && isfinite(y) && isfinite(z) && isfinite(vx) &&
                        isfinite(vy) && isfinite(vz) && isfinite(heading) && isfinite(pitch) &&
                        isfinite(roll) && isfinite(speed) && isfinite(total);
    const bool envelope = z < 100.0 || z > 10000.0 || speed < 50.0 || speed > 350.0 ||
                          fabs(vy) > 50.0 || fabs(vz) > 50.0 || fabs(pitch) > 10.0 ||
                          fabs(roll) > 10.0 ||
                          fabs(dynamics[kDynAlpha * world_capacity + world]) > 14.0;
    const std::uint8_t reason =
        !finite    ? static_cast<std::uint8_t>(CudaResidentTerminationCode::nan_guard)
        : envelope ? static_cast<std::uint8_t>(CudaResidentTerminationCode::envelope_violation)
                   : static_cast<std::uint8_t>(CudaResidentTerminationCode::running);
    const std::uint8_t terminated = static_cast<std::uint8_t>(reason != 0);
    const double obs[kObservationProjectionObservationFieldCount] = {
        simulation_times[world] + time_steps[world],
        x,
        y,
        z,
        vx,
        vy,
        vz,
        heading,
        pitch,
        roll,
        speed,
        kObservationProjectionHealth,
        instruments[kInstGear * world_capacity + world],
        instruments[kInstThrottle * world_capacity + world],
        total,
    };
    for (std::size_t field = 0; field < kObservationProjectionObservationFieldCount; ++field) {
        observations[field * world_capacity + world] = obs[field];
    }
    observation_ids[world] = entity_ids[world];
    rewards[kRewardSurvival * world_capacity + world] = survival;
    rewards[kRewardSpeed * world_capacity + world] = speed_term;
    rewards[kRewardTotal * world_capacity + world] = total;
    reward_versions[world] = global_versions[world] + 1U;
    termination_flags[world] = terminated;
    termination_codes[world] = reason;
    event_empty[world] = 1;
    if (!finite || !isfinite(obs[kObsTotalReward])) atomicExch(status, 1U);
}

} // namespace

cudaError_t launch_instrument_projection(CudaWorldStoreDeviceAllocation *allocation,
                                         std::uint8_t slot_index) noexcept {
    if (allocation == nullptr) return cudaErrorInvalidValue;
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    std::uint8_t *slot = allocation->state_slots[slot_index];
    instrument_projection_kernel<<<blocks, threads>>>(
        allocation->world_capacity, device_field<double>(slot, allocation->state_layout.kinematics),
        device_field<double>(slot, allocation->state_layout.dynamics),
        device_field<double>(slot, allocation->state_layout.flight_dynamics_forces),
        device_field<double>(slot, allocation->state_layout.projected_instruments),
        allocation->barrier_status);
    return cudaGetLastError();
}

cudaError_t launch_configuration_projection(CudaWorldStoreDeviceAllocation *allocation,
                                            std::uint8_t slot_index) noexcept {
    if (allocation == nullptr) return cudaErrorInvalidValue;
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    std::uint8_t *slot = allocation->state_slots[slot_index];
    configuration_projection_kernel<<<blocks, threads>>>(
        allocation->world_capacity, device_field<double>(slot, allocation->state_layout.dynamics),
        device_field<double>(slot, allocation->state_layout.control_doubles),
        device_field<float>(slot, allocation->state_layout.control_floats),
        device_field<double>(slot, allocation->state_layout.projected_instruments),
        allocation->barrier_status);
    return cudaGetLastError();
}

cudaError_t launch_episode_projection(CudaWorldStoreDeviceAllocation *allocation,
                                      std::uint8_t slot_index) noexcept {
    if (allocation == nullptr) return cudaErrorInvalidValue;
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    std::uint8_t *slot = allocation->state_slots[slot_index];
    episode_projection_kernel<<<blocks, threads>>>(
        allocation->world_capacity, device_field<double>(slot, allocation->state_layout.time_steps),
        device_field<double>(slot, allocation->state_layout.simulation_times),
        device_field<double>(slot, allocation->state_layout.kinematics),
        device_field<double>(slot, allocation->state_layout.dynamics),
        device_field<double>(slot, allocation->state_layout.projected_instruments),
        device_field<std::uint64_t>(slot, allocation->state_layout.entity_ids),
        device_field<std::uint64_t>(slot, allocation->state_layout.global_versions),
        device_field<double>(slot, allocation->state_layout.projected_observations),
        device_field<std::uint64_t>(slot, allocation->state_layout.projected_observation_ids),
        device_field<double>(slot, allocation->state_layout.projected_rewards),
        device_field<std::uint64_t>(slot, allocation->state_layout.projected_reward_versions),
        device_field<std::uint8_t>(slot, allocation->state_layout.projected_termination_flags),
        device_field<std::uint8_t>(slot, allocation->state_layout.projected_termination_codes),
        device_field<std::uint8_t>(slot, allocation->state_layout.projected_event_empty),
        allocation->barrier_status);
    return cudaGetLastError();
}

bool query_cuda_world_store_observation_projection_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error) {
    return query_cuda_kernel_resources(episode_projection_kernel, "episode_projection_kernel",
                                       resources, error);
}

bool query_cuda_world_store_instrument_projection_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error) {
    return query_cuda_kernel_resources(instrument_projection_kernel, "instrument_projection_kernel",
                                       resources, error);
}

bool query_cuda_world_store_configuration_projection_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error) {
    return query_cuda_kernel_resources(configuration_projection_kernel,
                                       "configuration_projection_kernel", resources, error);
}

} // namespace runtime::cuda_resident::detail
