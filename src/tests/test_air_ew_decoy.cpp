// Native Air EW decoy tests: typed chaff/flare expendables, the IR signature
// they present, and seeker seduction inside the missile guidance contact loop.
// Missiles are launched through the maintained weapon-release service with a
// global tuning overlay, so the decoy-discrimination fields travel the same
// tuning -> resolved tuning -> Missile path weapon data uses.

#include "core/engine/simulation_kernel.h"
#include "core/engine/simulation_kernel_missile_tuning.h"

#include "components/basic/common.h"
#include "components/basic/stable_identity.h"
#include "components/combat/common/weapon_common.h"
#include "components/combat/health.h"
#include "components/combat/scoring.h"
#include "components/command/pilot_action.h"
#include "components/systems/ew.h"
#include "components/systems/sensor.h"
#include "core/interfaces/sensor_model.h"
#include "core/interfaces/stable_entity_identity.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <vector>

namespace {

constexpr double kNaN = std::numeric_limits<double>::quiet_NaN();
constexpr double kAltitudeM = 3000.0;
constexpr double kTargetNorthM = 5000.0;

struct Engagement {
    std::uint64_t shooter = 0;
    std::uint64_t target = 0;
    std::uint64_t missile = 0;
};

Detection seen(std::uint64_t id, double range_m, double bearing_deg, double signal) {
    Detection det{};
    det.target_id = id;
    det.range = range_m;
    det.bearing = bearing_deg;
    det.signal_strength = signal;
    det.local_sensor_hit = true;
    return det;
}

// Blue shooter at the origin facing north, Red target 5 km north facing south.
// The missile is launched with the given seeker type and decoy discrimination
// (NaN = not authored).
Engagement launch(SimulationKernel &kernel, unsigned seed, SensorType seeker, double rejection,
                  double resolution_cell_m) {
    kernel.reset(seed);
    MissileTuning tuning{};
    tuning.seeker_type = static_cast<int>(seeker);
    tuning.seeker_fov_deg = 90.0;
    tuning.seeker_decoy_rejection = rejection;
    tuning.seeker_resolution_cell_m = resolution_cell_m;
    kernel.set_missile_tuning(tuning);

    auto shooter = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, kAltitudeM, 0.0, 0.0, 0.0,
                                     0.0, 200.0, 0.0);
    auto target = kernel.spawn_unit(Side::Red, "Aircraft", 0.0, kTargetNorthM, kAltitudeM, 180.0,
                                    0.0, 0.0, 0.0, -200.0, 0.0);
    REQUIRE(shooter.is_valid());
    REQUIRE(target.is_valid());
    {
        auto lease = kernel.acquire_world_lease();
        auto shooter_e = lease.world().entity(shooter.id());
        shooter_e.set<ContactList>({{seen(target.id(), kTargetNorthM, 0.0, 1.0)}});
        shooter_e.set<Ammo>({4, 4});
    }
    auto missile = kernel.fire_missile(shooter.id(), target.id());
    REQUIRE(missile.is_valid());
    return {shooter.id(), target.id(), missile.id()};
}

// A released expendable parked `north_offset_m` north of the target.
std::uint64_t place_decoy(SimulationKernel &kernel, DecoyKind kind, std::uint64_t owner_id,
                          double north_offset_m, double signature = 500.0) {
    auto lease = kernel.acquire_world_lease();
    flecs::world &world = lease.world();
    auto decoy =
        world.entity()
            .set<Transform>({0.0, kTargetNorthM + north_offset_m, kAltitudeM, 0.0, 0.0, 0.0})
            .set<Decoy>({kind, owner_id, 0.0, signature});
    stamp_stable_serial(decoy);
    return decoy.id();
}

void set_missile_contacts(SimulationKernel &kernel, std::uint64_t missile_id,
                          std::vector<Detection> contacts) {
    auto lease = kernel.acquire_world_lease();
    lease.world().entity(missile_id).set<ContactList>({std::move(contacts)});
}

Missile missile_state(SimulationKernel &kernel, std::uint64_t missile_id) {
    auto lease = kernel.acquire_world_lease();
    const Missile *missile = lease.world().entity(missile_id).get<Missile>();
    REQUIRE(missile != nullptr);
    return *missile;
}

bool guide(SimulationKernel &kernel) {
    return kernel.run_exact_stage_direct("MissileGuidance");
}

// One draw with an even signal split (p = 0.5): reports whether the flare
// captured an IR seeker with zero rejection.
bool even_split_capture(SimulationKernel &kernel, unsigned seed) {
    const Engagement e = launch(kernel, seed, SensorType::Infrared, 0.0, 150.0);
    const std::uint64_t flare = place_decoy(kernel, DecoyKind::Flare, e.target, 50.0);
    set_missile_contacts(kernel, e.missile,
                         {seen(e.target, 4800.0, 0.0, 1.0), seen(flare, 4850.0, 0.0, 1.0)});
    REQUIRE(guide(kernel));
    const Missile missile = missile_state(kernel, e.missile);
    REQUIRE(missile.evaluated_decoy_serials.size() == 1);
    return missile.target_id == flare;
}

} // namespace

TEST_SUITE("air_ew_decoy") {
    TEST_CASE("decoy discrimination reaches the missile through the tuning path") {
        SimulationKernel kernel;
        const Engagement authored = launch(kernel, 21, SensorType::Infrared, 0.4, 150.0);
        Missile missile = missile_state(kernel, authored.missile);
        CHECK(missile.seeker_decoy_rejection == doctest::Approx(0.4));
        CHECK(missile.seeker_resolution_cell_m == doctest::Approx(150.0));

        const Engagement unauthored = launch(kernel, 22, SensorType::Infrared, kNaN, kNaN);
        missile = missile_state(kernel, unauthored.missile);
        CHECK(missile.seeker_decoy_rejection == doctest::Approx(1.0));
        CHECK(missile.seeker_resolution_cell_m == doctest::Approx(0.0));
    }

    TEST_CASE("a flare in the target's cell captures an IR seeker with zero rejection") {
        SimulationKernel kernel;
        const Engagement e = launch(kernel, 31, SensorType::Infrared, 0.0, 150.0);
        const std::uint64_t flare = place_decoy(kernel, DecoyKind::Flare, e.target, 50.0);
        // The target itself is not seen this frame, so s_t = 0 and p = 1.
        set_missile_contacts(kernel, e.missile, {seen(flare, 4850.0, 0.0, 1.0)});
        REQUIRE(guide(kernel));
        const Missile missile = missile_state(kernel, e.missile);
        CHECK(missile.target_id == flare);
        CHECK(missile.evaluated_decoy_serials.size() == 1);
    }

    TEST_CASE("perfect rejection, the default, never captures") {
        SimulationKernel kernel;
        const Engagement e = launch(kernel, 32, SensorType::Infrared, kNaN, 150.0);
        const std::uint64_t flare = place_decoy(kernel, DecoyKind::Flare, e.target, 50.0);
        set_missile_contacts(kernel, e.missile, {seen(flare, 4850.0, 0.0, 1.0)});
        REQUIRE(guide(kernel));
        const Missile missile = missile_state(kernel, e.missile);
        CHECK(missile.seeker_decoy_rejection == doctest::Approx(1.0));
        CHECK(missile.target_id == e.target);
        CHECK(missile.evaluated_decoy_serials.empty());
    }

    TEST_CASE("decoy physics must match the seeker") {
        SimulationKernel kernel;
        {
            const Engagement e = launch(kernel, 33, SensorType::Infrared, 0.0, 150.0);
            const std::uint64_t chaff = place_decoy(kernel, DecoyKind::Chaff, e.target, 50.0);
            set_missile_contacts(kernel, e.missile, {seen(chaff, 4850.0, 0.0, 1.0)});
            REQUIRE(guide(kernel));
            CHECK(missile_state(kernel, e.missile).target_id == e.target);
        }
        {
            const Engagement e = launch(kernel, 34, SensorType::Radar, 0.0, 300.0);
            const std::uint64_t flare = place_decoy(kernel, DecoyKind::Flare, e.target, 50.0);
            set_missile_contacts(kernel, e.missile, {seen(flare, 4850.0, 0.0, 1.0)});
            REQUIRE(guide(kernel));
            CHECK(missile_state(kernel, e.missile).target_id == e.target);
        }
        {
            // The matching pairing does capture, so the two checks above are
            // not vacuous.
            const Engagement e = launch(kernel, 35, SensorType::Radar, 0.0, 300.0);
            const std::uint64_t chaff = place_decoy(kernel, DecoyKind::Chaff, e.target, 50.0);
            set_missile_contacts(kernel, e.missile, {seen(chaff, 4850.0, 0.0, 1.0)});
            REQUIRE(guide(kernel));
            CHECK(missile_state(kernel, e.missile).target_id == chaff);
        }
    }

    TEST_CASE("a decoy outside the cell, outside the FOV or released by a non-target is ignored") {
        SimulationKernel kernel;
        {
            const Engagement e = launch(kernel, 41, SensorType::Infrared, 0.0, 150.0);
            const std::uint64_t far = place_decoy(kernel, DecoyKind::Flare, e.target, 400.0);
            set_missile_contacts(kernel, e.missile, {seen(far, 5200.0, 0.0, 1.0)});
            REQUIRE(guide(kernel));
            CHECK(missile_state(kernel, e.missile).target_id == e.target);
        }
        {
            const Engagement e = launch(kernel, 42, SensorType::Infrared, 0.0, 150.0);
            const std::uint64_t flare = place_decoy(kernel, DecoyKind::Flare, e.target, 50.0);
            // Seeker FOV is 90 deg total: a 60 deg bearing is outside it.
            set_missile_contacts(kernel, e.missile, {seen(flare, 4850.0, 60.0, 1.0)});
            REQUIRE(guide(kernel));
            const Missile missile = missile_state(kernel, e.missile);
            CHECK(missile.target_id == e.target);
            CHECK(missile.evaluated_decoy_serials.empty());
        }
        {
            const Engagement e = launch(kernel, 43, SensorType::Infrared, 0.0, 150.0);
            const std::uint64_t foreign = place_decoy(kernel, DecoyKind::Flare, e.shooter, 50.0);
            set_missile_contacts(kernel, e.missile, {seen(foreign, 4850.0, 0.0, 1.0)});
            REQUIRE(guide(kernel));
            const Missile missile = missile_state(kernel, e.missile);
            CHECK(missile.target_id == e.target);
            CHECK(missile.evaluated_decoy_serials.empty());
        }
        {
            // A decoy reported only through a data link is not the seeker's own.
            const Engagement e = launch(kernel, 44, SensorType::Infrared, 0.0, 150.0);
            const std::uint64_t flare = place_decoy(kernel, DecoyKind::Flare, e.target, 50.0);
            Detection linked = seen(flare, 4850.0, 0.0, 1.0);
            linked.local_sensor_hit = false;
            set_missile_contacts(kernel, e.missile, {linked});
            REQUIRE(guide(kernel));
            CHECK(missile_state(kernel, e.missile).target_id == e.target);
        }
        {
            // Zero resolution cell: decoys are never eligible.
            const Engagement e = launch(kernel, 45, SensorType::Infrared, 0.0, 0.0);
            const std::uint64_t flare = place_decoy(kernel, DecoyKind::Flare, e.target, 0.0);
            set_missile_contacts(kernel, e.missile, {seen(flare, 4800.0, 0.0, 1.0)});
            REQUIRE(guide(kernel));
            CHECK(missile_state(kernel, e.missile).target_id == e.target);
        }
    }

    TEST_CASE("the same episode seed gives the same seduction outcome across kernels") {
        std::vector<bool> first;
        std::vector<bool> second;
        for (unsigned seed = 100; seed < 124; ++seed) {
            SimulationKernel a;
            SimulationKernel b;
            first.push_back(even_split_capture(a, seed));
            second.push_back(even_split_capture(b, seed));
        }
        CHECK(first == second);
        // p = 0.5 per seed: the sweep must contain both outcomes.
        CHECK(std::count(first.begin(), first.end(), true) > 0);
        CHECK(std::count(first.begin(), first.end(), false) > 0);
    }

    TEST_CASE("each decoy is drawn at most once per missile") {
        SimulationKernel kernel;
        const Engagement e = launch(kernel, 51, SensorType::Infrared, 0.0, 150.0);
        const std::uint64_t flare = place_decoy(kernel, DecoyKind::Flare, e.target, 50.0);
        // First eligible frame: the target dominates, p = 1e-9.
        set_missile_contacts(kernel, e.missile,
                             {seen(e.target, 4800.0, 0.0, 1.0e9), seen(flare, 4850.0, 0.0, 1.0)});
        REQUIRE(guide(kernel));
        Missile missile = missile_state(kernel, e.missile);
        REQUIRE(missile.target_id == e.target);
        REQUIRE(missile.evaluated_decoy_serials.size() == 1);

        // Later frames would give p = 1 (target unseen), but the flare has
        // already had its draw against this missile.
        set_missile_contacts(kernel, e.missile, {seen(flare, 4850.0, 0.0, 1.0)});
        for (int frame = 0; frame < 5; ++frame) {
            REQUIRE(guide(kernel));
        }
        missile = missile_state(kernel, e.missile);
        CHECK(missile.target_id == e.target);
        CHECK(missile.evaluated_decoy_serials.size() == 1);

        // A second flare is a new decoy and gets its own draw.
        const std::uint64_t second = place_decoy(kernel, DecoyKind::Flare, e.target, -40.0);
        set_missile_contacts(kernel, e.missile, {seen(second, 4760.0, 0.0, 1.0)});
        REQUIRE(guide(kernel));
        missile = missile_state(kernel, e.missile);
        CHECK(missile.target_id == second);
        CHECK(missile.evaluated_decoy_serials.size() == 2);
    }

    TEST_CASE("a seduced missile never damages its decoy or credits a kill") {
        SimulationKernel kernel;
        const Engagement e = launch(kernel, 61, SensorType::Infrared, 0.0, 150.0);
        const std::uint64_t flare = place_decoy(kernel, DecoyKind::Flare, e.target, 50.0);
        set_missile_contacts(kernel, e.missile, {seen(flare, 4850.0, 0.0, 1.0)});
        REQUIRE(guide(kernel));
        REQUIRE(missile_state(kernel, e.missile).target_id == flare);

        Score score_before{};
        {
            auto lease = kernel.acquire_world_lease();
            flecs::world &world = lease.world();
            // Give the decoy hit points so any damage would be visible, and
            // put the missile on top of it.
            world.entity(flare).set<Health>({100.0, 100.0});
            const Transform *decoy_t = world.entity(flare).get<Transform>();
            REQUIRE(decoy_t != nullptr);
            Transform *missile_t = world.entity(e.missile).get_mut<Transform>();
            REQUIRE(missile_t != nullptr);
            missile_t->x = decoy_t->x;
            missile_t->y = decoy_t->y;
            missile_t->z = decoy_t->z;
            const Score *score = world.entity(e.shooter).get<Score>();
            REQUIRE(score != nullptr);
            score_before = *score;
        }
        for (int frame = 0; frame < 3; ++frame) {
            REQUIRE(kernel.run_exact_stage_direct("ProximityFuze"));
        }

        auto lease = kernel.acquire_world_lease();
        flecs::world &world = lease.world();
        REQUIRE(world.entity(flare).is_alive());
        CHECK(world.entity(flare).get<Health>()->current_hp == doctest::Approx(100.0));
        REQUIRE(world.entity(e.missile).is_alive());
        CHECK(world.entity(e.missile).get<Missile>()->active);
        const Score *score = world.entity(e.shooter).get<Score>();
        REQUIRE(score != nullptr);
        CHECK(score->hits_landed == score_before.hits_landed);
        CHECK(score->kills_confirmed == score_before.kills_confirmed);
        CHECK(score->total_reward == doctest::Approx(score_before.total_reward));
    }

    TEST_CASE("dispensers spawn typed decoys with data or historical-default signatures") {
        SimulationKernel kernel;
        kernel.reset(71);
        auto owner = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, kAltitudeM, 0.0, 0.0, 0.0,
                                       0.0, 200.0, 0.0);
        REQUIRE(owner.is_valid());
        {
            auto lease = kernel.acquire_world_lease();
            Countermeasures cms{};
            cms.chaff_count = 2;
            cms.flare_count = 2;
            cms.release_interval = 0.5;
            cms.flare_ir_intensity = 750.0; // authored
            cms.chaff_lifetime_s = 12.0;    // authored; the others take the defaults
            lease.world().entity(owner.id()).set<Countermeasures>(cms);
        }
        PilotAction action{};
        action.active = true;
        action.program_chaff = true;
        action.program_flare = true;
        kernel.set_pilot_action(owner.id(), action);
        REQUIRE(kernel.run_exact_stage_direct("EW_Release_Chaff"));
        REQUIRE(kernel.run_exact_stage_direct("EW_Release_Flare"));

        auto lease = kernel.acquire_world_lease();
        int chaff = 0;
        int flares = 0;
        lease.world().each([&](flecs::entity e, const Decoy &decoy) {
            CHECK(decoy.owner_id == owner.id());
            CHECK(decoy.release_time_s >= 0.0);
            CHECK(e.has<StableEntitySerial>());
            const Lifetime *lifetime = e.get<Lifetime>();
            REQUIRE(lifetime != nullptr);
            if (decoy.kind == DecoyKind::Chaff) {
                ++chaff;
                CHECK(decoy.signature == doctest::Approx(kDefaultChaffRcsM2));
                const RCSProfile *rcs = e.get<RCSProfile>();
                REQUIRE(rcs != nullptr);
                CHECK(rcs->frontal_rcs == doctest::Approx(kDefaultChaffRcsM2));
                CHECK(lifetime->max_age == doctest::Approx(12.0));
            } else {
                ++flares;
                CHECK(decoy.signature == doctest::Approx(750.0));
                CHECK(lifetime->max_age == doctest::Approx(kDefaultFlareLifetimeS));
            }
        });
        CHECK(chaff == 1);
        CHECK(flares == 1);
    }

    TEST_CASE("an IR sensor sees a flare at its intensity and does not see chaff") {
        SimulationKernel kernel;
        kernel.reset(81);
        auto owner = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, kAltitudeM, 0.0, 0.0, 0.0,
                                       0.0, 200.0, 0.0);
        REQUIRE(owner.is_valid());
        auto lease = kernel.acquire_world_lease();
        flecs::world &world = lease.world();
        auto make_decoy = [&](DecoyKind kind, double x, double signature) {
            auto decoy = world.entity()
                             .set<Transform>({x, 2000.0, kAltitudeM, 0.0, 0.0, 0.0})
                             .set<Velocity>({0.0, 0.0, 0.0})
                             .set<Decoy>({kind, 0, 0.0, signature})
                             .set<KeyEntity>({UnitType::Unknown});
            stamp_stable_serial(decoy);
            return decoy;
        };
        const auto flare = make_decoy(DecoyKind::Flare, 0.0, 640.0);
        const auto chaff = make_decoy(DecoyKind::Chaff, 300.0, 50.0);

        Sensor ir{};
        ir.type = static_cast<int>(SensorType::Infrared);
        ir.max_range = 20000.0;
        ir.fov_deg = 120.0;
        ir.detection_prob = 1.0;
        // A steep range power keeps Pd at 1 inside a short range.
        ir.range_power = 50.0;
        ir.reference_snr_db = 40.0;
        ir.reference_range_m = 20000.0;
        ir.reference_rcs_m2 = 5.0;
        ir.pfa = 1.0e-6;

        const Transform owner_t = *world.entity(owner.id()).get<Transform>();
        ContactList contacts;
        auto model = make_default_sensor_model();
        model->scan(world, world.entity(owner.id()), owner_t, ir, contacts, 0.0);

        const auto find = [&](std::uint64_t id) {
            return std::find_if(contacts.contacts.begin(), contacts.contacts.end(),
                                [&](const Detection &det) { return det.target_id == id; });
        };
        const auto flare_det = find(flare.id());
        REQUIRE(flare_det != contacts.contacts.end());
        const double dist_sq = 2000.0 * 2000.0;
        CHECK(flare_det->signal_strength == doctest::Approx(640.0 / dist_sq));
        CHECK(find(chaff.id()) == contacts.contacts.end());
    }
}
