#pragma once

// Naval domain damage-response surface (DM-N1).
//
// This header owns naval damage-response *data*: the profile that parameterizes
// how a naval platform's fire / flooding / hull-breach state evolves and how
// that state projects onto shared PlatformDamageState capability fields.
//
// Layer rule: components/ declares data contracts and owns no per-tick behavior
// (architecture law 3). Every function below is a pure, constexpr-style helper
// over its arguments; the tick loop lives in
// `systems/combat/damage_system_naval.h`.
//
// Maturity: this is a damage-response mechanism only. It carries no naval
// weapon-release authority (N5) and no kill/outcome authority (N6). Every
// profile declares `synthetic = true` and `calibrated = false` until a
// validation package exists, and no field here widens launch or kill authority.
//
// Units: all rates are per-second first-order coefficients. Severity channels
// are dimensionless fractions in [0, 1]; capability fields are dimensionless
// fractions in [0, 1]; `*_floor` fields are dimensionless lower clamps.

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

#include "components/combat/common/damage_common.h"

using NavalPlatformDamageState = PlatformDamageState;

[[nodiscard]] inline double
naval_damage_flooding_severity(const NavalPlatformDamageState &state) noexcept {
    return state.flooding_severity;
}

[[nodiscard]] inline double
naval_damage_ongoing_hull_breach(const NavalPlatformDamageState &state) noexcept {
    return state.ongoing_hull_breach;
}

// Declared naval damage-response profile.
//
// Every coefficient that `systems/combat/damage_system_naval.h` previously held
// as an inline literal now lives here. The `naval_damage_response_profile_default()`
// values preserve those coefficients while declaring them in per-second units;
// the runtime applies the elapsed step explicitly rather than treating a tick
// count as a unit of time.
struct NavalDamageResponseProfile {
    // Registry key. The current runtime admits the parity default only; this
    // keeps provenance explicit without pretending that per-class selection is
    // already wired into content.
    std::string ship_class_id = "naval_damage_response_default";

    // --- Fire channel -------------------------------------------------------
    // fire_severity loses fire_decay_per_s * mount_response_scale every second.
    double fire_decay_per_s = 0.0008;

    // --- Hull-breach channel -------------------------------------------------
    // ongoing_hull_breach loses breach_decay_per_s * mount_response_scale every
    // second (a breach is patched or it is not; no autonomous growth term).
    double breach_decay_per_s = 0.0001;

    // --- Flooding channel ----------------------------------------------------
    // flooding_severity gains breach_to_flooding_per_s * breach_progress and
    // loses flooding_decay_per_s * mount_response_scale each second. The two
    // terms are separate so an ingress-only profile can still be expressed.
    double flooding_decay_per_s = 0.0002;
    double breach_to_flooding_per_s = 0.003;

    // --- Severity -> capability loss ----------------------------------------
    // Capability fields lose (<coefficient> * channel_progress *
    // mount_response_scale) per second. The coefficients stay split per channel
    // so a profile can push one failure mode ahead of the others.
    double mission_loss_per_s_at_fire = 0.0015;
    double sensor_loss_per_s_at_fire = 0.0012;
    double mobility_loss_per_s_at_flooding = 0.0018;
    double survivability_loss_per_s_at_flooding = 0.0022;
    double survivability_loss_per_s_at_fire = 0.0010;

    // --- Mount-state coupling ------------------------------------------------
    // Sustained mount engagement degrades the damage-response posture: a mount
    // that has spent rounds is not a full damage-control asset. `ready_fraction`
    // is the mean (ready_count / max_ready_count) over the platform's mounts, so
    // it is 1.0 exactly while no mount has been spent.
    //
    //   mount_response_scale = 1 + (1 - ready_fraction) * mount_response_weight
    // mount_response_weight = 0.0   -> response is neutral for any mount state
    // mount_response_weight > 0.0   -> spent rounds alter the declared response
    //
    // The ready fraction is also clamped to [mount_ready_fraction_floor, 1.0]
    // before use so an empty magazine cannot remove the response entirely.
    //
    // The admitted parity profile is neutral (0.0). A nonzero weight is an
    // explicit future profile choice, not an implicit side effect of constructing
    // this data contract with default member initializers.
    double mount_response_weight = 0.0;
    double mount_ready_fraction_floor = 0.0;

    // --- Derived capability floors ------------------------------------------
    // Lower clamps applied to the capability values that feed derived platform
    // state (propulsion scale, loss projection).
    double mobility_propulsion_floor = 0.2;
    double mobility_propulsion_ceiling = 1.0;
    double mil_thrust_n_per_mps = 100000.0;
    double ab_thrust_n_per_mps = 120000.0;

    // --- Declared provenance pasted onto naval_damage_response_profiles() -----
    std::string provenance =
        "synthetic_engineering: parity extraction of the pre-DM-N1 inline literals";
    bool synthetic = true;
    bool calibrated = false;
    bool evidence_backed = false;
};

// Built-in profile whose response coefficients are the pre-DM-N1 literals, so
// the shipped naval severity/capability response is preserved exactly.
//
// `mount_response_weight` is 0.0 here on purpose. The naval damage system
// declares no consumed services in the composition contract, so the admitted
// profile may not silently consume weapon-mount state. The coupling code and
// mount-input projection stay available for a future explicitly selected profile,
// while the admitted default stays bit-exact with the shipped literals for every
// mount state.
[[nodiscard]] constexpr NavalDamageResponseProfile
naval_damage_response_profile_default() noexcept {
    constexpr std::string_view default_provenance =
        "synthetic_engineering: parity extraction of the pre-DM-N1 inline literals";
    NavalDamageResponseProfile profile{};
    profile.ship_class_id = std::string("naval_damage_response_default");
    profile.fire_decay_per_s = 0.0008;
    profile.breach_decay_per_s = 0.0001;
    profile.flooding_decay_per_s = 0.0002;
    profile.breach_to_flooding_per_s = 0.003;
    profile.mission_loss_per_s_at_fire = 0.0015;
    profile.sensor_loss_per_s_at_fire = 0.0012;
    profile.mobility_loss_per_s_at_flooding = 0.0018;
    profile.survivability_loss_per_s_at_flooding = 0.0022;
    profile.survivability_loss_per_s_at_fire = 0.0010;
    profile.mount_response_weight = 0.0;
    profile.mount_ready_fraction_floor = 0.0;
    profile.mobility_propulsion_floor = 0.2;
    profile.mobility_propulsion_ceiling = 1.0;
    profile.mil_thrust_n_per_mps = 100000.0;
    profile.ab_thrust_n_per_mps = 120000.0;
    profile.provenance = std::string(default_provenance);
    profile.synthetic = true;
    profile.calibrated = false;
    profile.evidence_backed = false;
    return profile;
}

// Built-in registry of admitted naval damage-response profiles. The current
// branch intentionally exposes one parity profile only: adding a second profile
// requires an explicit content selection path and a runtime test before it may
// affect a platform.
[[nodiscard]] inline const std::vector<NavalDamageResponseProfile> &
naval_damage_response_profiles() {
    static const std::vector<NavalDamageResponseProfile> profiles{
        naval_damage_response_profile_default(),
    };
    return profiles;
}

// Registry index of the only profile currently admitted by the runtime.
inline constexpr std::size_t kNavalDamageResponseProfileDefaultIndex = 0;

// Resolve a registry index to a profile. Out-of-range indices and an empty
// registry resolve to nullptr, which the caller treats as "no naval response for
// this platform".
[[nodiscard]] inline const NavalDamageResponseProfile *
resolve_naval_damage_response_profile(std::size_t profile_index) noexcept {
    const std::vector<NavalDamageResponseProfile> &profiles = naval_damage_response_profiles();
    if (profile_index >= profiles.size()) {
        return nullptr;
    }
    return &profiles[profile_index];
}

// Mount-derived damage-response degradation term shared by every coefficient
// below. `mount_ready_fraction` is the mean ready/max fraction over the
// platform's mounts (1.0 when nothing has been spent). Returns a multiplier that
// is exactly 1.0 whenever the profile declares no coupling or the mounts are
// full, so `mount_response_weight = 0.0` is provably neutral and a full magazine
// never changes the declared coefficients.
[[nodiscard]] inline double
naval_damage_mount_response_scale(const NavalDamageResponseProfile &profile,
                                  double mount_ready_fraction) noexcept {
    const double floor_fraction = std::clamp(profile.mount_ready_fraction_floor, 0.0, 1.0);
    const double ready_fraction = std::clamp(mount_ready_fraction, floor_fraction, 1.0);
    const double spent_fraction = 1.0 - ready_fraction;
    const double weight = std::max(0.0, profile.mount_response_weight);
    return 1.0 + (spent_fraction * weight);
}

// Mean ready/max fraction over declared mounts. Returns 1.0 for a platform with
// no mounts, so mount coupling is neutral where there is nothing to spend.
// `mounts` only needs `ready_count` / `max_ready_count`, which keeps this a pure
// projection without pulling a weapon header into the damage surface.
template <typename MountRange>
[[nodiscard]] inline double naval_damage_mount_ready_fraction(const MountRange &mounts) noexcept {
    std::size_t counted_mounts = 0;
    double ready_fraction_sum = 0.0;
    for (const auto &mount : mounts) {
        if (mount.max_ready_count <= 0) {
            continue;
        }
        ++counted_mounts;
        ready_fraction_sum += std::clamp(static_cast<double>(mount.ready_count) /
                                             static_cast<double>(mount.max_ready_count),
                                         0.0, 1.0);
    }
    if (counted_mounts == 0) {
        return 1.0;
    }
    return ready_fraction_sum / static_cast<double>(counted_mounts);
}

// Fire-severity decay term for one tick scaled by the mount coupling.
[[nodiscard]] inline double naval_damage_fire_decay_per_s(const NavalDamageResponseProfile &profile,
                                                          double mount_response_scale) noexcept {
    return profile.fire_decay_per_s * mount_response_scale;
}

// Hull-breach decay term for one tick scaled by the mount coupling.
[[nodiscard]] inline double
naval_damage_breach_decay_per_s(const NavalDamageResponseProfile &profile,
                                double mount_response_scale) noexcept {
    return profile.breach_decay_per_s * mount_response_scale;
}

// Flooding decay term for one tick scaled by the mount coupling.
[[nodiscard]] inline double
naval_damage_flooding_decay_per_s(const NavalDamageResponseProfile &profile,
                                  double mount_response_scale) noexcept {
    return profile.flooding_decay_per_s * mount_response_scale;
}

// Flooding ingress from an open hull breach. Not mount scaled: an open breach
// admits water whether or not the mounts have been firing.
[[nodiscard]] inline double
naval_damage_breach_flooding_gain_per_s(const NavalDamageResponseProfile &profile,
                                        double breach_progress) noexcept {
    return profile.breach_to_flooding_per_s * breach_progress;
}

// Capability loss for one tick, scaled by the mount coupling. `progress` is the
// severity of the driving channel (fire or flooding).
[[nodiscard]] inline double
naval_damage_capability_loss_per_s(double coefficient_per_s, double progress,
                                   double mount_response_scale) noexcept {
    return coefficient_per_s * progress * mount_response_scale;
}
