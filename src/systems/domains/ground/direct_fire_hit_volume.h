#pragma once

#include <algorithm>
#include <limits>
#include <optional>
#include <utility>

#include "components/basic/common.h"
#include "components/domains/ground/ground_capabilities.h"

// Pure geometry for the authored infantry hit volumes. No environment access:
// the terrain owner is consulted by `direct_fire_line_of_sight.h`.
//
// Frame: the soldier's upright body frame. Its origin is the ground contact
// point under the entity Transform, `forward_m` follows the Transform heading,
// `right_m` is clockwise from forward, and `up_m` is height above the measured
// terrain at the contact point. The infantry body frame is upright by
// definition: posture is expressed by the authored per-stance volumes, not by
// Transform pitch or roll.
namespace ground_direct_fire_detail {

struct GroundBodyPoint {
    double forward_m = 0.0;
    double right_m = 0.0;
    double up_m = 0.0;
};

struct GroundWorldOffset {
    double east_m = 0.0;
    double north_m = 0.0;
};

[[nodiscard]] inline GroundWorldOffset upright_body_to_world_offset(double heading_deg,
                                                                    double forward_m,
                                                                    double right_m) {
    // The shared frame helpers take a Math body vector whose +y is left.
    const Math::Vector3 world = Math::body_to_world({forward_m, -right_m, 0.0}, heading_deg,
                                                    /*pitch_deg=*/0.0, /*roll_deg=*/0.0);
    return {world.x, world.y};
}

[[nodiscard]] inline GroundBodyPoint world_offset_to_upright_body(double heading_deg,
                                                                  double east_m, double north_m) {
    const Math::Vector3 body = Math::world_to_body({east_m, north_m, 0.0}, heading_deg,
                                                   /*pitch_deg=*/0.0, /*roll_deg=*/0.0);
    return {body.x, -body.y, 0.0};
}

[[nodiscard]] inline GroundBodyPoint hit_volume_center(const GroundInfantryHitVolume &volume) {
    return {volume.offset_forward_m, volume.offset_right_m, volume.offset_up_m};
}

// The point a rifle holds on when it aims at `region`. The torso is aimed at
// its horizontal centre at the authored centre-of-mass height, which the
// posture validation keeps inside the torso volume; the head and legs are
// aimed at their volume centres.
[[nodiscard]] inline GroundBodyPoint
ground_direct_fire_aim_point(const GroundInfantryPostureGeometry &posture,
                             GroundInfantryHitRegion region) {
    GroundBodyPoint aim = hit_volume_center(ground_infantry_hit_volume(posture, region));
    if (region == GroundInfantryHitRegion::Torso) {
        aim.up_m = posture.center_of_mass_height_m;
    }
    return aim;
}

// The interval of the ray `from + t * (to - from)`, t >= 0, that lies inside
// the box (slab method), or nullopt when the ray misses it. `to` is the aim
// point at t = 1; the ray continues past it, as the shot does. A ray that
// starts inside the box enters at 0.
struct GroundRayVolumeInterval {
    double enter = 0.0;
    double leave = 0.0;
};

[[nodiscard]] inline std::optional<GroundRayVolumeInterval>
ray_hit_volume_interval(const GroundBodyPoint &from, const GroundBodyPoint &to,
                        const GroundInfantryHitVolume &volume) {
    double enter = 0.0;
    double leave = std::numeric_limits<double>::infinity();
    const auto clip = [&enter, &leave](double origin, double delta, double center, double size) {
        const double low = center - size * 0.5;
        const double high = center + size * 0.5;
        if (delta == 0.0) {
            return origin >= low && origin <= high;
        }
        double t_low = (low - origin) / delta;
        double t_high = (high - origin) / delta;
        if (t_low > t_high) {
            std::swap(t_low, t_high);
        }
        enter = std::max(enter, t_low);
        leave = std::min(leave, t_high);
        return enter <= leave;
    };
    if (!clip(from.forward_m, to.forward_m - from.forward_m, volume.offset_forward_m,
              volume.size_forward_m) ||
        !clip(from.right_m, to.right_m - from.right_m, volume.offset_right_m,
              volume.size_right_m) ||
        !clip(from.up_m, to.up_m - from.up_m, volume.offset_up_m, volume.size_up_m)) {
        return std::nullopt;
    }
    return GroundRayVolumeInterval{enter, leave};
}

[[nodiscard]] inline GroundBodyPoint point_on_ray(const GroundBodyPoint &from,
                                                  const GroundBodyPoint &to, double fraction) {
    return {from.forward_m + (to.forward_m - from.forward_m) * fraction,
            from.right_m + (to.right_m - from.right_m) * fraction,
            from.up_m + (to.up_m - from.up_m) * fraction};
}

[[nodiscard]] inline bool box_axis_contains(double center, double size, double value) {
    return value >= center - size * 0.5 && value <= center + size * 0.5;
}

[[nodiscard]] inline bool hit_volume_contains(const GroundInfantryHitVolume &volume,
                                              const GroundBodyPoint &point) {
    return box_axis_contains(volume.offset_forward_m, volume.size_forward_m, point.forward_m) &&
           box_axis_contains(volume.offset_right_m, volume.size_right_m, point.right_m) &&
           box_axis_contains(volume.offset_up_m, volume.size_up_m, point.up_m);
}

// Exact per-axis affine map of a point from one region volume to the same
// normalised position inside another volume of the same region. It carries a
// held-stance hit point onto the standing region inventory that the shared
// `HitboxConfig` holds, so the shared effects route resolves the same region.
[[nodiscard]] inline GroundBodyPoint
map_point_between_hit_volumes(const GroundBodyPoint &point, const GroundInfantryHitVolume &from,
                              const GroundInfantryHitVolume &to) {
    const auto map_axis = [](double value, double from_center, double from_size, double to_center,
                             double to_size) {
        return to_center + (value - from_center) / from_size * to_size;
    };
    return {map_axis(point.forward_m, from.offset_forward_m, from.size_forward_m,
                     to.offset_forward_m, to.size_forward_m),
            map_axis(point.right_m, from.offset_right_m, from.size_right_m, to.offset_right_m,
                     to.size_right_m),
            map_axis(point.up_m, from.offset_up_m, from.size_up_m, to.offset_up_m, to.size_up_m)};
}

} // namespace ground_direct_fire_detail
