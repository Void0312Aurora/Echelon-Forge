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
            gear_cmd_down = (pilot->gear_handle > 0.5);
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

        if (forces && ang_vel) {
            // Aerodynamic Authority Scaling (Dynamic Pressure)
            // For MVP: Constant max torque + Damping
            // In reality: Torque ~ q * S * l * Deflection
            
            double max_roll_torque = 500000.0;
            double max_pitch_torque = 500000.0;
            double max_yaw_torque = 200000.0;
            
            double damping_roll = 40000.0; 
            double damping_pitch = 60000.0;
            double damping_yaw = 40000.0;

            forces->add_torque(
                stick_roll * max_roll_torque - ang_vel->p * damping_roll,
                stick_pitch * max_pitch_torque - ang_vel->q * damping_pitch, 
                stick_yaw * max_yaw_torque - ang_vel->r * damping_yaw
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
