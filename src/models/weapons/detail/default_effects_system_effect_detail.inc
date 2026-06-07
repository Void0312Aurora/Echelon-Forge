// Private fragment for default_effects_model.cpp.
// Included inside that file's anonymous namespace; not a standalone API.

struct DefaultEffectsSystemEffectContext {
    DefaultEffectsScratch& scratch;
    flecs::entity target_entity;
    bool structured_air_target;
    const Missile& missile;
    const AircraftVulnerabilityProfile* aircraft_vulnerability;
    ComponentDamageState* component_damage;
    AircraftDamageState* aircraft_damage;
    PlatformDamageState* platform_damage;
    SystemHealth& sys_health;
    const Vec3& local_imp;
    double closure_mps;
    double severity;
};

struct DefaultEffectsSystemSeverityContext {
    bool structured_air_target;
    const Missile& missile;
    const AircraftVulnerabilityProfile* aircraft_vulnerability;
    const Vec3& local_imp;
    double closure_mps;
    double base_system_severity;
};

double resolve_default_effects_system_severity(
    const DefaultEffectsSystemSeverityContext& context,
    double local_spatial_effect_scale,
    bool direct_hit,
    const WarheadMechanismLoadEvidence& mechanism_load
) {
    if (!context.structured_air_target) {
        return context.base_system_severity;
    }

    double vulnerability_scale = 1.0;
    if (context.aircraft_vulnerability) {
        vulnerability_scale =
            make_vulnerability_adjustment(
                context.missile.warhead_profile,
                context.aircraft_vulnerability,
                context.local_imp,
                context.closure_mps,
                local_spatial_effect_scale,
                direct_hit,
                &mechanism_load).scale;
    }
    return std::clamp(
        context.base_system_severity * vulnerability_scale,
        0.05,
        0.95);
}

struct DefaultEffectsSystemSeverityResolver {
    const DefaultEffectsSystemSeverityContext& context;

    double operator()(
        double local_spatial_effect_scale,
        bool direct_hit,
        const WarheadMechanismLoadEvidence& mechanism_load
    ) const {
        return resolve_default_effects_system_severity(
            context,
            local_spatial_effect_scale,
            direct_hit,
            mechanism_load);
    }
};

void sample_default_effects_component_failure(
    DefaultEffectsSystemEffectContext& context,
    const std::string& system,
    double base_severity,
    double mechanism_scale,
    double component_scale,
    bool direct_hit,
    const WarheadMechanismLoadEvidence& mechanism_load,
    bool component_critical,
    double redundancy_group,
    const DamageComponent* component,
    ComponentMechanismLoadRow* component_row
) {
    if (!context.structured_air_target) {
        return;
    }

    DefaultEffectsScratch& scratch = context.scratch;
    double resolved_component_scale = component_scale;
    if (!component_critical) {
        resolved_component_scale *= 0.72;
    }
    if (redundancy_group > 0.0) {
        resolved_component_scale *=
            std::clamp(1.0 / std::sqrt(1.0 + redundancy_group), 0.45, 1.0);
    }

    const ComponentFragilityRuntimeState fragility_state =
        resolve_component_fragility_runtime_state(component, context.component_damage);
    double failure_probability = component_failure_probability(
        base_severity,
        mechanism_scale,
        resolved_component_scale,
        direct_hit,
        mechanism_load,
        system,
        component,
        fragility_state);
    // Keep the legacy baseline identifier stable until Stage C snapshots are refreshed.
    std::string failure_probability_source = "synthetic_sigmoid";
    bool failure_probability_calibrated = false;
    bool failure_probability_component_specific = false;
    std::string failure_probability_evidence_dataset_ref;
    std::string failure_probability_evidence_row_id;
    std::string failure_probability_evidence_source_ref;
    std::string failure_probability_evidence_provenance;
    std::string failure_probability_evidence_component_name;
    std::string failure_probability_evidence_component_system;
    std::string failure_probability_evidence_component_redundancy_group_id;
    const std::string failure_family =
        warhead_effect_family(context.missile.warhead_profile);
    const std::string failure_aspect_bucket =
        classify_local_aspect_bucket(context.local_imp);
    const std::string failure_closure_bucket =
        classify_closure_bucket(context.closure_mps);
    const std::string failure_miss_distance_bucket =
        classify_miss_distance_bucket(direct_hit);
    if (context.aircraft_vulnerability) {
        const AircraftVulnerabilityEvidenceRow* failure_row =
            find_component_failure_vulnerability_evidence_row(
                *context.aircraft_vulnerability,
                failure_family,
                failure_aspect_bucket,
                failure_closure_bucket,
                failure_miss_distance_bucket,
                component,
                mechanism_load,
                &failure_probability_component_specific);
        if (failure_row) {
            failure_probability = std::clamp(
                failure_row->component_failure_probability,
                0.0,
                1.0);
            failure_probability_source = "vulnerability_evidence_row";
            failure_probability_calibrated = true;
            failure_probability_evidence_dataset_ref =
                context.aircraft_vulnerability->evidence_dataset_ref;
            failure_probability_evidence_row_id =
                failure_row->row_id;
            failure_probability_evidence_source_ref =
                failure_row->source_ref;
            failure_probability_evidence_provenance =
                failure_row->provenance;
            failure_probability_evidence_component_name =
                failure_row->component_name;
            failure_probability_evidence_component_system =
                failure_row->component_system;
            failure_probability_evidence_component_redundancy_group_id =
                failure_row->component_redundancy_group_id;
        }
    }

    const PartFailureModeAssessment part_failure_modes = assess_part_failure_modes(
        failure_probability,
        mechanism_scale,
        resolved_component_scale,
        direct_hit,
        mechanism_load,
        system,
        component);
    const double failure_sample = rand_uniform01(scratch.component_rng_state);
    if (component_row) {
        populate_component_failure_mode_row(*component_row, part_failure_modes);
        component_row->component_failure_probability = failure_probability;
        component_row->component_failure_probability_source =
            failure_probability_source;
        component_row->component_failure_probability_calibrated =
            failure_probability_calibrated;
        component_row->component_failure_probability_evidence_dataset_ref =
            failure_probability_evidence_dataset_ref;
        component_row->component_failure_probability_evidence_row_id =
            failure_probability_evidence_row_id;
        component_row->component_failure_probability_evidence_source_ref =
            failure_probability_evidence_source_ref;
        component_row->component_failure_probability_evidence_provenance =
            failure_probability_evidence_provenance;
        component_row->component_failure_sample = failure_sample;
        component_row->component_failure_probability_authority =
            failure_probability_source == "vulnerability_evidence_row";
        component_row->component_failure_probability_component_specific =
            failure_probability_component_specific;
        component_row->component_failure_probability_weapon_family =
            failure_family;
        component_row->component_failure_probability_aspect_bucket =
            failure_aspect_bucket;
        component_row->component_failure_probability_closure_bucket =
            failure_closure_bucket;
        component_row->component_failure_probability_miss_distance_bucket =
            failure_miss_distance_bucket;
        component_row->component_failure_probability_evidence_component_name =
            failure_probability_evidence_component_name;
        component_row->component_failure_probability_evidence_component_system =
            failure_probability_evidence_component_system;
        component_row->component_failure_probability_evidence_component_redundancy_group_id =
            failure_probability_evidence_component_redundancy_group_id;
    }

    if (!scratch.sampled_component_failure_probability_seen ||
        failure_probability > scratch.sampled_component_failure_probability) {
        scratch.sampled_component_failure_probability_seen = true;
        scratch.sampled_component_failure_probability =
            failure_probability;
        scratch.sampled_component_failure_probability_source =
            failure_probability_source;
        scratch.sampled_component_failure_probability_calibrated =
            failure_probability_calibrated;
        scratch.sampled_component_failure_probability_evidence_dataset_ref =
            failure_probability_evidence_dataset_ref;
        scratch.sampled_component_failure_probability_evidence_row_id =
            failure_probability_evidence_row_id;
        scratch.sampled_component_failure_probability_evidence_source_ref =
            failure_probability_evidence_source_ref;
        scratch.sampled_component_failure_probability_evidence_provenance =
            failure_probability_evidence_provenance;
    }
    scratch.sampled_component_failure_sample =
        std::min(scratch.sampled_component_failure_sample, failure_sample);

    if (component) {
        const ComponentDamageSample component_sample =
            apply_component_damage_state(
                *component,
                failure_probability,
                mechanism_scale * resolved_component_scale,
                context.component_damage,
                &context.sys_health);
        const std::string component_key = damage_component_key(*component);
        const double primary_priority = component_primary_priority_score(
            failure_probability,
            mechanism_scale,
            resolved_component_scale,
            direct_hit);
        const bool promote_primary =
            direct_hit
                ? (component_key == scratch.component_primary_name)
                : (primary_priority > scratch.component_primary_priority ||
                   (primary_priority == scratch.component_primary_priority &&
                    mechanism_scale > scratch.component_primary_effect_scale) ||
                   (component_key == scratch.component_primary_name &&
                    scratch.component_primary_priority < 0.0));
        if (promote_primary) {
            scratch.component_primary_priority = primary_priority;
            scratch.component_primary_effect_scale = mechanism_scale;
            scratch.component_primary_name =
                component->name.empty() ? component->system : component->name;
            scratch.component_primary_system = component->system;
            scratch.component_primary_redundancy_group = component->redundancy_group;
            scratch.component_primary_critical = component->critical;
            scratch.component_primary_redundancy_group_id =
                damage_component_redundancy_group_key(*component);
            scratch.component_primary_mechanism_load = mechanism_load;
            scratch.component_primary_integrity = component_sample.integrity;
            scratch.component_redundancy_group_availability =
                component_sample.group_availability;
            scratch.component_redundancy_group_member_count =
                component_sample.group_member_count;
            scratch.component_redundancy_group_failed_count =
                component_sample.group_failed_count;
        }
        if (component_is_fire_suppression_path(*component) &&
            context.aircraft_damage) {
            context.aircraft_damage->fire_suppression_integrity = std::min(
                context.aircraft_damage->fire_suppression_integrity,
                component_sample.group_availability);
        }
        const ComponentDependencyPropagationSummary dependency_summary =
            apply_component_dependency_damage(
                *component,
                component_sample,
                failure_probability,
                mechanism_scale * resolved_component_scale,
                context.component_damage,
                &context.sys_health,
                context.aircraft_damage,
                context.platform_damage);
        if (component_row) {
            component_row->component_dependency_propagation_count =
                dependency_summary.propagation_count;
            component_row->component_dependency_target_system =
                dependency_summary.target_system;
            component_row->component_dependency_edge_type =
                dependency_summary.edge_type;
            component_row->component_dependency_threshold =
                dependency_summary.threshold;
            component_row->component_dependency_delay_s =
                dependency_summary.delay_s;
            component_row->component_dependency_direction =
                dependency_summary.direction;
            component_row->component_dependency_provenance =
                dependency_summary.provenance;
            component_row->component_dependency_source_availability =
                dependency_summary.source_availability;
            component_row->component_dependency_effective_scale =
                dependency_summary.effective_scale;
            component_row->component_dependency_propagated =
                dependency_summary.propagated;
        }
    }

    if (failure_sample <= failure_probability) {
        ++scratch.component_failure_count;
        apply_part_failure_mode_state(
            system,
            component,
            part_failure_modes,
            context.component_damage,
            context.aircraft_damage,
            context.platform_damage);
        apply_component_failure_impulse(
            system,
            failure_probability,
            resolved_component_scale,
            mechanism_scale,
            component ? component_is_engine_fuel_feed_path(*component) : false,
            component ? component_is_fire_suppression_path(*component) : false,
            component ? component_is_lateral_fuel_storage_path(*component) : false,
            component ? component_is_hydraulic_supply_path(*component) : false,
            component ? component_is_hydraulic_consumer_path(*component) : false,
            context.aircraft_damage,
            context.platform_damage);
    }
}

void apply_default_effects_system_effect(
    DefaultEffectsSystemEffectContext& context,
    const std::string& system,
    double system_base_severity,
    double mechanism_scale,
    double component_scale,
    bool direct_hit,
    const WarheadMechanismLoadEvidence& mechanism_load = WarheadMechanismLoadEvidence{},
    bool component_critical = true,
    double redundancy_group = 0.0,
    const DamageComponent* component = nullptr,
    ComponentMechanismLoadRow* component_row = nullptr
) {
    DefaultEffectsScratch& scratch = context.scratch;
    const double resolved_component_scale = std::clamp(component_scale, 0.40, 1.80);
    context.sys_health.systems[system] = std::max(
        0.0,
        context.sys_health.systems[system] -
            std::clamp(
                system_base_severity * mechanism_scale * resolved_component_scale,
                0.02,
                0.95));
    sample_default_effects_component_failure(
        context,
        system,
        system_base_severity,
        mechanism_scale,
        resolved_component_scale,
        direct_hit,
        mechanism_load,
        component_critical,
        redundancy_group,
        component,
        component_row);
    if (context.structured_air_target && component) {
        apply_control_axis_component_damage(
            *component,
            system_base_severity,
            mechanism_scale,
            resolved_component_scale,
            direct_hit,
            context.aircraft_damage);
    }

    if (context.platform_damage) {
        if (context.structured_air_target) {
            note_default_effects_air_system_hit(
                scratch,
                system,
                mechanism_scale,
                component);
        } else {
            context.platform_damage->survivability_margin -=
                0.08 + 0.08 * context.severity;
            if (system_name_matches(system, "radar")) {
                context.platform_damage->sensor_capability -=
                    0.35 + 0.20 * context.severity;
                context.platform_damage->fire_severity +=
                    0.05 + 0.05 * context.severity;
            }
            if (system_name_matches(system, "engineering") ||
                system_name_matches(system, "engine") ||
                system_name_matches(system, "fuel")) {
                context.platform_damage->mobility_capability -=
                    0.25 + 0.20 * context.severity;
                context.platform_damage->fire_severity +=
                    0.08 + 0.08 * context.severity;
                context.platform_damage->flooding_severity +=
                    0.04 + 0.05 * context.severity;
                context.platform_damage->ongoing_hull_breach +=
                    0.03 + 0.04 * context.severity;
            }
            if (system_name_matches(system, "combat") ||
                system_name_matches(system, "command") ||
                system_name_matches(system, "data_link") ||
                system_name_matches(system, "vls") ||
                system_name_matches(system, "gun") ||
                system_name_matches(system, "radar")) {
                context.platform_damage->mission_capability -=
                    0.20 + 0.20 * context.severity;
                context.platform_damage->fire_severity +=
                    0.04 + 0.04 * context.severity;
            }
            context.platform_damage->fire_severity =
                std::clamp(context.platform_damage->fire_severity, 0.0, 1.0);
            context.platform_damage->flooding_severity =
                std::clamp(context.platform_damage->flooding_severity, 0.0, 1.0);
            context.platform_damage->ongoing_hull_breach =
                std::clamp(context.platform_damage->ongoing_hull_breach, 0.0, 1.0);
        }
    }

    if (context.sys_health.systems[system] <= 0.5) {
        if (system == "radar" || system_name_matches(system, "radar")) {
            if (Sensor* s = context.target_entity.get_mut<Sensor>()) {
                s->max_range *= 0.4;
                spdlog::warn("   -> RADAR DEGRADED!");
            }
        } else if (!context.aircraft_damage &&
                   (system == "engineering" || system == "engine" ||
                    system == "engine_left" || system == "engine_right")) {
            if (Propulsion* p = context.target_entity.get_mut<Propulsion>()) {
                p->mil_thrust_n *= 0.75;
                p->ab_thrust_n *= 0.75;
                spdlog::warn("   -> ENGINE DAMAGE! Thrust reduced.");
            }
        } else if (!context.aircraft_damage && system == "fuel") {
            if (Mass* m = context.target_entity.get_mut<Mass>()) {
                m->fuel_leak_rate_kg_s += 5.0;
                spdlog::warn("   -> FUEL TANK RUPTURED! Massive Leak Started.");
            }
        } else if (!context.aircraft_damage &&
                   system_is_air_control_surface(system)) {
            if (FlightModel* f = context.target_entity.get_mut<FlightModel>()) {
                f->max_g *= 0.65;
                f->max_turn_rate *= 0.70;
                f->max_accel *= 0.80;
                f->max_climb_rate *= 0.75;
                spdlog::warn("   -> FLIGHT CONTROL DAMAGE! Maneuver limits reduced.");
            }
        }
    }
}

struct DefaultEffectsSystemEffectApplicator {
    DefaultEffectsSystemEffectContext& context;

    void operator()(
        const std::string& system,
        double system_base_severity,
        double mechanism_scale,
        double component_scale,
        bool direct_hit,
        const WarheadMechanismLoadEvidence& mechanism_load = WarheadMechanismLoadEvidence{},
        bool component_critical = true,
        double redundancy_group = 0.0,
        const DamageComponent* component = nullptr,
        ComponentMechanismLoadRow* component_row = nullptr
    ) const {
        apply_default_effects_system_effect(
            context,
            system,
            system_base_severity,
            mechanism_scale,
            component_scale,
            direct_hit,
            mechanism_load,
            component_critical,
            redundancy_group,
            component,
            component_row);
    }
};
