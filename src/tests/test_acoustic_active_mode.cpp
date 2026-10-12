#include "components/basic/common.h"
#include "components/basic/stable_identity.h"
#include "components/domains/naval/platform/submarine_platform.h"
#include "components/physics/dynamics.h"
#include "components/systems/sonar.h"
#include "content/unit_definition_loader.h"
#include "core/interfaces/acoustic_model.h"
#include "systems/system_contribution_registry.h"
#include "systems/systems/sonar_system.h"

#include <doctest/doctest.h>
#include <nlohmann/json.hpp>

#include <filesystem>
#include <fstream>
#include <memory>
#include <string>
#include <vector>

namespace {

struct ScanResult {
    std::size_t contact_count = 0;
    AcousticScanStatus status = AcousticScanStatus::NotScanned;
};

ScanResult run_scan(int mode) {
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
    const auto status = model->scan(world, owner, *owner.get<Transform>(), sonar, contacts, 0.0);
    return {contacts.contacts.size(), status};
}

} // namespace

TEST_CASE("active sonar does not use the passive acoustic model") {
    const auto active = run_scan(static_cast<int>(SonarMode::Active));
    CHECK(active.contact_count == 0);
    CHECK(active.status == AcousticScanStatus::UnsupportedMode);
    const auto passive = run_scan(static_cast<int>(SonarMode::Passive));
    CHECK(passive.contact_count == 1);
    CHECK(passive.status == AcousticScanStatus::Completed);
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

TEST_CASE("loaded Active sonar is explicitly unsupported by the default provider") {
    const std::filesystem::path path =
        std::filesystem::temp_directory_path() / "ef_active_sonar_admission_test.json";
    {
        std::ofstream definition(path);
        definition << R"json({
  "name": "Active_Sonar_Module",
  "type": "Ship",
  "sonar": {"mode": "Active", "passive_only": false}
})json";
    }
    std::vector<UnitDefinition> definitions;
    std::string error;
    REQUIRE(load_unit_definitions_json(path.string(), definitions, &error));
    REQUIRE(definitions.size() == 1);
    CHECK(definitions.front().sonar.mode == static_cast<int>(SonarMode::Active));
    auto active = run_scan(definitions.front().sonar.mode);
    CHECK(active.status == AcousticScanStatus::UnsupportedMode);
    CHECK(active.contact_count == 0);
    CHECK(error.empty());
    std::filesystem::remove(path);
}

TEST_CASE("sonar caller distinguishes unsupported loaded modules from completed empty scans") {
    const auto path =
        std::filesystem::temp_directory_path() / "ef_sonar_provider_binding_test.json";
    for (bool mounted : {false, true}) {
        for (bool explicit_mode : {false, true}) {
            INFO("mounted=", mounted, " explicit_mode=", explicit_mode);
            nlohmann::json authored_sonar{{"passive_only", false}, {"scan_period_s", 0.0}};
            if (explicit_mode) authored_sonar["mode"] = "Active";
            nlohmann::json definition{{"name", "Sonar_Provider_Binding"}, {"type", "Ship"}};
            if (mounted) {
                definition["mounted_sonars"] =
                    nlohmann::json::array({{{"label", "ActiveMount"}, {"sonar", authored_sonar}}});
            } else {
                definition["sonar"] = authored_sonar;
            }
            {
                std::ofstream output(path);
                output << definition.dump();
            }
            std::vector<UnitDefinition> definitions;
            std::string error;
            REQUIRE(load_unit_definitions_json(path.string(), definitions, &error));
            REQUIRE(definitions.size() == 1);

            flecs::world world;
            runtime::systems::register_default_component_contributions(world);
            auto model = make_default_acoustic_model();
            world.set<AcousticModelRef>({model.get()});
            register_sonar_system(world);
            auto owner = world.entity().set<Transform>({}).set<ContactList>({});
            if (mounted)
                owner.set<MountedSonars>(definitions.front().mounted_sonars);
            else
                owner.set<Sonar>(definitions.front().sonar);
            world.progress(1.0);
            auto *sonar = mounted ? &owner.get_mut<MountedSonars>()->mounts.front().sonar
                                  : owner.get_mut<Sonar>();
            REQUIRE(sonar != nullptr);
            CHECK(sonar->last_scan_status == static_cast<int>(AcousticScanStatus::UnsupportedMode));
            CHECK(owner.get<ContactList>()->contacts.empty());
            // An admitted passive scan in the same empty world is Completed,
            // even though both attempts produce zero contacts.
            sonar->mode = static_cast<int>(SonarMode::Passive);
            world.progress(1.0);
            sonar = mounted ? &owner.get_mut<MountedSonars>()->mounts.front().sonar
                            : owner.get_mut<Sonar>();
            CHECK(sonar->last_scan_status == static_cast<int>(AcousticScanStatus::Completed));
            CHECK(owner.get<ContactList>()->contacts.empty());
        }
    }
    std::filesystem::remove(path);
}
