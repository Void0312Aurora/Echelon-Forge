#pragma once

#include <cstdint>

// Stable per-episode entity identity (docs/architecture/work/active/stable_entity_identity).
//
// A Flecs entity id is an allocation handle: it moves with the registered component census,
// with earlier spawns, and with the generation recycled after reset(). Stochastic draws must
// key on this serial instead. Serials are assigned 1..N in creation order within an episode
// by the single creation primitive `stamp_stable_serial` (core/interfaces), never by hand.
struct StableEntitySerial {
    std::uint64_t value;
};

// World singleton owning identity for the current episode. `SimulationKernel::reset(seed)`
// rewrites it to {next_serial = 1, episode_seed = seed}; kernel construction installs it
// through its default reset.
struct StableIdentityState {
    std::uint64_t next_serial;
    std::uint64_t episode_seed;
};
