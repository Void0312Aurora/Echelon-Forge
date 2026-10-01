// Native Air EW jamming mechanism tests: data-driven burn-through, the pod's
// main-beam geometry, spot power concentration, DRFM range deception, and the
// transmitting pod as an ESM emitter. Each case drives the composed sensor
// model directly with a deterministic probe radar, so the asserted boundary
// is the jamming geometry and not a detection-probability draw.

#include "core/engine/simulation_kernel.h"

#include "components/basic/common.h"
#include "components/systems/ew.h"
#include "components/systems/sensor.h"
#include "content/unit_definition.h"
#include "core/interfaces/sensor_model.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace {

constexpr const char *kDatabasePath = "examples/config/database";
constexpr double kAltitudeM = 5000.0;
// Gen-4 pod: 1 kW ERP, 60 deg main beam, burn-through reference reproducing
// the legacy K = 283000 calibration point.
constexpr double kPodErpW = 1000.0;
constexpr double kPodBeamDeg = 60.0;
constexpr double kGen4BurnThroughReferenceM = 20011.121907579294;

std::string resolve_database_path() {
    const std::filesystem::path source_relative{kDatabasePath};
    if (std::filesystem::exists(source_relative)) {
        return source_relative.string();
    }
    const std::filesystem::path build_relative = std::filesystem::path{".."} / source_relative;
    if (std::filesystem::exists(build_relative)) {
        return build_relative.string();
    }
    return source_relative.string();
}

// A noise-free radar whose single-scan Pd is 1 to double precision over the
// probed ranges: the reference SNR is far above threshold and the range
// roll-off exponent makes the range factor indistinguishable from 1.
Sensor probe_radar() {
    Sensor sensor = make_unit_definition_default_sensor();
    sensor.type = static_cast<int>(SensorType::Radar);
    sensor.max_range = 1.0e6;
    sensor.fov_deg = 360.0;
    sensor.detection_prob = 1.0;
    sensor.range_power = 8.0;
    sensor.reference_snr_db = 60.0;
    sensor.reference_range_m = 1.0e6;
    sensor.reference_rcs_m2 = 5.0;
    sensor.bearing_noise_std = 0.0;
    sensor.range_noise_std = 0.0;
    sensor.velocity_noise_std = 0.0;
    sensor.aspect_influence = 0.0;
    return sensor;
}

Sensor probe_esm() {
    Sensor sensor = probe_radar();
    sensor.type = static_cast<int>(SensorType::ESM);
    sensor.max_range = 200000.0;
    sensor.reference_range_m = 200000.0;
    sensor.bearing_only = true;
    return sensor;
}

Jammer gen4_pod(JammingType type) {
    Jammer pod{false, kPodErpW, 2000.0, type, kPodBeamDeg};
    pod.burn_through_reference_m = kGen4BurnThroughReferenceM;
    return pod;
}

struct Pair {
    std::uint64_t radar = 0;
    std::uint64_t jammer = 0;
};

// Blue radar at the origin facing north; Red pod platform due north at
// `range_m`, nose rotated `jammer_heading_deg` (180 points it at the radar).
Pair spawn_pair(SimulationKernel &kernel, double range_m, double jammer_heading_deg) {
    auto radar = kernel.spawn_unit(Side::Blue, "Aircraft", 0.0, 0.0, kAltitudeM, 0.0, 0.0, 0.0, 0.0,
                                   0.0, 0.0);
    auto jammer = kernel.spawn_unit(Side::Red, "Aircraft", 0.0, range_m, kAltitudeM,
                                    jammer_heading_deg, 0.0, 0.0, 0.0, 0.0, 0.0);
    REQUIRE(radar.is_valid());
    REQUIRE(jammer.is_valid());
    auto lease = kernel.acquire_world_lease();
    flecs::world &world = lease.world();
    world.entity(radar.id()).set<Transform>({0.0, 0.0, kAltitudeM, 0.0, 0.0, 0.0});
    world.entity(jammer.id())
        .set<Transform>({0.0, range_m, kAltitudeM, jammer_heading_deg, 0.0, 0.0});
    return {radar.id(), jammer.id()};
}

void install_pod(SimulationKernel &kernel, std::uint64_t entity_id, Jammer pod, bool transmit) {
    pod.is_active = transmit;
    auto lease = kernel.acquire_world_lease();
    lease.world().entity(entity_id).set<Jammer>(pod);
}

void move_jammer(SimulationKernel &kernel, std::uint64_t entity_id, double range_m,
                 double heading_deg) {
    auto lease = kernel.acquire_world_lease();
    lease.world().entity(entity_id).set<Transform>(
        {0.0, range_m, kAltitudeM, heading_deg, 0.0, 0.0});
}

// One scan of `sensor` from `owner_id` through the world's composed sensor
// model; returns the contact on `target_id`, if any.
std::optional<Detection> scan_for(SimulationKernel &kernel, std::uint64_t owner_id,
                                  std::uint64_t target_id, const Sensor &sensor) {
    auto lease = kernel.acquire_world_lease();
    flecs::world &world = lease.world();
    const SensorModelRef *model_ref = world.get<SensorModelRef>();
    REQUIRE(model_ref != nullptr);
    REQUIRE(model_ref->model != nullptr);
    flecs::entity owner = world.entity(owner_id);
    const Transform owner_t = *owner.get<Transform>();
    ContactList contacts;
    model_ref->model->scan(world, owner, owner_t, sensor, contacts, 0.0);
    const auto found =
        std::find_if(contacts.contacts.begin(), contacts.contacts.end(),
                     [&](const Detection &det) { return det.target_id == target_id; });
    if (found == contacts.contacts.end()) {
        return std::nullopt;
    }
    return *found;
}

std::vector<EmitterDetection> esm_detections(SimulationKernel &kernel, std::uint64_t owner_id) {
    auto lease = kernel.acquire_world_lease();
    const ESMReceiver *esm = lease.world().entity(owner_id).get<ESMReceiver>();
    REQUIRE(esm != nullptr);
    return esm->detections;
}

void clear_esm(SimulationKernel &kernel, std::uint64_t owner_id) {
    auto lease = kernel.acquire_world_lease();
    lease.world().entity(owner_id).get_mut<ESMReceiver>()->detections.clear();
}

void remove_radar(SimulationKernel &kernel, std::uint64_t entity_id) {
    auto lease = kernel.acquire_world_lease();
    flecs::entity entity = lease.world().entity(entity_id);
    entity.remove<Sensor>();
    entity.remove<MountedSensors>();
}

} // namespace

TEST_SUITE("air_ew_jamming") {
    TEST_CASE("gen4 burn-through data reproduces the legacy calibration point") {
        Jammer legacy = gen4_pod(JammingType::NoiseBarrage);
        legacy.burn_through_reference_m = 0.0;
        const Jammer gen4 = gen4_pod(JammingType::NoiseBarrage);
        for (const double rcs : {0.5, 5.0, 25.0}) {
            const double legacy_r_bt = kLegacyBurnThroughConstant * std::sqrt(rcs / kPodErpW);
            CHECK(jammer_burn_through_range_m(legacy, rcs) == doctest::Approx(legacy_r_bt));
            CHECK(jammer_burn_through_range_m(gen4, rcs) ==
                  doctest::Approx(legacy_r_bt).epsilon(0.01));
        }
        // The reference is the burn-through range against 5 m^2 at the pod ERP.
        CHECK(jammer_burn_through_range_m(gen4, kBurnThroughReferenceRcsM2) ==
              doctest::Approx(kGen4BurnThroughReferenceM));

        // The radar boundary itself: tracked just inside, denied just outside,
        // identically for the legacy constant and the data-driven pod.
        const double r_bt = jammer_burn_through_range_m(gen4, 5.0);
        for (const Jammer &pod : {legacy, gen4}) {
            SimulationKernel kernel;
            kernel.reset(41);
            const Pair pair = spawn_pair(kernel, 0.99 * r_bt, 180.0);
            install_pod(kernel, pair.jammer, pod, true);
            CHECK(scan_for(kernel, pair.radar, pair.jammer, probe_radar()).has_value());
            move_jammer(kernel, pair.jammer, 1.01 * r_bt, 180.0);
            CHECK_FALSE(scan_for(kernel, pair.radar, pair.jammer, probe_radar()).has_value());
        }
    }

    TEST_CASE("the shipped gen4 suite loads the burn-through, spot and DRFM data") {
        SimulationKernel kernel;
        kernel.reset(42);
        REQUIRE(kernel.load_database(resolve_database_path()));
        auto fighter = kernel.spawn_unit(Side::Blue, "F-16C_Block50", 0.0, 0.0, kAltitudeM, 0.0,
                                         0.0, 0.0, 0.0, 200.0, 0.0);
        REQUIRE(fighter.is_valid());
        auto lease = kernel.acquire_world_lease();
        const Jammer *pod = lease.world().entity(fighter.id()).get<Jammer>();
        REQUIRE(pod != nullptr);
        CHECK(pod->burn_through_reference_m == doctest::Approx(kGen4BurnThroughReferenceM));
        CHECK(pod->spot_power_gain == doctest::Approx(1.0));
        CHECK(pod->drfm_range_offset_m == doctest::Approx(0.0));
        CHECK(pod->effective_angle == doctest::Approx(kPodBeamDeg));
        CHECK(jammer_burn_through_range_m(*pod, 5.0) ==
              doctest::Approx(kLegacyBurnThroughConstant * std::sqrt(5.0 / kPodErpW)));
    }

    TEST_CASE("noise jamming suppresses only a radar inside the pod main beam") {
        SimulationKernel kernel;
        kernel.reset(43);
        // 40 km is well beyond the 20 km burn-through range.
        const Pair pair = spawn_pair(kernel, 40000.0, 180.0);
        install_pod(kernel, pair.jammer, gen4_pod(JammingType::NoiseBarrage), true);
        // Nose on the radar, and 25 deg off it: inside the 30 deg half-beam.
        CHECK_FALSE(scan_for(kernel, pair.radar, pair.jammer, probe_radar()).has_value());
        move_jammer(kernel, pair.jammer, 40000.0, 205.0);
        CHECK_FALSE(scan_for(kernel, pair.radar, pair.jammer, probe_radar()).has_value());
        // 35 deg off, beam-on, and tail-on: outside the beam, not suppressed.
        for (const double heading : {215.0, 90.0, 0.0}) {
            move_jammer(kernel, pair.jammer, 40000.0, heading);
            CHECK(scan_for(kernel, pair.radar, pair.jammer, probe_radar()).has_value());
        }

        // A pod without beam-width data radiates omnidirectionally.
        Jammer omni = gen4_pod(JammingType::NoiseBarrage);
        omni.effective_angle = 0.0;
        install_pod(kernel, pair.jammer, omni, true);
        CHECK_FALSE(scan_for(kernel, pair.radar, pair.jammer, probe_radar()).has_value());
    }

    TEST_CASE("spot power gain shrinks burn-through as the inverse square root") {
        const Jammer barrage = gen4_pod(JammingType::NoiseBarrage);
        Jammer spot = gen4_pod(JammingType::NoiseSpot);
        CHECK(jammer_burn_through_range_m(spot, 5.0) ==
              doctest::Approx(jammer_burn_through_range_m(barrage, 5.0)));
        spot.spot_power_gain = 4.0;
        const double r_bt_barrage = jammer_burn_through_range_m(barrage, 5.0);
        CHECK(jammer_burn_through_range_m(spot, 5.0) == doctest::Approx(0.5 * r_bt_barrage));
        // The gain belongs to the spot technique; barrage ignores it.
        Jammer barrage_with_gain = barrage;
        barrage_with_gain.spot_power_gain = 4.0;
        CHECK(jammer_burn_through_range_m(barrage_with_gain, 5.0) ==
              doctest::Approx(r_bt_barrage));

        // Between the two burn-through ranges, barrage burns through and the
        // gain-4 spot still denies the track.
        SimulationKernel kernel;
        kernel.reset(44);
        const Pair pair = spawn_pair(kernel, 0.75 * r_bt_barrage, 180.0);
        install_pod(kernel, pair.jammer, barrage, true);
        CHECK(scan_for(kernel, pair.radar, pair.jammer, probe_radar()).has_value());
        Jammer unit_gain_spot = gen4_pod(JammingType::NoiseSpot);
        install_pod(kernel, pair.jammer, unit_gain_spot, true);
        CHECK(scan_for(kernel, pair.radar, pair.jammer, probe_radar()).has_value());
        install_pod(kernel, pair.jammer, spot, true);
        CHECK_FALSE(scan_for(kernel, pair.radar, pair.jammer, probe_radar()).has_value());
        move_jammer(kernel, pair.jammer, 0.45 * r_bt_barrage, 180.0);
        CHECK(scan_for(kernel, pair.radar, pair.jammer, probe_radar()).has_value());
    }

    TEST_CASE("drfm displaces the reported range beyond burn-through only") {
        constexpr double kOffsetM = 3000.0;
        const double r_bt = jammer_burn_through_range_m(gen4_pod(JammingType::DeceptionDRFM), 5.0);
        const double beyond_m = 2.0 * r_bt;
        const double inside_m = 0.5 * r_bt;

        SimulationKernel kernel;
        kernel.reset(45);
        const Pair pair = spawn_pair(kernel, beyond_m, 180.0);
        const auto clear = scan_for(kernel, pair.radar, pair.jammer, probe_radar());
        REQUIRE(clear.has_value());
        CHECK(clear->range == doctest::Approx(beyond_m));

        // Offset 0: the technique is admitted but inert.
        install_pod(kernel, pair.jammer, gen4_pod(JammingType::DeceptionDRFM), true);
        const auto inert = scan_for(kernel, pair.radar, pair.jammer, probe_radar());
        REQUIRE(inert.has_value());
        CHECK(inert->range == clear->range);
        CHECK(inert->bearing == clear->bearing);

        Jammer deceiving = gen4_pod(JammingType::DeceptionDRFM);
        deceiving.drfm_range_offset_m = kOffsetM;
        install_pod(kernel, pair.jammer, deceiving, true);
        const auto deceived = scan_for(kernel, pair.radar, pair.jammer, probe_radar());
        REQUIRE(deceived.has_value());
        CHECK(deceived->range == doctest::Approx(beyond_m + kOffsetM));
        CHECK(deceived->bearing == doctest::Approx(clear->bearing));

        // Outside the beam the radar sees the true range.
        move_jammer(kernel, pair.jammer, beyond_m, 0.0);
        const auto off_beam = scan_for(kernel, pair.radar, pair.jammer, probe_radar());
        REQUIRE(off_beam.has_value());
        CHECK(off_beam->range == doctest::Approx(beyond_m));

        // Inside burn-through the skin return wins over the false target.
        move_jammer(kernel, pair.jammer, inside_m, 180.0);
        const auto burned = scan_for(kernel, pair.radar, pair.jammer, probe_radar());
        REQUIRE(burned.has_value());
        CHECK(burned->range == doctest::Approx(inside_m));
    }

    TEST_CASE("a transmitting pod is an esm emitter and a standby pod is not") {
        SimulationKernel kernel;
        kernel.reset(46);
        // The ESM receiver is the radar-side aircraft; the pod platform carries
        // no radar, so the pod is its only emitter.
        const Pair pair = spawn_pair(kernel, 60000.0, 0.0);
        remove_radar(kernel, pair.jammer);

        install_pod(kernel, pair.jammer, gen4_pod(JammingType::NoiseBarrage), false);
        CHECK_FALSE(scan_for(kernel, pair.radar, pair.jammer, probe_esm()).has_value());
        CHECK(esm_detections(kernel, pair.radar).empty());

        // Any technique radiates, and the beam does not gate the ESM view
        // (the pod faces away from the receiver here).
        for (const JammingType type : {JammingType::NoiseBarrage, JammingType::NoiseSpot,
                                       JammingType::DeceptionDRFM}) {
            clear_esm(kernel, pair.radar);
            install_pod(kernel, pair.jammer, gen4_pod(type), true);
            const auto strobe = scan_for(kernel, pair.radar, pair.jammer, probe_esm());
            REQUIRE(strobe.has_value());
            CHECK(strobe->range == doctest::Approx(0.0));
            const auto detections = esm_detections(kernel, pair.radar);
            REQUIRE(detections.size() == 1);
            CHECK(detections.front().source_id == pair.jammer);
            CHECK(detections.front().is_jammer);
            CHECK_FALSE(detections.front().is_radar_lock);
            CHECK_FALSE(detections.front().is_missile_guidance);
            // Due north of a north-facing receiver.
            CHECK(detections.front().bearing_deg == doctest::Approx(0.0));
        }

        // The strobe reaches the observation as a plain emitter row.
        const AgentObservation obs = kernel.get_agent_observation(pair.radar);
        const auto row =
            std::find_if(obs.rwr_warnings.begin(), obs.rwr_warnings.end(),
                         [&](const RWREvent &event) { return event.source_id == pair.jammer; });
        REQUIRE(row != obs.rwr_warnings.end());
        CHECK_FALSE(row->is_lock);
        CHECK_FALSE(row->is_launch);

        // Back in standby the platform is silent again.
        clear_esm(kernel, pair.radar);
        install_pod(kernel, pair.jammer, gen4_pod(JammingType::NoiseBarrage), false);
        CHECK_FALSE(scan_for(kernel, pair.radar, pair.jammer, probe_esm()).has_value());
        CHECK(esm_detections(kernel, pair.radar).empty());
    }

    TEST_CASE("a radar platform that also jams yields a radar and a jammer detection") {
        SimulationKernel kernel;
        kernel.reset(47);
        const Pair pair = spawn_pair(kernel, 60000.0, 180.0);
        install_pod(kernel, pair.jammer, gen4_pod(JammingType::NoiseBarrage), false);
        REQUIRE(scan_for(kernel, pair.radar, pair.jammer, probe_esm()).has_value());
        auto detections = esm_detections(kernel, pair.radar);
        REQUIRE(detections.size() == 1);
        CHECK_FALSE(detections.front().is_jammer);

        clear_esm(kernel, pair.radar);
        install_pod(kernel, pair.jammer, gen4_pod(JammingType::NoiseBarrage), true);
        REQUIRE(scan_for(kernel, pair.radar, pair.jammer, probe_esm()).has_value());
        detections = esm_detections(kernel, pair.radar);
        REQUIRE(detections.size() == 2);
        const auto jammer_rows =
            std::count_if(detections.begin(), detections.end(),
                          [](const EmitterDetection &det) { return det.is_jammer; });
        CHECK(jammer_rows == 1);
        for (const auto &det : detections) {
            CHECK(det.source_id == pair.jammer);
        }
    }
}
