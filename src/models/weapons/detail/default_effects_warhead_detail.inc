// Private fragment for default_effects_model.cpp.
// Included inside that file's anonymous namespace; not a standalone API.

struct WarheadEffectProfile {
    double system_damage_scale = 1.0;
    double structure_scale = 1.0;
    double sensor_scale = 1.0;
    double propulsion_scale = 1.0;
    double control_scale = 1.0;
    double crew_scale = 1.0;
    double mission_scale = 1.0;
    double fire_scale = 1.0;
    double breach_scale = 1.0;
};

struct WarheadSpatialProjectionProfile {
    double radius_fraction = 0.35;
    double min_radius_m = 1.0;
    double max_radius_m = 12.0;
    double min_effect_scale = 0.05;
    double max_effect_scale = 0.80;
    double falloff_exponent = 1.0;
    std::size_t max_projected_hitboxes = 1;
};

struct SpatialProjectionCandidate {
    const Hitbox *box = nullptr;
    const DamageComponent *component = nullptr;
    double distance_m = std::numeric_limits<double>::infinity();
    double effect_scale = 0.0;
    double axis_weight = 1.0;
    double orientation_weight = 1.0;
    double armor_scale = 1.0;
    double exposure_scale = 1.0;
    std::uint32_t spatial_sample_count = 0;
    double spatial_hit_estimate = 0.0;
    double spatial_hit_fraction = 0.0;
    double spatial_energy_scale = 1.0;
    double spatial_pattern_scale = 1.0;
    double surface_incidence_cos = 0.0;
    WarheadMechanismLoadEvidence mechanism_load;
};

double resolve_default_effects_component_scale(const WarheadProfile &profile,
                                               const DamageComponent &component) {
    return component_mechanism_threshold_scale(profile, component.system) *
           std::clamp(component.threshold_scale, 0.40, 1.80) *
           component_authored_mechanism_threshold_scale(profile, component);
}

double component_projection_priority_score(const WarheadProfile &profile,
                                           const SpatialProjectionCandidate &candidate) {
    if (!candidate.component) {
        return std::clamp(candidate.effect_scale, 0.0, 1.0);
    }

    const DamageComponent &component = *candidate.component;
    const double component_scale = resolve_default_effects_component_scale(profile, component);
    const double criticality_scale = component.critical ? 1.0 : 0.82;
    return std::clamp(candidate.effect_scale, 0.0, 1.0) * std::clamp(component_scale, 0.40, 1.80) *
           component_system_fragility_scale(component.system, &component) *
           component_dependency_complexity_scale(&component) * criticality_scale;
}

struct WarheadSpatialSample {
    std::uint32_t sample_count = 0;
    double hit_estimate = 0.0;
    double hit_fraction = 0.0;
    double areal_density_per_m2 = 0.0;
    double energy_scale = 1.0;
    double pattern_scale = 1.0;
    double orientation_pattern_scale = 1.0;
};

WarheadSpatialSample
make_default_effects_spatial_sample(const SpatialProjectionCandidate &candidate) {
    return WarheadSpatialSample{
        .sample_count = candidate.spatial_sample_count,
        .hit_estimate = candidate.spatial_hit_estimate,
        .hit_fraction = candidate.spatial_hit_fraction,
        .energy_scale = candidate.spatial_energy_scale,
        .pattern_scale = candidate.spatial_pattern_scale,
        .orientation_pattern_scale = candidate.orientation_weight,
    };
}

struct VulnerabilityAdjustment {
    double scale = 1.0;
    double family_scale = 1.0;
    double aspect_scale = 1.0;
    double closure_scale = 1.0;
    double miss_distance_scale = 1.0;
    std::string aspect_bucket = "unknown";
    double closure_mps = 0.0;
    bool profile_present = false;
    bool synthetic = true;
    bool calibrated_evidence = false;
    bool pk_authority = false;
    bool deterministic_fuze_authority = false;
    bool evidence_dataset_valid = false;
    std::string provenance;
    std::string calibration_status = "none";
    std::string evidence_dataset_ref;
    std::string evidence_schema_version;
    std::string evidence_source_kind;
    std::string evidence_source_ref;
    std::string evidence_validation_artifact_ref;
    std::string evidence_validation_manifest_schema_version;
    std::string evidence_validation_status;
    std::string evidence_validation_artifact_sha256;
    std::string evidence_validated_surrogate_model_ref;
    std::string evidence_validation_benchmark_ref;
    std::string evidence_validation_metrics_ref;
    std::string evidence_validation_acceptance_criteria_ref;
    std::string effect_scale_source = "profile_scale";
    std::string effect_scale_evidence_row_id;
    std::string effect_scale_evidence_source_ref;
    std::string effect_scale_evidence_provenance;
};

WarheadEffectProfile make_warhead_effect_profile(const WarheadProfile &profile) {
    const std::string family = warhead_effect_family(profile);
    WarheadEffectProfile out{};

    if (family == "blast") {
        out.system_damage_scale = 0.85;
        out.structure_scale = 1.35;
        out.sensor_scale = 0.70;
        out.propulsion_scale = 1.15;
        out.control_scale = 0.65;
        out.crew_scale = 0.75;
        out.mission_scale = 0.85;
        out.fire_scale = 1.60;
        out.breach_scale = 1.30;
    } else if (family == "fragmentation" || family == "blast_fragmentation") {
        out = WarheadEffectProfile{};
    } else if (family == "continuous_rod") {
        out.system_damage_scale = 1.20;
        out.structure_scale = 1.05;
        out.sensor_scale = 0.85;
        out.propulsion_scale = 1.00;
        out.control_scale = 1.45;
        out.crew_scale = 1.00;
        out.mission_scale = 1.05;
        out.fire_scale = 0.70;
        out.breach_scale = 0.85;
    } else if (family == "hit_to_kill") {
        out.system_damage_scale = 1.55;
        out.structure_scale = 1.25;
        out.sensor_scale = 1.25;
        out.propulsion_scale = 1.25;
        out.control_scale = 1.25;
        out.crew_scale = 1.35;
        out.mission_scale = 1.35;
        out.fire_scale = 0.45;
        out.breach_scale = 0.50;
    }

    return out;
}

WarheadSpatialProjectionProfile
make_warhead_spatial_projection_profile(const WarheadProfile &profile) {
    const std::string family = warhead_effect_family(profile);
    WarheadSpatialProjectionProfile out{};

    if (family == "blast") {
        out.radius_fraction = 0.55;
        out.max_radius_m = 20.0;
        out.min_effect_scale = 0.05;
        out.max_effect_scale = 0.70;
        out.falloff_exponent = 1.65;
        out.max_projected_hitboxes = 4;
    } else if (family == "fragmentation" || family == "blast_fragmentation") {
        out.radius_fraction = 0.45;
        out.max_radius_m = 18.0;
        out.min_effect_scale = 0.06;
        out.max_effect_scale = 0.78;
        out.falloff_exponent = 1.15;
        out.max_projected_hitboxes = 3;
    } else if (family == "continuous_rod") {
        out.radius_fraction = 0.32;
        out.max_radius_m = 11.0;
        out.min_effect_scale = 0.05;
        out.max_effect_scale = 0.85;
        out.falloff_exponent = 1.25;
        out.max_projected_hitboxes = 2;
    } else if (family == "hit_to_kill") {
        out.radius_fraction = 0.24;
        out.max_radius_m = 6.0;
        out.min_effect_scale = 0.04;
        out.max_effect_scale = 0.90;
        out.falloff_exponent = 2.20;
        out.max_projected_hitboxes = 1;
    }

    if (std::isfinite(profile.projection_radius_fraction)) {
        out.radius_fraction = std::clamp(profile.projection_radius_fraction, 0.05, 2.0);
    }
    if (std::isfinite(profile.projection_min_radius_m)) {
        out.min_radius_m = std::clamp(profile.projection_min_radius_m, 0.0, 100.0);
    }
    if (std::isfinite(profile.projection_max_radius_m)) {
        out.max_radius_m = std::clamp(profile.projection_max_radius_m, out.min_radius_m, 100.0);
    }
    if (std::isfinite(profile.projection_min_effect_scale)) {
        out.min_effect_scale = std::clamp(profile.projection_min_effect_scale, 0.0, 1.0);
    }
    if (std::isfinite(profile.projection_max_effect_scale)) {
        out.max_effect_scale =
            std::clamp(profile.projection_max_effect_scale, out.min_effect_scale, 1.5);
    }
    if (std::isfinite(profile.projection_falloff_exponent)) {
        out.falloff_exponent = std::clamp(profile.projection_falloff_exponent, 0.25, 4.0);
    }
    if (profile.projection_max_projected_hitboxes > 0) {
        out.max_projected_hitboxes =
            std::clamp<std::size_t>(profile.projection_max_projected_hitboxes, 1, 12);
    }
    out.max_radius_m = std::max(out.max_radius_m, out.min_radius_m);
    out.max_effect_scale = std::max(out.max_effect_scale, out.min_effect_scale);

    return out;
}

double resolve_spatial_projection_radius_m(const Missile &missile,
                                           const WarheadSpatialProjectionProfile &projection) {
    const double warhead_radius_m = std::isfinite(missile.warhead_profile.lethal_radius_m)
                                        ? missile.warhead_profile.lethal_radius_m
                                        : missile.fuse_distance;
    return std::clamp(warhead_radius_m * projection.radius_fraction, projection.min_radius_m,
                      projection.max_radius_m);
}

double projected_spatial_effect_scale(double distance_m, double radius_m,
                                      const WarheadSpatialProjectionProfile &projection) {
    if (radius_m <= 0.0 || !std::isfinite(distance_m)) {
        return 0.0;
    }
    const double quality = std::clamp(1.0 - distance_m / radius_m, 0.0, 1.0);
    const double shaped_quality = std::pow(quality, projection.falloff_exponent);
    return std::clamp(projection.min_effect_scale +
                          (projection.max_effect_scale - projection.min_effect_scale) *
                              shaped_quality,
                      projection.min_effect_scale, projection.max_effect_scale);
}

bool warhead_uses_broad_spatial_projection(const WarheadProfile &profile) {
    const std::string family = warhead_effect_family(profile);
    return family == "blast" || family == "fragmentation" || family == "blast_fragmentation";
}

double broad_warhead_near_field_effect_floor(const WarheadProfile &profile, double distance_m,
                                             double radius_m,
                                             const WarheadSpatialProjectionProfile &projection) {
    if (!warhead_uses_broad_spatial_projection(profile) || !std::isfinite(distance_m) ||
        radius_m <= 0.0) {
        return projection.min_effect_scale;
    }
    const double near_field_radius_m = std::min(2.0, std::max(0.5, 0.25 * radius_m));
    if (distance_m <= near_field_radius_m) {
        return 0.95 * projection.max_effect_scale;
    }
    return projection.min_effect_scale;
}

double resolved_warhead_effective_mass_kg(const Missile &missile) {
    const bool has_authored_mass =
        std::isfinite(missile.warhead_profile.mass_kg) && missile.warhead_profile.mass_kg > 0.0;
    const bool has_damage_proxy = std::isfinite(missile.warhead_profile.damage_scalar) &&
                                  missile.warhead_profile.damage_scalar > 0.0;
    const double damage_proxy_mass_kg =
        has_damage_proxy ? std::max(1.0, missile.warhead_profile.damage_scalar * 0.12)
                         : std::max(1.0, missile.damage * 0.12);

    if (has_authored_mass) {
        if (!has_damage_proxy || missile.warhead_profile.damage_scalar_synthetic) {
            return missile.warhead_profile.mass_kg;
        }

        // Keep explicit warhead mass as the anchor, but let an authored damage
        // scalar nudge the local mechanism-load surrogate when the two disagree.
        const double blended_mass_kg =
            missile.warhead_profile.mass_kg +
            0.35 * (damage_proxy_mass_kg - missile.warhead_profile.mass_kg);
        return std::clamp(blended_mass_kg, missile.warhead_profile.mass_kg * 0.70,
                          missile.warhead_profile.mass_kg * 1.60);
    }

    return damage_proxy_mass_kg;
}

double resolved_warhead_fragment_count(const WarheadProfile &profile, double effective_mass_kg) {
    if (std::isfinite(profile.fragment_count) && profile.fragment_count > 0.0) {
        return std::clamp(profile.fragment_count, 8.0, 12000.0);
    }
    return std::clamp(18.0 * std::max(0.1, effective_mass_kg), 80.0, 1200.0);
}

double resolved_warhead_fragment_mass_kg(const WarheadProfile &profile, double effective_mass_kg,
                                         double fragment_count) {
    if (std::isfinite(profile.fragment_mass_kg) && profile.fragment_mass_kg > 0.0) {
        return std::clamp(profile.fragment_mass_kg, 0.0002, 0.080);
    }
    const double casing_mass_kg = std::isfinite(profile.case_mass_kg) && profile.case_mass_kg > 0.0
                                      ? profile.case_mass_kg
                                      : effective_mass_kg;
    return std::clamp((0.36 * casing_mass_kg) / std::max(1.0, fragment_count), 0.0002, 0.080);
}

double hitbox_projected_exposure_scale(const Vec3 &local_imp, const Hitbox &box) {
    const Vec3 nearest = hitbox_nearest_point(local_imp, box);
    const Vec3 ray = vec3_normalize({
        nearest.x - local_imp.x,
        nearest.y - local_imp.y,
        nearest.z - local_imp.z,
    });
    if (vec3_norm(ray) <= 1.0e-9) {
        return 1.0;
    }

    const double area_forward = std::max(1.0e-6, box.dim_w * box.dim_h);
    const double area_side = std::max(1.0e-6, box.dim_l * box.dim_h);
    const double area_top = std::max(1.0e-6, box.dim_l * box.dim_w);
    const double projected_area = (std::abs(ray.x) * area_forward) + (std::abs(ray.y) * area_side) +
                                  (std::abs(ray.z) * area_top);
    const double reference_area = std::max({area_forward, area_side, area_top, 1.0e-6});
    return std::clamp(0.45 + 0.55 * (projected_area / reference_area), 0.45, 1.0);
}

double hitbox_projected_area_m2(const Hitbox &box, double exposure_scale) {
    const double projected_area = std::max(
        1.0e-4, std::max({box.dim_l * box.dim_w, box.dim_l * box.dim_h, box.dim_w * box.dim_h}) *
                    std::clamp(exposure_scale, 0.05, 1.25));
    return projected_area;
}

double closure_intercept_scale(double closure_mps) {
    const double centered = std::clamp((closure_mps - 900.0) / 400.0, -1.0, 1.0);
    return std::clamp(1.0 + 0.08 * centered, 0.92, 1.08);
}

double closure_blast_coupling_scale(double closure_mps) {
    const double centered = std::clamp((closure_mps - 900.0) / 400.0, -1.0, 1.0);
    return std::clamp(1.0 + 0.05 * centered, 0.95, 1.05);
}

double warhead_mechanism_armor_scale(const Missile &missile, const Hitbox &box, double distance_m,
                                     double radius_m, double axis_weight, bool direct_hit) {
    const std::string family = warhead_effect_family(missile.warhead_profile);
    const double mass_kg = resolved_warhead_effective_mass_kg(missile);
    const double radius_quality =
        direct_hit || radius_m <= 1.0e-6 ? 1.0 : std::clamp(1.0 - distance_m / radius_m, 0.0, 1.0);

    double mechanism_capacity_mm = 4.0 + 0.45 * std::sqrt(mass_kg);
    double armor_coupling = 1.0;
    double lower_bound = 0.55;
    double upper_bound = 1.05;

    if (family == "blast") {
        mechanism_capacity_mm = 7.0 + 0.30 * std::sqrt(mass_kg);
        armor_coupling = 0.45;
        lower_bound = 0.70;
        upper_bound = 1.02;
    } else if (family == "fragmentation" || family == "blast_fragmentation") {
        mechanism_capacity_mm = 3.6 + 0.55 * std::sqrt(mass_kg);
        armor_coupling = 1.00;
        lower_bound = 0.52;
        upper_bound = 1.06;
    } else if (family == "continuous_rod") {
        mechanism_capacity_mm = 7.5 + 1.10 * std::sqrt(mass_kg);
        armor_coupling = 0.80;
        lower_bound = 0.62;
        upper_bound = 1.08;
    } else if (family == "hit_to_kill") {
        mechanism_capacity_mm = 14.0 + 1.35 * std::sqrt(mass_kg);
        armor_coupling = 0.55;
        lower_bound = 0.78;
        upper_bound = 1.10;
    }

    mechanism_capacity_mm *= 0.40 + 0.60 * radius_quality;
    if (family == "continuous_rod") {
        mechanism_capacity_mm *= std::clamp(0.80 + 0.20 * axis_weight, 0.75, 1.15);
    }

    const double effective_armor_mm = std::max(0.0, box.armor_mm) * armor_coupling;
    const double ratio =
        mechanism_capacity_mm / std::max(1.0e-6, mechanism_capacity_mm + effective_armor_mm);
    return std::clamp(0.48 + 0.58 * ratio, lower_bound, upper_bound);
}

WarheadMechanismLoadEvidence
estimate_warhead_mechanism_load(const Missile &missile, const Hitbox &target_shape,
                                double distance_m, double radius_m, double axis_weight,
                                double orientation_weight, double exposure_scale, bool direct_hit,
                                double closure_mps, const WarheadSpatialSample &spatial_sample) {
    WarheadMechanismLoadEvidence evidence{};
    const std::string family = warhead_effect_family(missile.warhead_profile);
    const double mass_kg = resolved_warhead_effective_mass_kg(missile);
    const double radius_quality =
        direct_hit || radius_m <= 1.0e-6 ? 1.0 : std::clamp(1.0 - distance_m / radius_m, 0.0, 1.0);
    const double standoff_m = std::max(direct_hit ? 1.0 : distance_m, 1.0);
    const double armor_mm = std::max(0.0, target_shape.armor_mm);
    const double exposure = std::clamp(exposure_scale, 0.05, 1.25);
    const double pattern = std::clamp(axis_weight * orientation_weight, 0.20, 1.60);
    const double closure = std::clamp(closure_mps, 0.0, 1600.0);
    const double projected_area_m2 = hitbox_projected_area_m2(target_shape, exposure);
    const double characteristic_length_m = std::sqrt(projected_area_m2);
    const double hit_estimate_scale =
        std::clamp(std::sqrt(std::clamp(spatial_sample.hit_estimate, 0.0, 4.0)) / 2.0, 0.0, 1.0);
    const double geometry_intercept_scale =
        std::clamp(0.52 + 0.18 * exposure + 0.18 * hit_estimate_scale +
                       0.12 * std::clamp(characteristic_length_m / 3.0, 0.25, 1.50),
                   0.45, 1.35);
    const double closure_intercept = closure_intercept_scale(closure);
    const double blast_coupling_scale =
        std::clamp(0.76 + 0.12 * exposure + 0.08 * hit_estimate_scale +
                       0.10 * std::clamp(characteristic_length_m / 3.0, 0.25, 1.50),
                   0.70, 1.28) *
        closure_blast_coupling_scale(closure);

    const bool has_physics_warhead = std::isfinite(missile.warhead_profile.gurney_constant_mps) &&
                                     std::isfinite(missile.warhead_profile.explosive_mass_kg) &&
                                     std::isfinite(missile.warhead_profile.case_mass_kg);

    if (family == "fragmentation" || family == "blast_fragmentation") {
        double fragment_count, fragment_mass_kg, fragment_velocity_mps;

        if (has_physics_warhead) {
            // Physics-based: use authored fragment specs or derive from case mass.
            const double C = missile.warhead_profile.explosive_mass_kg;
            const double M = missile.warhead_profile.case_mass_kg;
            const double gurney = missile.warhead_profile.gurney_constant_mps;
            const double CM_ratio = C / std::max(1.0e-6, M);
            const double V0 = gurney * std::sqrt(CM_ratio / (1.0 + 0.5 * CM_ratio));

            fragment_count = resolved_warhead_fragment_count(missile.warhead_profile, C + M);
            fragment_mass_kg =
                resolved_warhead_fragment_mass_kg(missile.warhead_profile, C + M, fragment_count);
            fragment_velocity_mps = std::clamp(V0, 550.0, 2500.0) * (0.42 + 0.58 * radius_quality);
            // Atmospheric decay: V(s) = V₀ · exp(-Cd·ρ·A·s / (2m))
            // Cd≈1.0 for supersonic fragment, ρ≈1.225 kg/m³ at sea level,
            // A derived from fragment mass assuming steel sphere (ρ_steel≈7800 kg/m³).
            {
                const double frag_radius_m =
                    std::cbrt((3.0 * fragment_mass_kg) / (4.0 * M_PI * 7800.0));
                const double frag_area_m2 = M_PI * frag_radius_m * frag_radius_m;
                const double decay_dist_m = std::max(0.0, distance_m - 2.0);
                const double decay_factor = std::exp(-(1.0 * 1.225 * frag_area_m2 * decay_dist_m) /
                                                     (2.0 * std::max(1.0e-6, fragment_mass_kg)));
                fragment_velocity_mps *= std::clamp(decay_factor, 0.3, 1.0);
            }
        } else {
            // Legacy empirical formulas (backward-compatible).
            fragment_count = resolved_warhead_fragment_count(missile.warhead_profile, mass_kg);
            fragment_mass_kg =
                resolved_warhead_fragment_mass_kg(missile.warhead_profile, mass_kg, fragment_count);
            fragment_velocity_mps =
                std::clamp(1120.0 + 18.0 * std::sqrt(mass_kg) + 0.18 * closure, 550.0, 1850.0) *
                (0.42 + 0.58 * radius_quality);
        }
        evidence.fragment_energy_j = 0.5 * fragment_mass_kg * fragment_velocity_mps *
                                     fragment_velocity_mps *
                                     std::clamp(spatial_sample.energy_scale, 0.05, 1.20);
        evidence.fragment_areal_density_per_m2 =
            std::max(0.0, spatial_sample.areal_density_per_m2) * geometry_intercept_scale *
            closure_intercept;
        const double penetration_capacity_mm =
            (1.2 + 0.028 * std::sqrt(std::max(0.0, evidence.fragment_energy_j))) *
            std::clamp(0.65 + 0.35 * spatial_sample.pattern_scale, 0.45, 1.30);
        evidence.penetration_margin = std::clamp(
            (penetration_capacity_mm - armor_mm) / std::max(1.0, armor_mm + 1.0), 0.0, 8.0);
    }

    if (family == "blast" || family == "blast_fragmentation") {
        const double cube_root_mass_kg = std::cbrt(std::max(0.1, mass_kg));
        const double inverse_scaled_distance = cube_root_mass_kg / standoff_m;
        evidence.blast_scaled_distance_m_kg13 = standoff_m / std::max(1.0e-6, cube_root_mass_kg);
        evidence.blast_overpressure_kpa =
            std::clamp(115.0 * inverse_scaled_distance * inverse_scaled_distance *
                           (0.30 + 0.70 * radius_quality) * exposure,
                       0.0, 1800.0);
        evidence.blast_impulse_kpa_ms =
            evidence.blast_overpressure_kpa *
            std::clamp(1.1 + 0.32 * std::cbrt(std::max(0.1, mass_kg)), 1.0, 5.0) *
            blast_coupling_scale;
    }

    if (family == "continuous_rod") {
        const double rod_count = std::clamp(3.2 * mass_kg, 24.0, 96.0);
        const double rod_segment_mass_kg = std::clamp((0.42 * mass_kg) / rod_count, 0.035, 0.42);

        const bool has_physics_warhead =
            std::isfinite(missile.warhead_profile.gurney_constant_mps) &&
            std::isfinite(missile.warhead_profile.explosive_mass_kg);

        double rod_velocity_mps;
        double cut_capacity_mm;

        if (has_physics_warhead) {
            // Physics-based: weld-limited cap + striking velocity decay + cutting threshold
            rod_velocity_mps =
                std::clamp(920.0 + 0.16 * closure, 450.0, 1150.0) * (0.50 + 0.50 * radius_quality);
            const double rod_striking_velocity_mps =
                rod_velocity_mps * std::exp(-0.004 * std::max(0.0, distance_m - 3.0));
            const double rod_energy_j = 0.5 * rod_segment_mass_kg * rod_velocity_mps *
                                        rod_velocity_mps *
                                        std::clamp(spatial_sample.energy_scale, 0.08, 1.20);
            cut_capacity_mm =
                rod_striking_velocity_mps >= 610.0
                    ? (3.0 + 0.022 * std::sqrt(std::max(0.0, rod_energy_j))) * pattern *
                          std::clamp(0.60 + 0.40 * spatial_sample.hit_estimate, 0.45, 1.35)
                    : 0.0;
        } else {
            // Legacy: original empirical formulas (backward-compatible)
            rod_velocity_mps =
                std::clamp(920.0 + 0.16 * closure, 450.0, 1450.0) * (0.50 + 0.50 * radius_quality);
            const double rod_energy_j = 0.5 * rod_segment_mass_kg * rod_velocity_mps *
                                        rod_velocity_mps *
                                        std::clamp(spatial_sample.energy_scale, 0.08, 1.20);
            cut_capacity_mm = (3.0 + 0.022 * std::sqrt(std::max(0.0, rod_energy_j))) * pattern *
                              std::clamp(0.60 + 0.40 * spatial_sample.hit_estimate, 0.45, 1.35);
        }

        evidence.rod_cut_margin =
            std::clamp((cut_capacity_mm - armor_mm) / std::max(1.0, armor_mm + 1.0), 0.0, 8.0);
        evidence.penetration_margin =
            std::max(evidence.penetration_margin, evidence.rod_cut_margin);
    }

    if (family == "hit_to_kill") {
        const double body_mass_kg = std::max(8.0, mass_kg * 4.0);
        const double impact_velocity_mps =
            std::clamp(std::max({missile.max_speed, closure, 300.0}), 300.0, 1700.0);
        const double kinetic_energy_j =
            0.5 * body_mass_kg * impact_velocity_mps * impact_velocity_mps;
        const double penetration_capacity_mm =
            8.0 + 0.012 * std::sqrt(std::max(0.0, kinetic_energy_j));
        evidence.penetration_margin = std::clamp(
            (penetration_capacity_mm - armor_mm) / std::max(1.0, armor_mm + 1.0), 0.0, 10.0);
    }

    return evidence;
}

WarheadSpatialSample sample_warhead_spatial_effect(const Missile &missile,
                                                   const Hitbox &target_shape, double distance_m,
                                                   double radius_m, double axis_weight,
                                                   double orientation_weight, double exposure_scale,
                                                   bool direct_hit) {
    WarheadSpatialSample sample{};
    const std::string family = warhead_effect_family(missile.warhead_profile);
    const double mass_kg = resolved_warhead_effective_mass_kg(missile);
    const double radius_quality =
        direct_hit || radius_m <= 1.0e-6 ? 1.0 : std::clamp(1.0 - distance_m / radius_m, 0.0, 1.0);
    const double exposed_area_m2 =
        std::max(1.0e-4, std::max({target_shape.dim_l * target_shape.dim_w,
                                   target_shape.dim_l * target_shape.dim_h,
                                   target_shape.dim_w * target_shape.dim_h}) *
                             std::clamp(exposure_scale, 0.05, 1.25));
    const double sphere_area_m2 = 4.0 * M_PI * std::max(distance_m * distance_m, 1.0);

    if (family == "fragmentation" || family == "blast_fragmentation") {
        const double fragment_count =
            resolved_warhead_fragment_count(missile.warhead_profile, mass_kg);
        sample.sample_count = static_cast<std::uint32_t>(std::round(fragment_count));
        const double pattern_scale = std::clamp(
            (0.70 + 0.30 * axis_weight) * std::clamp(orientation_weight, 0.70, 1.18), 0.50, 1.35);
        sample.areal_density_per_m2 =
            fragment_count / sphere_area_m2 * pattern_scale * (0.35 + 0.65 * radius_quality);
        sample.hit_estimate = fragment_count *
                              std::clamp(exposed_area_m2 / sphere_area_m2, 0.0, 0.35) *
                              pattern_scale * (0.35 + 0.65 * radius_quality);
        sample.energy_scale =
            std::clamp((0.35 + 0.65 * radius_quality) *
                           (0.70 + 0.30 * std::sqrt(mass_kg / std::max(1.0, mass_kg + 20.0))),
                       0.05, 1.10);
        sample.pattern_scale = pattern_scale;
    } else if (family == "continuous_rod") {
        const double rod_count = std::clamp(3.2 * mass_kg, 24.0, 96.0);
        sample.sample_count = static_cast<std::uint32_t>(std::round(rod_count));
        const double side_sweep = std::clamp(
            (axis_weight / 1.25) * std::clamp(orientation_weight, 0.42, 1.30), 0.15, 1.25);
        const double span_m = std::max(target_shape.dim_w, target_shape.dim_l);
        const double ring_circumference_m = 2.0 * M_PI * std::max(distance_m, 1.0);
        sample.hit_estimate = rod_count * std::clamp(span_m / ring_circumference_m, 0.0, 0.60) *
                              side_sweep * (0.45 + 0.55 * radius_quality);
        sample.energy_scale = std::clamp(0.45 + 0.55 * radius_quality, 0.08, 1.15);
        sample.pattern_scale = side_sweep;
    } else if (family == "blast") {
        sample.sample_count = 1;
        sample.hit_estimate =
            std::clamp(exposed_area_m2 / sphere_area_m2, 0.0, 1.0) * (0.65 + 0.35 * radius_quality);
        sample.energy_scale = std::clamp(std::pow(radius_quality, 1.6), 0.05, 1.0);
        sample.pattern_scale = std::clamp(orientation_weight, 0.94, 1.02);
    } else {
        sample.sample_count = 1;
        sample.hit_estimate = direct_hit ? 1.0 : std::clamp(radius_quality, 0.0, 1.0);
        sample.energy_scale = direct_hit ? 1.0 : std::clamp(radius_quality, 0.0, 1.0);
        sample.pattern_scale = std::clamp(axis_weight * orientation_weight, 0.25, 1.35);
    }

    sample.hit_estimate = std::max(0.0, sample.hit_estimate);
    sample.hit_fraction =
        sample.sample_count > 0
            ? std::clamp(sample.hit_estimate / static_cast<double>(sample.sample_count), 0.0, 1.0)
            : 0.0;
    sample.orientation_pattern_scale = std::clamp(orientation_weight, 0.0, 2.0);
    return sample;
}

double scaled_effect_delta(double base, double slope, double severity, double scale) {
    return std::clamp((base + slope * severity) * scale, 0.0, 0.95);
}

double localized_effect_delta(double base, double slope, double severity, double warhead_scale,
                              double spatial_scale) {
    const double resolved_spatial_scale = std::clamp(spatial_scale, 0.0, 1.0);
    return std::clamp(scaled_effect_delta(base, slope, severity, warhead_scale) *
                          resolved_spatial_scale,
                      0.0, 0.95);
}

double horizontal_speed_mps(const Velocity *velocity) {
    if (!velocity) {
        return 0.0;
    }
    return std::hypot(velocity->vx, velocity->vy);
}

double resolve_closure_mps(flecs::entity missile_entity, flecs::entity target_entity) {
    const Transform *missile_transform = missile_entity.get<Transform>();
    const Transform *target_transform = target_entity.get<Transform>();
    const Velocity *missile_velocity = missile_entity.get<Velocity>();
    const Velocity *target_velocity = target_entity.get<Velocity>();
    if (!missile_transform || !target_transform || !missile_velocity || !target_velocity) {
        return 0.0;
    }

    const double dx = target_transform->x - missile_transform->x;
    const double dy = target_transform->y - missile_transform->y;
    const double dz = target_transform->z - missile_transform->z;
    const double range = std::sqrt(dx * dx + dy * dy + dz * dz);
    if (range <= 1.0e-6) {
        return horizontal_speed_mps(missile_velocity) + horizontal_speed_mps(target_velocity);
    }

    const double ux = dx / range;
    const double uy = dy / range;
    const double uz = dz / range;
    const double rel_vx = target_velocity->vx - missile_velocity->vx;
    const double rel_vy = target_velocity->vy - missile_velocity->vy;
    const double rel_vz = target_velocity->vz - missile_velocity->vz;
    return std::max(0.0, -(rel_vx * ux + rel_vy * uy + rel_vz * uz));
}

Vec3 missile_velocity_axis_in_target_body(flecs::entity missile_entity,
                                          const Transform &target_transform) {
    const Velocity *missile_velocity = missile_entity.get<Velocity>();
    if (!missile_velocity) {
        return {0.0, 0.0, 0.0};
    }
    return vec3_normalize(world_to_body(target_transform, target_transform.x + missile_velocity->vx,
                                        target_transform.y + missile_velocity->vy,
                                        target_transform.z + missile_velocity->vz));
}

Vec3 missile_forward_axis_in_target_body(const Transform &missile_transform,
                                         const Transform &target_transform) {
    const Math::Vector3 missile_forward_world =
        Math::body_to_world({1.0, 0.0, 0.0}, missile_transform);
    return vec3_normalize(math_body_to_local_right_frame(
        Math::world_to_body(missile_forward_world, target_transform)));
}

double warhead_axis_projection_weight(const WarheadProfile &profile, const Vec3 &local_imp,
                                      const Hitbox &box, const Vec3 &velocity_axis_body) {
    const double axis_norm = vec3_norm(velocity_axis_body);
    if (axis_norm <= 1.0e-9) {
        return 1.0;
    }

    const Vec3 nearest = hitbox_nearest_point(local_imp, box);
    const Vec3 radial = vec3_normalize({
        nearest.x - local_imp.x,
        nearest.y - local_imp.y,
        nearest.z - local_imp.z,
    });
    const double radial_norm = vec3_norm(radial);
    if (radial_norm <= 1.0e-9) {
        return 1.0;
    }

    const double axial_alignment = std::abs(vec3_dot(radial, velocity_axis_body));
    const double side_alignment = std::sqrt(std::max(0.0, 1.0 - axial_alignment * axial_alignment));
    const std::string family = warhead_effect_family(profile);

    if (family == "continuous_rod") {
        return std::clamp(0.35 + 0.95 * side_alignment, 0.35, 1.25);
    }
    if (family == "hit_to_kill") {
        return std::clamp(0.70 + 0.45 * axial_alignment, 0.70, 1.15);
    }
    if (family == "blast") {
        return std::clamp(0.85 + 0.20 * axial_alignment, 0.85, 1.05);
    }
    if (family == "fragmentation" || family == "blast_fragmentation") {
        return std::clamp(0.75 + 0.45 * side_alignment, 0.75, 1.20);
    }
    return 1.0;
}

double warhead_orientation_pattern_weight(const WarheadProfile &profile, const Vec3 &local_imp,
                                          const Hitbox &box, const Vec3 &orientation_axis_body) {
    const double axis_norm = vec3_norm(orientation_axis_body);
    if (axis_norm <= 1.0e-9) {
        return 1.0;
    }

    const Vec3 nearest = hitbox_nearest_point(local_imp, box);
    const Vec3 radial = vec3_normalize({
        nearest.x - local_imp.x,
        nearest.y - local_imp.y,
        nearest.z - local_imp.z,
    });
    if (vec3_norm(radial) <= 1.0e-9) {
        return 1.0;
    }

    const double axial_alignment = std::abs(vec3_dot(radial, orientation_axis_body));
    const double side_alignment = std::sqrt(std::max(0.0, 1.0 - axial_alignment * axial_alignment));
    const std::string family = warhead_effect_family(profile);

    if (family == "continuous_rod") {
        return std::clamp(0.42 + 0.88 * side_alignment, 0.42, 1.30);
    }
    if (family == "fragmentation" || family == "blast_fragmentation") {
        return std::clamp(0.78 + 0.34 * side_alignment + 0.08 * axial_alignment, 0.70, 1.18);
    }
    if (family == "hit_to_kill") {
        return std::clamp(0.82 + 0.28 * axial_alignment, 0.82, 1.10);
    }
    if (family == "blast") {
        return std::clamp(0.94 + 0.08 * axial_alignment, 0.94, 1.02);
    }
    return 1.0;
}

bool make_default_effects_spatial_projection_candidate(
    const Missile &missile, const WarheadSpatialProjectionProfile &projection,
    const Vec3 &local_imp, const Vec3 &missile_axis_body, const Vec3 &warhead_orientation_axis_body,
    const Hitbox &target_shape, const Hitbox *owning_box, const DamageComponent *component,
    double distance_m, double spatial_radius_m, double exposure_scale, double closure_mps,
    SpatialProjectionCandidate *out_candidate) {
    if (!out_candidate || !owning_box) {
        return false;
    }

    const double axis_weight = warhead_axis_projection_weight(missile.warhead_profile, local_imp,
                                                              target_shape, missile_axis_body);
    const double armor_scale = warhead_mechanism_armor_scale(missile, target_shape, distance_m,
                                                             spatial_radius_m, axis_weight, false);
    const double orientation_weight = warhead_orientation_pattern_weight(
        missile.warhead_profile, local_imp, target_shape, warhead_orientation_axis_body);
    const WarheadSpatialSample spatial_sample =
        sample_warhead_spatial_effect(missile, target_shape, distance_m, spatial_radius_m,
                                      axis_weight, orientation_weight, exposure_scale, false);
    const double sampling_scale =
        std::clamp(0.55 + 0.35 * std::clamp(spatial_sample.hit_estimate, 0.0, 3.0) / 3.0 +
                       0.10 * spatial_sample.energy_scale,
                   0.35, 1.20);
    const double base_spatial_effect_scale =
        projected_spatial_effect_scale(distance_m, spatial_radius_m, projection);
    const double near_field_effect_floor = broad_warhead_near_field_effect_floor(
        missile.warhead_profile, distance_m, spatial_radius_m, projection);
    *out_candidate = SpatialProjectionCandidate{
        .box = owning_box,
        .component = component,
        .distance_m = distance_m,
        .effect_scale =
            std::clamp(std::max(base_spatial_effect_scale, near_field_effect_floor) * axis_weight *
                           orientation_weight * armor_scale * exposure_scale * sampling_scale,
                       projection.min_effect_scale, projection.max_effect_scale),
        .axis_weight = axis_weight,
        .orientation_weight = orientation_weight,
        .armor_scale = armor_scale,
        .exposure_scale = exposure_scale,
        .spatial_sample_count = spatial_sample.sample_count,
        .spatial_hit_estimate = spatial_sample.hit_estimate,
        .spatial_hit_fraction = spatial_sample.hit_fraction,
        .spatial_energy_scale = spatial_sample.energy_scale,
        .spatial_pattern_scale = spatial_sample.pattern_scale,
        .surface_incidence_cos =
            hitbox_surface_incidence_cos(local_imp, target_shape, missile_axis_body),
        .mechanism_load = with_surface_incidence(
            estimate_warhead_mechanism_load(missile, target_shape, distance_m, spatial_radius_m,
                                            axis_weight, orientation_weight, exposure_scale, false,
                                            closure_mps, spatial_sample),
            hitbox_surface_incidence_cos(local_imp, target_shape, missile_axis_body)),
    };
    return true;
}

std::string classify_local_aspect_bucket(const Vec3 &local_imp) {
    if (std::abs(local_imp.x) >= std::abs(local_imp.y)) {
        return local_imp.x >= 0.0 ? "nose" : "tail";
    }
    return "beam";
}

std::string classify_closure_bucket(double closure_mps) {
    if (closure_mps >= 700.0) {
        return "high";
    }
    if (closure_mps > 0.0 && closure_mps <= 250.0) {
        return "low";
    }
    return "medium";
}

std::string classify_miss_distance_bucket(bool direct_structure_hit) {
    return direct_structure_hit ? "direct_hit" : "near_miss";
}

const AircraftVulnerabilityEvidenceRow *find_matching_vulnerability_evidence_row(
    const AircraftVulnerabilityProfile &vulnerability, const std::string &family,
    const std::string &aspect_bucket, const std::string &closure_bucket,
    const std::string &miss_distance_bucket) {
    if (!aircraft_vulnerability_has_calibrated_evidence(vulnerability)) {
        return nullptr;
    }
    for (const AircraftVulnerabilityEvidenceRow &row : vulnerability.evidence_rows) {
        if (row.weapon_family == family && row.aspect_bucket == aspect_bucket &&
            row.closure_bucket == closure_bucket &&
            row.miss_distance_bucket == miss_distance_bucket && row.component_name.empty() &&
            row.component_system.empty() && row.component_redundancy_group_id.empty()) {
            return &row;
        }
    }
    return nullptr;
}

bool vulnerability_row_matches_component(const AircraftVulnerabilityEvidenceRow &row,
                                         const DamageComponent *component) {
    if (!component) {
        return row.component_name.empty() && row.component_system.empty() &&
               row.component_redundancy_group_id.empty();
    }
    if (!row.component_name.empty() && row.component_name != damage_component_key(*component)) {
        return false;
    }
    if (!row.component_system.empty() && row.component_system != component->system) {
        return false;
    }
    if (!row.component_redundancy_group_id.empty() &&
        row.component_redundancy_group_id != damage_component_redundancy_group_key(*component)) {
        return false;
    }
    return true;
}

bool vulnerability_row_matches_mechanism_load(const AircraftVulnerabilityEvidenceRow &row,
                                              const WarheadMechanismLoadEvidence &mechanism_load) {
    const auto passes_min = [](bool has_value, double threshold, double value) {
        return !has_value || value + 1.0e-9 >= threshold;
    };
    const auto passes_max = [](bool has_value, double threshold, double value) {
        return !has_value || value <= threshold + 1.0e-9;
    };

    return passes_min(row.has_min_fragment_energy_j, row.min_fragment_energy_j,
                      mechanism_load.fragment_energy_j) &&
           passes_max(row.has_max_fragment_energy_j, row.max_fragment_energy_j,
                      mechanism_load.fragment_energy_j) &&
           passes_min(row.has_min_fragment_areal_density_per_m2,
                      row.min_fragment_areal_density_per_m2,
                      mechanism_load.fragment_areal_density_per_m2) &&
           passes_max(row.has_max_fragment_areal_density_per_m2,
                      row.max_fragment_areal_density_per_m2,
                      mechanism_load.fragment_areal_density_per_m2) &&
           passes_min(row.has_min_penetration_margin, row.min_penetration_margin,
                      mechanism_load.penetration_margin) &&
           passes_max(row.has_max_penetration_margin, row.max_penetration_margin,
                      mechanism_load.penetration_margin) &&
           passes_min(row.has_min_blast_overpressure_kpa, row.min_blast_overpressure_kpa,
                      mechanism_load.blast_overpressure_kpa) &&
           passes_max(row.has_max_blast_overpressure_kpa, row.max_blast_overpressure_kpa,
                      mechanism_load.blast_overpressure_kpa) &&
           passes_min(row.has_min_blast_impulse_kpa_ms, row.min_blast_impulse_kpa_ms,
                      mechanism_load.blast_impulse_kpa_ms) &&
           passes_max(row.has_max_blast_impulse_kpa_ms, row.max_blast_impulse_kpa_ms,
                      mechanism_load.blast_impulse_kpa_ms) &&
           passes_min(row.has_min_blast_scaled_distance_m_kg13,
                      row.min_blast_scaled_distance_m_kg13,
                      mechanism_load.blast_scaled_distance_m_kg13) &&
           passes_max(row.has_max_blast_scaled_distance_m_kg13,
                      row.max_blast_scaled_distance_m_kg13,
                      mechanism_load.blast_scaled_distance_m_kg13) &&
           passes_min(row.has_min_rod_cut_margin, row.min_rod_cut_margin,
                      mechanism_load.rod_cut_margin) &&
           passes_max(row.has_max_rod_cut_margin, row.max_rod_cut_margin,
                      mechanism_load.rod_cut_margin) &&
           passes_min(row.has_min_surface_incidence_cos, row.min_surface_incidence_cos,
                      mechanism_load.surface_incidence_cos) &&
           passes_max(row.has_max_surface_incidence_cos, row.max_surface_incidence_cos,
                      mechanism_load.surface_incidence_cos);
}

bool vulnerability_row_has_mechanism_load_gate(const AircraftVulnerabilityEvidenceRow &row) {
    return row.has_min_fragment_energy_j || row.has_max_fragment_energy_j ||
           row.has_min_fragment_areal_density_per_m2 || row.has_max_fragment_areal_density_per_m2 ||
           row.has_min_penetration_margin || row.has_max_penetration_margin ||
           row.has_min_blast_overpressure_kpa || row.has_max_blast_overpressure_kpa ||
           row.has_min_blast_impulse_kpa_ms || row.has_max_blast_impulse_kpa_ms ||
           row.has_min_blast_scaled_distance_m_kg13 || row.has_max_blast_scaled_distance_m_kg13 ||
           row.has_min_rod_cut_margin || row.has_max_rod_cut_margin ||
           row.has_min_surface_incidence_cos || row.has_max_surface_incidence_cos;
}

int vulnerability_row_specificity(const AircraftVulnerabilityEvidenceRow &row) {
    int specificity = 0;
    if (!row.component_name.empty()) {
        specificity += 400;
    }
    if (!row.component_system.empty()) {
        specificity += 200;
    }
    if (!row.component_redundancy_group_id.empty()) {
        specificity += 100;
    }
    if (row.has_min_fragment_energy_j) {
        specificity += 1;
    }
    if (row.has_max_fragment_energy_j) {
        specificity += 1;
    }
    if (row.has_min_fragment_areal_density_per_m2) {
        specificity += 1;
    }
    if (row.has_max_fragment_areal_density_per_m2) {
        specificity += 1;
    }
    if (row.has_min_penetration_margin) {
        specificity += 1;
    }
    if (row.has_max_penetration_margin) {
        specificity += 1;
    }
    if (row.has_min_blast_overpressure_kpa) {
        specificity += 1;
    }
    if (row.has_max_blast_overpressure_kpa) {
        specificity += 1;
    }
    if (row.has_min_blast_impulse_kpa_ms) {
        specificity += 1;
    }
    if (row.has_max_blast_impulse_kpa_ms) {
        specificity += 1;
    }
    if (row.has_min_blast_scaled_distance_m_kg13) {
        specificity += 1;
    }
    if (row.has_max_blast_scaled_distance_m_kg13) {
        specificity += 1;
    }
    if (row.has_min_rod_cut_margin) {
        specificity += 1;
    }
    if (row.has_max_rod_cut_margin) {
        specificity += 1;
    }
    if (row.has_min_surface_incidence_cos) {
        specificity += 1;
    }
    if (row.has_max_surface_incidence_cos) {
        specificity += 1;
    }
    return specificity;
}

const AircraftVulnerabilityEvidenceRow *find_effect_scale_vulnerability_evidence_row(
    const AircraftVulnerabilityProfile &vulnerability, const std::string &family,
    const std::string &aspect_bucket, const std::string &closure_bucket,
    const std::string &miss_distance_bucket, const WarheadMechanismLoadEvidence *mechanism_load) {
    if (!vulnerability.effect_scale_authority) {
        return nullptr;
    }
    const AircraftVulnerabilityEvidenceRow *best_row = nullptr;
    int best_specificity = -1;
    for (const AircraftVulnerabilityEvidenceRow &row : vulnerability.evidence_rows) {
        if (row.weapon_family != family || row.aspect_bucket != aspect_bucket ||
            row.closure_bucket != closure_bucket ||
            row.miss_distance_bucket != miss_distance_bucket || !row.component_name.empty() ||
            !row.component_system.empty() || !row.component_redundancy_group_id.empty()) {
            continue;
        }
        if (!mechanism_load && vulnerability_row_has_mechanism_load_gate(row)) {
            continue;
        }
        if (mechanism_load && !vulnerability_row_matches_mechanism_load(row, *mechanism_load)) {
            continue;
        }
        const int specificity = vulnerability_row_specificity(row);
        if (specificity > best_specificity) {
            best_specificity = specificity;
            best_row = &row;
        }
    }
    return best_row;
}

const AircraftVulnerabilityEvidenceRow *find_component_failure_vulnerability_evidence_row(
    const AircraftVulnerabilityProfile &vulnerability, const std::string &family,
    const std::string &aspect_bucket, const std::string &closure_bucket,
    const std::string &miss_distance_bucket, const DamageComponent *component,
    const WarheadMechanismLoadEvidence &mechanism_load, bool *component_specific = nullptr) {
    if (!vulnerability.component_failure_probability_authority) {
        return nullptr;
    }
    const AircraftVulnerabilityEvidenceRow *best_row = nullptr;
    int best_specificity = -1;
    for (const AircraftVulnerabilityEvidenceRow &row : vulnerability.evidence_rows) {
        if (row.weapon_family != family || row.aspect_bucket != aspect_bucket ||
            row.closure_bucket != closure_bucket ||
            row.miss_distance_bucket != miss_distance_bucket ||
            !row.has_component_failure_probability ||
            !vulnerability_row_matches_component(row, component) ||
            !vulnerability_row_matches_mechanism_load(row, mechanism_load)) {
            continue;
        }
        const int specificity = vulnerability_row_specificity(row);
        if (specificity > best_specificity) {
            best_specificity = specificity;
            best_row = &row;
        }
    }
    if (component_specific) {
        *component_specific = best_specificity > 0;
    }
    return best_row;
}

VulnerabilityAdjustment make_vulnerability_adjustment(
    const WarheadProfile &warhead_profile, const AircraftVulnerabilityProfile *vulnerability,
    const Vec3 &local_imp, double closure_mps, double spatial_effect_scale,
    bool direct_structure_hit, const WarheadMechanismLoadEvidence *mechanism_load) {
    VulnerabilityAdjustment out{};
    if (!vulnerability) {
        return out;
    }
    out.profile_present = true;
    out.synthetic = vulnerability->synthetic;
    out.calibrated_evidence = aircraft_vulnerability_has_calibrated_evidence(*vulnerability);
    out.pk_authority = aircraft_vulnerability_pk_authority(*vulnerability);
    out.deterministic_fuze_authority =
        aircraft_vulnerability_deterministic_fuze_authority(*vulnerability);
    out.evidence_dataset_valid = vulnerability->evidence_dataset_valid;
    out.provenance = vulnerability->provenance;
    out.calibration_status = vulnerability->calibration_status;
    out.evidence_dataset_ref = vulnerability->evidence_dataset_ref;
    out.evidence_schema_version = vulnerability->evidence_schema_version;
    out.evidence_source_kind = vulnerability->evidence_source_kind;
    out.evidence_source_ref = vulnerability->evidence_source_ref;
    out.evidence_validation_artifact_ref = vulnerability->evidence_validation_artifact_ref;
    out.evidence_validation_manifest_schema_version =
        vulnerability->evidence_validation_manifest_schema_version;
    out.evidence_validation_status = vulnerability->evidence_validation_status;
    out.evidence_validation_artifact_sha256 = vulnerability->evidence_validation_artifact_sha256;
    out.evidence_validated_surrogate_model_ref =
        vulnerability->evidence_validated_surrogate_model_ref;
    out.evidence_validation_benchmark_ref = vulnerability->evidence_validation_benchmark_ref;
    out.evidence_validation_metrics_ref = vulnerability->evidence_validation_metrics_ref;
    out.evidence_validation_acceptance_criteria_ref =
        vulnerability->evidence_validation_acceptance_criteria_ref;

    const std::string family = warhead_effect_family(warhead_profile);
    double family_scale = vulnerability->fragmentation_scale;
    if (family == "blast") {
        family_scale = vulnerability->blast_scale;
    } else if (family == "continuous_rod") {
        family_scale = vulnerability->continuous_rod_scale;
    } else if (family == "hit_to_kill") {
        family_scale = vulnerability->hit_to_kill_scale;
    }
    out.family_scale = family_scale;

    out.aspect_bucket = classify_local_aspect_bucket(local_imp);
    if (out.aspect_bucket == "nose") {
        out.aspect_scale = vulnerability->nose_aspect_scale;
    } else if (out.aspect_bucket == "tail") {
        out.aspect_scale = vulnerability->tail_aspect_scale;
    } else if (out.aspect_bucket == "beam") {
        out.aspect_scale = vulnerability->beam_aspect_scale;
    }

    out.closure_mps = closure_mps;
    const std::string closure_bucket = classify_closure_bucket(closure_mps);
    if (closure_mps >= 700.0) {
        out.closure_scale = vulnerability->high_closure_scale;
    } else if (closure_mps > 0.0 && closure_mps <= 250.0) {
        out.closure_scale = vulnerability->low_closure_scale;
    }

    out.miss_distance_scale =
        direct_structure_hit ? vulnerability->direct_hit_scale : vulnerability->near_miss_scale;

    const std::string miss_distance_bucket = classify_miss_distance_bucket(direct_structure_hit);
    const AircraftVulnerabilityEvidenceRow *evidence_row =
        find_effect_scale_vulnerability_evidence_row(*vulnerability, family, out.aspect_bucket,
                                                     closure_bucket, miss_distance_bucket,
                                                     mechanism_load);
    if (evidence_row) {
        out.family_scale = evidence_row->family_scale;
        out.aspect_scale = evidence_row->aspect_scale;
        out.closure_scale = evidence_row->closure_scale;
        out.miss_distance_scale = evidence_row->miss_distance_scale;
        out.scale = evidence_row->effect_scale;
        out.effect_scale_source = "vulnerability_evidence_row";
        out.effect_scale_evidence_row_id = evidence_row->row_id;
        out.effect_scale_evidence_source_ref = evidence_row->source_ref;
        out.effect_scale_evidence_provenance = evidence_row->provenance;
    }

    const double raw_scale =
        out.family_scale * out.aspect_scale * out.closure_scale * out.miss_distance_scale;
    const double authority_floor = vulnerability->synthetic ? 0.80 : 0.55;
    const double authority_ceiling = vulnerability->synthetic ? 1.25 : 1.60;
    if (!evidence_row) {
        out.scale = std::clamp(raw_scale, authority_floor, authority_ceiling);
    } else {
        out.scale = std::clamp(out.scale, authority_floor, authority_ceiling);
    }

    if (!direct_structure_hit) {
        out.scale =
            std::clamp(out.scale * (0.85 + 0.15 * std::clamp(spatial_effect_scale, 0.0, 1.0)),
                       authority_floor, authority_ceiling);
    }

    return out;
}
