#include "core/sensor_model.h"

#include <cmath>

#include "components/tags.h"

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

class DefaultSensorModel : public ISensorModel {
public:
    void scan(flecs::world world,
              flecs::entity owner,
              const Transform& owner_transform,
              const Sensor& sensor,
              ContactList& out_contacts,
              double current_time) override {
        auto target_query = world.query<Transform, SimObject>();

        target_query.each([&](flecs::entity target_e,
                              const Transform& target_t,
                              const SimObject& /*tag*/) {
            if (target_e == owner) return;

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
                out_contacts.contacts.push_back({
                    target_e.id(),
                    dist,
                    rel_bearing,
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
