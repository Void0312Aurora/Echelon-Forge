#include "components/basic/common.h"
#include "components/basic/stable_identity.h"
#include "components/domains/naval/platform/submarine_platform.h"
#include "components/systems/sonar.h"
#include "components/systems/sensor.h"
#include "components/physics/dynamics.h"
#include "core/interfaces/acoustic_model.h"
#include "systems/system_contribution_registry.h"

#include <doctest/doctest.h>

namespace {

struct AcousticProbe {
    double snr_db = 0.0;
    std::size_t contacts = 0;
};

AcousticProbe run_passive_probe(double receiver_source_level_db, double target_speed_mps) {
    flecs::world world;
    runtime::systems::register_default_component_contributions(world);
    world.set<StableIdentityState>({3, 42});
    auto owner = world.entity()
                     .set<KeyEntity>({UnitType::Ship})
                     .set<StableEntitySerial>({1})
                     .set<Transform>({0.0, 0.0, -20.0, 0.0, 0.0, 0.0})
                     .set<Velocity>({0.0, 0.0, 0.0});
    world.entity()
        .set<KeyEntity>({UnitType::Submarine})
        .set<StableEntitySerial>({2})
        .set<Transform>({1000.0, 0.0, -60.0, 0.0, 0.0, 0.0})
        .set<Velocity>({target_speed_mps, 0.0, 0.0})
        .set<SubmarinePlatform>({});

    Sonar sonar{};
    sonar.max_range_m = 5000.0;
    sonar.detection_threshold_db = -100.0;
    sonar.ambient_noise_db = 0.0;
    sonar.directivity_gain_db = 0.0;
    sonar.baffle_exclusion_deg = 0.0;
    sonar.source_level_reference_db = receiver_source_level_db;
    sonar.source_level_speed_factor_db = receiver_source_level_db > 0.0 ? 8.0 : 0.0;
    sonar.passive_only = true;
    sonar.mode = static_cast<int>(SonarMode::Passive);

    ContactList contacts{};
    const std::unique_ptr<IAcousticModel> model = make_default_acoustic_model();
    model->scan(world, owner, *owner.get<Transform>(), sonar, contacts, 0.0);

    AcousticProbe out;
    out.contacts = contacts.contacts.size();
    if (!contacts.contacts.empty()) out.snr_db = contacts.contacts.front().snr_db;
    return out;
}

} // namespace

TEST_CASE("passive target source level is invariant to receiver source settings") {
    const AcousticProbe passive_receiver = run_passive_probe(0.0, 10.0);
    const AcousticProbe active_capable_receiver = run_passive_probe(235.0, 10.0);

    REQUIRE(passive_receiver.contacts == 1);
    REQUIRE(active_capable_receiver.contacts == 1);
    CHECK(active_capable_receiver.snr_db == doctest::Approx(passive_receiver.snr_db));
}

TEST_CASE("passive target source level follows target speed") {
    const AcousticProbe slow_target = run_passive_probe(0.0, 10.0);
    const AcousticProbe fast_target = run_passive_probe(0.0, 20.0);

    REQUIRE(slow_target.contacts == 1);
    REQUIRE(fast_target.contacts == 1);
    CHECK(fast_target.snr_db > slow_target.snr_db);
}
