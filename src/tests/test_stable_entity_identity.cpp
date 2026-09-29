// SI-P2-B native seam tests for stable entity identity
// (docs/architecture/work/active/stable_entity_identity/README.md).
//
// Covers the stamping primitive, reset wiring, KeyEntity coverage after spawn/fire/step/reset,
// the E1/E2 factory identity fixes, and the pure draw-seed helper including stream-step
// bit-identity against the pre-existing private copies.

#include "core/engine/simulation_kernel.h"

#include "components/basic/common.h"
#include "components/basic/stable_identity.h"
#include "components/basic/tags.h"
#include "components/combat/common/weapon_common.h"
#include "components/command/pilot_action.h"
#include "components/systems/ew.h"
#include "components/systems/sensor.h"
#include "core/interfaces/stable_entity_identity.h"
#include "core/interfaces/stochastic_draw.h"
#include "systems/system_contribution_registry.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <algorithm>
#include <array>
#include <cstdint>
#include <string>
#include <vector>

// Bit-identity references: verbatim copies of the two pre-existing stream steps, so this test
// pins the helper to the exact pre-change sequences. The originals live in private fragments
// (an anonymous-namespace include of default_effects_model.cpp, and damage_system_common.h's
// anonymous namespace) that cannot be linked from a test TU. P3 deletes the originals and
// routes both call sites through the helper; this test then remains the sequence pin.
namespace reference_streams {

// models/weapons/detail/default_effects_geometry_detail.h `splitmix64` (Weyl form).
std::uint64_t geometry_splitmix64(std::uint64_t &state) {
    std::uint64_t z = (state += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

// systems/combat/damage_system_common.h `damage_splitmix64` (feedback form via
// `damage_rand_uniform01`: state = damage_splitmix64(state)).
std::uint64_t damage_splitmix64(std::uint64_t seed) {
    std::uint64_t z = seed + 0x9e3779b97f4a7c15ULL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

} // namespace reference_streams

namespace {

// Raw-world fixture (P1 E5): a world built without a kernel must install the identity state
// explicitly before any stamped path; nothing defaults it.
//
// Components are registered through the admitted registry, in registry order, not one type at
// a time. Flecs caches a component id per C++ type for the whole process (first registration
// wins, and the consistency assert is compiled out in Release). A raw world that registers
// `StableEntitySerial` first would claim the id that a kernel world later expects for
// `Transform`. The kernel then aborts with INCONSISTENT_NAME, but only when this suite runs
// first, which is exactly what `ef_test -ts=...` does. This is the same defect class as the
// DM-G1 94/105 component split.
void install_stable_identity_state(flecs::world &world, std::uint64_t episode_seed) {
    runtime::systems::register_default_component_contributions(world);
    world.set<StableIdentityState>({1, episode_seed});
}

std::vector<flecs::entity> key_entities(flecs::world &world) {
    std::vector<flecs::entity> out;
    world.each([&](flecs::entity e, const KeyEntity &) { out.push_back(e); });
    return out;
}

void require_every_key_entity_stamped(flecs::world &world) {
    std::vector<std::uint64_t> serials;
    for (const auto &e : key_entities(world)) {
        const StableEntitySerial *serial = e.get<StableEntitySerial>();
        INFO("KeyEntity without serial: ", e.id());
        REQUIRE(serial != nullptr);
        serials.push_back(serial->value);
    }
    std::sort(serials.begin(), serials.end());
    CHECK(std::adjacent_find(serials.begin(), serials.end()) == serials.end());
}

std::vector<flecs::entity> station_children(flecs::world &world, flecs::entity parent) {
    std::vector<flecs::entity> out;
    parent.children([&](flecs::entity child) {
        if (child.has<Munition>()) out.push_back(child);
    });
    return out;
}

std::uint64_t next_serial(flecs::world &world) {
    const StableIdentityState *state = world.get<StableIdentityState>();
    REQUIRE(state != nullptr);
    return state->next_serial;
}

} // namespace

TEST_SUITE("stable_entity_identity") {

    TEST_CASE("raw world: serials are 1..N in creation order and re-stamp is refused") {
        flecs::world world;
        install_stable_identity_state(world, 7);
        std::vector<flecs::entity> created;
        for (int index = 0; index < 5; ++index) {
            auto e = world.entity();
            CHECK(stamp_stable_serial(e) == static_cast<std::uint64_t>(index + 1));
            created.push_back(e);
        }
        for (std::size_t index = 0; index < created.size(); ++index) {
            CHECK(created[index].get<StableEntitySerial>()->value == index + 1);
        }
        CHECK(next_serial(world) == 6);

        CHECK(stable_identity::stamp_refusal(created.front()) ==
              stable_identity::StampRefusal::already_stamped);
        CHECK(stable_identity::stamp_refusal(world.entity()) ==
              stable_identity::StampRefusal::none);
        CHECK(stable_identity::stamp_refusal(flecs::entity::null(world.c_ptr())) ==
              stable_identity::StampRefusal::invalid_entity);

        flecs::world bare;
        runtime::systems::register_default_component_contributions(bare);
        CHECK(stable_identity::stamp_refusal(bare.entity()) ==
              stable_identity::StampRefusal::missing_state);
    }

    TEST_CASE("raw world: deferred creation advances the live counter in order (E3)") {
        flecs::world world;
        install_stable_identity_state(world, 1);
        std::vector<std::uint64_t> stamped;
        world.defer_begin();
        for (int index = 0; index < 3; ++index) {
            auto e = world.entity();
            stamped.push_back(stamp_stable_serial(e));
        }
        CHECK(next_serial(world) == 4);
        world.defer_end();
        CHECK(stamped == std::vector<std::uint64_t>{1, 2, 3});
    }

    TEST_CASE("kernel: construction installs identity; reset restarts at 1 with the seed") {
        SimulationKernel kernel;
        {
            auto lease = kernel.acquire_world_lease();
            const StableIdentityState *state = lease.world().get<StableIdentityState>();
            REQUIRE(state != nullptr);
            CHECK(state->next_serial == 1);
            CHECK(state->episode_seed == 42);
        }
        REQUIRE(kernel.load_database("examples/config/database"));
        auto first = kernel.spawn_unit(Side::Blue, "F-16C_Block50", 0.0, 0.0, 5000.0, 0.0, 0.0,
                                       0.0, 200.0, 0.0, 0.0);
        REQUIRE(first.is_valid());
        CHECK(first.get<StableEntitySerial>()->value == 1);

        kernel.reset(20260529);
        auto lease = kernel.acquire_world_lease();
        flecs::world &world = lease.world();
        const StableIdentityState *state = world.get<StableIdentityState>();
        REQUIRE(state != nullptr);
        CHECK(state->next_serial == 1);
        CHECK(state->episode_seed == 20260529);
        // E7: reset cascades to ChildOf children, so no stale serial survives.
        std::size_t stale = 0;
        world.each([&](flecs::entity, const StableEntitySerial &) { ++stale; });
        CHECK(stale == 0);
    }

    TEST_CASE("kernel: spawn serials follow creation order; stations fresh and ascending") {
        SimulationKernel kernel;
        REQUIRE(kernel.load_database("examples/config/database"));
        kernel.reset(11);
        auto a = kernel.spawn_unit(Side::Blue, "F-16C_Block50", 0.0, 0.0, 5000.0, 0.0, 0.0, 0.0,
                                   200.0, 0.0, 0.0);
        auto b = kernel.spawn_unit(Side::Blue, "F-16C_Block50", 1000.0, 0.0, 5000.0, 0.0, 0.0,
                                   0.0, 200.0, 0.0, 0.0);
        REQUIRE(a.is_valid());
        REQUIRE(b.is_valid());

        auto lease = kernel.acquire_world_lease();
        flecs::world &world = lease.world();
        const auto a_stations = station_children(world, a);
        const auto b_stations = station_children(world, b);
        // F-16C default loadout has stations 1, 2, 8, 9.
        REQUIRE(a_stations.size() == 4);
        REQUIRE(b_stations.size() == 4);

        // Root first, then its stations in ascending station order, then the next unit (E1).
        CHECK(a.get<StableEntitySerial>()->value == 1);
        std::vector<std::pair<int, std::uint64_t>> a_rows;
        for (const auto &child : a_stations) {
            a_rows.emplace_back(child.get<Munition>()->station_id,
                                child.get<StableEntitySerial>()->value);
            CHECK(std::string(child.name().c_str()) ==
                  "F-16C_Block50_Stn_" + std::to_string(child.get<Munition>()->station_id));
        }
        std::sort(a_rows.begin(), a_rows.end());
        CHECK(a_rows == std::vector<std::pair<int, std::uint64_t>>{{1, 2}, {2, 3}, {8, 4}, {9, 5}});
        CHECK(b.get<StableEntitySerial>()->value == 6);

        // E2: the second spawn owns fresh children; the first spawn keeps its own.
        for (const auto &child : a_stations) {
            CHECK(child.parent().id() == a.id());
            for (const auto &other : b_stations) {
                CHECK(child.id() != other.id());
            }
        }
        for (const auto &child : b_stations) {
            CHECK(child.parent().id() == b.id());
        }
        require_every_key_entity_stamped(world);
    }

    TEST_CASE("kernel: every KeyEntity carries a serial after spawn, fire, step and reset") {
        SimulationKernel kernel;
        REQUIRE(kernel.load_database("examples/config/database"));
        kernel.reset(5);
        auto shooter = kernel.spawn_unit(Side::Blue, "F-16C_Block50", 0.0, 0.0, 5000.0, 0.0, 0.0,
                                         0.0, 200.0, 0.0, 0.0);
        auto target = kernel.spawn_unit(Side::Red, "F-16C_Block50", 0.0, 20000.0, 5000.0, 180.0,
                                        0.0, 0.0, 200.0, 0.0, 0.0);
        auto ship = kernel.spawn_unit(Side::Blue, "DDG-51_Flight_I_ASW_Helo_MVP", 50000.0, 0.0,
                                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
        REQUIRE(shooter.is_valid());
        REQUIRE(target.is_valid());
        REQUIRE(ship.is_valid());

        std::uint64_t fired_id = 0;
        {
            auto lease = kernel.acquire_world_lease();
            flecs::world &world = lease.world();
            // The embarked helo arrives through the recursive spawn and is stamped there.
            std::size_t helos = 0;
            ship.children([&](flecs::entity child) {
                if (child.has<KeyEntity>() && !child.has<Munition>()) {
                    ++helos;
                    CHECK(child.has<StableEntitySerial>());
                }
            });
            CHECK(helos == 1);

            // Give the shooter a track, ammunition and countermeasure programs so the fire
            // path and both deferred EW creation paths run.
            Detection det{};
            det.target_id = target.id();
            det.range = 20000.0;
            det.local_sensor_hit = true;
            shooter.set<ContactList>({{det}});
            shooter.set<Ammo>({4, 4});
            shooter.set<Countermeasures>({3, 3, 0.0, -1.0, false});
            require_every_key_entity_stamped(world);
        }
        PilotAction action{};
        action.active = true;
        action.program_chaff = true;
        action.program_flare = true;
        kernel.set_pilot_action(shooter.id(), action);

        auto missile = kernel.fire_missile(shooter.id(), target.id());
        REQUIRE(missile.is_valid());
        fired_id = missile.id();
        CHECK(missile.has<StableEntitySerial>());

        const std::uint64_t before_step = [&] {
            auto lease = kernel.acquire_world_lease();
            return next_serial(lease.world());
        }();
        kernel.step();
        {
            auto lease = kernel.acquire_world_lease();
            flecs::world &world = lease.world();
            std::size_t countermeasures = 0;
            world.each([&](flecs::entity, const Lifetime &) { ++countermeasures; });
            CHECK(countermeasures >= 1);
            CHECK(next_serial(world) == before_step + countermeasures);
            require_every_key_entity_stamped(world);
            CHECK(world.entity(fired_id).has<StableEntitySerial>());
        }

        kernel.reset(6);
        auto lease = kernel.acquire_world_lease();
        flecs::world &world = lease.world();
        CHECK(key_entities(world).empty());
        std::size_t stale = 0;
        world.each([&](flecs::entity, const StableEntitySerial &) { ++stale; });
        CHECK(stale == 0);
        CHECK(next_serial(world) == 1);
    }

    TEST_CASE("kernel: naval gun rejects a live target without a serial (E9)") {
        SimulationKernel kernel;
        REQUIRE(kernel.load_database("examples/config/database"));
        kernel.reset(9);
        auto ship = kernel.spawn_unit(Side::Blue, "DDG-51_Flight_I_ASW_Helo_MVP", 0.0, 0.0, 0.0,
                                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
        REQUIRE(ship.is_valid());
        std::uint64_t unstamped_id = 0;
        {
            auto lease = kernel.acquire_world_lease();
            flecs::world &world = lease.world();
            auto unstamped = world.entity()
                                 .set<Transform>({0.0, 1000.0, 10.0, 0.0, 0.0, 0.0})
                                 .add<SimObject>();
            unstamped_id = unstamped.id();
            Detection det{};
            det.target_id = unstamped_id;
            det.range = 1000.0;
            ship.set<ContactList>({{det}});
        }
        CHECK_FALSE(kernel.fire_naval_weapon(ship.id(), unstamped_id, 2));
        CHECK_FALSE(kernel.fire_naval_weapon(ship.id(), unstamped_id, 3));
    }

    TEST_CASE("helper: every input changes the seed and participant order matters") {
        flecs::world world;
        install_stable_identity_state(world, 1234);
        auto a = world.entity();
        auto b = world.entity();
        stamp_stable_serial(a);
        stamp_stable_serial(b);
        using stochastic_draw::DrawSite;
        using stochastic_draw::draw_seed;

        const std::uint64_t base = draw_seed(world, DrawSite::naval_gun_ciws, 1.25, {a, b}, {3});
        CHECK(base == draw_seed(world, DrawSite::naval_gun_ciws, 1.25, {a, b}, {3}));
        CHECK(base != draw_seed(world, DrawSite::ground_direct_fire, 1.25, {a, b}, {3}));
        CHECK(base != draw_seed(world, DrawSite::naval_gun_ciws, 1.251, {a, b}, {3}));
        CHECK(base != draw_seed(world, DrawSite::naval_gun_ciws, 1.25, {b, a}, {3}));
        CHECK(base != draw_seed(world, DrawSite::naval_gun_ciws, 1.25, {a}, {3}));
        CHECK(base != draw_seed(world, DrawSite::naval_gun_ciws, 1.25, {a, b}, {4}));
        CHECK(base != draw_seed(world, DrawSite::naval_gun_ciws, 1.25, {a, b}));
        // Participant and word sequences are length-separated.
        CHECK(draw_seed(world, DrawSite::naval_gun_ciws, 1.25, {a}, {7}) !=
              draw_seed(world, DrawSite::naval_gun_ciws, 1.25, {a, b}));

        world.set<StableIdentityState>({world.get<StableIdentityState>()->next_serial, 1235});
        CHECK(base != draw_seed(world, DrawSite::naval_gun_ciws, 1.25, {a, b}, {3}));

        // The seed depends on serials, not on raw ids: a second world that allocates extra
        // entities first (moving every raw id) draws the same seed for the same serials.
        flecs::world shifted;
        install_stable_identity_state(shifted, 1235);
        for (int index = 0; index < 17; ++index) shifted.entity();
        auto sa = shifted.entity();
        auto sb = shifted.entity();
        stamp_stable_serial(sa);
        stamp_stable_serial(sb);
        CHECK(sa.id() != a.id());
        CHECK(draw_seed(shifted, DrawSite::naval_gun_ciws, 1.25, {sa, sb}, {3}) ==
              draw_seed(world, DrawSite::naval_gun_ciws, 1.25, {a, b}, {3}));

        CHECK(stochastic_draw::lane(base, 1) != stochastic_draw::lane(base, 2));
        CHECK(stochastic_draw::lane(base, 1) != base);
        const double u = stochastic_draw::uniform01(base);
        CHECK(u >= 0.0);
        CHECK(u < 1.0);
        CHECK(static_cast<std::uint64_t>(DrawSite::ground_direct_fire) == 4);
    }

    TEST_CASE("helper: stream steps are bit-identical to the pre-existing copies") {
        const std::array<std::uint64_t, 4> seeds = {0ULL, 1ULL, 0x0123456789abcdefULL,
                                                    0xffffffffffffffffULL};
        for (const std::uint64_t seed : seeds) {
            std::uint64_t helper_weyl = seed;
            std::uint64_t reference_weyl = seed;
            std::uint64_t helper_feedback = seed;
            std::uint64_t reference_feedback = seed;
            for (int step = 0; step < 64; ++step) {
                CHECK(stochastic_draw::splitmix64_weyl_next(helper_weyl) ==
                      reference_streams::geometry_splitmix64(reference_weyl));
                CHECK(helper_weyl == reference_weyl);
                reference_feedback = reference_streams::damage_splitmix64(reference_feedback);
                CHECK(stochastic_draw::splitmix64_feedback_next(helper_feedback) ==
                      reference_feedback);
                CHECK(helper_feedback == reference_feedback);
            }
        }
        // Golden values (independent Python computation) guard against the references and the
        // helper drifting together.
        std::uint64_t weyl = 0x0123456789abcdefULL;
        CHECK(stochastic_draw::splitmix64_weyl_next(weyl) == 0x157a3807a48faa9dULL);
        CHECK(stochastic_draw::splitmix64_weyl_next(weyl) == 0xd573529b34a1d093ULL);
        std::uint64_t feedback = 0x0123456789abcdefULL;
        CHECK(stochastic_draw::splitmix64_feedback_next(feedback) == 0x157a3807a48faa9dULL);
        CHECK(stochastic_draw::splitmix64_feedback_next(feedback) == 0x021c88d0a3fd73b6ULL);
        CHECK(stochastic_draw::splitmix64_feedback_next(feedback) == 0x47cc2e80f0aef1a3ULL);
    }
}
