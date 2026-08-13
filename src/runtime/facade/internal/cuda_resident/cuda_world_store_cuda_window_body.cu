#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_internal.cuh"
#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_math.cuh"

#include "runtime/contracts/cuda_resident_flight_dynamics_fixture_contract.h"
#include "runtime/contracts/cuda_resident_observation_projection_fixture_contract.h"

#include <cmath>

// CP-5 fused window-commit body. The CP-4 achieved counters measured the split
// six-launch window graph at 8.33-10.89% achieved occupancy with zero local
// traffic and zero divergence: the device was near idle and the wall clock was
// the sequential launch chain, not the kernels. The six per-world phases below
// are therefore one launch. Each phase function keeps its original kernel body
// verbatim -- including its global loads and stores and its internal early
// returns -- so the per-world arithmetic order, and with it CPU parity, is
// unchanged by construction. Cross-phase device-wide barriers are not needed:
// every phase reads and writes only its own world's slots.
namespace runtime::cuda_resident::detail {
namespace {

// Phase body of the retired flight_dynamics_forces_kernel, minus the grid
// index computation and capacity guard that now live in the fused kernel.
__device__ void window_phase_flight_dynamics_forces(
    std::size_t world_capacity, std::size_t world, const double *time_steps,
    const double *control_doubles, const float *control_floats, const std::uint8_t *control_flags,
    const double *prepared_doubles, const std::uint8_t *prepared_flags, double *kinematics,
    double *dynamics, double *flight_dynamics_forces, std::uint32_t *status) {
    const double dt = static_cast<double>(static_cast<float>(time_steps[world]));
    const std::size_t kin = world_capacity;
    const std::size_t dyn = world_capacity;
    const bool active = control_flags[2 * world_capacity + world] != 0;
    const bool manual = prepared_flags[world_capacity + world] != 0;
    bool invalid =
        !isfinite(dt) || dt < kFlightDynamicsMinTimeStepS || dt > kFlightDynamicsMaxTimeStepS;

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
    const double flaps = flight_dynamics_clamp(
        static_cast<double>(control_floats[1 * world_capacity + world]), 0.0, 1.0);
    const double speedbrake = flight_dynamics_clamp(
        static_cast<double>(control_floats[2 * world_capacity + world]), 0.0, 1.0);
    (void)raw_pitch;
    (void)raw_roll;
    (void)raw_rudder;

    // control preparation is the authoritative filtered command.  This is the bounded
    // manual/airborne branch of the maintained control model.
    const double stick_roll = flight_dynamics_clamp(prepared_doubles[world], -1.0, 1.0);
    const double stick_pitch =
        flight_dynamics_clamp(prepared_doubles[world_capacity + world], -1.0, 1.0);
    const double stick_yaw =
        flight_dynamics_clamp(prepared_doubles[2 * world_capacity + world], -1.0, 1.0);
    double p_cmd = stick_roll * 1.2;
    double q_cmd = stick_pitch * 0.8;
    double r_cmd = prepared_doubles[3 * world_capacity + world] * 0.8;

    // The fixed fixture has no instrument stage between windows, so its
    // initial/held normal-load sensor value is zero, matching the CPU trace.
    const double g_cmd = stick_pitch >= 0.0 ? 1.0 + stick_pitch * 7.0 : 1.0 + stick_pitch * 3.0;
    q_cmd = flight_dynamics_clamp(0.30 * g_cmd, -0.8, 0.8);
    const double speed = sqrt(vx * vx + vy * vy + vz * vz);
    const double v_eff = fmax(50.0, speed);
    const double phi = flight_dynamics_deg_to_rad(roll);
    const double theta = flight_dynamics_deg_to_rad(pitch);
    const double r_turn = (kFlightDynamicsGravityMps2 / v_eff) * sin(phi) * cos(theta);
    if (manual) {
        r_cmd += 2.0 * flight_dynamics_deg_to_rad(beta) - 0.55 * r;
    } else {
        r_cmd += r_turn - 2.0 * flight_dynamics_deg_to_rad(beta) - 0.55 * (r - r_turn);
    }
    r_cmd = flight_dynamics_clamp(r_cmd, -0.8, 0.8);
    if (fabs(alpha) > 10.0) {
        const double t = flight_dynamics_clamp((fabs(alpha) - 10.0) / 8.0, 0.0, 1.0);
        q_cmd *= 1.0 - t;
    }
    if (fabs(alpha) > 18.0) q_cmd = fmin(q_cmd, -0.15);

    const double aileron_cmd = flight_dynamics_clamp(1.2 * (p_cmd - p), -1.0, 1.0);
    const double elevator_cmd = flight_dynamics_clamp(0.9 * (q_cmd - q_rate), -1.0, 1.0);
    double rudder_cmd = 1.2 * (r_cmd - r) - 0.25 * aileron_cmd;
    rudder_cmd = flight_dynamics_clamp(rudder_cmd, -1.0, 1.0);
    const double gear_target = active && gear_handle >= 0.5 ? 1.0 : 0.0;
    gear_extension += (gear_target >= gear_extension ? 1.0 : -1.0) * dt / 5.0;
    gear_extension = flight_dynamics_clamp(gear_extension, 0.0, 1.0);

    elevator =
        flight_dynamics_first_order(elevator, elevator_cmd, dt, kFlightDynamicsAeroElevatorTauS);
    aileron = flight_dynamics_first_order(aileron, aileron_cmd, dt, kFlightDynamicsAeroAileronTauS);
    rudder = flight_dynamics_first_order(rudder, rudder_cmd, dt, kFlightDynamicsAeroRudderTauS);
    elevator = flight_dynamics_clamp(elevator, -1.0, 1.0);
    aileron = flight_dynamics_clamp(aileron, -1.0, 1.0);
    rudder = flight_dynamics_clamp(rudder, -1.0, 1.0);

    const FlightDynamicsAtmosphere atmosphere = flight_dynamics_atmosphere(z);
    const double air_vx = vx - atmosphere.wind_x;
    const double air_vy = vy;
    const double air_vz = vz;
    const double air_speed_sq = air_vx * air_vx + air_vy * air_vy + air_vz * air_vz;
    const double air_speed = sqrt(air_speed_sq);
    dynamic_pressure = flight_dynamics_canonical(0.5 * atmosphere.density * air_speed_sq, 1.0e-10);
    mach = flight_dynamics_canonical(air_speed / atmosphere.speed_of_sound, 0x1p-40);
    const FlightDynamicsRotation rotation = flight_dynamics_rotation(heading, pitch, roll);
    double body_x = 0.0;
    double body_y = 0.0;
    double body_z = 0.0;
    flight_dynamics_world_to_body(air_vx, air_vy, air_vz, rotation, &body_x, &body_y, &body_z);
    const double alpha_raw = flight_dynamics_rad_to_deg(atan2(-body_z, body_x));
    const double beta_arg = flight_dynamics_clamp(body_y / fmax(air_speed, 1.0e-6), -1.0, 1.0);
    const double beta_raw = flight_dynamics_rad_to_deg(asin(beta_arg));
    const double blend = air_speed <= 2.0 ? 0.0 : (air_speed < 8.0 ? (air_speed - 2.0) / 6.0 : 1.0);
    const double old_alpha = alpha;
    alpha = flight_dynamics_clamp((1.0 - blend) * alpha + blend * alpha_raw, -90.0, 90.0);
    beta = flight_dynamics_clamp((1.0 - blend) * beta + blend * beta_raw, -90.0, 90.0);
    alpha = flight_dynamics_canonical(alpha, 0x1p-40);
    beta = flight_dynamics_canonical(beta, 0x1p-40);
    previous_alpha = old_alpha;
    alpha_rate = blend > 0.0 && dt > 1.0e-6
                     ? flight_dynamics_canonical((alpha - old_alpha) / dt, 0x1p-40)
                     : 0.0;
    // The fixed-air fixture freezes the attached-flow envelope. Post-stall tables, ground
    // effect, damage, and terrain ownership belong to later capability slices.
    if (fabs(alpha) > 14.0 || z < 100.0 || z > 10000.0) invalid = true;

    const double throttle = flight_dynamics_clamp(raw_throttle, 0.0, 1.0);
    const double throttle_target =
        throttle <= kFlightDynamicsEngineAbThreshold ? throttle : kFlightDynamicsEngineAbThreshold;
    const double spool_tau = throttle_target >= throttle_state ? kFlightDynamicsEngineSpoolUpTauS
                                                               : kFlightDynamicsEngineSpoolDownTauS;
    throttle_state = flight_dynamics_clamp(
        flight_dynamics_first_order(throttle_state, throttle_target, dt, spool_tau), 0.0, 1.0);
    const double dry_span = 1.0 - kFlightDynamicsEngineIdleBias;
    const double dry_throttle = flight_dynamics_clamp(
        (throttle_state - kFlightDynamicsEngineIdleBias) / dry_span, 0.0, 1.0);
    const double dry_command = kFlightDynamicsMilThrustN * dry_throttle;
    dry_thrust_state = flight_dynamics_clamp(
        flight_dynamics_first_order(dry_thrust_state, dry_command, dt, spool_tau), 0.0,
        fmax(kFlightDynamicsMilThrustN, dry_command));
    const double ab_command =
        throttle > kFlightDynamicsEngineAbThreshold
            ? flight_dynamics_clamp((throttle - kFlightDynamicsEngineAbThreshold) /
                                        (1.0 - kFlightDynamicsEngineAbThreshold),
                                    0.0, 1.0)
            : 0.0;
    const double ab_tau = ab_command >= ab_state ? kFlightDynamicsEngineAbLightTauS
                                                 : kFlightDynamicsEngineAbExtinguishTauS;
    ab_state = flight_dynamics_clamp(flight_dynamics_first_order(ab_state, ab_command, dt, ab_tau),
                                     0.0, 1.0);
    const double sigma = fmax(0.01, atmosphere.density / kFlightDynamicsSeaLevelDensityKgM3);
    double ram = 1.0 + kFlightDynamicsEngineRamRiseGain *
                           fmin(fmax(0.0, mach), kFlightDynamicsEngineRamRiseMachCap);
    if (mach > kFlightDynamicsEngineRamDecayStartMach)
        ram -= kFlightDynamicsEngineRamDecayGain * (mach - kFlightDynamicsEngineRamDecayStartMach);
    ram = fmax(0.6, ram);
    current_thrust = flight_dynamics_canonical(
        fmax(0.0, (dry_thrust_state +
                   (kFlightDynamicsAbThrustN - kFlightDynamicsMilThrustN) * ab_state) *
                      sigma * ram),
        0x1p-32);

    double force_x = 0.0;
    double force_y = 0.0;
    double force_z = 0.0;
    double torque_roll = 0.0;
    double torque_pitch = 0.0;
    double torque_yaw = 0.0;
    if (active) {
        const double mass =
            kFlightDynamicsEmptyMassKg + kFlightDynamicsFuelMassKg + kFlightDynamicsStoresMassKg;
        force_z -= mass * kFlightDynamicsGravityMps2;
        const double yaw_rad = flight_dynamics_deg_to_rad(90.0 - heading);
        const double pitch_rad = flight_dynamics_deg_to_rad(pitch);
        const double nose_x = flight_dynamics_canonical(cos(yaw_rad) * cos(pitch_rad), 1.0e-14);
        const double nose_y = flight_dynamics_canonical(sin(yaw_rad) * cos(pitch_rad), 1.0e-14);
        const double nose_z = flight_dynamics_canonical(sin(pitch_rad), 1.0e-14);
        force_x += flight_dynamics_canonical(current_thrust * nose_x, 0x1p-32);
        force_y += flight_dynamics_canonical(current_thrust * nose_y, 0x1p-32);
        force_z += flight_dynamics_canonical(current_thrust * nose_z, 0x1p-32);

        // Aerodynamic force/moment accumulation is intentionally the next
        // phase. Keeping this phase responsible for control, aero state,
        // propulsion, gravity, and thrust preserves the retired kernel split
        // as readable structure inside the fused launch.
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
    flight_dynamics_forces[kForceX * world_capacity + world] = force_x;
    flight_dynamics_forces[kForceY * world_capacity + world] = force_y;
    flight_dynamics_forces[kForceZ * world_capacity + world] = force_z;
    flight_dynamics_forces[kTorqueRoll * world_capacity + world] = torque_roll;
    flight_dynamics_forces[kTorquePitch * world_capacity + world] = torque_pitch;
    flight_dynamics_forces[kTorqueYaw * world_capacity + world] = torque_yaw;
}

// Phase body of the retired flight_dynamics_aerodynamics_kernel.
__device__ void window_phase_flight_dynamics_aerodynamics(
    std::size_t world_capacity, std::size_t world, const float *control_floats,
    const std::uint8_t *control_flags, const double *kinematics, double *dynamics,
    double *flight_dynamics_forces, std::uint32_t *status) {
    if (control_flags[2 * world_capacity + world] == 0) return;
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
    const double flaps = flight_dynamics_clamp(
        static_cast<double>(control_floats[world_capacity + world]), 0.0, 1.0);
    const double speedbrake = flight_dynamics_clamp(
        static_cast<double>(control_floats[2 * world_capacity + world]), 0.0, 1.0);
    if (dynamic_pressure < 0.1) {
        dynamics[kDynLiftCoefficient * dyn + world] = 0.0;
        dynamics[kDynDragCoefficient * dyn + world] = 0.0;
        dynamics[kDynStallProgress * dyn + world] = 0.0;
        return;
    }

    const double cl =
        kFlightDynamicsAeroClAlphaPerDeg * flight_dynamics_lookup(mach, 0) * alpha + flaps * 0.35;
    const double cd0 = kFlightDynamicsAeroCd0Clean + flight_dynamics_lookup(mach, 1) +
                       0.02 * 0.001 + gear_extension * 0.04 + speedbrake * 0.08 + flaps * 0.02;
    const double cd =
        cd0 + kFlightDynamicsAeroInducedDragK * flight_dynamics_lookup(mach, 2) * cl * cl;
    const double air_speed = sqrt(vx * vx + vy * vy + vz * vz);
    const double inv_speed = 1.0 / fmax(air_speed, 1.0e-6);
    const double drag_x = -vx * inv_speed;
    const double drag_y = -vy * inv_speed;
    const double drag_z = -vz * inv_speed;
    const FlightDynamicsRotation rotation = flight_dynamics_rotation(heading, pitch, roll);
    double right_x = 0.0;
    double right_y = 0.0;
    double right_z = 0.0;
    flight_dynamics_body_to_world(0.0, 1.0, 0.0, rotation, &right_x, &right_y, &right_z);
    const double cross_x = vy * right_z - vz * right_y;
    const double cross_y = vz * right_x - vx * right_z;
    const double cross_z = vx * right_y - vy * right_x;
    const double cross_mag = sqrt(cross_x * cross_x + cross_y * cross_y + cross_z * cross_z);
    const double lift_x = cross_mag < 1.0e-6 ? 0.0 : cross_x / cross_mag;
    const double lift_y = cross_mag < 1.0e-6 ? 0.0 : cross_y / cross_mag;
    const double lift_z = cross_mag < 1.0e-6 ? 0.0 : cross_z / cross_mag;
    const double lift_mag = dynamic_pressure * kFlightDynamicsReferenceAreaM2 * cl;
    const double drag_mag = dynamic_pressure * kFlightDynamicsReferenceAreaM2 * cd;
    const double aero_force_x = drag_mag * drag_x + lift_mag * lift_x;
    const double aero_force_y = drag_mag * drag_y + lift_mag * lift_y;
    const double aero_force_z = drag_mag * drag_z + lift_mag * lift_z;

    const double v_for_moments = fmax(10.0, air_speed);
    const double p_hat = p * kFlightDynamicsWingSpanM / (2.0 * v_for_moments);
    const double q_hat = q_rate * kFlightDynamicsChordM / (2.0 * v_for_moments);
    const double r_hat = r * kFlightDynamicsWingSpanM / (2.0 * v_for_moments);
    double cm = kFlightDynamicsAeroCmAlphaPerRad * flight_dynamics_lookup(mach, 3) *
                    flight_dynamics_deg_to_rad(alpha) -
                12.0 * q_hat;
    cm += kFlightDynamicsAeroCmDeltaEPerRad *
          flight_dynamics_deg_to_rad(elevator * kFlightDynamicsAeroElevatorMaxDeflectionDeg);
    const double cl_mom =
        -0.1 * flight_dynamics_deg_to_rad(beta) - 0.45 * p_hat + 0.1 * r_hat +
        kFlightDynamicsAeroClDeltaAPerRad *
            flight_dynamics_deg_to_rad(aileron * kFlightDynamicsAeroAileronMaxDeflectionDeg);
    const double cn_mom =
        0.15 * flight_dynamics_deg_to_rad(beta) - 0.25 * r_hat +
        kFlightDynamicsAeroCnDeltaRPerRad *
            flight_dynamics_deg_to_rad(rudder * kFlightDynamicsAeroRudderMaxDeflectionDeg);
    const double torque_pitch =
        dynamic_pressure * kFlightDynamicsReferenceAreaM2 * kFlightDynamicsChordM * cm;
    const double torque_roll =
        dynamic_pressure * kFlightDynamicsReferenceAreaM2 * kFlightDynamicsWingSpanM * cl_mom;
    const double torque_yaw =
        dynamic_pressure * kFlightDynamicsReferenceAreaM2 * kFlightDynamicsWingSpanM * cn_mom;
    if (!isfinite(cl) || !isfinite(cd) || !isfinite(aero_force_x) || !isfinite(aero_force_y) ||
        !isfinite(aero_force_z) || !isfinite(torque_roll) || !isfinite(torque_pitch) ||
        !isfinite(torque_yaw)) {
        atomicExch(status, 1U);
        return;
    }
    dynamics[kDynLiftCoefficient * dyn + world] = cl;
    dynamics[kDynDragCoefficient * dyn + world] = cd;
    dynamics[kDynStallProgress * dyn + world] = 0.0;
    flight_dynamics_forces[kForceX * world_capacity + world] += aero_force_x;
    flight_dynamics_forces[kForceY * world_capacity + world] += aero_force_y;
    flight_dynamics_forces[kForceZ * world_capacity + world] += aero_force_z;
    flight_dynamics_forces[kTorqueRoll * world_capacity + world] = torque_roll;
    flight_dynamics_forces[kTorquePitch * world_capacity + world] = torque_pitch;
    flight_dynamics_forces[kTorqueYaw * world_capacity + world] = torque_yaw;
}

// Phase body of the retired flight_dynamics_integrate_kernel.
__device__ void window_phase_flight_dynamics_integrate(std::size_t world_capacity,
                                                       std::size_t world, const double *time_steps,
                                                       double *kinematics, double *dynamics,
                                                       const double *flight_dynamics_forces,
                                                       std::uint32_t *status) {
    const double dt = static_cast<double>(static_cast<float>(time_steps[world]));
    if (!isfinite(dt) || dt < kFlightDynamicsMinTimeStepS || dt > kFlightDynamicsMaxTimeStepS) {
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
    const double torque_roll = flight_dynamics_forces[kTorqueRoll * world_capacity + world];
    const double torque_pitch = flight_dynamics_forces[kTorquePitch * world_capacity + world];
    const double torque_yaw = flight_dynamics_forces[kTorqueYaw * world_capacity + world];
    constexpr double max_rate = 6.0;
    constexpr double max_accel = 1.0e4;
    p +=
        flight_dynamics_clamp(torque_roll / kFlightDynamicsInertiaRollKgM2, -max_accel, max_accel) *
        dt;
    q_rate += flight_dynamics_clamp(torque_pitch / kFlightDynamicsInertiaPitchKgM2, -max_accel,
                                    max_accel) *
              dt;
    r += flight_dynamics_clamp(torque_yaw / kFlightDynamicsInertiaYawKgM2, -max_accel, max_accel) *
         dt;
    p = flight_dynamics_clamp(p, -max_rate, max_rate);
    q_rate = flight_dynamics_clamp(q_rate, -max_rate, max_rate);
    r = flight_dynamics_clamp(r, -max_rate, max_rate);
    const double phi = flight_dynamics_deg_to_rad(roll);
    double ctheta = cos(flight_dynamics_deg_to_rad(pitch));
    const double stheta = sin(flight_dynamics_deg_to_rad(pitch));
    if (fabs(ctheta) < cos(flight_dynamics_deg_to_rad(85.0)))
        ctheta = copysign(cos(flight_dynamics_deg_to_rad(85.0)), ctheta);
    const double sphi = sin(phi);
    const double cphi = cos(phi);
    const double tan_theta = stheta / ctheta;
    const double sec_theta = 1.0 / ctheta;
    const double dphi = p + (q_rate * sphi + r * cphi) * tan_theta;
    const double dtheta = q_rate * cphi - r * sphi;
    const double dpsi = (q_rate * sphi + r * cphi) * sec_theta;
    roll += flight_dynamics_rad_to_deg(dphi) * dt;
    pitch += flight_dynamics_rad_to_deg(dtheta) * dt;
    heading -= flight_dynamics_rad_to_deg(dpsi) * dt;
    roll = fmod(roll + 180.0, 360.0);
    if (roll < 0.0) roll += 360.0;
    roll -= 180.0;
    pitch = flight_dynamics_clamp(pitch, -89.0, 89.0);
    heading = flight_dynamics_wrap_360(heading);

    const double mass =
        kFlightDynamicsEmptyMassKg + kFlightDynamicsFuelMassKg + kFlightDynamicsStoresMassKg;
    const double ax = flight_dynamics_forces[kForceX * world_capacity + world] / mass;
    const double ay = flight_dynamics_forces[kForceY * world_capacity + world] / mass;
    const double az = flight_dynamics_forces[kForceZ * world_capacity + world] / mass;
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

// Phase body of the retired instrument_projection_kernel.
__device__ void window_phase_instrument_projection(std::size_t world_capacity, std::size_t world,
                                                   const double *kinematics, const double *dynamics,
                                                   const double *flight_dynamics_forces,
                                                   double *instruments, std::uint32_t *status) {
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

// Phase body of the retired configuration_projection_kernel.
__device__ void window_phase_configuration_projection(std::size_t world_capacity, std::size_t world,
                                                      const double *dynamics,
                                                      const double *control_doubles,
                                                      const float *control_floats,
                                                      double *instruments, std::uint32_t *status) {
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

// Phase body of the retired episode_projection_kernel.
__device__ void window_phase_episode_projection(
    std::size_t world_capacity, std::size_t world, const double *time_steps,
    const double *simulation_times, const double *kinematics, const double *dynamics,
    const double *instruments, const std::uint64_t *entity_ids,
    const std::uint64_t *global_versions, double *observations, std::uint64_t *observation_ids,
    double *rewards, std::uint64_t *reward_versions, std::uint8_t *termination_flags,
    std::uint8_t *termination_codes, std::uint8_t *event_empty, std::uint32_t *status) {
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

// One launch for the whole per-world window-commit body. Phase order is the
// retired launch order. Every phase ran for every world in the split graph --
// no kernel read the status flag, so a failed world only marked status and the
// host discarded the staged slot. Running all phases unconditionally here
// preserves exactly that observable contract.
//
// CP-7b: the window_commit barrier is the kernel's final per-world epilogue
// instead of a separate launch. The epilogue mirrors apply_barrier_kernel's
// window_commit branch exactly, runs after the episode phase (which reads the
// pre-increment simulation time and global version, as it did across the v3
// launch boundary), and touches only its own world's version, clock, and
// shard fields.
__global__ void window_commit_body_kernel(
    std::size_t world_capacity, const double *time_steps, double *simulation_times,
    const double *control_doubles, const float *control_floats, const std::uint8_t *control_flags,
    const double *prepared_doubles, const std::uint8_t *prepared_flags,
    const std::uint64_t *entity_ids, std::uint64_t *global_versions, double *kinematics,
    double *dynamics, double *flight_dynamics_forces, double *instruments, double *observations,
    std::uint64_t *observation_ids, double *rewards, std::uint64_t *reward_versions,
    std::uint8_t *termination_flags, std::uint8_t *termination_codes, std::uint8_t *event_empty,
    std::uint64_t *clock_ticks, std::uint64_t *barrier_sequences, std::uint8_t *barrier_codes,
    std::uint64_t *shard_versions, std::uint32_t *status) {
    const std::size_t world = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (world >= world_capacity) return;
    window_phase_flight_dynamics_forces(
        world_capacity, world, time_steps, control_doubles, control_floats, control_flags,
        prepared_doubles, prepared_flags, kinematics, dynamics, flight_dynamics_forces, status);
    window_phase_flight_dynamics_aerodynamics(world_capacity, world, control_floats, control_flags,
                                              kinematics, dynamics, flight_dynamics_forces, status);
    window_phase_flight_dynamics_integrate(world_capacity, world, time_steps, kinematics, dynamics,
                                           flight_dynamics_forces, status);
    window_phase_instrument_projection(world_capacity, world, kinematics, dynamics,
                                       flight_dynamics_forces, instruments, status);
    window_phase_configuration_projection(world_capacity, world, dynamics, control_doubles,
                                          control_floats, instruments, status);
    window_phase_episode_projection(world_capacity, world, time_steps, simulation_times, kinematics,
                                    dynamics, instruments, entity_ids, global_versions,
                                    observations, observation_ids, rewards, reward_versions,
                                    termination_flags, termination_codes, event_empty, status);

    bool overflow = increment_would_overflow(barrier_sequences[world]) ||
                    increment_would_overflow(global_versions[world]) ||
                    increment_would_overflow(clock_ticks[world]) ||
                    !isfinite(simulation_times[world] + time_steps[world]);

    const std::size_t identity_index =
        static_cast<std::size_t>(CudaResidentShard::identity) * world_capacity + world;
    const std::size_t clock_index =
        static_cast<std::size_t>(CudaResidentShard::clock) * world_capacity + world;
    const std::size_t snapshot_index =
        static_cast<std::size_t>(CudaResidentShard::snapshot) * world_capacity + world;
    const std::size_t kinematics_index =
        static_cast<std::size_t>(CudaResidentShard::kinematics) * world_capacity + world;
    const std::size_t dynamics_index =
        static_cast<std::size_t>(CudaResidentShard::dynamics) * world_capacity + world;
    const std::size_t episode_index =
        static_cast<std::size_t>(CudaResidentShard::episode) * world_capacity + world;
    const std::size_t instrument_index =
        static_cast<std::size_t>(CudaResidentShard::instrument) * world_capacity + world;
    const std::size_t observation_index =
        static_cast<std::size_t>(CudaResidentShard::observation) * world_capacity + world;
    const std::size_t reward_index =
        static_cast<std::size_t>(CudaResidentShard::reward) * world_capacity + world;
    const std::size_t termination_index =
        static_cast<std::size_t>(CudaResidentShard::termination) * world_capacity + world;
    const std::size_t events_index =
        static_cast<std::size_t>(CudaResidentShard::events) * world_capacity + world;
    overflow = overflow || increment_would_overflow(shard_versions[identity_index]) ||
               increment_would_overflow(shard_versions[clock_index]) ||
               increment_would_overflow(shard_versions[snapshot_index]) ||
               increment_would_overflow(shard_versions[kinematics_index]) ||
               increment_would_overflow(shard_versions[dynamics_index]) ||
               increment_would_overflow(shard_versions[episode_index]) ||
               increment_would_overflow(shard_versions[instrument_index]) ||
               increment_would_overflow(shard_versions[observation_index]) ||
               increment_would_overflow(shard_versions[reward_index]) ||
               increment_would_overflow(shard_versions[termination_index]) ||
               increment_would_overflow(shard_versions[events_index]);
    if (overflow) {
        atomicExch(status, 1U);
        return;
    }

    ++barrier_sequences[world];
    barrier_codes[world] = static_cast<std::uint8_t>(CudaResidentBarrierCode::window_commit);
    ++global_versions[world];
    ++clock_ticks[world];
    simulation_times[world] += time_steps[world];
    ++shard_versions[identity_index];
    ++shard_versions[clock_index];
    ++shard_versions[snapshot_index];
    ++shard_versions[kinematics_index];
    ++shard_versions[dynamics_index];
    ++shard_versions[episode_index];
    ++shard_versions[instrument_index];
    ++shard_versions[observation_index];
    ++shard_versions[reward_index];
    ++shard_versions[termination_index];
    ++shard_versions[events_index];
}

} // namespace

cudaError_t launch_window_commit_body(CudaWorldStoreDeviceAllocation *allocation,
                                      std::uint8_t slot_index) noexcept {
    if (allocation == nullptr) return cudaErrorInvalidValue;
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    std::uint8_t *slot = allocation->state_slots[slot_index];
    window_commit_body_kernel<<<blocks, threads>>>(
        allocation->world_capacity, device_field<double>(slot, allocation->state_layout.time_steps),
        device_field<double>(slot, allocation->state_layout.simulation_times),
        device_field<double>(slot, allocation->state_layout.control_doubles),
        device_field<float>(slot, allocation->state_layout.control_floats),
        device_field<std::uint8_t>(slot, allocation->state_layout.control_flags),
        device_field<double>(slot, allocation->state_layout.prepared_doubles),
        device_field<std::uint8_t>(slot, allocation->state_layout.prepared_flags),
        device_field<std::uint64_t>(slot, allocation->state_layout.entity_ids),
        device_field<std::uint64_t>(slot, allocation->state_layout.global_versions),
        device_field<double>(slot, allocation->state_layout.kinematics),
        device_field<double>(slot, allocation->state_layout.dynamics),
        device_field<double>(slot, allocation->state_layout.flight_dynamics_forces),
        device_field<double>(slot, allocation->state_layout.projected_instruments),
        device_field<double>(slot, allocation->state_layout.projected_observations),
        device_field<std::uint64_t>(slot, allocation->state_layout.projected_observation_ids),
        device_field<double>(slot, allocation->state_layout.projected_rewards),
        device_field<std::uint64_t>(slot, allocation->state_layout.projected_reward_versions),
        device_field<std::uint8_t>(slot, allocation->state_layout.projected_termination_flags),
        device_field<std::uint8_t>(slot, allocation->state_layout.projected_termination_codes),
        device_field<std::uint8_t>(slot, allocation->state_layout.projected_event_empty),
        device_field<std::uint64_t>(slot, allocation->state_layout.clock_ticks),
        device_field<std::uint64_t>(slot, allocation->state_layout.barrier_sequences),
        device_field<std::uint8_t>(slot, allocation->state_layout.barrier_codes),
        device_field<std::uint64_t>(slot, allocation->state_layout.shard_versions),
        allocation->barrier_status);
    return cudaGetLastError();
}

bool query_cuda_world_store_window_commit_body_kernel_resources(
    CudaBarrierKernelResources *resources, std::string *error) {
    return query_cuda_kernel_resources(window_commit_body_kernel, "window_commit_body_kernel",
                                       resources, error);
}

} // namespace runtime::cuda_resident::detail
