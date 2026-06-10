#pragma once

#include <flecs.h>
#include <cmath>
#include <iostream>
#include "components/basic/common.h"
#include "components/domains/air/command/control_input_resolution.h"
#include "components/physics/forces.h"
#include "components/physics/dynamics.h"
#include "components/systems/logistics.h"   // For GroundState
#include "components/physics/performance.h" // For LandingGear
#include "components/physics/control_law.h" // For ControlLawState (FBW filtered inputs)
#include "core/interfaces/environment_model.h"

namespace {
// Penalty Method Constants
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

// Tire model knobs (lightweight, training-stable):
// - Lateral force from slip angle with linear cornering stiffness and saturation at mu_lat * Fn.
// - Longitudinal rolling resistance as separate drag term (does not consume friction ellipse
// budget).
// - Braking uses Coulomb-style slip force and is coupled to lateral via a friction ellipse.
constexpr double kTireCorneringStiffnessPerFn =
    18.0;                                 // [N/rad] per [N] of normal load (dimensionless)
constexpr double kTireAlphaMaxDeg = 20.0; // Clamp slip angle to avoid low-speed blowups
constexpr double kTireVrefRollMps = 1.0;  // Smoothing speed for rolling resistance
constexpr double kTireVrefBrakeMps = 0.5; // Smoothing speed for braking force
constexpr double kEnvironmentScalarCanonicalQuantum = 0x1p-76;
constexpr double kHardLandingSinkRateMps = 9.0;
constexpr double kSevereImpactSinkRateMps = 15.0;
constexpr double kOffroadCrashSpeedMps = 45.0;
constexpr double kPavedCrashSpeedMps = 95.0;

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
} // namespace

/**
 * GroundContactSystem
 *
 * Implements a Penalty Method for ground interaction.
 * Integrates with EnvironmentModel for surface-dependent physics (Friction, Damage).
 */
inline void register_ground_contact_system(flecs::world &ecs, IEnvironmentModel *env) {
    ecs.system<ForceAccumulator, const Transform, Velocity, const Mass, GroundState>(
           "GroundContact")
        .kind(flecs::OnUpdate)
        // Must run BEFORE Integration but AFTER Aerodynamics
        .run([env](flecs::iter &it) {
            while (it.next()) {
                auto forces = it.field<ForceAccumulator>(0);
                auto transform = it.field<const Transform>(1);
                auto velocity = it.field<Velocity>(2);
                auto mass = it.field<const Mass>(3);
                auto ground = it.field<GroundState>(4);

                for (auto i : it) {
                    double m = mass[i].get_total_kg();
                    if (m < 1.0) m = 15000.0;
                    const double dt = std::max(1.0e-3, static_cast<double>(it.delta_time()));

                    // 1. Detection: Query Environment
                    // Use current position (x, y)
                    auto terrain = env->get_terrain_at(transform[i].x, transform[i].y);

                    double terrain_z = canonicalize_environment_scalar(terrain.elevation);
                    ground[i].terrain_elevation = terrain_z;

                    double z = transform[i].z;

                    // Contact height is model-specific and scales with extension state.
                    double gear_height = 2.0;
                    if (const LandingGear *lg = it.entity(i).get<LandingGear>()) {
                        const double ext = std::clamp(lg->extension_state, 0.0, 1.0);
                        gear_height = std::max(0.4, lg->contact_height_m) * ext;
                    }

                    double penetration = gear_height - (z - terrain_z);

                    bool is_touching = (penetration > 0.0);
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

                    // 2. Normal Force (Spring-Damper)
                    double f_spring = kGroundSpring * penetration;

                    double vz = velocity[i].vz;
                    double f_damper = -kGroundDamper * vz;

                    double Fn = std::max(0.0, f_spring + f_damper); // Unilateral

                    forces[i].add_force(0.0, 0.0, Fn);

                    // 2.5 Pitch Damping When On Ground
                    // Prevent uncontrolled pitch-up rotation on ground roll.
                    // The gear pivot creates a restoring moment that limits pitch.
                    // Acting like a torsional spring-damper on pitch.
                    const AngularVelocity *ang_vel = it.entity(i).get<AngularVelocity>();
                    if (ang_vel) {
                        double q_rate = ang_vel->q; // Pitch rate (rad/s)
                        double pitch_deg = transform[i].pitch;
                        double p_rate = ang_vel->p; // Roll rate (rad/s)
                        double roll_deg = transform[i].roll;

                        // Ground pitch limit: ~10 degrees (rotation attitude)
                        // Stiffness must exceed aerodynamic control moment.
                        // Control: ~60 * q * 0.8 @ q=3000 -> 144,000 Nm
                        // We need restoring > 144,000 at 10 deg -> Kp > 825,000/rad
                        double kp_pitch = 2000000.0; // 2 MNm per radian
                        double kd_pitch = 200000.0;  // 200 kNm per rad/s

                        // Allow a realistic ground rotation attitude (~10 deg) before the gear
                        // constraint starts resisting further pitch-up. This prevents the previous
                        // behavior where the aircraft was effectively "pinned" near 2 deg pitch and
                        // required unrealistically high takeoff speeds/ground-roll distances to
                        // lift off.
                        constexpr double kGroundPitchFreeDeg = 10.0;

                        if (pitch_deg > kGroundPitchFreeDeg) {
                            const double err_deg = pitch_deg - kGroundPitchFreeDeg;
                            const double restoring_torque = -kp_pitch * Math::to_radians(err_deg);
                            const double damping_torque = -kd_pitch * q_rate;
                            forces[i].add_torque(0.0, restoring_torque + damping_torque, 0.0);
                        } else if (std::abs(q_rate) > 0.01) {
                            // Just damping for small angles
                            forces[i].add_torque(0.0, -kd_pitch * q_rate, 0.0);
                        }

                        // Ground roll/gear constraint: prevent unrealistic banking on the runway.
                        // Without this, small roll-stick errors can accumulate to >30deg roll while
                        // still "on ground", which is physically impossible with landing gear
                        // contact and ruins takeoff training.
                        double kp_roll = 2000000.0; // 2 MNm per radian
                        double kd_roll = 200000.0;  // 200 kNm per rad/s
                        double abs_roll = std::abs(roll_deg);
                        if (abs_roll > 2.0) {
                            double restoring = -kp_roll * Math::to_radians(roll_deg);
                            double damping = -kd_roll * p_rate;
                            forces[i].add_torque(restoring + damping, 0.0, 0.0);
                        } else if (std::abs(p_rate) > 0.01) {
                            forces[i].add_torque(-kd_roll * p_rate, 0.0, 0.0);
                        }
                    }

                    // 3. Friction & Surface Interaction
                    double vx = velocity[i].vx;
                    double vy = velocity[i].vy;
                    double v_h_sq = vx * vx + vy * vy;
                    double v_h = std::sqrt(std::max(0.0, v_h_sq));
                    const double sink_rate_mps = std::max(0.0, -velocity[i].vz);
                    ground[i].impact_horizontal_speed_mps = v_h;
                    ground[i].impact_sink_rate_mps = sink_rate_mps;

                    double gear_mu_roll = 0.02; // Default paved-surface rolling coefficient
                    if (const LandingGear *lg = it.entity(i).get<LandingGear>()) {
                        gear_mu_roll = std::max(0.0, lg->rolling_friction_coeff);
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
                    if (ground[i].lifecycle != GroundImpactLifecycle::CrashedWreck &&
                        ground[i].lifecycle != GroundImpactLifecycle::DebrisFragmentResidue) {
                        ground[i].lifecycle = severe_impact ? GroundImpactLifecycle::CrashedWreck
                                                            : GroundImpactLifecycle::LandedAirframe;
                    }
                    const ResolvedAirControlInput control_input = resolve_air_control_input(
                        it.entity(i).get<PilotAction>(),
                        it.entity(i).get<MissionCommandControlState>(), nullptr);
                    const ResolvedGroundControlInput ground_control = control_input.ground_control;
                    bool throttle_idle = ground_control.throttle_idle;
                    double brake_amount = ground_control.brake_amount;

                    if (v_h_sq > 0.001) {
                        // --- Gear State Update ---
                        // Track whether on paved surface and accumulate stress if off-road at speed
                        GearState *gear = it.entity(i).get_mut<GearState>();
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

                                // Stress rate: (v - 40) / 60 * severity → ~1.0/s at 100 m/s on
                                // SoftDirt
                                double dt = it.delta_time();
                                gear->stress_rate = severity * (v_h - 40.0) / 60.0;
                                gear->stress += gear->stress_rate * dt;

                                // Increase friction to simulate digging in
                                mu_rolling *= (1.0 + 4.0 * gear->stress); // Up to 5x at collapse

                                // Check for collapse
                                if (gear->stress >= 1.0) {
                                    gear->collapsed = true;
                                    ground[i].lifecycle = GroundImpactLifecycle::CrashedWreck;
                                    ground[i].impact_severity =
                                        std::max(ground[i].impact_severity, 1.0);
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
                            if (const ControlLawState *ctl = it.entity(i).get<ControlLawState>()) {
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
                                if (const LandingGear *lg = it.entity(i).get<LandingGear>()) {
                                    gear_extended = (lg->extension_state >= 0.5);
                                }
                                if (gear_extended) {
                                    double speed_factor =
                                        std::clamp(v_h / kNwsMinSpeedMps, 0.0, 1.0);
                                    double fade = 1.0;
                                    if (v_h >= kNwsFadeStartMps) {
                                        double t = (v_h - kNwsFadeStartMps) /
                                                   (kNwsFadeEndMps - kNwsFadeStartMps);
                                        t = std::clamp(t, 0.0, 1.0);
                                        // Fade down to a small residual steering authority instead
                                        // of zero. Many aircraft retain a limited pedal->nosewheel
                                        // linkage at higher speeds.
                                        fade = (1.0 - t) * (1.0 - kNwsHighSpeedFrac) +
                                               kNwsHighSpeedFrac;
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
                        if (throttle_idle && v_h < 10.0) {
                            brake_amount = std::max(brake_amount, 1.0);
                        }

                        // Rolling resistance (drag) and braking (slip) are treated separately.
                        // Rolling resistance should not reduce lateral grip (no friction ellipse
                        // coupling).
                        double mu_roll = mu_rolling;
                        double mu_brake = std::clamp(brake_amount, 0.0, 1.0) * kMuBraking;

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

                        // Resolve velocity into body-forward / body-left components using heading.
                        const double hdg_rad = Math::to_radians(transform[i].heading);
                        const double fwd_x = std::sin(hdg_rad);
                        const double fwd_y = std::cos(hdg_rad);
                        // Note: The sim's body frame uses +Y = LEFT (consistent with AeroState
                        // world_to_body).
                        const double left_x = -std::cos(hdg_rad);
                        const double left_y = std::sin(hdg_rad);
                        const double v_long = vx * fwd_x + vy * fwd_y;
                        const double v_lat_comp = vx * left_x + vy * left_y;

                        auto smooth_coulomb = [](double v, double mu_in, double Fn_in,
                                                 double v_ref) {
                            if (Fn_in <= 0.0 || mu_in <= 0.0) return 0.0;
                            v_ref = std::max(v_ref, 1e-3);
                            const double s = std::tanh(v / v_ref); // smooth sign
                            return -mu_in * Fn_in * s;
                        };

                        // Wheel-based tire forces (apply at effective contact points so yaw moments
                        // emerge naturally).
                        const double alpha_max = Math::to_radians(kTireAlphaMaxDeg);
                        const double Fn_nose = Fn * kWheelFnNoseFrac;
                        const double Fn_main = Fn * kWheelFnMainFrac;

                        // Yaw rate (body frame). Used to compute contact patch lateral velocity v =
                        // v_cg + r*x.
                        double r = 0.0;
                        if (const AngularVelocity *ang_vel = it.entity(i).get<AngularVelocity>()) {
                            r = ang_vel->r;
                        }

                        auto apply_wheel = [&](double x_body_m, double Fn_w, double steer_rad,
                                               double mu_brake_w, double &f_long_sum,
                                               double &f_lat_sum, double &tau_yaw_sum) {
                            if (Fn_w <= 0.0) return;

                            // Local slip velocity at wheel contact (body forward/left).
                            const double v_long_w = v_long;
                            const double v_lat_w = v_lat_comp + r * x_body_m;

                            const double c = std::cos(steer_rad);
                            const double s = std::sin(steer_rad);

                            // Wheel-frame velocities (forward/left)
                            const double v_long_wf = v_long_w * c + v_lat_w * s;
                            const double v_lat_wf = -v_long_w * s + v_lat_w * c;

                            // Longitudinal: rolling resistance (drag) + braking (slip)
                            const double fx_roll =
                                smooth_coulomb(v_long_wf, mu_roll, Fn_w, kTireVrefRollMps);
                            double fx_brake = 0.0;
                            if (mu_brake_w > 1e-6) {
                                fx_brake =
                                    smooth_coulomb(v_long_wf, mu_brake_w, Fn_w, kTireVrefBrakeMps);
                            }

                            // Lateral: slip angle with cornering stiffness, saturated at mu_lat*Fn
                            double alpha = std::atan2(v_lat_wf, std::abs(v_long_wf) + 1e-3);
                            alpha = std::clamp(alpha, -alpha_max, alpha_max);
                            const double C_alpha = kTireCorneringStiffnessPerFn * Fn_w;
                            double fy = -C_alpha * alpha;
                            const double fy_max = mu_lat * Fn_w;
                            if (fy_max > 0.0) {
                                fy = std::clamp(fy, -fy_max, fy_max);
                            } else {
                                fy = 0.0;
                            }

                            // Friction ellipse coupling (braking vs lateral). Rolling resistance is
                            // excluded.
                            if (mu_brake_w > 1e-6 && fy_max > 1e-6) {
                                const double fx_max = (mu_brake_w * Fn_w);
                                const double ux = fx_brake / std::max(fx_max, 1e-6);
                                const double uy = fy / std::max(fy_max, 1e-6);
                                const double u = std::sqrt(ux * ux + uy * uy);
                                if (u > 1.0) {
                                    fx_brake /= u;
                                    fy /= u;
                                }
                            }

                            const double fx_wf = fx_roll + fx_brake;
                            const double fy_wf = fy;

                            // Rotate wheel forces back to body (forward/left)
                            const double fx_b = fx_wf * c - fy_wf * s;
                            const double fy_b = fx_wf * s + fy_wf * c;

                            f_long_sum += fx_b;
                            f_lat_sum += fy_b;
                            tau_yaw_sum += x_body_m * fy_b;
                        };

                        double f_long_sum = 0.0;
                        double f_lat_sum = 0.0;
                        double tau_yaw = 0.0;

                        // Brakes primarily act on main gear; nose wheel is treated as unbraked for
                        // realism.
                        apply_wheel(kWheelContactNoseX, Fn_nose, nws_steer_rad, 0.0, f_long_sum,
                                    f_lat_sum, tau_yaw);
                        apply_wheel(kWheelContactMainX, Fn_main, 0.0, mu_brake, f_long_sum,
                                    f_lat_sum, tau_yaw);

                        // Apply summed forces in world frame.
                        const double fx = f_long_sum * fwd_x + f_lat_sum * left_x;
                        const double fy = f_long_sum * fwd_y + f_lat_sum * left_y;

                        forces[i].add_force(fx, fy, 0.0);
                        forces[i].add_torque(0.0, 0.0, tau_yaw);

                        // Low-speed stop-hold:
                        // Coulomb braking alone leaves a long tail of tiny rollout velocities,
                        // especially after landing in wind. When brakes are held and thrust is
                        // idle, use a bounded static-friction style hold force to settle the
                        // aircraft to a full stop instead of letting it creep.
                        if (throttle_idle && brake_amount > 0.2 && v_h < 3.0) {
                            const double hold_force_max = std::max(0.0, 1.20 * Fn);
                            const double hold_force_need = (m * v_h) / dt;
                            const double hold_force = std::min(hold_force_need, hold_force_max);
                            if (hold_force > 0.0 && v_h > 1.0e-6) {
                                const double inv_v = 1.0 / v_h;
                                forces[i].add_force(-vx * inv_v * hold_force,
                                                    -vy * inv_v * hold_force, 0.0);
                            }
                            if (v_h < 0.25) {
                                velocity[i].vx = 0.0;
                                velocity[i].vy = 0.0;
                            }
                        }

                        // 4. Yaw stability is handled implicitly by wheel contact forces/moments
                        // above.
                    } else {
                        // Static stiction (simplified)
                        if (throttle_idle && std::abs(vx) < 0.25 && std::abs(vy) < 0.25) {
                            velocity[i].vx = 0.0;
                            velocity[i].vy = 0.0;
                        }
                    }
                }
            }
        });
}
