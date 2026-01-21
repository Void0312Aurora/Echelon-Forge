#include "core/interfaces/sensor_model.h"
#include "core/interfaces/environment_model.h"
#include "components/systems/ew.h"

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
        
        // Environment Singleton Access
        const EnvironmentModelRef* env_ref = world.get<EnvironmentModelRef>();

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

            // Phase 2 & 3: Environment Checks
            double weath_factor = 1.0;
            double sun_factor = 1.0;

            if (env_ref && env_ref->model) {
                // 1. Line of Sight
                if (!env_ref->model->check_line_of_sight(
                        owner_transform.x, owner_transform.y, owner_transform.z,
                        target_t.x, target_t.y, target_t.z)) {
                    return; // Obscured
                }

                // 2. Weather Attenuation
                double att = env_ref->model->get_weather_attenuation(
                        owner_transform.x, owner_transform.y, owner_transform.z,
                        target_t.x, target_t.y, target_t.z, sensor.type);
                weath_factor = 1.0 - att;

                // 3. Sun Glare (Visual/IR)
                if (sensor.type <= 1) { // 0=Visual, 1=IR
                    Vec3 sun = env_ref->model->get_sun_direction();
                    // Dot product of (ToTarget) and (Sun)
                    if (dist > 1.0) {
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

                // Doppler Logic
                const Velocity* owner_v = world.entity(owner).get<Velocity>();
                const Velocity* target_v = target_e.get<Velocity>();
                
                double doppler_factor = 1.0;

                // RWR Update (Electronic Warfare)
                // If Owner is a Radar, painting the target
                if (sensor.type == 2) {
                    // We use get_mut because we are modifying the Target's RWR state
                    RWR* target_rwr = target_e.get_mut<RWR>();
                    if (target_rwr) {
                        // Sensitivity Check (Simplified: Range * 1.5)
                        if (dist < sensor.max_range * 1.5) {
                            bool found = false;
                            for (auto id : target_rwr->detected_radar_ids) {
                                if (id == owner.id()) { found = true; break; }
                            }
                            if (!found) {
                                target_rwr->detected_radar_ids.push_back(owner.id());
                            }
                        }
                    }
                }
                
                double v_closing = 0.0;
                if (owner_v && target_v && dist > 1.0) {
                    double rx = dx / dist;
                    double ry = dy / dist;
                    double rz = dz / dist;
                    
                    double v_rel_x = target_v->vx - owner_v->vx;
                    double v_rel_y = target_v->vy - owner_v->vy;
                    double v_rel_z = target_v->vz - owner_v->vz;
                    
                    v_closing = -(v_rel_x * rx + v_rel_y * ry + v_rel_z * rz);
                    
                    constexpr double kDopplerGate = 25.0; 
                    if (std::abs(v_closing) < kDopplerGate) {
                         doppler_factor = 0.1;
                    }
                }

                double detection_prob = sensor.detection_prob * range_factor * aspect_factor * doppler_factor * weath_factor * sun_factor;
                detection_prob = std::clamp(detection_prob, 0.0, 1.0);

                uint64_t seed_base = static_cast<uint64_t>(current_time * 1000.0);
                uint64_t seed_det = seed_base ^ (owner.id() * 0x9e3779b97f4a7c15ULL) ^
                                    (target_e.id() * 0xbf58476d1ce4e5b9ULL);
                if (rand_uniform01(seed_det) > detection_prob) {
                    return;
                }
                
                double horizontal_dist = std::sqrt(std::max(0.0, dx * dx + dy * dy));
                double elevation_deg = 0.0;
                if (horizontal_dist > 1e-6) {
                    elevation_deg = std::atan2(dz, horizontal_dist) * 180.0 / M_PI;
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

                double signal_strength = 0.0;
                double rcs = 5.0; // Default RCS
                const RCSProfile* rcs_prof = target_e.get<RCSProfile>();
                if (rcs_prof) {
                    // Simple omni-directional fallback or frontal
                    rcs = rcs_prof->frontal_rcs; 
                    // TODO: Calculate based on aspect
                }

                if (sensor.type == 2) {
                     // Radar Equation: Prop to RCS / R^4
                     if (dist > 1.0) {
                        signal_strength = rcs / (dist_sq * dist_sq); 
                     } else {
                        signal_strength = rcs;
                     }

                     // Phase 3: Suppression Jamming (Burn-Through)
                     const Jammer* jammer = target_e.get<Jammer>();
                     if (jammer && jammer->is_active && 
                         (jammer->type == JammingType::NoiseBarrage || jammer->type == JammingType::NoiseSpot)) {
                         
                         // Burn-Through Range: R_bt = K * sqrt(sigma / P_j)
                         // K derived from R_bt=20km, sigma=5, P_j=1000 => K ~ 283000
                         const double K_BT = 283000.0; 
                         double p_j = jammer->power_watts > 1.0 ? jammer->power_watts : 1.0;
                         double r_bt = K_BT * std::sqrt(rcs / p_j);

                         if (dist > r_bt) {
                             // Jamming Effective: Target hidden (Noise suppressed)
                             return; 
                         }
                     }
                } else if (sensor.type == 1) {
                     // IR: Prop to Heat / R^2
                     // Hack: If target has Lifetime (Decoy) assume Flare
                     if (target_e.has<Lifetime>()) {
                         signal_strength = 500.0 / dist_sq;
                     } else {
                         signal_strength = 50.0 / dist_sq;
                     }
                } else {
                     // Visual
                     signal_strength = 1.0 / dist_sq;
                }

                out_contacts.contacts.push_back({
                    target_e.id(),
                    noisy_range,
                    normalize_angle_deg(noisy_bearing),
                    std::clamp(elevation_deg, -90.0, 90.0),
                    v_closing,
                    signal_strength,
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
