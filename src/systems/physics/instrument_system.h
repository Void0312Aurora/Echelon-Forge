#pragma once

#include <flecs.h>
#include <cmath>
#include <algorithm>
#include "components/basic/common.h"
#include "components/physics/instruments.h"
#include "components/physics/action.h"       // MissionCommand
#include "components/physics/forces.h"       // AeroState, ForceAccumulator, AngularVelocity
#include "components/physics/dynamics.h"     // Mass, Propulsion
#include "components/systems/ew.h"           // RWR
#include "components/combat/weapon.h"        // Ammo
#include "core/interfaces/environment_model.h"

namespace {
    inline double inst_rad_to_deg(double rad) { return rad * 180.0 / M_PI; }
    
    // Body Frame acceleration projection
    // Returns [ax, ay, az] in body frame
    inline Math::Vector3 project_forces_to_body(const Math::Vector3& f_world, const Transform& val) {
        // Yaw(psi), Pitch(theta), Roll(phi)
        double psi = Math::to_radians(90.0 - val.heading);
        double theta = Math::to_radians(val.pitch);
        double phi = Math::to_radians(val.roll);
        
        double c_psi = std::cos(psi);
        double s_psi = std::sin(psi);
        double c_theta = std::cos(theta);
        double s_theta = std::sin(theta);
        // double c_phi = std::cos(phi);
        // double s_phi = std::sin(phi);
        
        double fx = f_world.x;
        double fy = f_world.y;
        double fz = f_world.z;
        
        // Rotate Z (Un-Yaw)
        double x1 =  fx * c_psi + fy * s_psi;
        double y1 = -fx * s_psi + fy * c_psi;
        double z1 =  fz;

        // Rotate Y (Un-Pitch)
        double x2 =  x1 * c_theta + z1 * s_theta;
        double y2 =  y1;
        double z2 = -x1 * s_theta + z1 * c_theta;

        // Rotate X (Un-Roll)
        // We only really care about Normal (Az) and Axial (Ax) Gs for now.
        // Az is roughly -y2 * sin(phi) + z2 * cos(phi)
        // But wait, "Normal" G is usually "Lift". Lift is defined in wind frame, but pilot feels body frame Az.
        // So we do full rotation.
        double phi_rad = Math::to_radians(val.roll);
        double c_phi = std::cos(phi_rad);
        double s_phi = std::sin(phi_rad);
        
        double ax_b = x2;
        // double ay_b =  y2 * c_phi + z2 * s_phi; 
        double az_b = -y2 * s_phi + z2 * c_phi;
        
        return {ax_b, 0, az_b}; 
    }
}

inline void register_instrument_system(flecs::world& ecs) {
    ecs.system<InstrumentState, const Transform, const Velocity, const AeroState, 
               const ForceAccumulator, const Mass, const Propulsion, const AngularVelocity>
        ("UpdateInstruments")
        .kind(flecs::OnUpdate) // Runs after physics loop
        .run([](flecs::iter& it) {
            const EnvironmentModelRef* env_ref = it.world().get<EnvironmentModelRef>();
            
            while (it.next()) {
                auto inst = it.field<InstrumentState>(0);
                auto transform = it.field<const Transform>(1);
                auto velocity = it.field<const Velocity>(2);
                auto aero = it.field<const AeroState>(3);
                auto forces = it.field<const ForceAccumulator>(4);
                auto mass = it.field<const Mass>(5);
                auto propulsion = it.field<const Propulsion>(6);
                auto ang_vel = it.field<const AngularVelocity>(7);
                
                for (auto i : it) {
                    // 1. Flight Dynamics
                    inst[i].alt_baro_m = transform[i].z; 
                    
                    // Radar Alt
                    double terrain_z = 0.0;
                    if (env_ref && env_ref->model) {
                         auto cell = env_ref->model->get_terrain_at(transform[i].x, transform[i].y);
                         terrain_z = cell.elevation;
                    }
                    inst[i].alt_radar_m = std::max(0.0, transform[i].z - terrain_z);
                    
                    // Attitude
                    inst[i].pitch_deg = transform[i].pitch;
                    inst[i].roll_deg = transform[i].roll;
                    inst[i].heading_deg = transform[i].heading;
                    
                    // Speed
                    inst[i].mach = aero[i].mach_number;
                    inst[i].ias_mps = std::sqrt(2.0 * aero[i].dynamic_pressure / 1.225); // IAS approx
                    inst[i].vvi_mps = velocity[i].vz;
                    
                    inst[i].aoa_deg = aero[i].angle_of_attack;
                    inst[i].beta_deg = aero[i].sideslip_angle;
                    
                    // Rates
                    inst[i].p_deg_s = inst_rad_to_deg(ang_vel[i].p);
                    inst[i].q_deg_s = inst_rad_to_deg(ang_vel[i].q);
                    inst[i].r_deg_s = inst_rad_to_deg(ang_vel[i].r);

                    // G-Load
                    double total_mass = mass[i].get_total_kg();
                    if (total_mass < 1.0) total_mass = 1.0;
                    
                    // Remove gravity from Fz (ForceAccumulator includes gravity)
                    // F_sensor = F_total - F_gravity
                    // F_gravity = (0, 0, -mg)
                    // F_sensor = F_total - (0,0,-mg) = F_total + (0,0,mg)
                    // Wait, ForceAccumulator stores F_total.
                    // If F_total has gravity (-mg), then removing it means - (-mg) = +mg.
                    // Correct.
                    Math::Vector3 f_contact = {
                        forces[i].fx, 
                        forces[i].fy, 
                        forces[i].fz + (total_mass * 9.80665) 
                    };
                    
                    Math::Vector3 f_body = project_forces_to_body(f_contact, transform[i]);
                    
                    // Gs usually defined as Load / Weight. Load = f_sensor.
                    inst[i].g_load_normal = -f_body.z / (total_mass * 9.80665); // Positive G is Up (Body -Z)
                    inst[i].g_load_axial  = f_body.x / (total_mass * 9.80665);
                    
                    // 2. Propulsion
                    double tsfc = propulsion[i].afterburner_active ? 0.25 : 0.1; // kg/N/h approx
                    inst[i].fuel_flow_kg_h = std::abs(propulsion[i].current_thrust_n) * tsfc;
                    
                    if (propulsion[i].afterburner_active) {
                        inst[i].engine_rpm_pct = 100.0 + (propulsion[i].current_thrust_n / (propulsion[i].ab_thrust_n + 1e-6)) * 10.0;
                    } else {
                        inst[i].engine_rpm_pct = (propulsion[i].current_thrust_n / (propulsion[i].mil_thrust_n + 1e-6)) * 100.0;
                    }
                    inst[i].engine_temp_c = 600.0 + inst[i].engine_rpm_pct * 3.0; // Mocked EGT
                    
                    inst[i].fuel_internal_kg = mass[i].fuel_mass_kg; 
                    inst[i].fuel_external_kg = mass[i].stores_mass_kg; // Simplified
                    
                    // 3. Env
                    inst[i].oat_c = 15.0 - (transform[i].z / 1000.0) * 6.5; 
                    
                    // Command Bugs
                    const MissionCommand* mission = it.entity(i).get<MissionCommand>();
                    if (mission && mission->active) {
                        inst[i].cmd_heading_deg = mission->cmd_heading_deg;
                        inst[i].cmd_alt_m = mission->cmd_altitude_m;
                        inst[i].cmd_speed_mps = mission->cmd_speed_mps;
                    } else {
                        // Fallback to legacy or hold current
                        inst[i].cmd_heading_deg = inst[i].heading_deg; // Center bug
                        inst[i].cmd_alt_m = inst[i].alt_baro_m;
                        inst[i].cmd_speed_mps = inst[i].ias_mps;
                    }
 
                    // 4. EW
                    const RWR* rwr = it.entity(i).get<RWR>();
                    inst[i].rwr_active = (rwr && !rwr->detected_radar_ids.empty());
                    
                    const Ammo* ammo = it.entity(i).get<Ammo>();
                    inst[i].missiles_remaining = ammo ? ammo->missiles_remaining : 0;
                }
            }
        });
}
