// Maintained air-owned default effects helper surface for default_effects_model.cpp.
// Included through the common effects router; not a standalone model entry point.

#pragma once

struct DefaultEffectsAirDomainTargetSelection {
    bool structured_damage_target = false;
    AircraftDamageState* aircraft_damage = nullptr;
    const AircraftVulnerabilityProfile* aircraft_vulnerability = nullptr;
};

inline DefaultEffectsAirDomainTargetSelection select_default_effects_air_domain_target(
    flecs::entity target_entity
) {
    const KeyEntity* key = target_entity.get<KeyEntity>();
    const bool structured_damage_target =
        key &&
        (key->type == UnitType::Aircraft || key->type == UnitType::C2Node) &&
        target_entity.get<HitboxConfig>() != nullptr &&
        target_entity.get<SystemHealth>() != nullptr &&
        target_entity.get<PlatformDamageState>() != nullptr;
    return DefaultEffectsAirDomainTargetSelection{
        .structured_damage_target = structured_damage_target,
        .aircraft_damage = target_entity.get_mut<AircraftDamageState>(),
        .aircraft_vulnerability = target_entity.get<AircraftVulnerabilityProfile>(),
    };
}

bool default_effects_mechanism_load_is_empty(
    const WarheadMechanismLoadEvidence& load
) {
    return load.fragment_energy_j <= 0.0 &&
        load.fragment_areal_density_per_m2 <= 0.0 &&
        load.penetration_margin <= 0.0 &&
        load.blast_overpressure_kpa <= 0.0 &&
        load.blast_impulse_kpa_ms <= 0.0 &&
        load.blast_scaled_distance_m_kg13 <= 0.0 &&
        load.rod_cut_margin <= 0.0 &&
        load.surface_incidence_cos <= 0.0;
}

WarheadMechanismLoadEvidence make_default_effects_sampled_mechanism_load(
    const DefaultEffectsScratch& scratch
) {
    WarheadMechanismLoadEvidence load{};
    load.fragment_energy_j = scratch.sampled_mechanism_fragment_energy_j;
    load.fragment_areal_density_per_m2 =
        scratch.sampled_mechanism_fragment_areal_density_per_m2;
    load.penetration_margin = scratch.sampled_mechanism_penetration_margin;
    load.blast_overpressure_kpa = scratch.sampled_mechanism_blast_overpressure_kpa;
    load.blast_impulse_kpa_ms = scratch.sampled_mechanism_blast_impulse_kpa_ms;
    load.blast_scaled_distance_m_kg13 =
        scratch.sampled_mechanism_blast_scaled_distance_m_kg13;
    load.rod_cut_margin = scratch.sampled_mechanism_rod_cut_margin;
    load.surface_incidence_cos = scratch.sampled_mechanism_surface_incidence_cos;
    return load;
}

WarheadMechanismLoadEvidence resolve_default_effects_vulnerability_mechanism_load(
    const DefaultEffectsScratch& scratch,
    bool direct_structure_hit
) {
    WarheadMechanismLoadEvidence load = direct_structure_hit
        ? scratch.component_primary_mechanism_load
        : WarheadMechanismLoadEvidence{};
    if (default_effects_mechanism_load_is_empty(load)) {
        load = make_default_effects_sampled_mechanism_load(scratch);
    }
    return load;
}

struct DefaultEffectsAirSpatialScales {
    double sensor = 0.0;
    double propulsion_or_fuel = 0.0;
    double propulsion = 0.0;
    double fuel = 0.0;
    double control = 0.0;
    double crew = 0.0;
    double pilot = 0.0;
    double mission_crew = 0.0;
    double command_navigation = 0.0;
    double mission_or_combat = 0.0;
    double fire_suppression = 0.0;
    double lateral_fuel_storage = 0.0;
    double hydraulic_supply = 0.0;
    double engine_fire_zone = 0.0;
    double wing_fire_zone = 0.0;
    double fuselage_fire_zone = 0.0;
    double mission_fire_zone = 0.0;
    double structure = 0.05;
};

double resolve_default_effects_air_hit_scale(bool hit, double spatial_scale) {
    return hit ? std::max(0.05, spatial_scale) : 0.0;
}

DefaultEffectsAirSpatialScales make_default_effects_air_spatial_scales(
    const DefaultEffectsScratch& scratch
) {
    return DefaultEffectsAirSpatialScales{
        .sensor = resolve_default_effects_air_hit_scale(
            scratch.air_sensor_hit,
            scratch.air_sensor_spatial_scale),
        .propulsion_or_fuel = resolve_default_effects_air_hit_scale(
            scratch.air_propulsion_or_fuel_hit,
            scratch.air_propulsion_or_fuel_spatial_scale),
        .propulsion = resolve_default_effects_air_hit_scale(
            scratch.air_propulsion_hit,
            scratch.air_propulsion_spatial_scale),
        .fuel = resolve_default_effects_air_hit_scale(
            scratch.air_fuel_hit,
            scratch.air_fuel_spatial_scale),
        .control = resolve_default_effects_air_hit_scale(
            scratch.air_control_hit,
            scratch.air_control_spatial_scale),
        .crew = resolve_default_effects_air_hit_scale(
            scratch.air_crew_hit,
            scratch.air_crew_spatial_scale),
        .pilot = resolve_default_effects_air_hit_scale(
            scratch.air_pilot_hit,
            scratch.air_pilot_spatial_scale),
        .mission_crew = resolve_default_effects_air_hit_scale(
            scratch.air_mission_crew_hit,
            scratch.air_mission_crew_spatial_scale),
        .command_navigation = resolve_default_effects_air_hit_scale(
            scratch.air_command_navigation_hit,
            scratch.air_command_navigation_spatial_scale),
        .mission_or_combat = resolve_default_effects_air_hit_scale(
            scratch.air_mission_or_combat_hit,
            scratch.air_mission_or_combat_spatial_scale),
        .fire_suppression = resolve_default_effects_air_hit_scale(
            scratch.air_fire_suppression_hit,
            scratch.air_fire_suppression_spatial_scale),
        .lateral_fuel_storage = resolve_default_effects_air_hit_scale(
            scratch.air_lateral_fuel_storage_hit,
            scratch.air_lateral_fuel_storage_spatial_scale),
        .hydraulic_supply = resolve_default_effects_air_hit_scale(
            scratch.air_hydraulic_supply_hit,
            scratch.air_hydraulic_supply_spatial_scale),
        .engine_fire_zone = resolve_default_effects_air_hit_scale(
            scratch.air_engine_fire_zone_hit,
            scratch.air_engine_fire_zone_spatial_scale),
        .wing_fire_zone = resolve_default_effects_air_hit_scale(
            scratch.air_wing_fire_zone_hit,
            scratch.air_wing_fire_zone_spatial_scale),
        .fuselage_fire_zone = resolve_default_effects_air_hit_scale(
            scratch.air_fuselage_fire_zone_hit,
            scratch.air_fuselage_fire_zone_spatial_scale),
        .mission_fire_zone = resolve_default_effects_air_hit_scale(
            scratch.air_mission_fire_zone_hit,
            scratch.air_mission_fire_zone_spatial_scale),
        .structure = std::max(0.05, scratch.air_structure_spatial_scale),
    };
}

void apply_default_effects_platform_air_consequence_blocks(
    const DefaultEffectsScratch& scratch,
    const DefaultEffectsAirSpatialScales& scales,
    double resolved_severity,
    const WarheadEffectProfile& warhead_effects,
    PlatformDamageState& platform_damage
) {
    if (scratch.air_propulsion_or_fuel_hit) {
        platform_damage.fire_severity +=
            localized_effect_delta(
                0.08,
                0.08,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.propulsion_or_fuel);
        platform_damage.ongoing_hull_breach +=
            localized_effect_delta(
                0.03,
                0.04,
                resolved_severity,
                warhead_effects.breach_scale,
                scales.propulsion_or_fuel);
    }
    if (scratch.air_control_hit) {
        platform_damage.survivability_margin -=
            localized_effect_delta(
                0.06,
                0.08,
                resolved_severity,
                warhead_effects.control_scale,
                scales.control);
    }
    if (scratch.air_crew_hit || scratch.air_pilot_hit || scratch.air_mission_crew_hit ||
        scratch.air_command_navigation_hit) {
        platform_damage.survivability_margin -=
            localized_effect_delta(
                0.10,
                0.10,
                resolved_severity,
                warhead_effects.crew_scale,
                std::max({
                    scales.crew,
                    scales.pilot,
                    scales.mission_crew,
                    scales.command_navigation}));
    }
    if (scratch.air_mission_or_combat_hit) {
        platform_damage.fire_severity +=
            localized_effect_delta(
                0.04,
                0.04,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.mission_or_combat);
    }
    if (scratch.air_fire_suppression_hit) {
        platform_damage.survivability_margin -=
            localized_effect_delta(
                0.03,
                0.05,
                resolved_severity,
                warhead_effects.breach_scale,
                scales.fire_suppression);
    }
    platform_damage.fire_severity =
        std::clamp(platform_damage.fire_severity, 0.0, 1.0);
    platform_damage.flooding_severity =
        std::clamp(platform_damage.flooding_severity, 0.0, 1.0);
    platform_damage.ongoing_hull_breach =
        std::clamp(platform_damage.ongoing_hull_breach, 0.0, 1.0);
}

void apply_default_effects_aircraft_sensor_consequence_block(
    const DefaultEffectsScratch& scratch,
    const DefaultEffectsAirSpatialScales& scales,
    double resolved_severity,
    const WarheadEffectProfile& warhead_effects,
    AircraftDamageState& aircraft_damage
) {
    if (scratch.air_sensor_hit) {
        aircraft_damage.avionics_integrity -=
            localized_effect_delta(
                0.25,
                0.20,
                resolved_severity,
                warhead_effects.sensor_scale,
                scales.sensor);
        aircraft_damage.fire_severity +=
            localized_effect_delta(
                0.03,
                0.04,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.sensor);
        aircraft_damage.ignition_source_severity +=
            localized_effect_delta(
                0.03,
                0.05,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.sensor);
    }
}

void apply_default_effects_aircraft_propulsion_fuel_consequence_blocks(
    const DefaultEffectsScratch& scratch,
    const DefaultEffectsAirSpatialScales& scales,
    double resolved_severity,
    const WarheadEffectProfile& warhead_effects,
    AircraftDamageState& aircraft_damage
) {
    if (scratch.air_propulsion_hit) {
        aircraft_damage.propulsion_integrity -=
            localized_effect_delta(
                0.22,
                0.22,
                resolved_severity,
                warhead_effects.propulsion_scale,
                scales.propulsion);
        aircraft_damage.ignition_source_severity +=
            localized_effect_delta(
                0.04,
                0.08,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.propulsion);
    }
    if (scratch.air_fuel_hit) {
        aircraft_damage.fuel_system_integrity -=
            localized_effect_delta(
                0.25,
                0.20,
                resolved_severity,
                warhead_effects.propulsion_scale,
                scales.fuel);
        aircraft_damage.fuel_leak_severity +=
            localized_effect_delta(
                0.18,
                0.25,
                resolved_severity,
                warhead_effects.breach_scale,
                scales.fuel);
        aircraft_damage.fire_severity +=
            localized_effect_delta(
                0.08,
                0.10,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.fuel);
        aircraft_damage.flammable_fluid_exposure +=
            localized_effect_delta(
                0.12,
                0.20,
                resolved_severity,
                warhead_effects.breach_scale,
                scales.fuel);
    }
}

void apply_default_effects_aircraft_control_hydraulic_consequence_blocks(
    const DefaultEffectsScratch& scratch,
    const DefaultEffectsAirSpatialScales& scales,
    double resolved_severity,
    const WarheadEffectProfile& warhead_effects,
    AircraftDamageState& aircraft_damage
) {
    if (scratch.air_lateral_fuel_storage_hit) {
        aircraft_damage.fuel_imbalance_severity +=
            localized_effect_delta(
                0.07,
                0.12,
                resolved_severity,
                warhead_effects.breach_scale,
                scales.lateral_fuel_storage);
        aircraft_damage.control_asymmetry +=
            localized_effect_delta(
                0.010,
                0.020,
                resolved_severity,
                warhead_effects.control_scale,
                scales.lateral_fuel_storage);
    }
    if (scratch.air_hydraulic_supply_hit) {
        aircraft_damage.hydraulic_pressure_availability -=
            localized_effect_delta(
                0.18,
                0.22,
                resolved_severity,
                warhead_effects.control_scale,
                scales.hydraulic_supply);
        aircraft_damage.flammable_fluid_exposure +=
            localized_effect_delta(
                0.04,
                0.06,
                resolved_severity,
                warhead_effects.breach_scale,
                scales.hydraulic_supply);
    }
    if (scratch.air_control_hit) {
        aircraft_damage.flight_control_integrity -=
            localized_effect_delta(
                0.28,
                0.24,
                resolved_severity,
                warhead_effects.control_scale,
                scales.control);
        aircraft_damage.hydraulic_integrity -=
            localized_effect_delta(
                0.20,
                0.20,
                resolved_severity,
                warhead_effects.control_scale,
                scales.control);
        aircraft_damage.structural_integrity -=
            localized_effect_delta(
                0.05,
                0.06,
                resolved_severity,
                warhead_effects.control_scale,
                scales.control);
        aircraft_damage.flammable_fluid_exposure +=
            localized_effect_delta(
                0.03,
                0.05,
                resolved_severity,
                warhead_effects.breach_scale,
                scales.control);
    }
}

void apply_default_effects_aircraft_crew_role_consequence_blocks(
    const DefaultEffectsScratch& scratch,
    const DefaultEffectsAirSpatialScales& scales,
    double resolved_severity,
    const WarheadEffectProfile& warhead_effects,
    AircraftDamageState& aircraft_damage
) {
    if (scratch.air_pilot_hit) {
        apply_aircraft_crew_consequence(
            aircraft_damage,
            CrewConsequenceKind::Pilot,
            localized_effect_delta(
                0.42,
                0.25,
                resolved_severity,
                warhead_effects.crew_scale,
                scales.pilot));
    }
    if (scratch.air_mission_crew_hit) {
        apply_aircraft_crew_consequence(
            aircraft_damage,
            CrewConsequenceKind::MissionCrew,
            localized_effect_delta(
                0.32,
                0.22,
                resolved_severity,
                warhead_effects.crew_scale,
                scales.mission_crew));
    }
    if (scratch.air_command_navigation_hit) {
        apply_aircraft_crew_consequence(
            aircraft_damage,
            CrewConsequenceKind::CommandNavigation,
            localized_effect_delta(
                0.34,
                0.22,
                resolved_severity,
                warhead_effects.mission_scale,
                scales.command_navigation));
    }
    if (scratch.air_crew_hit &&
        !(scratch.air_pilot_hit || scratch.air_mission_crew_hit || scratch.air_command_navigation_hit)) {
        aircraft_damage.crew_effectiveness -=
            localized_effect_delta(
                0.42,
                0.25,
                resolved_severity,
                warhead_effects.crew_scale,
                scales.crew);
    }
}

void apply_default_effects_aircraft_mission_combat_consequence_block(
    const DefaultEffectsScratch& scratch,
    const DefaultEffectsAirSpatialScales& scales,
    double resolved_severity,
    const WarheadEffectProfile& warhead_effects,
    AircraftDamageState& aircraft_damage
) {
    if (scratch.air_mission_or_combat_hit) {
        aircraft_damage.avionics_integrity -=
            localized_effect_delta(
                0.18,
                0.20,
                resolved_severity,
                warhead_effects.mission_scale,
                scales.mission_or_combat);
        aircraft_damage.fire_severity +=
            localized_effect_delta(
                0.04,
                0.04,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.mission_or_combat);
        aircraft_damage.ignition_source_severity +=
            localized_effect_delta(
                0.02,
                0.05,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.mission_or_combat);
    }
}

void apply_default_effects_aircraft_structure_spatial_consequence_block(
    const DefaultEffectsScratch& scratch,
    const DefaultEffectsAirSpatialScales& scales,
    double resolved_severity,
    const WarheadEffectProfile& warhead_effects,
    AircraftDamageState& aircraft_damage
) {
    if (scratch.air_structure_spatial_scale > 0.0) {
        aircraft_damage.structural_integrity -=
            localized_effect_delta(
                0.06,
                0.07,
                resolved_severity,
                warhead_effects.structure_scale,
                scales.structure);
    }
}

void apply_default_effects_aircraft_fire_zone_consequence_blocks(
    const DefaultEffectsScratch& scratch,
    const DefaultEffectsAirSpatialScales& scales,
    double resolved_severity,
    const WarheadEffectProfile& warhead_effects,
    AircraftDamageState& aircraft_damage
) {
    if (scratch.air_engine_fire_zone_hit) {
        aircraft_damage.engine_fire_zone_severity +=
            localized_effect_delta(
                0.06,
                0.10,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.engine_fire_zone);
        aircraft_damage.smoke_heat_exposure +=
            localized_effect_delta(
                0.010,
                0.020,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.engine_fire_zone);
    }
    if (scratch.air_wing_fire_zone_hit) {
        aircraft_damage.wing_fire_zone_severity +=
            localized_effect_delta(
                0.04,
                0.07,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.wing_fire_zone);
        aircraft_damage.smoke_heat_exposure +=
            localized_effect_delta(
                0.012,
                0.020,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.wing_fire_zone);
    }
    if (scratch.air_fuselage_fire_zone_hit) {
        aircraft_damage.fuselage_fire_zone_severity +=
            localized_effect_delta(
                0.04,
                0.08,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.fuselage_fire_zone);
        aircraft_damage.smoke_heat_exposure +=
            localized_effect_delta(
                0.030,
                0.045,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.fuselage_fire_zone);
    }
    if (scratch.air_mission_fire_zone_hit) {
        aircraft_damage.mission_fire_zone_severity +=
            localized_effect_delta(
                0.05,
                0.08,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.mission_fire_zone);
        aircraft_damage.smoke_heat_exposure +=
            localized_effect_delta(
                0.035,
                0.050,
                resolved_severity,
                warhead_effects.fire_scale,
                scales.mission_fire_zone);
    }
}

inline bool resolve_default_effects_air_domain_consequences(
    DefaultEffectsScratch& scratch,
    flecs::entity target_entity,
    const Missile& missile,
    bool structured_air_target,
    const AircraftVulnerabilityProfile* aircraft_vulnerability,
    const Vec3& local_imp,
    double closure_mps,
    double severity,
    const WarheadEffectProfile& warhead_effects,
    PlatformDamageState* platform_damage,
    AircraftDamageState* aircraft_damage,
    ComponentDamageState* component_damage,
    Health* hp
) {
            if (platform_damage && structured_air_target && scratch.structure_hit) {
                const bool direct_structure_hit = scratch.direct_hitbox_intersection;
                WarheadMechanismLoadEvidence vulnerability_effect_mechanism_load =
                    resolve_default_effects_vulnerability_mechanism_load(
                        scratch,
                        direct_structure_hit);
                const VulnerabilityAdjustment vulnerability_adjustment =
                    make_vulnerability_adjustment(
                        missile.warhead_profile,
                        aircraft_vulnerability,
                        local_imp,
                        closure_mps,
                        scratch.spatial_effect_scale,
                        direct_structure_hit,
                        &vulnerability_effect_mechanism_load);
                scratch.sampled_vulnerability_adjustment = vulnerability_adjustment;
                const double resolved_severity =
                    std::clamp(
                        severity *
                            std::max(0.05, scratch.spatial_effect_scale) *
                            scratch.sampled_mechanism_scale *
                            vulnerability_adjustment.scale,
                        0.02,
                        0.65);
                if (aircraft_vulnerability) {
                    spdlog::info(
                        "AIR VULNERABILITY >>> provenance={} synthetic={} calibrated={} pk_authority={} deterministic_fuze_authority={} dataset={} status={} aspect={} closure={:.1f} scale={:.2f}",
                        aircraft_vulnerability->provenance,
                        aircraft_vulnerability->synthetic,
                        vulnerability_adjustment.calibrated_evidence,
                        vulnerability_adjustment.pk_authority,
                        vulnerability_adjustment.deterministic_fuze_authority,
                        vulnerability_adjustment.evidence_dataset_ref,
                        vulnerability_adjustment.calibration_status,
                        vulnerability_adjustment.aspect_bucket,
                        vulnerability_adjustment.closure_mps,
                        vulnerability_adjustment.scale);
                }
                const DefaultEffectsAirSpatialScales scales =
                    make_default_effects_air_spatial_scales(scratch);
                platform_damage->survivability_margin -=
                    localized_effect_delta(
                        0.08,
                        0.08,
                        resolved_severity,
                        warhead_effects.structure_scale,
                        std::max(scales.structure, scratch.spatial_effect_scale));
                if (scratch.air_sensor_hit) {
                    platform_damage->sensor_capability -=
                        localized_effect_delta(
                            0.35,
                            0.20,
                            resolved_severity,
                            warhead_effects.sensor_scale,
                            scales.sensor);
                    platform_damage->fire_severity +=
                        localized_effect_delta(
                            0.05,
                            0.05,
                            resolved_severity,
                            warhead_effects.fire_scale,
                            scales.sensor);
                }
                if (aircraft_damage) {
                    aircraft_damage->structural_integrity -=
                        localized_effect_delta(
                            0.05,
                            0.07,
                            resolved_severity,
                            warhead_effects.structure_scale,
                            std::max(scales.structure, scratch.spatial_effect_scale));
                    apply_default_effects_aircraft_sensor_consequence_block(
                        scratch,
                        scales,
                        resolved_severity,
                        warhead_effects,
                        *aircraft_damage);
                    apply_default_effects_aircraft_propulsion_fuel_consequence_blocks(
                        scratch,
                        scales,
                        resolved_severity,
                        warhead_effects,
                        *aircraft_damage);
                    apply_default_effects_aircraft_control_hydraulic_consequence_blocks(
                        scratch,
                        scales,
                        resolved_severity,
                        warhead_effects,
                        *aircraft_damage);
                    apply_default_effects_aircraft_crew_role_consequence_blocks(
                        scratch,
                        scales,
                        resolved_severity,
                        warhead_effects,
                        *aircraft_damage);
                    apply_default_effects_aircraft_mission_combat_consequence_block(
                        scratch,
                        scales,
                        resolved_severity,
                        warhead_effects,
                        *aircraft_damage);
                    apply_default_effects_aircraft_structure_spatial_consequence_block(
                        scratch,
                        scales,
                        resolved_severity,
                        warhead_effects,
                        *aircraft_damage);
                    apply_default_effects_aircraft_fire_zone_consequence_blocks(
                        scratch,
                        scales,
                        resolved_severity,
                        warhead_effects,
                        *aircraft_damage);
                    if (component_damage) {
                        derive_aircraft_damage_from_component_state(
                            *component_damage,
                            *aircraft_damage);
                    }
                    clamp_aircraft_damage_state(*aircraft_damage);
                    apply_aircraft_damage_state_to_platform(*aircraft_damage, *platform_damage);
                }
                apply_default_effects_platform_air_consequence_blocks(
                    scratch,
                    scales,
                    resolved_severity,
                    warhead_effects,
                    *platform_damage);
            }

            return finalize_default_effects_platform_damage(
                target_entity,
                platform_damage,
                hp);
}
