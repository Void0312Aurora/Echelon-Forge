#include "core/sensor_model.h"

#include <algorithm>
#include <cmath>
#include <cstdint>

namespace {

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

double wrap_angle_360(double angle) {
    while (angle < 0.0) angle += 360.0;
    while (angle >= 360.0) angle -= 360.0;
    return angle;
}

double normalize_angle_deg(double angle) {
    while (angle > 180.0) angle -= 360.0;
    while (angle < -180.0) angle += 360.0;
    return angle;
}

double math_deg_to_nav_deg(double math_deg) {
    return wrap_angle_360(90.0 - math_deg);
}

uint64_t splitmix64(uint64_t seed) {
    uint64_t z = seed + 0x9e3779b97f4a7c15ULL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

double rand_uniform01(uint64_t seed) {
    uint64_t z = splitmix64(seed);
    return (z >> 11) * (1.0 / 9007199254740992.0);
}

double rand_normal(uint64_t seed_a, uint64_t seed_b) {
    double u1 = std::max(1e-12, rand_uniform01(seed_a));
    double u2 = rand_uniform01(seed_b);
    return std::sqrt(-2.0 * std::log(u1)) * std::cos(2.0 * M_PI * u2);
}

class DefaultSensorModel : public ISensorModel {
public:
    void scan(flecs::world world,
              flecs::entity owner,
              const Transform& owner_transform,
              const Sensor& sensor,
              ContactList& out_contacts,
              double current_time) override {
        auto target_query = world.query<const KeyEntity, const Transform>();

        target_query.each([&](flecs::entity target_e,
                              const KeyEntity& /*key*/,
                              const Transform& target_t) {
            if (target_e == owner) return;
            if (sensor.max_range <= 0.0 || sensor.detection_prob <= 0.0) return;

            double dx = target_t.x - owner_transform.x;
            double dy = target_t.y - owner_transform.y;
            double dz = target_t.z - owner_transform.z;
            double dist_sq = dx * dx + dy * dy + dz * dz;
            double max_sq = sensor.max_range * sensor.max_range;

            if (dist_sq > max_sq) return;

            double dist = std::sqrt(dist_sq);
            double bearing_rad = std::atan2(dy, dx);
            double bearing_math_deg = bearing_rad * 180.0 / M_PI;
            double bearing_nav_deg = math_deg_to_nav_deg(bearing_math_deg);
            double rel_bearing = normalize_angle_deg(bearing_nav_deg - owner_transform.heading);

            if (std::abs(rel_bearing) <= sensor.fov_deg / 2.0) {
                double range_ratio = std::clamp(dist / sensor.max_range, 0.0, 1.0);
                double range_power = (sensor.range_power > 0.0) ? sensor.range_power : 1.0;
                double range_factor = 1.0 - std::pow(range_ratio, range_power);
                range_factor = std::clamp(range_factor, 0.0, 1.0);

                double aspect_factor = 1.0;
                double aspect_weight = std::clamp(sensor.aspect_influence, 0.0, 1.0);
                if (aspect_weight > 0.0) {
                    double los_math_deg = std::atan2(owner_transform.y - target_t.y,
                                                     owner_transform.x - target_t.x) * 180.0 / M_PI;
                    double los_nav_deg = math_deg_to_nav_deg(los_math_deg);
                    double aspect_deg = normalize_angle_deg(los_nav_deg - target_t.heading);
                    double aspect_cos = std::cos(aspect_deg * M_PI / 180.0);
                    double aspect_scale = 0.5 + 0.5 * aspect_cos;
                    aspect_factor = (1.0 - aspect_weight) + aspect_weight * aspect_scale;
                }

                double detection_prob = sensor.detection_prob * range_factor * aspect_factor;
                detection_prob = std::clamp(detection_prob, 0.0, 1.0);

                uint64_t seed_base = static_cast<uint64_t>(current_time * 1000.0);
                uint64_t seed_det = seed_base ^ (owner.id() * 0x9e3779b97f4a7c15ULL) ^
                                    (target_e.id() * 0xbf58476d1ce4e5b9ULL);
                if (rand_uniform01(seed_det) > detection_prob) {
                    return;
                }

                double noisy_bearing = rel_bearing;
                if (sensor.bearing_noise_std > 0.0) {
                    noisy_bearing += rand_normal(seed_det ^ 0x12345678ULL,
                                                 seed_det ^ 0x9abcdef0ULL) *
                                     sensor.bearing_noise_std;
                }
                double noisy_range = dist;
                if (sensor.range_noise_std > 0.0) {
                    noisy_range += rand_normal(seed_det ^ 0x87654321ULL,
                                               seed_det ^ 0x0fedcba9ULL) *
                                   sensor.range_noise_std;
                }
                noisy_range = std::max(0.0, noisy_range);

                out_contacts.contacts.push_back({
                    target_e.id(),
                    noisy_range,
                    normalize_angle_deg(noisy_bearing),
                    current_time
                });
            }
        });
    }
};

} // namespace

std::unique_ptr<ISensorModel> make_default_sensor_model() {
    return std::make_unique<DefaultSensorModel>();
}
