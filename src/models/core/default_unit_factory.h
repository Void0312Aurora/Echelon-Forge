#pragma once

#include <cctype>
#include <algorithm>
#include <cmath>
#include <limits>
#include <unordered_map>
#include <string_view>

#include <spdlog/spdlog.h>

#include "components/command/command_link.h"
#include "components/command/command_link_qos.h"
#include "components/command/default_factory_legacy_spawn_compat.h"
#include "components/basic/common.h"
#include "components/combat/health.h"
#include "components/physics/performance.h"
#include "components/combat/scoring.h"
#include "components/systems/sensor.h"
#include "components/physics/dynamics.h"
#include "components/physics/forces.h"
#include "components/combat/damage.h"
#include "components/combat/weapon.h"
#include "components/physics/instruments.h"
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
#include "runtime/contracts/platform_capability_contracts.h"
#include "models/weapons/missile_guidance_types.h"

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

inline double default_factory_finite_or(double candidate, double fallback) {
    return std::isfinite(candidate) ? candidate : fallback;
}

inline double default_factory_positive_or(double candidate, double fallback) {
    return (std::isfinite(candidate) && candidate > 0.0) ? candidate : fallback;
}

inline double default_factory_nonnegative_or(double candidate, double fallback) {
    return (std::isfinite(candidate) && candidate >= 0.0) ? candidate : fallback;
}

inline double default_factory_default_missile_propellant_mass(double total_mass_kg) {
    const double scaled = total_mass_kg * MissileGuidanceDefaults::kPropellantMassFraction;
    return std::clamp(
        scaled,
        MissileGuidanceDefaults::kMinPropellantMassKg,
        std::max(MissileGuidanceDefaults::kMinPropellantMassKg, total_mass_kg * 0.55));
}

namespace default_unit_factory_detail {

inline std::string make_platform_token(std::string_view value) {
    std::string token;
    token.reserve(value.size());

    bool last_was_underscore = false;
    for (unsigned char ch : value) {
        if (std::isalnum(ch) != 0) {
            token.push_back(static_cast<char>(std::tolower(ch)));
            last_was_underscore = false;
            continue;
        }
        if (!last_was_underscore) {
            token.push_back('_');
            last_was_underscore = true;
        }
    }

    while (!token.empty() && token.front() == '_') {
        token.erase(token.begin());
    }
    while (!token.empty() && token.back() == '_') {
        token.pop_back();
    }
    if (token.empty()) {
        return "unnamed";
    }
    return token;
}

inline std::string make_bundle_id(std::string_view type_name) {
    return "platform.bundle." + make_platform_token(type_name);
}

inline std::string make_plan_id(std::string_view type_name) {
    return "platform.plan." + make_platform_token(type_name);
}

inline std::string make_capability_id(
    std::string_view type_name,
    std::string_view capability_type
) {
    return "platform.capability." + make_platform_token(type_name) + "." +
        make_platform_token(capability_type);
}

inline std::string make_evidence_ref(
    std::string_view type_name,
    std::string_view evidence_type
) {
    return "platform.evidence." + make_platform_token(type_name) + "." +
        make_platform_token(evidence_type);
}

inline std::string make_definition_ref(std::string_view type_name) {
    return "platform.definition." + make_platform_token(type_name);
}

inline void append_unique(std::vector<std::string>& values, std::string value) {
    if (std::find(values.begin(), values.end(), value) == values.end()) {
        values.push_back(std::move(value));
    }
}

inline runtime::platform_capabilities::Capability make_capability(
    std::string_view type_name,
    std::string_view family,
    std::string_view capability_type,
    std::vector<std::string> evidence_refs,
    bool required = true,
    bool supported = true,
    std::string unsupported_reason = {}
) {
    runtime::platform_capabilities::Capability capability{};
    capability.capability_id = make_capability_id(type_name, capability_type);
    capability.family = std::string(family);
    capability.capability_type = std::string(capability_type);
    capability.implementation_ref = make_definition_ref(type_name);
    capability.evidence_refs = std::move(evidence_refs);
    capability.required = required;
    capability.supported = supported;
    capability.unsupported_reason = std::move(unsupported_reason);
    return capability;
}

inline void append_capability(
    runtime::platform_capabilities::CapabilityBundle& bundle,
    runtime::platform_capabilities::Capability capability
) {
    for (const auto& evidence : capability.evidence_refs) {
        append_unique(bundle.evidence_refs, evidence);
    }
    append_unique(bundle.evidence_refs, bundle.template_evidence_ref);
    bundle.capabilities.push_back(std::move(capability));
}

} // namespace default_unit_factory_detail

class DefaultUnitFactory : public IUnitFactory {
public:
    using Capability = runtime::platform_capabilities::Capability;
    using CapabilityBundle = runtime::platform_capabilities::CapabilityBundle;
    using PlatformCapabilityValidationResult =
        runtime::platform_capabilities::PlatformCapabilityValidationResult;
    using ResolvedPlatformSpawnPlan =
        runtime::platform_capabilities::ResolvedPlatformSpawnPlan;

    explicit DefaultUnitFactory(const std::string& config_path = std::string()) {
        UnitDefinition aircraft{};
        aircraft.type = UnitType::Aircraft;
        aircraft.name = "Aircraft";
        aircraft.health = {100.0, 100.0, false, false, false};
        aircraft.has_sensor = true;
        aircraft.sensor = make_unit_definition_default_sensor_preset(
            30000.0, 120.0, 1.0, 0.9, 1.0, 25.0, 2.0, 0.3, static_cast<int>(SensorType::Radar));
        aircraft.has_flight_model = true;
        aircraft.flight_model = {600.0, 50.0, 20.0, 50.0, 300.0, 9.0, -3.0, 80.0, 70.0, 20.0};
        aircraft.has_score = true;
        aircraft.score = {0.0, 0, 0, 0};
        aircraft.has_ammo = true;
        aircraft.ammo = {4, 4};
        aircraft.has_command_link = true;
        aircraft.command_link = {0.2, 0.0};
        aircraft.has_data_link = true;
        aircraft.data_link_network_id = 0; // Dynamic assignment? Or per side? Usually side-based.
        aircraft.airframe.has_tuning = true;
        aircraft.airframe.tuning = flight_dynamics::default_aero_tuning();
        definitions_.emplace(aircraft.name, aircraft);

        UnitDefinition missile{};
        missile.type = UnitType::Missile;
        missile.name = "Missile";
        missile.health = {100.0, 100.0, false, false, false};
        missile.has_sensor = true;
        missile.sensor = make_unit_definition_default_sensor_preset(
            30000.0, 120.0, 0.2, 0.95, 0.5, 15.0, 0.5, 0.2, static_cast<int>(SensorType::Radar));
        missile.has_flight_model = true;
        missile.flight_model = {1200.0, 100.0, 40.0, 100.0, 600.0, 30.0, 0.0, 0.0, 0.0, 0.0};
        missile.has_score = true;
        missile.score = {0.0, 0, 0, 0};
        missile.has_ammo = false;
        missile.ammo = {0, 0};
        missile.has_command_link = false;
        missile.command_link = {0.0, 0.0};
        missile.has_data_link = true; // Missiles often have DL (Mid-course updates)
        missile.data_link_network_id = 0;
        missile.has_missile_tuning = true;
        missile.missile_tuning.max_speed = missile.flight_model.max_speed;
        missile.missile_tuning.turn_rate = missile.flight_model.max_turn_rate;
        missile.missile_tuning.seeker_fov_deg = missile.sensor.fov_deg;
        missile.missile_tuning.seeker_lock_range = missile.sensor.max_range;
        missile.missile_tuning.sensor_max_range = missile.sensor.max_range;
        missile.missile_tuning.sensor_fov_deg = missile.sensor.fov_deg;
        missile.missile_tuning.sensor_scan_period = missile.sensor.scan_period;
        missile.missile_tuning.sensor_detection_prob = missile.sensor.detection_prob;
        missile.missile_tuning.sensor_bearing_noise_std = missile.sensor.bearing_noise_std;
        missile.missile_tuning.sensor_range_noise_std = missile.sensor.range_noise_std;
        missile.missile_tuning.sensor_track_memory_s = missile.sensor.track_memory_s;
        missile.missile_tuning.seeker_type = static_cast<int>(SensorType::Radar);
        missile.missile_tuning.track_break_time_s = MissileGuidanceDefaults::kTrackMemoryTimeoutS;
        missile.missile_tuning.boost_time_s = MissileGuidanceDefaults::kBoostTimeS;
        missile.missile_tuning.sustain_time_s = MissileGuidanceDefaults::kSustainTimeS;
        missile.missile_tuning.reference_area_m2 = MissileGuidanceDefaults::kReferenceAreaM2;
        missile.missile_tuning.cd0_subsonic = MissileGuidanceDefaults::kCd0Subsonic;
        missile.missile_tuning.cd0_supersonic = MissileGuidanceDefaults::kCd0Supersonic;
        missile.missile_tuning.induced_drag_k = MissileGuidanceDefaults::kInducedDragScale;
        missile.missile_tuning.max_lateral_g = missile.flight_model.max_g;
        missile.missile_tuning.autopilot_tau_s = MissileGuidanceDefaults::kAutopilotTauS;
        missile.missile_tuning.max_accel_response_g_per_s = MissileGuidanceDefaults::kAccelResponseGps;
        definitions_.emplace(missile.name, missile);

        UnitDefinition ship{};
        ship.type = UnitType::Ship;
        ship.name = "Ship";
        ship.health = {100.0, 100.0, false, false, false};
        ship.has_sensor = true;
        ship.sensor = make_unit_definition_default_sensor_preset(
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
        facility.sensor = make_unit_definition_default_sensor_preset(
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
        c2node.sensor = make_unit_definition_default_sensor_preset(
            400000.0, 360.0, 5.0, 0.99, 0.5, 50.0, 10.0, 0.0, static_cast<int>(SensorType::Radar));
        c2node.has_flight_model = true; // It flies
        c2node.flight_model = {250.0, 100.0, 5.0, 5.0, 50.0, 2.0, -1.0, 70.0, 60.0, 10.0}; // Slow, low G
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

    [[nodiscard]] CapabilityBundle build_platform_capability_bundle_template(
        std::string_view type_name,
        const UnitDefinition& def
    ) const {
        using namespace runtime::platform_capabilities;
        using namespace default_unit_factory_detail;

        CapabilityBundle bundle{};
        bundle.bundle_id = make_bundle_id(type_name);
        bundle.source_type_name = std::string(type_name);
        bundle.template_evidence_ref = make_evidence_ref(type_name, "bundle_template");
        bundle.compatibility_path_preserved = true;
        bundle.diagnostics_reason = "type_name_to_capability_bundle_template";
        bundle.evidence_refs = {
            bundle.template_evidence_ref,
            make_evidence_ref(type_name, "definition_snapshot"),
        };

        const auto add_sensing_capability = [&](std::string_view capability_type,
                                                std::vector<std::string> evidence_refs) {
            append_capability(bundle, make_capability(
                type_name,
                kCapabilityFamilySensing,
                capability_type,
                std::move(evidence_refs)));
        };
        const auto add_mobility_capability = [&](std::string_view capability_type,
                                                 std::vector<std::string> evidence_refs) {
            append_capability(bundle, make_capability(
                type_name,
                kCapabilityFamilyMobility,
                capability_type,
                std::move(evidence_refs)));
        };
        const auto add_communication_capability = [
        ](CapabilityBundle& bundle_ref,
          std::string_view type_name_ref,
          std::string_view capability_type,
          std::vector<std::string> evidence_refs) {
            append_capability(bundle_ref, make_capability(
                type_name_ref,
                kCapabilityFamilyCommunication,
                capability_type,
                std::move(evidence_refs)));
        };
        const auto add_command_capability = [
        ](CapabilityBundle& bundle_ref,
          std::string_view type_name_ref,
          std::string_view capability_type,
          std::vector<std::string> evidence_refs) {
            append_capability(bundle_ref, make_capability(
                type_name_ref,
                kCapabilityFamilyCommand,
                capability_type,
                std::move(evidence_refs)));
        };
        const auto add_launching_capability = [&](std::string_view capability_type,
                                                  std::vector<std::string> evidence_refs) {
            append_capability(bundle, make_capability(
                type_name,
                kCapabilityFamilyLaunching,
                capability_type,
                std::move(evidence_refs)));
        };
        const auto add_survivability_capability = [&](std::string_view capability_type,
                                                      std::vector<std::string> evidence_refs) {
            append_capability(bundle, make_capability(
                type_name,
                kCapabilityFamilySurvivability,
                capability_type,
                std::move(evidence_refs)));
        };
        const auto add_doctrine_capability = [&](std::string_view capability_type,
                                                 std::vector<std::string> evidence_refs) {
            append_capability(bundle, make_capability(
                type_name,
                kCapabilityFamilyDoctrine,
                capability_type,
                std::move(evidence_refs)));
        };

        if (!def.sensor_refs.empty()) {
            add_sensing_capability(
                "sensor_refs",
                {
                    make_evidence_ref(type_name, "sensor_refs"),
                    make_evidence_ref(type_name, "sensor_ref"),
                });
        }
        if (!def.sensor_ref.empty()) {
            add_sensing_capability(
                "sensor_ref",
                {
                    make_evidence_ref(type_name, "sensor_ref"),
                });
        }
        if (def.has_sensor) {
            add_sensing_capability(
                "inline_sensor",
                {
                    make_evidence_ref(type_name, "sensor_inline"),
                    make_evidence_ref(type_name, "sensor"),
                });
        }
        if (!def.mounted_sensors.mounts.empty()) {
            add_sensing_capability(
                "mounted_sensors",
                {
                    make_evidence_ref(type_name, "mounted_sensors"),
                });
        }
        if (def.has_sonar) {
            add_sensing_capability(
                "sonar",
                {
                    make_evidence_ref(type_name, "sonar"),
                });
        }
        if (!def.mounted_sonars.mounts.empty()) {
            add_sensing_capability(
                "mounted_sonars",
                {
                    make_evidence_ref(type_name, "mounted_sonars"),
                });
        }

        if (def.has_ship_platform) {
            add_mobility_capability(
                "ship_platform_mobility",
                {
                    make_evidence_ref(type_name, "ship_platform"),
                    make_evidence_ref(type_name, "mobility"),
                });
            add_survivability_capability(
                "ship_platform_survivability",
                {
                    make_evidence_ref(type_name, "ship_platform"),
                    make_evidence_ref(type_name, "survivability"),
                });
        }
        if (def.has_submarine_platform) {
            add_mobility_capability(
                "submarine_platform_mobility",
                {
                    make_evidence_ref(type_name, "submarine_platform"),
                    make_evidence_ref(type_name, "mobility"),
                });
            add_survivability_capability(
                "submarine_platform_survivability",
                {
                    make_evidence_ref(type_name, "submarine_platform"),
                    make_evidence_ref(type_name, "survivability"),
                });
        }
        if (def.type == UnitType::Ground) {
            add_mobility_capability(
                "ground_mobility_flat_deferred",
                {
                    make_evidence_ref(type_name, "ground_platform"),
                    make_evidence_ref(type_name, "ground_mobility_flat_deferred"),
                    make_evidence_ref(type_name, "movement_behavior_deferred"),
                });
            add_doctrine_capability(
                "land_tactics",
                {
                    make_evidence_ref(type_name, "army_service_profile"),
                    make_evidence_ref(type_name, "land_tactics"),
                });
        }
        if (def.airframe.empty_mass_kg > 0.0 || def.has_flight_model || def.type == UnitType::Aircraft) {
            add_mobility_capability(
                "airframe",
                {
                    make_evidence_ref(type_name, "airframe"),
                    make_evidence_ref(type_name, "flight_model"),
                });
        }
        if (def.has_landing_gear) {
            add_mobility_capability(
                "landing_gear",
                {
                    make_evidence_ref(type_name, "landing_gear"),
                });
        }
        if (def.has_naval_stores) {
            add_survivability_capability(
                "naval_stores",
                {
                    make_evidence_ref(type_name, "naval_stores"),
                });
        }
        if (def.has_naval_weapon_system) {
            add_launching_capability(
                "naval_weapon_system",
                {
                    make_evidence_ref(type_name, "naval_weapon_system"),
                });
        }
        if (!def.default_loadout.empty()) {
            add_launching_capability(
                "default_loadout",
                {
                    make_evidence_ref(type_name, "default_loadout"),
                });
        }
        if (def.has_command_link) {
            add_command_capability(
                bundle,
                type_name,
                "command_link",
                {
                    make_evidence_ref(type_name, "command_link"),
                });
        }
        if (def.has_data_link) {
            add_communication_capability(
                bundle,
                type_name,
                "data_link",
                {
                    make_evidence_ref(type_name, "data_link"),
                    make_evidence_ref(type_name, "data_link_network_id"),
                });
        }
        if (def.has_embarked_air_ops) {
            add_doctrine_capability(
                "embarked_air_ops",
                {
                    make_evidence_ref(type_name, "embarked_air_ops"),
                });
        }
        if (def.has_ship_platform || def.has_submarine_platform || def.has_naval_weapon_system) {
            add_doctrine_capability(
                "naval_platform_doctrine",
                {
                    make_evidence_ref(type_name, "naval_platform_doctrine"),
                    make_evidence_ref(type_name, "naval_weapon_system"),
                });
        }
        if (def.damage_model.hitboxes.empty() == false || def.health.current_hp > 0.0) {
            add_survivability_capability(
                "health_and_damage_model",
                {
                    make_evidence_ref(type_name, "health"),
                    make_evidence_ref(type_name, "damage_model"),
                });
        }
        if (def.has_aircraft_vulnerability) {
            add_survivability_capability(
                aircraft_vulnerability_has_calibrated_evidence(def.aircraft_vulnerability)
                    ? "aircraft_vulnerability_calibrated_profile"
                    : "aircraft_vulnerability_synthetic_profile",
                {
                    make_evidence_ref(type_name, "damage_model.vulnerability"),
                    aircraft_vulnerability_has_calibrated_evidence(def.aircraft_vulnerability)
                        ? make_evidence_ref(type_name, "damage_model.vulnerability.calibrated_dataset")
                        : make_evidence_ref(type_name, "damage_model.vulnerability.synthetic_scaffold"),
                });
        }

        return bundle;
    }

    [[nodiscard]] PlatformCapabilityValidationResult validate_platform_capability_bundle_template(
        std::string_view type_name,
        const UnitDefinition& def
    ) const {
        return runtime::platform_capabilities::validate_capability_bundle(
            build_platform_capability_bundle_template(type_name, def));
    }

    [[nodiscard]] ResolvedPlatformSpawnPlan resolve_platform_spawn_plan(
        std::string_view type_name,
        const UnitDefinition& def
    ) const {
        using namespace runtime::platform_capabilities;
        using namespace default_unit_factory_detail;

        const CapabilityBundle bundle = build_platform_capability_bundle_template(type_name, def);
        const PlatformCapabilityValidationResult bundle_validation =
            runtime::platform_capabilities::validate_capability_bundle(bundle);

        ResolvedPlatformSpawnPlan plan{};
        plan.plan_id = make_plan_id(type_name);
        plan.source_request_kind = std::string(kPlatformSpawnRequestKindTypeNameCompatibility);
        plan.source_type_name = std::string(type_name);
        plan.capability_bundle_id = bundle.bundle_id;
        plan.resolved_platform_definition_ref = make_definition_ref(type_name);
        plan.materialization_strategy =
            std::string(kPlatformMaterializationStrategyFactoryCompatibility);
        plan.template_evidence_ref = bundle.template_evidence_ref;
        plan.resolution_evidence_ref = make_evidence_ref(type_name, "plan_resolution");
        plan.materialization_evidence_ref = make_evidence_ref(type_name, "factory_materialization");
        plan.evidence_refs = bundle.evidence_refs;
        append_unique(plan.evidence_refs, plan.resolution_evidence_ref);
        append_unique(plan.evidence_refs, plan.materialization_evidence_ref);
        plan.resolved_capabilities = bundle.capabilities;
        plan.compatibility_path_preserved = true;
        plan.admitted = bundle_validation.valid;
        if (!bundle_validation.valid) {
            plan.rejection_reason = bundle_validation.rejection_reason;
            plan.diagnostics_reason = bundle_validation.rejection_reason;
            return plan;
        }

        plan.diagnostics_reason = "type_name_to_resolved_platform_spawn_plan";
        return plan;
    }

    [[nodiscard]] PlatformCapabilityValidationResult validate_resolved_platform_spawn_plan(
        std::string_view type_name,
        const UnitDefinition& def
    ) const {
        return runtime::platform_capabilities::validate_resolved_platform_spawn_plan(
            resolve_platform_spawn_plan(type_name, def));
    }

    [[nodiscard]] ResolvedPlatformSpawnPlan resolve_platform_spawn_plan_for_type_name(
        std::string_view type_name
    ) const {
        using namespace runtime::platform_capabilities;
        using namespace default_unit_factory_detail;

        const std::string lookup_name(type_name);
        auto it = definitions_.find(lookup_name);
        if (it != definitions_.end()) {
            return resolve_platform_spawn_plan(type_name, it->second);
        }

        ResolvedPlatformSpawnPlan plan{};
        plan.plan_id = make_plan_id(type_name);
        plan.source_request_kind = std::string(kPlatformSpawnRequestKindTypeNameCompatibility);
        plan.source_type_name = lookup_name;
        plan.capability_bundle_id = make_bundle_id(type_name);
        plan.compatibility_path_preserved = true;
        plan.admitted = false;
        plan.rejection_reason = "resolved_platform_spawn_plan_type_name_not_found";
        plan.diagnostics_reason = plan.rejection_reason;
        return plan;
    }

    [[nodiscard]] PlatformCapabilityValidationResult validate_resolved_platform_spawn_plan_for_type_name(
        std::string_view type_name
    ) const {
        return runtime::platform_capabilities::validate_resolved_platform_spawn_plan(
            resolve_platform_spawn_plan_for_type_name(type_name));
    }

    const UnitDefinition* get_definition(const std::string& name) const override {
        auto it = definitions_.find(name);
        if (it == definitions_.end()) return nullptr;
        return &it->second;
    }

    flecs::entity spawn(flecs::world& ecs,
                        const std::string& unit_name,
                        const SpawnParams& params) override {
        const auto resolved_spawn_plan =
            resolve_platform_spawn_plan_for_type_name(unit_name);
        const auto plan_validation =
            runtime::platform_capabilities::validate_resolved_platform_spawn_plan(
                resolved_spawn_plan);
        if (!plan_validation.valid || !resolved_spawn_plan.admitted) {
            const std::string rejection_reason =
                !plan_validation.valid
                    ? plan_validation.rejection_reason
                    : resolved_spawn_plan.rejection_reason;
            spdlog::error(
                "Spawn gate rejected type_name {} via resolved platform spawn plan: {}",
                unit_name,
                rejection_reason.empty() ? "unspecified_rejection" : rejection_reason);
            return flecs::entity::null();
        }

        auto it = definitions_.find(unit_name);
        if (it == definitions_.end()) {
            spdlog::error(
                "Spawn gate admitted type_name {} but definition lookup failed during materialization",
                unit_name);
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
            e.set<StallState>(def.has_stall_state ? def.stall_state : StallState{});
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
            if (def.type != UnitType::Missile) {
                e.set<AeroState>({});
            }
        }
        
        if (def.type != UnitType::Missile) {
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
            e.set<InstrumentState>(initial_instruments);
        }

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

        if (def.type == UnitType::Missile) {
            const double missile_max_speed = def.has_missile_tuning
                ? default_factory_positive_or(def.missile_tuning.max_speed, def.flight_model.max_speed)
                : def.flight_model.max_speed;
            const double missile_turn_rate = def.has_missile_tuning
                ? default_factory_positive_or(def.missile_tuning.turn_rate, def.flight_model.max_turn_rate)
                : def.flight_model.max_turn_rate;
            const double seeker_fov_deg = def.has_missile_tuning
                ? default_factory_positive_or(
                    def.missile_tuning.seeker_fov_deg,
                    default_factory_positive_or(def.missile_tuning.sensor_fov_deg, def.sensor.fov_deg))
                : def.sensor.fov_deg;
            const double seeker_lock_range = def.has_missile_tuning
                ? default_factory_positive_or(
                    def.missile_tuning.seeker_lock_range,
                    default_factory_positive_or(def.missile_tuning.sensor_max_range, def.sensor.max_range))
                : def.sensor.max_range;
            const double missile_total_mass_kg = std::max(
                1.0,
                def.mass_kg > 0.0 ? def.mass_kg : 80.0);
            double propellant_mass_kg = def.has_missile_tuning
                ? default_factory_nonnegative_or(
                    def.missile_tuning.propellant_mass_kg,
                    default_factory_default_missile_propellant_mass(missile_total_mass_kg))
                : default_factory_default_missile_propellant_mass(missile_total_mass_kg);
            propellant_mass_kg = std::clamp(
                propellant_mass_kg,
                0.0,
                std::max(0.0, missile_total_mass_kg - 1.0));
            const double empty_mass_kg = std::max(1.0, missile_total_mass_kg - propellant_mass_kg);
            const double reference_area_m2 = def.has_missile_tuning
                ? default_factory_positive_or(
                    def.missile_tuning.reference_area_m2,
                    MissileGuidanceDefaults::kReferenceAreaM2)
                : MissileGuidanceDefaults::kReferenceAreaM2;
            const double current_speed_mps = std::sqrt(
                params.vx * params.vx + params.vy * params.vy + params.vz * params.vz);
            const double current_time = 0.0;

            Missile missile_runtime{
                0,
                0,
                missile_max_speed,
                missile_turn_rate,
                def.has_missile_tuning
                    ? default_factory_positive_or(def.missile_tuning.fuse_distance, 300.0)
                    : 300.0,
                def.has_missile_tuning
                    ? default_factory_positive_or(def.missile_tuning.damage, 120.0)
                    : 120.0,
                seeker_fov_deg,
                seeker_lock_range,
                def.has_missile_tuning
                    ? default_factory_nonnegative_or(def.missile_tuning.guidance_delay_s, 0.0)
                    : 0.0,
                def.has_missile_tuning
                    ? default_factory_nonnegative_or(def.missile_tuning.guidance_update_period_s, 0.0)
                    : 0.0,
                -1.0,
                current_time,
                def.has_missile_tuning
                    ? default_factory_positive_or(def.missile_tuning.max_flight_time_s, 15.0)
                    : 15.0,
                def.has_missile_tuning
                    ? default_factory_positive_or(def.missile_tuning.nav_gain, 3.0)
                    : 3.0,
                true
            };
            missile_runtime.warhead_profile = def.has_missile_tuning && def.missile_tuning.has_warhead_profile
                ? def.missile_tuning.warhead_profile
                : make_synthetic_warhead_profile(
                    missile_runtime.damage,
                    missile_runtime.fuse_distance);
            missile_runtime.p0_runtime_initialized = true;
            missile_runtime.seeker_has_valid_track = false;
            missile_runtime.seeker_has_range = false;
            missile_runtime.seeker_mode = static_cast<int>(MissileSeekerMode::Ballistic);
            missile_runtime.filtered_bearing_deg = 0.0;
            missile_runtime.filtered_elevation_deg = 0.0;
            missile_runtime.filtered_range_m = 0.0;
            missile_runtime.filtered_closing_speed_mps = 0.0;
            missile_runtime.bearing_rate_deg_s = 0.0;
            missile_runtime.elevation_rate_deg_s = 0.0;
            missile_runtime.last_track_time_s = -1.0;
            missile_runtime.track_memory_timeout_s = def.has_missile_tuning
                ? default_factory_nonnegative_or(
                    def.missile_tuning.track_break_time_s,
                    MissileGuidanceDefaults::kTrackMemoryTimeoutS)
                : MissileGuidanceDefaults::kTrackMemoryTimeoutS;
            missile_runtime.current_speed_mps = current_speed_mps;
            missile_runtime.commanded_lateral_accel_mps2 = 0.0;
            missile_runtime.achieved_lateral_accel_mps2 = 0.0;
            missile_runtime.boost_duration_s = def.has_missile_tuning
                ? default_factory_nonnegative_or(def.missile_tuning.boost_time_s, MissileGuidanceDefaults::kBoostTimeS)
                : MissileGuidanceDefaults::kBoostTimeS;
            missile_runtime.sustain_duration_s = def.has_missile_tuning
                ? default_factory_nonnegative_or(def.missile_tuning.sustain_time_s, MissileGuidanceDefaults::kSustainTimeS)
                : MissileGuidanceDefaults::kSustainTimeS;
            missile_runtime.burnout_time_s =
                current_time + missile_runtime.boost_duration_s + missile_runtime.sustain_duration_s;
            missile_runtime.guidance_bearing_filter_tau_s = def.has_missile_tuning
                ? default_factory_nonnegative_or(
                    def.missile_tuning.bearing_filter_tau_s,
                    MissileGuidanceDefaults::kTrackFilterTauS)
                : MissileGuidanceDefaults::kTrackFilterTauS;
            missile_runtime.guidance_elevation_filter_tau_s = def.has_missile_tuning
                ? default_factory_nonnegative_or(
                    def.missile_tuning.elevation_filter_tau_s,
                    MissileGuidanceDefaults::kTrackFilterTauS)
                : MissileGuidanceDefaults::kTrackFilterTauS;
            missile_runtime.guidance_range_filter_tau_s = def.has_missile_tuning
                ? default_factory_nonnegative_or(
                    def.missile_tuning.range_filter_tau_s,
                    MissileGuidanceDefaults::kTrackFilterTauS)
                : MissileGuidanceDefaults::kTrackFilterTauS;
            missile_runtime.guidance_boost_thrust_n = def.has_missile_tuning
                ? def.missile_tuning.boost_thrust_n
                : std::numeric_limits<double>::quiet_NaN();
            missile_runtime.guidance_sustain_thrust_n = def.has_missile_tuning
                ? def.missile_tuning.sustain_thrust_n
                : std::numeric_limits<double>::quiet_NaN();
            missile_runtime.guidance_cd0_subsonic = def.has_missile_tuning
                ? def.missile_tuning.cd0_subsonic
                : MissileGuidanceDefaults::kCd0Subsonic;
            missile_runtime.guidance_cd0_supersonic = def.has_missile_tuning
                ? def.missile_tuning.cd0_supersonic
                : MissileGuidanceDefaults::kCd0Supersonic;
            missile_runtime.guidance_induced_drag_k = def.has_missile_tuning
                ? default_factory_nonnegative_or(
                    def.missile_tuning.induced_drag_k,
                    MissileGuidanceDefaults::kInducedDragScale)
                : MissileGuidanceDefaults::kInducedDragScale;
            missile_runtime.guidance_max_lateral_g = def.has_missile_tuning
                ? default_factory_positive_or(
                    def.missile_tuning.max_lateral_g,
                    std::clamp(12.0 + 0.4 * std::max(0.0, missile_turn_rate), 12.0, 35.0))
                : std::clamp(12.0 + 0.4 * std::max(0.0, missile_turn_rate), 12.0, 35.0);
            missile_runtime.guidance_autopilot_tau_s = def.has_missile_tuning
                ? default_factory_positive_or(
                    def.missile_tuning.autopilot_tau_s,
                    MissileGuidanceDefaults::kAutopilotTauS)
                : MissileGuidanceDefaults::kAutopilotTauS;
            missile_runtime.guidance_max_accel_response_g_per_s = def.has_missile_tuning
                ? default_factory_positive_or(
                    def.missile_tuning.max_accel_response_g_per_s,
                    MissileGuidanceDefaults::kAccelResponseGps)
                : MissileGuidanceDefaults::kAccelResponseGps;

            e.set<Missile>(missile_runtime);
            e.set<Mass>({empty_mass_kg, propellant_mass_kg, 0.0});
            e.set<MassProperties>({
                empty_mass_kg,
                empty_mass_kg + propellant_mass_kg,
                0.0,
                0.0,
                reference_area_m2,
                0.0,
                0.0
            });
            if (!e.has<ContactList>()) {
                e.set<ContactList>({});
            }
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
        if (!def.has_flight_model) {
            default_unit_factory_detail::apply_spawn_compatibility_action_command_seed(e);
        }
        if (def.has_landing_gear) {
            e.set<LandingGear>(def.landing_gear);
        } else if (def.type == UnitType::Aircraft) {
            // Fallback for aircraft without explicit config (assume paved only)
            e.set<LandingGear>({false, 0.02, 3.0, 2.0, 1.0, false, 5.0});
        }

        const bool has_air_damage_baseline =
            (def.type == UnitType::Aircraft || def.type == UnitType::C2Node || def.has_flight_model);
        bool aircraft_damage_baseline_set = false;
        if (def.has_flight_model) {
            e.set<FlightModel>(def.flight_model);
            AircraftDamageBaseline baseline{};
            baseline.max_speed = def.flight_model.max_speed;
            baseline.min_speed = def.flight_model.min_speed;
            baseline.max_turn_rate = def.flight_model.max_turn_rate;
            baseline.max_accel = def.flight_model.max_accel;
            baseline.max_climb_rate = def.flight_model.max_climb_rate;
            baseline.max_g = def.flight_model.max_g;
            baseline.min_g = def.flight_model.min_g;
            baseline.takeoff_speed = def.flight_model.takeoff_speed;
            baseline.landing_speed = def.flight_model.landing_speed;
            baseline.taxi_turn_rate = def.flight_model.taxi_turn_rate;
            e.set<AircraftDamageBaseline>(baseline);
            aircraft_damage_baseline_set = true;
            double speed = std::sqrt(params.vx * params.vx +
                                     params.vy * params.vy +
                                     params.vz * params.vz);
            MissionCommand mission_seed{};
            static_cast<MissionCommandCore&>(mission_seed) =
                default_unit_factory_detail::make_spawn_default_mission_command_core_seed(
                    heading_init,
                    speed,
                    params.z);
            e.set<MissionCommand>(mission_seed);
            default_unit_factory_detail::apply_spawn_compatibility_control_state_seed(
                e,
                default_unit_factory_detail::make_spawn_compatibility_control_state_seed(
                    static_cast<const MissionCommandCore&>(mission_seed)));
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
        if (has_air_damage_baseline) {
            AircraftDamageBaseline baseline = aircraft_damage_baseline_set
                ? *e.get<AircraftDamageBaseline>()
                : AircraftDamageBaseline{};
            if (const Propulsion* propulsion = e.get<Propulsion>()) {
                baseline.mil_thrust_n = propulsion->mil_thrust_n;
                baseline.ab_thrust_n = propulsion->ab_thrust_n;
            }
            if (const Mass* mass = e.get<Mass>()) {
                baseline.fuel_leak_rate_kg_s = mass->fuel_leak_rate_kg_s;
            }
            if (const Sensor* sensor = e.get<Sensor>()) {
                baseline.sensor_max_range = sensor->max_range;
                baseline.sensor_detection_prob = sensor->detection_prob;
                baseline.sensor_bearing_noise_std = sensor->bearing_noise_std;
                baseline.sensor_range_noise_std = sensor->range_noise_std;
                baseline.sensor_track_memory_s = sensor->track_memory_s;
            }
            e.set<AircraftDamageBaseline>(baseline);
        }

        // Damage Model Initialization
        if (!def.damage_model.hitboxes.empty()) {
            e.set<HitboxConfig>(def.damage_model);
            if (def.has_aircraft_vulnerability) {
                e.set<AircraftVulnerabilityProfile>(def.aircraft_vulnerability);
            }
            
            SystemHealth initial_health;
            for (const auto& hb : def.damage_model.hitboxes) {
                for (const auto& sys_name : hb.protected_systems) {
                    initial_health.systems[sys_name] = 1.0;
                }
                for (const auto& component : hb.components) {
                    if (!component.system.empty()) {
                        initial_health.systems[component.system] = 1.0;
                    }
                    for (const auto& dependency : component.dependencies) {
                        if (!dependency.system.empty()) {
                            initial_health.systems[dependency.system] = 1.0;
                        }
                    }
                }
            }
            e.set<SystemHealth>(initial_health);
            ComponentDamageState component_damage;
            for (const auto& hb : def.damage_model.hitboxes) {
                for (const auto& component : hb.components) {
                    const std::string component_key = damage_component_key(component);
                    const std::string group_key = damage_component_redundancy_group_key(component);
                    component_damage.component_integrity[component_key] = 1.0;
                    component_damage.component_redundancy_group[component_key] = group_key;
                    component_damage.component_redundancy_weight[component_key] =
                        std::clamp(component.redundancy_weight, 0.15, 2.50);
                    component_damage.redundancy_group_availability[group_key] = 1.0;
                    component_damage.redundancy_group_member_count[group_key] += 1;
                    component_damage.redundancy_group_failed_count[group_key] += 0;
                    if (!component_damage.has_fire_suppression_components &&
                        (damage_dependency_system_is_fire_suppression(component.system) ||
                         damage_dependency_system_is_fire_suppression(component.name) ||
                         damage_dependency_system_is_fire_suppression(group_key))) {
                        component_damage.has_fire_suppression_components = true;
                    }
                }
            }
            if (!component_damage.component_integrity.empty()) {
                e.set<ComponentDamageState>(component_damage);
            }
            e.set<PlatformDamageState>({});
            if (def.type == UnitType::Aircraft || def.type == UnitType::C2Node) {
                e.set<AircraftDamageState>({});
            }
        } else if (def.airframe.length_m > 0.0) {
            // Procedural Generation
            HitboxConfig generated = generate_default_hitboxes(def.airframe);
            e.set<HitboxConfig>(generated);
            if (def.has_aircraft_vulnerability) {
                e.set<AircraftVulnerabilityProfile>(def.aircraft_vulnerability);
            }
            
            SystemHealth initial_health;
            for (const auto& hb : generated.hitboxes) {
                for (const auto& sys_name : hb.protected_systems) {
                    initial_health.systems[sys_name] = 1.0;
                }
            }
            e.set<SystemHealth>(initial_health);
            e.set<PlatformDamageState>({});
            if (def.type == UnitType::Aircraft || def.type == UnitType::C2Node) {
                e.set<AircraftDamageState>({});
            }
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
             
             // 5. Wings (Fuel, Flight Control)
             config.hitboxes.push_back({4, -L * 0.1, 0, 0, L * 0.2, W, 0.2, 3.0, {"wings", "flight_control"}});
            
        } else {
             // "Conventional" (Default F-16 style)
             // 1. Nose
             config.hitboxes.push_back({0, L * 0.4, 0, 0, L * 0.25, 0.8, 0.8, 5.0, {"radar", "cockpit"}});
             
             // 2. Fuselage
             config.hitboxes.push_back({1, 0, 0, 0, L * 0.5, 1.0, 1.0, 10.0, {"fuel", "ammo", "engine"}}); // Single engine usually embedded
             
             // 3. Tail / Exhaust
             config.hitboxes.push_back({2, -L * 0.4, 0, 0, L * 0.2, 0.8, 0.8, 12.0, {"engine"}});
             
             // 4. Wings
             config.hitboxes.push_back({3, -L * 0.05, 0, 0, L * 0.2, W, 0.2, 3.0, {"wings", "flight_control"}});
        }
        
        return config;
    }
};
