#pragma once

// The one creation primitive that assigns `StableEntitySerial` (Decision 1 of
// docs/architecture/work/active/stable_entity_identity). It is applied at every path that sets
// `KeyEntity`; the architecture guard forbids `set<KeyEntity>` elsewhere.
//
// Failure is an invariant violation, not a recoverable error: the primitive logs and aborts.
// It does not throw, because stamp sites run inside Flecs systems (EW chaff/flare, pilot weapon
// release) where exceptions cannot cross the C frames.

#include "components/basic/stable_identity.h"

#include <flecs.h>

#include <cstdint>
#include <cstdio>
#include <cstdlib>

namespace stable_identity {

enum class StampRefusal : std::uint8_t {
    none = 0,
    invalid_entity,
    already_stamped,
    missing_state,
};

// Pure predicate behind the primitive, exposed so the refusal is testable without a crash.
[[nodiscard]] inline StampRefusal stamp_refusal(flecs::entity entity) {
    if (!entity.is_valid()) {
        return StampRefusal::invalid_entity;
    }
    if (entity.has<StableEntitySerial>()) {
        return StampRefusal::already_stamped;
    }
    if (entity.world().get<StableIdentityState>() == nullptr) {
        return StampRefusal::missing_state;
    }
    return StampRefusal::none;
}

[[nodiscard]] inline const char *stamp_refusal_name(StampRefusal refusal) noexcept {
    switch (refusal) {
    case StampRefusal::none:
        return "none";
    case StampRefusal::invalid_entity:
        return "invalid_entity";
    case StampRefusal::already_stamped:
        return "already_stamped";
    case StampRefusal::missing_state:
        return "missing_state";
    }
    return "unknown";
}

[[noreturn]] inline void identity_invariant_violation(const char *operation, const char *detail,
                                                      std::uint64_t entity_id) noexcept {
    std::fprintf(stderr, "stable identity invariant violated: %s: %s (entity %llu)\n", operation,
                 detail, static_cast<unsigned long long>(entity_id));
    std::fflush(stderr);
    std::abort();
}

} // namespace stable_identity

// Assigns the next episode serial to `entity` and returns it.
//
// The counter advances through `get_mut` on the live singleton, never through a queued `set`
// command, so deferred creation inside a system (P1 E3) still increments immediately and in
// iteration order. The serial component itself may be queued; nothing reads it before merge.
inline std::uint64_t stamp_stable_serial(flecs::entity entity) {
    const stable_identity::StampRefusal refusal = stable_identity::stamp_refusal(entity);
    if (refusal != stable_identity::StampRefusal::none) {
        stable_identity::identity_invariant_violation(
            "stamp_stable_serial", stable_identity::stamp_refusal_name(refusal),
            entity.is_valid() ? static_cast<std::uint64_t>(entity.id()) : 0);
    }
    StableIdentityState *state = entity.world().get_mut<StableIdentityState>();
    const std::uint64_t serial = state->next_serial;
    state->next_serial += 1;
    entity.set<StableEntitySerial>({serial});
    return serial;
}
