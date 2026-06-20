#include "core/engine/simulation_kernel.h"

#include <doctest/doctest.h>

#include <string>
#include <utility>

namespace {

constexpr const char* kDatabasePath = "examples/config/database";

WarheadProfile make_profiled_warhead(const std::string& family) {
    WarheadProfile profile{};
    profile.family = family;
    profile.mass_kg = 12.0;
    profile.lethal_radius_m = 35.0;
    profile.damage_scalar = family == "continuous_rod" ? 160.0 : 90.0;
    profile.synthetic = true;
    profile.damage_scalar_synthetic = true;
    profile.provenance = "test_default_effects_model";
    return profile;
}

std::pair<flecs::entity, flecs::entity> spawn_structured_f16_pair(SimulationKernel& kernel) {
    auto attacker = kernel.spawn_unit(
        Side::Blue,
        "F-16C_Block50",
        0.0,
        0.0,
        5000.0,
        0.0,
        0.0,
        0.0,
        0.0,
        250.0,
        0.0
    );
    auto target = kernel.spawn_unit(
        Side::Red,
        "F-16C_Block50",
        0.0,
        500.0,
        5000.0,
        180.0,
        0.0,
        0.0,
        0.0,
        -250.0,
        0.0
    );
    return {attacker, target};
}

RecentEngagementEvents run_profiled_hit(const std::string& family) {
    SimulationKernel kernel;
    kernel.reset(20260620);
    REQUIRE(kernel.load_database(kDatabasePath));

    auto [attacker, target] = spawn_structured_f16_pair(kernel);
    REQUIRE(attacker.is_valid());
    REQUIRE(target.is_valid());

    const WarheadProfile profile = make_profiled_warhead(family);
    CHECK(kernel.debug_apply_profiled_local_proximity_hit_with_velocity(
        static_cast<std::uint64_t>(attacker.id()),
        static_cast<std::uint64_t>(target.id()),
        -0.8,
        4.1,
        -0.985,
        profile,
        900.0,
        -250.0,
        0.0
    ));

    return kernel.export_recent_engagement_events();
}

}  // namespace

TEST_SUITE("default_effects_model") {

TEST_CASE("profiled proximity hit fails closed for invalid entities") {
    SimulationKernel kernel;
    kernel.reset(20260620);
    REQUIRE(kernel.load_database(kDatabasePath));

    auto [attacker, target] = spawn_structured_f16_pair(kernel);
    REQUIRE(attacker.is_valid());
    REQUIRE(target.is_valid());

    const WarheadProfile profile = make_profiled_warhead("continuous_rod");
    CHECK_FALSE(kernel.debug_apply_profiled_local_proximity_hit(
        0,
        static_cast<std::uint64_t>(target.id()),
        -0.8,
        4.1,
        -0.985,
        profile
    ));
    CHECK_FALSE(kernel.debug_apply_profiled_local_proximity_hit(
        static_cast<std::uint64_t>(attacker.id()),
        0,
        -0.8,
        4.1,
        -0.985,
        profile
    ));

    const RecentEngagementEvents events = kernel.export_recent_engagement_events();
    CHECK(events.effects_events.empty());
    CHECK(events.warhead_mechanism_events.empty());
    CHECK(events.component_load_events.empty());
}

TEST_CASE("continuous rod profile emits rod mechanism facts through default effects") {
    const RecentEngagementEvents events = run_profiled_hit("continuous_rod");
    REQUIRE(events.effects_events.size() == 1);
    REQUIRE(events.warhead_mechanism_events.size() == 1);
    REQUIRE(!events.component_load_events.empty());

    const EffectsEvent& effects = events.effects_events.front();
    const WarheadMechanismEvent& warhead = events.warhead_mechanism_events.front();

    CHECK(effects.trigger_type == "debug_profiled_local_proximity_hit");
    CHECK(effects.effect_family == "continuous_rod");
    CHECK(effects.mechanism_rod_cut_margin > 0.0);
    CHECK(effects.component_primary_mechanism_rod_cut_margin > 0.0);
    CHECK(warhead.header.stage == "warhead_mechanism");
    CHECK(warhead.header.status == "applied");
    CHECK(warhead.header.parent_event_id == effects.event_id);
    CHECK(warhead.header.chain_id == effects.event_id);
    CHECK(warhead.mechanism_family == effects.effect_family);
    CHECK(warhead.rod_cut_margin == doctest::Approx(effects.mechanism_rod_cut_margin));

    REQUIRE(events.component_load_events.size() == effects.component_mechanism_load_rows.size());
    bool saw_positive_rod_load = false;
    bool saw_primary_load = false;
    for (std::size_t index = 0; index < events.component_load_events.size(); ++index) {
        const ComponentLoadEvent& load = events.component_load_events[index];
        const ComponentMechanismLoadRow& row = effects.component_mechanism_load_rows[index];
        CHECK(load.header.stage == "component_load");
        CHECK(load.header.parent_event_id == effects.event_id);
        CHECK(load.header.chain_id == effects.event_id);
        CHECK(load.component_name == row.component_name);
        CHECK(load.component_system == row.component_system);
        CHECK(load.rod_cut_margin == doctest::Approx(row.mechanism_rod_cut_margin));
        const bool known_load_source =
            load.load_source == "direct_component_hit" ||
            load.load_source == "spatial_component_projection";
        CHECK(known_load_source);
        saw_positive_rod_load = saw_positive_rod_load || load.rod_cut_margin > 0.0;
        saw_primary_load = saw_primary_load ||
            (load.component_name == effects.component_primary_name &&
             load.component_system == effects.component_primary_system);
    }
    CHECK(saw_positive_rod_load);
    CHECK(saw_primary_load);
}

TEST_CASE("blast fragmentation profile does not synthesize rod mechanism facts") {
    const RecentEngagementEvents events = run_profiled_hit("blast_fragmentation");
    REQUIRE(events.effects_events.size() == 1);
    REQUIRE(events.warhead_mechanism_events.size() == 1);

    const EffectsEvent& effects = events.effects_events.front();
    const WarheadMechanismEvent& warhead = events.warhead_mechanism_events.front();

    CHECK(effects.effect_family == "blast_fragmentation");
    CHECK(effects.mechanism_rod_cut_margin == doctest::Approx(0.0));
    CHECK(effects.component_primary_mechanism_rod_cut_margin == doctest::Approx(0.0));
    CHECK(warhead.rod_cut_margin == doctest::Approx(0.0));
    for (const ComponentLoadEvent& load : events.component_load_events) {
        CHECK(load.rod_cut_margin == doctest::Approx(0.0));
    }
    for (const ComponentMechanismLoadRow& row : effects.component_mechanism_load_rows) {
        CHECK(row.mechanism_rod_cut_margin == doctest::Approx(0.0));
    }
}

}  // TEST_SUITE("default_effects_model")
