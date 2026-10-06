// RF values in this suite are synthetic test inputs, not platform calibrations.
#include "core/engine/simulation_kernel.h"
#include "core/engine/state_transfer_component_reflection.h"
#include "core/interfaces/sensor_model.h"
#include "components/systems/ew.h"
#include "components/systems/rf_signal.h"
#include "components/systems/sensor.h"
#include "components/combat/common/weapon_common.h"
#include "content/unit_definition_loader.h"

#include <doctest/doctest.h>
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <limits>

namespace {
Sensor esm_probe() {
    Sensor s = make_unit_definition_default_sensor();
    s.type = static_cast<int>(SensorType::ESM);
    s.max_range = 1.0e6;
    s.fov_deg = 360.0;
    s.range_power = 8.0;
    s.reference_range_m = 1.0e6;
    s.reference_snr_db = 100.0;
    s.velocity_noise_std = 0.0;
    return s;
}
Sensor rf_radar(double watts = 100.0, double mhz = 1000.0) {
    Sensor s = esm_probe();
    s.type = static_cast<int>(SensorType::Radar);
    s.rf_eirp_watts = watts;
    s.rf_frequency_mhz = mhz;
    s.rf_bandwidth_mhz = 20.0;
    return s;
}
ESMReceiver strict_receiver() {
    ESMReceiver r;
    r.require_rf_contract = true;
    r.frequency_min_mhz = 900.0;
    r.frequency_max_mhz = 1100.0;
    r.sensitivity_dbm = -85.0;
    r.max_detection_range_m = 200000.0;
    return r;
}
struct Fixture {
    SimulationKernel kernel;
    std::uint64_t owner, emitter;
    Fixture() {
        kernel.reset(161);
        owner = kernel.spawn_unit(Side::Blue, "Aircraft", 0, 0, 5000, 0, 0, 0, 0, 0, 0).id();
        emitter = kernel.spawn_unit(Side::Red, "Aircraft", 0, 10000, 5000, 180, 0, 0, 0, 0, 0).id();
        auto lease = kernel.acquire_world_lease();
        lease.world().entity(owner).set<ESMReceiver>(strict_receiver()).remove<Sensor>().remove<MountedSensors>();
        lease.world().entity(emitter).set<Sensor>(rf_radar()).remove<MountedSensors>();
    }
    ContactList scan(double time = 0.0) {
        auto lease = kernel.acquire_world_lease();
        auto entity = lease.world().entity(owner);
        ContactList contacts;
        lease.world().get<SensorModelRef>()->model->scan(
            lease.world(), entity, *entity.get<Transform>(), esm_probe(), contacts, time);
        return contacts;
    }
    ESMReceiver receiver() {
        auto lease = kernel.acquire_world_lease();
        return *lease.world().entity(owner).get<ESMReceiver>();
    }
    void receiver(ESMReceiver r) {
        auto lease = kernel.acquire_world_lease();
        lease.world().entity(owner).set<ESMReceiver>(r);
    }
    void radar(Sensor s) {
        auto lease = kernel.acquire_world_lease();
        lease.world().entity(emitter).set<Sensor>(s);
    }
};
}

TEST_SUITE("air_ew_esm") {
    TEST_CASE("RF sensitivity and band gates deny both emitter and passive contact") {
        Fixture f;
        REQUIRE(f.scan().contacts.size() == 1);
        REQUIRE(f.receiver().detections.size() == 1);
        const auto d = f.receiver().detections.front();
        CHECK(d.has_rf_power);
        CHECK(d.received_power_dbm == doctest::Approx(-62.4477832219));
        CHECK(d.sensitivity_margin_db == doctest::Approx(22.5522167781));
        CHECK(d.classification_known);
        CHECK_FALSE(d.is_radar_lock); // An ordinary radar strobe never implies STT.
        CHECK_FALSE(d.is_missile_guidance);
        f.receiver(strict_receiver());
        f.radar(rf_radar(0.01)); // -102.45 dBm, below -85 dBm.
        CHECK(f.scan().contacts.empty());
        CHECK(f.receiver().detections.empty());
        f.radar(rf_radar(100.0, 3000.0));
        CHECK(f.scan().contacts.empty());
        CHECK(f.receiver().detections.empty());
        auto r = strict_receiver();
        r.sensitivity_dbm = d.received_power_dbm;
        f.receiver(r);
        f.radar(rf_radar());
        CHECK(f.scan().contacts.size() == 1); // Threshold equality is admitted.
        CHECK(rf_band_overlap(1110.0, 20.0, 1000.0, 200.0) == 0.0); // Touching edge only.
    }

    TEST_CASE("a rejected inline radar does not hide an in-band mounted radar") {
        Fixture f;
        f.radar(rf_radar(100.0, 3000.0));
        {
            auto lease = f.kernel.acquire_world_lease();
            lease.world().entity(f.emitter).set<MountedSensors>({{{rf_radar(), "InBand"}}});
        }
        REQUIRE(f.scan().contacts.size() == 1);
        REQUIRE(f.receiver().detections.size() == 1);
        CHECK(f.receiver().detections.front().received_power_dbm == doctest::Approx(-62.4477832219));
    }

    TEST_CASE("legacy proxy is explicit and strict receivers reject missing RF data") {
        Fixture f;
        Sensor legacy = rf_radar();
        legacy.rf_eirp_watts = legacy.rf_frequency_mhz = legacy.rf_bandwidth_mhz = 0.0;
        f.radar(legacy);
        CHECK(f.scan().contacts.empty());
        auto r = strict_receiver();
        r.require_rf_contract = false;
        f.receiver(r);
        REQUIRE(f.scan().contacts.size() == 1);
        CHECK_FALSE(f.receiver().detections.front().has_rf_power);
        CHECK(f.receiver().detections.front().signal_strength == doctest::Approx(0.01));
    }

    TEST_CASE("same-time radar strobes prefer physical RF power over the legacy proxy") {
        Fixture f;
        Sensor weak = rf_radar(1.0);
        weak.reference_range_m = 2.0e6;
        f.radar(weak); // A larger legacy proxy must not beat stronger RF power.
        {
            auto lease = f.kernel.acquire_world_lease();
            lease.world().entity(f.emitter).set<MountedSensors>({{{rf_radar(), "StrongRF"}}});
        }
        REQUIRE(f.scan().contacts.size() == 1);
        REQUIRE(f.receiver().detections.size() == 1);
        CHECK(f.receiver().detections.front().received_power_dbm == doctest::Approx(-62.4477832219));
        CHECK(f.receiver().detections.front().confirmation_count == 1);
        auto r = strict_receiver();
        r.require_rf_contract = false;
        f.receiver(r);
        Sensor legacy = weak;
        legacy.rf_eirp_watts = legacy.rf_frequency_mhz = legacy.rf_bandwidth_mhz = 0.0;
        f.radar(legacy);
        f.scan();
        REQUIRE(f.receiver().detections.size() == 1);
        CHECK(f.receiver().detections.front().has_rf_power);
        CHECK(f.receiver().detections.front().received_power_dbm == doctest::Approx(-62.4477832219));
    }

    TEST_CASE("confirmation counts distinct scan times and expires before reacquisition") {
        Fixture f;
        auto r = strict_receiver();
        r.memory_s = 2.0;
        r.confirmation_scans = 2;
        f.receiver(r);
        REQUIRE(f.scan(0.0).contacts.size() == 1);
        CHECK(f.receiver().detections.front().confidence == doctest::Approx(0.5));
        CHECK_FALSE(f.receiver().detections.front().classification_known);
        f.scan(0.0); // Multiple sensors at the same instant are one confirmation.
        CHECK(f.receiver().detections.front().confirmation_count == 1);
        f.radar(rf_radar(10.0));
        f.scan(1.0);
        CHECK(f.receiver().detections.front().confidence == 1.0);
        CHECK(f.receiver().detections.front().classification_known);
        CHECK(f.receiver().detections.front().received_power_dbm == doctest::Approx(-72.4477832219));
        // Newer weaker scans replace the prior stronger measurement.
        f.scan(3.01);
        CHECK(f.receiver().detections.front().confirmation_count == 1);
        CHECK(f.receiver().detections.front().confidence == doctest::Approx(0.5));
        f.scan(0.0); // Rewound clock cannot retain future evidence.
        CHECK(f.receiver().detections.front().observed_time_s == 0.0);
    }

    TEST_CASE("RF jammer requires transmit and beam coverage; classification is opt out") {
        Fixture f;
        Jammer pod{true, 1000.0, 20.0, JammingType::NoiseBarrage, 60.0};
        pod.rf_eirp_watts = 100.0;
        pod.rf_frequency_mhz = 1000.0;
        auto r = strict_receiver();
        r.classify_emitters = false;
        f.receiver(r);
        {
            auto lease = f.kernel.acquire_world_lease();
            lease.world().entity(f.emitter).remove<Sensor>().set<Jammer>(pod);
        }
        REQUIRE(f.scan().contacts.size() == 1);
        auto obs = f.kernel.get_agent_observation(f.owner);
        REQUIRE(obs.esm_detections.size() == 1);
        CHECK_FALSE(obs.esm_detections.front().classification_known);
        CHECK_FALSE(obs.esm_detections.front().is_jammer);
        CHECK_FALSE(obs.esm_detections.front().is_lock);
        CHECK_FALSE(obs.esm_detections.front().is_guidance);
        {
            auto lease = f.kernel.acquire_world_lease();
            auto &d = lease.world().entity(f.owner).get_mut<ESMReceiver>()->detections.front();
            d.is_radar_lock = d.is_missile_guidance = true;
        }
        // An unclassified imported row cannot bypass the public RWR mask.
        obs = f.kernel.get_agent_observation(f.owner);
        REQUIRE(obs.rwr_warnings.size() == 1);
        CHECK_FALSE(obs.rwr_warnings.front().is_lock);
        CHECK_FALSE(obs.rwr_warnings.front().is_launch);
        f.receiver(strict_receiver());
        {
            auto lease = f.kernel.acquire_world_lease();
            lease.world().entity(f.emitter).get_mut<Transform>()->heading = 0.0;
        }
        CHECK(f.scan().contacts.empty());
        {
            auto lease = f.kernel.acquire_world_lease();
            lease.world().entity(f.emitter).get_mut<Transform>()->heading = 180.0;
            lease.world().entity(f.emitter).get_mut<Jammer>()->is_active = false;
        }
        CHECK(f.scan().contacts.empty());
    }

    TEST_CASE("coasting ESM evidence has age and cannot assert current RWR lock or launch") {
        Fixture f;
        auto r = strict_receiver();
        r.memory_s = 0.5;
        f.receiver(r);
        REQUIRE(f.scan().contacts.size() == 1);
        {
            auto lease = f.kernel.acquire_world_lease();
            // Exercise projection separately from the existing missile-emitter classifier.
            auto *esm = lease.world().entity(f.owner).get_mut<ESMReceiver>();
            esm->detections.front().is_radar_lock = true;
            esm->detections.front().is_missile_guidance = true;
            lease.world().entity(f.emitter).remove<Sensor>();
        }
        REQUIRE(f.kernel.get_agent_observation(f.owner).rwr_warnings.size() == 1);
        f.kernel.set_time_step(0.25);
        f.kernel.step();
        auto coast = f.kernel.get_agent_observation(f.owner);
        REQUIRE(coast.esm_detections.size() == 1);
        CHECK(coast.esm_detections.front().age_s == doctest::Approx(0.25));
        CHECK(coast.rwr_warnings.empty());
        CHECK_FALSE(coast.esm_detections.front().is_lock);
        CHECK_FALSE(coast.esm_detections.front().is_guidance);
        f.kernel.step();
        CHECK(f.kernel.get_agent_observation(f.owner).esm_detections.size() == 1);
        f.kernel.step();
        CHECK(f.kernel.get_agent_observation(f.owner).esm_detections.empty());
        CHECK(f.receiver().detections.empty());
        f.kernel.reset(161);
        CHECK(f.kernel.get_agent_observation(f.owner).esm_detections.empty());
    }


}
