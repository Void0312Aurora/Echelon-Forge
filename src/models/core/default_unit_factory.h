#pragma once

#include <algorithm>
#include <cmath>
#include <unordered_map>

#include <spdlog/spdlog.h>

#include "components/command/command_link.h"
#include "components/command/command_link_qos.h"
#include "components/command/legacy_command.h"
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
#include "components/systems/sonar.h"
#include "components/systems/track_management.h"
#include "components/physics/flight_dynamics_tuning.h"
#include "components/naval/embarked_air_ops.h"
#include "components/naval/ship_platform.h"
#include "components/naval/submarine_platform.h"
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

inline Sensor make_factory_default_sensor(
    double max_range,
    double fov_deg,
    double scan_period,
    double detection_prob,
    double bearing_noise_std,
    double range_noise_std,
    double track_memory_s,
    double aspect_influence,
    int sensor_type
) {
    Sensor sensor{};
    sensor.max_range = max_range;
    sensor.fov_deg = fov_deg;
    sensor.scan_period = scan_period;
    sensor.last_scan_time = -1.0;
    sensor.detection_prob = detection_prob;
    sensor.range_power = 2.0;
    sensor.bearing_noise_std = bearing_noise_std;
    sensor.range_noise_std = range_noise_std;
    sensor.track_memory_s = track_memory_s;
    sensor.aspect_influence = aspect_influence;
    sensor.doppler_notch_width = 20.0;
    sensor.reference_snr_db = 13.0;
    sensor.reference_range_m = std::max(1000.0, max_range);
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
    sensor.type = sensor_type;
    return sensor;
}

class DefaultUnitFactory : public IUnitFactory {
public:
    explicit DefaultUnitFactory(const std::string& config_path = std::string()) {
        UnitDefinition aircraft{};
        aircraft.type = UnitType::Aircraft;
        aircraft.name = "Aircraft";
        aircraft.health = {100.0, 100.0, false, false, false};
        aircraft.has_sensor = true;
        aircraft.sensor = make_factory_default_sensor(
            30000.0, 120.0, 1.0, 0.9, 1.0, 25.0, 2.0, 0.3, static_cast<int>(SensorType::Radar));
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
        missile.health = {100.0, 100.0, false, false, false};
        missile.has_sensor = true;
        missile.sensor = make_factory_default_sensor(
            30000.0, 120.0, 0.2, 0.95, 0.5, 15.0, 0.5, 0.2, static_cast<int>(SensorType::Radar));
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
        ship.health = {100.0, 100.0, false, false, false};
        ship.has_sensor = true;
        ship.sensor = make_factory_default_sensor(
            30000.0, 120.0, 2.0, 0.9, 2.0, 50.0, 3.0, 0.2, static_cast<int>(SensorType::Radar));
        ship.has_flight_model = false;
        ship.has_ship_platform = false;
        ship.has_score = true;
        ship.score = {0.0, 0, 0, 0};
        ship.has_ammo = false;
        ship.ammo = {0, 0};
        ship.has_command_link = false;
        ship.command_link = {0.0, 0.0};
        ship.has_data_link = true;
        ship.data_link_network_id = 0;
        definitions_.emplace(ship.name, ship);

        UnitDefinition submarine{};
        submarine.type = UnitType::Submarine;
        submarine.name = "Submarine";
        submarine.health = {100.0, 100.0, false, false, false};
        submarine.has_sonar = true;
        submarine.sonar = {};
        submarine.sonar.max_range_m = 22000.0;
        submarine.sonar.scan_period_s = 5.0;
        submarine.sonar.track_memory_s = 20.0;
        submarine.sonar.ambient_noise_db = 70.0;
        submarine.sonar.bearing_only = false;
        submarine.has_score = true;
        submarine.score = {0.0, 0, 0, 0};
        submarine.has_ammo = false;
        submarine.has_command_link = false;
        submarine.has_data_link = false;
        definitions_.emplace(submarine.name, submarine);

        UnitDefinition facility{};
        facility.type = UnitType::Facility;
        facility.name = "Facility";
        facility.health = {100.0, 100.0, false, false, false};
        facility.has_sensor = true;
        facility.sensor = make_factory_default_sensor(
            30000.0, 120.0, 2.0, 0.9, 2.0, 50.0, 3.0, 0.2, static_cast<int>(SensorType::Radar));
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
        c2node.health = {100.0, 100.0, false, false, false};
        c2node.has_sensor = true;
        // Big Radar: 400km Range, 360 scan, 5s period (slow scan)
        c2node.sensor = make_factory_default_sensor(
            400000.0, 360.0, 5.0, 0.99, 0.5, 50.0, 10.0, 0.0, static_cast<int>(SensorType::Radar));
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
            .set<Health>({
                def.health.current_hp,
                def.health.max_hp,
                def.health.mission_kill,
                def.health.mobility_kill,
                def.health.sensor_kill
            });

        auto attach_sensor_mount = [&](const Sensor& sensor, const std::string& label) {
            MountedSensors* mounted = e.get_mut<MountedSensors>();
            if (!mounted) {
                e.set<MountedSensors>({});
                mounted = e.get_mut<MountedSensors>();
            }
            mounted->mounts.push_back(SensorMount{sensor, label});
            e.modified<MountedSensors>();
        };
        auto attach_sensor_compat = [&](const Sensor& sensor, const std::string& label) {
            if (!e.has<Sensor>()) {
                e.set<Sensor>(sensor);
            } else {
                attach_sensor_mount(sensor, label);
            }
        };
        auto attach_sonar_mount = [&](const Sonar& sonar, const std::string& label) {
            MountedSonars* mounted = e.get_mut<MountedSonars>();
            if (!mounted) {
                e.set<MountedSonars>({});
                mounted = e.get_mut<MountedSonars>();
            }
            mounted->mounts.push_back(SonarMount{sonar, label});
            e.modified<MountedSonars>();
        };
        auto attach_sonar_compat = [&](const Sonar& sonar, const std::string& label) {
            if (!e.has<Sonar>()) {
                e.set<Sonar>(sonar);
            } else {
                attach_sonar_mount(sonar, label);
            }
        };

        bool attached_any_sensor = false;
        if (!def.sensor_refs.empty()) {
            for (const auto& sensor_ref_name : def.sensor_refs) {
                auto s_it = definitions_.find(sensor_ref_name);
                if (s_it == definitions_.end()) {
                    spdlog::warn("Unit {} references unknown sensor {}", unit_name, sensor_ref_name);
                    continue;
                }
                attach_sensor_compat(s_it->second.sensor, sensor_ref_name);
                attached_any_sensor = true;
            }
        }
        if (!def.sensor_ref.empty()) {
            auto s_it = definitions_.find(def.sensor_ref);
            if (s_it != definitions_.end()) {
                 const UnitDefinition& sensor_def = s_it->second;
                 attach_sensor_compat(sensor_def.sensor, def.sensor_ref);
                 attached_any_sensor = true;
            } else {
                spdlog::warn("Unit {} references unknown sensor {}", unit_name, def.sensor_ref);
            }
        } else if (def.has_sensor) {
            attach_sensor_compat(def.sensor, "inline_sensor");
            attached_any_sensor = true;
        }
        if (!def.mounted_sensors.mounts.empty()) {
            for (const auto& mount : def.mounted_sensors.mounts) {
                attach_sensor_compat(mount.sensor, mount.label);
            }
            attached_any_sensor = true;
        }
        if (attached_any_sensor) {
            e.set<ContactList>({});
        }
        bool attached_any_sonar = false;
        if (def.has_sonar) {
            attach_sonar_compat(def.sonar, "inline_sonar");
            attached_any_sonar = true;
        }
        if (!def.mounted_sonars.mounts.empty()) {
            for (const auto& mount : def.mounted_sonars.mounts) {
                attach_sonar_compat(mount.sonar, mount.label);
            }
            attached_any_sonar = true;
        }
        if (attached_any_sonar && !e.has<ContactList>()) {
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
        if (def.has_ship_platform && def.ship_platform.displacement_full_load_kg > 0.0) {
             e.set<Mass>({def.ship_platform.displacement_full_load_kg, 0.0, stores_kg});
        } else if (def.has_submarine_platform && def.submarine_platform.submerged_displacement_kg > 0.0) {
             e.set<Mass>({def.submarine_platform.submerged_displacement_kg, 0.0, stores_kg});
        } else if (def.airframe.empty_mass_kg > 0) {
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
                 
                 if (eng_data.has_tuning) {
                     EngineTuning tuning = eng_data.tuning;
                     tuning.enabled = true;
                     if (tuning.mil_thrust_n <= 1.0) {
                         tuning.mil_thrust_n = eng_data.mil_thrust_n;
                     }
                     if (tuning.ab_thrust_n <= tuning.mil_thrust_n) {
                         tuning.ab_thrust_n = std::max(eng_data.ab_thrust_n, tuning.mil_thrust_n);
                     }
                     if (tuning.tsfc_mil_kg_per_nh <= 0.0 && eng_data.sfc_mil > 0.0) {
                         tuning.tsfc_mil_kg_per_nh = eng_data.sfc_mil;
                     }
                     if (tuning.tsfc_ab_kg_per_nh <= 0.0 && eng_data.sfc_ab > 0.0) {
                         tuning.tsfc_ab_kg_per_nh = eng_data.sfc_ab;
                     }
                     e.set<EngineTuning>(tuning);
                 }

                 if (eng_data.sfc_mil > 0.0 && eng_data.mil_thrust_n > 0.0) {
                     mil_flow_rate = (eng_data.mil_thrust_n * eng_data.sfc_mil) / 3600.0;
                 }
            } else {
                 spdlog::warn("Unit {} references unknown engine {}", unit_name, def.engine_ref);
            }
        } else if (def.type == UnitType::Aircraft || def.has_flight_model) {
             // Fallback Generic Propulsion
             e.set<Propulsion>({40000.0, 70000.0, 0.0, false});
        }
        if (def.airframe.has_tuning) {
            AeroTuning tuning = def.airframe.tuning;
            tuning.enabled = true;
            e.set<AeroTuning>(tuning);
        }
        if (def.type == UnitType::Aircraft || def.has_flight_model) {
            e.set<StallState>({});
        }
        double internal_fuel = (def.airframe.max_fuel_kg > 0) ? def.airframe.max_fuel_kg : 0.0;
        if (def.type == UnitType::Aircraft || def.has_flight_model || internal_fuel > 0.0) {
            if (const Propulsion* propulsion = e.get<Propulsion>()) {
                if (propulsion->mil_thrust_n > 0.0) {
                    if (const EngineTuning* tuning = e.get<EngineTuning>()) {
                        if (tuning->tsfc_mil_kg_per_nh > 0.0) {
                            mil_flow_rate = (propulsion->mil_thrust_n * tuning->tsfc_mil_kg_per_nh) / 3600.0;
                        }
                        if (tuning->tsfc_mil_kg_per_nh > 1.0e-9) {
                            ab_mult = std::max(1.0, tuning->tsfc_ab_kg_per_nh / tuning->tsfc_mil_kg_per_nh);
                        }
                    }
                }
            }
            e.set<FuelSystem>({
                 internal_fuel, // Current
                 internal_fuel, // Max
                 0.0, 0.0,      // External
                 0.0, false,    // State
                 mil_flow_rate,
                 ab_mult
            });
        }

        // Initialize EW Suite
        if (!def.ew_suite_ref.empty()) {
            auto ew_it = definitions_.find(def.ew_suite_ref);
            if (ew_it != definitions_.end()) {
                const auto& ew_def = ew_it->second;
                e.set<RWR>(ew_def.rwr_data);
                e.set<ESMReceiver>(ew_def.esm_data);
                e.set<Jammer>(ew_def.jammer_data);
                e.set<Countermeasures>(ew_def.cms_data);
            } else {
                spdlog::warn("Unit {} references unknown EW suite {}", unit_name, def.ew_suite_ref);
            }
        } else {
             // Defaults or Minimal
             e.set<RWR>({-80.0, {}, {}, false});
             e.set<ESMReceiver>({-85.0, 250000.0, true, {}});
             e.set<Jammer>({false, 0.0, 0.0, JammingType::NoiseBarrage, 0.0});
             e.set<Countermeasures>({0, 0, 1.0, 0.0, false});
        }
        if (def.has_esm_data) {
            e.set<ESMReceiver>(def.esm_data);
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
        if (def.has_ship_platform && def.ship_platform.displacement_full_load_kg > 0.0) {
            empty_mass = def.ship_platform.displacement_full_load_kg;
        } else if (def.has_submarine_platform && def.submarine_platform.submerged_displacement_kg > 0.0) {
            empty_mass = def.submarine_platform.submerged_displacement_kg;
        }
        double drag_coef = (def.airframe.drag_coefficient > 0) ? def.airframe.drag_coefficient : 0.02;
        double ref_area = (def.airframe.reference_area > 0) ? def.airframe.reference_area : 30.0;
        double span_m = (def.airframe.wingspan_m > 1.0) ? def.airframe.wingspan_m : 10.0;
        if (def.has_ship_platform && def.ship_platform.beam_m > 0.0) {
            ref_area = std::max(1.0, def.ship_platform.length_m * def.ship_platform.draft_m);
            span_m = def.ship_platform.beam_m;
        } else if (def.has_submarine_platform && def.submarine_platform.beam_m > 0.0) {
            ref_area = std::max(1.0, def.submarine_platform.length_m * def.submarine_platform.draft_m);
            span_m = def.submarine_platform.beam_m;
        }
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
        
        if (def.type != UnitType::Ship && def.type != UnitType::Submarine) {
            e.set<ForceAccumulator>({});
            e.set<AeroState>({});
        }
        
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
        if (def.type != UnitType::Ship && def.type != UnitType::Submarine) {
            e.set<Inertia>(inertia_guess);
            e.set<AngularVelocity>({0.0, 0.0, 0.0});
        }
        if (def.type != UnitType::Ship && def.type != UnitType::Submarine) {
            e.set<GroundState>({false, 0.0}); // Initialize Ground Contact
            e.set<GearState>({true, 0.0, false, 0.0, true}); // gear_down, stress, collapsed, stress_rate, on_runway
        }
        
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
        if (def.has_naval_weapon_system) {
            e.set<NavalWeaponSystem>(def.naval_weapon_system);
        }
        if (def.has_ship_platform) {
            e.set<ShipPlatform>(def.ship_platform);
        }
        if (def.has_submarine_platform) {
            e.set<SubmarinePlatform>(def.submarine_platform);
        }
        if (def.has_embarked_air_ops) {
            e.set<EmbarkedAirOps>(def.embarked_air_ops);
        }
        if (def.has_naval_stores) {
            e.set<NavalStores>({
                def.naval_stores.fuel_units_current,
                def.naval_stores.fuel_units_max,
                def.naval_stores.missile_units_current,
                def.naval_stores.missile_units_max,
                def.naval_stores.dry_cargo_units_current,
                def.naval_stores.dry_cargo_units_max,
                def.naval_stores.can_receive_underway,
                def.naval_stores.can_provide_underway
            });
            e.set<ResupplyState>({
                0.0,
                false,
                false,
                ResupplyKind::BaseRefuel,
                0,
                NavalResupplyStage::None
            });
        }
        if (def.has_command_link) {
            e.set<CommandLink>(def.command_link);
            e.set<PendingMovementCommand>(make_pending_movement_command());
            e.set<PendingActionCommand>(make_pending_action_command());
            e.set<PendingMissionCommand>(make_pending_mission_command());
            e.set<MissionCommandPendingQueue>(make_mission_command_pending_queue());
        }
        // ActionCommand
        e.set<ActionCommand>(make_action_command());
    
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
            e.set<MovementCommand>(make_legacy_autopilot_movement_command(heading_init, speed, params.z));
            e.set<LaggedCommand>(make_lagged_command(heading_init, speed, params.z));
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
            e.set<PlatformDamageState>({});
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
            e.set<PlatformDamageState>({});
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
                500.0, // Default 500km range
                std::max(0, def.data_link_max_reports_per_update),
                std::max(0, def.data_link_max_messages_per_update)
            });
            e.set<CommQueue>({}); // Enable messaging with an explicit empty inbox
        } else {
            e.remove<DataLink>();
        }

        // Initialize Track Database
        e.set<TrackDatabase>({});

        if (def.has_embarked_air_ops && def.embarked_air_ops.enabled && !def.embarked_air_ops.helo_unit_name.empty()) {
            auto helo_it = definitions_.find(def.embarked_air_ops.helo_unit_name);
            if (helo_it != definitions_.end()) {
                const double heading_rad = Math::to_radians(heading_init);
                const double right_rad = Math::to_radians(heading_init + 90.0);
                SpawnParams helo_params = params;
                helo_params.x += std::sin(heading_rad) * def.embarked_air_ops.launch_offset_forward_m +
                                 std::sin(right_rad) * def.embarked_air_ops.launch_offset_starboard_m;
                helo_params.y += std::cos(heading_rad) * def.embarked_air_ops.launch_offset_forward_m +
                                 std::cos(right_rad) * def.embarked_air_ops.launch_offset_starboard_m;
                helo_params.z = params.z;
                helo_params.vx = 0.0;
                helo_params.vy = 0.0;
                helo_params.vz = 0.0;
                auto helo = spawn(ecs, def.embarked_air_ops.helo_unit_name, helo_params);
                if (helo.is_valid()) {
                    helo.child_of(e);
                    MissionCommand helo_cmd{};
                    helo.set<MissionCommand>(helo_cmd);
                    if (EmbarkedAirOps* ops = e.get_mut<EmbarkedAirOps>()) {
                        ops->active_helo_entity_id = helo.id();
                        ops->helo_airborne = false;
                    }
                } else {
                    spdlog::warn("Unit {} failed to pre-spawn embarked helo {}", unit_name, def.embarked_air_ops.helo_unit_name);
                }
            } else {
                spdlog::warn("Unit {} references unknown embarked helo {}", unit_name, def.embarked_air_ops.helo_unit_name);
            }
        }

        // Initialize Logistics Node for Facilities/Carriers
        if (def.type == UnitType::Facility || def.name.find("Airbase") != std::string::npos) {
             e.set<LogisticsNode>({
                 1000.0, // 1km radius
                 true,   // infinite
                 false,
                 0.0,
                 0.0,
                 0.0,
                 0.0,
                 0.0,
                 0.0
             });
        } else if (def.has_naval_logistics) {
             e.set<LogisticsNode>({
                 0.0,
                 false,
                 def.naval_logistics.underway_replenishment_enabled,
                 def.naval_logistics.min_separation_m,
                 def.naval_logistics.max_separation_m,
                 def.naval_logistics.max_relative_speed_mps,
                 def.naval_logistics.transfer_rate_fuel_units_per_s,
                 def.naval_logistics.transfer_rate_missile_units_per_s,
                 def.naval_logistics.transfer_rate_dry_cargo_units_per_s
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
