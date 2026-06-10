#pragma once

namespace naval::effects {

inline bool is_default_effects_naval_placeholder_target(flecs::entity target_entity) {
    if (const KeyEntity *key = target_entity.get<KeyEntity>()) {
        return key->type == UnitType::Ship || key->type == UnitType::Submarine;
    }
    return false;
}

inline bool resolve_default_effects_naval_placeholder_consequences(
    flecs::entity target_entity, PlatformDamageState *platform_damage, Health *hp) {
    // DS-M1-A ownership shell only: naval routing is explicit here, but the
    // maintained behavior stays finalize-only until naval damage fidelity has
    // its own runtime owner.
    return finalize_default_effects_platform_damage(target_entity, platform_damage, hp);
}

} // namespace naval::effects
