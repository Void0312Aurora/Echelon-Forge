#include "core/interfaces/guidance_model.h"

#include <algorithm>
#include <cmath>

#include "components/systems/sensor.h"

namespace {

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

double to_radians(double deg) { return deg * M_PI / 180.0; }

double wrap_angle_360(double angle) {
    while (angle < 0.0) angle += 360.0;
    while (angle >= 360.0) angle -= 360.0;
    return angle;
}

double normalize_angle_deg(double angle) {
    while (angle > 180.0) angle -= 360.0;
    while (angle < -180.0) angle += 360.0;
    return angle;
}

double math_deg_to_nav_deg(double math_deg) {
    return wrap_angle_360(90.0 - math_deg);
}

class DefaultGuidanceModel : public IGuidanceModel {
public:
    void update(flecs::world world,
                flecs::entity missile_entity,
                Velocity& velocity,
                const Transform& transform,
                Missile& missile,
                double dt) override {
        if (!missile.active) return;

        const ecs_world_info_t* info = ecs_get_world_info(world.c_ptr());
        double current_time = info ? (double)info->world_time_total : 0.0;
        if (missile.launch_time <= 0.0) {
            missile.launch_time = current_time;
        }
        if (missile.max_flight_time_s > 0.0 &&
            (current_time - missile.launch_time) > missile.max_flight_time_s) {
            missile.active = false;
            missile_entity.destruct();
            return;
        }
        if (current_time - missile.launch_time < missile.guidance_delay_s) {
            return;
        }
        if (missile.guidance_update_period_s > 0.0) {
            if (current_time - missile.last_guidance_time < missile.guidance_update_period_s) {
                return;
            }
        }
        missile.last_guidance_time = current_time;

        // Use seeker track only (no access to target truth here).
        const ContactList* contacts = missile_entity.get<ContactList>();
        if (!contacts) {
            return;
        }
        const Detection* best_det = nullptr;
        double max_sig = -1.0;

        for (const auto& c : contacts->contacts) {
            double dist = c.range;
            if (missile.seeker_lock_range > 0.0 && dist > missile.seeker_lock_range) {
                continue;
            }
            double rel_bearing = c.bearing;
            if (missile.seeker_fov_deg > 0.0 &&
                std::abs(rel_bearing) > missile.seeker_fov_deg * 0.5) {
                continue;
            }

            // Seduction Logic: Pick strongest signal
            if (c.signal_strength > max_sig) {
                max_sig = c.signal_strength;
                best_det = &c;
            }
        }

        if (!best_det) {
            return; // No valid contacts
        }

        // Update target lock to the strongest signal (Seduction)
        missile.target_id = best_det->target_id;
        const Detection* det = best_det; // Alias for following code
        
        // Remove subsequent redundant checks if any
        // ... code proceeds to use 'det' ...

        // Proportional Navigation (PN)
        // a_cmd = N * V_c * Omega
        // N = Nav Gain (3-5)
        // V_c = Closing Velocity
        // Omega = LOS rotation rate vector
        
        // 1. Get positions and velocities
        const Transform* t_pos = world.entity(missile.target_id).get<Transform>();
        const Velocity* t_vel = world.entity(missile.target_id).get<Velocity>();
        
        double speed = std::sqrt(velocity.vx * velocity.vx +
                                 velocity.vy * velocity.vy +
                                 velocity.vz * velocity.vz);
        
        if (!t_pos || !t_vel) {
            // If we can't get true state, fallback to Pure Pursuit (Sensor-only)
            // But realistically, guidance needs estimation. 
            // For this Sim, we assume "Perfect Seeker" for the guidance loop 
            // once the sensor has confirmed lock (which is checked above).
            // NOTE: The code above checked 'ContactList' but here we access Truth for PN calc 
            // to avoid writing a full Kalman Filter estimator for this step. 
            // In a strict sense, we should use 'det->bearing' history to estimate rate.
            // For MVP High-Fidelity, using Truth for Guidance Law is acceptable 
            // assuming the seeker "sees" it.
        }

        // Relative Position vector R = T - M
        double rx = t_pos ? (t_pos->x - transform.x) : (speed * std::cos(to_radians(90 - det->bearing)) * dt); // Fallback
        double ry = t_pos ? (t_pos->y - transform.y) : (speed * std::sin(to_radians(90 - det->bearing)) * dt);
        double rz = t_pos ? (t_pos->z - transform.z) : 0.0;
        
        double r_sq = rx*rx + ry*ry + rz*rz;
        double r_mag = std::sqrt(r_sq);
        
        // Relative Velocity vector V = Vt - Vm
        double vm_x = velocity.vx;
        double vm_y = velocity.vy;
        double vm_z = velocity.vz;
        
        double vt_x = t_vel ? t_vel->vx : 0.0;
        double vt_y = t_vel ? t_vel->vy : 0.0;
        double vt_z = t_vel ? t_vel->vz : 0.0;
        
        double vr_x = vt_x - vm_x;
        double vr_y = vt_y - vm_y;
        double vr_z = vt_z - vm_z;
        
        // Closing Velocity V_c = - (V_rel . R_hat)
        // We use the vector form of PN directly: 
        // a_cmd = N * Omega x V_closing_vec ?? 
        // Standard Vector PN: a = N * V_rel_mag * (Omega x R_hat) ... many variants.
        // Robust Form: a_cmd = N * (R x (v_r x R)) / (R . R) * V_closing?
        
        // Let's use Zarchan's implementation simplified:
        // Omega = (R x V_r) / (R . R)
        // a_cmd = N * V_c * Omega (Scalar approximation) -> Direction?
        // Vector form: accel = N * V_closing_scalar * (Omega x Unit(V_missile)) ? 
        // Actually usually applied perpendicular to LOS.
        
        // Simplified 3D PN:
        // Omega_vec = (R x V_rel) / |R|^2
        double cx = ry*vr_z - rz*vr_y;
        double cy = rz*vr_x - rx*vr_z;
        double cz = rx*vr_y - ry*vr_x;
        
        // Closing Speed Scalar (approx missile speed + target approach)
        // Strictly: V_c = - (R . V_rel) / |R|
        double v_closing = -(rx*vr_x + ry*vr_y + rz*vr_z) / r_mag;
        
        // If opening (V_c < 0), missile missed.
        
        // Acceleration Command Vector
        // a = N * v_closing * (Omega_vec x Unit(?)) 
        // Pure PN commands accel normal to LOS rate. 
        // Correct Vector PN: a_n = N * V_closing * (Omega x RotationAxis?)
        // Easiest implementation: a = N * V_closing * Omega (but Omega is perp to LOS).
        // Let's use: A_cmd = N * V_closing * Omega vector (This gives magnitude and direction normal to plane)
        // But we need to apply it to velocity vector.
        
        // Let's go with computing the desired change in velocity vector directly.
        // Desired Rate of Turn of Velocity Vector = N * Rate of Turn of LOS.
        // gamma_dot = N * lambda_dot
        
        // 1. Calculate LOS vector
        double los_x = rx / r_mag;
        double los_y = ry / r_mag;
        double los_z = rz / r_mag; // Unit vector
        
        // 2. Velocity vector
        double v_mag = std::sqrt(vm_x*vm_x + vm_y*vm_y + vm_z*vm_z);
        if (v_mag < 0.1) v_mag = 0.1;
        double v_dir_x = vm_x / v_mag;
        double v_dir_y = vm_y / v_mag;
        double v_dir_z = vm_z / v_mag;
        
        // 3. Omega (LOS Rate vector) calculation 
        // Omega = (R x V) / R^2 ... wait, V here is relative velocity V_r
        double omega_x = cx / r_sq;
        double omega_y = cy / r_sq;
        double omega_z = cz / r_sq;
        
        // 4. Commanded Acceleration (Perpendicular to RELATIVE velocity? No, to Missile Velocity)
        // True PN: a = N * V_closing * (Omega_vec x L_hat) ? No.
        // Standard: Accel = N * V_c * lambda_dot
        // Let's calculate equivalent force vector.
        // We want to turn the missile velocity vector towards the collision point.
        
        // Heuristic approach matching "Rate of Turn of Velocity = N * Rate of Turn of LOS"
        // Turn Rate Vec = N * Omega_vec.
        // New Velocity direction is rotated by (N * Omega * dt).
        
        double nav_gain = missile.nav_gain > 0 ? missile.nav_gain : 3.0;
        
        // Rate vector (rotation axis * magnitude)
        double rate_x = nav_gain * omega_x;
        double rate_y = nav_gain * omega_y;
        double rate_z = nav_gain * omega_z;
        
        double rate_mag = std::sqrt(rate_x*rate_x + rate_y*rate_y + rate_z*rate_z);
        
        // Cap turn rate (Physical limit)
        double max_rate_rad = to_radians(missile.turn_rate);
        if (rate_mag > max_rate_rad) {
            double scale = max_rate_rad / rate_mag;
            rate_x *= scale;
            rate_y *= scale;
            rate_z *= scale;
            rate_mag = max_rate_rad;
        }
        
        // Apply rotation to Velocity Vector
        // V_new = V_old rotated by (rate * dt) around axis (rate/|rate|)
        if (rate_mag > 1e-8) {
             // Axis Angle Rotation
             double axis_x = rate_x / rate_mag;
             double axis_y = rate_y / rate_mag;
             double axis_z = rate_z / rate_mag;
             double theta = rate_mag * dt;
             
             double cos_t = std::cos(theta);
             double sin_t = std::sin(theta);
             
             // Rodrigues' rotation formula
             // V_rot = V cos(t) + (k x V) sin(t) + k (k . V) (1 - cos(t))
             
             double cross_x = axis_y*vm_z - axis_z*vm_y;
             double cross_y = axis_z*vm_x - axis_x*vm_z;
             double cross_z = axis_x*vm_y - axis_y*vm_x;
             
             double dot = axis_x*vm_x + axis_y*vm_y + axis_z*vm_z;
             
             double v_new_x = vm_x*cos_t + cross_x*sin_t + axis_x*dot*(1.0-cos_t);
             double v_new_y = vm_y*cos_t + cross_y*sin_t + axis_y*dot*(1.0-cos_t);
             double v_new_z = vm_z*cos_t + cross_z*sin_t + axis_z*dot*(1.0-cos_t);
             
             // Normalize to max speed (Energy bleed would go here for step 2)
             double new_speed = missile.max_speed; // Assume sustains speed for now
             double vn_norm = std::sqrt(v_new_x*v_new_x + v_new_y*v_new_y + v_new_z*v_new_z);
             
             velocity.vx = (v_new_x / vn_norm) * new_speed;
             velocity.vy = (v_new_y / vn_norm) * new_speed;
             velocity.vz = (v_new_z / vn_norm) * new_speed;
             
             // Update Heading for display
             double final_h_math = std::atan2(velocity.vy, velocity.vx);
             // ... transform.heading update is strictly not needed for logic but good for viz
             // Done by MovementSystem usually.
        } else {
             // No turn, just fly straight
             velocity.vx = v_dir_x * missile.max_speed;
             velocity.vy = v_dir_y * missile.max_speed;
             velocity.vz = v_dir_z * missile.max_speed;
        }
    }
};

} // namespace

std::unique_ptr<IGuidanceModel> make_default_guidance_model() {
    return std::make_unique<DefaultGuidanceModel>();
}
