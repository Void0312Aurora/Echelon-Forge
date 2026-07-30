#include "runtime/facade/internal/cuda_resident/cuda_world_store_device_api.h"

#include <cuda_runtime_api.h>

#include <cmath>
#include <cstddef>
#include <limits>
#include <memory>
#include <new>
#include <utility>
#include <vector>

#include "runtime/contracts/cuda_resident_phase_a_fixture_contract.h"
#include "runtime/contracts/cuda_resident_phase_b_fixture_contract.h"

namespace runtime::cuda_resident::detail {

namespace {

struct alignas(16) CudaWorldLifecycleRecord {
    std::uint64_t reset_generation = 0;
    std::uint32_t seed = 0;
    std::uint32_t reserved = 0;
};

struct alignas(16) HostStateBlock {
    std::byte bytes[16];
};

static_assert(sizeof(CudaWorldLifecycleRecord) == 16);
static_assert(sizeof(HostStateBlock) == 16);

inline constexpr std::size_t kKinematicsFieldCount = 9;
inline constexpr std::size_t kControlDoubleFieldCount = 5;
inline constexpr std::size_t kControlFloatFieldCount = 3;
inline constexpr std::size_t kControlFlagFieldCount = 3;
inline constexpr std::size_t kPreparedDoubleFieldCount = 4;
inline constexpr std::size_t kPreparedFlagFieldCount = 2;
inline constexpr std::size_t kDynamicsDoubleFieldCount = 20;
inline constexpr std::size_t kPhaseBForceFieldCount = 6;

struct CudaWorldStateSlotLayout {
    std::size_t setup_complete = 0;
    std::size_t entity_ids = 0;
    std::size_t entity_generations = 0;
    std::size_t time_steps = 0;
    std::size_t kinematics = 0;
    std::size_t dynamics = 0;
    std::size_t phase_b_forces = 0;
    std::size_t control_doubles = 0;
    std::size_t control_floats = 0;
    std::size_t control_flags = 0;
    std::size_t prepared_doubles = 0;
    std::size_t prepared_flags = 0;
    std::size_t phase_versions = 0;
    std::size_t clock_ticks = 0;
    std::size_t simulation_times = 0;
    std::size_t global_versions = 0;
    std::size_t barrier_sequences = 0;
    std::size_t barrier_codes = 0;
    std::size_t shard_versions = 0;
    std::size_t slot_bytes = 0;
};

std::string cuda_error_message(const char *operation, cudaError_t status) {
    return std::string(operation) + ": " + cudaGetErrorString(status);
}

bool consume_fault(bool *fault) noexcept {
    if (fault == nullptr || !*fault) {
        return false;
    }
    *fault = false;
    return true;
}

bool checked_product(std::size_t left, std::size_t right, std::size_t *result) noexcept {
    if (result == nullptr ||
        (right != 0 && left > std::numeric_limits<std::size_t>::max() / right)) {
        return false;
    }
    *result = left * right;
    return true;
}

bool checked_add(std::size_t left, std::size_t right, std::size_t *result) noexcept {
    if (result == nullptr || left > std::numeric_limits<std::size_t>::max() - right) {
        return false;
    }
    *result = left + right;
    return true;
}

bool checked_align(std::size_t value, std::size_t alignment, std::size_t *result) noexcept {
    const std::size_t remainder = value % alignment;
    const std::size_t padding = remainder == 0 ? 0 : alignment - remainder;
    return checked_add(value, padding, result);
}

template <typename T>
bool append_array(std::size_t count, std::size_t *cursor, std::size_t *offset) noexcept {
    if (cursor == nullptr || offset == nullptr || !checked_align(*cursor, alignof(T), offset)) {
        return false;
    }
    std::size_t bytes = 0;
    return checked_product(count, sizeof(T), &bytes) && checked_add(*offset, bytes, cursor);
}

bool build_state_layout(std::size_t world_capacity, CudaWorldStateSlotLayout *layout) noexcept {
    if (layout == nullptr) {
        return false;
    }
    std::size_t cursor = 0;
    std::size_t kinematics_count = 0;
    std::size_t control_double_count = 0;
    std::size_t control_float_count = 0;
    std::size_t control_flag_count = 0;
    std::size_t prepared_double_count = 0;
    std::size_t prepared_flag_count = 0;
    std::size_t dynamics_count = 0;
    std::size_t phase_b_force_count = 0;
    std::size_t shard_version_count = 0;
    if (!checked_product(world_capacity, kKinematicsFieldCount, &kinematics_count) ||
        !checked_product(world_capacity, kControlDoubleFieldCount, &control_double_count) ||
        !checked_product(world_capacity, kControlFloatFieldCount, &control_float_count) ||
        !checked_product(world_capacity, kControlFlagFieldCount, &control_flag_count) ||
        !checked_product(world_capacity, kPreparedDoubleFieldCount, &prepared_double_count) ||
        !checked_product(world_capacity, kPreparedFlagFieldCount, &prepared_flag_count) ||
        !checked_product(world_capacity, kDynamicsDoubleFieldCount, &dynamics_count) ||
        !checked_product(world_capacity, kPhaseBForceFieldCount, &phase_b_force_count) ||
        !checked_product(world_capacity, kCudaResidentShardCount, &shard_version_count)) {
        return false;
    }
    if (!append_array<std::uint8_t>(world_capacity, &cursor, &layout->setup_complete) ||
        !append_array<std::uint64_t>(world_capacity, &cursor, &layout->entity_ids) ||
        !append_array<std::uint32_t>(world_capacity, &cursor, &layout->entity_generations) ||
        !append_array<double>(world_capacity, &cursor, &layout->time_steps) ||
        !append_array<double>(kinematics_count, &cursor, &layout->kinematics) ||
        !append_array<double>(dynamics_count, &cursor, &layout->dynamics) ||
        !append_array<double>(phase_b_force_count, &cursor, &layout->phase_b_forces) ||
        !append_array<double>(control_double_count, &cursor, &layout->control_doubles) ||
        !append_array<float>(control_float_count, &cursor, &layout->control_floats) ||
        !append_array<std::uint8_t>(control_flag_count, &cursor, &layout->control_flags) ||
        !append_array<double>(prepared_double_count, &cursor, &layout->prepared_doubles) ||
        !append_array<std::uint8_t>(prepared_flag_count, &cursor, &layout->prepared_flags) ||
        !append_array<std::uint64_t>(world_capacity, &cursor, &layout->phase_versions) ||
        !append_array<std::uint64_t>(world_capacity, &cursor, &layout->clock_ticks) ||
        !append_array<double>(world_capacity, &cursor, &layout->simulation_times) ||
        !append_array<std::uint64_t>(world_capacity, &cursor, &layout->global_versions) ||
        !append_array<std::uint64_t>(world_capacity, &cursor, &layout->barrier_sequences) ||
        !append_array<std::uint8_t>(world_capacity, &cursor, &layout->barrier_codes) ||
        !append_array<std::uint64_t>(shard_version_count, &cursor, &layout->shard_versions) ||
        !checked_align(cursor, alignof(HostStateBlock), &layout->slot_bytes)) {
        return false;
    }
    return true;
}

template <typename T> T *host_field(std::vector<HostStateBlock> &storage, std::size_t offset) {
    return reinterpret_cast<T *>(reinterpret_cast<std::byte *>(storage.data()) + offset);
}

template <typename T>
const T *host_field(const std::vector<HostStateBlock> &storage, std::size_t offset) {
    return reinterpret_cast<const T *>(reinterpret_cast<const std::byte *>(storage.data()) +
                                       offset);
}

std::vector<HostStateBlock> make_host_slot(std::size_t slot_bytes) {
    return std::vector<HostStateBlock>((slot_bytes + sizeof(HostStateBlock) - 1) /
                                       sizeof(HostStateBlock));
}

template <typename T> T *device_field(std::uint8_t *slot_base, std::size_t offset) noexcept {
    return reinterpret_cast<T *>(slot_base + offset);
}

template <typename T>
const T *device_field(const std::uint8_t *slot_base, std::size_t offset) noexcept {
    return reinterpret_cast<const T *>(slot_base + offset);
}

__device__ bool increment_would_overflow(std::uint64_t value) {
    return value == ~std::uint64_t{0};
}

__global__ void
prepare_phase_a_controls_kernel(std::size_t world_capacity, const double *time_steps,
                                const double *control_doubles, const std::uint8_t *control_flags,
                                double *prepared_doubles, std::uint8_t *prepared_flags,
                                std::uint64_t *phase_versions, std::uint32_t *status) {
    const std::size_t world_index = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world_index >= world_capacity) {
        return;
    }

    // Match the maintained CPU FlightControl stage's ecs_ftime_t=float boundary.
    const double dt = static_cast<double>(static_cast<float>(time_steps[world_index]));
    const double tau = kCudaResidentPhaseAStickTauS;
    const double alpha = dt / (tau + dt);
    const bool active = control_flags[2 * world_capacity + world_index] != 0;
    // The frozen flight-control SoA preserves the maintained CPU component order:
    // pitch, roll, rudder, throttle, brake. Prepared controls use semantic order.
    const double raw_pitch = control_doubles[world_index];
    const double raw_roll = control_doubles[world_capacity + world_index];
    const double raw_rudder = control_doubles[2 * world_capacity + world_index];
    const bool manual_takeover = active && (fabs(raw_roll) > kCudaResidentPhaseAManualDeadband ||
                                            fabs(raw_pitch) > kCudaResidentPhaseAManualDeadband ||
                                            fabs(raw_rudder) > kCudaResidentPhaseAManualDeadband);
    const double target_roll = manual_takeover ? raw_roll : 0.0;
    const double target_pitch = manual_takeover ? raw_pitch : 0.0;
    const double target_yaw = manual_takeover ? -raw_rudder : 0.0;
    const std::size_t roll_index = world_index;
    const std::size_t pitch_index = world_capacity + world_index;
    const std::size_t yaw_index = 2 * world_capacity + world_index;
    const std::size_t yaw_cmd_index = 3 * world_capacity + world_index;

    bool invalid = !isfinite(dt) || !(dt > 0.0) || !isfinite(alpha) ||
                   increment_would_overflow(phase_versions[world_index]);
    const double next_roll =
        prepared_doubles[roll_index] + alpha * (target_roll - prepared_doubles[roll_index]);
    const double next_pitch =
        prepared_doubles[pitch_index] + alpha * (target_pitch - prepared_doubles[pitch_index]);
    const double next_yaw =
        prepared_doubles[yaw_index] + alpha * (target_yaw - prepared_doubles[yaw_index]);
    invalid = invalid || !isfinite(next_roll) || !isfinite(next_pitch) || !isfinite(next_yaw);
    if (invalid) {
        atomicExch(status, 1U);
        return;
    }

    prepared_doubles[roll_index] = next_roll;
    prepared_doubles[pitch_index] = next_pitch;
    prepared_doubles[yaw_index] = next_yaw;
    prepared_doubles[yaw_cmd_index] = next_yaw;
    prepared_flags[world_index] = 1;
    prepared_flags[world_capacity + world_index] = static_cast<std::uint8_t>(manual_takeover);
    ++phase_versions[world_index];
}

enum PhaseBDynamicsField : std::size_t {
    kDynP = 0,
    kDynQ,
    kDynR,
    kDynElevatorPos,
    kDynAileronPos,
    kDynRudderPos,
    kDynThrottleState,
    kDynDryThrustState,
    kDynAbState,
    kDynCurrentThrust,
    kDynDynamicPressure,
    kDynAlpha,
    kDynAlphaRate,
    kDynPreviousAlpha,
    kDynBeta,
    kDynMach,
    kDynLiftCoefficient,
    kDynDragCoefficient,
    kDynStallProgress,
    kDynGearExtension,
};

enum PhaseBForceField : std::size_t {
    kForceX = 0,
    kForceY,
    kForceZ,
    kTorqueRoll,
    kTorquePitch,
    kTorqueYaw,
};

__device__ inline double phase_b_clamp(double value, double lo, double hi) {
    return fmin(fmax(value, lo), hi);
}

__device__ inline double phase_b_deg_to_rad(double value) {
    return value * 3.1415926535897932384626433832795 / 180.0;
}

__device__ inline double phase_b_rad_to_deg(double value) {
    return value * 180.0 / 3.1415926535897932384626433832795;
}

__device__ inline double phase_b_lerp(double a, double b, double t) {
    return a + (b - a) * phase_b_clamp(t, 0.0, 1.0);
}

__device__ inline double phase_b_lookup(double mach, int table) {
    constexpr double x[] = {0.0, 0.8, 0.95, 1.1, 1.6, 2.0};
    constexpr double cl_alpha[] = {1.00, 1.04, 1.10, 0.96, 0.82, 0.72};
    constexpr double cd0[] = {0.00, 0.005, 0.025, 0.040, 0.030, 0.025};
    constexpr double induced[] = {1.00, 1.00, 1.05, 1.12, 1.05, 1.00};
    constexpr double cm_alpha[] = {1.00, 1.00, 0.96, 0.92, 0.86, 0.82};
    constexpr double control[] = {1.00, 1.00, 0.92, 0.78, 0.68, 0.60};
    const double *values = cl_alpha;
    if (table == 1) values = cd0;
    if (table == 2) values = induced;
    if (table == 3) values = cm_alpha;
    if (table == 4) values = control;
    if (mach <= x[0]) return values[0];
    if (mach >= x[5]) return values[5];
    for (int i = 1; i < 6; ++i) {
        if (mach <= x[i]) {
            const double t = (mach - x[i - 1]) / fmax(1.0e-6, x[i] - x[i - 1]);
            return phase_b_lerp(values[i - 1], values[i], t);
        }
    }
    return values[5];
}

__device__ inline double phase_b_canonical(double value, double quantum) {
    if (!isfinite(value) || quantum <= 0.0) return value;
    if (fabs(value) <= quantum * 0.5) return 0.0;
    const double rounded = nearbyint(value / quantum) * quantum;
    return fabs(rounded) <= quantum * 0.5 ? 0.0 : rounded;
}

struct PhaseBAtmosphere {
    double density;
    double temperature;
    double speed_of_sound;
    double wind_x;
};

__device__ inline PhaseBAtmosphere phase_b_atmosphere(double altitude_m) {
    const double h = fmax(0.0, altitude_m);
    double temperature = kPhaseBSeaLevelTemperatureK;
    double pressure = kPhaseBSeaLevelPressurePa;
    if (h < kPhaseBTropopauseAltitudeM) {
        temperature = kPhaseBSeaLevelTemperatureK - kPhaseBLapseRateKPerM * h;
        pressure = kPhaseBSeaLevelPressurePa *
                   pow(1.0 - kPhaseBLapseRateKPerM * h / kPhaseBSeaLevelTemperatureK,
                       kPhaseBGravityMps2 / (kPhaseBGasConstantDryAir * kPhaseBLapseRateKPerM));
    } else {
        temperature = kPhaseBTropopauseTemperatureK;
        pressure = kPhaseBTropopausePressurePa *
                   exp(-kPhaseBGravityMps2 * (h - kPhaseBTropopauseAltitudeM) /
                       (kPhaseBGasConstantDryAir * kPhaseBTropopauseTemperatureK));
    }
    return {
        pressure / (kPhaseBGasConstantDryAir * temperature),
        temperature,
        sqrt(kPhaseBSpecificHeatRatioAir * kPhaseBGasConstantDryAir * temperature),
        kPhaseBWindBaseMps + kPhaseBWindShearMpsPerKm * h / 1000.0,
    };
}

struct PhaseBRotation {
    double cpsi;
    double spsi;
    double ctheta;
    double stheta;
    double cphi;
    double sphi;
};

__device__ inline PhaseBRotation phase_b_rotation(double heading, double pitch, double roll) {
    const double psi = phase_b_deg_to_rad(90.0 - heading);
    const double theta = phase_b_deg_to_rad(-pitch);
    const double phi = phase_b_deg_to_rad(roll);
    return {cos(psi), sin(psi), cos(theta), sin(theta), cos(phi), sin(phi)};
}

__device__ inline void phase_b_world_to_body(double vx, double vy, double vz,
                                             const PhaseBRotation &rot, double *bx, double *by,
                                             double *bz) {
    *bx = rot.cpsi * rot.ctheta * vx + rot.spsi * rot.ctheta * vy - rot.stheta * vz;
    *by = (rot.cpsi * rot.stheta * rot.sphi - rot.spsi * rot.cphi) * vx +
          (rot.spsi * rot.stheta * rot.sphi + rot.cpsi * rot.cphi) * vy +
          rot.ctheta * rot.sphi * vz;
    *bz = (rot.cpsi * rot.stheta * rot.cphi + rot.spsi * rot.sphi) * vx +
          (rot.spsi * rot.stheta * rot.cphi - rot.cpsi * rot.sphi) * vy +
          rot.ctheta * rot.cphi * vz;
}

__device__ inline void phase_b_body_to_world(double bx, double by, double bz,
                                             const PhaseBRotation &rot, double *vx, double *vy,
                                             double *vz) {
    *vx = rot.cpsi * rot.ctheta * bx +
          (rot.cpsi * rot.stheta * rot.sphi - rot.spsi * rot.cphi) * by +
          (rot.cpsi * rot.stheta * rot.cphi + rot.spsi * rot.sphi) * bz;
    *vy = rot.spsi * rot.ctheta * bx +
          (rot.spsi * rot.stheta * rot.sphi + rot.cpsi * rot.cphi) * by +
          (rot.spsi * rot.stheta * rot.cphi - rot.cpsi * rot.sphi) * bz;
    *vz = -rot.stheta * bx + rot.ctheta * rot.sphi * by + rot.ctheta * rot.cphi * bz;
}

__device__ inline double phase_b_first_order(double state, double command, double dt, double tau) {
    if (!isfinite(state)) state = 0.0;
    if (!isfinite(command)) return state;
    if (tau <= 1.0e-6 || dt <= 0.0) return command;
    const double gain = phase_b_clamp(dt / (tau + dt), 0.0, 1.0);
    return state + gain * (command - state);
}

__device__ inline double phase_b_wrap_360(double angle) {
    angle = fmod(angle, 360.0);
    if (angle < 0.0) angle += 360.0;
    return angle;
}

__global__ void phase_b_forces_kernel(std::size_t world_capacity, const double *time_steps,
                                      const double *control_doubles, const float *control_floats,
                                      const std::uint8_t *control_flags,
                                      const double *prepared_doubles,
                                      const std::uint8_t *prepared_flags, double *kinematics,
                                      double *dynamics, double *phase_b_forces,
                                      std::uint32_t *status) {
    const std::size_t world = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world >= world_capacity) return;

    const double dt = static_cast<double>(static_cast<float>(time_steps[world]));
    const std::size_t kin = world_capacity;
    const std::size_t dyn = world_capacity;
    const bool active = control_flags[2 * world_capacity + world] != 0;
    const bool manual = prepared_flags[world_capacity + world] != 0;
    bool invalid = !isfinite(dt) || dt < kPhaseBMinTimeStepS || dt > kPhaseBMaxTimeStepS;

    double &x = kinematics[0 * kin + world];
    double &y = kinematics[1 * kin + world];
    double &z = kinematics[2 * kin + world];
    double &vx = kinematics[3 * kin + world];
    double &vy = kinematics[4 * kin + world];
    double &vz = kinematics[5 * kin + world];
    double &heading = kinematics[6 * kin + world];
    double &pitch = kinematics[7 * kin + world];
    double &roll = kinematics[8 * kin + world];
    (void)x;
    (void)y;

    double &p = dynamics[kDynP * dyn + world];
    double &q_rate = dynamics[kDynQ * dyn + world];
    double &r = dynamics[kDynR * dyn + world];
    double &elevator = dynamics[kDynElevatorPos * dyn + world];
    double &aileron = dynamics[kDynAileronPos * dyn + world];
    double &rudder = dynamics[kDynRudderPos * dyn + world];
    double &throttle_state = dynamics[kDynThrottleState * dyn + world];
    double &dry_thrust_state = dynamics[kDynDryThrustState * dyn + world];
    double &ab_state = dynamics[kDynAbState * dyn + world];
    double &current_thrust = dynamics[kDynCurrentThrust * dyn + world];
    double &dynamic_pressure = dynamics[kDynDynamicPressure * dyn + world];
    double &alpha = dynamics[kDynAlpha * dyn + world];
    double &alpha_rate = dynamics[kDynAlphaRate * dyn + world];
    double &previous_alpha = dynamics[kDynPreviousAlpha * dyn + world];
    double &beta = dynamics[kDynBeta * dyn + world];
    double &mach = dynamics[kDynMach * dyn + world];
    double &lift_coefficient = dynamics[kDynLiftCoefficient * dyn + world];
    double &drag_coefficient = dynamics[kDynDragCoefficient * dyn + world];
    double &stall_progress = dynamics[kDynStallProgress * dyn + world];
    double &gear_extension = dynamics[kDynGearExtension * dyn + world];

    const double raw_pitch = control_doubles[0 * world_capacity + world];
    const double raw_roll = control_doubles[1 * world_capacity + world];
    const double raw_rudder = control_doubles[2 * world_capacity + world];
    const double raw_throttle = control_doubles[3 * world_capacity + world];
    const double gear_handle = control_floats[0 * world_capacity + world];
    const double flaps =
        phase_b_clamp(static_cast<double>(control_floats[1 * world_capacity + world]), 0.0, 1.0);
    const double speedbrake =
        phase_b_clamp(static_cast<double>(control_floats[2 * world_capacity + world]), 0.0, 1.0);
    (void)raw_pitch;
    (void)raw_roll;
    (void)raw_rudder;

    // Phase A is the authoritative filtered command.  This is the bounded
    // manual/airborne branch of the maintained control model.
    const double stick_roll = phase_b_clamp(prepared_doubles[world], -1.0, 1.0);
    const double stick_pitch = phase_b_clamp(prepared_doubles[world_capacity + world], -1.0, 1.0);
    const double stick_yaw = phase_b_clamp(prepared_doubles[2 * world_capacity + world], -1.0, 1.0);
    double p_cmd = stick_roll * 1.2;
    double q_cmd = stick_pitch * 0.8;
    double r_cmd = prepared_doubles[3 * world_capacity + world] * 0.8;

    // The fixed fixture has no instrument stage between windows, so its
    // initial/held normal-load sensor value is zero, matching the CPU trace.
    const double g_cmd = stick_pitch >= 0.0 ? 1.0 + stick_pitch * 7.0 : 1.0 + stick_pitch * 3.0;
    q_cmd = phase_b_clamp(0.30 * g_cmd, -0.8, 0.8);
    const double speed = sqrt(vx * vx + vy * vy + vz * vz);
    const double v_eff = fmax(50.0, speed);
    const double phi = phase_b_deg_to_rad(roll);
    const double theta = phase_b_deg_to_rad(pitch);
    const double r_turn = (kPhaseBGravityMps2 / v_eff) * sin(phi) * cos(theta);
    if (manual) {
        r_cmd += 2.0 * phase_b_deg_to_rad(beta) - 0.55 * r;
    } else {
        r_cmd += r_turn - 2.0 * phase_b_deg_to_rad(beta) - 0.55 * (r - r_turn);
    }
    r_cmd = phase_b_clamp(r_cmd, -0.8, 0.8);
    if (fabs(alpha) > 10.0) {
        const double t = phase_b_clamp((fabs(alpha) - 10.0) / 8.0, 0.0, 1.0);
        q_cmd *= 1.0 - t;
    }
    if (fabs(alpha) > 18.0) q_cmd = fmin(q_cmd, -0.15);

    const double aileron_cmd = phase_b_clamp(1.2 * (p_cmd - p), -1.0, 1.0);
    const double elevator_cmd = phase_b_clamp(0.9 * (q_cmd - q_rate), -1.0, 1.0);
    double rudder_cmd = 1.2 * (r_cmd - r) - 0.25 * aileron_cmd;
    rudder_cmd = phase_b_clamp(rudder_cmd, -1.0, 1.0);
    const double gear_target = active && gear_handle >= 0.5 ? 1.0 : 0.0;
    gear_extension += (gear_target >= gear_extension ? 1.0 : -1.0) * dt / 5.0;
    gear_extension = phase_b_clamp(gear_extension, 0.0, 1.0);

    elevator = phase_b_first_order(elevator, elevator_cmd, dt, kPhaseBAeroElevatorTauS);
    aileron = phase_b_first_order(aileron, aileron_cmd, dt, kPhaseBAeroAileronTauS);
    rudder = phase_b_first_order(rudder, rudder_cmd, dt, kPhaseBAeroRudderTauS);
    elevator = phase_b_clamp(elevator, -1.0, 1.0);
    aileron = phase_b_clamp(aileron, -1.0, 1.0);
    rudder = phase_b_clamp(rudder, -1.0, 1.0);

    const PhaseBAtmosphere atmosphere = phase_b_atmosphere(z);
    const double air_vx = vx - atmosphere.wind_x;
    const double air_vy = vy;
    const double air_vz = vz;
    const double air_speed_sq = air_vx * air_vx + air_vy * air_vy + air_vz * air_vz;
    const double air_speed = sqrt(air_speed_sq);
    dynamic_pressure = phase_b_canonical(0.5 * atmosphere.density * air_speed_sq, 1.0e-10);
    mach = phase_b_canonical(air_speed / atmosphere.speed_of_sound, 0x1p-40);
    const PhaseBRotation rotation = phase_b_rotation(heading, pitch, roll);
    double body_x = 0.0;
    double body_y = 0.0;
    double body_z = 0.0;
    phase_b_world_to_body(air_vx, air_vy, air_vz, rotation, &body_x, &body_y, &body_z);
    const double alpha_raw = phase_b_rad_to_deg(atan2(-body_z, body_x));
    const double beta_arg = phase_b_clamp(body_y / fmax(air_speed, 1.0e-6), -1.0, 1.0);
    const double beta_raw = phase_b_rad_to_deg(asin(beta_arg));
    const double blend = air_speed <= 2.0 ? 0.0 : (air_speed < 8.0 ? (air_speed - 2.0) / 6.0 : 1.0);
    const double old_alpha = alpha;
    alpha = phase_b_clamp((1.0 - blend) * alpha + blend * alpha_raw, -90.0, 90.0);
    beta = phase_b_clamp((1.0 - blend) * beta + blend * beta_raw, -90.0, 90.0);
    alpha = phase_b_canonical(alpha, 0x1p-40);
    beta = phase_b_canonical(beta, 0x1p-40);
    previous_alpha = old_alpha;
    alpha_rate =
        blend > 0.0 && dt > 1.0e-6 ? phase_b_canonical((alpha - old_alpha) / dt, 0x1p-40) : 0.0;
    // RB6 freezes the attached-flow envelope.  Post-stall tables, ground
    // effect, damage, and terrain ownership belong to later capability slices.
    if (fabs(alpha) > 14.0 || z < 100.0 || z > 10000.0) invalid = true;

    const double throttle = phase_b_clamp(raw_throttle, 0.0, 1.0);
    const double throttle_target =
        throttle <= kPhaseBEngineAbThreshold ? throttle : kPhaseBEngineAbThreshold;
    const double spool_tau =
        throttle_target >= throttle_state ? kPhaseBEngineSpoolUpTauS : kPhaseBEngineSpoolDownTauS;
    throttle_state = phase_b_clamp(
        phase_b_first_order(throttle_state, throttle_target, dt, spool_tau), 0.0, 1.0);
    const double dry_span = 1.0 - kPhaseBEngineIdleBias;
    const double dry_throttle =
        phase_b_clamp((throttle_state - kPhaseBEngineIdleBias) / dry_span, 0.0, 1.0);
    const double dry_command = kPhaseBMilThrustN * dry_throttle;
    dry_thrust_state =
        phase_b_clamp(phase_b_first_order(dry_thrust_state, dry_command, dt, spool_tau), 0.0,
                      fmax(kPhaseBMilThrustN, dry_command));
    const double ab_command = throttle > kPhaseBEngineAbThreshold
                                  ? phase_b_clamp((throttle - kPhaseBEngineAbThreshold) /
                                                      (1.0 - kPhaseBEngineAbThreshold),
                                                  0.0, 1.0)
                                  : 0.0;
    const double ab_tau =
        ab_command >= ab_state ? kPhaseBEngineAbLightTauS : kPhaseBEngineAbExtinguishTauS;
    ab_state = phase_b_clamp(phase_b_first_order(ab_state, ab_command, dt, ab_tau), 0.0, 1.0);
    const double sigma = fmax(0.01, atmosphere.density / kPhaseBSeaLevelDensityKgM3);
    double ram =
        1.0 + kPhaseBEngineRamRiseGain * fmin(fmax(0.0, mach), kPhaseBEngineRamRiseMachCap);
    if (mach > kPhaseBEngineRamDecayStartMach)
        ram -= kPhaseBEngineRamDecayGain * (mach - kPhaseBEngineRamDecayStartMach);
    ram = fmax(0.6, ram);
    current_thrust = phase_b_canonical(
        fmax(0.0,
             (dry_thrust_state + (kPhaseBAbThrustN - kPhaseBMilThrustN) * ab_state) * sigma * ram),
        0x1p-32);

    double force_x = 0.0;
    double force_y = 0.0;
    double force_z = 0.0;
    double torque_roll = 0.0;
    double torque_pitch = 0.0;
    double torque_yaw = 0.0;
    if (active) {
        const double mass = kPhaseBEmptyMassKg + kPhaseBFuelMassKg + kPhaseBStoresMassKg;
        force_z -= mass * kPhaseBGravityMps2;
        const double yaw_rad = phase_b_deg_to_rad(90.0 - heading);
        const double pitch_rad = phase_b_deg_to_rad(pitch);
        const double nose_x = phase_b_canonical(cos(yaw_rad) * cos(pitch_rad), 1.0e-14);
        const double nose_y = phase_b_canonical(sin(yaw_rad) * cos(pitch_rad), 1.0e-14);
        const double nose_z = phase_b_canonical(sin(pitch_rad), 1.0e-14);
        force_x += phase_b_canonical(current_thrust * nose_x, 0x1p-32);
        force_y += phase_b_canonical(current_thrust * nose_y, 0x1p-32);
        force_z += phase_b_canonical(current_thrust * nose_z, 0x1p-32);

        // Aerodynamic force/moment accumulation is intentionally a separate
        // kernel below. Keeping this launch responsible for control, aero
        // state, propulsion, gravity, and thrust bounds the live range.
        (void)dynamic_pressure;
        (void)alpha;
        (void)beta;
        (void)mach;
        (void)flaps;
        (void)speedbrake;
        (void)air_speed;
        (void)air_vx;
        (void)air_vy;
        (void)air_vz;
        (void)rotation;
        (void)lift_coefficient;
        (void)drag_coefficient;
        (void)stall_progress;
        (void)elevator;
        (void)aileron;
        (void)rudder;
        (void)p;
        (void)q_rate;
        (void)r;
    }

    invalid = invalid || !isfinite(force_x) || !isfinite(force_y) || !isfinite(force_z) ||
              !isfinite(torque_roll) || !isfinite(torque_pitch) || !isfinite(torque_yaw) ||
              !isfinite(x) || !isfinite(y) || !isfinite(z) || !isfinite(vx) || !isfinite(vy) ||
              !isfinite(vz) || !isfinite(heading) || !isfinite(pitch) || !isfinite(roll);
    if (invalid) {
        atomicExch(status, 1U);
        return;
    }
    phase_b_forces[kForceX * world_capacity + world] = force_x;
    phase_b_forces[kForceY * world_capacity + world] = force_y;
    phase_b_forces[kForceZ * world_capacity + world] = force_z;
    phase_b_forces[kTorqueRoll * world_capacity + world] = torque_roll;
    phase_b_forces[kTorquePitch * world_capacity + world] = torque_pitch;
    phase_b_forces[kTorqueYaw * world_capacity + world] = torque_yaw;
}

__global__ void phase_b_aerodynamics_kernel(std::size_t world_capacity, const float *control_floats,
                                            const std::uint8_t *control_flags,
                                            const double *kinematics, double *dynamics,
                                            double *phase_b_forces, std::uint32_t *status) {
    const std::size_t world = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world >= world_capacity || control_flags[2 * world_capacity + world] == 0) return;
    const std::size_t kin = world_capacity;
    const std::size_t dyn = world_capacity;
    const double vx = kinematics[3 * kin + world];
    const double vy = kinematics[4 * kin + world];
    const double vz = kinematics[5 * kin + world];
    const double heading = kinematics[6 * kin + world];
    const double pitch = kinematics[7 * kin + world];
    const double roll = kinematics[8 * kin + world];
    const double p = dynamics[kDynP * dyn + world];
    const double q_rate = dynamics[kDynQ * dyn + world];
    const double r = dynamics[kDynR * dyn + world];
    const double elevator = dynamics[kDynElevatorPos * dyn + world];
    const double aileron = dynamics[kDynAileronPos * dyn + world];
    const double rudder = dynamics[kDynRudderPos * dyn + world];
    const double dynamic_pressure = dynamics[kDynDynamicPressure * dyn + world];
    const double alpha = dynamics[kDynAlpha * dyn + world];
    const double beta = dynamics[kDynBeta * dyn + world];
    const double mach = dynamics[kDynMach * dyn + world];
    const double gear_extension = dynamics[kDynGearExtension * dyn + world];
    const double flaps =
        phase_b_clamp(static_cast<double>(control_floats[world_capacity + world]), 0.0, 1.0);
    const double speedbrake =
        phase_b_clamp(static_cast<double>(control_floats[2 * world_capacity + world]), 0.0, 1.0);
    if (dynamic_pressure < 0.1) {
        dynamics[kDynLiftCoefficient * dyn + world] = 0.0;
        dynamics[kDynDragCoefficient * dyn + world] = 0.0;
        dynamics[kDynStallProgress * dyn + world] = 0.0;
        return;
    }

    const double cl = kPhaseBAeroClAlphaPerDeg * phase_b_lookup(mach, 0) * alpha + flaps * 0.35;
    const double cd0 = kPhaseBAeroCd0Clean + phase_b_lookup(mach, 1) + 0.02 * 0.001 +
                       gear_extension * 0.04 + speedbrake * 0.08 + flaps * 0.02;
    const double cd = cd0 + kPhaseBAeroInducedDragK * phase_b_lookup(mach, 2) * cl * cl;
    const double air_speed = sqrt(vx * vx + vy * vy + vz * vz);
    const double inv_speed = 1.0 / fmax(air_speed, 1.0e-6);
    const double drag_x = -vx * inv_speed;
    const double drag_y = -vy * inv_speed;
    const double drag_z = -vz * inv_speed;
    const PhaseBRotation rotation = phase_b_rotation(heading, pitch, roll);
    double right_x = 0.0;
    double right_y = 0.0;
    double right_z = 0.0;
    phase_b_body_to_world(0.0, 1.0, 0.0, rotation, &right_x, &right_y, &right_z);
    const double cross_x = vy * right_z - vz * right_y;
    const double cross_y = vz * right_x - vx * right_z;
    const double cross_z = vx * right_y - vy * right_x;
    const double cross_mag = sqrt(cross_x * cross_x + cross_y * cross_y + cross_z * cross_z);
    const double lift_x = cross_mag < 1.0e-6 ? 0.0 : cross_x / cross_mag;
    const double lift_y = cross_mag < 1.0e-6 ? 0.0 : cross_y / cross_mag;
    const double lift_z = cross_mag < 1.0e-6 ? 0.0 : cross_z / cross_mag;
    const double lift_mag = dynamic_pressure * kPhaseBReferenceAreaM2 * cl;
    const double drag_mag = dynamic_pressure * kPhaseBReferenceAreaM2 * cd;
    const double aero_force_x = drag_mag * drag_x + lift_mag * lift_x;
    const double aero_force_y = drag_mag * drag_y + lift_mag * lift_y;
    const double aero_force_z = drag_mag * drag_z + lift_mag * lift_z;

    const double v_for_moments = fmax(10.0, air_speed);
    const double p_hat = p * kPhaseBWingSpanM / (2.0 * v_for_moments);
    const double q_hat = q_rate * kPhaseBChordM / (2.0 * v_for_moments);
    const double r_hat = r * kPhaseBWingSpanM / (2.0 * v_for_moments);
    double cm = kPhaseBAeroCmAlphaPerRad * phase_b_lookup(mach, 3) * phase_b_deg_to_rad(alpha) -
                12.0 * q_hat;
    cm += kPhaseBAeroCmDeltaEPerRad *
          phase_b_deg_to_rad(elevator * kPhaseBAeroElevatorMaxDeflectionDeg);
    const double cl_mom = -0.1 * phase_b_deg_to_rad(beta) - 0.45 * p_hat + 0.1 * r_hat +
                          kPhaseBAeroClDeltaAPerRad *
                              phase_b_deg_to_rad(aileron * kPhaseBAeroAileronMaxDeflectionDeg);
    const double cn_mom =
        0.15 * phase_b_deg_to_rad(beta) - 0.25 * r_hat +
        kPhaseBAeroCnDeltaRPerRad * phase_b_deg_to_rad(rudder * kPhaseBAeroRudderMaxDeflectionDeg);
    const double torque_pitch = dynamic_pressure * kPhaseBReferenceAreaM2 * kPhaseBChordM * cm;
    const double torque_roll =
        dynamic_pressure * kPhaseBReferenceAreaM2 * kPhaseBWingSpanM * cl_mom;
    const double torque_yaw = dynamic_pressure * kPhaseBReferenceAreaM2 * kPhaseBWingSpanM * cn_mom;
    if (!isfinite(cl) || !isfinite(cd) || !isfinite(aero_force_x) || !isfinite(aero_force_y) ||
        !isfinite(aero_force_z) || !isfinite(torque_roll) || !isfinite(torque_pitch) ||
        !isfinite(torque_yaw)) {
        atomicExch(status, 1U);
        return;
    }
    dynamics[kDynLiftCoefficient * dyn + world] = cl;
    dynamics[kDynDragCoefficient * dyn + world] = cd;
    dynamics[kDynStallProgress * dyn + world] = 0.0;
    phase_b_forces[kForceX * world_capacity + world] += aero_force_x;
    phase_b_forces[kForceY * world_capacity + world] += aero_force_y;
    phase_b_forces[kForceZ * world_capacity + world] += aero_force_z;
    phase_b_forces[kTorqueRoll * world_capacity + world] = torque_roll;
    phase_b_forces[kTorquePitch * world_capacity + world] = torque_pitch;
    phase_b_forces[kTorqueYaw * world_capacity + world] = torque_yaw;
}

__global__ void phase_b_integrate_kernel(std::size_t world_capacity, const double *time_steps,
                                         double *kinematics, double *dynamics,
                                         const double *phase_b_forces, std::uint32_t *status) {
    const std::size_t world = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world >= world_capacity) return;
    const double dt = static_cast<double>(static_cast<float>(time_steps[world]));
    if (!isfinite(dt) || dt < kPhaseBMinTimeStepS || dt > kPhaseBMaxTimeStepS) {
        atomicExch(status, 1U);
        return;
    }
    const std::size_t kin = world_capacity;
    const std::size_t dyn = world_capacity;
    double &x = kinematics[0 * kin + world];
    double &y = kinematics[1 * kin + world];
    double &z = kinematics[2 * kin + world];
    double &vx = kinematics[3 * kin + world];
    double &vy = kinematics[4 * kin + world];
    double &vz = kinematics[5 * kin + world];
    double &heading = kinematics[6 * kin + world];
    double &pitch = kinematics[7 * kin + world];
    double &roll = kinematics[8 * kin + world];
    double p = dynamics[kDynP * dyn + world];
    double q_rate = dynamics[kDynQ * dyn + world];
    double r = dynamics[kDynR * dyn + world];
    const double torque_roll = phase_b_forces[kTorqueRoll * world_capacity + world];
    const double torque_pitch = phase_b_forces[kTorquePitch * world_capacity + world];
    const double torque_yaw = phase_b_forces[kTorqueYaw * world_capacity + world];
    constexpr double max_rate = 6.0;
    constexpr double max_accel = 1.0e4;
    p += phase_b_clamp(torque_roll / kPhaseBInertiaRollKgM2, -max_accel, max_accel) * dt;
    q_rate += phase_b_clamp(torque_pitch / kPhaseBInertiaPitchKgM2, -max_accel, max_accel) * dt;
    r += phase_b_clamp(torque_yaw / kPhaseBInertiaYawKgM2, -max_accel, max_accel) * dt;
    p = phase_b_clamp(p, -max_rate, max_rate);
    q_rate = phase_b_clamp(q_rate, -max_rate, max_rate);
    r = phase_b_clamp(r, -max_rate, max_rate);
    const double phi = phase_b_deg_to_rad(roll);
    double ctheta = cos(phase_b_deg_to_rad(pitch));
    const double stheta = sin(phase_b_deg_to_rad(pitch));
    if (fabs(ctheta) < cos(phase_b_deg_to_rad(85.0)))
        ctheta = copysign(cos(phase_b_deg_to_rad(85.0)), ctheta);
    const double sphi = sin(phi);
    const double cphi = cos(phi);
    const double tan_theta = stheta / ctheta;
    const double sec_theta = 1.0 / ctheta;
    const double dphi = p + (q_rate * sphi + r * cphi) * tan_theta;
    const double dtheta = q_rate * cphi - r * sphi;
    const double dpsi = (q_rate * sphi + r * cphi) * sec_theta;
    roll += phase_b_rad_to_deg(dphi) * dt;
    pitch += phase_b_rad_to_deg(dtheta) * dt;
    heading -= phase_b_rad_to_deg(dpsi) * dt;
    roll = fmod(roll + 180.0, 360.0);
    if (roll < 0.0) roll += 360.0;
    roll -= 180.0;
    pitch = phase_b_clamp(pitch, -89.0, 89.0);
    heading = phase_b_wrap_360(heading);

    const double mass = kPhaseBEmptyMassKg + kPhaseBFuelMassKg + kPhaseBStoresMassKg;
    const double ax = phase_b_forces[kForceX * world_capacity + world] / mass;
    const double ay = phase_b_forces[kForceY * world_capacity + world] / mass;
    const double az = phase_b_forces[kForceZ * world_capacity + world] / mass;
    const double vx_half = vx + ax * dt * 0.5;
    const double vy_half = vy + ay * dt * 0.5;
    const double vz_half = vz + az * dt * 0.5;
    x += vx_half * dt;
    y += vy_half * dt;
    z += vz_half * dt;
    vx = vx_half + ax * dt * 0.5;
    vy = vy_half + ay * dt * 0.5;
    vz = vz_half + az * dt * 0.5;
    if (z < -5.0) {
        z = -5.0;
        if (vz < 0.0) vz = 0.0;
    }
    if (!isfinite(x) || !isfinite(y) || !isfinite(z) || !isfinite(vx) || !isfinite(vy) ||
        !isfinite(vz) || !isfinite(heading) || !isfinite(pitch) || !isfinite(roll)) {
        atomicExch(status, 1U);
        return;
    }
    dynamics[kDynP * dyn + world] = p;
    dynamics[kDynQ * dyn + world] = q_rate;
    dynamics[kDynR * dyn + world] = r;
}

__global__ void apply_barrier_kernel(std::size_t world_capacity, CudaResidentBarrierCode barrier,
                                     double *simulation_times, const double *time_steps,
                                     std::uint64_t *clock_ticks, std::uint64_t *global_versions,
                                     std::uint64_t *barrier_sequences, std::uint8_t *barrier_codes,
                                     std::uint64_t *shard_versions, std::uint32_t *status) {
    const std::size_t world_index = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world_index >= world_capacity) {
        return;
    }

    const bool mutates_snapshot = barrier != CudaResidentBarrierCode::stage_publish;
    bool overflow = increment_would_overflow(barrier_sequences[world_index]);
    if (mutates_snapshot) {
        overflow = overflow || increment_would_overflow(global_versions[world_index]);
    }
    if (barrier == CudaResidentBarrierCode::window_commit) {
        overflow = overflow || increment_would_overflow(clock_ticks[world_index]) ||
                   !isfinite(simulation_times[world_index] + time_steps[world_index]);
    }

    const std::size_t identity_index =
        static_cast<std::size_t>(CudaResidentShard::identity) * world_capacity + world_index;
    const std::size_t controls_index =
        static_cast<std::size_t>(CudaResidentShard::pilot_flight_controls) * world_capacity +
        world_index;
    const std::size_t clock_index =
        static_cast<std::size_t>(CudaResidentShard::clock) * world_capacity + world_index;
    const std::size_t snapshot_index =
        static_cast<std::size_t>(CudaResidentShard::snapshot) * world_capacity + world_index;
    const std::size_t kinematics_index =
        static_cast<std::size_t>(CudaResidentShard::kinematics) * world_capacity + world_index;
    const std::size_t dynamics_index =
        static_cast<std::size_t>(CudaResidentShard::dynamics) * world_capacity + world_index;
    const std::size_t episode_index =
        static_cast<std::size_t>(CudaResidentShard::episode) * world_capacity + world_index;
    if (barrier == CudaResidentBarrierCode::input_injection) {
        overflow = overflow || increment_would_overflow(shard_versions[identity_index]) ||
                   increment_would_overflow(shard_versions[controls_index]);
    } else if (barrier == CudaResidentBarrierCode::window_commit) {
        overflow = overflow || increment_would_overflow(shard_versions[identity_index]) ||
                   increment_would_overflow(shard_versions[clock_index]) ||
                   increment_would_overflow(shard_versions[snapshot_index]) ||
                   increment_would_overflow(shard_versions[kinematics_index]) ||
                   increment_would_overflow(shard_versions[dynamics_index]) ||
                   increment_would_overflow(shard_versions[episode_index]);
    }
    if (overflow) {
        atomicExch(status, 1U);
        return;
    }

    ++barrier_sequences[world_index];
    barrier_codes[world_index] = static_cast<std::uint8_t>(barrier);
    if (!mutates_snapshot) {
        return;
    }
    ++global_versions[world_index];
    if (barrier == CudaResidentBarrierCode::input_injection) {
        ++shard_versions[identity_index];
        ++shard_versions[controls_index];
        return;
    }

    ++clock_ticks[world_index];
    simulation_times[world_index] += time_steps[world_index];
    ++shard_versions[identity_index];
    ++shard_versions[clock_index];
    ++shard_versions[snapshot_index];
    ++shard_versions[kinematics_index];
    ++shard_versions[dynamics_index];
    ++shard_versions[episode_index];
}

} // namespace

struct CudaWorldStoreDeviceAllocation {
    std::uint8_t *storage = nullptr;
    std::size_t storage_bytes = 0;
    CudaWorldLifecycleRecord *records = nullptr;
    std::uint8_t *state_slots[2] = {nullptr, nullptr};
    std::uint32_t *barrier_status = nullptr;
    CudaWorldStateSlotLayout state_layout{};
    std::size_t world_capacity = 0;
    std::uint8_t active_lifecycle_slot = 0;
    std::uint8_t active_state_slot = 0;
};

namespace {

bool finalize_staged_barrier(CudaWorldStoreDeviceAllocation *allocation, std::uint8_t next_slot,
                             CudaResidentBarrierCode barrier,
                             CudaWorldStoreDeviceFaultInjection *faults, std::string *error) {
    if (allocation == nullptr) {
        if (error != nullptr) {
            *error = "CUDA world store barrier requires an allocation";
        }
        return false;
    }
    if (allocation->world_capacity == 0) {
        allocation->active_state_slot = next_slot;
        if (error != nullptr) {
            error->clear();
        }
        return true;
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_barrier_commit)) {
        if (error != nullptr) {
            *error = "injected CUDA world store barrier commit failure";
        }
        return false;
    }

    cudaError_t status = cudaMemset(allocation->barrier_status, 0, sizeof(std::uint32_t));
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("clear resident barrier status", status);
        }
        return false;
    }
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    std::uint8_t *slot = allocation->state_slots[next_slot];
    apply_barrier_kernel<<<blocks, threads>>>(
        allocation->world_capacity, barrier,
        device_field<double>(slot, allocation->state_layout.simulation_times),
        device_field<double>(slot, allocation->state_layout.time_steps),
        device_field<std::uint64_t>(slot, allocation->state_layout.clock_ticks),
        device_field<std::uint64_t>(slot, allocation->state_layout.global_versions),
        device_field<std::uint64_t>(slot, allocation->state_layout.barrier_sequences),
        device_field<std::uint8_t>(slot, allocation->state_layout.barrier_codes),
        device_field<std::uint64_t>(slot, allocation->state_layout.shard_versions),
        allocation->barrier_status);
    status = cudaGetLastError();
    if (status == cudaSuccess) {
        status = cudaDeviceSynchronize();
    }
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("commit resident barrier", status);
        }
        return false;
    }
    std::uint32_t barrier_status = 0;
    status = cudaMemcpy(&barrier_status, allocation->barrier_status, sizeof(barrier_status),
                        cudaMemcpyDeviceToHost);
    if (status != cudaSuccess || barrier_status != 0) {
        if (error != nullptr) {
            *error = status == cudaSuccess
                         ? "CUDA world store barrier version/clock overflow"
                         : cuda_error_message("read resident barrier status", status);
        }
        return false;
    }

    allocation->active_state_slot = next_slot;
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

bool commit_barrier(CudaWorldStoreDeviceAllocation *allocation, CudaResidentBarrierCode barrier,
                    CudaWorldStoreDeviceFaultInjection *faults, std::string *error) {
    if (allocation == nullptr) {
        if (error != nullptr) {
            *error = "CUDA world store barrier requires an allocation";
        }
        return false;
    }
    const std::uint8_t next_slot = allocation->active_state_slot ^ 1U;
    if (allocation->world_capacity == 0) {
        return finalize_staged_barrier(allocation, next_slot, barrier, faults, error);
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_state_transfer)) {
        if (error != nullptr) {
            *error = "injected CUDA world store state transfer failure";
        }
        return false;
    }
    const cudaError_t status = cudaMemcpy(
        allocation->state_slots[next_slot], allocation->state_slots[allocation->active_state_slot],
        allocation->state_layout.slot_bytes, cudaMemcpyDeviceToDevice);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("copy resident state to inactive slot", status);
        }
        return false;
    }
    return finalize_staged_barrier(allocation, next_slot, barrier, faults, error);
}

bool commit_phase_a_stage(CudaWorldStoreDeviceAllocation *allocation,
                          CudaWorldStoreDeviceFaultInjection *faults, std::string *error) {
    if (allocation == nullptr) {
        if (error != nullptr) {
            *error = "CUDA Phase A stage requires an allocation";
        }
        return false;
    }
    const std::uint8_t next_slot = allocation->active_state_slot ^ 1U;
    if (allocation->world_capacity == 0) {
        return finalize_staged_barrier(allocation, next_slot,
                                       CudaResidentBarrierCode::stage_publish, faults, error);
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_state_transfer)) {
        if (error != nullptr) {
            *error = "injected CUDA Phase A state transfer failure";
        }
        return false;
    }

    cudaError_t status = cudaMemcpy(allocation->state_slots[next_slot],
                                    allocation->state_slots[allocation->active_state_slot],
                                    allocation->state_layout.slot_bytes, cudaMemcpyDeviceToDevice);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("copy state for Phase A preparation", status);
        }
        return false;
    }
    status = cudaMemset(allocation->barrier_status, 0, sizeof(std::uint32_t));
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("clear Phase A status", status);
        }
        return false;
    }
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    std::uint8_t *slot = allocation->state_slots[next_slot];
    prepare_phase_a_controls_kernel<<<blocks, threads>>>(
        allocation->world_capacity, device_field<double>(slot, allocation->state_layout.time_steps),
        device_field<double>(slot, allocation->state_layout.control_doubles),
        device_field<std::uint8_t>(slot, allocation->state_layout.control_flags),
        device_field<double>(slot, allocation->state_layout.prepared_doubles),
        device_field<std::uint8_t>(slot, allocation->state_layout.prepared_flags),
        device_field<std::uint64_t>(slot, allocation->state_layout.phase_versions),
        allocation->barrier_status);
    status = cudaGetLastError();
    if (status == cudaSuccess) {
        status = cudaDeviceSynchronize();
    }
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("run Phase A control preparation", status);
        }
        return false;
    }
    std::uint32_t phase_status = 0;
    status = cudaMemcpy(&phase_status, allocation->barrier_status, sizeof(phase_status),
                        cudaMemcpyDeviceToHost);
    if (status != cudaSuccess || phase_status != 0) {
        if (error != nullptr) {
            *error = status == cudaSuccess
                         ? "CUDA Phase A control preparation overflow or non-finite state"
                         : cuda_error_message("read Phase A status", status);
        }
        return false;
    }
    return finalize_staged_barrier(allocation, next_slot, CudaResidentBarrierCode::stage_publish,
                                   faults, error);
}

bool commit_phase_b_window(CudaWorldStoreDeviceAllocation *allocation,
                           CudaWorldStoreDeviceFaultInjection *faults, std::string *error) {
    if (allocation == nullptr) {
        if (error != nullptr) *error = "CUDA Phase B window requires an allocation";
        return false;
    }
    const std::uint8_t next_slot = allocation->active_state_slot ^ 1U;
    if (allocation->world_capacity == 0) {
        return finalize_staged_barrier(allocation, next_slot,
                                       CudaResidentBarrierCode::window_commit, faults, error);
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_state_transfer)) {
        if (error != nullptr) *error = "injected CUDA Phase B state transfer failure";
        return false;
    }
    cudaError_t status = cudaMemcpy(allocation->state_slots[next_slot],
                                    allocation->state_slots[allocation->active_state_slot],
                                    allocation->state_layout.slot_bytes, cudaMemcpyDeviceToDevice);
    if (status != cudaSuccess) {
        if (error != nullptr)
            *error = cuda_error_message("copy state for Phase B dynamics", status);
        return false;
    }
    status = cudaMemset(allocation->barrier_status, 0, sizeof(std::uint32_t));
    if (status != cudaSuccess) {
        if (error != nullptr) *error = cuda_error_message("clear Phase B status", status);
        return false;
    }
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    std::uint8_t *slot = allocation->state_slots[next_slot];
    phase_b_forces_kernel<<<blocks, threads>>>(
        allocation->world_capacity, device_field<double>(slot, allocation->state_layout.time_steps),
        device_field<double>(slot, allocation->state_layout.control_doubles),
        device_field<float>(slot, allocation->state_layout.control_floats),
        device_field<std::uint8_t>(slot, allocation->state_layout.control_flags),
        device_field<double>(slot, allocation->state_layout.prepared_doubles),
        device_field<std::uint8_t>(slot, allocation->state_layout.prepared_flags),
        device_field<double>(slot, allocation->state_layout.kinematics),
        device_field<double>(slot, allocation->state_layout.dynamics),
        device_field<double>(slot, allocation->state_layout.phase_b_forces),
        allocation->barrier_status);
    status = cudaGetLastError();
    if (status == cudaSuccess) {
        phase_b_aerodynamics_kernel<<<blocks, threads>>>(
            allocation->world_capacity,
            device_field<float>(slot, allocation->state_layout.control_floats),
            device_field<std::uint8_t>(slot, allocation->state_layout.control_flags),
            device_field<double>(slot, allocation->state_layout.kinematics),
            device_field<double>(slot, allocation->state_layout.dynamics),
            device_field<double>(slot, allocation->state_layout.phase_b_forces),
            allocation->barrier_status);
        status = cudaGetLastError();
    }
    if (status == cudaSuccess) {
        phase_b_integrate_kernel<<<blocks, threads>>>(
            allocation->world_capacity,
            device_field<double>(slot, allocation->state_layout.time_steps),
            device_field<double>(slot, allocation->state_layout.kinematics),
            device_field<double>(slot, allocation->state_layout.dynamics),
            device_field<double>(slot, allocation->state_layout.phase_b_forces),
            allocation->barrier_status);
        status = cudaGetLastError();
    }
    // The three Phase-B launches form one device graph. This is the only host
    // synchronization before the declared window barrier.
    if (status == cudaSuccess) status = cudaDeviceSynchronize();
    if (status != cudaSuccess) {
        if (error != nullptr) *error = cuda_error_message("run Phase B airframe dynamics", status);
        return false;
    }
    std::uint32_t phase_status = 0;
    status = cudaMemcpy(&phase_status, allocation->barrier_status, sizeof(phase_status),
                        cudaMemcpyDeviceToHost);
    if (status != cudaSuccess || phase_status != 0) {
        if (error != nullptr) {
            *error = status == cudaSuccess
                         ? "CUDA Phase B dynamics produced overflow or non-finite state"
                         : cuda_error_message("read Phase B status", status);
        }
        return false;
    }
    return finalize_staged_barrier(allocation, next_slot, CudaResidentBarrierCode::window_commit,
                                   faults, error);
}

} // namespace

bool cuda_world_store_runtime_available(std::string *error) {
    int device_count = 0;
    const cudaError_t status = cudaGetDeviceCount(&device_count);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("cudaGetDeviceCount", status);
        }
        return false;
    }
    if (device_count <= 0) {
        if (error != nullptr) {
            *error = "cudaGetDeviceCount returned no CUDA devices";
        }
        return false;
    }
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

CudaWorldStoreDeviceAllocationResult
allocate_cuda_world_store_metadata(std::size_t world_capacity,
                                   CudaWorldStoreDeviceFaultInjection *faults) {
    CudaWorldStoreDeviceAllocationResult result{};
    std::unique_ptr<CudaWorldStoreDeviceAllocation> allocation(
        new (std::nothrow) CudaWorldStoreDeviceAllocation{});
    if (!allocation) {
        result.error = "failed to allocate CUDA world store host owner";
        return result;
    }
    allocation->world_capacity = world_capacity;

    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_allocation)) {
        result.error = "injected CUDA world store allocation failure";
        return result;
    }
    if (!build_state_layout(world_capacity, &allocation->state_layout)) {
        result.error = "CUDA world store state layout size overflow";
        return result;
    }
    if (world_capacity == 0) {
        result.allocation = allocation.release();
        return result;
    }

    std::size_t lifecycle_count = 0;
    std::size_t lifecycle_bytes = 0;
    std::size_t state_base = 0;
    std::size_t state_bytes = 0;
    std::size_t status_offset = 0;
    std::size_t total_bytes = 0;
    if (!checked_product(world_capacity, 2, &lifecycle_count) ||
        !checked_product(lifecycle_count, sizeof(CudaWorldLifecycleRecord), &lifecycle_bytes) ||
        !checked_align(lifecycle_bytes, alignof(HostStateBlock), &state_base) ||
        !checked_product(allocation->state_layout.slot_bytes, 2, &state_bytes) ||
        !checked_add(state_base, state_bytes, &status_offset) ||
        !checked_align(status_offset, alignof(std::uint32_t), &status_offset) ||
        !checked_add(status_offset, sizeof(std::uint32_t), &total_bytes)) {
        result.error = "CUDA world store allocation byte total overflow";
        return result;
    }

    const cudaError_t status =
        cudaMalloc(reinterpret_cast<void **>(&allocation->storage), total_bytes);
    if (status != cudaSuccess) {
        result.error = cuda_error_message("cudaMalloc(resident_world_store)", status);
        return result;
    }
    allocation->storage_bytes = total_bytes;
    allocation->records = reinterpret_cast<CudaWorldLifecycleRecord *>(allocation->storage);
    allocation->state_slots[0] = allocation->storage + state_base;
    allocation->state_slots[1] = allocation->state_slots[0] + allocation->state_layout.slot_bytes;
    allocation->barrier_status =
        reinterpret_cast<std::uint32_t *>(allocation->storage + status_offset);
    result.device_bytes = total_bytes;

    // No potentially-throwing operation follows the successful cudaMalloc;
    // ownership transfers directly into the opaque result.
    result.allocation = allocation.release();
    return result;
}

bool reset_cuda_world_store_metadata(CudaWorldStoreDeviceAllocation *allocation,
                                     const std::uint32_t *seeds, std::size_t world_capacity,
                                     std::uint64_t reset_generation,
                                     CudaWorldStoreDeviceFaultInjection *faults,
                                     std::string *error) {
    if (allocation == nullptr || allocation->world_capacity != world_capacity) {
        if (error != nullptr) {
            *error = "CUDA world store reset allocation/capacity mismatch";
        }
        return false;
    }
    if (world_capacity == 0) {
        allocation->active_lifecycle_slot ^= 1U;
        allocation->active_state_slot ^= 1U;
        if (error != nullptr) {
            error->clear();
        }
        return true;
    }

    std::vector<CudaWorldLifecycleRecord> next_records;
    try {
        next_records.resize(world_capacity);
    } catch (const std::bad_alloc &) {
        if (error != nullptr) {
            *error = "failed to allocate CUDA world store reset staging metadata";
        }
        return false;
    }
    for (std::size_t index = 0; index < world_capacity; ++index) {
        next_records[index].reset_generation = reset_generation;
        next_records[index].seed = seeds == nullptr ? 0 : seeds[index];
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_reset_copy)) {
        if (error != nullptr) {
            *error = "injected CUDA world store reset metadata copy failure";
        }
        return false;
    }

    const std::uint8_t next_lifecycle_slot = allocation->active_lifecycle_slot ^ 1U;
    const std::uint8_t next_state_slot = allocation->active_state_slot ^ 1U;
    CudaWorldLifecycleRecord *destination =
        allocation->records + (static_cast<std::size_t>(next_lifecycle_slot) * world_capacity);
    cudaError_t status =
        cudaMemcpy(destination, next_records.data(),
                   world_capacity * sizeof(CudaWorldLifecycleRecord), cudaMemcpyHostToDevice);
    if (status == cudaSuccess) {
        status = cudaMemset(allocation->state_slots[next_state_slot], 0,
                            allocation->state_layout.slot_bytes);
    }
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("reset resident world state", status);
        }
        return false;
    }

    allocation->active_lifecycle_slot = next_lifecycle_slot;
    allocation->active_state_slot = next_state_slot;
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

bool read_cuda_world_store_metadata(const CudaWorldStoreDeviceAllocation *allocation,
                                    std::size_t world_capacity,
                                    CudaWorldStoreDeviceSnapshot *snapshot, std::string *error) {
    if (allocation == nullptr || allocation->world_capacity != world_capacity ||
        snapshot == nullptr) {
        if (error != nullptr) {
            *error = "CUDA world store readback allocation/capacity mismatch";
        }
        return false;
    }

    std::vector<CudaWorldLifecycleRecord> records(world_capacity);
    if (world_capacity != 0) {
        const CudaWorldLifecycleRecord *source =
            allocation->records +
            (static_cast<std::size_t>(allocation->active_lifecycle_slot) * world_capacity);
        const cudaError_t status =
            cudaMemcpy(records.data(), source, world_capacity * sizeof(CudaWorldLifecycleRecord),
                       cudaMemcpyDeviceToHost);
        if (status != cudaSuccess) {
            if (error != nullptr) {
                *error = cuda_error_message("read lifecycle metadata", status);
            }
            return false;
        }
    }

    CudaWorldStoreDeviceSnapshot next_snapshot;
    next_snapshot.seeds.reserve(world_capacity);
    next_snapshot.reset_generations.reserve(world_capacity);
    for (const CudaWorldLifecycleRecord &record : records) {
        next_snapshot.seeds.push_back(record.seed);
        next_snapshot.reset_generations.push_back(record.reset_generation);
    }
    *snapshot = std::move(next_snapshot);
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

bool setup_cuda_world_store_fixed_air_fixture(CudaWorldStoreDeviceAllocation *allocation,
                                              const std::vector<CudaFixedAirWorldSetup> &setups,
                                              CudaWorldStoreDeviceFaultInjection *faults,
                                              std::string *error) {
    if (allocation == nullptr || setups.size() != allocation->world_capacity) {
        if (error != nullptr) {
            *error = "CUDA fixed-air setup count must equal world capacity";
        }
        return false;
    }
    for (std::size_t index = 0; index < setups.size(); ++index) {
        if (setups[index].world_index != index) {
            if (error != nullptr) {
                *error = "CUDA fixed-air setup worlds must be canonical and contiguous";
            }
            return false;
        }
    }
    if (allocation->world_capacity == 0) {
        allocation->active_state_slot ^= 1U;
        if (error != nullptr) {
            error->clear();
        }
        return true;
    }

    std::vector<HostStateBlock> host_slot = make_host_slot(allocation->state_layout.slot_bytes);
    auto *setup_complete =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.setup_complete);
    auto *entity_ids = host_field<std::uint64_t>(host_slot, allocation->state_layout.entity_ids);
    auto *entity_generations =
        host_field<std::uint32_t>(host_slot, allocation->state_layout.entity_generations);
    auto *time_steps = host_field<double>(host_slot, allocation->state_layout.time_steps);
    auto *kinematics = host_field<double>(host_slot, allocation->state_layout.kinematics);
    auto *dynamics = host_field<double>(host_slot, allocation->state_layout.dynamics);
    auto *phase_b_forces = host_field<double>(host_slot, allocation->state_layout.phase_b_forces);
    auto *global_versions =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.global_versions);
    auto *barrier_sequences =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.barrier_sequences);
    auto *barrier_codes =
        host_field<std::uint8_t>(host_slot, allocation->state_layout.barrier_codes);
    auto *shard_versions =
        host_field<std::uint64_t>(host_slot, allocation->state_layout.shard_versions);

    for (std::size_t world = 0; world < setups.size(); ++world) {
        const CudaFixedAirWorldSetup &setup = setups[world];
        setup_complete[world] = 1;
        entity_ids[world] = setup.entity_id;
        entity_generations[world] = setup.entity_generation;
        time_steps[world] = setup.time_step_s;
        const double values[kKinematicsFieldCount] = {
            setup.kinematics.x,       setup.kinematics.y,     setup.kinematics.z,
            setup.kinematics.vx,      setup.kinematics.vy,    setup.kinematics.vz,
            setup.kinematics.heading, setup.kinematics.pitch, setup.kinematics.roll,
        };
        for (std::size_t field = 0; field < kKinematicsFieldCount; ++field) {
            kinematics[field * setups.size() + world] = values[field];
        }
        for (std::size_t field = 0; field < kDynamicsDoubleFieldCount; ++field) {
            dynamics[field * setups.size() + world] = 0.0;
        }
        dynamics[kDynGearExtension * setups.size() + world] = 1.0;
        for (std::size_t field = 0; field < kPhaseBForceFieldCount; ++field) {
            phase_b_forces[field * setups.size() + world] = 0.0;
        }
        global_versions[world] = 1;
        barrier_sequences[world] = 1;
        barrier_codes[world] = static_cast<std::uint8_t>(CudaResidentBarrierCode::input_injection);
        for (CudaResidentShard shard :
             {CudaResidentShard::identity, CudaResidentShard::pilot_flight_controls,
              CudaResidentShard::clock, CudaResidentShard::snapshot, CudaResidentShard::kinematics,
              CudaResidentShard::dynamics, CudaResidentShard::episode}) {
            shard_versions[static_cast<std::size_t>(shard) * setups.size() + world] = 1;
        }
    }

    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_state_transfer)) {
        if (error != nullptr) {
            *error = "injected CUDA fixed-air setup transfer failure";
        }
        return false;
    }
    const std::uint8_t next_slot = allocation->active_state_slot ^ 1U;
    const cudaError_t status =
        cudaMemcpy(allocation->state_slots[next_slot], host_slot.data(),
                   allocation->state_layout.slot_bytes, cudaMemcpyHostToDevice);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("upload fixed-air setup state", status);
        }
        return false;
    }
    allocation->active_state_slot = next_slot;
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

bool inject_cuda_world_store_flight_controls(
    CudaWorldStoreDeviceAllocation *allocation,
    const std::vector<CudaWorldFlightControlAssignment> &assignments,
    CudaWorldStoreDeviceFaultInjection *faults, std::string *error) {
    if (allocation == nullptr || assignments.size() != allocation->world_capacity) {
        if (error != nullptr) {
            *error = "CUDA flight-control assignment count must equal world capacity";
        }
        return false;
    }
    for (std::size_t index = 0; index < assignments.size(); ++index) {
        if (assignments[index].world_index != index) {
            if (error != nullptr) {
                *error = "CUDA flight-control worlds must be canonical and contiguous";
            }
            return false;
        }
    }
    if (allocation->world_capacity == 0) {
        return commit_barrier(allocation, CudaResidentBarrierCode::input_injection, faults, error);
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_state_transfer)) {
        if (error != nullptr) {
            *error = "injected CUDA flight-control state transfer failure";
        }
        return false;
    }

    const std::uint8_t next_slot = allocation->active_state_slot ^ 1U;
    cudaError_t status = cudaMemcpy(allocation->state_slots[next_slot],
                                    allocation->state_slots[allocation->active_state_slot],
                                    allocation->state_layout.slot_bytes, cudaMemcpyDeviceToDevice);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("copy state for flight-control injection", status);
        }
        return false;
    }

    std::vector<double> control_doubles(kControlDoubleFieldCount * assignments.size());
    std::vector<float> control_floats(kControlFloatFieldCount * assignments.size());
    std::vector<std::uint8_t> control_flags(kControlFlagFieldCount * assignments.size());
    for (std::size_t world = 0; world < assignments.size(); ++world) {
        const CudaWorldFlightControls &controls = assignments[world].controls;
        const double double_values[kControlDoubleFieldCount] = {
            controls.stick_pitch, controls.stick_roll, controls.rudder,
            controls.throttle,    controls.brake,
        };
        const float float_values[kControlFloatFieldCount] = {
            controls.gear_handle,
            controls.flaps,
            controls.speedbrake,
        };
        const std::uint8_t flag_values[kControlFlagFieldCount] = {
            static_cast<std::uint8_t>(controls.brake_left),
            static_cast<std::uint8_t>(controls.brake_right),
            static_cast<std::uint8_t>(controls.active),
        };
        for (std::size_t field = 0; field < kControlDoubleFieldCount; ++field) {
            control_doubles[field * assignments.size() + world] = double_values[field];
        }
        for (std::size_t field = 0; field < kControlFloatFieldCount; ++field) {
            control_floats[field * assignments.size() + world] = float_values[field];
        }
        for (std::size_t field = 0; field < kControlFlagFieldCount; ++field) {
            control_flags[field * assignments.size() + world] = flag_values[field];
        }
    }

    std::uint8_t *slot = allocation->state_slots[next_slot];
    status = cudaMemcpy(device_field<double>(slot, allocation->state_layout.control_doubles),
                        control_doubles.data(), control_doubles.size() * sizeof(double),
                        cudaMemcpyHostToDevice);
    if (status == cudaSuccess) {
        status = cudaMemcpy(device_field<float>(slot, allocation->state_layout.control_floats),
                            control_floats.data(), control_floats.size() * sizeof(float),
                            cudaMemcpyHostToDevice);
    }
    if (status == cudaSuccess) {
        status =
            cudaMemcpy(device_field<std::uint8_t>(slot, allocation->state_layout.control_flags),
                       control_flags.data(), control_flags.size() * sizeof(std::uint8_t),
                       cudaMemcpyHostToDevice);
    }
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("upload flight-control shard", status);
        }
        return false;
    }

    return finalize_staged_barrier(allocation, next_slot, CudaResidentBarrierCode::input_injection,
                                   faults, error);
}

bool publish_cuda_world_store_stage(CudaWorldStoreDeviceAllocation *allocation,
                                    CudaWorldStoreDeviceFaultInjection *faults,
                                    std::string *error) {
    return commit_phase_a_stage(allocation, faults, error);
}

bool commit_cuda_world_store_window(CudaWorldStoreDeviceAllocation *allocation,
                                    CudaWorldStoreDeviceFaultInjection *faults,
                                    std::string *error) {
    return commit_phase_b_window(allocation, faults, error);
}

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

bool query_cuda_world_store_barrier_kernel_resources(CudaBarrierKernelResources *resources,
                                                     std::string *error) {
    if (resources == nullptr) {
        if (error != nullptr) {
            *error = "CUDA barrier kernel resource query requires an output";
        }
        return false;
    }
    cudaFuncAttributes attributes{};
    cudaError_t status = cudaFuncGetAttributes(&attributes, apply_barrier_kernel);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("cudaFuncGetAttributes(apply_barrier_kernel)", status);
        }
        return false;
    }
    constexpr int threads_per_block = 128;
    int active_blocks = 0;
    status = cudaOccupancyMaxActiveBlocksPerMultiprocessor(&active_blocks, apply_barrier_kernel,
                                                           threads_per_block, 0);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("cudaOccupancyMaxActiveBlocksPerMultiprocessor", status);
        }
        return false;
    }
    int device = 0;
    cudaDeviceProp properties{};
    status = cudaGetDevice(&device);
    if (status == cudaSuccess) {
        status = cudaGetDeviceProperties(&properties, device);
    }
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("query CUDA device occupancy properties", status);
        }
        return false;
    }
    if (properties.warpSize <= 0 || properties.maxThreadsPerMultiProcessor <= 0) {
        if (error != nullptr) {
            *error = "CUDA device returned invalid occupancy properties";
        }
        return false;
    }

    *resources = {
        .registers_per_thread = attributes.numRegs,
        .local_bytes_per_thread = attributes.localSizeBytes,
        .static_shared_bytes = attributes.sharedSizeBytes,
        .threads_per_block = threads_per_block,
        .active_blocks_per_multiprocessor = active_blocks,
        .active_warps_per_multiprocessor =
            active_blocks * (threads_per_block / properties.warpSize),
        .theoretical_occupancy = static_cast<double>(active_blocks * threads_per_block) /
                                 static_cast<double>(properties.maxThreadsPerMultiProcessor),
    };
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

bool query_cuda_world_store_phase_a_kernel_resources(CudaBarrierKernelResources *resources,
                                                     std::string *error) {
    if (resources == nullptr) {
        if (error != nullptr) {
            *error = "CUDA Phase A kernel resource query requires an output";
        }
        return false;
    }
    cudaFuncAttributes attributes{};
    cudaError_t status = cudaFuncGetAttributes(&attributes, prepare_phase_a_controls_kernel);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("cudaFuncGetAttributes(prepare_phase_a_controls_kernel)",
                                        status);
        }
        return false;
    }
    constexpr int threads_per_block = 128;
    int active_blocks = 0;
    status = cudaOccupancyMaxActiveBlocksPerMultiprocessor(
        &active_blocks, prepare_phase_a_controls_kernel, threads_per_block, 0);
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("cudaOccupancyMaxActiveBlocksPerMultiprocessor(Phase A)",
                                        status);
        }
        return false;
    }
    int device = 0;
    cudaDeviceProp properties{};
    status = cudaGetDevice(&device);
    if (status == cudaSuccess) {
        status = cudaGetDeviceProperties(&properties, device);
    }
    if (status != cudaSuccess) {
        if (error != nullptr) {
            *error = cuda_error_message("query CUDA Phase A occupancy properties", status);
        }
        return false;
    }
    if (properties.warpSize <= 0 || properties.maxThreadsPerMultiProcessor <= 0) {
        if (error != nullptr) {
            *error = "CUDA device returned invalid Phase A occupancy properties";
        }
        return false;
    }

    *resources = {
        .registers_per_thread = attributes.numRegs,
        .local_bytes_per_thread = attributes.localSizeBytes,
        .static_shared_bytes = attributes.sharedSizeBytes,
        .threads_per_block = threads_per_block,
        .active_blocks_per_multiprocessor = active_blocks,
        .active_warps_per_multiprocessor =
            active_blocks * (threads_per_block / properties.warpSize),
        .theoretical_occupancy = static_cast<double>(active_blocks * threads_per_block) /
                                 static_cast<double>(properties.maxThreadsPerMultiProcessor),
    };
    if (error != nullptr) {
        error->clear();
    }
    return true;
}

template <typename Kernel>
bool query_phase_b_kernel_resources(Kernel kernel, const char *name,
                                    CudaBarrierKernelResources *resources, std::string *error) {
    if (resources == nullptr) {
        if (error != nullptr)
            *error = std::string("CUDA ") + name + " resource query requires an output";
        return false;
    }
    cudaFuncAttributes attributes{};
    cudaError_t status = cudaFuncGetAttributes(&attributes, kernel);
    if (status != cudaSuccess) {
        if (error != nullptr) *error = cuda_error_message(name, status);
        return false;
    }
    constexpr int threads_per_block = 128;
    int active_blocks = 0;
    status =
        cudaOccupancyMaxActiveBlocksPerMultiprocessor(&active_blocks, kernel, threads_per_block, 0);
    if (status != cudaSuccess) {
        if (error != nullptr) *error = cuda_error_message("query Phase B active blocks", status);
        return false;
    }
    int device = 0;
    cudaDeviceProp properties{};
    status = cudaGetDevice(&device);
    if (status == cudaSuccess) status = cudaGetDeviceProperties(&properties, device);
    if (status != cudaSuccess || properties.warpSize <= 0 ||
        properties.maxThreadsPerMultiProcessor <= 0) {
        if (error != nullptr) {
            *error = status == cudaSuccess
                         ? "CUDA device returned invalid Phase B occupancy properties"
                         : cuda_error_message("query CUDA Phase B occupancy properties", status);
        }
        return false;
    }
    *resources = {
        .registers_per_thread = attributes.numRegs,
        .local_bytes_per_thread = attributes.localSizeBytes,
        .static_shared_bytes = attributes.sharedSizeBytes,
        .threads_per_block = threads_per_block,
        .active_blocks_per_multiprocessor = active_blocks,
        .active_warps_per_multiprocessor =
            active_blocks * (threads_per_block / properties.warpSize),
        .theoretical_occupancy = static_cast<double>(active_blocks * threads_per_block) /
                                 static_cast<double>(properties.maxThreadsPerMultiProcessor),
    };
    if (error != nullptr) error->clear();
    return true;
}

bool query_cuda_world_store_phase_b_forces_kernel_resources(CudaBarrierKernelResources *resources,
                                                            std::string *error) {
    return query_phase_b_kernel_resources(phase_b_forces_kernel, "phase_b_forces_kernel", resources,
                                          error);
}

bool query_cuda_world_store_phase_b_aerodynamics_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error) {
    return query_phase_b_kernel_resources(phase_b_aerodynamics_kernel,
                                          "phase_b_aerodynamics_kernel", resources, error);
}

bool query_cuda_world_store_phase_b_integrate_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error) {
    return query_phase_b_kernel_resources(phase_b_integrate_kernel, "phase_b_integrate_kernel",
                                          resources, error);
}

bool release_cuda_world_store_metadata(CudaWorldStoreDeviceAllocation *&allocation,
                                       CudaWorldStoreDeviceFaultInjection *faults) noexcept {
    if (allocation == nullptr) {
        return true;
    }
    if (consume_fault(faults == nullptr ? nullptr : &faults->fail_next_release)) {
        return false;
    }
    if (allocation->storage != nullptr) {
        if (cudaDeviceSynchronize() != cudaSuccess) {
            return false;
        }
        if (cudaFree(allocation->storage) != cudaSuccess) {
            return false;
        }
        allocation->storage = nullptr;
    }
    delete allocation;
    allocation = nullptr;
    return true;
}

} // namespace runtime::cuda_resident::detail
