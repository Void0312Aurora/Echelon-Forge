#include "core/interfaces/sensor_model.h"
#include "core/interfaces/environment_model.h"
#include "components/basic/common.h"
#include "components/systems/ew.h"
#include "components/combat/common/weapon_common.h"
#include "core/interfaces/stochastic_draw.h"
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

double horizon_distance_m(double h1_m, double h2_m) {
    const double h1 = std::max(0.0, h1_m);
    const double h2 = std::max(0.0, h2_m);
    return 3570.0 * (std::sqrt(h1) + std::sqrt(h2));
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

// Range out to which a passive receiver hears an emitter: the receiver's own
// detection range, else the scanning ESM sensor's range.
double esm_receiver_range_m(const flecs::entity &owner, const Sensor &esm_sensor) {
    const ESMReceiver *owner_esm = owner.get<ESMReceiver>();
    if (owner_esm && owner_esm->max_detection_range_m > 0.0) {
        return owner_esm->max_detection_range_m;
    }
    return esm_sensor.max_range;
}

// A transmitting pod is an RF emitter whatever its technique. It is described
// as an emitter detectable out to the listening receiver's range; its ERP is
// the emitter-strength proxy, as the reference range is for a radar.
bool entity_has_jammer_emitter(const flecs::entity &entity, double receiver_range_m,
                               Sensor *out_emitter, double *out_erp_watts) {
    const Jammer *jammer = entity.get<Jammer>();
    if (!jammer || !jammer_transmitting(*jammer)) {
        return false;
    }
    if (out_emitter) {
        *out_emitter = Sensor{};
        out_emitter->max_range = receiver_range_m;
        out_emitter->reference_range_m = receiver_range_m;
    }
    if (out_erp_watts) {
        *out_erp_watts = jammer->power_watts;
    }
    return true;
}

void record_esm_detection(ESMReceiver &owner_esm, flecs::entity emitter, const Sensor &esm_sensor,
                          const Sensor &emitter_sensor, double emitter_power_proxy, bool is_jammer,
                          double dist_m, double rel_bearing_deg) {
    const double max_range = owner_esm.max_detection_range_m > 0.0
                                 ? owner_esm.max_detection_range_m
                                 : std::max(esm_sensor.max_range, emitter_sensor.max_range * 2.0);
    if (dist_m > max_range) {
        return;
    }

    const double emitter_strength = emitter_power_proxy / std::max(1.0, dist_m * dist_m);
    auto existing = std::find_if(owner_esm.detections.begin(), owner_esm.detections.end(),
                                 [&](const EmitterDetection &det) {
                                     return det.source_id == emitter.id() &&
                                            det.is_jammer == is_jammer;
                                 });
    EmitterDetection det{};
    det.source_id = emitter.id();
    det.bearing_deg = rel_bearing_deg;
    det.signal_strength = emitter_strength;
    // A jammer strobe is never lock or launch evidence.
    det.is_radar_lock = !is_jammer && emitter.has<Missile>();
    det.is_missile_guidance = !is_jammer && emitter.has<Missile>();
    det.is_jammer = is_jammer;
    if (existing == owner_esm.detections.end()) {
        owner_esm.detections.push_back(det);
    } else if (det.signal_strength >= existing->signal_strength) {
        *existing = det;
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
    if (entity_has_radar_emitter(emitter, &emitter_radar)) {
        record_esm_detection(*owner_esm, emitter, esm_sensor, emitter_radar,
                             std::max(1.0, emitter_radar.reference_range_m), false, dist_m,
                             rel_bearing_deg);
    }
    Sensor jammer_emitter{};
    double jammer_erp_watts = 0.0;
    if (entity_has_jammer_emitter(emitter, esm_receiver_range_m(owner, esm_sensor),
                                  &jammer_emitter, &jammer_erp_watts)) {
        record_esm_detection(*owner_esm, emitter, esm_sensor, jammer_emitter,
                             std::max(1.0, jammer_erp_watts), true, dist_m, rel_bearing_deg);
    }
}

// True when the radar at `radar_t` lies inside the main beam of the pod on the
// platform at `jammer_t`. The beam is centred on the platform nose; a pod
// without a positive beam width radiates omnidirectionally.
bool jammer_beam_covers(const Jammer &jammer, const Transform &jammer_t,
                        const Transform &radar_t) {
    if (!(jammer.effective_angle > 0.0)) {
        return true;
    }
    const Vector3 nose = Math::body_to_world(Vector3{1.0, 0.0, 0.0}, jammer_t);
    const double lx = radar_t.x - jammer_t.x;
    const double ly = radar_t.y - jammer_t.y;
    const double lz = radar_t.z - jammer_t.z;
    const double los = std::sqrt(lx * lx + ly * ly + lz * lz);
    if (los <= 0.0) {
        return true;
    }
    const double cos_off = std::clamp((nose.x * lx + nose.y * ly + nose.z * lz) / los, -1.0, 1.0);
    const double off_boresight_deg = std::acos(cos_off) * 180.0 / std::numbers::pi_v<double>;
    return off_boresight_deg <= 0.5 * jammer.effective_angle;
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

            if (sensor.type == static_cast<int>(SensorType::Radar) &&
                sensor.enforce_radar_horizon &&
                sensor.environment_domain ==
                    static_cast<int>(SensorEnvironmentDomain::SurfaceMaritime)) {
                const double owner_height = std::max(1.0, sensor.antenna_height_m);
                const double target_height =
                    naval::sensor::maritime_radar_target_height_m(sensor, target_e, target_t);
                // Treat the configured max_range for maritime radars as the baseline
                // public-runtime horizon proxy. This avoids double-penalizing modules
                // such as SPS-67 whose public runtime range is already calibrated from
                // owner/target mast heights.
                const double configured_baseline =
                    std::max(sensor.max_range, horizon_distance_m(owner_height, target_height));
                const double horizon_limit = configured_baseline + maritime_bonus_m;
                if (dist > horizon_limit) {
                    return;
                }
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
                    Sensor emitter{};
                    if (!entity_has_radar_emitter(target_e, &emitter) &&
                        !entity_has_jammer_emitter(target_e, esm_receiver_range_m(owner, sensor),
                                                   &emitter, nullptr)) {
                        return;
                    }
                    rcs = std::max(5.0, emitter.reference_rcs_m2);
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

                    // Phase 3: self-protection jamming by the target's pod. It
                    // acts only on a radar inside its main beam and only beyond
                    // burn-through (Jammer::burn_through_reference_m).
                    const Jammer *jammer = target_e.get<Jammer>();
                    if (jammer && jammer->is_active &&
                        jammer_beam_covers(*jammer, target_t, owner_transform)) {
                        const double r_bt = jammer_burn_through_range_m(*jammer, rcs);
                        if (dist > r_bt) {
                            if (jammer->type != JammingType::DeceptionDRFM) {
                                // Noise suppression: the target is hidden.
                                return;
                            }
                            // Range deception: the radar keeps a contact on the
                            // DRFM false target, displaced in range only.
                            noisy_range = std::max(0.0, noisy_range + jammer->drfm_range_offset_m);
                        }
                    }
                } else if (sensor.type == static_cast<int>(SensorType::Infrared)) {
                    // IR: Prop to Heat / R^2
                    // Hack: If target has Lifetime (Decoy) assume Flare
                    if (target_e.has<Lifetime>()) {
                        signal_strength = 500.0 / dist_sq;
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
