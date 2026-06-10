#include "core/interfaces/acoustic_model.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>

#include "components/domains/naval/platform/ship_platform.h"
#include "components/domains/naval/platform/submarine_platform.h"
#include "components/systems/ew.h"
#include "core/interfaces/environment_model.h"

namespace {

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

double wrap_angle_deg(double angle) {
    while (angle > 180.0) angle -= 360.0;
    while (angle < -180.0) angle += 360.0;
    return angle;
}

double nav_bearing_rel_deg(const Transform& owner, const Transform& target) {
    const double dx = target.x - owner.x;
    const double dy = target.y - owner.y;
    const double bearing_math_deg = std::atan2(dy, dx) * 180.0 / M_PI;
    const double bearing_nav_deg = Math::normalize_heading_deg(90.0 - bearing_math_deg);
    return wrap_angle_deg(bearing_nav_deg - owner.heading);
}

double splitmix01(std::uint64_t seed) {
    std::uint64_t z = seed + 0x9e3779b97f4a7c15ULL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    z ^= (z >> 31);
    return (z >> 11) * (1.0 / 9007199254740992.0);
}

double splitmix_normal(std::uint64_t seed_a, std::uint64_t seed_b) {
    const double u1 = std::max(1.0e-12, splitmix01(seed_a));
    const double u2 = splitmix01(seed_b);
    return std::sqrt(-2.0 * std::log(u1)) * std::cos(2.0 * M_PI * u2);
}

double platform_self_noise_bias_db(const flecs::entity& entity, double speed_mps) {
    if (const SubmarinePlatform* sub = entity.get<SubmarinePlatform>()) {
        return std::max(0.0, speed_mps - std::max(0.0, sub->quiet_speed_mps)) *
            std::max(0.0, sub->self_noise_per_speed_db);
    }
    if (const ShipPlatform* ship = entity.get<ShipPlatform>()) {
        const double econ = ship->economical_speed_mps > 0.0 ? ship->economical_speed_mps : 5.0;
        return std::max(0.0, speed_mps - econ) * 0.8;
    }
    return std::max(0.0, speed_mps - 5.0) * 0.6;
}

double target_source_level_db(const flecs::entity& target, double speed_mps, const Sonar& sonar) {
    double source_level = sonar.source_level_reference_db +
        std::max(0.0, speed_mps) * std::max(0.0, sonar.source_level_speed_factor_db);
    if (const SubmarinePlatform* sub = target.get<SubmarinePlatform>()) {
        source_level += sub->acoustic_stealth_bias_db + 10.0;
    } else if (target.get<ShipPlatform>() != nullptr) {
        source_level += 16.0;
    } else if (const KeyEntity* key = target.get<KeyEntity>(); key && key->type == UnitType::Aircraft) {
        source_level += 18.0;
    }
    return source_level;
}

double transmission_loss_db(double range_m, const Sonar& sonar) {
    const double safe_range = std::max(1.0, range_m);
    const double spreading_db = 20.0 * std::log10(safe_range);
    const double absorption_db =
        std::max(0.0, sonar.transmission_loss_alpha_db_per_km) * (safe_range / 1000.0);
    return spreading_db + absorption_db;
}

IEnvironmentModel::MaritimeState maritime_state_for(
    const EnvironmentModelRef* env_ref,
    const flecs::entity& owner
) {
    if (env_ref && env_ref->model) {
        const auto state = env_ref->model->get_maritime_state();
        if (state.configured) {
            return state;
        }
    }

    IEnvironmentModel::MaritimeState state{};
    if (const ShipPlatform* ship = owner.get<ShipPlatform>()) {
        state.configured = true;
        state.sea_state = std::max(0.0, ship->sea_state);
        state.wave_heading_deg = ship->wave_heading_deg;
        state.wave_period_s = std::max(2.0, ship->wave_period_s);
    }
    return state;
}

double maritime_ambient_noise_bias_db(
    const EnvironmentModelRef* env_ref,
    const flecs::entity& owner,
    const Sonar& sonar
) {
    const auto state = maritime_state_for(env_ref, owner);
    if (!state.configured || state.sea_state <= 0.0) {
        return 0.0;
    }

    // Engineering calibration: rougher seas raise broadband ambient noise and
    // make passive contacts less stable without implying authoritative sonar data.
    const double wave_period_factor = std::clamp(8.0 / std::max(4.0, state.wave_period_s), 0.75, 1.35);
    const double sea_state_factor = std::min(4.5, state.sea_state * 0.9);
    const double sonar_sensitivity = sonar.passive_only ? 1.0 : 0.75;
    return sea_state_factor * wave_period_factor * sonar_sensitivity;
}

class DefaultAcousticModel : public IAcousticModel {
public:
    void scan(flecs::world world,
              flecs::entity owner,
              const Transform& owner_transform,
              const Sonar& sonar,
              ContactList& out_contacts,
              double current_time) override {
        const Alliance* owner_alliance = owner.get<Alliance>();
        const Velocity* owner_velocity = owner.get<Velocity>();
        const EnvironmentModelRef* env_ref = world.get<EnvironmentModelRef>();
        const double own_speed_mps = owner_velocity
            ? std::sqrt(owner_velocity->vx * owner_velocity->vx +
                        owner_velocity->vy * owner_velocity->vy +
                        owner_velocity->vz * owner_velocity->vz)
            : 0.0;
        const double maritime_noise_bias_db = maritime_ambient_noise_bias_db(env_ref, owner, sonar);

        auto target_query = world.query<const KeyEntity, const Transform>();
        target_query.each([&](flecs::entity target, const KeyEntity& key, const Transform& target_transform) {
            if (target == owner) return;
            if (key.type != UnitType::Ship && key.type != UnitType::Submarine) return;
            if (owner_alliance) {
                if (const Alliance* target_alliance = target.get<Alliance>()) {
                    if (target_alliance->side == owner_alliance->side) return;
                }
            }

            const double dx = target_transform.x - owner_transform.x;
            const double dy = target_transform.y - owner_transform.y;
            const double dz = target_transform.z - owner_transform.z;
            const double range_m = std::sqrt(dx * dx + dy * dy + dz * dz);
            if (range_m <= 1.0 || range_m > sonar.max_range_m) return;

            const double rel_bearing_deg = nav_bearing_rel_deg(owner_transform, target_transform);
            const double aft_abs = std::abs(std::abs(rel_bearing_deg) - 180.0);
            if (aft_abs < std::max(0.0, sonar.baffle_exclusion_deg)) {
                return;
            }

            const Velocity* target_velocity = target.get<Velocity>();
            const double target_speed_mps = target_velocity
                ? std::sqrt(target_velocity->vx * target_velocity->vx +
                            target_velocity->vy * target_velocity->vy +
                            target_velocity->vz * target_velocity->vz)
                : 0.0;

            double snr_db = target_source_level_db(target, target_speed_mps, sonar);
            snr_db -= transmission_loss_db(range_m, sonar);
            snr_db += sonar.directivity_gain_db;
            snr_db -= ((sonar.ambient_noise_db + maritime_noise_bias_db) - 50.0);
            snr_db -= platform_self_noise_bias_db(owner, own_speed_mps);
            if (std::abs(dz) > 45.0) {
                snr_db -= std::max(0.0, sonar.layer_break_penalty_db);
            }

            const double margin_db = snr_db - sonar.detection_threshold_db;
            if (margin_db < 0.0) return;
            const double pd = std::clamp(0.55 + margin_db / 18.0, 0.0, 1.0);
            const std::uint64_t seed_base = static_cast<std::uint64_t>(current_time * 1000.0);
            const std::uint64_t seed = seed_base ^ (owner.id() * 0x9e3779b97f4a7c15ULL) ^ target.id();
            if (splitmix01(seed) > pd) return;

            double noisy_bearing = rel_bearing_deg;
            if (sonar.bearing_noise_std_deg > 0.0) {
                noisy_bearing += splitmix_normal(seed ^ 0xabc123ULL, seed ^ 0xdef456ULL) *
                    sonar.bearing_noise_std_deg;
            }
            double noisy_range = range_m;
            if (!sonar.bearing_only && sonar.range_noise_std_m > 0.0) {
                noisy_range += splitmix_normal(seed ^ 0x456abcULL, seed ^ 0x123defULL) *
                    sonar.range_noise_std_m;
                noisy_range = std::max(1.0, noisy_range);
            }

            double closing_speed = 0.0;
            if (owner_velocity && target_velocity && range_m > 1.0) {
                const double rx = dx / range_m;
                const double ry = dy / range_m;
                const double rz = dz / range_m;
                closing_speed = -((target_velocity->vx - owner_velocity->vx) * rx +
                                  (target_velocity->vy - owner_velocity->vy) * ry +
                                  (target_velocity->vz - owner_velocity->vz) * rz);
            }

            const double horiz_m = std::sqrt(std::max(0.0, dx * dx + dy * dy));
            const double elevation_deg = horiz_m > 1.0e-6
                ? std::atan2(dz, horiz_m) * 180.0 / M_PI
                : 0.0;

            Detection detection{};
            detection.target_id = target.id();
            detection.range = sonar.bearing_only ? 0.0 : noisy_range;
            detection.bearing = wrap_angle_deg(noisy_bearing);
            detection.elevation = elevation_deg;
            detection.closing_speed = closing_speed;
            detection.signal_strength = std::max(0.0, margin_db);
            detection.snr_db = snr_db;
            detection.detection_prob_used = pd;
            detection.measured_vr = closing_speed;
            detection.sensor_type = static_cast<int>(SensorType::Sonar);
            detection.local_sensor_hit = true;
            detection.timestamp = current_time;
            out_contacts.contacts.push_back(detection);
        });
    }
};

} // namespace

std::unique_ptr<IAcousticModel> make_default_acoustic_model() {
    return std::make_unique<DefaultAcousticModel>();
}
