#include "core/interfaces/control_model.h"
#include "core/interfaces/environment_model.h"

#include "components/physics/performance.h"
#include "components/physics/action.h"
#include "components/physics/control_law.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/systems/logistics.h"
#include "components/combat/health.h"
#include <spdlog/spdlog.h>
#include <algorithm>
#include <cmath>
#include <iostream>

namespace {

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

double normalize_angle(double angle) {
    while (angle > 180.0) angle -= 360.0;
    while (angle < -180.0) angle += 360.0;
    return angle;
}

double to_degrees(double rad) { return rad * 180.0 / M_PI; }
double to_radians(double deg) { return deg * M_PI / 180.0; }

class DefaultControlModel : public IControlModel {
public:
    void update(flecs::world /*world*/,
                flecs::entity entity,
                Velocity& velocity,
                Transform& transform,
                const FlightModel& flight_model,
                double dt,
                IEnvironmentModel* env_model) override {
        
        // --- 1. Get Inputs ---
        const PilotAction* pilot = entity.get<PilotAction>();
        const MissionCommand* mission = entity.get<MissionCommand>();
        
        // Synthesized controls (inputs to the physical actuators)
        double stick_roll = 0.0;
        double stick_pitch = 0.0;
        double stick_yaw = 0.0;
        bool gear_cmd_down = false;

        bool has_pilot = (pilot && pilot->active);
        bool has_mission = (mission && mission->active);

        // --- 2. Determine Source of Control (Autopilot vs Manual) ---
        if (has_pilot) {
            // [A] Manual / RL Control
            stick_roll = pilot->stick_roll;
            stick_pitch = pilot->stick_pitch;
            // Sign convention: PilotAction.rudder > 0 means "nose right" (heading increases).
            // In the sim's NAV heading convention, positive yaw rate/torque decreases heading (left turn),
            // so we invert here to keep the PilotAction interface physically meaningful.
            stick_yaw = -pilot->rudder;
            // Treat the midpoint as "down" so an untrained policy (often near action midpoints)
            // doesn't retract the gear on the runway.
            gear_cmd_down = (pilot->gear_handle >= 0.5);
        } 
        else if (has_mission) {
            // [B] Legacy Autopilot (Rule-Based Helper)
            //     Goal: Translate Mission (Heading/Alt/Speed) -> Stick Inputs (Roll/Pitch)
            
            // B.1 Heading -> Roll -> Stick Roll
            double current_heading = transform.heading; // Magnetic
            double heading_err = normalize_angle(mission->cmd_heading_deg - current_heading);
            
            // Simple P-Controller for Bank Angle
            double target_bank = std::clamp(heading_err * 2.0, -60.0, 60.0);
            double bank_err = target_bank - transform.roll;
            stick_roll = std::clamp(bank_err * 0.05, -1.0, 1.0); // kP = 0.05
            
            // B.2 Altitude -> Pitch -> Stick Pitch
            double alt_err = mission->cmd_altitude_m - transform.z;
            double target_pitch = std::clamp(alt_err * 0.1, -15.0, 20.0);
            double pitch_err = target_pitch - transform.pitch;
            stick_pitch = std::clamp(pitch_err * 0.1, -1.0, 1.0); // kP = 0.1
            
            // B.3 Yaw (Coordination)
            stick_yaw = 0.0; // Assume auto-coordination or fly-by-wire handles it
            
            // B.4 Config (Gear)
            // Retract gear if speed > 100 m/s or alt > 200m
            double speed = std::sqrt(velocity.vx*velocity.vx + velocity.vy*velocity.vy + velocity.vz*velocity.vz);
            if (speed < 100.0 || (transform.z < 200.0 && mission->cmd_altitude_m < 500.0)) {
                 gear_cmd_down = true; 
            } else {
                 gear_cmd_down = false;
            }
        }
        else {
            // [C] No Command (Stability Augmentation / Dampener only)
            // Inputs remain 0.0, SAS will dampen rates below
        }

        // --- 3. Apply PHYSICAL Torques (Fly-By-Wire) ---
        auto* forces = entity.get_mut<ForceAccumulator>();
        const auto* ang_vel = entity.get<AngularVelocity>();
        const auto* aero = entity.get<AeroState>();
        const auto* ground = entity.get<GroundState>();

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

            auto& ctl = entity.ensure<ControlLawState>();

            // Filter pilot demands to emulate stick/actuator dynamics (prevents high-frequency PIO).
            constexpr double kStickTauS = 0.15; // ~150 ms
	            ctl.stick_roll_filt = lpf(ctl.stick_roll_filt, stick_roll, dt, kStickTauS);
	            ctl.stick_pitch_filt = lpf(ctl.stick_pitch_filt, stick_pitch, dt, kStickTauS);
	            ctl.stick_yaw_filt = lpf(ctl.stick_yaw_filt, stick_yaw, dt, kStickTauS);

	            const double stick_roll_f = std::clamp(ctl.stick_roll_filt, -1.0, 1.0);
	            const double stick_pitch_f = std::clamp(ctl.stick_pitch_filt, -1.0, 1.0);
	            const double stick_yaw_f = std::clamp(ctl.stick_yaw_filt, -1.0, 1.0);

	            const bool on_ground = ground ? ground->on_ground : false;
	            const double q_bar = std::max(0.0, aero->dynamic_pressure);
	            // Limit effective dynamic pressure for control authority scheduling at high speed.
	            // Prevents unrealistically stiff controls and training instabilities.
	            const double q_bar_eff = std::min(q_bar, 9000.0);

	            // Ground directional-control protection:
	            // At high speed on the runway, full-scale rudder pedal input should not directly map
	            // to max yaw commands (prevents runway departure from a single saturated action).
	            // This acts like a mechanical/FBW limit schedule and uses only physical state.
	            double stick_yaw_cmd = stick_yaw_f;
	            if (on_ground) {
	                const double v_h = std::sqrt(velocity.vx * velocity.vx + velocity.vy * velocity.vy);
	                constexpr double kYawLimitStartMps = 5.0;
	                constexpr double kYawLimitEndMps = 80.0;
	                constexpr double kYawMaxLowSpeed = 1.0;
	                constexpr double kYawMaxHighSpeed = 0.35;
	                double t = 0.0;
	                if (v_h > kYawLimitStartMps) {
	                    t = (v_h - kYawLimitStartMps) / (kYawLimitEndMps - kYawLimitStartMps);
	                    t = std::clamp(t, 0.0, 1.0);
	                }
	                const double yaw_max = kYawMaxLowSpeed + t * (kYawMaxHighSpeed - kYawMaxLowSpeed);
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

	            // Ground rotation/attitude protection (tailstrike/PIO reduction).
	            if (on_ground) {
	                constexpr double kPitchSoftDeg = 8.0;
	                constexpr double kPitchHardDeg = 12.0;
	                if (transform.pitch > kPitchSoftDeg && q_cmd > 0.0) {
	                    double t = (transform.pitch - kPitchSoftDeg) / (kPitchHardDeg - kPitchSoftDeg);
	                    double scale = 1.0 - std::clamp(t, 0.0, 1.0);
	                    q_cmd *= scale;
	                }
	                if (transform.pitch > kPitchHardDeg) {
	                    q_cmd = std::min(q_cmd, -0.2);
	                }
	            }
	
	            // Airborne pitch-attitude protection: prevent unrealistic near-vertical attitudes that
	            // frequently destabilize RL training (and are outside normal takeoff envelopes).
	            // This is a realistic FBW-style limit schedule using only physical state.
	            if (!on_ground) {
	                constexpr double kPitchSoftDeg = 60.0;
	                constexpr double kPitchHardDeg = 80.0;
	                if (transform.pitch > kPitchSoftDeg && q_cmd > 0.0) {
	                    double t = (transform.pitch - kPitchSoftDeg) / (kPitchHardDeg - kPitchSoftDeg);
	                    double scale = 1.0 - std::clamp(t, 0.0, 1.0);
	                    q_cmd *= scale;
	                }
	                if (transform.pitch > kPitchHardDeg) {
	                    q_cmd = std::min(q_cmd, -0.2);
	                }
	            }

	            // AoA limiter (envelope protection) to prevent deep-stall / departure behavior.
	            // Use |AoA| so both positive and negative departures are handled.
	            const double alpha_deg = aero->angle_of_attack;
	            const double alpha_abs = std::abs(alpha_deg);
	            constexpr double kAoASoftDeg = 10.0;
	            constexpr double kAoAHardDeg = 18.0;
	            if (alpha_abs > kAoASoftDeg) {
	                double t = (alpha_abs - kAoASoftDeg) / (kAoAHardDeg - kAoASoftDeg);
	                double scale = 1.0 - std::clamp(t, 0.0, 1.0);
	                q_cmd *= scale;
	            }
	            if (alpha_abs > kAoAHardDeg) {
	                // Hard recovery: unload the wing with a pitch-down command when AoA is excessive.
	                q_cmd = std::min(q_cmd, -0.15);
	            }

            // Rate-command control moments: M = q_bar * K * (rate_cmd - rate)
            // Gains are tuned so that at takeoff q_bar (~3000 Pa) we can rotate a ~15t aircraft.
            constexpr double kRollGain = 40.0;
            constexpr double kPitchGain = 60.0;
            constexpr double kYawGain = 20.0;

            const double tau_roll = (p_cmd - ang_vel->p) * (kRollGain * q_bar_eff);
            const double tau_pitch = (q_cmd - ang_vel->q) * (kPitchGain * q_bar_eff);
            const double tau_yaw = (r_cmd - ang_vel->r) * (kYawGain * q_bar_eff);

            forces->add_torque(tau_roll, tau_pitch, tau_yaw);
        }


	        // --- 4. Secondary Systems (Gear) ---
	        LandingGear* gear = entity.get_mut<LandingGear>();
	        if (gear) {
	             // Realism: squat-switch interlock prevents inadvertent gear retraction on ground.
	             // This keeps the takeoff roll stable without introducing any non-physical ("god") info.
	             if (const GroundState* g = entity.get<GroundState>(); g && g->on_ground) {
	                 gear_cmd_down = true;
	             }
	             double rate = 1.0 / (gear->transit_time_s > 0 ? gear->transit_time_s : 5.0);
	             if (gear_cmd_down) gear->extension_state += rate * dt;
	             else gear->extension_state -= rate * dt;
	             gear->extension_state = std::clamp(gear->extension_state, 0.0, 1.0);
	        }
	    };
};

} // namespace

std::unique_ptr<IControlModel> make_default_control_model() {
    return std::make_unique<DefaultControlModel>();
}
