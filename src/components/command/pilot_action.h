#pragma once

/**
 * PilotAction
 * Implements [act.md]: The physical interface for the Digital Pilot.
 */
struct PilotAction {
    // 1. Primary Flight Controls (Continuous [-1, 1] or [0, 1])
    double stick_pitch; // [-1, 1] positive = nose up
    double stick_roll;  // [-1, 1] Positive = Right Roll
    double rudder;      // [-1, 1] Positive = Nose Right (Yaw)
    double throttle;    // [0, 1] 0=Idle, 1=Max AB

    // 2. Secondary Controls
    float gear_handle; // 0.0 (Up) to 1.0 (Down)
    float flaps;       // 0.0 (Up) to 1.0 (Full)
    float speedbrake;  // 0.0 (Retracted) to 1.0 (Extended)
    double brake;      // 0.0 (Off) to 1.0 (Full)
    bool brake_left;   // Wheel brake
    bool brake_right;  // Wheel brake

    // 3. Sensors / Avionics
    bool radar_active;    // Main Radar Switch
    double radar_scan_az; // Scan Center Azimuth
    double radar_scan_el; // Scan Center Elevation
    bool tms_up;          // Target Management Switch Up (Lock)

    // 4. Weapons
    bool master_arm;
    bool fire_weapon;     // Pickle/Trigger
    bool fire_gun;        // Gun Trigger
    int weapon_select_id; // Selected Weapon Station/Type
    bool jettison_emergency;

    // 5. Countermeasures
    bool program_chaff;
    bool program_flare;

    // 6. Self-protection jammer (cockpit ECM panel). jammer_transmit is the
    // transmit/standby switch; jammer_mode selects the technique and is an
    // integer JammingType code (0 barrage, 1 spot, 2 DRFM deception). The
    // native EW owner admits the request against the installed pod.
    bool jammer_transmit = false;
    int jammer_mode = 0;

    bool active; // Validity flag
};
