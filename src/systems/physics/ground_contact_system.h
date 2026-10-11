#pragma once

#include <flecs.h>
#include <array>
#include <cmath>
#include <utility>
#include "components/basic/common.h"
#include "components/combat/structural_failure.h"
#include "components/domains/air/command/control_input_resolution.h"
#include "components/physics/forces.h"
#include "components/physics/physics_input_policy.h"
#include "components/physics/dynamics.h"
#include "components/systems/logistics.h"   // For GroundState
#include "components/physics/performance.h" // For LandingGear
#include "components/physics/control_law.h" // For ControlLawState (FBW filtered inputs)
#include "core/interfaces/engagement_event_recorder.h"
#include "core/interfaces/environment_model.h"
#include "systems/combat/mlf8_lifecycle_events.h"
#include "systems/physics/ground_contact_solver.h"

namespace {
// Gear spring-damper (normal direction).
constexpr double kGroundSpring = 2000000.0;
constexpr double kGroundDamper = 350000.0;

// Default Friction (Fallback)
constexpr double kMuBraking = 0.8;

// Simple Nose Wheel Steering (NWS) approximation:
// Map rudder pedal input to a nose-wheel steering angle at low speeds when weight-on-wheels.
// This provides realistic directional control during the takeoff roll (rudder surfaces have little
// authority at low airspeed). The effect fades out at higher speeds to avoid unrealistic high-speed
// steering.
constexpr double kNwsMinSpeedMps = 2.0;   // No steering at (near) standstill
constexpr double kNwsFadeStartMps = 30.0; // Begin fading out toward aero rudder
constexpr double kNwsFadeEndMps = 55.0;   // Fully faded out by this speed
constexpr double kNwsDeadzone = 0.02;     // Ignore tiny pedal noise
constexpr double kNwsMaxSteerDeg = 25.0;  // Max nose wheel steer angle (low speed, NWS engaged)
constexpr double kNwsHighSpeedFrac =
    0.15; // Residual steering fraction at/above fade end (~3-4 deg)
constexpr double kNwsInputScaler =
    1.0; // Pedals map directly; ControlLawState filtering handles PIO

// Wheel contact patch approximation (tricycle gear as two effective contact points along body X
// axis).
constexpr double kWheelContactNoseX = 4.0;  // meters forward of CG
constexpr double kWheelContactMainX = -2.0; // meters aft of CG
constexpr double kWheelFnNoseFrac = 0.20;   // weight on nose gear
constexpr double kWheelFnMainFrac = 0.80;   // weight on main gear

// Tire model:
// - Lateral force from slip with linear cornering stiffness, saturated at mu_lat * Fn. The slip
//   law is expressed as a lateral compliance |v_long| / C_alpha, so at rest it degenerates to
//   exact sticking.
// - Longitudinal rolling resistance as a separate Coulomb term (does not consume the friction
//   ellipse budget).
// - Braking is Coulomb friction coupled to lateral grip through a friction ellipse.
// All three are set-valued (exact) Coulomb laws solved implicitly; see ground_contact_solver.h.
constexpr double kTireCorneringStiffnessPerFn =
    18.0; // [N/rad] per [N] of normal load (dimensionless)
constexpr double kEnvironmentScalarCanonicalQuantum = 0x1p-76;
constexpr double kHardLandingSinkRateMps = 9.0;
constexpr double kSevereImpactSinkRateMps = 15.0;
constexpr double kOffroadCrashSpeedMps = 45.0;
constexpr double kPavedCrashSpeedMps = 95.0;

// Gear attitude constraints (torsional spring-dampers on pitch and roll while on the gear).
// Pitch stiffness must exceed the aerodynamic control moment: ~60 * q * 0.8 @ q=3000 -> 144,000
// Nm, so restoring > 144,000 Nm at 10 deg needs Kp > 825,000 Nm/rad.
constexpr double kGearPitchStiffnessNmPerRad = 2000000.0;
constexpr double kGearPitchDampingNmSPerRad = 200000.0;
// Allow a realistic ground rotation attitude (~10 deg) before the gear constraint starts
// resisting further pitch-up, so the aircraft is not pinned near 2 deg pitch and can lift off at
// realistic takeoff speeds and ground-roll distances.
constexpr double kGroundPitchFreeDeg = 10.0;
// Roll: prevent banking on the runway (small roll-stick errors must not accumulate to >30 deg
// roll while on the gear).
constexpr double kGearRollStiffnessNmPerRad = 2000000.0;
constexpr double kGearRollDampingNmSPerRad = 200000.0;
constexpr double kGroundRollFreeDeg = 2.0;
// Below these rates only the spring acts (damping deadband).
constexpr double kGearDampingDeadbandRadS = 0.01;

// Must match the fallbacks in RotationalIntegrate and LeapfrogIntegrate, whose updates the implicit
// solve reproduces.

inline double canonicalize_environment_scalar(double value) {
    if (!std::isfinite(value) || kEnvironmentScalarCanonicalQuantum <= 0.0) {
        return value;
    }
    if (std::abs(value) <= (kEnvironmentScalarCanonicalQuantum * 0.5)) {
        return 0.0;
    }
    const double rounded = std::nearbyint(value / kEnvironmentScalarCanonicalQuantum) *
                           kEnvironmentScalarCanonicalQuantum;
    return std::abs(rounded) <= (kEnvironmentScalarCanonicalQuantum * 0.5) ? 0.0 : rounded;
}

inline void record_terminal_wreck_lifecycle(flecs::entity entity,
                                            IEngagementEventRecorder *recorder,
                                            GroundImpactLifecycle lifecycle, double source_time_s) {
    mlf8_lifecycle::record_terminal_wreck_lifecycle(entity, recorder, lifecycle, source_time_s);
}

// Gear pitch law: spring beyond the free rotation attitude plus damping outside the deadband.
inline double gear_pitch_law_torque(double pitch_rad, double q_rad_s) {
    const double free_rad = Math::to_radians(kGroundPitchFreeDeg);
    double torque = 0.0;
    if (pitch_rad > free_rad) {
        torque -= kGearPitchStiffnessNmPerRad * (pitch_rad - free_rad);
        torque -= kGearPitchDampingNmSPerRad * q_rad_s;
    } else if (std::abs(q_rad_s) > kGearDampingDeadbandRadS) {
        torque -= kGearPitchDampingNmSPerRad * q_rad_s;
    }
    return torque;
}

// Gear roll law: restoring spring on |roll| beyond the free band plus damping outside the deadband.
inline double gear_roll_law_torque(double roll_rad, double p_rad_s) {
    const double free_rad = Math::to_radians(kGroundRollFreeDeg);
    double torque = 0.0;
    if (std::abs(roll_rad) > free_rad) {
        torque -= kGearRollStiffnessNmPerRad * roll_rad;
        torque -= kGearRollDampingNmSPerRad * p_rad_s;
    } else if (std::abs(p_rad_s) > kGearDampingDeadbandRadS) {
        torque -= kGearRollDampingNmSPerRad * p_rad_s;
    }
    return torque;
}
} // namespace

/**
 * GroundContactSystem
 *
 * Penalty-method gear contact with surface-dependent friction from the EnvironmentModel.
 *
 * Time discretization: GroundContact is the last force producer before RotationalIntegrate and
 * LeapfrogIntegrate, so the ForceAccumulator already holds every other force and torque of the
 * step. The contact force and torques are solved so the contact laws hold at the END of the step
 * under those integrators' updates (semi-implicit), which keeps the stiff gear spring-damper and
 * the Coulomb friction stable at any step size. The laws themselves are in
 * ground_contact_solver.h.
 */
inline void register_ground_contact_system(flecs::world &ecs) {
    ecs.system<ForceAccumulator, const Transform, const Velocity, const Mass, GroundState>(
           "GroundContact")
        .kind(flecs::OnUpdate)
        // Must run BEFORE Integration but AFTER Aerodynamics
        .run([](flecs::iter &it) {
            namespace solver = ground_contact_solver;
            while (it.next()) {
                auto forces = it.field<ForceAccumulator>(0);
                auto transform = it.field<const Transform>(1);
                auto velocity = it.field<const Velocity>(2);
                auto mass = it.field<const Mass>(3);
                auto ground = it.field<GroundState>(4);
                const EngagementEventRecorderRef *recorder_ref =
                    it.world().get<EngagementEventRecorderRef>();
                IEngagementEventRecorder *recorder =
                    recorder_ref ? recorder_ref->recorder : nullptr;
                const EnvironmentModelRef *environment_ref = it.world().get<EnvironmentModelRef>();
                IEnvironmentModel *environment = environment_ref ? environment_ref->model : nullptr;
                if (environment == nullptr) {
                    continue;
                }
                const ecs_world_info_t *world_info = ecs_get_world_info(it.world().c_ptr());
                const double current_time =
                    world_info ? static_cast<double>(world_info->world_time_total) : 0.0;
                const double dt = physics_runtime::resolve_integrator_dt(it.delta_time());

                for (auto i : it) {
                    double m = mass[i].get_total_kg();
                    if (!physics_runtime::valid_mass(m)) continue;
                    flecs::entity entity = it.entity(i);

                    // 1. Detection: Query Environment
                    // Use current position (x, y)
                    auto terrain = environment->get_terrain_at(transform[i].x, transform[i].y);

                    double terrain_z = canonicalize_environment_scalar(terrain.elevation);
                    ground[i].terrain_elevation = terrain_z;

                    // Contact height is model-specific and scales with extension state.
                    double gear_height = 2.0;
                    const LandingGear *landing_gear = entity.get<LandingGear>();
                    if (landing_gear) {
                        const double ext = std::clamp(landing_gear->extension_state, 0.0, 1.0);
                        gear_height = std::max(0.4, landing_gear->contact_height_m) * ext;
                    }

                    const double penetration = gear_height - (transform[i].z - terrain_z);

                    // 2. Normal Force: unilateral spring-damper, solved on the end-of-step
                    // penetration. The contact engages when the free motion of this step would
                    // end in penetration, so a body falling onto the surface is caught in the
                    // step it arrives rather than one step later.
                    solver::NormalContactInput normal_in;
                    normal_in.mass_kg = m;
                    normal_in.dt_s = dt;
                    normal_in.penetration_m = penetration;
                    normal_in.vertical_speed_mps = velocity[i].vz;
                    normal_in.other_vertical_force_n = forces[i].fz;
                    normal_in.stiffness_n_per_m = kGroundSpring;
                    normal_in.damping_n_s_per_m = kGroundDamper;
                    const solver::NormalContactResult normal =
                        solver::solve_normal_contact(normal_in);

                    const bool is_touching = normal.active;
                    ground[i].on_ground = is_touching;

                    if (!is_touching) {
                        if (ground[i].lifecycle != GroundImpactLifecycle::CrashedWreck &&
                            ground[i].lifecycle != GroundImpactLifecycle::DebrisFragmentResidue) {
                            ground[i].lifecycle = GroundImpactLifecycle::None;
                            ground[i].impact_horizontal_speed_mps = 0.0;
                            ground[i].impact_sink_rate_mps = 0.0;
                            ground[i].impact_severity = 0.0;
                        }
                        continue;
                    }

                    const double Fn = normal.force_n;
                    forces[i].add_force(0.0, 0.0, Fn);

                    // 3. Friction & Surface Interaction
                    const double vx = velocity[i].vx;
                    const double vy = velocity[i].vy;
                    const double v_h = std::hypot(vx, vy);
                    const double sink_rate_mps = std::max(0.0, -velocity[i].vz);
                    ground[i].impact_horizontal_speed_mps = v_h;
                    ground[i].impact_sink_rate_mps = sink_rate_mps;

                    double gear_mu_roll = 0.02; // Default paved-surface rolling coefficient
                    if (landing_gear) {
                        gear_mu_roll = std::max(0.0, landing_gear->rolling_friction_coeff);
                    }

                    double mu_rolling = gear_mu_roll;

                    using Surface = IEnvironmentModel::SurfaceType;
                    bool is_offroad = false;

                    switch (terrain.type) {
                    case Surface::Concrete:
                        mu_rolling = std::max(0.01, gear_mu_roll);
                        break;
                    case Surface::Asphalt:
                        mu_rolling = std::max(0.0125, gear_mu_roll * 1.25);
                        break;
                    case Surface::HardPacked:
                        mu_rolling = std::max(0.05, gear_mu_roll * 2.5);
                        is_offroad = true;
                        break;
                    case Surface::SoftDirt:
                        mu_rolling = std::max(0.15, gear_mu_roll * 7.5);
                        is_offroad = true;
                        break;
                    case Surface::Water:
                        mu_rolling = std::max(0.80, gear_mu_roll * 20.0);
                        is_offroad = true;
                        break; // Sinking
                    case Surface::Obstacle:
                        mu_rolling = std::max(1.0, gear_mu_roll * 25.0);
                        is_offroad = true;
                        break; // Collision
                    default:
                        mu_rolling = std::max(0.10, gear_mu_roll * 5.0);
                        is_offroad = true;
                        break;
                    }

                    const double sink_severity = sink_rate_mps / kSevereImpactSinkRateMps;
                    const double speed_reference =
                        is_offroad ? kOffroadCrashSpeedMps : kPavedCrashSpeedMps;
                    const double speed_severity = v_h / std::max(1.0, speed_reference);
                    const double impact_severity = std::max(sink_severity, speed_severity);
                    const bool severe_impact =
                        sink_rate_mps >= kSevereImpactSinkRateMps ||
                        (is_offroad && v_h >= kOffroadCrashSpeedMps && sink_rate_mps >= 2.0) ||
                        (!is_offroad && v_h >= kPavedCrashSpeedMps &&
                         sink_rate_mps >= kHardLandingSinkRateMps);
                    ground[i].impact_severity = impact_severity;
                    const GroundImpactLifecycle prior_lifecycle = ground[i].lifecycle;
                    if (ground[i].lifecycle != GroundImpactLifecycle::CrashedWreck &&
                        ground[i].lifecycle != GroundImpactLifecycle::DebrisFragmentResidue) {
                        ground[i].lifecycle = severe_impact ? GroundImpactLifecycle::CrashedWreck
                                                            : GroundImpactLifecycle::LandedAirframe;
                        if (ground[i].lifecycle != prior_lifecycle &&
                            mlf8_lifecycle::is_terminal_wreck_lifecycle(ground[i].lifecycle)) {
                            record_terminal_wreck_lifecycle(entity, recorder, ground[i].lifecycle,
                                                            current_time);
                        }
                    }
                    const ResolvedAirControlInput control_input = resolve_air_control_input(
                        it.entity(i).get<PilotAction>(),
                        it.entity(i).get<MissionCommandControlState>(), nullptr);
                    const ResolvedGroundControlInput ground_control = control_input.ground_control;
                    double brake_amount = ground_control.brake_amount;

                    // --- Gear State Update ---
                    // Track whether on paved surface and accumulate stress if off-road at speed
                    GearState *gear = entity.get_mut<GearState>();
                    if (gear) {
                        gear->on_runway = !is_offroad;
                        gear->stress_rate = 0.0; // Reset each frame

                        // Stress accumulation only when gear down, off-road, and moving fast
                        if (gear->gear_down && !gear->collapsed && is_offroad && v_h > 40.0) {
                            // Severity based on surface type
                            double severity = 1.0;
                            if (terrain.type == Surface::SoftDirt)
                                severity = 1.0;
                            else if (terrain.type == Surface::HardPacked)
                                severity = 0.3;
                            else if (terrain.type == Surface::Water)
                                severity = 2.0;
                            else if (terrain.type == Surface::Obstacle)
                                severity = 5.0;

                            // Stress rate: (v - 40) / 60 * severity -> ~1.0/s at 100 m/s on
                            // SoftDirt
                            gear->stress_rate = severity * (v_h - 40.0) / 60.0;
                            gear->stress += gear->stress_rate * dt;

                            // Increase friction to simulate digging in
                            mu_rolling *= (1.0 + 4.0 * gear->stress); // Up to 5x at collapse

                            // Check for collapse
                            if (gear->stress >= 1.0) {
                                gear->collapsed = true;
                                const GroundImpactLifecycle prior_gear_lifecycle =
                                    ground[i].lifecycle;
                                ground[i].lifecycle = GroundImpactLifecycle::CrashedWreck;
                                ground[i].impact_severity =
                                    std::max(ground[i].impact_severity, 1.0);
                                if (ground[i].lifecycle != prior_gear_lifecycle) {
                                    record_terminal_wreck_lifecycle(
                                        entity, recorder, ground[i].lifecycle, current_time);
                                }
                            }
                        }
                    } else {
                        // Legacy behavior: just increase friction
                        if (is_offroad && v_h > 40.0) {
                            mu_rolling *= 5.0;
                        }
                    }

                    // 3.5 Nose Wheel Steering (NWS): rudder pedal -> steer angle (low speed,
                    // WoW). NOTE: Sign convention: PilotAction.rudder > 0 means "nose right".
                    // In our NAV heading convention, increasing heading is a right turn, which
                    // corresponds to NEGATIVE yaw torque (see RotationalIntegrate). Here we
                    // model steering via the wheel, so we set a negative steer angle for
                    // positive rudder.
                    double nws_steer_rad = 0.0;
                    if (control_input.nose_wheel_steering.available) {
                        double yaw_cmd = control_input.nose_wheel_steering.yaw_command;
                        if (const ControlLawState *ctl = entity.get<ControlLawState>()) {
                            // Use the *filtered pedal* (not the yaw-rate-limited command) for
                            // NWS. NWS is a mechanical linkage from pedals to the nose wheel at
                            // low speed; it should not inherit the high-speed yaw authority
                            // limits intended for aerodynamic rudder control.
                            //
                            // ControlLawState.stick_yaw_filt is stored in the sim's internal
                            // yaw sign (positive corresponds to decreasing heading). Convert
                            // back to the PilotAction convention (positive = nose right /
                            // increasing heading) for NWS.
                            yaw_cmd = -ctl->stick_yaw_filt;
                        }
                        double steer = std::clamp(yaw_cmd, -1.0, 1.0) * kNwsInputScaler;
                        if (std::abs(steer) < kNwsDeadzone) {
                            steer = 0.0;
                        }

                        if (std::abs(steer) > 1e-6) {
                            bool gear_extended = true;
                            if (landing_gear) {
                                gear_extended = (landing_gear->extension_state >= 0.5);
                            }
                            if (gear_extended) {
                                double speed_factor = std::clamp(v_h / kNwsMinSpeedMps, 0.0, 1.0);
                                double fade = 1.0;
                                if (v_h >= kNwsFadeStartMps) {
                                    double t = (v_h - kNwsFadeStartMps) /
                                               (kNwsFadeEndMps - kNwsFadeStartMps);
                                    t = std::clamp(t, 0.0, 1.0);
                                    // Fade down to a small residual steering authority instead
                                    // of zero. Many aircraft retain a limited pedal->nosewheel
                                    // linkage at higher speeds.
                                    fade =
                                        (1.0 - t) * (1.0 - kNwsHighSpeedFrac) + kNwsHighSpeedFrac;
                                }
                                double gain = speed_factor * fade;
                                if (gain > 0.0) {
                                    nws_steer_rad =
                                        -steer * Math::to_radians(kNwsMaxSteerDeg) * gain;
                                }
                            }
                        }
                    }

                    // Auto-stop / parking brake when throttle is idle at low speed.
                    if (ground_control.throttle_idle && v_h < 10.0) {
                        brake_amount = std::max(brake_amount, 1.0);
                    }

                    const double mu_roll = mu_rolling;
                    const double mu_brake = std::clamp(brake_amount, 0.0, 1.0) * kMuBraking;

                    // Tire lateral grip is much higher than rolling resistance.
                    double mu_lat = mu_rolling;
                    switch (terrain.type) {
                    case Surface::Concrete:
                        mu_lat = 0.80;
                        break;
                    case Surface::Asphalt:
                        mu_lat = 0.75;
                        break;
                    case Surface::HardPacked:
                        mu_lat = 0.60;
                        break;
                    case Surface::SoftDirt:
                        mu_lat = 0.50;
                        break;
                    case Surface::Water:
                        mu_lat = 0.20;
                        break;
                    case Surface::Obstacle:
                        mu_lat = 1.00;
                        break;
                    default:
                        mu_lat = 0.40;
                        break;
                    }
                    mu_lat = std::max(mu_lat, mu_roll);

                    // Resolve into the body-heading frame: forward / left (the sim's body frame
                    // uses +Y = LEFT, consistent with AeroState world_to_body).
                    const double hdg_rad = Math::to_radians(transform[i].heading);
                    const double fwd_x = std::sin(hdg_rad);
                    const double fwd_y = std::cos(hdg_rad);
                    const double left_x = -std::cos(hdg_rad);
                    const double left_y = std::sin(hdg_rad);

                    // Yaw state as RotationalIntegrate advances it (it clamps torque and angular
                    // acceleration; ground torques stay far inside those bounds).
                    const AngularVelocity *ang_vel = entity.get<AngularVelocity>();
                    const Inertia *inertia = entity.get<Inertia>();
                    const bool has_rotation = ang_vel != nullptr && inertia != nullptr;
                    const double r0 = ang_vel ? ang_vel->r : 0.0;
                    const double inv_izz =
                        (has_rotation && inertia->izz > 0.0) ? 1.0 / inertia->izz : 0.0;

                    // Free end-of-step body twist (no contact friction).
                    const double inv_m = 1.0 / m;
                    const double vx_free = vx + dt * inv_m * forces[i].fx;
                    const double vy_free = vy + dt * inv_m * forces[i].fy;
                    const std::array<double, 3> u_free{
                        vx_free * fwd_x + vy_free * fwd_y,
                        vx_free * left_x + vy_free * left_y,
                        r0 + dt * inv_izz * forces[i].torque_yaw,
                    };

                    // Wheel-based tire forces at effective contact points, so yaw moments emerge
                    // from the contact. Brakes act on the main gear; the nose wheel is unbraked.
                    const double v_long = vx * fwd_x + vy * fwd_y;
                    const double v_lat = vx * left_x + vy * left_y;
                    auto make_wheel = [&](double x_body_m, double fn_frac, double steer_rad,
                                          double mu_brake_w) {
                        const double fn_w = Fn * fn_frac;
                        solver::Wheel wheel;
                        wheel.x_m = x_body_m;
                        wheel.steer_rad = steer_rad;
                        wheel.force_set.rolling_n = mu_roll * fn_w;
                        wheel.force_set.brake_n = mu_brake_w * fn_w;
                        wheel.force_set.lateral_n = mu_lat * fn_w;
                        // Slip-angle law as lateral compliance, from the start-of-step rolling
                        // speed of the wheel.
                        const double v_long_wheel =
                            std::abs(v_long * std::cos(steer_rad) +
                                     (v_lat + r0 * x_body_m) * std::sin(steer_rad));
                        const double c_alpha = kTireCorneringStiffnessPerFn * fn_w;
                        wheel.lateral_compliance_s_per_kg =
                            (c_alpha > 0.0) ? v_long_wheel / c_alpha : 0.0;
                        return wheel;
                    };
                    const std::array<solver::Wheel, 2> wheels{
                        make_wheel(kWheelContactNoseX, kWheelFnNoseFrac, nws_steer_rad, 0.0),
                        make_wheel(kWheelContactMainX, kWheelFnMainFrac, 0.0, mu_brake),
                    };
                    const solver::TangentialResult<2> tangential = solver::solve_tangential_contact(
                        solver::PlanarBody{m, inv_izz}, dt, u_free, wheels);

                    // Apply summed forces in world frame.
                    forces[i].add_force(
                        tangential.force_forward_n * fwd_x + tangential.force_left_n * left_x,
                        tangential.force_forward_n * fwd_y + tangential.force_left_n * left_y, 0.0);
                    if (has_rotation) {
                        forces[i].add_torque(0.0, 0.0, tangential.torque_yaw_nm);
                    }

                    // 4. Gear attitude constraints, evaluated on the end-of-step pitch/roll and
                    // rate under RotationalIntegrate's update (Euler kinematics with the other
                    // body rates at their start-of-step values).
                    if (has_rotation) {
                        const double phi = Math::to_radians(transform[i].roll);
                        const double theta = Math::to_radians(transform[i].pitch);
                        const double c_phi = std::cos(phi);
                        const double s_phi = std::sin(phi);
                        const double t_theta = std::tan(theta);
                        const double p0 = ang_vel->p;
                        const double q0 = ang_vel->q;
                        const double r_end = u_free[2] + dt * inv_izz * tangential.torque_yaw_nm;

                        solver::ImplicitAxis pitch_axis;
                        pitch_axis.inverse_inertia =
                            (inertia->iyy > 0.0) ? 1.0 / inertia->iyy : 0.0;
                        pitch_axis.dt_s = dt;
                        pitch_axis.angle_rad = theta;
                        pitch_axis.rate_rad_s = q0;
                        pitch_axis.other_torque_nm = forces[i].torque_pitch;
                        pitch_axis.angle_rate_gain = c_phi;
                        pitch_axis.angle_rate_bias = -r_end * s_phi;
                        const double pitch_torque = solver::solve_implicit_axis_torque(
                            pitch_axis, [](double pitch1, double q1) {
                                return gear_pitch_law_torque(pitch1, q1);
                            });

                        const double q_end = q0 + dt * pitch_axis.inverse_inertia *
                                                      (forces[i].torque_pitch + pitch_torque);
                        solver::ImplicitAxis roll_axis;
                        roll_axis.inverse_inertia = (inertia->ixx > 0.0) ? 1.0 / inertia->ixx : 0.0;
                        roll_axis.dt_s = dt;
                        roll_axis.angle_rad = phi;
                        roll_axis.rate_rad_s = p0;
                        roll_axis.other_torque_nm = forces[i].torque_roll;
                        roll_axis.angle_rate_gain = 1.0;
                        roll_axis.angle_rate_bias = (q_end * s_phi + r_end * c_phi) * t_theta;
                        const double roll_torque = solver::solve_implicit_axis_torque(
                            roll_axis, [](double roll1, double p1) {
                                return gear_roll_law_torque(roll1, p1);
                            });

                        forces[i].add_torque(roll_torque, pitch_torque, 0.0);
                    }
                }
            }
        });
}
