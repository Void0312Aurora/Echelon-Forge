// Maintained ground-owned default effects helper surface for default_effects_model.cpp.
// Included through the common effects router; not a standalone model entry point.

#pragma once

#include "components/domains/ground/combat/damage_ground.h"

// Ground-domain warhead consequence application (DM-G1).
//
// Layer boundary: this file lives in `models/` and therefore applies
// consequences only. It never registers ECS systems and never calls into the
// systems layer. The loss projection runs inside the shared model-side
// `finalize_default_effects_platform_damage` helper below, and the maintained
// per-tick loss projector `sync_platform_damage_loss_state` is called by
// `systems/domains/ground/damage_system_ground.h`, which is where it belongs.
//
// The air domain is the working reference for a structured per-domain effects
// mechanism, but ground does not share air's sub-system inventory: there is no
// propulsion/crew/fire-zone decomposition here, and the ground state is a
// chassis/mobility/fire/structural ledger. This file therefore mirrors the air
// shape (explicit target selection -> mechanism load -> per-domain consequence
// blocks -> projection -> shared finalize) without copying air semantics.

namespace ground::effects {

// Spatial reach of the warhead against a ground chassis, per mechanism.
struct DefaultEffectsGroundSpatialScales {
    double structure = 0.0;
    double blast = 0.0;
    double mobility = 0.0;
    double fragmentation = 0.0;
    double fire = 0.0;
    double suppression = 0.0;
};

struct DefaultEffectsGroundDomainTargetSelection {
    bool structured_damage_target = false;
    GroundPlatformDamageState *ground_damage = nullptr;
};

// A ground target is a structured ground damage target only when it carries the
// ground-owned damage state on top of the full shared damage-model surface. The
// predicate is intentionally strict: anything less stays on the placeholder
// route, so the router keeps the fallback honest.
inline bool is_structured_ground_damage_target(flecs::entity target_entity,
                                               flecs::id_t ground_damage_component) {
    const KeyEntity *key = target_entity.get<KeyEntity>();
    const bool ground_keyed = key != nullptr && key->type == UnitType::Ground;
    if (ground_keyed) {
        // Reachability diagnostic. This is the measurement that localized the
        // DM-G1 residual: a ground-keyed target reached the ground selection with
        // the shared surface present (`hitbox`/`sys`/`platform` all 1) but with
        // `state=0`, because this translation unit resolved
        // `GroundPlatformDamageState` to a duplicate component id and addressed a
        // different component than the spawn path wrote. The state is now read
        // through the id the composition path resolved, so `state` reports the
        // spawn path's component. Kept at warn level because `spdlog::debug` is
        // filtered by this kernel's logger and a debug-level probe cannot
        // distinguish "never reached" from "ran and returned false".
        spdlog::warn("GROUND SELECT entity={} key_type={} state={} hitbox={} sys={} platform={}",
                     static_cast<uint64_t>(target_entity.id()), static_cast<int>(key->type),
                     target_entity.has(ground_damage_component) ? 1 : 0,
                     target_entity.get<HitboxConfig>() != nullptr ? 1 : 0,
                     target_entity.get<SystemHealth>() != nullptr ? 1 : 0,
                     target_entity.get<PlatformDamageState>() != nullptr ? 1 : 0);
    }
    if (!target_entity.has(ground_damage_component)) {
        return false;
    }
    if (target_entity.get<HitboxConfig>() == nullptr ||
        target_entity.get<SystemHealth>() == nullptr ||
        target_entity.get<PlatformDamageState>() == nullptr) {
        return false;
    }
    return ground_keyed;
}

inline DefaultEffectsGroundDomainTargetSelection
select_default_effects_ground_domain_target(flecs::entity target_entity,
                                            flecs::id_t ground_damage_component) {
    // `get_mut` has no untyped overload: every typed form resolves the component id from
    // the type inside flecs, which is the resolution this repair removes. The C accessor
    // takes the id the composition path resolved instead, and the cast is the same one
    // flecs's own typed wrapper performs.
    return DefaultEffectsGroundDomainTargetSelection{
        .structured_damage_target =
            is_structured_ground_damage_target(target_entity, ground_damage_component),
        .ground_damage = static_cast<GroundPlatformDamageState *>(ecs_get_mut_id(
            target_entity.world().c_ptr(), target_entity.id(), ground_damage_component)),
    };
}

inline bool check_ground_damage_hitbox(const Vec3 &local_imp, const Hitbox &box) {
    return check_hitbox(local_imp, box);
}

// Direct structural contact against any chassis hitbox. This is the ground
// analogue of the air domain's `structure_hit` scratch flag, which is only ever
// set through the air-only component path.
inline bool resolve_default_effects_ground_direct_structure_hit(const HitboxConfig &hitboxes,
                                                                const Vec3 &local_imp) {
    for (const Hitbox &box : hitboxes.hitboxes) {
        if (check_ground_damage_hitbox(local_imp, box)) {
            return true;
        }
    }
    return false;
}

inline DefaultEffectsGroundSpatialScales
make_default_effects_ground_spatial_scales(const DefaultEffectsScratch &scratch,
                                           bool direct_structure_hit) {
    const auto hit_scale = [](bool hit, double scale) {
        return hit ? std::clamp(scale, 0.05, 1.0) : 0.0;
    };
    const auto mechanism_scale = [&scratch, &hit_scale](bool hit) {
        return hit_scale(hit,
                         std::max(scratch.spatial_effect_scale, scratch.sampled_mechanism_scale));
    };
    return DefaultEffectsGroundSpatialScales{
        .structure = hit_scale(direct_structure_hit, scratch.spatial_effect_scale),
        .blast = mechanism_scale(scratch.sampled_mechanism_blast_overpressure_kpa > 0.0 ||
                                 scratch.sampled_mechanism_blast_impulse_kpa_ms > 0.0),
        .mobility = mechanism_scale(scratch.sampled_mechanism_blast_impulse_kpa_ms > 0.0 ||
                                    scratch.sampled_mechanism_penetration_margin > 0.0),
        .fragmentation = mechanism_scale(scratch.sampled_mechanism_fragment_energy_j > 0.0),
        .fire =
            mechanism_scale(direct_structure_hit || scratch.spatial_projection_effect_scale > 0.0),
        .suppression = hit_scale(direct_structure_hit, scratch.sampled_exposure_scale),
    };
}

void apply_default_effects_ground_platform_consequence_blocks(
    const DefaultEffectsGroundSpatialScales &scales, double resolved_severity,
    const WarheadEffectProfile &warhead_effects, PlatformDamageState &platform_damage) {
    // Mobile ground elements lose the shared mobility projection at a higher
    // rate than air or naval platforms: there is no altitude or buoyancy
    // reserve to fall back on once the running gear is gone.
    platform_damage.mobility_capability -=
        localized_effect_delta(0.16, 0.18, resolved_severity, warhead_effects.control_scale,
                               std::max(scales.mobility, scales.blast));
    platform_damage.mission_capability -= localized_effect_delta(
        0.10, 0.12, resolved_severity, warhead_effects.mission_scale, scales.suppression);
    platform_damage.survivability_margin -= localized_effect_delta(
        0.08, 0.08, resolved_severity, warhead_effects.structure_scale, scales.structure);
    platform_damage.fire_severity = std::clamp(
        platform_damage.fire_severity +
            localized_effect_delta(0.06, 0.08, resolved_severity, warhead_effects.fire_scale,
                                   std::max(scales.fire, scales.structure)),
        0.0, 1.0);
    platform_damage.sensor_capability -= localized_effect_delta(
        0.06, 0.06, resolved_severity, warhead_effects.sensor_scale, scales.suppression);
    platform_damage.flooding_severity = std::clamp(platform_damage.flooding_severity, 0.0, 1.0);
    platform_damage.ongoing_hull_breach = std::clamp(platform_damage.ongoing_hull_breach, 0.0, 1.0);
}

void apply_default_effects_ground_chassis_consequence_blocks(
    const DefaultEffectsGroundSpatialScales &scales, double resolved_severity,
    const WarheadEffectProfile &warhead_effects, GroundPlatformDamageState &ground_damage) {
    ground_damage.structural_integrity -= localized_effect_delta(
        0.07, 0.09, resolved_severity, warhead_effects.structure_scale, scales.structure);
    ground_damage.command_integrity -= localized_effect_delta(
        0.06, 0.07, resolved_severity, warhead_effects.mission_scale, scales.suppression);
    if (scales.blast > 0.0) {
        ground_damage.mobility_integrity -= localized_effect_delta(
            0.12, 0.16, resolved_severity, warhead_effects.control_scale, scales.blast);
        ground_damage.structural_integrity -= localized_effect_delta(
            0.05, 0.07, resolved_severity, warhead_effects.structure_scale, scales.blast);
    }
    if (scales.mobility > 0.0) {
        ground_damage.track_integrity -= localized_effect_delta(
            0.16, 0.20, resolved_severity, warhead_effects.control_scale, scales.mobility);
        ground_damage.mobility_integrity -= localized_effect_delta(
            0.08, 0.12, resolved_severity, warhead_effects.control_scale, scales.mobility);
    }
    if (scales.fragmentation > 0.0) {
        ground_damage.casualty_fraction += localized_effect_delta(
            0.05, 0.08, resolved_severity, warhead_effects.crew_scale, scales.fragmentation);
        ground_damage.command_integrity -= localized_effect_delta(
            0.04, 0.05, resolved_severity, warhead_effects.mission_scale, scales.fragmentation);
    }
    if (scales.fire > 0.0) {
        ground_damage.ignition_source_severity += localized_effect_delta(
            0.06, 0.10, resolved_severity, warhead_effects.fire_scale, scales.fire);
        ground_damage.fire_severity += localized_effect_delta(
            0.08, 0.12, resolved_severity, warhead_effects.fire_scale, scales.fire);
    }
    ground_damage.fire_suppression_integrity -= localized_effect_delta(
        0.05, 0.06, resolved_severity, warhead_effects.breach_scale, scales.fire);
    clamp_ground_platform_damage_state(ground_damage);
}

// Ground-owned projection: the ground state is the authority for the ground
// response, and this is where its damage becomes shared capability. It writes
// capability only; the loss projection itself stays with the shared finalize,
// so ground does not fork loss semantics and `models/` keeps its layer.
void project_ground_damage_state_to_platform(const GroundPlatformDamageState &ground_damage,
                                             PlatformDamageState &platform_damage) {
    platform_damage.mobility_capability =
        std::min(platform_damage.mobility_capability, ground_mobility_availability(ground_damage));
    platform_damage.mission_capability = std::clamp(
        platform_damage.mission_capability - 0.05 * (1.0 - ground_damage.command_integrity) -
            0.06 * ground_damage.casualty_fraction,
        0.0, 1.0);
    platform_damage.survivability_margin =
        std::min(platform_damage.survivability_margin, ground_damage.structural_integrity);
    platform_damage.fire_severity =
        std::max(platform_damage.fire_severity, ground_damage.fire_severity);
    platform_damage.ongoing_hull_breach = std::clamp(
        platform_damage.ongoing_hull_breach + ground_damage.ongoing_structural_damage, 0.0, 1.0);
    platform_damage.flooding_severity = std::clamp(platform_damage.flooding_severity, 0.0, 1.0);
}

// Mirrors the shared kill-flag contract onto the ground ledger once the shared
// finalize has resolved the authoritative `PlatformLossState`. It reads the
// projection; it does not re-derive thresholds.
void project_shared_loss_state_onto_ground_state(const PlatformDamageState &platform_damage,
                                                 Health *hp,
                                                 GroundPlatformDamageState &ground_damage) {
    ground_damage.mobility_kill = platform_damage.mobility_kill;
    ground_damage.mission_kill = platform_damage.mission_kill;
    ground_damage.element_destroyed = platform_damage.loss_state == PlatformLossState::Lost ||
                                      (hp != nullptr && hp->current_hp <= 0.0);
}

inline bool resolve_default_effects_ground_domain_consequences(
    DefaultEffectsScratch &scratch, flecs::entity target_entity, const Missile &missile,
    bool structured_ground_target, const HitboxConfig *hitboxes, const Vec3 &local_imp,
    double severity, const WarheadEffectProfile &warhead_effects,
    PlatformDamageState *platform_damage, GroundPlatformDamageState *ground_damage, Health *hp) {
    // Ground has no calibrated vulnerability profile yet, so unlike the air
    // domain this path does not derive a vulnerability adjustment from the
    // missile profile. The warhead mechanism load arrives through `scratch`,
    // which is the same evidence seam the air domain uses.
    (void)missile;

    const bool direct_structure_hit =
        hitboxes != nullptr &&
        resolve_default_effects_ground_direct_structure_hit(*hitboxes, local_imp);

    if (structured_ground_target && ground_damage != nullptr && direct_structure_hit) {
        const WarheadMechanismLoadEvidence mechanism_load =
            resolve_default_effects_vulnerability_mechanism_load(scratch, direct_structure_hit);
        const double resolved_severity =
            std::clamp(severity * std::max(0.05, scratch.spatial_effect_scale) *
                           std::max(0.20, scratch.sampled_mechanism_scale),
                       0.02, 0.65);
        const DefaultEffectsGroundSpatialScales scales =
            make_default_effects_ground_spatial_scales(scratch, direct_structure_hit);
        // Warhead mechanism load first, ground state next, shared projection
        // last. The order is the contract: the ground state is the domain
        // authority and the platform state is its projection.
        apply_default_effects_ground_chassis_consequence_blocks(scales, resolved_severity,
                                                                warhead_effects, *ground_damage);
        if (mechanism_load.surface_incidence_cos > 0.0) {
            ground_damage->structural_integrity -= localized_effect_delta(
                0.03, 0.05, resolved_severity, warhead_effects.structure_scale,
                mechanism_load.surface_incidence_cos);
        }
        if (mechanism_load.rod_cut_margin > 0.0) {
            ground_damage->track_integrity -=
                localized_effect_delta(0.06, 0.09, resolved_severity, warhead_effects.control_scale,
                                       std::max(scales.mobility, scales.structure));
        }
        clamp_ground_platform_damage_state(*ground_damage);

        if (platform_damage != nullptr) {
            apply_default_effects_ground_platform_consequence_blocks(
                scales, resolved_severity, warhead_effects, *platform_damage);
            project_ground_damage_state_to_platform(*ground_damage, *platform_damage);
        }
    }

    const bool destroyed =
        finalize_default_effects_platform_damage(target_entity, platform_damage, hp);
    if (structured_ground_target && ground_damage != nullptr) {
        clamp_ground_platform_damage_state(*ground_damage);
        if (platform_damage != nullptr) {
            project_shared_loss_state_onto_ground_state(*platform_damage, hp, *ground_damage);
        }
    }
    return destroyed;
}

// ---------------------------------------------------------------------------
// Legacy placeholder names.
//
// The DS-M1-A shells below stay defined so the existing routing fragment keeps
// compiling during the transition, but they are no longer the maintained ground
// path: the router selects the structured ground route whenever the target
// satisfies `is_structured_ground_damage_target`, and reaches the placeholder
// only when that selection is unsatisfied.
// ---------------------------------------------------------------------------

inline bool is_default_effects_ground_placeholder_target(flecs::entity target_entity) {
    if (const KeyEntity *key = target_entity.get<KeyEntity>()) {
        return key->type == UnitType::Ground;
    }
    return false;
}

inline bool resolve_default_effects_ground_placeholder_consequences(
    flecs::entity target_entity, PlatformDamageState *platform_damage, Health *hp) {
    return finalize_default_effects_platform_damage(target_entity, platform_damage, hp);
}

} // namespace ground::effects
