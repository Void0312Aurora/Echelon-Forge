#pragma once

#include <flecs.h>

struct InstrumentState {
    // 1. Flight Dynamics
    double alt_baro_m;      // Barometric Altitude (MSL)
    double alt_radar_m;     // Radar Altitude (AGL)
    double ias_mps;         // Indicated Airspeed
    double mach;            // Mach Number
    double vvi_mps;         // Vertical Velocity Indicator
    
    double pitch_deg;       // Pitch Angle
    double roll_deg;        // Roll Angle
    double heading_deg;     // Magnetic Heading
    
    double aoa_deg;         // Angle of Attack
    double beta_deg;        // Sideslip Angle
    
    double g_load_normal;   // Normal G-Load (Nz)
    double g_load_axial;    // Axial G-Load (Nx)
    
    double p_deg_s;         // Roll Rate
    double q_deg_s;         // Pitch Rate
    double r_deg_s;         // Yaw Rate

    // 2. Propulsion
    double engine_rpm_pct;  // Engine RPM %
    double engine_temp_c;   // EGT
    double fuel_flow_kg_h;  // Fuel Flow
    double throttle_pos;    // Throttle Lever Position [0,1]
    
    double fuel_internal_kg;// Internal Fuel
    double fuel_external_kg;// External Fuel

    // 3. Configuration
    float gear_pos;         // 0.0 (Up) to 1.0 (Down)
    float flaps_pos;        // Degrees or Ratio
    float speedbrake_pos;   // 0.0 (Retracted) to 1.0 (Extended)
    bool master_arm;        // Master Arm Switch

    // 4. Environment & Command (Navigation Bugs)
    double oat_c;           // Outside Air Temperature
    
    // Command Bugs (What the pilot sees as target on HSI/HUD)
    double cmd_heading_deg; // Commanded Heading (Bug)
    double cmd_alt_m;       // Commanded Altitude (Bug)
    double cmd_speed_mps;   // Commanded Speed (Bug)
    
    // 5. Tactical (System Status)
    bool rwr_active;        // RWR is detecting threats
    int weapon_selected;    // Ind index of selected weapon
    int missiles_remaining; // Total count? Or per type? Simple count for now.
};
