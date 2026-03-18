#pragma once

#include <algorithm>
#include <cmath>
#include <unordered_map>

#include <spdlog/spdlog.h>

#include "components/physics/action.h"
#include "components/basic/common.h"
#include "components/combat/health.h"
#include "components/physics/performance.h"
#include "components/combat/scoring.h"
#include "components/systems/sensor.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/combat/damage.h"
#include "components/combat/weapon.h"
#include "components/systems/data_link.h"
#include "components/systems/logistics.h"
#include "components/systems/comm.h"
#include "components/systems/ew.h"
#include "components/systems/navigation.h"
#include "components/systems/track_management.h"
#include "content/unit_definition_loader.h"
#include "core/interfaces/unit_factory.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

inline double default_factory_wrap_angle_360(double angle) {
    while (angle < 0.0) angle += 360.0;
    while (angle >= 360.0) angle -= 360.0;
    return angle;
}

inline double default_factory_math_deg_to_nav_deg(double math_deg) {
    return default_factory_wrap_angle_360(90.0 - math_deg);
}

class DefaultUnitFactory : public IUnitFactory {
public:
    explicit DefaultUnitFactory(const std::string& config_path = std::string()) {
        UnitDefinition aircraft{};
        aircraft.type = UnitType::Aircraft;
        aircraft.name = "Aircraft";
        aircraft.health = {100.0, 100.0};
        aircraft.has_sensor = true;
        aircraft.sensor = {30000.0, 120.0, 1.0, -1.0, 0.9, 2.0, 1.0, 25.0, 2.0, 0.3};
        aircraft.has_flight_model = true;
        aircraft.flight_model = {600.0, 50.0, 20.0, 50.0, 300.0, 9.0, 80.0, 70.0, 20.0};
        aircraft.has_score = true;
        aircraft.score = {0.0, 0, 0, 0};
        aircraft.has_ammo = true;
        aircraft.ammo = {4, 4};
        aircraft.has_command_link = true;
        aircraft.command_link = {0.2, 0.0};
        aircraft.has_data_link = true;
        aircraft.data_link_network_id = 0; // Dynamic assignment? Or per side? Usually side-based.
        definitions_.emplace(aircraft.name, aircraft);

        UnitDefinition missile{};
        missile.type = UnitType::Missile;
        missile.name = "Missile";
        missile.health = {100.0, 100.0};
        missile.has_sensor = true;
        missile.sensor = {30000.0, 120.0, 0.2, -1.0, 0.95, 2.0, 0.5, 15.0, 0.5, 0.2};
        missile.has_flight_model = true;
        missile.flight_model = {1200.0, 100.0, 40.0, 100.0, 600.0, 30.0, 0.0, 0.0, 0.0};
        missile.has_score = true;
        missile.score = {0.0, 0, 0, 0};
        missile.has_ammo = false;
        missile.ammo = {0, 0};
        missile.has_command_link = false;
        missile.command_link = {0.0, 0.0};
        missile.has_data_link = true; // Missiles often have DL (Mid-course updates)
        missile.data_link_network_id = 0;
        definitions_.emplace(missile.name, missile);

        UnitDefinition ship{};
        ship.type = UnitType::Ship;
        ship.name = "Ship";
        ship.health = {100.0, 100.0};
        ship.has_sensor = true;
        ship.sensor = {30000.0, 120.0, 2.0, -1.0, 0.9, 2.0, 2.0, 50.0, 3.0, 0.2};
        ship.has_flight_model = false;
        ship.has_score = true;
        ship.score = {0.0, 0, 0, 0};
        ship.has_ammo = false;
        ship.ammo = {0, 0};
        ship.has_command_link = false;
        ship.command_link = {0.0, 0.0};
        ship.has_data_link = true;
        ship.data_link_network_id = 0;
        definitions_.emplace(ship.name, ship);

        UnitDefinition facility{};
        facility.type = UnitType::Facility;
        facility.name = "Facility";
        facility.health = {100.0, 100.0};
        facility.has_sensor = true;
        facility.sensor = {30000.0, 120.0, 2.0, -1.0, 0.9, 2.0, 2.0, 50.0, 3.0, 0.2};
        facility.has_flight_model = false;
        facility.has_score = true;
        facility.score = {0.0, 0, 0, 0};
        facility.has_ammo = false;
        facility.ammo = {0, 0};
        facility.has_command_link = false;
        facility.command_link = {0.0, 0.0};
        facility.has_data_link = true;
        facility.data_link_network_id = 0;
        definitions_.emplace(facility.name, facility);
        
        UnitDefinition c2node{};
        c2node.type = UnitType::C2Node;
        c2node.name = "AWACS"; // Or generic C2
        c2node.health = {100.0, 100.0};
        c2node.has_sensor = true;
        // Big Radar: 400km Range, 360 scan, 5s period (slow scan)
        c2node.sensor = {400000.0, 360.0, 5.0, -1.0, 0.99, 2.0, 0.5, 50.0, 10.0, 0.0};
        c2node.has_flight_model = true; // It flies
        c2node.flight_model = {250.0, 100.0, 5.0, 5.0, 50.0, 2.0, 70.0, 60.0, 10.0}; // Slow, low G
        c2node.has_score = true;
        c2node.score = {0.0,0,0,0};
        c2node.has_ammo = false;
        c2node.has_command_link = true;
        c2node.command_link = {0.1, 0.0}; // Good comms
        c2node.has_data_link = true;
        c2node.data_link_network_id = 0;
        definitions_.emplace(c2node.name, c2node);

        if (!config_path.empty()) {
            std::string error;
            if (!load_definitions(config_path, &error)) {
                spdlog::warn("Unit definition load failed: {}", error);
            }
        }
    }

    const UnitDefinition* get_definition(const std::string& name) const override {
        auto it = definitions_.find(name);
        if (it == definitions_.end()) return nullptr;
        return &it->second;
    }

    flecs::entity spawn(flecs::world& ecs,
                        const std::string& unit_name,
                        const SpawnParams& params) override {
        auto it = definitions_.find(unit_name);
        if (it == definitions_.end()) {
            spdlog::error("Unknown unit name: {}", unit_name);
            return flecs::entity::null();
        }
        const UnitDefinition& def = it->second;
        double heading_init = params.heading;
        double pitch_init = params.pitch;
        double roll_init = params.roll;
        
        // Only infer if heading is exactly 0 and velocity is significant? 
        // Or trust the caller? 
        // Let's trust the caller. If they want to align with velocity, they should calculate it.
        // However, existing code might define 0.
        // Let's keep the velocity inference ONLY if all angles are 0?
        if (std::abs(heading_init) < 1e-6 && std::abs(pitch_init) < 1e-6 && std::abs(roll_init) < 1e-6) {
             double h_speed_sq = params.vx * params.vx + params.vy * params.vy;
             if (h_speed_sq > 1e-12) {
                 double math_deg = std::atan2(params.vy, params.vx) * 180.0 / M_PI;
                 heading_init = default_factory_math_deg_to_nav_deg(math_deg);
                 // Pitch from vertical velocity?
                 double speed = std::sqrt(h_speed_sq + params.vz * params.vz);
                 if (speed > 1e-3) {
                     double pitch_arg = params.vz / speed;
                     pitch_arg = std::clamp(pitch_arg, -1.0, 1.0);
                     pitch_init = std::asin(pitch_arg) * 180.0 / M_PI;
                 }
             }
        }

        auto e = ecs.entity()
            .set<Transform>({params.x, params.y, params.z, heading_init, pitch_init, roll_init})
            .set<Velocity>({params.vx, params.vy, params.vz})
            .set<Alliance>({params.side})
            .set<KeyEntity>({def.type})
            .set<Health>({def.health.current_hp, def.health.max_hp});

        if (!def.sensor_ref.empty()) {
            // Modular Sensor Loading
            auto s_it = definitions_.find(def.sensor_ref);
            if (s_it != definitions_.end()) {
                 const UnitDefinition& sensor_def = s_it->second;
                 e.set<Sensor>(sensor_def.sensor);
                 e.set<ContactList>({});
            } else {
                spdlog::warn("Unit {} references unknown sensor {}", unit_name, def.sensor_ref);
            }
        } else if (def.has_sensor) {
            // Legacy/Inline Sensor
            e.set<Sensor>(def.sensor);
            e.set<ContactList>({});
        }

        // Modular Dynamics Initialization
        double stores_kg = 0.0;
        if (!def.default_loadout.empty()) {
             for (const auto& [station, weapon_name] : def.default_loadout) {
                 auto w_it = definitions_.find(weapon_name);
                 if (w_it != definitions_.end()) {
                     stores_kg += w_it->second.mass_kg;
                     
                     // Spawn Real Munition Entity (Child)
                     std::string mun_name = unit_name + "_Stn_" + std::to_string(station);
                     auto m_e = ecs.entity(mun_name.c_str()).child_of(e)
                        .set<Munition>({station, false})
                        .set<KeyEntity>({w_it->second.type})
                        .set<Mass>({w_it->second.mass_kg, 0, 0});
                        
                     // Copy weapon characteristics if present?
                     // Ideally we just point to the def, but for now copying generic props or tagging is enough.
                     // The WeaponSystem will look at these children later.
                 } else {
                     spdlog::warn("Unit {} references unknown weapon {}", unit_name, weapon_name);
                 }
             }
        }
        
        // Initialize Mass
        // If airframe data is present (non-zero), use it. otherwise fallback to 0 (or legacy handling?)
        if (def.airframe.empty_mass_kg > 0) {
             e.set<Mass>({def.airframe.empty_mass_kg, def.airframe.max_fuel_kg, stores_kg});
        } else if (def.type == UnitType::Aircraft || def.has_flight_model) {
             // Fallback Mass
             e.set<Mass>({10000.0, 3000.0, stores_kg});
        }

        // Initialize Logistics Variables
        double mil_flow_rate = 2.0;
        double ab_mult = 3.0;
        
        // Initialize Propulsion
        if (!def.engine_ref.empty()) {
            auto eng_it = definitions_.find(def.engine_ref);
            if (eng_it != definitions_.end()) {
                 const auto& eng_data = eng_it->second.engine_data;
                 e.set<InstrumentState>({});
                 e.set<Propulsion>({eng_data.mil_thrust_n, eng_data.ab_thrust_n, 0.0, false});
                 
                 // Heuristic flow rate if SFC not provided (0.0): ~ 1kg/s per 40kN ?
                 // If SFC provided (assume kg/s for now)
                 if (eng_data.sfc_mil > 0) mil_flow_rate = eng_data.sfc_mil;
            } else {
                 spdlog::warn("Unit {} references unknown engine {}", unit_name, def.engine_ref);
            }
        } else if (def.type == UnitType::Aircraft || def.has_flight_model) {
             // Fallback Generic Propulsion
             e.set<Propulsion>({40000.0, 70000.0, 0.0, false});
        }
        double internal_fuel = (def.airframe.max_fuel_kg > 0) ? def.airframe.max_fuel_kg : 2000.0;
        e.set<FuelSystem>({
             internal_fuel, // Current
             internal_fuel, // Max
             0.0, 0.0,      // External
             0.0, false,    // State
             mil_flow_rate,
             ab_mult
        });

        // Initialize EW Suite
        if (!def.ew_suite_ref.empty()) {
            auto ew_it = definitions_.find(def.ew_suite_ref);
            if (ew_it != definitions_.end()) {
                const auto& ew_def = ew_it->second;
                e.set<RWR>(ew_def.rwr_data);
                e.set<Jammer>(ew_def.jammer_data);
                e.set<Countermeasures>(ew_def.cms_data);
            } else {
                spdlog::warn("Unit {} references unknown EW suite {}", unit_name, def.ew_suite_ref);
            }
        } else {
             // Defaults or Minimal
             e.set<RWR>({-80.0, {}, {}, false});
             e.set<Jammer>({false, 0.0, 0.0, JammingType::NoiseBarrage, 0.0});
             e.set<Countermeasures>({0, 0, 1.0, 0.0, false});
        }
        
        // Initialize RCS Profile
        if (!def.rcs_profile_ref.empty()) {
             auto rcs_it = definitions_.find(def.rcs_profile_ref);
             if (rcs_it != definitions_.end()) {
                 e.set<RCSProfile>(rcs_it->second.rcs_data);
             } else {
                 spdlog::warn("Unit {} references unknown RCS profile {}", unit_name, def.rcs_profile_ref);
             }
        } else {
             // Fallback
             e.set<RCSProfile>({5.0, 5.0, 5.0});
        }

        // Initialize MassProperties
        double empty_mass = (def.airframe.empty_mass_kg > 0) ? def.airframe.empty_mass_kg : 10000.0;
        double drag_coef = (def.airframe.drag_coefficient > 0) ? def.airframe.drag_coefficient : 0.02;
        double ref_area = (def.airframe.reference_area > 0) ? def.airframe.reference_area : 30.0;
        double span_m = (def.airframe.wingspan_m > 1.0) ? def.airframe.wingspan_m : 10.0;
        double chord_m = (span_m > 1.0) ? (ref_area / span_m) : 3.0;
        e.set<MassProperties>({
            empty_mass,
            empty_mass + internal_fuel, // Initial Total
            drag_coef,
            drag_coef,
            ref_area,
            span_m,
            chord_m
        });
        
        // Initialize New Physics Components
        // Initialize New Physics Components
        e.set<ForceAccumulator>({});
        e.set<AeroState>({});
        
        // Initialize InstrumentState with valid starting values
        InstrumentState initial_instruments{};
        initial_instruments.heading_deg = heading_init;
        initial_instruments.pitch_deg = pitch_init;
        initial_instruments.roll_deg = roll_init;
        initial_instruments.alt_baro_m = params.z;
        initial_instruments.alt_radar_m = params.z; // Assume flat ground for init
        initial_instruments.ias_mps = std::sqrt(params.vx*params.vx + params.vy*params.vy + params.vz*params.vz);
        initial_instruments.fuel_internal_kg = internal_fuel;
        initial_instruments.fuel_external_kg = 0.0;
        initial_instruments.gear_pos = 1.0f;
        // ... fill others if needed
        e.set<InstrumentState>(initial_instruments);

        // Inertia: approximate from airframe geometry for aircraft.
        // The previous fixed inertia was far too small for fighter-sized masses, producing unrealistically
        // high yaw/roll accelerations on the ground (e.g., excessive weathervaning in crosswind).
        Inertia inertia_guess{30000.0, 50000.0, 60000.0}; // legacy minimums (kg*m^2)
        if (def.type == UnitType::Aircraft) {
            const double m_total = std::max(1.0, empty_mass + internal_fuel + stores_kg);
            const double l_m = (def.airframe.length_m > 1.0) ? def.airframe.length_m : 15.0;
            const double b_m = (def.airframe.wingspan_m > 1.0) ? def.airframe.wingspan_m : 10.0;
            const double h_m = (def.airframe.height_m > 0.5) ? def.airframe.height_m : 5.0;

            // Box inertia scaled down to reflect centralized mass distribution (engines/fuel near CG).
            // Scale chosen to keep fighter Izz on the order of 1e5 kg*m^2.
            constexpr double kInertiaScale = 0.5;
            const double m_over_12 = m_total / 12.0;
            const double ixx = kInertiaScale * m_over_12 * (b_m * b_m + h_m * h_m);
            const double iyy = kInertiaScale * m_over_12 * (l_m * l_m + h_m * h_m);
            const double izz = kInertiaScale * m_over_12 * (l_m * l_m + b_m * b_m);

            inertia_guess.ixx = std::max(inertia_guess.ixx, ixx);
            inertia_guess.iyy = std::max(inertia_guess.iyy, iyy);
            inertia_guess.izz = std::max(inertia_guess.izz, izz);
        }
        e.set<Inertia>(inertia_guess);
        e.set<AngularVelocity>({0.0, 0.0, 0.0});
        e.set<GroundState>({false, 0.0}); // Initialize Ground Contact
        e.set<GearState>({true, 0.0, false, 0.0, true}); // gear_down, stress, collapsed, stress_rate, on_runway
        
        // Initialize Loadout (Empty for now)
        e.set<Loadout>({});

        // Initialize EGI (Embedded GPS/INS)
        // Assume perfect alignment at spawn
        // Recalculate Initial Lat/Lon (Use same constants as NavigationSystem)
        constexpr double kRefLat = 36.24;
        constexpr double kRefLon = -115.05;
        constexpr double kMetersPerDegLat = 111132.954;
        constexpr double kMetersPerDegLon = 90000.0;
        
        double lat = kRefLat + (params.y / kMetersPerDegLat);
        double lon = kRefLon + (params.x / kMetersPerDegLon);
        
        e.set<EGI>({
            lat, lon, params.z, params.z, // Pos
            params.vy, params.vx, -params.vz, // Vel (NED)
            heading_init, pitch_init, roll_init, // Att
            0.0, 0.0, // Wind
            0.0, 0.0, 0.0, // Drift
            5.0, 0.0, // Uncertainty, TimeSinceFix
            0.5, true // Drift Rate, GPS Avail
        });
        
        if (def.has_score) {
            e.set<Score>(def.score);
        }
        if (def.has_ammo) {
            e.set<Ammo>(def.ammo);
            e.set<WeaponCooldown>({2.0, -1.0});
        }
        if (def.has_command_link) {
            e.set<CommandLink>(def.command_link);
            e.set<PendingMovementCommand>({{0.0, 0.0, 0.0, false}, 0.0, false});
            e.set<PendingActionCommand>({{0.0, 0.0, 0.0, 0.0, false}, 0.0, false});
            e.set<PendingMissionCommand>({{}, 0.0, false});
        }
       // ActionCommand
    e.set<ActionCommand>({
        0.0, 0.0, 0.0, 0.0,
        false, false, false, // Chaff, Flare, Jettison
        false, 0, 0, 0,      // SendMsg, Type, Recipient, Arg
        false // Active
    });
    
    if (def.has_landing_gear) {
        e.set<LandingGear>(def.landing_gear);
    } else if (def.type == UnitType::Aircraft) {
        // Fallback for aircraft without explicit config (assume paved only)
        e.set<LandingGear>({false, 0.02, 3.0, 2.0, 1.0, false, 5.0});
    }

        if (def.has_flight_model) {
            e.set<FlightModel>(def.flight_model);
            double speed = std::sqrt(params.vx * params.vx +
                                     params.vy * params.vy +
                                     params.vz * params.vz);
            e.set<MovementCommand>({
                heading_init,
                speed,
                params.z,
                false, // use_stick_control
                0.0,   // stick_roll
                0.0,   // stick_pitch
                0.0,   // throttle_cmd (ignored in autopilot)
                true,  // gear_handle (down)
                true   // active
            });
            e.set<ActionCommand>({0.0, 0.0, 0.0, 0.0, false});
            e.set<LaggedCommand>({heading_init, speed, params.z, true});
            e.set<ActionSpaceConfig>({
                def.flight_model.max_turn_rate,
                def.flight_model.max_accel,
                def.flight_model.max_climb_rate,
                def.flight_model.min_speed,
                def.flight_model.max_speed,
                0.0,
                20000.0
            });
            e.set<CommandLag>({0.5, 1.0, 1.5});
        }

        // Damage Model Initialization
        if (!def.damage_model.hitboxes.empty()) {
            e.set<HitboxConfig>(def.damage_model);
            
            SystemHealth initial_health;
            for (const auto& hb : def.damage_model.hitboxes) {
                for (const auto& sys_name : hb.protected_systems) {
                    initial_health.systems[sys_name] = 1.0;
                }
            }
            e.set<SystemHealth>(initial_health);
        } else if (def.airframe.length_m > 0.0) {
            // Procedural Generation
            HitboxConfig generated = generate_default_hitboxes(def.airframe);
            e.set<HitboxConfig>(generated);
            
            SystemHealth initial_health;
            for (const auto& hb : generated.hitboxes) {
                for (const auto& sys_name : hb.protected_systems) {
                    initial_health.systems[sys_name] = 1.0;
                }
            }
            e.set<SystemHealth>(initial_health);
        }


        
        if (def.has_data_link) {
            // Auto-assign Network ID by Side for MVP
            // Blue=1, Red=2
            int net_id = (params.side == Side::Blue) ? 1 : 
                         (params.side == Side::Red) ? 2 : 0;
            e.set<DataLink>({
                true, 
                net_id,
                LinkType::Link16,
                500.0 // Default 500km range
            });
            e.add<CommQueue>(); // Enable Messaging
        } else {
            e.remove<DataLink>();
        }

        // Initialize Track Database
        e.set<TrackDatabase>({});

        // Initialize Logistics Node for Facilities/Carriers
        if (def.type == UnitType::Facility || def.name.find("Airbase") != std::string::npos) {
             e.set<LogisticsNode>({
                 1000.0, // 1km radius
                 true    // infinite
             });
        }
        
        return e;
    }

    bool load_definitions(const std::string& path,
                          std::string* error) override {
        std::vector<UnitDefinition> loaded;
        if (!load_unit_definitions_json(path, loaded, error)) {
            return false;
        }

        for (const auto& def : loaded) {
            definitions_[def.name] = def;
        }
        return true;
    }

private:
    std::unordered_map<std::string, UnitDefinition> definitions_;
    
    HitboxConfig generate_default_hitboxes(const Airframe& af) {
        HitboxConfig config;
        
        // Basic Dimensions
        double L = af.length_m;
        double W = af.wingspan_m;
        double H = af.height_m;
        
        if (af.configuration == "Flanker") {
             // Widespread engines, heavy fighter
             // 1. Nose (Sensor, Cockpit)
             config.hitboxes.push_back({0, L * 0.4, 0, 0, L * 0.2, 0.8, 0.8, 5.0, {"radar", "cockpit"}});
             
             // 2. Central Fuselage (Fuel, Ammo, Spine)
             config.hitboxes.push_back({1, 0, 0, 0, L * 0.5, 1.5, 1.0, 10.0, {"fuel", "ammo"}});
             
             // 3. Left Engine Nacelle
             config.hitboxes.push_back({2, -L * 0.35, -1.0, -0.5, L * 0.25, 0.8, 0.8, 15.0, {"engine_left"}});
             
             // 4. Right Engine Nacelle
             config.hitboxes.push_back({3, -L * 0.35, 1.0, -0.5, L * 0.25, 0.8, 0.8, 15.0, {"engine_right"}});
             
             // 5. Wings (Fuel, Control)
             config.hitboxes.push_back({4, -L * 0.1, 0, 0, L * 0.2, W, 0.2, 3.0, {"wings"}});
            
        } else {
             // "Conventional" (Default F-16 style)
             // 1. Nose
             config.hitboxes.push_back({0, L * 0.4, 0, 0, L * 0.25, 0.8, 0.8, 5.0, {"radar", "cockpit"}});
             
             // 2. Fuselage
             config.hitboxes.push_back({1, 0, 0, 0, L * 0.5, 1.0, 1.0, 10.0, {"fuel", "ammo", "engine"}}); // Single engine usually embedded
             
             // 3. Tail / Exhaust
             config.hitboxes.push_back({2, -L * 0.4, 0, 0, L * 0.2, 0.8, 0.8, 12.0, {"engine"}});
             
             // 4. Wings
             config.hitboxes.push_back({3, -L * 0.05, 0, 0, L * 0.2, W, 0.2, 3.0, {"wings"}});
        }
        
        return config;
    }
};
