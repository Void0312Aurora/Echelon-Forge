#include "core/interfaces/control_model.h"
#include "core/interfaces/environment_model.h"

#include "components/physics/performance.h"
#include "components/physics/action.h"
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
            stick_yaw = pilot->rudder;
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

        if (forces && ang_vel && aero) {
            // Aerodynamic Authority Scaling
            // Torque = Coeff * q * deflection
            // We tune 'Coeff' s.t. at rotation speed (Vr ~ 70 m/s, q ~ 3000 Pa) we have enough torque to rotate.
            // Requirement: Rotate 15000kg aircraft with gear 1m behind CG.
            // Weight Moment ~ 15000 * 9.8 * 1.0 ~ 150,000 Nm.
            // So at q=3000, Torque should be > 150,000.
            // Coeff_pitch = 150,000 / 3000 = 50.0.
            
            // To be safe and allow crisp handling:
            double q_bar = aero->dynamic_pressure;
            
            // Limit q_bar for numerical stability at very low speeds (though 0 is fine for 0 torque)
            // But lets clamp max q for "stiffening" at high speed if needed (fly-by-wire Limiter)
            // For now, pure physical scaling.
            
            double scaling_roll = 40.0 * q_bar;  
            double scaling_pitch = 60.0 * q_bar; // 60 * 3000 = 180,000 Nm @ 70m/s
            double scaling_yaw = 20.0 * q_bar;
            
            // Damping also scales with q? Or standard rotational damping?
            // Standard damping is usually proportional to speed or constant "friction".
            // Aerodynamic damping (Cm_q) scales with q and velocity.
            // For MVP, we stick to constant damping or linear speed damping, 
            // but let's keep the existing damping constants for stability first, 
            // maybe scale them slightly with speed? 
            // Existing: 40000. Let's keep them constant for now to dampen the "spring" effect of high torque.
            
            double damping_roll = 40000.0; 
            double damping_pitch = 60000.0;
            double damping_yaw = 40000.0;

            forces->add_torque(
                stick_roll * scaling_roll - ang_vel->p * damping_roll,
                stick_pitch * scaling_pitch - ang_vel->q * damping_pitch, 
                stick_yaw * scaling_yaw - ang_vel->r * damping_yaw
            );
        }


        // --- 4. Secondary Systems (Gear) ---
        LandingGear* gear = entity.get_mut<LandingGear>();
        if (gear) {
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
