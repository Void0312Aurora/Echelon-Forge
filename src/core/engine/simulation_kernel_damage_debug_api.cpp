#include "simulation_kernel.h"
#include "simulation_kernel_engagement_event_store.h"

#include "components/basic/common.h"
#include "components/combat/damage.h"
#include "components/combat/health.h"
#include "components/combat/weapon.h"
#include "core/interfaces/effects_model.h"

#include <algorithm>
#include <array>
#include <cstdio>
#include <limits>
#include <cmath>
#include <string>

namespace {

Transform local_body_point_to_world_transform(
    const Transform& target_transform,
    double local_forward_m,
    double local_right_m,
    double local_up_m
) {
    const Math::Vector3 world_delta = Math::body_to_world(
        {local_forward_m, -local_right_m, local_up_m},
        target_transform);
    return {
        target_transform.x + world_delta.x,
        target_transform.y + world_delta.y,
        target_transform.z + world_delta.z,
        target_transform.heading,
        target_transform.pitch,
        target_transform.roll,
    };
}

std::array<double, 3> world_point_to_local_body(
    const Transform& target_transform,
    double world_x,
    double world_y,
    double world_z
) {
    const Math::Vector3 local = Math::world_to_body(
        {
            world_x - target_transform.x,
            world_y - target_transform.y,
            world_z - target_transform.z,
        },
        target_transform);
    return {
        local.x,
        -local.y,
        local.z,
    };
}

std::array<double, 3> velocity_axis_in_target_body(
    const Transform& target_transform,
    double vx,
    double vy,
    double vz
) {
    const double norm = std::sqrt(vx * vx + vy * vy + vz * vz);
    if (norm <= 1.0e-9) {
        return {0.0, 0.0, 0.0};
    }
    const auto local_velocity = world_point_to_local_body(
        target_transform,
        target_transform.x + vx,
        target_transform.y + vy,
        target_transform.z + vz);
    return {
        local_velocity[0] / norm,
        local_velocity[1] / norm,
        local_velocity[2] / norm,
    };
}

double resolve_closure_from_impact(
    const Transform& target_transform,
    const Transform& impact_transform,
    const Velocity* target_velocity,
    double missile_vx,
    double missile_vy,
    double missile_vz
) {
    const double target_vx = target_velocity ? target_velocity->vx : 0.0;
    const double target_vy = target_velocity ? target_velocity->vy : 0.0;
    const double target_vz = target_velocity ? target_velocity->vz : 0.0;
    const double rel_vx = target_vx - missile_vx;
    const double rel_vy = target_vy - missile_vy;
    const double rel_vz = target_vz - missile_vz;
    const double dx = target_transform.x - impact_transform.x;
    const double dy = target_transform.y - impact_transform.y;
    const double dz = target_transform.z - impact_transform.z;
    const double range = std::sqrt(dx * dx + dy * dy + dz * dz);
    if (range <= 1.0e-6) {
        return std::sqrt(rel_vx * rel_vx + rel_vy * rel_vy + rel_vz * rel_vz);
    }
    const double ux = dx / range;
    const double uy = dy / range;
    const double uz = dz / range;
    return std::max(0.0, -(rel_vx * ux + rel_vy * uy + rel_vz * uz));
}

double local_miss_distance_m(
    double local_forward_m,
    double local_right_m,
    double local_up_m
) {
    return std::sqrt(
        local_forward_m * local_forward_m +
        local_right_m * local_right_m +
        local_up_m * local_up_m);
}

}  // namespace


bool SimulationKernel::debug_apply_proximity_hit(
    uint64_t attacker_id,
    uint64_t target_id,
    double damage,
    double fuse_distance
) {
    auto attacker = ecs.entity(attacker_id);
    auto target = ecs.entity(target_id);
    if (!attacker.is_valid() || !target.is_valid()) {
        return false;
    }

    const Transform* target_transform = target.get<Transform>();
    if (!target_transform) {
        return false;
    }

    const EffectsModelRef* effects_ref = ecs.get<EffectsModelRef>();
    if (!effects_ref || !effects_ref->model) {
        return false;
    }

    const EngagementDamageStateSnapshot before = engagement_event_store_->capture_engagement_damage_state(target_id);

    Missile synthetic{};
    synthetic.attacker_id = attacker_id;
    synthetic.target_id = target_id;
    synthetic.max_speed = 900.0;
    synthetic.turn_rate = 20.0;
    synthetic.fuse_distance = fuse_distance;
    synthetic.damage = damage;
    synthetic.seeker_fov_deg = 120.0;
    synthetic.seeker_lock_range = 10000.0;
    synthetic.guidance_delay_s = 0.0;
    synthetic.guidance_update_period_s = 0.0;
    synthetic.last_guidance_time = -1.0;
    synthetic.launch_time = 0.0;
    synthetic.max_flight_time_s = 30.0;
    synthetic.nav_gain = 3.0;
    synthetic.active = true;
    synthetic.warhead_profile = make_synthetic_warhead_profile(damage, fuse_distance, "debug_synthetic_warhead");
    synthetic.fuze_profile = make_synthetic_fuze_profile(fuse_distance, "debug_synthetic_fuze_distance");
    synthetic.rng_state = 123456789ULL;
    synthetic.proximity_min_dist_m = 0.0;
    synthetic.proximity_last_dist_m = 0.0;
    synthetic.proximity_engaged = true;

    const KeyEntity* target_key = target.get<KeyEntity>();
    const bool structured_air_target = target_key &&
        (target_key->type == UnitType::Aircraft || target_key->type == UnitType::C2Node) &&
        target.get<HitboxConfig>() != nullptr &&
        target.get<SystemHealth>() != nullptr &&
        target.get<PlatformDamageState>() != nullptr;

    const Transform impact_transform = local_body_point_to_world_transform(
        *target_transform,
        0.0,
        0.0,
        structured_air_target ? 0.0 : 2.0);

    auto impact = ecs.entity()
        .set<Transform>(impact_transform)
        .set<Missile>(synthetic)
        .add<SimObject>();

    const EffectsResult effects_result =
        effects_ref->model->on_proximity_hit(ecs, impact, synthetic, target);
    const EngagementDamageStateSnapshot after = engagement_event_store_->capture_engagement_damage_state(target_id);
    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
    const auto detonation_local = world_point_to_local_body(
        *target_transform,
        impact_transform.x,
        impact_transform.y,
        impact_transform.z);
    (void)engagement_event_store_->record_effects_damage_event(
        static_cast<uint64_t>(impact.id()),
        target_id,
        before,
        after,
        "debug_proximity_hit",
        "hit",
        current_time,
        current_time,
        local_miss_distance_m(detonation_local[0], detonation_local[1], detonation_local[2]),
        detonation_local[0],
        detonation_local[1],
        detonation_local[2],
        impact_transform.heading,
        impact_transform.pitch,
        impact_transform.roll,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        1.0,
        warhead_effect_family(synthetic.warhead_profile),
        0.0,
        fuse_distance,
        true,
        true,
        fuze_profile_type(synthetic.fuze_profile),
        synthetic.fuze_profile.trigger_radius_m,
        synthetic.fuze_profile.delay_s,
        synthetic.fuze_profile.reliability,
        synthetic.fuze_profile.synthetic,
        "debug",
        0.0,
        1.0,
        synthetic.fuze_profile.reliability,
        0.0,
        0.0,
        0.0,
        false,
        effects_result.direct_hitbox_intersection,
        effects_result.projected_hitbox_count,
        effects_result.spatial_effect_scale,
        effects_result.mechanism_armor_scale,
        effects_result.mechanism_exposure_scale,
        effects_result.mechanism_effect_scale,
        effects_result.mechanism_fragment_energy_j,
        effects_result.mechanism_fragment_areal_density_per_m2,
        effects_result.mechanism_penetration_margin,
        effects_result.mechanism_blast_overpressure_kpa,
        effects_result.mechanism_blast_impulse_kpa_ms,
        effects_result.mechanism_blast_scaled_distance_m_kg13,
        effects_result.mechanism_rod_cut_margin,
        effects_result.warhead_spatial_sample_count,
        effects_result.warhead_spatial_hit_estimate,
        effects_result.warhead_spatial_hit_fraction,
        effects_result.warhead_spatial_energy_scale,
        effects_result.warhead_spatial_pattern_scale,
        effects_result.warhead_orientation_axis_forward,
        effects_result.warhead_orientation_axis_right,
        effects_result.warhead_orientation_axis_up,
        effects_result.warhead_orientation_pattern_scale,
        effects_result.component_threshold_scale,
        effects_result.component_failure_probability,
        effects_result.component_failure_probability_source,
        effects_result.component_failure_probability_calibrated,
        effects_result.component_failure_probability_evidence_dataset_ref,
        effects_result.component_failure_probability_evidence_row_id,
        effects_result.component_failure_probability_evidence_source_ref,
        effects_result.component_failure_probability_evidence_provenance,
        effects_result.component_failure_sample,
        effects_result.component_failure_count,
        effects_result.component_hit_count,
        effects_result.component_mechanism_load_rows,
        effects_result.component_primary_name,
        effects_result.component_primary_system,
        effects_result.component_primary_redundancy_group,
        effects_result.component_primary_critical,
        effects_result.component_primary_redundancy_group_id,
        effects_result.component_primary_integrity,
        effects_result.component_primary_mechanism_fragment_energy_j,
        effects_result.component_primary_mechanism_fragment_areal_density_per_m2,
        effects_result.component_primary_mechanism_penetration_margin,
        effects_result.component_primary_mechanism_blast_overpressure_kpa,
        effects_result.component_primary_mechanism_blast_impulse_kpa_ms,
        effects_result.component_primary_mechanism_blast_scaled_distance_m_kg13,
        effects_result.component_primary_mechanism_rod_cut_margin,
        effects_result.component_redundancy_group_availability,
        effects_result.component_redundancy_group_member_count,
        effects_result.component_redundancy_group_failed_count,
        effects_result.vulnerability_profile_present,
        effects_result.vulnerability_profile_synthetic,
        effects_result.vulnerability_calibrated_evidence,
        effects_result.vulnerability_pk_authority,
        effects_result.vulnerability_deterministic_fuze_authority,
        effects_result.vulnerability_evidence_dataset_valid,
        effects_result.vulnerability_evidence_dataset_ref,
        effects_result.vulnerability_calibration_status,
        effects_result.vulnerability_provenance,
        effects_result.vulnerability_evidence_schema_version,
        effects_result.vulnerability_evidence_source_kind,
        effects_result.vulnerability_evidence_source_ref,
        effects_result.vulnerability_evidence_validation_artifact_ref,
        effects_result.vulnerability_evidence_validation_manifest_schema_version,
        effects_result.vulnerability_evidence_validation_status,
        effects_result.vulnerability_evidence_validation_artifact_sha256,
        effects_result.vulnerability_evidence_validated_surrogate_model_ref,
        effects_result.vulnerability_evidence_validation_benchmark_ref,
        effects_result.vulnerability_evidence_validation_metrics_ref,
        effects_result.vulnerability_evidence_validation_acceptance_criteria_ref,
        effects_result.vulnerability_aspect_bucket,
        effects_result.vulnerability_family_scale,
        effects_result.vulnerability_aspect_scale,
        effects_result.vulnerability_closure_mps,
        effects_result.vulnerability_closure_scale,
        effects_result.vulnerability_miss_distance_scale,
        effects_result.vulnerability_effect_scale,
        effects_result.vulnerability_effect_scale_source,
        effects_result.vulnerability_effect_scale_evidence_row_id,
        effects_result.vulnerability_effect_scale_evidence_source_ref,
        effects_result.vulnerability_effect_scale_evidence_provenance,
        effects_result.mechanism_surface_incidence_cos,
        effects_result.component_primary_mechanism_surface_incidence_cos);
    impact.destruct();
    return true;
}

bool SimulationKernel::debug_apply_local_proximity_hit(
    uint64_t attacker_id,
    uint64_t target_id,
    double local_forward_m,
    double local_right_m,
    double local_up_m,
    double damage,
    double fuse_distance
) {
    auto attacker = ecs.entity(attacker_id);
    auto target = ecs.entity(target_id);
    if (!attacker.is_valid() || !target.is_valid()) {
        return false;
    }

    const Transform* target_transform = target.get<Transform>();
    if (!target_transform) {
        return false;
    }

    const EffectsModelRef* effects_ref = ecs.get<EffectsModelRef>();
    if (!effects_ref || !effects_ref->model) {
        return false;
    }

    const EngagementDamageStateSnapshot before = engagement_event_store_->capture_engagement_damage_state(target_id);

    Missile synthetic{};
    synthetic.attacker_id = attacker_id;
    synthetic.target_id = target_id;
    synthetic.max_speed = 900.0;
    synthetic.turn_rate = 20.0;
    synthetic.fuse_distance = fuse_distance;
    synthetic.damage = damage;
    synthetic.seeker_fov_deg = 120.0;
    synthetic.seeker_lock_range = 10000.0;
    synthetic.guidance_delay_s = 0.0;
    synthetic.guidance_update_period_s = 0.0;
    synthetic.last_guidance_time = -1.0;
    synthetic.launch_time = 0.0;
    synthetic.max_flight_time_s = 30.0;
    synthetic.nav_gain = 3.0;
    synthetic.active = true;
    synthetic.warhead_profile = make_synthetic_warhead_profile(damage, fuse_distance, "debug_synthetic_warhead");
    synthetic.fuze_profile = make_synthetic_fuze_profile(fuse_distance, "debug_synthetic_fuze_distance");
    synthetic.rng_state = 123456789ULL;
    synthetic.proximity_min_dist_m = 0.0;
    synthetic.proximity_last_dist_m = 0.0;
    synthetic.proximity_engaged = true;

    const Transform impact_transform = local_body_point_to_world_transform(
        *target_transform,
        local_forward_m,
        local_right_m,
        local_up_m);
    auto impact = ecs.entity()
        .set<Transform>(impact_transform)
        .set<Missile>(synthetic)
        .add<SimObject>();

    const EffectsResult effects_result =
        effects_ref->model->on_proximity_hit(ecs, impact, synthetic, target);
    const EngagementDamageStateSnapshot after = engagement_event_store_->capture_engagement_damage_state(target_id);
    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
    const auto detonation_local = world_point_to_local_body(
        *target_transform,
        impact_transform.x,
        impact_transform.y,
        impact_transform.z);
    (void)engagement_event_store_->record_effects_damage_event(
        static_cast<uint64_t>(impact.id()),
        target_id,
        before,
        after,
        "debug_local_proximity_hit",
        "hit",
        current_time,
        current_time,
        local_miss_distance_m(detonation_local[0], detonation_local[1], detonation_local[2]),
        detonation_local[0],
        detonation_local[1],
        detonation_local[2],
        impact_transform.heading,
        impact_transform.pitch,
        impact_transform.roll,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        1.0,
        warhead_effect_family(synthetic.warhead_profile),
        0.0,
        fuse_distance,
        true,
        true,
        fuze_profile_type(synthetic.fuze_profile),
        synthetic.fuze_profile.trigger_radius_m,
        synthetic.fuze_profile.delay_s,
        synthetic.fuze_profile.reliability,
        synthetic.fuze_profile.synthetic,
        "debug",
        0.0,
        1.0,
        synthetic.fuze_profile.reliability,
        0.0,
        0.0,
        0.0,
        false,
        effects_result.direct_hitbox_intersection,
        effects_result.projected_hitbox_count,
        effects_result.spatial_effect_scale,
        effects_result.mechanism_armor_scale,
        effects_result.mechanism_exposure_scale,
        effects_result.mechanism_effect_scale,
        effects_result.mechanism_fragment_energy_j,
        effects_result.mechanism_fragment_areal_density_per_m2,
        effects_result.mechanism_penetration_margin,
        effects_result.mechanism_blast_overpressure_kpa,
        effects_result.mechanism_blast_impulse_kpa_ms,
        effects_result.mechanism_blast_scaled_distance_m_kg13,
        effects_result.mechanism_rod_cut_margin,
        effects_result.warhead_spatial_sample_count,
        effects_result.warhead_spatial_hit_estimate,
        effects_result.warhead_spatial_hit_fraction,
        effects_result.warhead_spatial_energy_scale,
        effects_result.warhead_spatial_pattern_scale,
        effects_result.warhead_orientation_axis_forward,
        effects_result.warhead_orientation_axis_right,
        effects_result.warhead_orientation_axis_up,
        effects_result.warhead_orientation_pattern_scale,
        effects_result.component_threshold_scale,
        effects_result.component_failure_probability,
        effects_result.component_failure_probability_source,
        effects_result.component_failure_probability_calibrated,
        effects_result.component_failure_probability_evidence_dataset_ref,
        effects_result.component_failure_probability_evidence_row_id,
        effects_result.component_failure_probability_evidence_source_ref,
        effects_result.component_failure_probability_evidence_provenance,
        effects_result.component_failure_sample,
        effects_result.component_failure_count,
        effects_result.component_hit_count,
        effects_result.component_mechanism_load_rows,
        effects_result.component_primary_name,
        effects_result.component_primary_system,
        effects_result.component_primary_redundancy_group,
        effects_result.component_primary_critical,
        effects_result.component_primary_redundancy_group_id,
        effects_result.component_primary_integrity,
        effects_result.component_primary_mechanism_fragment_energy_j,
        effects_result.component_primary_mechanism_fragment_areal_density_per_m2,
        effects_result.component_primary_mechanism_penetration_margin,
        effects_result.component_primary_mechanism_blast_overpressure_kpa,
        effects_result.component_primary_mechanism_blast_impulse_kpa_ms,
        effects_result.component_primary_mechanism_blast_scaled_distance_m_kg13,
        effects_result.component_primary_mechanism_rod_cut_margin,
        effects_result.component_redundancy_group_availability,
        effects_result.component_redundancy_group_member_count,
        effects_result.component_redundancy_group_failed_count,
        effects_result.vulnerability_profile_present,
        effects_result.vulnerability_profile_synthetic,
        effects_result.vulnerability_calibrated_evidence,
        effects_result.vulnerability_pk_authority,
        effects_result.vulnerability_deterministic_fuze_authority,
        effects_result.vulnerability_evidence_dataset_valid,
        effects_result.vulnerability_evidence_dataset_ref,
        effects_result.vulnerability_calibration_status,
        effects_result.vulnerability_provenance,
        effects_result.vulnerability_evidence_schema_version,
        effects_result.vulnerability_evidence_source_kind,
        effects_result.vulnerability_evidence_source_ref,
        effects_result.vulnerability_evidence_validation_artifact_ref,
        effects_result.vulnerability_evidence_validation_manifest_schema_version,
        effects_result.vulnerability_evidence_validation_status,
        effects_result.vulnerability_evidence_validation_artifact_sha256,
        effects_result.vulnerability_evidence_validated_surrogate_model_ref,
        effects_result.vulnerability_evidence_validation_benchmark_ref,
        effects_result.vulnerability_evidence_validation_metrics_ref,
        effects_result.vulnerability_evidence_validation_acceptance_criteria_ref,
        effects_result.vulnerability_aspect_bucket,
        effects_result.vulnerability_family_scale,
        effects_result.vulnerability_aspect_scale,
        effects_result.vulnerability_closure_mps,
        effects_result.vulnerability_closure_scale,
        effects_result.vulnerability_miss_distance_scale,
        effects_result.vulnerability_effect_scale,
        effects_result.vulnerability_effect_scale_source,
        effects_result.vulnerability_effect_scale_evidence_row_id,
        effects_result.vulnerability_effect_scale_evidence_source_ref,
        effects_result.vulnerability_effect_scale_evidence_provenance,
        effects_result.mechanism_surface_incidence_cos,
        effects_result.component_primary_mechanism_surface_incidence_cos);
    impact.destruct();
    return true;
}

bool SimulationKernel::debug_apply_profiled_local_proximity_hit(
    uint64_t attacker_id,
    uint64_t target_id,
    double local_forward_m,
    double local_right_m,
    double local_up_m,
    const WarheadProfile& warhead_profile
) {
    return debug_apply_profiled_local_proximity_hit_with_velocity(
        attacker_id,
        target_id,
        local_forward_m,
        local_right_m,
        local_up_m,
        warhead_profile,
        0.0,
        0.0,
        0.0);
}

bool SimulationKernel::debug_apply_profiled_local_proximity_hit_with_velocity(
    uint64_t attacker_id,
    uint64_t target_id,
    double local_forward_m,
    double local_right_m,
    double local_up_m,
    const WarheadProfile& warhead_profile,
    double missile_vx_mps,
    double missile_vy_mps,
    double missile_vz_mps
) {
    const auto target = ecs.entity(target_id);
    const Transform* target_transform = target.is_valid() ? target.get<Transform>() : nullptr;
    return debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude(
        attacker_id,
        target_id,
        local_forward_m,
        local_right_m,
        local_up_m,
        warhead_profile,
        missile_vx_mps,
        missile_vy_mps,
        missile_vz_mps,
        target_transform ? target_transform->heading : 0.0,
        target_transform ? target_transform->pitch : 0.0,
        target_transform ? target_transform->roll : 0.0);
}

bool SimulationKernel::debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude(
    uint64_t attacker_id,
    uint64_t target_id,
    double local_forward_m,
    double local_right_m,
    double local_up_m,
    const WarheadProfile& warhead_profile,
    double missile_vx_mps,
    double missile_vy_mps,
    double missile_vz_mps,
    double detonation_heading_deg,
    double detonation_pitch_deg,
    double detonation_roll_deg
) {
    auto attacker = ecs.entity(attacker_id);
    auto target = ecs.entity(target_id);
    if (!attacker.is_valid() || !target.is_valid()) {
        return false;
    }

    const Transform* target_transform = target.get<Transform>();
    if (!target_transform) {
        return false;
    }

    const EffectsModelRef* effects_ref = ecs.get<EffectsModelRef>();
    if (!effects_ref || !effects_ref->model) {
        return false;
    }

    const double damage = std::isfinite(warhead_profile.damage_scalar)
        ? warhead_profile.damage_scalar
        : 180.0;
    const double fuse_distance = std::isfinite(warhead_profile.lethal_radius_m)
        ? warhead_profile.lethal_radius_m
        : 80.0;
    WarheadProfile resolved_profile = warhead_profile;
    if (!std::isfinite(resolved_profile.damage_scalar)) {
        resolved_profile.damage_scalar = damage;
        resolved_profile.damage_scalar_synthetic = true;
    }
    if (!std::isfinite(resolved_profile.lethal_radius_m)) {
        resolved_profile.lethal_radius_m = fuse_distance;
    }

    const EngagementDamageStateSnapshot before = engagement_event_store_->capture_engagement_damage_state(target_id);

    Missile synthetic{};
    synthetic.attacker_id = attacker_id;
    synthetic.target_id = target_id;
    synthetic.max_speed = 900.0;
    synthetic.turn_rate = 20.0;
    synthetic.fuse_distance = fuse_distance;
    synthetic.damage = damage;
    synthetic.seeker_fov_deg = 120.0;
    synthetic.seeker_lock_range = 10000.0;
    synthetic.guidance_delay_s = 0.0;
    synthetic.guidance_update_period_s = 0.0;
    synthetic.last_guidance_time = -1.0;
    synthetic.launch_time = 0.0;
    synthetic.max_flight_time_s = 30.0;
    synthetic.nav_gain = 3.0;
    synthetic.active = true;
    synthetic.warhead_profile = resolved_profile;
    synthetic.fuze_profile = make_synthetic_fuze_profile(fuse_distance, "debug_profiled_fuze_distance");
    synthetic.rng_state = 123456789ULL;
    synthetic.proximity_min_dist_m = 0.0;
    synthetic.proximity_last_dist_m = 0.0;
    synthetic.proximity_engaged = true;

    const Transform impact_transform = local_body_point_to_world_transform(
        *target_transform,
        local_forward_m,
        local_right_m,
        local_up_m);
    Transform detonation_transform = impact_transform;
    detonation_transform.heading = detonation_heading_deg;
    detonation_transform.pitch = detonation_pitch_deg;
    detonation_transform.roll = detonation_roll_deg;
    auto impact = ecs.entity()
        .set<Transform>(detonation_transform)
        .set<Velocity>({missile_vx_mps, missile_vy_mps, missile_vz_mps})
        .set<Missile>(synthetic)
        .add<SimObject>();

    const EffectsResult effects_result =
        effects_ref->model->on_proximity_hit(ecs, impact, synthetic, target);
    const EngagementDamageStateSnapshot after = engagement_event_store_->capture_engagement_damage_state(target_id);
    const ecs_world_info_t* info = ecs_get_world_info(ecs.c_ptr());
    const double current_time = info ? static_cast<double>(info->world_time_total) : 0.0;
    const auto detonation_local = world_point_to_local_body(
        *target_transform,
        impact_transform.x,
        impact_transform.y,
        impact_transform.z);
    const auto missile_axis = velocity_axis_in_target_body(
        *target_transform,
        missile_vx_mps,
        missile_vy_mps,
        missile_vz_mps);
    const double closure_mps = resolve_closure_from_impact(
        *target_transform,
        impact_transform,
        target.get<Velocity>(),
        missile_vx_mps,
        missile_vy_mps,
        missile_vz_mps);
    (void)engagement_event_store_->record_effects_damage_event(
        static_cast<uint64_t>(impact.id()),
        target_id,
        before,
        after,
        "debug_profiled_local_proximity_hit",
        "hit",
        current_time,
        current_time,
        local_miss_distance_m(detonation_local[0], detonation_local[1], detonation_local[2]),
        detonation_local[0],
        detonation_local[1],
        detonation_local[2],
        detonation_transform.heading,
        detonation_transform.pitch,
        detonation_transform.roll,
        closure_mps,
        missile_axis[0],
        missile_axis[1],
        missile_axis[2],
        1.0,
        1.0,
        warhead_effect_family(synthetic.warhead_profile),
        std::isfinite(synthetic.warhead_profile.mass_kg)
            ? synthetic.warhead_profile.mass_kg
            : 0.0,
        std::isfinite(synthetic.warhead_profile.lethal_radius_m)
            ? synthetic.warhead_profile.lethal_radius_m
            : fuse_distance,
        synthetic.warhead_profile.synthetic,
        synthetic.warhead_profile.damage_scalar_synthetic,
        fuze_profile_type(synthetic.fuze_profile),
        synthetic.fuze_profile.trigger_radius_m,
        synthetic.fuze_profile.delay_s,
        synthetic.fuze_profile.reliability,
        synthetic.fuze_profile.synthetic,
        "debug",
        0.0,
        1.0,
        synthetic.fuze_profile.reliability,
        0.0,
        0.0,
        0.0,
        false,
        effects_result.direct_hitbox_intersection,
        effects_result.projected_hitbox_count,
        effects_result.spatial_effect_scale,
        effects_result.mechanism_armor_scale,
        effects_result.mechanism_exposure_scale,
        effects_result.mechanism_effect_scale,
        effects_result.mechanism_fragment_energy_j,
        effects_result.mechanism_fragment_areal_density_per_m2,
        effects_result.mechanism_penetration_margin,
        effects_result.mechanism_blast_overpressure_kpa,
        effects_result.mechanism_blast_impulse_kpa_ms,
        effects_result.mechanism_blast_scaled_distance_m_kg13,
        effects_result.mechanism_rod_cut_margin,
        effects_result.warhead_spatial_sample_count,
        effects_result.warhead_spatial_hit_estimate,
        effects_result.warhead_spatial_hit_fraction,
        effects_result.warhead_spatial_energy_scale,
        effects_result.warhead_spatial_pattern_scale,
        effects_result.warhead_orientation_axis_forward,
        effects_result.warhead_orientation_axis_right,
        effects_result.warhead_orientation_axis_up,
        effects_result.warhead_orientation_pattern_scale,
        effects_result.component_threshold_scale,
        effects_result.component_failure_probability,
        effects_result.component_failure_probability_source,
        effects_result.component_failure_probability_calibrated,
        effects_result.component_failure_probability_evidence_dataset_ref,
        effects_result.component_failure_probability_evidence_row_id,
        effects_result.component_failure_probability_evidence_source_ref,
        effects_result.component_failure_probability_evidence_provenance,
        effects_result.component_failure_sample,
        effects_result.component_failure_count,
        effects_result.component_hit_count,
        effects_result.component_mechanism_load_rows,
        effects_result.component_primary_name,
        effects_result.component_primary_system,
        effects_result.component_primary_redundancy_group,
        effects_result.component_primary_critical,
        effects_result.component_primary_redundancy_group_id,
        effects_result.component_primary_integrity,
        effects_result.component_primary_mechanism_fragment_energy_j,
        effects_result.component_primary_mechanism_fragment_areal_density_per_m2,
        effects_result.component_primary_mechanism_penetration_margin,
        effects_result.component_primary_mechanism_blast_overpressure_kpa,
        effects_result.component_primary_mechanism_blast_impulse_kpa_ms,
        effects_result.component_primary_mechanism_blast_scaled_distance_m_kg13,
        effects_result.component_primary_mechanism_rod_cut_margin,
        effects_result.component_redundancy_group_availability,
        effects_result.component_redundancy_group_member_count,
        effects_result.component_redundancy_group_failed_count,
        effects_result.vulnerability_profile_present,
        effects_result.vulnerability_profile_synthetic,
        effects_result.vulnerability_calibrated_evidence,
        effects_result.vulnerability_pk_authority,
        effects_result.vulnerability_deterministic_fuze_authority,
        effects_result.vulnerability_evidence_dataset_valid,
        effects_result.vulnerability_evidence_dataset_ref,
        effects_result.vulnerability_calibration_status,
        effects_result.vulnerability_provenance,
        effects_result.vulnerability_evidence_schema_version,
        effects_result.vulnerability_evidence_source_kind,
        effects_result.vulnerability_evidence_source_ref,
        effects_result.vulnerability_evidence_validation_artifact_ref,
        effects_result.vulnerability_evidence_validation_manifest_schema_version,
        effects_result.vulnerability_evidence_validation_status,
        effects_result.vulnerability_evidence_validation_artifact_sha256,
        effects_result.vulnerability_evidence_validated_surrogate_model_ref,
        effects_result.vulnerability_evidence_validation_benchmark_ref,
        effects_result.vulnerability_evidence_validation_metrics_ref,
        effects_result.vulnerability_evidence_validation_acceptance_criteria_ref,
        effects_result.vulnerability_aspect_bucket,
        effects_result.vulnerability_family_scale,
        effects_result.vulnerability_aspect_scale,
        effects_result.vulnerability_closure_mps,
        effects_result.vulnerability_closure_scale,
        effects_result.vulnerability_miss_distance_scale,
        effects_result.vulnerability_effect_scale,
        effects_result.vulnerability_effect_scale_source,
        effects_result.vulnerability_effect_scale_evidence_row_id,
        effects_result.vulnerability_effect_scale_evidence_source_ref,
        effects_result.vulnerability_effect_scale_evidence_provenance,
        effects_result.mechanism_surface_incidence_cos,
        effects_result.component_primary_mechanism_surface_incidence_cos);
    impact.destruct();
    return true;
}
