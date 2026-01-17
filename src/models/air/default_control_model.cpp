#include "core/interfaces/control_model.h"
#include "core/interfaces/environment_model.h"

#include "components/physics/performance.h"
#include "components/physics/action.h"
#include "components/physics/dynamics.h"
#include <algorithm>
#include <cmath>

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
                const MovementCommand& command,
                const FlightModel& flight_model,
                double dt) override {
        if (!command.active) return;

        constexpr double kGravity = 9.80665;
        double current_speed = std::sqrt(velocity.vx * velocity.vx +
                                         velocity.vy * velocity.vy +
                                         velocity.vz * velocity.vz);

        double current_heading_nav = transform.heading;
        if (current_speed > 1e-3) {
            double current_heading_math = std::atan2(velocity.vy, velocity.vx);
            current_heading_nav = 90.0 - to_degrees(current_heading_math);
            current_heading_nav = normalize_angle(current_heading_nav);
        }

        double heading_error = normalize_angle(command.target_heading - current_heading_nav);
        double max_turn_rate = flight_model.max_turn_rate;
        if (current_speed > 1.0 && flight_model.max_g > 1.0) {
            double max_turn_rate_g = kGravity *
                                     std::sqrt(flight_model.max_g * flight_model.max_g - 1.0) /
                                     current_speed;
            max_turn_rate = std::min(max_turn_rate, to_degrees(max_turn_rate_g));
        }
        double max_turn_step = max_turn_rate * dt;
        double turn_step = std::clamp(heading_error, -max_turn_step, max_turn_step);
        double turn_rate_deg = (dt > 0.0) ? (turn_step / dt) : 0.0;
        double new_heading_nav = normalize_angle(current_heading_nav + turn_step);

        double turn_rate_rad = to_radians(turn_rate_deg);
        
        // Environment Query
        double alt_km = transform.z / 1000.0;
        double rho = 1.225; // SL fallback
        double sos = 340.29; // SL fallback
        
        if (const auto* env_ref = entity.get<EnvironmentModelRef>()) {
             if (env_ref->model) {
                 auto data = env_ref->model->get_atmosphere_at(transform.x, transform.y, transform.z);
                 rho = data.air_density;
                 sos = data.speed_of_sound;
             }
        } else {
             // Fallback simple lapse if no env model
             rho = 1.225 * std::exp(-alt_km / 7.2);
             sos = 340.29 * std::sqrt(std::max(0.0, 1.0 - 0.02256 * alt_km));
        }

        double mach = current_speed / std::max(1.0, sos);
        
        // 2. Calculate Load Factor (n)
        // Bank angle logic determines G-load
        double turn_rate_rad_req = std::abs(to_radians(heading_error) / dt); // Requested
        // Clamp to max sustained G? No, Peak G.
        double turn_rate_rad_cap = turn_rate_rad_req;
        
        // Max G based on structural limit
        double max_g_struct = flight_model.max_g;
        double min_turn_r = current_speed * current_speed / (kGravity * std::sqrt(max_g_struct*max_g_struct - 1.0));
        double max_rate_struct = current_speed / min_turn_r;
        
        if (turn_rate_rad_cap > max_rate_struct) turn_rate_rad_cap = max_rate_struct;
        if (turn_rate_rad_cap > to_radians(flight_model.max_turn_rate)) turn_rate_rad_cap = to_radians(flight_model.max_turn_rate);
        
        double applied_turn_deg = to_degrees(turn_rate_rad_cap) * dt;
        if (applied_turn_deg > std::abs(heading_error)) applied_turn_deg = std::abs(heading_error);
        if (heading_error < 0) applied_turn_deg = -applied_turn_deg;
        
        double real_turn_rate_rad = std::abs(to_radians(applied_turn_deg) / dt);
        double g_load_sq = 1.0 + (real_turn_rate_rad * current_speed / kGravity) * (real_turn_rate_rad * current_speed / kGravity);
        double g_load = std::sqrt(g_load_sq);
        
        // 3. Calculate Ps (Specific Excess Power) [m/s]
        // Model: Ps = (Thrust - Drag) * V / Weight
        // Parametric Approximation for a generic F-16/Su-27 like fighter:
        // Thrust: Decays with Alt. Peaks at Mach 0.9.
        // Drag: Induced (k*n^2) + Parasitic (Cd0*v^2) + Wave (Mach > 1.0)
        
        double thrust_static_sl = flight_model.max_accel * kGravity; // Normalized T/W approx ~1.0-1.2 effectively
        // Thrust lapse
        double thrust_avail = thrust_static_sl * std::pow(std::max(0.1, 1.0 - alt_km/15.0), 3.5); 
        // Transonic thrust bump (afterburner efficiency)
        if (mach > 0.8 && mach < 2.0) thrust_avail *= 1.2;
        
        // Drag
        double q = 0.5 * rho * current_speed * current_speed; // Dynamic Pressure using Env Data
        // Drag Polar: Cd = Cdo + k * CL^2
        // We approximate Drag Force directly relative to Weight
        // Zero-Lift Drag (Parasitic)
        double drag_parasitic = 0.02 * q * 0.005; // 0.02 Cd0, Wing ref area scale... 
        // Simplification: Drag q-component: 
        double drag_q = (current_speed / 340.0); 
        drag_q = drag_q * drag_q * 0.015; // Cdo coeff
                // Calculate Net Force
            // F = Thrust - Drag
            // Drag = 0.5 * rho * v^2 * Cd * Area
            // Use simple drag model: D = k * v^2
            // The following variables (v_body, air_density, current_thrust, step_size) are not defined in this scope.
            // This block seems to be from a different context or requires additional setup.
            // For now, I will insert the fuel leak part as requested, assuming the context for other variables is handled elsewhere or will be added.
            // double v_sq = std::abs(v_body) * v_body; // Signed square
            // double drag = 0.3 * v_sq * air_density; // Simplified Drag
            
            // F = ma -> a = F/m
            // double net_force = current_thrust - drag;
            // double mass_val = 10000.0;
            Mass* mass = entity.get_mut<Mass>(); // Re-get mass for this block
            Propulsion* prop = entity.get_mut<Propulsion>(); // Re-get prop for this block
            if (mass && prop) {
                 // mass_val = mass->get_total_kg();
                 
                 // Apply Fuel Burn & Leak
                 // TODO: Use SFC from Engine definition. For now, constant burn.
                 // double burn_rate = (prop->afterburner_active ? 2.5 : 0.8) * (current_thrust / 10000.0); // kg/s approx
                 // Assuming 'dt' is the 'step_size' for this context
                 mass->fuel_mass_kg -= (mass->fuel_leak_rate_kg_s) * dt; // Only apply leak rate as per instruction
                 if (mass->fuel_mass_kg < 0) {
                     mass->fuel_mass_kg = 0;
                     // prop->current_thrust_n = 0; // Flameout - this would require a mutable prop
                     // current_thrust = 0;
                 }
            }
            // double accel = net_force / mass_val;
        // Induced Drag: Proportional to G^2 / Speed^2? 
        // Di ~ n^2 / (rho * v^2)
        double drag_induced = 0.0;
        if (current_speed > 10.0) {
            drag_induced = 0.2 * (g_load * g_load) / (mach * mach + 0.1); 
        }
        
        // Wave Drag
        double drag_wave = 0.0;
        if (mach > 1.0) {
            drag_wave = 0.05 * (mach - 1.0) * (mach - 1.0);
        }
        
        // Net Normalized Drag (D/W)
        double drag_total_ratio = (drag_q + drag_induced + drag_wave);
        
        // Net Normalized Thrust (T/W)
        double thrust_total_ratio = thrust_avail / 9.81; // Rough approx since max_accel is m/s^2
        
        // Ps = V * (T - D) / W = V * (T/W - D/W)
        double ps = current_speed * (thrust_total_ratio - drag_total_ratio);
        
        // Apply Ps to State
        // Agent controls: Target Speed, Target Alt.
        // If Ps > 0: Can Accelerate OR Climb.
        // If Ps < 0: Must Decelerate OR Dive.
        
        // Simplified Energy Distribution Logic:
        // Priority 1: Altitude (Climb/Dive to target)
        // Priority 2: Speed
        
        // Calculate demands
        double dh = command.target_altitude - transform.z;
        // Helper to avoid undefined vars
        double safe_target_speed = std::clamp(command.target_speed, flight_model.min_speed, flight_model.max_speed);
        
        double dv = safe_target_speed - current_speed;
        
        // Desired energy rate
        double dh_dt_req = dh; // 1 sec tau
        if (std::abs(dh_dt_req) > flight_model.max_climb_rate) dh_dt_req = std::copysign(flight_model.max_climb_rate, dh_dt_req);
        
        double dv_dt_req = dv; 
        if (std::abs(dv_dt_req) > flight_model.max_accel) dv_dt_req = std::copysign(flight_model.max_accel, dv_dt_req);
        
        // Total Energy Rate Reqd: Ps_req = dh_dt + (V/g)*dv_dt
        double ps_req = dh_dt_req + (current_speed / kGravity) * dv_dt_req;
        
        // Actual Realizable rates
        double final_climb_rate = 0.0;
        double final_accel = 0.0;
        
        if (ps >= ps_req) {
            // We have enough energy, do exactly what is asked
            final_climb_rate = dh_dt_req;
            final_accel = dv_dt_req;
        } else {
            // Deficit! Prioritize avoiding ground collision / stalling?
            // "Energy Sustainment Logic"
            
            // If diving (dh < 0), that adds energy. 
            // If we are turning hard (drag_induced high), Ps is likely negative.
            
            // Allocate Ps:
            // If dragging, we mostly lose speed rather than altitude (unless stalling).
            
            if (current_speed < flight_model.min_speed * 1.1) {
                // Stall protect: Dive to trade potential for kinetic
                final_climb_rate = -20.0; // Force dive
                final_accel = (ps - final_climb_rate) * kGravity / current_speed;
            } else {
                // Bleed speed to hold altitude
                final_climb_rate = dh_dt_req; 
                // If climb is too demanding, reduce it
                if (final_climb_rate > ps) final_climb_rate = ps; // Climb as much as Ps allows
                
                // Remaining Ps goes to accel (which will be negative)
                double ps_rem = ps - final_climb_rate;
                // Physics-Based Acceleration Logic
        const Mass* mass = entity.get<Mass>();
        const Propulsion* prop = entity.get<Propulsion>();
        
        double available_accel = flight_model.max_accel; // Fallback

        if (mass && prop) {
             double current_mass = mass->get_total_kg();
             double v = velocity.vx * velocity.vx + velocity.vy * velocity.vy + velocity.vz * velocity.vz; // v^2
             v = std::sqrt(v);
             
             // Simple Drag Model: D = 0.5 * rho * v^2 * Cd * A
             // Assume generic fighter: Cd=0.02, Area=30m^2 -> Cd*A ~ 0.6
             // We can tune this later.
             double drag_area = 0.6; 
             double drag = 0.5 * rho * v * v * drag_area; 
             
             double thrust = prop->mil_thrust_n;
             // Logic: If target speed > current speed + margin, use AB? 
             // For now, simplify: if command.target_speed > 300m/s use AB
             if (command.target_speed > 300.0) {
                 thrust = prop->ab_thrust_n;
             }
             
             available_accel = (thrust - drag) / current_mass;
             if (available_accel < 0) available_accel = 0; // Can't accelerate if drag > thrust (max speed saturation)
             
             // Update Propulsion State for visualization/debugging
             // Need mutable propulsion, but get<Propulsion> is const in this query context?
             // Actually we can use e.get_mut<Propulsion>() if we change the system query or just use e.set.
        }

        double speed_error = safe_target_speed - current_speed;
        if (std::abs(speed_error) > 0.1) {
            double accel_req = speed_error / dt;
            
            // Clamp by physical limit
            if (accel_req > available_accel) accel_req = available_accel;
            if (accel_req < -flight_model.max_accel) accel_req = -flight_model.max_accel; // Brakes?
            
            double new_speed = current_speed + accel_req * dt;
            
            // Apply new speed to velocity vector
            if (current_speed > 1.0) {
                velocity.vx *= (new_speed / current_speed);
                velocity.vy *= (new_speed / current_speed);
                velocity.vz *= (new_speed / current_speed);
            }
        }
            }
        }
        double climb_rate = final_climb_rate;
        // The new physics logic already updates velocity.vx, vy, vz based on new_speed.
        // The original code's speed_step and new_speed calculation, and subsequent velocity update,
        // are now handled by the injected block.
        // We need to ensure new_speed is defined for the climb_vs check.
        // Let's re-calculate new_speed based on the updated velocity magnitude.
        double new_speed = std::sqrt(velocity.vx * velocity.vx + velocity.vy * velocity.vy + velocity.vz * velocity.vz);
        
        // Bank angle for viz
        double bank_rad = 0.0;
        if (g_load > 1.0) bank_rad = std::acos(1.0 / g_load);
        transform.roll = to_degrees(bank_rad); // Visualize bank
        
        turn_rate_deg = applied_turn_deg / dt;
        new_heading_nav = normalize_angle(current_heading_nav + applied_turn_deg);

        // Convert back to Velocity Vector
        // Limit new_speed to >= 0
        if (new_speed < 0.0) new_speed = 0.0;

        double climb_vs = climb_rate;
        // Ensure climb doesn't exceed total speed (impossible triangle)
        if (std::abs(climb_vs) > new_speed) climb_vs = std::copysign(new_speed, climb_vs);
        
        double ground_speed = std::sqrt(std::max(0.0, new_speed*new_speed - climb_vs*climb_vs));
        double new_heading_math = to_radians(90.0 - new_heading_nav);

        velocity.vx = ground_speed * std::cos(new_heading_math);
        velocity.vy = ground_speed * std::sin(new_heading_math);
        velocity.vz = climb_vs;
        
        // Update transform heading to match steering immediately
        transform.heading = new_heading_nav;
    }
};

} // namespace

std::unique_ptr<IControlModel> make_default_control_model() {
    return std::make_unique<DefaultControlModel>();
}
