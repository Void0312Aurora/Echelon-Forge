#pragma once

#include <flecs.h>
#include <cmath>
#include <algorithm>
#include "components/basic/common.h"
#include "components/physics/instruments.h"
#include "components/physics/action.h"       // MissionCommand
#include "components/physics/forces.h"       // AeroState, ForceAccumulator, AngularVelocity
#include "components/physics/dynamics.h"     // Mass, Propulsion
#include "components/physics/performance.h"  // LandingGear
#include "components/systems/ew.h"           // RWR
#include "components/combat/weapon.h"        // Ammo
#include "components/systems/logistics.h"    // FuelSystem
#include "components/systems/navigation.h"   // EGI
#include "core/interfaces/environment_model.h"

namespace {
    inline double inst_rad_to_deg(double rad) { return rad * 180.0 / M_PI; }

    inline double inst_normalize_heading_deg(double heading_deg) {
        if (!std::isfinite(heading_deg)) return 0.0;
        double out = std::fmod(heading_deg, 360.0);
        if (out < 0.0) out += 360.0;
        return out;
    }

    inline bool inst_is_runway_like_surface(IEnvironmentModel::SurfaceType surface) {
        return surface == IEnvironmentModel::SurfaceType::Concrete
            || surface == IEnvironmentModel::SurfaceType::Asphalt;
    }

    inline double inst_ground_track_deg_from_velocity(const Velocity& velocity, double fallback_heading_deg) {
        const double horiz_speed = std::hypot(velocity.vx, velocity.vy);
        if (horiz_speed <= 1.0) {
            return inst_normalize_heading_deg(fallback_heading_deg);
        }
        return inst_normalize_heading_deg(std::atan2(velocity.vx, velocity.vy) * 180.0 / M_PI);
    }

    inline double inst_mission_heading_bug(
        const MissionCommand& mission,
        const Transform& transform,
        const Velocity& velocity,
        const EnvironmentModelRef* env_ref
    ) {
        const double fallback_heading_deg = inst_ground_track_deg_from_velocity(velocity, transform.heading);
        if (mission.command_code == 4) {
            if (env_ref && env_ref->model) {
                const auto cell = env_ref->model->get_terrain_at(transform.x, transform.y);
                if (inst_is_runway_like_surface(cell.type) && std::isfinite(cell.runway_heading)) {
                    return inst_normalize_heading_deg(cell.runway_heading);
                }
            }
        }
        if (std::isfinite(mission.cmd_heading_deg)) {
            return inst_normalize_heading_deg(mission.cmd_heading_deg);
        }
        return fallback_heading_deg;
    }

    inline double inst_mission_alt_bug(const MissionCommand& mission, double fallback_alt_m) {
        return std::isfinite(mission.cmd_altitude_m) ? mission.cmd_altitude_m : fallback_alt_m;
    }

    inline double inst_mission_speed_bug(const MissionCommand& mission, double fallback_speed_mps) {
        return std::isfinite(mission.cmd_speed_mps) ? mission.cmd_speed_mps : fallback_speed_mps;
    }
    
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
                    inst[i].g_load_normal = f_body.z / (total_mass * 9.80665);
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
                    
                    if (const FuelSystem* fuel = it.entity(i).get<FuelSystem>()) {
                        inst[i].fuel_internal_kg = fuel->internal_fuel_kg;
                        inst[i].fuel_external_kg = fuel->external_fuel_kg;
                    } else {
                        inst[i].fuel_internal_kg = mass[i].fuel_mass_kg;
                        inst[i].fuel_external_kg = 0.0;
                    }

                    // 3. Configuration / Switches (Pilot-visible)
                    if (const LandingGear* gear = it.entity(i).get<LandingGear>()) {
                        inst[i].gear_pos = static_cast<float>(std::clamp(gear->extension_state, 0.0, 1.0));
                    } else {
                        inst[i].gear_pos = 0.0f;
                    }

                    const PilotAction* pilot = it.entity(i).get<PilotAction>();
                    const MovementCommand* legacy = it.entity(i).get<MovementCommand>();

                    if (pilot && pilot->active) {
                        inst[i].throttle_pos = std::clamp(pilot->throttle, 0.0, 1.0);
                        inst[i].flaps_pos = std::clamp(pilot->flaps, 0.0f, 1.0f);
                        inst[i].speedbrake_pos = std::clamp(pilot->speedbrake, 0.0f, 1.0f);
                        inst[i].master_arm = pilot->master_arm;
                        inst[i].weapon_selected = pilot->weapon_select_id;
                    } else if (legacy && legacy->active) {
                        inst[i].throttle_pos = std::clamp(legacy->throttle_cmd, 0.0, 1.0);
                        inst[i].flaps_pos = 0.0f;
                        inst[i].speedbrake_pos = 0.0f;
                        inst[i].master_arm = false;
                        inst[i].weapon_selected = 0;
                    } else {
                        inst[i].throttle_pos = 0.0;
                        inst[i].flaps_pos = 0.0f;
                        inst[i].speedbrake_pos = 0.0f;
                        inst[i].master_arm = false;
                        inst[i].weapon_selected = 0;
                    }
                    
                    // 3. Env
                    if (env_ref && env_ref->model) {
                        AtmosphericData atm = env_ref->model->get_atmosphere_at(transform[i].x, transform[i].y, transform[i].z);
                        inst[i].oat_c = atm.temperature - 273.15;

                        double wx = atm.wind_velocity.x;
                        double wy = atm.wind_velocity.y;
                        inst[i].wind_speed_mps = std::sqrt(wx * wx + wy * wy);
                        // Wind direction is conventionally "from" (deg NAV, CW from North).
                        double wind_to_deg = std::atan2(wx, wy) * 180.0 / M_PI;
                        double wind_from_deg = wind_to_deg + 180.0;
                        while (wind_from_deg < 0.0) wind_from_deg += 360.0;
                        while (wind_from_deg >= 360.0) wind_from_deg -= 360.0;
                        inst[i].wind_dir_deg = wind_from_deg;
                    } else {
                        inst[i].oat_c = 15.0 - (transform[i].z / 1000.0) * 6.5;
                        inst[i].wind_speed_mps = 0.0;
                        inst[i].wind_dir_deg = 0.0;
                    }
                    
                    // Command Bugs
                    const MissionCommand* mission = it.entity(i).get<MissionCommand>();
                    if (mission && mission->active) {
                        // The instrument bugs must reflect command-bound semantics:
                        // route commands expose an LNAV/track bug, while landing commands
                        // prefer the active runway / recovery course instead of a free heading hold.
                        inst[i].cmd_heading_deg = inst_mission_heading_bug(*mission, transform[i], velocity[i], env_ref);
                        inst[i].cmd_alt_m = inst_mission_alt_bug(*mission, inst[i].alt_baro_m);
                        inst[i].cmd_speed_mps = inst_mission_speed_bug(*mission, inst[i].ias_mps);
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
                    
                    // 5. EGI / Navigation
                    const EGI* egi = it.entity(i).get<EGI>();
                    if (egi) {
                        inst[i].lat_deg = egi->lat_deg;
                        inst[i].lon_deg = egi->lon_deg;
                        inst[i].vn_mps = egi->vn_mps;
                        inst[i].ve_mps = egi->ve_mps;
                        inst[i].vd_mps = egi->vd_mps;
                        
                        // Compute ground speed and track from NED velocity
                        inst[i].ground_speed_mps = std::sqrt(egi->vn_mps * egi->vn_mps + egi->ve_mps * egi->ve_mps);
                        if (inst[i].ground_speed_mps > 0.1) {
                            // atan2(East, North) gives angle from North, clockwise positive
                            inst[i].ground_track_deg = std::atan2(egi->ve_mps, egi->vn_mps) * 180.0 / M_PI;
                            if (inst[i].ground_track_deg < 0) inst[i].ground_track_deg += 360.0;
                        } else {
                            inst[i].ground_track_deg = inst[i].heading_deg; // Use heading when stationary
                        }
                        
                        // GPS status
                        inst[i].gps_available = egi->gps_available;
                        inst[i].position_uncertainty_m = egi->position_uncertainty_m;
                    } else {
                        // Fallback: no EGI data
                        inst[i].lat_deg = 0.0;
                        inst[i].lon_deg = 0.0;
                        inst[i].vn_mps = 0.0;
                        inst[i].ve_mps = 0.0;
                        inst[i].vd_mps = 0.0;
                        inst[i].ground_speed_mps = 0.0;
                        inst[i].ground_track_deg = inst[i].heading_deg;
                        inst[i].gps_available = false;
                        inst[i].position_uncertainty_m = 1000.0; // Large uncertainty
                    }
                    
                    // 6. Gear State (for RL penalty - NOT for observation)
                    const GearState* gear = it.entity(i).get<GearState>();
                    if (gear) {
                        inst[i].gear_stress = gear->stress;
                        inst[i].gear_collapsed = gear->collapsed;
                        inst[i].on_runway = gear->on_runway;
                    } else {
                        inst[i].gear_stress = 0.0;
                        inst[i].gear_collapsed = false;
                        inst[i].on_runway = true;
                    }
                }
            }
        });
}
