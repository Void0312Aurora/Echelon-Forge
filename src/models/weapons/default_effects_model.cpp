#include "core/interfaces/effects_model.h"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cmath>
#include <cstdio>
#include <limits>
#include <string>
#include <unordered_set>
#include <vector>
#include <spdlog/spdlog.h>

#include "components/combat/health.h"
#include "components/physics/performance.h"
#include "components/combat/scoring.h"
#include "components/systems/sensor.h"
#include "components/domains/air/combat/damage_air.h"
#include "components/combat/common/damage_common.h"
#include "components/combat/common/weapon_common.h"
#include "components/physics/dynamics.h"
#include "components/basic/common.h"

namespace {

// Private implementation fragments included inside this translation unit to
// keep helper linkage local while making the default effects model navigable.
#include "models/weapons/detail/default_effects_geometry_detail.inc"
#include "models/weapons/detail/default_effects_component_damage_detail.inc"
#include "models/weapons/detail/default_effects_warhead_detail.inc"
#include "models/weapons/detail/default_effects_state_detail.inc"
#include "models/weapons/detail/default_effects_system_effect_detail.inc"
#include "models/weapons/detail/default_effects_direct_hit_detail.inc"
#include "models/weapons/detail/default_effects_spatial_projection_detail.inc"
#include "models/weapons/detail/default_effects_result_detail.inc"
#include "models/weapons/detail/default_effects_legacy_detail.inc"
#include "models/weapons/detail/default_effects_domain_routing_detail.inc"

class DefaultEffectsModel : public IEffectsModel {
  public:
    EffectsResult on_proximity_hit(flecs::world world, flecs::entity missile_entity,
                                   const Missile &missile, flecs::entity target_entity) override {
        EffectsResult result;

        Score *score = nullptr;
        auto attacker = world.entity(missile.attacker_id);
        if (attacker.is_valid()) {
            score = attacker.get_mut<Score>();
        }

        const DefaultEffectsDomainTargetSelection domain_target =
            route_default_effects_target_domain(target_entity);
        const bool structured_air_target = domain_target.structured_damage_target;

        Health *hp = target_entity.get_mut<Health>();
        if (hp && !structured_air_target &&
            apply_legacy_health_damage(target_entity, missile, score, *hp)) {
            return result;
        }

        // --- 2. Geometric Damage Logic (New) ---
        const HitboxConfig *hitboxes = target_entity.get<HitboxConfig>();
        SystemHealth *sys_health = target_entity.get_mut<SystemHealth>();
        PlatformDamageState *platform_damage = target_entity.get_mut<PlatformDamageState>();
        AircraftDamageState *aircraft_damage = domain_target.aircraft_damage;
        ComponentDamageState *component_damage = target_entity.get_mut<ComponentDamageState>();
        const AircraftVulnerabilityProfile *aircraft_vulnerability =
            domain_target.aircraft_vulnerability;
        const Transform *t_tgt = target_entity.get<Transform>();
        const Transform *t_msl = missile_entity.get<Transform>();

        if (hitboxes && sys_health && t_tgt && t_msl) {
            // Transform Missile Pos to Target Body Frame
            Vec3 local_imp = world_to_body(*t_tgt, t_msl->x, t_msl->y, t_msl->z);
            const double closure_mps = resolve_closure_mps(missile_entity, target_entity);
            const Vec3 missile_axis_body =
                missile_velocity_axis_in_target_body(missile_entity, *t_tgt);
            const Vec3 warhead_orientation_axis_body =
                missile_forward_axis_in_target_body(*t_msl, *t_tgt);

            DefaultEffectsScratch scratch{missile.rng_state};
            const double severity = std::clamp(missile.damage / 180.0, 0.15, 0.65);
            const WarheadEffectProfile warhead_effects =
                structured_air_target ? make_warhead_effect_profile(missile.warhead_profile)
                                      : WarheadEffectProfile{};
            const WarheadSpatialProjectionProfile warhead_projection =
                structured_air_target
                    ? make_warhead_spatial_projection_profile(missile.warhead_profile)
                    : WarheadSpatialProjectionProfile{};
            const double base_system_severity =
                structured_air_target
                    ? std::clamp(severity * warhead_effects.system_damage_scale, 0.05, 0.95)
                    : severity;
            DefaultEffectsSystemSeverityContext system_severity_context{
                .structured_air_target = structured_air_target,
                .missile = missile,
                .aircraft_vulnerability = aircraft_vulnerability,
                .local_imp = local_imp,
                .closure_mps = closure_mps,
                .base_system_severity = base_system_severity,
            };
            DefaultEffectsSystemSeverityResolver resolve_system_severity{system_severity_context};
            DefaultEffectsSystemEffectContext system_effect_context{
                .scratch = scratch,
                .target_entity = target_entity,
                .structured_air_target = structured_air_target,
                .missile = missile,
                .aircraft_vulnerability = aircraft_vulnerability,
                .component_damage = component_damage,
                .aircraft_damage = aircraft_damage,
                .platform_damage = platform_damage,
                .sys_health = *sys_health,
                .local_imp = local_imp,
                .closure_mps = closure_mps,
                .severity = severity,
            };
            DefaultEffectsSystemEffectApplicator apply_system_effect{system_effect_context};
            const auto populate_result = [&]() {
                populate_default_effects_result(result, scratch, warhead_orientation_axis_body);
            };
            apply_default_effects_direct_hitboxes(scratch, *hitboxes, structured_air_target,
                                                  missile, local_imp, warhead_orientation_axis_body,
                                                  missile_axis_body, closure_mps, sys_health,
                                                  resolve_system_severity, apply_system_effect);
            apply_default_effects_spatial_projection(
                scratch, *hitboxes, structured_air_target, missile, warhead_projection, local_imp,
                missile_axis_body, warhead_orientation_axis_body, closure_mps, sys_health,
                resolve_system_severity, apply_system_effect);
            if (resolve_default_effects_domain_platform_consequences(
                    domain_target, scratch, target_entity, missile, local_imp, closure_mps,
                    severity, warhead_effects, platform_damage, component_damage, hp)) {
                populate_result();
                return result;
            }
            if (!scratch.structure_hit) {
                spdlog::info("PROXIMITY HIT BUT NO STRUCTURAL IMPACT (Near Miss or Gap)");
            }
            populate_result();
        }
        // --- 3. Fallback to Randomized Effects (Legacy) ---
        else {
            apply_legacy_randomized_fallback_effects(missile_entity, target_entity, missile, hp);
        }

        return result;
    }
};

} // namespace

std::unique_ptr<IEffectsModel> make_default_effects_model() {
    return std::make_unique<DefaultEffectsModel>();
}
