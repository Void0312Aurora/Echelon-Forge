#include "core/interfaces/sensor_model.h"
#include "core/interfaces/environment_model.h"
#include "components/basic/common.h"
#include "components/systems/ew.h"
#include "components/combat/common/weapon_common.h"
#include "core/interfaces/stochastic_draw.h"
#include "components/physics/geodesy.h"
#include "models/domains/naval/naval_sensor_maritime_adapter.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <numbers>

namespace {

double wrap_angle_360(double angle) {
    while (angle < 0.0)
        angle += 360.0;
    while (angle >= 360.0)
        angle -= 360.0;
    return angle;
}

double normalize_angle_deg(double angle) {
    while (angle > 180.0)
        angle -= 360.0;
    while (angle < -180.0)
        angle += 360.0;
    return angle;
}

double math_deg_to_nav_deg(double math_deg) {
    return wrap_angle_360(90.0 - math_deg);
}

double rand_normal(double u1, double u2) {
    const double safe_u1 = std::max(1e-12, u1);
    return std::sqrt(-2.0 * std::log(safe_u1)) * std::cos(2.0 * std::numbers::pi_v<double> * u2);
}

double clamp_sensor_probability(double value) {
    return std::clamp(value, 0.0, 1.0);
}

double rcs_for_detection(const flecs::entity &target_e, const Transform &owner_t,
                         const Transform &target_t) {
    double rcs = 5.0;
    const RCSProfile *rcs_prof = target_e.get<RCSProfile>();
    if (!rcs_prof) {
        return rcs;
    }

    double los_math_deg = std::atan2(owner_t.y - target_t.y, owner_t.x - target_t.x) * 180.0 /
                          std::numbers::pi_v<double>;
    double los_nav_deg = math_deg_to_nav_deg(los_math_deg);
    double aspect_deg = normalize_angle_deg(los_nav_deg - target_t.heading);
    const double aspect_abs = std::abs(aspect_deg);

    if (aspect_abs <= 45.0) {
        rcs = rcs_prof->frontal_rcs;
    } else if (aspect_abs >= 135.0) {
        rcs = rcs_prof->rear_rcs;
    } else {
        rcs = rcs_prof->side_rcs;
    }

    return std::max(1.0e-6, rcs);
}

double compute_snr_db(const Sensor &sensor, double dist_m, double rcs_m2, double attenuation_factor,
                      double doppler_factor) {
    if (sensor.type == static_cast<int>(SensorType::ESM)) {
        const double ref_range = sensor.reference_range_m > 1.0 ? sensor.reference_range_m
                                                                : std::max(sensor.max_range, 1.0);
        const double range_ratio = ref_range / std::max(1.0, dist_m);
        double snr_linear = std::pow(10.0, sensor.reference_snr_db / 10.0);
        snr_linear *= std::max(1.0, rcs_m2 / std::max(1.0, sensor.reference_rcs_m2));
        snr_linear *= std::pow(range_ratio, 2.0);
        snr_linear *= std::max(0.0, attenuation_factor);
        snr_linear = std::max(1.0e-12, snr_linear);
        return 10.0 * std::log10(snr_linear);
    }

    const double ref_range =
        sensor.reference_range_m > 1.0 ? sensor.reference_range_m : std::max(sensor.max_range, 1.0);
    const double ref_rcs = sensor.reference_rcs_m2 > 1.0e-6 ? sensor.reference_rcs_m2 : 5.0;
    const double ref_snr_db = sensor.reference_snr_db;

    double snr_linear = std::pow(10.0, ref_snr_db / 10.0);
    snr_linear *= std::max(1.0e-6, rcs_m2 / ref_rcs);

    const double range_ratio = ref_range / std::max(1.0, dist_m);
    const double range_power =
        (sensor.type == static_cast<int>(SensorType::Radar))
            ? 4.0
            : std::max(1.0, sensor.range_power > 0.0 ? sensor.range_power : 2.0);
    snr_linear *= std::pow(range_ratio, range_power);
    snr_linear *= std::max(0.0, attenuation_factor);
    snr_linear *= std::max(0.0, doppler_factor);
    snr_linear = std::max(1.0e-12, snr_linear);
    return 10.0 * std::log10(snr_linear);
}

double pd_from_snr_db(const Sensor &sensor, double snr_db) {
    const double pfa = sensor.pfa > 0.0 ? sensor.pfa : 1.0e-6;
    const double pfa_scale = std::clamp(std::log10(1.0 / pfa) / 6.0, 0.5, 2.0);
    const double snr_50_db = 0.0;
    const double slope = 0.85 * pfa_scale;
    const double logistic = 1.0 / (1.0 + std::exp(-slope * (snr_db - snr_50_db)));
    return clamp_sensor_probability(logistic);
}

constexpr double kReferenceJammerBandwidthMhz = 2000.0;

double jammer_bandwidth_factor(const Jammer &jammer) {
    if (!std::isfinite(jammer.bandwidth_mhz) || jammer.bandwidth_mhz <= 0.0) {
        return 0.0;
    }
    // The maintained Gen4 suite uses 2 GHz as its baseline. Until sensors
    // carry an authored RF band, treat wider coverage as full-band and
    // narrower coverage as the corresponding fraction of available power.
    return std::clamp(jammer.bandwidth_mhz / kReferenceJammerBandwidthMhz, 0.0, 1.0);
}

bool jammer_covers_receiver(const Jammer &jammer, const Transform &jammer_transform,
                            const Transform &receiver_transform) {
    if (!std::isfinite(jammer.effective_angle) || jammer.effective_angle <= 0.0) {
        return true; // Legacy/omnidirectional fixture semantics.
    }
    const double dx = receiver_transform.x - jammer_transform.x;
    const double dy = receiver_transform.y - jammer_transform.y;
    const double bearing_math_deg = std::atan2(dy, dx) * 180.0 / std::numbers::pi_v<double>;
    const double bearing_nav_deg = math_deg_to_nav_deg(bearing_math_deg);
    const double relative_bearing =
        normalize_angle_deg(bearing_nav_deg - jammer_transform.heading);
    const double half_angle = std::clamp(jammer.effective_angle, 0.0, 360.0) * 0.5;
    return std::abs(relative_bearing) <= half_angle;
}

bool jammer_suppresses_radar(const Jammer &jammer, const Transform &jammer_transform,
                             const Transform &receiver_transform, double target_rcs_m2,
                             double distance_m) {
    if (!jammer_installed(jammer) || !jammer.is_active ||
        (jammer.type != JammingType::NoiseBarrage && jammer.type != JammingType::NoiseSpot) ||
        !jammer_covers_receiver(jammer, jammer_transform, receiver_transform)) {
        return false;
    }
    const double bandwidth_factor = jammer_bandwidth_factor(jammer);
    if (bandwidth_factor <= 0.0) {
        return false;
    }

    // Burn-through is based on jammer power density. This is deliberately a
    // bounded proxy until the Sensor contract carries an authored RF band.
    const double effective_power =
        std::max(1.0, jammer.power_watts) * bandwidth_factor;
    const double burn_through_range =
        283000.0 * std::sqrt(std::max(1.0e-6, target_rcs_m2) / effective_power);
    return distance_m > burn_through_range;
}

bool entity_has_radar_emitter(const flecs::entity &entity, Sensor *out_emitter) {
    if (const Sensor *inline_sensor = entity.get<Sensor>()) {
        if (inline_sensor->type == static_cast<int>(SensorType::Radar)) {
            if (out_emitter) {
                *out_emitter = *inline_sensor;
            }
            return true;
        }
    }
    if (const MountedSensors *mounted = entity.get<MountedSensors>()) {
        for (const auto &mount : mounted->mounts) {
            if (mount.sensor.type == static_cast<int>(SensorType::Radar)) {
                if (out_emitter) {
                    *out_emitter = mount.sensor;
                }
                return true;
            }
        }
    }
    return false;
}

double horizon_refraction_factor(const Sensor &sensor) {
    // Visual and infrared sensors see the optical sea horizon; every
    // radio-frequency sensor (radar, ESM, RWR, data-link receivers) uses the
    // 4/3 effective-earth radius. Both factors are sourced in geodesy.h.
    if (sensor.type == static_cast<int>(SensorType::Visual) ||
        sensor.type == static_cast<int>(SensorType::Infrared)) {
        return geodesy::kStandardOpticalRefractionFactor;
    }
    return geodesy::kStandardRefractionFactor;
}

double sensor_height_above_surface_m(const Sensor &sensor, const Transform &owner_transform) {
    // The sensor sits at its declared mount height above the platform's
    // reference point; z is height above the reference sphere in the geodetic
    // frame (a ship's z is its waterline).
    return std::max(0.0, owner_transform.z) + std::max(0.0, sensor.antenna_height_m);
}

double target_height_above_surface_m(const Sensor &sensor, const flecs::entity &target,
                                     const Transform &target_transform) {
    const double z_m = std::max(0.0, target_transform.z);
    // A passive ESM receiver sees the emitting antenna, not the hull.
    if (sensor.type == static_cast<int>(SensorType::ESM)) {
        Sensor emitter_radar{};
        if (entity_has_radar_emitter(target, &emitter_radar)) {
            return z_m + std::max(0.0, emitter_radar.antenna_height_m);
        }
    }
    // Ships expose their radar-significant height above the waterline through
    // the naval adapter (the sensor's maritime target-height prior applies
    // there). Any other target is a point at its own height, so a sea-skimming
    // missile is seen late rather than lifted to a surface-ship prior.
    const double ship_height_m =
        naval::sensor::ship_target_horizon_height_m(sensor, target, target_transform);
    return ship_height_m >= 0.0 ? z_m + ship_height_m : z_m;
}

// Smooth-earth horizon gate shared by every line-of-sight sensor type
// (Geodetic Frame P3-A). The limit is the exact smooth-sphere line-of-sight
// boundary for the two heights, compared against the horizontal separation in
// the local frame (an azimuthal-equidistant projection, so the separation
// matches the great-circle arc to well under 0.1 % inside the declared frame
// extent). Anomalous propagation that the environment declares (maritime
// ducting) extends the limit by the same bonus that extends the range gate.
bool within_smooth_earth_horizon(const Sensor &sensor, const Transform &owner_transform,
                                 const flecs::entity &target, const Transform &target_transform,
                                 double horizontal_dist_m, double anomalous_propagation_bonus_m) {
    if (sensor.type == static_cast<int>(SensorType::Sonar)) {
        return true; // acoustic propagation is not a line-of-sight path
    }
    const double re =
        geodesy::effective_radius_m(geodesy::EarthModel{}, horizon_refraction_factor(sensor));
    const double horizon_limit_m =
        geodesy::two_way_horizon_arc_m(
            re, sensor_height_above_surface_m(sensor, owner_transform),
            target_height_above_surface_m(sensor, target, target_transform)) +
        std::max(0.0, anomalous_propagation_bonus_m);
    return horizontal_dist_m <= horizon_limit_m;
}

void append_rwr_detection_from_radar(const Sensor &sensor, flecs::entity emitter,
                                     flecs::entity target, double dist_m, bool is_lock) {
    if (sensor.type != static_cast<int>(SensorType::Radar)) {
        return;
    }

    RWR *target_rwr = target.get_mut<RWR>();
    if (target_rwr) {
        if (dist_m < sensor.max_range * 1.5) {
            const auto found = std::find(target_rwr->detected_radar_ids.begin(),
                                         target_rwr->detected_radar_ids.end(), emitter.id());
            if (found == target_rwr->detected_radar_ids.end()) {
                target_rwr->detected_radar_ids.push_back(emitter.id());
            }
            if (is_lock || emitter.has<Missile>()) {
                const auto locked = std::find(target_rwr->locking_radar_ids.begin(),
                                              target_rwr->locking_radar_ids.end(), emitter.id());
                if (locked == target_rwr->locking_radar_ids.end()) {
                    target_rwr->locking_radar_ids.push_back(emitter.id());
                }
            }
        }
    }
}

void append_esm_detection_from_emitter(flecs::entity owner, flecs::entity emitter,
                                       const Sensor &esm_sensor, double dist_m,
                                       double rel_bearing_deg) {
    ESMReceiver *owner_esm = owner.get_mut<ESMReceiver>();
    if (!owner_esm) {
        return;
    }

    Sensor emitter_radar{};
    if (!entity_has_radar_emitter(emitter, &emitter_radar)) {
        return;
    }

    const double max_range = owner_esm->max_detection_range_m > 0.0
                                 ? owner_esm->max_detection_range_m
                                 : std::max(esm_sensor.max_range, emitter_radar.max_range * 2.0);
    if (dist_m > max_range) {
        return;
    }

    const double emitter_strength =
        std::max(1.0, emitter_radar.reference_range_m) / std::max(1.0, dist_m * dist_m);
    auto existing =
        std::find_if(owner_esm->detections.begin(), owner_esm->detections.end(),
                     [&](const EmitterDetection &det) { return det.source_id == emitter.id(); });
    EmitterDetection det{};
    det.source_id = emitter.id();
    det.bearing_deg = rel_bearing_deg;
    det.signal_strength = emitter_strength;
    det.is_radar_lock = emitter.has<Missile>();
    det.is_missile_guidance = emitter.has<Missile>();
    if (existing == owner_esm->detections.end()) {
        owner_esm->detections.push_back(det);
    } else if (det.signal_strength >= existing->signal_strength) {
        *existing = det;
    }
}

class DefaultSensorModel : public ISensorModel {
  public:
    void scan(flecs::world world, flecs::entity owner, const Transform &owner_transform,
              const Sensor &sensor, ContactList &out_contacts, double current_time) override {

        auto target_query = world.query<const KeyEntity, const Transform>();
        const Alliance *owner_alliance = owner.get<Alliance>();
        // Environment Singleton Access
        const EnvironmentModelRef *env_ref = world.get<EnvironmentModelRef>();

        target_query.each([&](flecs::entity target_e, const KeyEntity & /*key*/,
                              const Transform &target_t) {
            if (target_e == owner) return;
            if (sensor.max_range <= 0.0 || sensor.detection_prob <= 0.0) return;

            if (owner_alliance) {
                const Alliance *target_alliance = target_e.get<Alliance>();
                if (target_alliance && owner_alliance->side == target_alliance->side) {
                    return;
                }
            }

            double dx = target_t.x - owner_transform.x;
            double dy = target_t.y - owner_transform.y;
            double dz = target_t.z - owner_transform.z;
            double dist_sq = dx * dx + dy * dy + dz * dz;
            double maritime_bonus_m = 0.0;
            if (sensor.type == static_cast<int>(SensorType::Radar) &&
                sensor.environment_domain ==
                    static_cast<int>(SensorEnvironmentDomain::SurfaceMaritime)) {
                maritime_bonus_m =
                    naval::sensor::maritime_radar_ducting_bonus_m(sensor, env_ref, owner);
            }
            double effective_max_range = sensor.max_range + maritime_bonus_m;
            double max_sq = effective_max_range * effective_max_range;

            if (dist_sq > max_sq) return;
            double dist = std::sqrt(dist_sq);

            if (!within_smooth_earth_horizon(sensor, owner_transform, target_e, target_t,
                                             std::sqrt(dx * dx + dy * dy), maritime_bonus_m)) {
                return; // below the smooth-earth horizon
            }

            // Phase 2 & 3: Environment Checks
            double weath_factor = 1.0;
            double sun_factor = 1.0;

            if (env_ref && env_ref->model) {
                // 1. Line of Sight
                if (!env_ref->model->check_line_of_sight(owner_transform.x, owner_transform.y,
                                                         owner_transform.z, target_t.x, target_t.y,
                                                         target_t.z)) {
                    return; // Obscured
                }

                // 2. Weather Attenuation
                double att = env_ref->model->get_weather_attenuation(
                    owner_transform.x, owner_transform.y, owner_transform.z, target_t.x, target_t.y,
                    target_t.z, sensor.type);
                weath_factor = 1.0 - att;

                // 3. Sun Glare (Visual/IR). Only a sun above the horizon can
                // blind a sensor; below-horizon (night) suns must not apply
                // the penalty through the earth.
                if (sensor.type <= 1) { // 0=Visual, 1=IR
                    Vec3 sun = env_ref->model->get_sun_direction();
                    // Dot product of (ToTarget) and (Sun)
                    if (sun.z > 0.0 && dist > 1.0) {
                        double udx = dx / dist;
                        double udy = dy / dist;
                        double udz = dz / dist;
                        double dot = udx * sun.x + udy * sun.y + udz * sun.z;
                        if (dot > 0.98) { // < 11.5 degrees separation
                            sun_factor = 0.1;
                        }
                    }
                }
            }

            double bearing_rad = std::atan2(dy, dx);
            double bearing_math_deg = bearing_rad * 180.0 / std::numbers::pi_v<double>;
            double bearing_nav_deg = math_deg_to_nav_deg(bearing_math_deg);
            double rel_bearing = normalize_angle_deg(bearing_nav_deg - owner_transform.heading);

            if (std::abs(rel_bearing) <= sensor.fov_deg / 2.0) {
                double range_ratio =
                    std::clamp(dist / std::max(1.0, effective_max_range), 0.0, 1.0);
                double range_power = (sensor.range_power > 0.0) ? sensor.range_power : 1.0;
                double range_factor = 1.0 - std::pow(range_ratio, range_power);
                range_factor = std::clamp(range_factor, 0.0, 1.0);

                double aspect_factor = 1.0;
                double aspect_weight = std::clamp(sensor.aspect_influence, 0.0, 1.0);
                if (aspect_weight > 0.0) {
                    double los_math_deg =
                        std::atan2(owner_transform.y - target_t.y, owner_transform.x - target_t.x) *
                        180.0 / std::numbers::pi_v<double>;
                    double los_nav_deg = math_deg_to_nav_deg(los_math_deg);
                    double aspect_deg = normalize_angle_deg(los_nav_deg - target_t.heading);
                    double aspect_cos = std::cos(aspect_deg * std::numbers::pi_v<double> / 180.0);
                    double aspect_scale = 0.5 + 0.5 * aspect_cos;
                    aspect_factor = (1.0 - aspect_weight) + aspect_weight * aspect_scale;
                }

                // Doppler Logic
                const Velocity *owner_v = world.entity(owner).get<Velocity>();
                const Velocity *target_v = target_e.get<Velocity>();
                double doppler_factor = 1.0;

                double v_closing = 0.0;
                if (owner_v && target_v && dist > 1.0) {
                    double rx = dx / dist;
                    double ry = dy / dist;
                    double rz = dz / dist;

                    double v_rel_x = target_v->vx - owner_v->vx;
                    double v_rel_y = target_v->vy - owner_v->vy;
                    double v_rel_z = target_v->vz - owner_v->vz;

                    v_closing = -(v_rel_x * rx + v_rel_y * ry + v_rel_z * rz);

                    double notch_width =
                        sensor.doppler_notch_width > 0.0 ? sensor.doppler_notch_width : 25.0;
                    if (std::abs(v_closing) < notch_width) {
                        doppler_factor = 0.1;
                    }
                }

                double attenuation_factor = aspect_factor * weath_factor * sun_factor;
                if (sensor.type == static_cast<int>(SensorType::Radar) &&
                    sensor.environment_domain ==
                        static_cast<int>(SensorEnvironmentDomain::SurfaceMaritime)) {
                    attenuation_factor *= naval::sensor::maritime_radar_sea_clutter_loss(
                        sensor, env_ref, owner, target_e, dist, dz);
                }
                double rcs = rcs_for_detection(target_e, owner_transform, target_t);
                if (sensor.type == static_cast<int>(SensorType::ESM)) {
                    Sensor emitter_radar{};
                    if (!entity_has_radar_emitter(target_e, &emitter_radar)) {
                        return;
                    }
                    rcs = std::max(5.0, emitter_radar.reference_rcs_m2);
                }
                double snr_db =
                    compute_snr_db(sensor, dist, rcs, attenuation_factor, doppler_factor);
                double detection_prob = pd_from_snr_db(sensor, snr_db);
                detection_prob *= std::clamp(sensor.detection_prob, 0.0, 1.0);
                detection_prob *= range_factor;
                detection_prob = clamp_sensor_probability(detection_prob);

                const uint64_t seed_det =
                    stochastic_draw::draw_seed(world, stochastic_draw::DrawSite::radar_detection,
                                               current_time, {owner, target_e});
                if (stochastic_draw::uniform01(seed_det) > detection_prob) {
                    return;
                }

                double horizontal_dist = std::sqrt(std::max(0.0, dx * dx + dy * dy));
                double elevation_deg = 0.0;
                if (horizontal_dist > 1e-6) {
                    elevation_deg =
                        std::atan2(dz, horizontal_dist) * 180.0 / std::numbers::pi_v<double>;
                }

                double noisy_bearing = rel_bearing;
                if (sensor.bearing_noise_std > 0.0) {
                    noisy_bearing +=
                        rand_normal(
                            stochastic_draw::uniform01(stochastic_draw::lane(seed_det, 1)),
                            stochastic_draw::uniform01(stochastic_draw::lane(seed_det, 2))) *
                        sensor.bearing_noise_std;
                }
                double noisy_range = dist;
                if (sensor.range_noise_std > 0.0) {
                    noisy_range +=
                        rand_normal(
                            stochastic_draw::uniform01(stochastic_draw::lane(seed_det, 3)),
                            stochastic_draw::uniform01(stochastic_draw::lane(seed_det, 4))) *
                        sensor.range_noise_std;
                }
                noisy_range = std::max(0.0, noisy_range);

                double signal_strength = 0.0;

                if (sensor.type == static_cast<int>(SensorType::Radar)) {
                    // Radar Equation: Prop to RCS / R^4
                    if (dist > 1.0) {
                        signal_strength = rcs / (dist_sq * dist_sq);
                    } else {
                        signal_strength = rcs;
                    }

                    // Phase 3: bounded suppression jamming (burn-through). The
                    // radar remains visible outside the jammer's beam, below
                    // its authored bandwidth, or for a DRFM technique; those
                    // cases require a separate seeker/false-track model.
                    const Jammer *jammer = target_e.get<Jammer>();
                    if (jammer && jammer_suppresses_radar(*jammer, target_t, owner_transform,
                                                          rcs, dist)) {
                        return;
                    }
                } else if (sensor.type == static_cast<int>(SensorType::Infrared)) {
                    // IR: Prop to Heat / R^2. A flare radiates its authored IR
                    // intensity; chaff is not an IR source; any other entity
                    // keeps the platform proxy signature.
                    const Decoy *decoy = target_e.get<Decoy>();
                    if (decoy && decoy->kind == DecoyKind::Chaff) {
                        return;
                    }
                    if (decoy && decoy->kind == DecoyKind::Flare) {
                        signal_strength = decoy->signature / dist_sq;
                    } else {
                        signal_strength = 50.0 / dist_sq;
                    }
                } else if (sensor.type == static_cast<int>(SensorType::ESM)) {
                    signal_strength = 1.0 / std::max(1.0, dist_sq);
                } else {
                    // Visual
                    signal_strength = 1.0 / dist_sq;
                }

                double measured_vr = v_closing;
                if (sensor.velocity_noise_std > 0.0) {
                    measured_vr +=
                        rand_normal(
                            stochastic_draw::uniform01(stochastic_draw::lane(seed_det, 5)),
                            stochastic_draw::uniform01(stochastic_draw::lane(seed_det, 6))) *
                        sensor.velocity_noise_std;
                }

                const bool bearing_only =
                    sensor.bearing_only || sensor.type == static_cast<int>(SensorType::ESM);
                if (sensor.type == static_cast<int>(SensorType::Radar)) {
                    append_rwr_detection_from_radar(sensor, owner, target_e, dist, false);
                } else if (sensor.type == static_cast<int>(SensorType::ESM)) {
                    append_esm_detection_from_emitter(owner, target_e, sensor, dist,
                                                      normalize_angle_deg(noisy_bearing));
                }

                out_contacts.contacts.push_back(
                    {target_e.id(), bearing_only ? 0.0 : noisy_range,
                     normalize_angle_deg(noisy_bearing), std::clamp(elevation_deg, -90.0, 90.0),
                     measured_vr, signal_strength, snr_db, detection_prob, measured_vr, sensor.type,
                     true, current_time});
            }
        });
    }
};

} // namespace

std::unique_ptr<ISensorModel> make_default_sensor_model() {
    return std::make_unique<DefaultSensorModel>();
}
