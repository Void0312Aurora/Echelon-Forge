#pragma once

#include <limits>
#include <string>
#include <unordered_map>
#include <vector>

#include "components/basic/common.h"
#include "components/combat/health.h"
#include "components/command/command_link.h"
#include "components/physics/performance.h"
#include "components/combat/scoring.h"
#include "components/systems/sensor.h"
#include "components/domains/air/combat/damage_air.h"
#include "components/combat/common/damage_common.h"
#include "components/combat/common/weapon_common.h"
#include "components/domains/naval/combat/weapon_naval.h"
#include "components/systems/ew.h"
#include "components/systems/sonar.h"
#include "components/domains/naval/platform/embarked_air_ops.h"
#include "components/domains/naval/platform/ship_platform.h"
#include "components/domains/naval/platform/submarine_platform.h"
#include "components/domains/air/platform/flight_dynamics_tuning.h"

inline Sensor make_unit_definition_default_sensor() {
    Sensor sensor{};
    sensor.max_range = 30000.0;
    sensor.fov_deg = 120.0;
    sensor.scan_period = 1.0;
    sensor.last_scan_time = -1.0;
    sensor.detection_prob = 1.0;
    sensor.range_power = 2.0;
    sensor.bearing_noise_std = 0.0;
    sensor.range_noise_std = 0.0;
    sensor.track_memory_s = 0.0;
    sensor.aspect_influence = 0.0;
    sensor.doppler_notch_width = 0.0;
    sensor.reference_snr_db = 13.0;
    sensor.reference_range_m = 30000.0;
    sensor.reference_rcs_m2 = 5.0;
    sensor.pfa = 1.0e-6;
    sensor.confirm_hits_m = 2;
    sensor.confirm_window_n = 3;
    sensor.velocity_noise_std = 3.0;
    sensor.alpha_beta_alpha = 0.65;
    sensor.alpha_beta_beta = 0.12;
    sensor.antenna_height_m = 10.0;
    sensor.target_height_bias_m = 5.0;
    sensor.sea_clutter_sensitivity = 0.0;
    sensor.sea_state_loss_per_level = 0.0;
    sensor.ducting_gain_factor = 1.0;
    sensor.ducting_max_bonus_m = 0.0;
    sensor.bearing_only_min_range_m = 0.0;
    sensor.environment_domain = static_cast<int>(SensorEnvironmentDomain::Air);
    sensor.enforce_radar_horizon = false;
    sensor.enable_ducting = false;
    sensor.sea_clutter_enabled = false;
    sensor.bearing_only = false;
    sensor.type = static_cast<int>(SensorType::Visual);
    return sensor;
}

struct MissileTuningDefinition {
    double max_speed = std::numeric_limits<double>::quiet_NaN();
    double turn_rate = std::numeric_limits<double>::quiet_NaN();
    double fuse_distance = std::numeric_limits<double>::quiet_NaN();
    double damage = std::numeric_limits<double>::quiet_NaN();
    double seeker_fov_deg = std::numeric_limits<double>::quiet_NaN();
    double seeker_lock_range = std::numeric_limits<double>::quiet_NaN();
    double guidance_delay_s = std::numeric_limits<double>::quiet_NaN();
    double guidance_update_period_s = std::numeric_limits<double>::quiet_NaN();
    double max_flight_time_s = std::numeric_limits<double>::quiet_NaN();
    double nav_gain = std::numeric_limits<double>::quiet_NaN();
    double apn_target_accel_gain = std::numeric_limits<double>::quiet_NaN();
    double sensor_max_range = std::numeric_limits<double>::quiet_NaN();
    double sensor_fov_deg = std::numeric_limits<double>::quiet_NaN();
    double sensor_scan_period = std::numeric_limits<double>::quiet_NaN();
    double sensor_detection_prob = std::numeric_limits<double>::quiet_NaN();
    double sensor_bearing_noise_std = std::numeric_limits<double>::quiet_NaN();
    double sensor_range_noise_std = std::numeric_limits<double>::quiet_NaN();
    double sensor_track_memory_s = std::numeric_limits<double>::quiet_NaN();
    int seeker_type = -1;
    double seeker_activation_range_m = std::numeric_limits<double>::quiet_NaN();
    double seeker_gimbal_limit_deg = std::numeric_limits<double>::quiet_NaN();
    double seeker_ifov_deg = std::numeric_limits<double>::quiet_NaN();
    double bearing_filter_tau_s = std::numeric_limits<double>::quiet_NaN();
    double elevation_filter_tau_s = std::numeric_limits<double>::quiet_NaN();
    double range_filter_tau_s = std::numeric_limits<double>::quiet_NaN();
    double track_break_time_s = std::numeric_limits<double>::quiet_NaN();
    double boost_time_s = std::numeric_limits<double>::quiet_NaN();
    double sustain_time_s = std::numeric_limits<double>::quiet_NaN();
    double boost_thrust_n = std::numeric_limits<double>::quiet_NaN();
    double sustain_thrust_n = std::numeric_limits<double>::quiet_NaN();
    double reference_area_m2 = std::numeric_limits<double>::quiet_NaN();
    double cd0_subsonic = std::numeric_limits<double>::quiet_NaN();
    double cd0_supersonic = std::numeric_limits<double>::quiet_NaN();
    double induced_drag_k = std::numeric_limits<double>::quiet_NaN();
    std::vector<double> cd0_mach_breakpoints;
    std::vector<double> cd0_mach_values;
    std::vector<double> induced_drag_k_mach_breakpoints;
    std::vector<double> induced_drag_k_mach_values;
    double propellant_mass_kg = std::numeric_limits<double>::quiet_NaN();
    double max_lateral_g = std::numeric_limits<double>::quiet_NaN();
    double autopilot_tau_s = std::numeric_limits<double>::quiet_NaN();
    double autopilot_damping = std::numeric_limits<double>::quiet_NaN();
    // Content definitions are complete values; runtime global tuning uses a
    // separate negative sentinel so an untouched patch does not force order 1.
    int autopilot_order = 1;
    double max_accel_response_g_per_s = std::numeric_limits<double>::quiet_NaN();
    double mach_transonic_start = std::numeric_limits<double>::quiet_NaN();
    double mach_transonic_end = std::numeric_limits<double>::quiet_NaN();
    double cd0_power_on_ratio = std::numeric_limits<double>::quiet_NaN();
    double min_launch_range_m = std::numeric_limits<double>::quiet_NaN();
    double max_launch_off_boresight_deg = std::numeric_limits<double>::quiet_NaN();
    bool lobl_required = false;
    bool midcourse_datalink_supported = false;
    bool use_kalman_seeker = false;
    WarheadProfile warhead_profile{};
    bool has_warhead_profile = false;
    FuzeProfile fuze_profile{};
    bool has_fuze_profile = false;
};

// Data Structs for Modules
struct Engine {
    double mil_thrust_n = 0.0;
    double ab_thrust_n = 0.0;
    double sfc_mil = 0.0;
    double sfc_ab = 0.0;
    double bypass_ratio = 0.0;
    bool has_tuning = false;
    EngineTuning tuning;
};

struct Hardpoint {
    int station_id;
    std::vector<std::string> supported_types;
    double capacity_kg;
};

struct Airframe {
    double empty_mass_kg = 0.0;
    double max_fuel_kg = 0.0;
    double drag_coefficient = 0.02;
    double reference_area = 27.0;

    // Procedural Gen Data
    double length_m = 0.0;
    double wingspan_m = 0.0;
    double height_m = 0.0;
    std::string configuration = "Conventional"; // "Conventional", "Delta", "Flanker", "Bomber"
    bool has_tuning = false;
    AeroTuning tuning;
};

struct NavalStoresDefinition {
    double fuel_units_current{0.0};
    double fuel_units_max{0.0};
    double missile_units_current{0.0};
    double missile_units_max{0.0};
    double dry_cargo_units_current{0.0};
    double dry_cargo_units_max{0.0};
    bool can_receive_underway{false};
    bool can_provide_underway{false};
};

struct NavalLogisticsDefinition {
    bool underway_replenishment_enabled{false};
    double min_separation_m{0.0};
    double max_separation_m{0.0};
    double max_relative_speed_mps{0.0};
    double transfer_rate_fuel_units_per_s{0.0};
    double transfer_rate_missile_units_per_s{0.0};
    double transfer_rate_dry_cargo_units_per_s{0.0};
};

struct UnitDefinition {
    UnitType type;
    std::string name;

    // Component References (Modular)
    std::string sensor_ref;
    std::vector<std::string> sensor_refs;
    std::string engine_ref;
    std::string ew_suite_ref;
    std::string rcs_profile_ref;

    // Modular Data
    std::vector<Hardpoint> hardpoints;
    std::unordered_map<int, std::string> default_loadout;

    // Module Definitions (if type == Engine)
    Engine engine_data;

    // EW Data (if type == EWSuite)
    // We can reuse UnitDefinition as a generic container or add specific structs
    // For simplicity, let's keep them here for now
    // Actually, to keep it clean, let's add these to components/systems/ew.h and include here?
    // They are already included.
    // We need to store the *loaded data* in the definition map.
    // So if "Generic_EW" is loaded, it stores RWR/Jammer configs here.
    Jammer jammer_data;
    RWR rwr_data;
    bool has_esm_data = false;
    ESMReceiver esm_data;
    Countermeasures cms_data;

    // RCS Data
    RCSProfile rcs_data;

    // Platform Data
    Airframe airframe;
    bool has_ship_platform;
    ShipPlatform ship_platform;
    bool has_submarine_platform = false;
    SubmarinePlatform submarine_platform;
    bool has_naval_stores = false;
    NavalStoresDefinition naval_stores;
    bool has_naval_logistics = false;
    NavalLogisticsDefinition naval_logistics;
    bool has_naval_weapon_system = false;
    NavalWeaponSystem naval_weapon_system;
    bool has_embarked_air_ops = false;
    EmbarkedAirOps embarked_air_ops;
    HitboxConfig damage_model;
    bool has_aircraft_vulnerability = false;
    AircraftVulnerabilityProfile aircraft_vulnerability;

    // Legacy Inline Components (Backwards Compat)
    Health health;
    bool has_sensor;
    Sensor sensor;
    MountedSensors mounted_sensors;
    bool has_sonar = false;
    Sonar sonar;
    MountedSonars mounted_sonars;

    bool has_flight_model;
    FlightModel flight_model;
    bool has_stall_state = false;
    StallState stall_state;

    bool has_landing_gear;
    LandingGear landing_gear;

    bool has_score;
    Score score;

    // Generic Data
    double mass_kg; // For missiles/bombs, or components

    bool has_ammo;
    Ammo ammo;

    bool has_command_link;
    CommandLink command_link;

    bool has_data_link;
    int data_link_network_id;
    int data_link_max_reports_per_update = 16;
    int data_link_max_messages_per_update = -1;

    bool has_missile_tuning = false;
    MissileTuningDefinition missile_tuning;
};

struct UnitTypeHash {
    std::size_t operator()(UnitType type) const { return static_cast<std::size_t>(type); }
};
