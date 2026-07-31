#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_internal.cuh"
#include "runtime/facade/internal/cuda_resident/cuda_world_store_cuda_math.cuh"

#include "runtime/contracts/cuda_resident_phase_b_fixture_contract.h"

#include <cmath>
namespace runtime::cuda_resident::detail {
namespace {
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

} // namespace


cudaError_t launch_phase_b_forces(CudaWorldStoreDeviceAllocation *allocation,
                                  std::uint8_t slot_index) noexcept {
    if (allocation == nullptr) return cudaErrorInvalidValue;
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    std::uint8_t *slot = allocation->state_slots[slot_index];
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
    return cudaGetLastError();
}

cudaError_t launch_phase_b_aerodynamics(CudaWorldStoreDeviceAllocation *allocation,
                                        std::uint8_t slot_index) noexcept {
    if (allocation == nullptr) return cudaErrorInvalidValue;
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    std::uint8_t *slot = allocation->state_slots[slot_index];
    phase_b_aerodynamics_kernel<<<blocks, threads>>>(
        allocation->world_capacity,
        device_field<float>(slot, allocation->state_layout.control_floats),
        device_field<std::uint8_t>(slot, allocation->state_layout.control_flags),
        device_field<double>(slot, allocation->state_layout.kinematics),
        device_field<double>(slot, allocation->state_layout.dynamics),
        device_field<double>(slot, allocation->state_layout.phase_b_forces),
        allocation->barrier_status);
    return cudaGetLastError();
}

cudaError_t launch_phase_b_integrate(CudaWorldStoreDeviceAllocation *allocation,
                                     std::uint8_t slot_index) noexcept {
    if (allocation == nullptr) return cudaErrorInvalidValue;
    constexpr unsigned int threads = 128;
    const unsigned int blocks =
        static_cast<unsigned int>((allocation->world_capacity + threads - 1) / threads);
    std::uint8_t *slot = allocation->state_slots[slot_index];
    phase_b_integrate_kernel<<<blocks, threads>>>(
        allocation->world_capacity,
        device_field<double>(slot, allocation->state_layout.time_steps),
        device_field<double>(slot, allocation->state_layout.kinematics),
        device_field<double>(slot, allocation->state_layout.dynamics),
        device_field<double>(slot, allocation->state_layout.phase_b_forces),
        allocation->barrier_status);
    return cudaGetLastError();
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


} // namespace runtime::cuda_resident::detail
