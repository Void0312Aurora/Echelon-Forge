// Private fragment for default_effects_model.cpp.
// Included inside that file's anonymous namespace; not a standalone API.

template <typename ResolveSystemSeverity, typename ApplySystemEffect>
void apply_default_effects_direct_hitboxes(
    DefaultEffectsScratch& scratch,
    const HitboxConfig& hitboxes,
    bool structured_air_target,
    const Missile& missile,
    const Vec3& local_imp,
    const Vec3& warhead_orientation_axis_body,
    const Vec3& missile_axis_body,
    double closure_mps,
    SystemHealth* sys_health,
    ResolveSystemSeverity&& resolve_system_severity,
    ApplySystemEffect&& apply_system_effect
) {
    for (const auto& box : hitboxes.hitboxes) {
        if (check_hitbox(local_imp, box)) {
            scratch.structure_hit = true;
            scratch.direct_hitbox_intersection = true;
            spdlog::info("HITBOX >>> Box {} HIT! Protected Systems:", box.id);

            bool component_direct_hit = false;
            if (structured_air_target && !box.components.empty()) {
                for (const auto& component : box.components) {
                    if (!check_component(local_imp, component)) {
                        continue;
                    }
                    component_direct_hit = true;
                    const Hitbox component_box = component_as_hitbox(component, box);
                    const double armor_scale = warhead_mechanism_armor_scale(
                        missile,
                        component_box,
                        0.0,
                        1.0,
                        1.0,
                        true);
                    const double exposure_scale =
                        component_projected_exposure_scale(local_imp, component);
                    const double orientation_weight = warhead_orientation_pattern_weight(
                        missile.warhead_profile,
                        local_imp,
                        component_box,
                        warhead_orientation_axis_body);
                    const WarheadSpatialSample spatial_sample =
                        sample_warhead_spatial_effect(
                            missile,
                            component_box,
                            0.0,
                            1.0,
                            1.0,
                            orientation_weight,
                            exposure_scale,
                            true);
                    const WarheadMechanismLoadEvidence mechanism_load =
                        with_surface_incidence(
                            estimate_warhead_mechanism_load(
                                missile,
                                component_box,
                                0.0,
                                1.0,
                                1.0,
                                orientation_weight,
                                exposure_scale,
                                true,
                                closure_mps,
                                spatial_sample),
                            hitbox_surface_incidence_cos(
                                local_imp,
                                component_box,
                                missile_axis_body));
                    const double direct_mechanism_scale =
                        std::clamp(armor_scale * exposure_scale, 0.05, 1.10);
                    record_default_effects_warhead_effect_sample(
                        scratch,
                        direct_mechanism_scale,
                        direct_mechanism_scale,
                        armor_scale,
                        exposure_scale,
                        spatial_sample,
                        mechanism_load);

                    const double component_scale =
                        resolve_default_effects_component_scale(
                            missile.warhead_profile,
                            component);
                    scratch.sampled_component_threshold_scale =
                        std::max(scratch.sampled_component_threshold_scale, component_scale);
                    ComponentMechanismLoadRow* component_row =
                        record_default_effects_component_hit(
                            scratch,
                            component,
                            direct_mechanism_scale,
                            component_scale,
                            true,
                            0.0,
                            mechanism_load);
                    const double direct_system_severity =
                        resolve_system_severity(
                            direct_mechanism_scale,
                            true,
                            mechanism_load);
                    apply_system_effect(
                        component.system,
                        direct_system_severity,
                        direct_mechanism_scale,
                        component_scale,
                        true,
                        mechanism_load,
                        component.critical,
                        component.redundancy_group,
                        &component,
                        component_row);
                    spdlog::info(
                        "   - component {}:{} Status: {:.2f} component_scale={:.2f}",
                        component.name.empty() ? component.system : component.name,
                        component.system,
                        sys_health->systems[component.system],
                        component_scale);
                }
            }

            if (!structured_air_target || box.components.empty() || !component_direct_hit) {
                const double armor_scale = structured_air_target
                    ? warhead_mechanism_armor_scale(
                          missile,
                          box,
                          0.0,
                          1.0,
                          1.0,
                          true)
                    : 1.0;
                const double exposure_scale = structured_air_target
                    ? hitbox_projected_exposure_scale(local_imp, box)
                    : 1.0;
                WarheadMechanismLoadEvidence mechanism_load{};
                if (structured_air_target) {
                    const double orientation_weight = warhead_orientation_pattern_weight(
                        missile.warhead_profile,
                        local_imp,
                        box,
                        warhead_orientation_axis_body);
                    const WarheadSpatialSample spatial_sample =
                        sample_warhead_spatial_effect(
                            missile,
                            box,
                            0.0,
                            1.0,
                            1.0,
                            orientation_weight,
                            exposure_scale,
                            true);
                    mechanism_load = with_surface_incidence(
                        estimate_warhead_mechanism_load(
                            missile,
                            box,
                            0.0,
                            1.0,
                            1.0,
                            orientation_weight,
                            exposure_scale,
                            true,
                            closure_mps,
                            spatial_sample),
                        hitbox_surface_incidence_cos(
                            local_imp,
                            box,
                            missile_axis_body));
                    const double direct_mechanism_scale =
                        std::clamp(armor_scale * exposure_scale, 0.05, 1.10);
                    record_default_effects_warhead_effect_sample(
                        scratch,
                        direct_mechanism_scale,
                        direct_mechanism_scale,
                        armor_scale,
                        exposure_scale,
                        spatial_sample,
                        mechanism_load);
                } else {
                    const double direct_mechanism_scale =
                        std::clamp(armor_scale * exposure_scale, 0.05, 1.10);
                    scratch.spatial_effect_scale =
                        std::max(scratch.spatial_effect_scale, direct_mechanism_scale);
                    scratch.sampled_mechanism_scale =
                        std::max(scratch.sampled_mechanism_scale, direct_mechanism_scale);
                    scratch.sampled_armor_scale =
                        std::min(scratch.sampled_armor_scale, armor_scale);
                    scratch.sampled_exposure_scale =
                        std::min(scratch.sampled_exposure_scale, exposure_scale);
                }
                const double direct_mechanism_scale =
                    std::clamp(armor_scale * exposure_scale, 0.05, 1.10);

                for (const auto& system : box.protected_systems) {
                    if (structured_air_target &&
                        !scratch.processed_air_systems.insert(system).second) {
                        continue;
                    }
                    const double component_scale = structured_air_target
                        ? component_mechanism_threshold_scale(missile.warhead_profile, system)
                        : 1.0;
                    scratch.sampled_component_threshold_scale =
                        std::max(scratch.sampled_component_threshold_scale, component_scale);
                    const double direct_system_severity =
                        resolve_system_severity(
                            direct_mechanism_scale,
                            true,
                            mechanism_load);
                    apply_system_effect(
                        system,
                        direct_system_severity,
                        direct_mechanism_scale,
                        component_scale,
                        true,
                        mechanism_load);
                    spdlog::info(
                        "   - {} Status: {:.2f} component_scale={:.2f}",
                        system,
                        sys_health->systems[system],
                        component_scale);
                }
            }
        }
    }
}
