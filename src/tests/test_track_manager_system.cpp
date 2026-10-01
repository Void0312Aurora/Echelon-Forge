// Track manager behaviour when a contact outlives its target.
//
// A contact list (or a data-link report) can name an entity that was destroyed
// earlier in the same step, for example by a CIWS intercept. Debug flecs asserts
// `ecs_is_alive` on `get`, so every target lookup in the track manager must check
// liveness first; a dead target classifies the track as Unknown.

#include "components/basic/common.h"
#include "components/systems/sensor.h"
#include "components/systems/track_management.h"
#include "systems/system_contribution_registry.h"
#include "systems/systems/track_manager_system.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <cstdint>

namespace {

Detection contact_for(std::uint64_t target_id) {
    Detection detection{};
    detection.target_id = target_id;
    detection.range = 1500.0;
    detection.bearing = 0.0;
    detection.elevation = 0.0;
    detection.signal_strength = 1.0;
    detection.local_sensor_hit = true;
    // Fresh relative to the first tick, so the manager opens a tentative track.
    detection.timestamp = 1.0;
    return detection;
}

} // namespace

TEST_SUITE("track_manager_system") {

    TEST_CASE("a contact naming a destroyed target opens an Unknown track") {
        flecs::world world;
        runtime::systems::register_default_component_contributions(world);
        register_track_manager_system(world);

        auto target = world.entity().set<Alliance>({Side::Red});
        const std::uint64_t target_id = target.id();
        target.destruct();
        REQUIRE_FALSE(world.entity(target_id).is_alive());

        ContactList contacts{};
        contacts.contacts.push_back(contact_for(target_id));
        auto owner = world.entity()
                         .set<Alliance>({Side::Blue})
                         .set<Transform>({0.0, 0.0, 0.0, 0.0, 0.0, 0.0})
                         .set<ContactList>(contacts)
                         .set<Sensor>(Sensor{})
                         .set<TrackDatabase>(TrackDatabase{});

        world.progress(1.0);

        const TrackDatabase *db = owner.get<TrackDatabase>();
        REQUIRE(db != nullptr);
        REQUIRE(db->tentative_tracks.size() == 1);
        CHECK(db->tentative_tracks[0].entity_id == target_id);
        CHECK(db->tentative_tracks[0].classification == TrackClass::Unknown);
    }

    TEST_CASE("referenced entity alliance is the live alliance or none") {
        flecs::world world;
        runtime::systems::register_default_component_contributions(world);

        auto live = world.entity().set<Alliance>({Side::Red});
        const Alliance *live_alliance = referenced_entity_alliance(world, live.id());
        REQUIRE(live_alliance != nullptr);
        CHECK(live_alliance->side == Side::Red);

        const std::uint64_t dead_id = live.id();
        live.destruct();
        CHECK(referenced_entity_alliance(world, dead_id) == nullptr);
    }

} // TEST_SUITE("track_manager_system")
