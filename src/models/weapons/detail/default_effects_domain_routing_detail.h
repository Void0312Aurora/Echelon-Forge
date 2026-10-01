// Private fragment for default_effects_model.cpp.
// Included inside that file's anonymous namespace; not a standalone API.

void clamp_platform_damage_state(PlatformDamageState *state) {
    if (!state) return;
    state->mission_capability = std::clamp(state->mission_capability, 0.0, 1.0);
    state->mobility_capability = std::clamp(state->mobility_capability, 0.0, 1.0);
    state->sensor_capability = std::clamp(state->sensor_capability, 0.0, 1.0);
    state->survivability_margin = std::clamp(state->survivability_margin, 0.0, 1.0);

    state->mission_kill = state->mission_capability <= 0.25;
    state->mobility_kill = state->mobility_capability <= 0.25;
    state->sensor_kill = state->sensor_capability <= 0.25;

    if (state->survivability_margin <= 0.0) {
        state->loss_state = PlatformLossState::Lost;
    } else if (state->mobility_kill) {
        state->loss_state = PlatformLossState::MobilityKill;
    } else if (state->sensor_kill) {
        state->loss_state = PlatformLossState::SensorKill;
    } else if (state->mission_kill) {
        state->loss_state = PlatformLossState::MissionKill;
    } else {
        state->loss_state = PlatformLossState::CombatCapable;
    }
}

bool finalize_default_effects_platform_damage(flecs::entity target_entity,
                                              PlatformDamageState *platform_damage, Health *hp) {
    if (!platform_damage) {
        return false;
    }

    clamp_platform_damage_state(platform_damage);
    if (hp) {
        hp->mission_kill = platform_damage->mission_kill;
        hp->mobility_kill = platform_damage->mobility_kill;
        hp->sensor_kill = platform_damage->sensor_kill;
        if (platform_damage->loss_state == PlatformLossState::Lost) {
            hp->current_hp = 0.0;
        }
    }
    if (platform_damage->loss_state == PlatformLossState::Lost) {
        target_entity.destruct();
        return true;
    }
    return false;
}

#include "models/domains/air/default_effects_air_domain.h"
#include "models/domains/naval/default_effects_naval_domain.h"
#include "models/domains/ground/default_effects_ground_domain.h"

enum class DefaultEffectsTargetDomain {
    CommonLegacy,
    Air,
    Ground,
    NavalPlaceholder,
    GroundPlaceholder,
};

struct DefaultEffectsDomainTargetSelection {
    DefaultEffectsTargetDomain domain = DefaultEffectsTargetDomain::CommonLegacy;
    bool structured_damage_target = false;
    bool is_air_target = false;
    AircraftDamageState *aircraft_damage = nullptr;
    const AircraftVulnerabilityProfile *aircraft_vulnerability = nullptr;
    GroundPlatformDamageState *ground_damage = nullptr;
};

DefaultEffectsDomainTargetSelection
route_default_effects_target_domain(flecs::entity target_entity,
                                    flecs::id_t ground_damage_component) {
    const DefaultEffectsAirDomainTargetSelection air_target =
        select_default_effects_air_domain_target(target_entity);
    if (air_target.structured_damage_target) {
        return DefaultEffectsDomainTargetSelection{
            .domain = DefaultEffectsTargetDomain::Air,
            .structured_damage_target = true,
            .is_air_target = true,
            .aircraft_damage = air_target.aircraft_damage,
            .aircraft_vulnerability = air_target.aircraft_vulnerability,
        };
    }
    // Structured ground selection is the maintained ground route, and it gets its
    // own domain value so it is distinguishable from the placeholder fallback
    // below. The GroundPlaceholder domain stays only as the
    // unsatisfied-selection fallback: it is reached when a ground-keyed target is
    // missing the ground-owned damage state or the shared hitbox/health/platform
    // damage surface.
    const ground::effects::DefaultEffectsGroundDomainTargetSelection ground_target =
        ground::effects::select_default_effects_ground_domain_target(target_entity,
                                                                     ground_damage_component);
    if (ground_target.structured_damage_target) {
        // Reachability discriminator, kept at debug level because it is a
        // diagnostic rather than maintained behavior: two distinct defects
        // produce the same observable for a ground hit -- "unit destroyed,
        // all-zero capability vector". Either (a) the structured route ran and
        // the shared platform pipeline destructed at the observed severity, or
        // (b) the ground damage state was absent at routing time and the
        // GroundPlaceholder fallback ran instead. `has_ground_state` separates
        // them, and `state_id` now reports the id this route actually resolved
        // rather than resolving the type a second time to print it. Set
        // `CMO_SIM_LOG_LEVEL=debug` to see it.
        spdlog::debug("GROUND ROUTE entity={} has_ground_state={} state_id={}",
                      static_cast<uint64_t>(target_entity.id()),
                      target_entity.has(ground_damage_component) ? 1 : 0,
                      static_cast<uint64_t>(ground_damage_component));
        return DefaultEffectsDomainTargetSelection{
            .domain = DefaultEffectsTargetDomain::Ground,
            .structured_damage_target = true,
            .ground_damage = ground_target.ground_damage,
        };
    }
    if (naval::effects::is_default_effects_naval_placeholder_target(target_entity)) {
        return DefaultEffectsDomainTargetSelection{
            .domain = DefaultEffectsTargetDomain::NavalPlaceholder,
        };
    }
    if (ground::effects::is_default_effects_ground_placeholder_target(target_entity)) {
        return DefaultEffectsDomainTargetSelection{
            .domain = DefaultEffectsTargetDomain::GroundPlaceholder,
        };
    }
    return DefaultEffectsDomainTargetSelection{};
}

bool resolve_default_effects_domain_platform_consequences(
    const DefaultEffectsDomainTargetSelection &domain_target, DefaultEffectsScratch &scratch,
    flecs::entity target_entity, const Missile &missile, const HitboxConfig *hitboxes,
    const Vec3 &local_imp, double closure_mps, double severity,
    const WarheadEffectProfile &warhead_effects, PlatformDamageState *platform_damage,
    GroundPlatformDamageState *ground_damage, ComponentDamageState *component_damage, Health *hp) {
    switch (domain_target.domain) {
    case DefaultEffectsTargetDomain::Air:
        return resolve_default_effects_air_domain_consequences(
            scratch, target_entity, missile, domain_target.structured_damage_target,
            domain_target.aircraft_vulnerability, local_imp, closure_mps, severity, warhead_effects,
            platform_damage, domain_target.aircraft_damage, component_damage, hp);
    case DefaultEffectsTargetDomain::NavalPlaceholder:
        return naval::effects::resolve_default_effects_naval_placeholder_consequences(
            target_entity, platform_damage, hp);
    case DefaultEffectsTargetDomain::Ground:
        // The model passes the selection-derived ground state, and the router
        // falls back to the domain target's own selection when the caller only
        // has the domain selection. Both resolve to the same component; the
        // ground consequence path is a no-op when neither is present.
        return ground::effects::resolve_default_effects_ground_domain_consequences(
            scratch, target_entity, missile, true, hitboxes, local_imp, severity, warhead_effects,
            platform_damage, ground_damage != nullptr ? ground_damage : domain_target.ground_damage,
            hp);
    case DefaultEffectsTargetDomain::GroundPlaceholder:
        return ground::effects::resolve_default_effects_ground_placeholder_consequences(
            target_entity, platform_damage, hp);
    case DefaultEffectsTargetDomain::CommonLegacy:
    default:
        return finalize_default_effects_platform_damage(target_entity, platform_damage, hp);
    }
}
