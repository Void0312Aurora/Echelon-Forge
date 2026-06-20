// Private fragment for default_effects_model.cpp.
// Included inside that file's anonymous namespace; not a standalone API.

template <typename ResolveSystemSeverity, typename ApplySystemEffect>
void apply_default_effects_spatial_projection(
    DefaultEffectsScratch& scratch,
    const HitboxConfig& hitboxes,
    bool structured_air_target,
    const Missile& missile,
    const WarheadSpatialProjectionProfile& warhead_projection,
    const Vec3& local_imp,
    const Vec3& missile_axis_body,
    const Vec3& warhead_orientation_axis_body,
    double closure_mps,
    SystemHealth* sys_health,
    ResolveSystemSeverity&& resolve_system_severity,
    ApplySystemEffect&& apply_system_effect
) {
    const bool broad_spatial_projection =
        warhead_uses_broad_spatial_projection(missile.warhead_profile);
    if (structured_air_target && (!scratch.structure_hit || broad_spatial_projection) &&
        !hitboxes.hitboxes.empty()) {
        std::vector<SpatialProjectionCandidate> candidates;
        candidates.reserve(hitboxes.hitboxes.size());
        const double spatial_radius_m =
            resolve_spatial_projection_radius_m(missile, warhead_projection);
        const auto make_component_projection_candidate = [&](
            const Hitbox& parent_box,
            const DamageComponent& component,
            SpatialProjectionCandidate* out_candidate) {
            const double distance_m = component_surface_distance(local_imp, component);
            if (distance_m > spatial_radius_m) {
                return false;
            }
            const Hitbox component_box = component_as_hitbox(component, parent_box);
            const double exposure_scale =
                component_projected_exposure_scale(local_imp, component);
            return make_default_effects_spatial_projection_candidate(
                missile,
                warhead_projection,
                local_imp,
                missile_axis_body,
                warhead_orientation_axis_body,
                component_box,
                &parent_box,
                &component,
                distance_m,
                spatial_radius_m,
                exposure_scale,
                closure_mps,
                out_candidate);
        };
        const auto make_box_projection_candidate = [&](
            const Hitbox& box,
            SpatialProjectionCandidate* out_candidate) {
            const double distance_m = hitbox_surface_distance(local_imp, box);
            if (distance_m > spatial_radius_m) {
                return false;
            }
            const double exposure_scale = hitbox_projected_exposure_scale(local_imp, box);
            return make_default_effects_spatial_projection_candidate(
                missile,
                warhead_projection,
                local_imp,
                missile_axis_body,
                warhead_orientation_axis_body,
                box,
                &box,
                nullptr,
                distance_m,
                spatial_radius_m,
                exposure_scale,
                closure_mps,
                out_candidate);
        };
        const auto collect_component_projection_candidates = [&](
            const Hitbox& parent_box) {
            std::vector<SpatialProjectionCandidate> component_candidates;
            for (const auto& component : parent_box.components) {
                SpatialProjectionCandidate candidate{};
                if (!make_component_projection_candidate(
                        parent_box,
                        component,
                        &candidate)) {
                    continue;
                }
                component_candidates.push_back(candidate);
            }
            std::sort(
                component_candidates.begin(),
                component_candidates.end(),
                [&](const SpatialProjectionCandidate& lhs,
                    const SpatialProjectionCandidate& rhs) {
                    const double lhs_score =
                        component_projection_priority_score(
                            missile.warhead_profile,
                            lhs);
                    const double rhs_score =
                        component_projection_priority_score(
                            missile.warhead_profile,
                            rhs);
                    if (lhs_score == rhs_score) {
                        return lhs.distance_m < rhs.distance_m;
                    }
                    return lhs_score > rhs_score;
                });
            return component_candidates;
        };
        const auto select_closest_component_projection_candidate = [&](
            const Hitbox& parent_box,
            SpatialProjectionCandidate* out_candidate) {
            bool found = false;
            SpatialProjectionCandidate best_candidate{};
            for (const auto& component : parent_box.components) {
                SpatialProjectionCandidate candidate{};
                if (!make_component_projection_candidate(
                        parent_box,
                        component,
                        &candidate)) {
                    continue;
                }
                if (!found ||
                    candidate.distance_m < best_candidate.distance_m ||
                    (candidate.distance_m == best_candidate.distance_m &&
                     candidate.effect_scale > best_candidate.effect_scale)) {
                    best_candidate = candidate;
                    found = true;
                }
            }
            if (found && out_candidate) {
                *out_candidate = best_candidate;
            }
            return found;
        };
        for (const auto& box : hitboxes.hitboxes) {
            if (broad_spatial_projection) {
                SpatialProjectionCandidate candidate{};
                if (make_box_projection_candidate(box, &candidate)) {
                    candidates.push_back(candidate);
                }
            }
            if (!broad_spatial_projection && !box.components.empty()) {
                for (const auto& component : box.components) {
                    SpatialProjectionCandidate component_candidate{};
                    if (make_component_projection_candidate(
                            box,
                            component,
                            &component_candidate)) {
                        candidates.push_back(component_candidate);
                    }
                }
            } else if (!broad_spatial_projection) {
                SpatialProjectionCandidate candidate{};
                if (make_box_projection_candidate(box, &candidate)) {
                    candidates.push_back(candidate);
                }
            }
        }

        std::sort(
            candidates.begin(),
            candidates.end(),
            [](const SpatialProjectionCandidate& lhs, const SpatialProjectionCandidate& rhs) {
                if (lhs.distance_m == rhs.distance_m) {
                    return lhs.effect_scale > rhs.effect_scale;
                }
                return lhs.distance_m < rhs.distance_m;
            });

        const std::size_t projected_count =
            std::min(candidates.size(), warhead_projection.max_projected_hitboxes);
        for (std::size_t candidate_index = 0; candidate_index < projected_count; ++candidate_index) {
            const SpatialProjectionCandidate& candidate = candidates[candidate_index];
            const Hitbox* projected_box = candidate.box;
            if (!projected_box) {
                continue;
            }
            const DamageComponent* projected_component = candidate.component;
            record_default_effects_warhead_effect_sample(
                scratch,
                candidate.effect_scale,
                candidate.armor_scale * candidate.exposure_scale,
                candidate.armor_scale,
                candidate.exposure_scale,
                make_default_effects_spatial_sample(candidate),
                candidate.mechanism_load);
            ++scratch.projected_hitbox_count;
            scratch.structure_hit = true;
            spdlog::info(
                "PROXIMITY FIELD >>> Box {}{} NEAR HIT at {:.2f} m, quality {:.2f}, armor {:.2f}, exposure {:.2f}",
                projected_box->id,
                projected_component ? " component" : "",
                candidate.distance_m,
                candidate.effect_scale,
                candidate.armor_scale,
                candidate.exposure_scale);

            const double projected_system_severity =
                std::clamp(
                    resolve_system_severity(
                        candidate.effect_scale,
                        false,
                        candidate.mechanism_load) *
                        candidate.effect_scale,
                    0.02,
                    0.95);
            if (!projected_component &&
                broad_spatial_projection &&
                !projected_box->components.empty()) {
                std::vector<SpatialProjectionCandidate> component_candidates;
                if (candidate_index == 0) {
                    component_candidates =
                        collect_component_projection_candidates(*projected_box);
                    if (component_candidates.size() > 2U) {
                        component_candidates.resize(2U);
                    }
                } else {
                    SpatialProjectionCandidate closest_candidate{};
                    if (select_closest_component_projection_candidate(
                            *projected_box,
                            &closest_candidate)) {
                        component_candidates.push_back(closest_candidate);
                    }
                }
                for (const SpatialProjectionCandidate& component_candidate :
                     component_candidates) {
                    record_default_effects_warhead_effect_sample(
                        scratch,
                        component_candidate.effect_scale,
                        component_candidate.armor_scale *
                            component_candidate.exposure_scale,
                        component_candidate.armor_scale,
                        component_candidate.exposure_scale,
                        make_default_effects_spatial_sample(component_candidate),
                        component_candidate.mechanism_load);

                    const double component_projected_system_severity = std::clamp(
                        resolve_system_severity(
                            component_candidate.effect_scale,
                            false,
                            component_candidate.mechanism_load) *
                            component_candidate.effect_scale,
                        0.02,
                        0.95);
                    const double component_scale =
                        resolve_default_effects_component_scale(
                            missile.warhead_profile,
                            *component_candidate.component);
                    scratch.sampled_component_threshold_scale =
                        std::max(
                            scratch.sampled_component_threshold_scale,
                            component_scale);
                    ComponentMechanismLoadRow* component_row =
                        record_default_effects_component_hit(
                            scratch,
                            *component_candidate.component,
                            component_candidate.effect_scale,
                            component_scale,
                            false,
                            component_candidate.distance_m,
                            component_candidate.mechanism_load);
                    scratch.processed_air_systems.insert(
                        component_candidate.component->system);
                    apply_system_effect(
                        component_candidate.component->system,
                        component_projected_system_severity,
                        component_candidate.effect_scale,
                        component_scale,
                        false,
                        component_candidate.mechanism_load,
                        component_candidate.component->critical,
                        component_candidate.component->redundancy_group,
                        component_candidate.component,
                        component_row);
                    spdlog::info(
                        "   - projected component {}:{} Status: {:.2f}",
                        component_candidate.component->name.empty()
                            ? component_candidate.component->system
                            : component_candidate.component->name,
                        component_candidate.component->system,
                        sys_health->systems[
                            component_candidate.component->system]);
                }
            }
            if (projected_component) {
                const double component_scale =
                    resolve_default_effects_component_scale(
                        missile.warhead_profile,
                        *projected_component);
                scratch.sampled_component_threshold_scale =
                    std::max(scratch.sampled_component_threshold_scale, component_scale);
                ComponentMechanismLoadRow* component_row =
                    record_default_effects_component_hit(
                        scratch,
                        *projected_component,
                        candidate.effect_scale,
                        component_scale,
                        false,
                        candidate.distance_m,
                        candidate.mechanism_load);
                apply_system_effect(
                    projected_component->system,
                    projected_system_severity,
                    candidate.effect_scale,
                    component_scale,
                    false,
                    candidate.mechanism_load,
                    projected_component->critical,
                    projected_component->redundancy_group,
                    projected_component,
                    component_row);
                spdlog::info(
                    "   - component {}:{} Status: {:.2f}",
                    projected_component->name.empty()
                        ? projected_component->system
                        : projected_component->name,
                    projected_component->system,
                    sys_health->systems[projected_component->system]);
            } else {
                for (const auto& system : projected_box->protected_systems) {
                    if (!scratch.processed_air_systems.insert(system).second) {
                        continue;
                    }
                    const double component_scale =
                        component_mechanism_threshold_scale(missile.warhead_profile, system);
                    scratch.sampled_component_threshold_scale =
                        std::max(scratch.sampled_component_threshold_scale, component_scale);
                    apply_system_effect(
                        system,
                        projected_system_severity,
                        candidate.effect_scale,
                        component_scale,
                        false,
                        candidate.mechanism_load);
                    spdlog::info("   - {} Status: {:.2f}", system, sys_health->systems[system]);
                }
            }
        }
    }
}
