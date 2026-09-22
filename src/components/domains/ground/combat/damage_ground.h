#pragma once

#include <algorithm>

#include "components/combat/common/damage_common.h"

// Ground-domain damage ownership boundary (DM-G1).
//
// The component layer defines data contracts only (architecture law 3): this
// header declares typed ground damage state and the pure helpers that keep it
// in range. It declares no per-tick behavior and registers no ECS system.
//
// Ownership split for ground damage:
// - `GroundPlatformDamageState` (here) is the ground-owned response state:
//   running-gear/track mobility, deck or hull fire load, structural integrity,
//   and the casualty pool that is no longer available to the ground element.
// - `PlatformDamageState` (components/combat/common/damage_common.h) stays the
//   shared capability projection: mission, mobility, sensor, survivability,
//   and `PlatformLossState`.
// - `src/systems/domains/ground/damage_system_ground.h` advances this state per tick
//   and projects it through `sync_platform_damage_loss_state`.
// - `src/models/domains/ground/default_effects_ground_domain.h` applies
//   warhead mechanism load into this state for a structured ground target.
//
// Explicit non-claims: this state is a consequence ledger, not a movement,
// sensing, fires, or terrain authority. Nothing here drives ground translation,
// route following, line of sight, or weapon release.
struct GroundPlatformDamageState {
    // Running gear, suspension, track band, and final drive. 1.0 = fully
    // mobile, 0.0 = no self-propulsion available.
    double mobility_integrity = 1.0;
    // Track band specifically separated from the rest of the running gear so a
    // thrown track degrades mobility without implying drive-train loss.
    double track_integrity = 1.0;
    // Internal fire load. Ground elements cannot pump or flood, so fire is the
    // dominant progressive casualty and is decayed by damage_system_ground.
    double fire_severity = 0.0;
    // Ignition sources feeding the fire load (fuel, ammunition, engine deck).
    double ignition_source_severity = 0.0;
    // Fire-fighting and damage-control availability for the element.
    double fire_suppression_integrity = 1.0;
    // Chassis, hull, and weapon-mount structural integrity.
    double structural_integrity = 1.0;
    // Progressive structural loss that keeps converting into capability loss
    // until it is contained.
    double ongoing_structural_damage = 0.0;
    // Casualties already taken as a fraction of the element's strength.
    double casualty_fraction = 0.0;
    // Communications and command availability for the element. Sensor
    // capability stays in the shared platform state.
    double command_integrity = 1.0;
    // Health-authoritative flags. They mirror the shared `Health` kill flags
    // and are only used as the ground-domain projection of that same truth.
    bool mobility_kill = false;
    bool mission_kill = false;
    bool element_destroyed = false;
};

inline void clamp_ground_platform_damage_state(GroundPlatformDamageState &state) {
    state.mobility_integrity = std::clamp(state.mobility_integrity, 0.0, 1.0);
    state.track_integrity = std::clamp(state.track_integrity, 0.0, 1.0);
    state.fire_severity = std::clamp(state.fire_severity, 0.0, 1.0);
    state.ignition_source_severity = std::clamp(state.ignition_source_severity, 0.0, 1.0);
    state.fire_suppression_integrity = std::clamp(state.fire_suppression_integrity, 0.0, 1.0);
    state.structural_integrity = std::clamp(state.structural_integrity, 0.0, 1.0);
    state.ongoing_structural_damage = std::clamp(state.ongoing_structural_damage, 0.0, 1.0);
    state.casualty_fraction = std::clamp(state.casualty_fraction, 0.0, 1.0);
    state.command_integrity = std::clamp(state.command_integrity, 0.0, 1.0);
}

// Effective ground mobility availability, derived from the ground-owned state
// only. This is a read-only projection used by the domain system and by the
// effects path; it is not a movement authority.
[[nodiscard]] inline double
ground_mobility_availability(const GroundPlatformDamageState &state) noexcept {
    return std::clamp(state.mobility_integrity * state.track_integrity, 0.0, 1.0);
}

// DS-C1-A ground-owned damage owner shell. It stayed `true` when the typed
// state above landed, because it marks the ownership boundary rather than the
// presence or absence of a data contract: `components/domains/ground/combat/`
// keeps owning ground damage state instead of hiding it in a generic combat
// header.
inline constexpr bool kGroundDomainDamageOwnerShell = true;
