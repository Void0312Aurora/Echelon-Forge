// Private fragment for default_effects_model.cpp.
// Included inside that file's anonymous namespace; not a standalone API.

void clamp_platform_damage_state(PlatformDamageState* state) {
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

bool finalize_default_effects_platform_damage(
    flecs::entity target_entity,
    PlatformDamageState* platform_damage,
    Health* hp
) {
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

#include "models/air/default_effects_air_domain.h"
#include "models/naval/default_effects_naval_domain.h"
#include "models/ground/default_effects_ground_domain.h"

enum class DefaultEffectsTargetDomain {
    CommonLegacy,
    Air,
    NavalPlaceholder,
    GroundPlaceholder,
};

struct DefaultEffectsDomainTargetSelection {
    DefaultEffectsTargetDomain domain = DefaultEffectsTargetDomain::CommonLegacy;
    bool structured_damage_target = false;
    AircraftDamageState* aircraft_damage = nullptr;
    const AircraftVulnerabilityProfile* aircraft_vulnerability = nullptr;
};

DefaultEffectsDomainTargetSelection route_default_effects_target_domain(
    flecs::entity target_entity
) {
    const DefaultEffectsAirDomainTargetSelection air_target =
        select_default_effects_air_domain_target(target_entity);
    if (air_target.structured_damage_target) {
        return DefaultEffectsDomainTargetSelection{
            .domain = DefaultEffectsTargetDomain::Air,
            .structured_damage_target = true,
            .aircraft_damage = air_target.aircraft_damage,
            .aircraft_vulnerability = air_target.aircraft_vulnerability,
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
    const DefaultEffectsDomainTargetSelection& domain_target,
    DefaultEffectsScratch& scratch,
    flecs::entity target_entity,
    const Missile& missile,
    const Vec3& local_imp,
    double closure_mps,
    double severity,
    const WarheadEffectProfile& warhead_effects,
    PlatformDamageState* platform_damage,
    ComponentDamageState* component_damage,
    Health* hp
) {
    switch (domain_target.domain) {
        case DefaultEffectsTargetDomain::Air:
            return resolve_default_effects_air_domain_consequences(
                scratch,
                target_entity,
                missile,
                domain_target.structured_damage_target,
                domain_target.aircraft_vulnerability,
                local_imp,
                closure_mps,
                severity,
                warhead_effects,
                platform_damage,
                domain_target.aircraft_damage,
                component_damage,
                hp);
        case DefaultEffectsTargetDomain::NavalPlaceholder:
            return naval::effects::resolve_default_effects_naval_placeholder_consequences(
                target_entity,
                platform_damage,
                hp);
        case DefaultEffectsTargetDomain::GroundPlaceholder:
            return ground::effects::resolve_default_effects_ground_placeholder_consequences(
                target_entity,
                platform_damage,
                hp);
        case DefaultEffectsTargetDomain::CommonLegacy:
        default:
            return finalize_default_effects_platform_damage(
                target_entity,
                platform_damage,
                hp);
    }
}
