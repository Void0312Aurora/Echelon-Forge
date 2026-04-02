#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>

namespace gpu::missile_guidance_cuda {

inline constexpr std::size_t kContactSummaryCapacity = 8;

struct Transform {
    double x = 0.0;
    double y = 0.0;
    double z = 0.0;
    double heading = 0.0;
    double pitch = 0.0;
    double roll = 0.0;
};

struct Velocity {
    double vx = 0.0;
    double vy = 0.0;
    double vz = 0.0;
};

struct Detection {
    std::uint64_t target_id = 0;
    double range = 0.0;
    double bearing = 0.0;
    double elevation = 0.0;
    double closing_speed = 0.0;
    double signal_strength = 0.0;
    double timestamp = 0.0;
};

struct ContactListSummary {
    std::uint32_t count = 0;
    bool truncated = false;
    Detection contacts[kContactSummaryCapacity]{};
};

struct Missile {
    std::uint64_t attacker_id = 0;
    std::uint64_t target_id = 0;
    double max_speed = 0.0;
    double turn_rate = 0.0;
    double fuse_distance = 0.0;
    double damage = 0.0;
    double seeker_fov_deg = 0.0;
    double seeker_lock_range = 0.0;
    double guidance_delay_s = 0.0;
    double guidance_update_period_s = 0.0;
    double last_guidance_time = 0.0;
    double launch_time = 0.0;
    double max_flight_time_s = 0.0;
    double nav_gain = 0.0;
    bool active = false;
    std::uint64_t rng_state = 0;
    double proximity_min_dist_m = std::numeric_limits<double>::infinity();
    double proximity_last_dist_m = std::numeric_limits<double>::infinity();
    bool proximity_engaged = false;
};

struct ExactWorldStepMissileGuidanceCudaState {
    std::uint64_t entity_id = 0;
    double time_step_s = 1.0 / 60.0;
    double world_time_s = 0.0;

    Transform transform{};
    Velocity velocity{};
    Missile missile{};
    ContactListSummary contact_list_summary{};

    bool has_missile = false;
    bool has_contact_list_summary = false;
};

}  // namespace gpu::missile_guidance_cuda
