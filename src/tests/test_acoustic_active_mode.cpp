#include "components/basic/common.h"
#include "components/basic/stable_identity.h"
#include "components/domains/naval/platform/submarine_platform.h"
#include "components/physics/dynamics.h"
#include "components/systems/sonar.h"
#include "content/unit_definition_loader.h"
#include "core/interfaces/acoustic_model.h"
#include "systems/system_contribution_registry.h"

#include <doctest/doctest.h>

#include <filesystem>
#include <fstream>
#include <memory>
#include <string>
#include <vector>

namespace {

std::size_t run_scan(int mode) {
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
        .set<Velocity>({0.0, 0.0, 0.0})
        .set<SubmarinePlatform>({});

    Sonar sonar{};
    sonar.max_range_m = 5000.0;
    sonar.detection_threshold_db = -100.0;
    sonar.ambient_noise_db = 0.0;
    sonar.directivity_gain_db = 0.0;
    sonar.baffle_exclusion_deg = 0.0;
    sonar.active_ping_source_level_db = 235.0;
    sonar.mode = mode;
    sonar.passive_only = false;

    ContactList contacts{};
    const std::unique_ptr<IAcousticModel> model = make_default_acoustic_model();
    model->scan(world, owner, *owner.get<Transform>(), sonar, contacts, 0.0);
    return contacts.contacts.size();
}

} // namespace

TEST_CASE("active sonar does not use the passive acoustic model") {
    CHECK(run_scan(static_cast<int>(SonarMode::Active)) == 0);
    CHECK(run_scan(static_cast<int>(SonarMode::Passive)) == 1);
}

TEST_CASE("sonar content rejects unsupported modes") {
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / "ef_invalid_sonar_mode_test.json";
    {
        std::ofstream definition(path);
        definition << R"json({
  "name": "Invalid_Sonar_Mode",
  "type": "Ship",
  "sonar": {"mode": "Bistatic"}
})json";
    }

    std::vector<UnitDefinition> definitions;
    std::string error;
    CHECK_FALSE(load_unit_definitions_json(path.string(), definitions, &error));
    CHECK(error.find("sonar.mode") != std::string::npos);
    CHECK(error.find("Passive") != std::string::npos);
    std::filesystem::remove(path);
}
