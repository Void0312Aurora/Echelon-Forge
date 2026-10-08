#pragma once

// Cross-layer draw-seed contract (Decision 3 of
// docs/architecture/work/active/stable_entity_identity). Header-only and pure.
//
// Every per-engagement or per-detection stochastic draw derives its seed here, from the episode
// seed, a fixed draw-site value, quantized simulation time, the participants' stable serials in
// the caller's order, and optional extra words. Raw Flecs ids are never mixed: they move with
// the component census, with earlier spawns and with the generation recycled after reset().
//
// The splitmix64 constants live only in this header; the architecture guard
// (tests/architecture/structural_boundaries/test_stochastic_draw_guard.py) forbids them
// elsewhere in the maintained source tree.

#include "components/basic/stable_identity.h"

#include <flecs.h>

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>

namespace stochastic_draw {

// Fixed and append-only. A value is an identity that seeds recorded outcomes, so a value is
// never renumbered or reused.
enum class DrawSite : std::uint64_t {
    debug_synthetic_missile = 1,
    missile_release = 2,
    naval_gun_ciws = 3,
    ground_direct_fire = 4,
    radar_detection = 5,
    acoustic_detection = 6,
    command_link_drop = 7,
    decoy_seduction = 8,
};

inline constexpr std::uint64_t kSplitmix64Gamma = 0x9e3779b97f4a7c15ULL;

// splitmix64 output finalizer.
[[nodiscard]] constexpr std::uint64_t splitmix64_mix(std::uint64_t z) noexcept {
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

// Weyl-form stream step: `state += gamma; out = mix(state)`. Bit-identical to the effects
// geometry stream (models/weapons/detail/default_effects_geometry_detail.h `splitmix64`).
[[nodiscard]] constexpr std::uint64_t splitmix64_weyl_next(std::uint64_t &state) noexcept {
    state += kSplitmix64Gamma;
    return splitmix64_mix(state);
}

// Feedback-form stream step: `state = mix(state + gamma); out = state`. Bit-identical to the
// damage stream (systems/combat/damage_system_common.h `damage_rand_uniform01`). The two forms
// are different streams and are deliberately not unified.
[[nodiscard]] constexpr std::uint64_t splitmix64_feedback_next(std::uint64_t &state) noexcept {
    state = splitmix64_mix(state + kSplitmix64Gamma);
    return state;
}

// Uniform double in [0, 1) from one stateless splitmix64 output: 53 random bits / 2^53.
[[nodiscard]] constexpr double uniform01(std::uint64_t seed) noexcept {
    return static_cast<double>(splitmix64_mix(seed + kSplitmix64Gamma) >> 11) *
           (1.0 / 9007199254740992.0);
}

// Uniform double in [0, 1) from a value already produced by `splitmix64_weyl_next` or
// `splitmix64_feedback_next`: 53 random bits / 2^53, with no re-mix. `uniform01` re-mixes its
// argument as a seed, which is the right call at every draw site; the two consolidated stream
// steps (geometry, damage) instead advance their own long-lived `rng_state` and need the mixed
// output scaled directly, exactly as their pre-consolidation copies did.
[[nodiscard]] constexpr double stream_uniform01(std::uint64_t mixed) noexcept {
    return static_cast<double>(mixed >> 11) * (1.0 / 9007199254740992.0);
}

// Independent sub-seed for one named quantity drawn from a site seed (for example range noise
// versus bearing noise). Replaces the sites' ad hoc xor constants.
[[nodiscard]] constexpr std::uint64_t lane(std::uint64_t seed, std::uint64_t tag) noexcept {
    return splitmix64_mix((seed ^ splitmix64_mix(tag + kSplitmix64Gamma)) + kSplitmix64Gamma);
}

namespace detail {

[[noreturn]] inline void draw_invariant_violation(DrawSite site, const char *detail,
                                                  std::uint64_t entity_id) noexcept {
    std::fprintf(stderr, "stochastic draw invariant violated: site %llu: %s (entity %llu)\n",
                 static_cast<unsigned long long>(site), detail,
                 static_cast<unsigned long long>(entity_id));
    std::fflush(stderr);
    std::abort();
}

// Order-dependent absorption of one 64-bit word.
[[nodiscard]] constexpr std::uint64_t absorb(std::uint64_t state, std::uint64_t word) noexcept {
    return splitmix64_mix((state ^ word) + kSplitmix64Gamma);
}

} // namespace detail

// Quantizes simulation time to whole milliseconds, the resolution every draw site uses. Two
// draws at one site with the same participants in the same millisecond stay correlated, as
// they are today (held out of scope by the package).
// Safe public-boundary predicate; also excludes integer-conversion overflow.
[[nodiscard]] inline bool valid_time(double sim_time_s) noexcept {
    return std::isfinite(sim_time_s) && sim_time_s >= 0.0 &&
           sim_time_s * 1000.0 < std::ldexp(1.0, 64);
}

[[nodiscard]] inline std::uint64_t quantize_time_ms(DrawSite site, double sim_time_s) noexcept {
    if (!valid_time(sim_time_s)) {
        detail::draw_invariant_violation(site, "simulation time is outside the draw clock range",
                                         0);
    }
    return static_cast<std::uint64_t>(sim_time_s * 1000.0);
}

// Serial of one participant. A participant without a serial is an invariant violation: callers
// reject such ids at their public API boundary (Decision 4), so reaching here is a defect.
// There is no fallback to the raw id or to zero.
[[nodiscard]] inline std::uint64_t participant_serial(DrawSite site, flecs::entity participant) {
    if (!participant.is_valid()) {
        detail::draw_invariant_violation(site, "participant is not a live entity",
                                         static_cast<std::uint64_t>(participant.id()));
    }
    const StableEntitySerial *serial = participant.get<StableEntitySerial>();
    if (serial == nullptr) {
        detail::draw_invariant_violation(site, "participant carries no StableEntitySerial",
                                         static_cast<std::uint64_t>(participant.id()));
    }
    return serial->value;
}

[[nodiscard]] inline std::uint64_t draw_seed(const flecs::world &world, DrawSite site,
                                             double sim_time_s,
                                             std::initializer_list<flecs::entity> participants,
                                             std::initializer_list<std::uint64_t> words = {}) {
    const StableIdentityState *identity = world.get<StableIdentityState>();
    if (identity == nullptr) {
        detail::draw_invariant_violation(site, "world has no StableIdentityState", 0);
    }
    std::uint64_t state = detail::absorb(kSplitmix64Gamma, identity->episode_seed);
    state = detail::absorb(state, static_cast<std::uint64_t>(site));
    state = detail::absorb(state, quantize_time_ms(site, sim_time_s));
    // Lengths separate the participant and word sequences, so {a, b} + {} never equals
    // {a} + {b}.
    state = detail::absorb(state, static_cast<std::uint64_t>(participants.size()));
    for (const flecs::entity &participant : participants) {
        state = detail::absorb(state, participant_serial(site, participant));
    }
    state = detail::absorb(state, static_cast<std::uint64_t>(words.size()));
    for (const std::uint64_t word : words) {
        state = detail::absorb(state, word);
    }
    return state;
}

} // namespace stochastic_draw
