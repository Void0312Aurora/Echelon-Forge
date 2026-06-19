#include "core/interfaces/control_model.h"
#include "core/interfaces/environment_model.h"

#include "components/command/common/mission_command_control_state.h"
#include "components/physics/performance.h"
#include "components/command/mission_command.h"
#include "components/command/pilot_action.h"
#include "components/physics/control_law.h"
#include "components/physics/control_surface.h"
#include "components/physics/instruments.h"
#include "components/domains/air/platform/flight_dynamics_tuning.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/systems/logistics.h"
#include "components/combat/health.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>

namespace {

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

double normalize_angle(double angle) {
    while (angle > 180.0)
        angle -= 360.0;
    while (angle < -180.0)
        angle += 360.0;
    return angle;
}

double to_degrees(double rad) {
    return rad * 180.0 / M_PI;
}
double to_radians(double deg) {
    return deg * M_PI / 180.0;
}

bool pilot_action_requests_manual_takeover(const PilotAction &pilot) {
    constexpr double kPrimaryAxisDeadband = 0.05;
    return std::abs(pilot.stick_roll) > kPrimaryAxisDeadband ||
           std::abs(pilot.stick_pitch) > kPrimaryAxisDeadband ||
           std::abs(pilot.rudder) > kPrimaryAxisDeadband;
}

bool is_runway_like_surface(IControlModel::IEnvironmentModel::SurfaceType surface) {
    return surface == IControlModel::IEnvironmentModel::SurfaceType::Concrete ||
           surface == IControlModel::IEnvironmentModel::SurfaceType::Asphalt;
}

double landing_bank_limit_deg(const MissionCommand &mission) {
    switch (mission.recovery_approach_type) {
    case RecoveryApproachType::ILS:
        return 18.0;
    case RecoveryApproachType::Visual:
        return 24.0;
    case RecoveryApproachType::Overhead:
        return 30.0;
    case RecoveryApproachType::TACAN:
        return 20.0;
    case RecoveryApproachType::StraightIn:
        return 20.0;
    case RecoveryApproachType::None:
    default:
        return 22.0;
    }
}

double landing_heading_reference_deg(const MissionCommand &mission, const Transform &transform,
                                     IControlModel::IEnvironmentModel *env_model) {
    if (env_model) {
        const auto terrain = env_model->get_terrain_at(transform.x, transform.y);
        if (is_runway_like_surface(terrain.type) && std::isfinite(terrain.runway_heading)) {
            double hdg = std::fmod(terrain.runway_heading, 360.0);
            if (hdg < 0.0) hdg += 360.0;
            return hdg;
        }
    }
    // Fallback: until the kernel carries richer recovery geometry, treat the
    // terminal cmd heading as the baked recovery-program reference.
    return mission.cmd_heading_deg;
}

enum class FbwProtectionMode {
    Strict,
    Relaxed,
    Off,
};

FbwProtectionMode get_fbw_protection_mode() {
    static FbwProtectionMode cached = []() {
        const char *v = std::getenv("CMO_FBW_PROTECTION_MODE");
        if (!v) return FbwProtectionMode::Strict;
        const std::string s(v);
        if (s == "off" || s == "OFF" || s == "0") return FbwProtectionMode::Off;
        if (s == "relaxed" || s == "RELAXED" || s == "1") return FbwProtectionMode::Relaxed;
        return FbwProtectionMode::Strict;
    }();
    return cached;
}

class DefaultControlModel : public IControlModel {
  public:
    void update(flecs::world /*world*/, flecs::entity entity, Velocity &velocity,
                Transform &transform, const FlightModel &flight_model, double dt,
                IEnvironmentModel *env_model) override {

        // --- 1. Get Inputs ---
        const PilotAction *pilot = entity.get<PilotAction>();
        const MissionCommand *mission = entity.get<MissionCommand>();
        const MissionCommandControlState *control_state = entity.get<MissionCommandControlState>();

        // Synthesized controls (inputs to the physical actuators)
        double stick_roll = 0.0;
        double stick_pitch = 0.0;
        double stick_yaw = 0.0;
        bool gear_cmd_down = false;

        const bool pilot_active = (pilot && pilot->active);
        bool has_pilot = pilot_active && pilot_action_requests_manual_takeover(*pilot);
        bool has_mission = (mission && mission->active);
        const bool has_control_state = (control_state && control_state->lagged_active);
        const auto *ground_state = entity.get<GroundState>();
        const bool on_ground_hint = ground_state ? ground_state->on_ground : false;

        // --- 2. Determine Source of Control (Autopilot vs Manual) ---
        if (has_pilot) {
            // [A] Manual / RL Control
            stick_roll = pilot->stick_roll;
            stick_pitch = pilot->stick_pitch;
            // Sign convention: PilotAction.rudder > 0 means "nose right" (heading increases).
            // In the sim's NAV heading convention, positive yaw rate/torque decreases heading (left
            // turn), so we invert here to keep the PilotAction interface physically meaningful.
            stick_yaw = -pilot->rudder;
            // Treat the midpoint as "down" so an untrained policy (often near action midpoints)
            // doesn't retract the gear on the runway.
            gear_cmd_down = (pilot->gear_handle >= 0.5);
        } else if (has_mission) {
            // [B] Mission-command autopilot.
            // Interpret cmd_* according to command_code semantics rather than treating
            // them as globally free heading/altitude/speed parameters.
            const int command_code = mission->command_code;
            const bool is_route_command = (command_code == 3);
            const bool is_landing_command = (command_code == 4);

            const double current_heading_deg = transform.heading;
            const double current_track_deg =
                Math::ground_track_deg_from_velocity(velocity.vx, velocity.vy, current_heading_deg);
            double reference_heading_deg = mission->cmd_heading_deg;
            double lateral_reference_deg = current_heading_deg;
            double bank_limit_deg = 60.0;
            double heading_to_bank_gain = 2.0;
            double bank_to_stick_gain = 0.05;
            double altitude_to_pitch_gain = 0.1;
            double pitch_min_deg = -15.0;
            double pitch_max_deg = 20.0;
            double pitch_to_stick_gain = 0.1;

            if (is_route_command) {
                // Route/LNAV uses target_heading as a track bug.
                lateral_reference_deg = current_track_deg;
                bank_limit_deg = 45.0;
            } else if (is_landing_command) {
                // Landing/final is a terminal recovery program. Keep the aircraft configured
                // for recovery and use a much gentler terminal gain schedule.
                reference_heading_deg =
                    landing_heading_reference_deg(*mission, transform, env_model);
                bank_limit_deg = landing_bank_limit_deg(*mission);
                if (on_ground_hint) {
                    bank_limit_deg = std::min(bank_limit_deg, 8.0);
                }
                heading_to_bank_gain = 1.0;
                bank_to_stick_gain = 0.04;
                altitude_to_pitch_gain = 0.05;
                pitch_min_deg = on_ground_hint ? -2.0 : -8.0;
                pitch_max_deg = on_ground_hint ? 5.0 : 12.0;
                pitch_to_stick_gain = 0.08;
                gear_cmd_down = true;
            } else if (command_code == 1) {
                bank_limit_deg = 30.0;
                heading_to_bank_gain = 1.4;
            }

            const double heading_err =
                normalize_angle(reference_heading_deg - lateral_reference_deg);
            // Navigation heading increases clockwise, while the rotational system maps a positive
            // bank/yaw coordination into decreasing heading. Convert the heading error into the
            // physical bank sign expected by the control-surface path.
            const double target_bank =
                std::clamp(-heading_err * heading_to_bank_gain, -bank_limit_deg, bank_limit_deg);
            const double bank_err = target_bank - transform.roll;
            stick_roll = std::clamp(bank_err * bank_to_stick_gain, -1.0, 1.0);

            const double alt_err = mission->cmd_altitude_m - transform.z;
            const double target_pitch =
                std::clamp(alt_err * altitude_to_pitch_gain, pitch_min_deg, pitch_max_deg);
            const double pitch_err = target_pitch - transform.pitch;
            stick_pitch = std::clamp(pitch_err * pitch_to_stick_gain, -1.0, 1.0);

            // Yaw/coordination is handled by the FBW / SAS later in the pipeline.
            stick_yaw = 0.0;

            if (!is_landing_command) {
                const double speed =
                    std::sqrt(velocity.vx * velocity.vx + velocity.vy * velocity.vy +
                              velocity.vz * velocity.vz);
                if (speed < 100.0 || (transform.z < 200.0 && mission->cmd_altitude_m < 500.0)) {
                    gear_cmd_down = true;
                } else {
                    gear_cmd_down = false;
                }
            }
        } else if (has_control_state) {
            const double heading_err =
                normalize_angle(control_state->lagged_heading_deg - transform.heading);
            const double target_bank = std::clamp(-heading_err * 2.0, -45.0, 45.0);
            const double bank_err = target_bank - transform.roll;
            stick_roll = std::clamp(bank_err * 0.05, -1.0, 1.0);

            const double alt_err = control_state->lagged_altitude_m - transform.z;
            const double target_pitch = std::clamp(alt_err * 0.1, -15.0, 20.0);
            const double pitch_err = target_pitch - transform.pitch;
            stick_pitch = std::clamp(pitch_err * 0.1, -1.0, 1.0);

            stick_yaw = 0.0;
            const double speed = std::sqrt(velocity.vx * velocity.vx + velocity.vy * velocity.vy +
                                           velocity.vz * velocity.vz);
            gear_cmd_down = (speed < 100.0 ||
                             (transform.z < 200.0 && control_state->lagged_altitude_m < 500.0));
        } else {
            // [C] No Command (Stability Augmentation / Dampener only)
            // Inputs remain 0.0, SAS will dampen rates below
        }

        // --- 3. Apply PHYSICAL Torques (Fly-By-Wire) ---
        auto *forces = entity.get_mut<ForceAccumulator>();
        const auto *ang_vel = entity.get<AngularVelocity>();
        const auto *aero = entity.get<AeroState>();
        const auto *ground = entity.get<GroundState>();

        if (forces && ang_vel && aero) {
            // SAS/FBW: rate-command with sensor-based protections.
            // This module is part of the aircraft system (realistic), but it must not use any
            // non-physical "god" information (e.g., runway heading vectors). Only sensor-like
            // signals (rates, AoA, pitch, WOW) are used here.

            auto lpf = [](double prev, double input, double dt_in, double tau_s) {
                if (tau_s <= 0.0) return input;
                double a = dt_in / (tau_s + dt_in);
                return prev + a * (input - prev);
            };

            auto &ctl = entity.ensure<ControlLawState>();

            // Filter pilot demands to emulate stick/actuator dynamics (prevents high-frequency
            // PIO).
            constexpr double kStickTauS = 0.15; // ~150 ms
            ctl.stick_roll_filt = lpf(ctl.stick_roll_filt, stick_roll, dt, kStickTauS);
            ctl.stick_pitch_filt = lpf(ctl.stick_pitch_filt, stick_pitch, dt, kStickTauS);
            ctl.stick_yaw_filt = lpf(ctl.stick_yaw_filt, stick_yaw, dt, kStickTauS);

            const double stick_roll_f = std::clamp(ctl.stick_roll_filt, -1.0, 1.0);
            const double stick_pitch_f = std::clamp(ctl.stick_pitch_filt, -1.0, 1.0);
            const double stick_yaw_f = std::clamp(ctl.stick_yaw_filt, -1.0, 1.0);

            const bool on_ground = ground ? ground->on_ground : false;
            // Ground directional-control protection:
            // At high speed on the runway, full-scale rudder pedal input should not directly map
            // to max yaw commands (prevents runway departure from a single saturated action).
            // This acts like a mechanical/FBW limit schedule and uses only physical state.
            const FbwProtectionMode fbw_mode = get_fbw_protection_mode();
            const bool rl_mode = has_pilot;
            const bool fbw_relaxed_for_rl = rl_mode && (fbw_mode == FbwProtectionMode::Relaxed);
            const bool fbw_off_for_rl = rl_mode && (fbw_mode == FbwProtectionMode::Off);

            double stick_yaw_cmd = stick_yaw_f;
            if (on_ground && !fbw_off_for_rl) {
                const double v_h = std::sqrt(velocity.vx * velocity.vx + velocity.vy * velocity.vy);
                constexpr double kYawLimitStartMps = 5.0;
                constexpr double kYawLimitEndMps = 80.0;
                constexpr double kYawMaxLowSpeed = 1.0;
                constexpr double kYawMaxHighSpeed = 0.35;
                constexpr double kYawMaxHighSpeedRelaxed = 0.60;
                double t = 0.0;
                if (v_h > kYawLimitStartMps) {
                    t = (v_h - kYawLimitStartMps) / (kYawLimitEndMps - kYawLimitStartMps);
                    t = std::clamp(t, 0.0, 1.0);
                }
                const double yaw_high =
                    fbw_relaxed_for_rl ? kYawMaxHighSpeedRelaxed : kYawMaxHighSpeed;
                const double yaw_max = kYawMaxLowSpeed + t * (yaw_high - kYawMaxLowSpeed);
                stick_yaw_cmd = std::clamp(stick_yaw_cmd, -yaw_max, yaw_max);
            }
            ctl.stick_yaw_cmd = stick_yaw_cmd;

            // Stick -> desired body rates (rad/s)
            constexpr double kPMaxRadS = 1.2; // roll rate
            constexpr double kQMaxRadS = 0.8; // pitch rate
            constexpr double kRMaxRadS = 0.8; // yaw rate

            double p_cmd = stick_roll_f * kPMaxRadS;
            double q_cmd = stick_pitch_f * kQMaxRadS;
            double r_cmd = stick_yaw_cmd * kRMaxRadS;

            // Pitch-axis g-command outer loop (F-16-style normal-acceleration
            // command). With the physical-surface path a neutral stick that only
            // damps pitch rate cannot sustain level flight: a statically stable
            // airframe trims toward zero AoA, sinks, and diverges. Instead, map
            // stick to a commanded normal load factor (center = 1 g) and close
            // the loop on the measured Nz (InstrumentState.g_load_normal, a
            // sensor-like signal from the previous frame) to synthesize the
            // pitch-rate command. The inner rate loop and every envelope
            // protection below are unchanged. Airborne and FBW-on only; on the
            // ground or with FBW off we keep the direct rate command so takeoff
            // rotation and the RL "off" mode behave exactly as before.
            const AeroTuning *pitch_tuning_attached = entity.get<AeroTuning>();
            const AeroTuning &pitch_tuning =
                (pitch_tuning_attached && pitch_tuning_attached->enabled)
                    ? *pitch_tuning_attached
                    : flight_dynamics::default_aero_tuning();
            if (pitch_tuning.fbw_g_command_enabled && !on_ground && !fbw_off_for_rl) {
                const double g_neutral = pitch_tuning.fbw_g_command_neutral;
                double g_cmd = g_neutral;
                if (stick_pitch_f >= 0.0) {
                    g_cmd =
                        g_neutral + stick_pitch_f * (pitch_tuning.fbw_g_command_max - g_neutral);
                } else {
                    g_cmd =
                        g_neutral + (-stick_pitch_f) * (pitch_tuning.fbw_g_command_min - g_neutral);
                }
                double measured_nz = g_neutral;
                if (const InstrumentState *inst = entity.get<InstrumentState>()) {
                    measured_nz = inst->g_load_normal;
                }
                if (!std::isfinite(measured_nz)) {
                    measured_nz = g_neutral;
                }
                q_cmd = pitch_tuning.fbw_pitch_rate_per_g_err * (g_cmd - measured_nz);
                q_cmd = std::clamp(q_cmd, -kQMaxRadS, kQMaxRadS);
                ctl.dbg_g_cmd = g_cmd;
                ctl.dbg_measured_nz = measured_nz;
                ctl.dbg_q_cmd = q_cmd;
                ctl.dbg_g_branch_active = 1.0;
            } else {
                ctl.dbg_g_branch_active = 0.0;
            }

            // F-16-style directional stability augmentation with turn coordination:
            // - feed-forward the body yaw rate required for a coordinated turn at the
            //   current bank angle, r_turn = (g/V) * sin(phi) * cos(theta);
            // - damp sideslip (beta) back toward zero;
            // - damp yaw-rate ERROR relative to the coordinated rate, not the absolute
            //   rate, so the damper no longer fights the natural turn yaw rate (which
            //   was the source of the roll-induced sideslip).
            // This uses only physical state (bank, pitch, speed, beta, yaw rate) and
            // prevents RL or scripted policies from turning rudder exploration into an
            // unrecoverable dutch-roll / slip oscillation, while keeping pure-stick
            // banked turns coordinated (beta ~ 0).
            if (!on_ground && !fbw_off_for_rl) {
                const double beta_rad = to_radians(aero->sideslip_angle);
                const double phi_rad = to_radians(transform.roll);
                const double theta_rad = to_radians(transform.pitch);
                const double speed =
                    std::sqrt(velocity.vx * velocity.vx + velocity.vy * velocity.vy +
                              velocity.vz * velocity.vz);
                const double v_eff = std::max(50.0, speed);
                // Manual/RL stick inputs expose the physical control-surface
                // sign directly: a positive internal rudder command drives beta
                // negative, so negative beta needs a negative rudder correction
                // instead of the pre-refactor direct-torque sign. The mission
                // autopilot path keeps the coordinated-turn feed-forward used by
                // the existing cruise/heading guards; those commands are already
                // generated as bank-to-heading guidance rather than raw roll
                // exploration.
                const double r_turn = (9.80665 / v_eff) * std::sin(phi_rad) * std::cos(theta_rad);
                double beta_gain = 2.0;
                double yaw_rate_gain = 0.55;
                if (fbw_relaxed_for_rl) {
                    beta_gain *= 0.7;
                    yaw_rate_gain *= 0.7;
                }
                if (rl_mode) {
                    r_cmd += (beta_gain * beta_rad) - (yaw_rate_gain * ang_vel->r);
                } else {
                    r_cmd +=
                        r_turn + (-beta_gain * beta_rad) + (-yaw_rate_gain * (ang_vel->r - r_turn));
                }
                r_cmd = std::clamp(r_cmd, -kRMaxRadS, kRMaxRadS);
            }

            // Ground rotation/attitude protection (tailstrike/PIO reduction).
            if (on_ground && !fbw_off_for_rl) {
                constexpr double kPitchSoftDeg = 8.0;
                constexpr double kPitchHardDeg = 12.0;
                const double protect_gain = fbw_relaxed_for_rl ? 0.45 : 1.0;
                if (transform.pitch > kPitchSoftDeg && q_cmd > 0.0) {
                    double t = (transform.pitch - kPitchSoftDeg) / (kPitchHardDeg - kPitchSoftDeg);
                    double scale = 1.0 - protect_gain * std::clamp(t, 0.0, 1.0);
                    q_cmd *= scale;
                }
                if (transform.pitch > kPitchHardDeg) {
                    const double q_hard = fbw_relaxed_for_rl ? -0.08 : -0.2;
                    q_cmd = std::min(q_cmd, q_hard);
                }
            }

            // Airborne pitch-attitude protection: prevent unrealistic near-vertical attitudes that
            // frequently destabilize RL training (and are outside normal takeoff envelopes).
            // This is a realistic FBW-style limit schedule using only physical state.
            if (!on_ground && !fbw_off_for_rl) {
                constexpr double kPitchSoftDeg = 60.0;
                constexpr double kPitchHardDeg = 80.0;
                const double protect_gain = fbw_relaxed_for_rl ? 0.55 : 1.0;
                if (transform.pitch > kPitchSoftDeg && q_cmd > 0.0) {
                    double t = (transform.pitch - kPitchSoftDeg) / (kPitchHardDeg - kPitchSoftDeg);
                    double scale = 1.0 - protect_gain * std::clamp(t, 0.0, 1.0);
                    q_cmd *= scale;
                }
                constexpr double kPitchRecoverySoftDeg = 35.0;
                if (transform.pitch > kPitchRecoverySoftDeg && stick_pitch_f < -0.05) {
                    const double t = std::clamp((transform.pitch - kPitchRecoverySoftDeg) /
                                                    (kPitchHardDeg - kPitchRecoverySoftDeg),
                                                0.0, 1.0);
                    const double base_recovery_q = fbw_relaxed_for_rl ? -0.14 : -0.22;
                    const double extra_recovery_q = fbw_relaxed_for_rl ? -0.08 : -0.18;
                    q_cmd = std::min(q_cmd, base_recovery_q + extra_recovery_q * t);
                }
                if (transform.pitch > kPitchHardDeg) {
                    const double q_hard = fbw_relaxed_for_rl ? -0.16 : -0.35;
                    q_cmd = std::min(q_cmd, q_hard);
                }
            }

            // AoA limiter (envelope protection) to prevent deep-stall / departure behavior.
            // Use |AoA| so both positive and negative departures are handled.
            const double alpha_deg = aero->angle_of_attack;
            const double alpha_abs = std::abs(alpha_deg);
            constexpr double kAoASoftDeg = 10.0;
            constexpr double kAoAHardDeg = 18.0;
            if (!fbw_off_for_rl && alpha_abs > kAoASoftDeg) {
                double t = (alpha_abs - kAoASoftDeg) / (kAoAHardDeg - kAoASoftDeg);
                const double protect_gain = fbw_relaxed_for_rl ? 0.50 : 1.0;
                double scale = 1.0 - protect_gain * std::clamp(t, 0.0, 1.0);
                q_cmd *= scale;
            }
            if (!fbw_off_for_rl && alpha_abs > kAoAHardDeg) {
                // Hard recovery: unload the wing with a pitch-down command when AoA is excessive.
                const double q_hard = fbw_relaxed_for_rl ? -0.06 : -0.15;
                q_cmd = std::min(q_cmd, q_hard);
            }

            // Rate-command fly-by-wire, realized through physical control surfaces.
            // The law converts each axis rate error into a normalized surface
            // command; the actuator system lags it into an actual deflection, and
            // the aerodynamics system turns deflection into a moment scaled by
            // dynamic pressure and Mach. This replaces the previous direct
            // q_bar*gain torque synthesis so control authority emerges from the
            // same aero path as the rest of the moments (and so battle damage can
            // act on surface effectiveness rather than on a synthetic torque).
            //
            // Gains are chosen so a moderate rate error saturates the surface,
            // giving a crisp rate-command response. Authority at takeoff q_bar is
            // preserved by the elevator effectiveness derivative (see AeroTuning),
            // not by these gains.
            // Inner-loop rate-command gains (rate error [rad/s] -> normalized
            // surface command). These must stay low enough that normal maneuver
            // rate errors keep the surface in its LINEAR range. With the physical
            // actuator lag (per-frame step dt/(tau+dt) ~= 0.33) a hot proportional
            // gain turns the surface into a bang-bang relay and the lagged loop
            // limit-cycles (pitch PIO that couples into roll and departs). Tuned
            // so a full-scale rate error gives roughly full deflection, leaving
            // partial deflection for the typical sub-scale errors, so the body's
            // natural Cm_q / Cl_p / Cn_r damping closes a well-damped loop.
            constexpr double kRollCmdGain = 1.2;
            constexpr double kPitchCmdGain = 0.9;
            constexpr double kYawCmdGain = 1.2;

            auto &surfaces = entity.ensure<ControlSurfaceState>();
            const double aileron_cmd = std::clamp(kRollCmdGain * (p_cmd - ang_vel->p), -1.0, 1.0);
            surfaces.aileron_cmd = aileron_cmd;
            surfaces.elevator_cmd = std::clamp(kPitchCmdGain * (q_cmd - ang_vel->q), -1.0, 1.0);
            ctl.dbg_q_cmd_final = q_cmd;
            ctl.dbg_elevator_cmd = surfaces.elevator_cmd;

            // Aileron-rudder interconnect (ARI): feed the aileron command forward
            // into the rudder to cancel adverse yaw at its source, the way a real
            // FBW system does. The reactive beta/yaw-rate damper above only
            // corrects sideslip after it appears, and with the physical actuator
            // lag on the rudder that reactive-only loop leaves a real, smoothly
            // growing sideslip during sustained rolling. The interconnect is a
            // pure feed-forward from a physical command (no god state). Manual/RL
            // roll commands use the beta-correcting physical-surface sign above;
            // mission/autopilot bank commands keep the existing coordinated-turn
            // sign convention for cruise stability.
            double rudder_cmd = kYawCmdGain * (r_cmd - ang_vel->r);
            if (!on_ground && !fbw_off_for_rl) {
                const AeroTuning *attached_tuning = entity.get<AeroTuning>();
                const AeroTuning &ari_tuning = (attached_tuning && attached_tuning->enabled)
                                                   ? *attached_tuning
                                                   : flight_dynamics::default_aero_tuning();
                double ari_gain = ari_tuning.ari_rudder_cmd_per_aileron_cmd;
                if (fbw_relaxed_for_rl) {
                    ari_gain *= 0.7;
                }
                if (rl_mode) {
                    rudder_cmd -= ari_gain * aileron_cmd;
                } else {
                    rudder_cmd += ari_gain * aileron_cmd;
                }
            }
            surfaces.rudder_cmd = std::clamp(rudder_cmd, -1.0, 1.0);
        }

        // --- 4. Secondary Systems (Gear) ---
        LandingGear *gear = entity.get_mut<LandingGear>();
        if (gear) {
            // Realism: squat-switch interlock prevents inadvertent gear retraction on ground.
            // This keeps the takeoff roll stable without introducing any non-physical ("god") info.
            if (const GroundState *g = entity.get<GroundState>(); g && g->on_ground) {
                gear_cmd_down = true;
            }
            double rate = 1.0 / (gear->transit_time_s > 0 ? gear->transit_time_s : 5.0);
            if (gear_cmd_down)
                gear->extension_state += rate * dt;
            else
                gear->extension_state -= rate * dt;
            gear->extension_state = std::clamp(gear->extension_state, 0.0, 1.0);
        }
    };
};

} // namespace

std::unique_ptr<IControlModel> make_default_control_model() {
    return std::make_unique<DefaultControlModel>();
}
