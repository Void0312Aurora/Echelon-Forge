// Private fragment for default_effects_model.cpp.
// Included inside that file's anonymous namespace; not a standalone API.

// Geometry Helpers
struct Vec3 { double x, y, z; };

double vec3_norm(const Vec3& value) {
    return std::sqrt(value.x * value.x + value.y * value.y + value.z * value.z);
}

Vec3 vec3_normalize(const Vec3& value) {
    const double norm = vec3_norm(value);
    if (norm <= 1.0e-9) {
        return {0.0, 0.0, 0.0};
    }
    return {value.x / norm, value.y / norm, value.z / norm};
}

double vec3_dot(const Vec3& lhs, const Vec3& rhs) {
    return lhs.x * rhs.x + lhs.y * rhs.y + lhs.z * rhs.z;
}

bool vec3_is_finite(const Vec3& value) {
    return std::isfinite(value.x) && std::isfinite(value.y) && std::isfinite(value.z);
}

Vec3 math_to_vec3(const Math::Vector3& value) {
    return {value.x, value.y, value.z};
}

Vec3 math_body_to_local_right_frame(const Math::Vector3& value) {
    return {value.x, -value.y, value.z};
}

Vec3 world_to_body(const Transform& t, double wx, double wy, double wz) {
    return math_body_to_local_right_frame(
        Math::world_to_body(
            {wx - t.x, wy - t.y, wz - t.z},
            t));
}

uint64_t splitmix64(uint64_t& state) {
    uint64_t z = (state += 0x9e3779b97f4a7c15ULL);
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
    return z ^ (z >> 31);
}

double rand_uniform01(uint64_t& state) {
    // 53 random bits / 2^53
    return (splitmix64(state) >> 11) * (1.0 / 9007199254740992.0);
}

bool check_hitbox(const Vec3& local_p, const Hitbox& box) {
    // Check if point is inside box (centered at offset)
    double min_x = box.offset_x - box.dim_l * 0.5;
    double max_x = box.offset_x + box.dim_l * 0.5;
    double min_y = box.offset_y - box.dim_w * 0.5;
    double max_y = box.offset_y + box.dim_w * 0.5;
    double min_z = box.offset_z - box.dim_h * 0.5;
    double max_z = box.offset_z + box.dim_h * 0.5;

    return (local_p.x >= min_x && local_p.x <= max_x &&
            local_p.y >= min_y && local_p.y <= max_y &&
            local_p.z >= min_z && local_p.z <= max_z);
}

double hitbox_surface_distance(const Vec3& local_p, const Hitbox& box) {
    const double min_x = box.offset_x - box.dim_l * 0.5;
    const double max_x = box.offset_x + box.dim_l * 0.5;
    const double min_y = box.offset_y - box.dim_w * 0.5;
    const double max_y = box.offset_y + box.dim_w * 0.5;
    const double min_z = box.offset_z - box.dim_h * 0.5;
    const double max_z = box.offset_z + box.dim_h * 0.5;

    const double dx = std::max({min_x - local_p.x, 0.0, local_p.x - max_x});
    const double dy = std::max({min_y - local_p.y, 0.0, local_p.y - max_y});
    const double dz = std::max({min_z - local_p.z, 0.0, local_p.z - max_z});
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

Vec3 hitbox_nearest_point(const Vec3& local_p, const Hitbox& box) {
    const double min_x = box.offset_x - box.dim_l * 0.5;
    const double max_x = box.offset_x + box.dim_l * 0.5;
    const double min_y = box.offset_y - box.dim_w * 0.5;
    const double max_y = box.offset_y + box.dim_w * 0.5;
    const double min_z = box.offset_z - box.dim_h * 0.5;
    const double max_z = box.offset_z + box.dim_h * 0.5;
    return {
        std::clamp(local_p.x, min_x, max_x),
        std::clamp(local_p.y, min_y, max_y),
        std::clamp(local_p.z, min_z, max_z),
    };
}

double hitbox_surface_incidence_cos(
    const Vec3& local_p,
    const Hitbox& box,
    const Vec3& missile_axis_body
) {
    const Vec3 axis = vec3_normalize(missile_axis_body);
    if (!vec3_is_finite(local_p) || !vec3_is_finite(axis) || vec3_norm(axis) <= 1.0e-9 ||
        !std::isfinite(box.offset_x) || !std::isfinite(box.offset_y) ||
        !std::isfinite(box.offset_z) || !std::isfinite(box.dim_l) ||
        !std::isfinite(box.dim_w) || !std::isfinite(box.dim_h) ||
        box.dim_l <= 0.0 || box.dim_w <= 0.0 || box.dim_h <= 0.0) {
        return 0.0;
    }

    const double min_x = box.offset_x - box.dim_l * 0.5;
    const double max_x = box.offset_x + box.dim_l * 0.5;
    const double min_y = box.offset_y - box.dim_w * 0.5;
    const double max_y = box.offset_y + box.dim_w * 0.5;
    const double min_z = box.offset_z - box.dim_h * 0.5;
    const double max_z = box.offset_z + box.dim_h * 0.5;

    bool has_candidate = false;
    double incidence_cos = 1.0;
    const auto consider_face = [&](const Vec3& normal) {
        const double candidate =
            std::clamp(std::abs(vec3_dot(axis, normal)), 0.0, 1.0);
        incidence_cos = has_candidate ? std::min(incidence_cos, candidate) : candidate;
        has_candidate = true;
    };

    if (local_p.x < min_x) {
        consider_face({-1.0, 0.0, 0.0});
    } else if (local_p.x > max_x) {
        consider_face({1.0, 0.0, 0.0});
    }
    if (local_p.y < min_y) {
        consider_face({0.0, -1.0, 0.0});
    } else if (local_p.y > max_y) {
        consider_face({0.0, 1.0, 0.0});
    }
    if (local_p.z < min_z) {
        consider_face({0.0, 0.0, -1.0});
    } else if (local_p.z > max_z) {
        consider_face({0.0, 0.0, 1.0});
    }
    if (has_candidate) {
        return incidence_cos;
    }

    const double distances[] = {
        std::abs(local_p.x - min_x),
        std::abs(max_x - local_p.x),
        std::abs(local_p.y - min_y),
        std::abs(max_y - local_p.y),
        std::abs(local_p.z - min_z),
        std::abs(max_z - local_p.z),
    };
    const double nearest_distance = *std::min_element(std::begin(distances), std::end(distances));
    const double epsilon = 1.0e-9;
    if (distances[0] <= nearest_distance + epsilon) {
        consider_face({-1.0, 0.0, 0.0});
    }
    if (distances[1] <= nearest_distance + epsilon) {
        consider_face({1.0, 0.0, 0.0});
    }
    if (distances[2] <= nearest_distance + epsilon) {
        consider_face({0.0, -1.0, 0.0});
    }
    if (distances[3] <= nearest_distance + epsilon) {
        consider_face({0.0, 1.0, 0.0});
    }
    if (distances[4] <= nearest_distance + epsilon) {
        consider_face({0.0, 0.0, -1.0});
    }
    if (distances[5] <= nearest_distance + epsilon) {
        consider_face({0.0, 0.0, 1.0});
    }
    return has_candidate ? incidence_cos : 0.0;
}

struct ComponentAxisBounds {
    Vec3 minimum;
    Vec3 maximum;
};

Vec3 component_geometry_axis(const DamageComponent& component, std::size_t index) {
    if (index >= component.geometry_axes.size()) {
        return index == 0 ? Vec3{1.0, 0.0, 0.0}
             : index == 1 ? Vec3{0.0, 1.0, 0.0}
                          : Vec3{0.0, 0.0, 1.0};
    }
    const auto& axis = component.geometry_axes[index];
    const Vec3 candidate{axis[0], axis[1], axis[2]};
    const Vec3 normalized = vec3_normalize(candidate);
    if (vec3_norm(normalized) <= 1.0e-9) {
        return index == 0 ? Vec3{1.0, 0.0, 0.0}
             : index == 1 ? Vec3{0.0, 1.0, 0.0}
                          : Vec3{0.0, 0.0, 1.0};
    }
    return normalized;
}

Vec3 component_geometry_half_extents(const DamageComponent& component) {
    return {
        component.geometry_half_extents_m[0] > 0.0
            ? component.geometry_half_extents_m[0]
            : component.dim_l * 0.5,
        component.geometry_half_extents_m[1] > 0.0
            ? component.geometry_half_extents_m[1]
            : component.dim_w * 0.5,
        component.geometry_half_extents_m[2] > 0.0
            ? component.geometry_half_extents_m[2]
            : component.dim_h * 0.5,
    };
}

bool component_uses_obb_like_geometry(const DamageComponent& component) {
    return component.geometry_primitive == "obb" ||
        component.geometry_primitive == "thin_prism";
}

Vec3 component_obb_local_coordinates(
    const Vec3& local_p,
    const DamageComponent& component
) {
    const Vec3 delta{
        local_p.x - component.offset_x,
        local_p.y - component.offset_y,
        local_p.z - component.offset_z,
    };
    return {
        vec3_dot(delta, component_geometry_axis(component, 0)),
        vec3_dot(delta, component_geometry_axis(component, 1)),
        vec3_dot(delta, component_geometry_axis(component, 2)),
    };
}

Vec3 component_obb_world_coordinates(
    const Vec3& local_p,
    const DamageComponent& component
) {
    const Vec3 axis_x = component_geometry_axis(component, 0);
    const Vec3 axis_y = component_geometry_axis(component, 1);
    const Vec3 axis_z = component_geometry_axis(component, 2);
    return {
        component.offset_x +
            axis_x.x * local_p.x + axis_y.x * local_p.y + axis_z.x * local_p.z,
        component.offset_y +
            axis_x.y * local_p.x + axis_y.y * local_p.y + axis_z.y * local_p.z,
        component.offset_z +
            axis_x.z * local_p.x + axis_y.z * local_p.y + axis_z.z * local_p.z,
    };
}

ComponentAxisBounds component_axis_aligned_bounds(const DamageComponent& component) {
    if (component.geometry_primitive == "convex_hull" &&
        !component.geometry_vertices_m.empty()) {
        Vec3 minimum{
            component.geometry_vertices_m.front()[0],
            component.geometry_vertices_m.front()[1],
            component.geometry_vertices_m.front()[2],
        };
        Vec3 maximum = minimum;
        for (const auto& vertex : component.geometry_vertices_m) {
            minimum.x = std::min(minimum.x, vertex[0]);
            minimum.y = std::min(minimum.y, vertex[1]);
            minimum.z = std::min(minimum.z, vertex[2]);
            maximum.x = std::max(maximum.x, vertex[0]);
            maximum.y = std::max(maximum.y, vertex[1]);
            maximum.z = std::max(maximum.z, vertex[2]);
        }
        return {minimum, maximum};
    }
    if (component_uses_obb_like_geometry(component)) {
        const Vec3 half = component_geometry_half_extents(component);
        const Vec3 axis_x = component_geometry_axis(component, 0);
        const Vec3 axis_y = component_geometry_axis(component, 1);
        const Vec3 axis_z = component_geometry_axis(component, 2);
        const Vec3 span{
            2.0 * (
                std::abs(axis_x.x) * half.x +
                std::abs(axis_y.x) * half.y +
                std::abs(axis_z.x) * half.z),
            2.0 * (
                std::abs(axis_x.y) * half.x +
                std::abs(axis_y.y) * half.y +
                std::abs(axis_z.y) * half.z),
            2.0 * (
                std::abs(axis_x.z) * half.x +
                std::abs(axis_y.z) * half.y +
                std::abs(axis_z.z) * half.z),
        };
        return {
            {component.offset_x - span.x * 0.5,
             component.offset_y - span.y * 0.5,
             component.offset_z - span.z * 0.5},
            {component.offset_x + span.x * 0.5,
             component.offset_y + span.y * 0.5,
             component.offset_z + span.z * 0.5},
        };
    }
    return {
        {component.offset_x - component.dim_l * 0.5,
         component.offset_y - component.dim_w * 0.5,
         component.offset_z - component.dim_h * 0.5},
        {component.offset_x + component.dim_l * 0.5,
         component.offset_y + component.dim_w * 0.5,
         component.offset_z + component.dim_h * 0.5},
    };
}

bool check_component(const Vec3& local_p, const DamageComponent& component) {
    if (component_uses_obb_like_geometry(component)) {
        const Vec3 local = component_obb_local_coordinates(local_p, component);
        const Vec3 half = component_geometry_half_extents(component);
        return std::abs(local.x) <= half.x &&
            std::abs(local.y) <= half.y &&
            std::abs(local.z) <= half.z;
    }
    const ComponentAxisBounds bounds = component_axis_aligned_bounds(component);
    return (local_p.x >= bounds.minimum.x && local_p.x <= bounds.maximum.x &&
            local_p.y >= bounds.minimum.y && local_p.y <= bounds.maximum.y &&
            local_p.z >= bounds.minimum.z && local_p.z <= bounds.maximum.z);
}

double component_surface_distance(const Vec3& local_p, const DamageComponent& component) {
    if (component_uses_obb_like_geometry(component)) {
        const Vec3 local = component_obb_local_coordinates(local_p, component);
        const Vec3 half = component_geometry_half_extents(component);
        const double dx = std::max({-half.x - local.x, 0.0, local.x - half.x});
        const double dy = std::max({-half.y - local.y, 0.0, local.y - half.y});
        const double dz = std::max({-half.z - local.z, 0.0, local.z - half.z});
        return std::sqrt(dx * dx + dy * dy + dz * dz);
    }
    const ComponentAxisBounds bounds = component_axis_aligned_bounds(component);
    const double dx = std::max({bounds.minimum.x - local_p.x, 0.0, local_p.x - bounds.maximum.x});
    const double dy = std::max({bounds.minimum.y - local_p.y, 0.0, local_p.y - bounds.maximum.y});
    const double dz = std::max({bounds.minimum.z - local_p.z, 0.0, local_p.z - bounds.maximum.z});
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

Vec3 component_nearest_point(const Vec3& local_p, const DamageComponent& component) {
    if (component_uses_obb_like_geometry(component)) {
        const Vec3 local = component_obb_local_coordinates(local_p, component);
        const Vec3 half = component_geometry_half_extents(component);
        return component_obb_world_coordinates(
            {
                std::clamp(local.x, -half.x, half.x),
                std::clamp(local.y, -half.y, half.y),
                std::clamp(local.z, -half.z, half.z),
            },
            component);
    }
    const ComponentAxisBounds bounds = component_axis_aligned_bounds(component);
    return {
        std::clamp(local_p.x, bounds.minimum.x, bounds.maximum.x),
        std::clamp(local_p.y, bounds.minimum.y, bounds.maximum.y),
        std::clamp(local_p.z, bounds.minimum.z, bounds.maximum.z),
    };
}

Vec3 component_effective_dimensions(const DamageComponent& component) {
    if (component_uses_obb_like_geometry(component)) {
        const Vec3 half = component_geometry_half_extents(component);
        return {2.0 * half.x, 2.0 * half.y, 2.0 * half.z};
    }
    const ComponentAxisBounds bounds = component_axis_aligned_bounds(component);
    return {
        std::max(1.0e-6, bounds.maximum.x - bounds.minimum.x),
        std::max(1.0e-6, bounds.maximum.y - bounds.minimum.y),
        std::max(1.0e-6, bounds.maximum.z - bounds.minimum.z),
    };
}

double component_projected_exposure_scale(const Vec3& local_imp, const DamageComponent& component) {
    const Vec3 nearest = component_nearest_point(local_imp, component);
    const Vec3 ray = vec3_normalize({
        nearest.x - local_imp.x,
        nearest.y - local_imp.y,
        nearest.z - local_imp.z,
    });
    if (vec3_norm(ray) <= 1.0e-9) {
        return 1.0;
    }

    const Vec3 dims = component_effective_dimensions(component);
    const double area_forward = std::max(1.0e-6, dims.y * dims.z);
    const double area_side = std::max(1.0e-6, dims.x * dims.z);
    const double area_top = std::max(1.0e-6, dims.x * dims.y);
    const double projected_area =
        (std::abs(ray.x) * area_forward) +
        (std::abs(ray.y) * area_side) +
        (std::abs(ray.z) * area_top);
    const double reference_area = std::max({area_forward, area_side, area_top, 1.0e-6});
    return std::clamp(0.45 + 0.55 * (projected_area / reference_area), 0.45, 1.0);
}

Hitbox component_as_hitbox(const DamageComponent& component, const Hitbox& parent) {
    Hitbox box = parent;
    const ComponentAxisBounds bounds = component_axis_aligned_bounds(component);
    box.offset_x = (bounds.minimum.x + bounds.maximum.x) * 0.5;
    box.offset_y = (bounds.minimum.y + bounds.maximum.y) * 0.5;
    box.offset_z = (bounds.minimum.z + bounds.maximum.z) * 0.5;
    box.dim_l = std::max(1.0e-6, bounds.maximum.x - bounds.minimum.x);
    box.dim_w = std::max(1.0e-6, bounds.maximum.y - bounds.minimum.y);
    box.dim_h = std::max(1.0e-6, bounds.maximum.z - bounds.minimum.z);
    box.armor_mm = component.armor_mm;
    box.protected_systems = {component.system};
    box.components.clear();
    return box;
}

bool system_name_matches(const std::string& system, const char* token) {
    return system.find(token) != std::string::npos;
}

bool system_is_air_control_surface(const std::string& system) {
    return system_name_matches(system, "flight_control") ||
        system_name_matches(system, "control") ||
        system_name_matches(system, "hydraulic");
}

bool system_is_air_sensor(const std::string& system) {
    return system_name_matches(system, "radar") ||
        system_name_matches(system, "sensor") ||
        system_name_matches(system, "rwr") ||
        system_name_matches(system, "esm");
}

bool system_is_air_propulsion_or_fuel(const std::string& system) {
    return system_name_matches(system, "engineering") ||
        system_name_matches(system, "engine") ||
        system_name_matches(system, "fuel") ||
        system_name_matches(system, "propeller") ||
        system_name_matches(system, "transmission");
}

bool system_is_air_propulsion(const std::string& system) {
    return system_name_matches(system, "engineering") ||
        system_name_matches(system, "engine") ||
        system_name_matches(system, "propeller") ||
        system_name_matches(system, "transmission");
}

bool system_is_air_fuel(const std::string& system) {
    return system_name_matches(system, "fuel");
}

bool system_is_air_fire_suppression(const std::string& system) {
    return system_name_matches(system, "fire_suppression") ||
        system_name_matches(system, "fire_bottle") ||
        system_name_matches(system, "suppression") ||
        system_name_matches(system, "extinguish");
}

bool system_is_crew_or_cockpit(const std::string& system) {
    return system_name_matches(system, "cockpit") ||
        system_name_matches(system, "pilot") ||
        system_name_matches(system, "crew");
}

bool system_is_command_navigation(const std::string& system) {
    return system_name_matches(system, "command") ||
        system_name_matches(system, "navigation");
}

bool system_is_mission_crew_station(const std::string& system) {
    return system_name_matches(system, "operator") ||
        system_name_matches(system, "crew");
}

enum class CrewConsequenceKind {
    None,
    Pilot,
    MissionCrew,
    CommandNavigation,
};

CrewConsequenceKind classify_crew_consequence(
    const std::string& system,
    const std::string& component_name
) {
    const std::string& name = component_name.empty() ? system : component_name;
    if (system_name_matches(system, "cockpit") ||
        system_name_matches(system, "pilot") ||
        system_name_matches(name, "flight_deck") ||
        system_name_matches(name, "cockpit") ||
        system_name_matches(name, "pilot")) {
        return CrewConsequenceKind::Pilot;
    }
    if (system_name_matches(system, "command") ||
        system_name_matches(system, "navigation") ||
        system_name_matches(name, "command") ||
        system_name_matches(name, "navigation")) {
        return CrewConsequenceKind::CommandNavigation;
    }
    if (system_name_matches(name, "mission_operator") ||
        system_name_matches(name, "operator") ||
        system_name_matches(name, "console")) {
        return CrewConsequenceKind::MissionCrew;
    }
    if (system_is_crew_or_cockpit(system)) {
        return CrewConsequenceKind::Pilot;
    }
    return CrewConsequenceKind::None;
}

void apply_aircraft_crew_consequence(
    AircraftDamageState& aircraft_damage,
    CrewConsequenceKind kind,
    double delta
) {
    const double resolved_delta = std::clamp(delta, 0.0, 1.0);
    if (resolved_delta <= 0.0 || kind == CrewConsequenceKind::None) {
        return;
    }
    if (kind == CrewConsequenceKind::Pilot) {
        aircraft_damage.pilot_effectiveness -= resolved_delta;
        aircraft_damage.crew_effectiveness -= 0.85 * resolved_delta;
        aircraft_damage.flight_control_integrity -= 0.18 * resolved_delta;
    } else if (kind == CrewConsequenceKind::MissionCrew) {
        aircraft_damage.mission_crew_effectiveness -= resolved_delta;
        aircraft_damage.crew_effectiveness -= 0.55 * resolved_delta;
        aircraft_damage.avionics_integrity -= 0.18 * resolved_delta;
    } else if (kind == CrewConsequenceKind::CommandNavigation) {
        aircraft_damage.command_navigation_integrity -= resolved_delta;
        aircraft_damage.crew_effectiveness -= 0.65 * resolved_delta;
        aircraft_damage.avionics_integrity -= 0.10 * resolved_delta;
    }
}

bool system_is_mission_or_combat(const std::string& system) {
    return system_name_matches(system, "combat") ||
        system_name_matches(system, "command") ||
        system_name_matches(system, "data_link") ||
        system_name_matches(system, "vls") ||
        system_name_matches(system, "gun") ||
        system_name_matches(system, "radar") ||
        system_name_matches(system, "avionics") ||
        system_name_matches(system, "navigation") ||
        system_name_matches(system, "mission");
}

bool system_is_air_structure(const std::string& system) {
    return system_name_matches(system, "wing") ||
        system_name_matches(system, "airframe") ||
        system_name_matches(system, "fuselage") ||
        system_name_matches(system, "structure") ||
        system_name_matches(system, "rotor") ||
        system_name_matches(system, "tail");
}

bool component_is_engine_fuel_feed_path(const DamageComponent& component) {
    const std::string name = damage_component_key(component);
    return system_name_matches(name, "fuel_feed") ||
        system_name_matches(name, "fuel_control") ||
        (system_name_matches(name, "engine") && system_name_matches(name, "fuel"));
}

bool component_is_fire_suppression_path(const DamageComponent& component) {
    const std::string name = damage_component_key(component);
    const std::string group = damage_component_redundancy_group_key(component);
    return system_is_air_fire_suppression(component.system) ||
        system_name_matches(name, "fire_bottle") ||
        system_name_matches(name, "fire_suppression") ||
        system_name_matches(name, "suppression") ||
        system_name_matches(group, "fire_suppression") ||
        system_name_matches(group, "fire_bottle");
}

bool component_is_lateral_fuel_storage_path(const DamageComponent& component) {
    if (!system_is_air_fuel(component.system) ||
        component_is_engine_fuel_feed_path(component) ||
        component_is_fire_suppression_path(component)) {
        return false;
    }
    const std::string name = damage_component_key(component);
    return system_name_matches(name, "left") ||
        system_name_matches(name, "right");
}

bool component_is_hydraulic_supply_path(const DamageComponent& component) {
    const std::string name = damage_component_key(component);
    const std::string group = damage_component_redundancy_group_key(component);
    return system_name_matches(component.system, "hydraulic") ||
        (system_name_matches(name, "hydraulic") &&
         (system_name_matches(name, "pump") ||
          system_name_matches(name, "reservoir") ||
          system_name_matches(name, "supply") ||
          system_name_matches(name, "line") ||
          system_name_matches(name, "module"))) ||
        (system_name_matches(group, "hydraulic") &&
         (system_name_matches(group, "supply") ||
          system_name_matches(group, "pump")));
}

bool component_depends_on_hydraulic_power(const DamageComponent& component) {
    for (const auto& dependency : component.dependencies) {
        const bool hydraulic_target =
            system_name_matches(dependency.target_system, "hydraulic") ||
            system_name_matches(dependency.system, "hydraulic");
        const bool hydraulic_edge =
            dependency.edge_type == "hydraulic_power" ||
            dependency.edge_type == "hydraulic-power";
        if (hydraulic_target || hydraulic_edge) {
            return true;
        }
    }
    return false;
}

bool component_is_hydraulic_consumer_path(const DamageComponent& component) {
    if (component_is_hydraulic_supply_path(component)) {
        return false;
    }
    const std::string name = damage_component_key(component);
    return component_depends_on_hydraulic_power(component) ||
        ((system_is_air_control_surface(component.system) ||
          system_name_matches(component.system, "rotor")) &&
         (system_name_matches(name, "actuator") ||
          system_name_matches(name, "servo") ||
          system_name_matches(name, "cyclic") ||
          system_name_matches(name, "collective")));
}

enum class AircraftFireZone {
    None,
    EngineBay,
    Wing,
    Fuselage,
    MissionBay
};

AircraftFireZone classify_aircraft_fire_zone(
    const std::string& system,
    const DamageComponent* component
) {
    std::string key = system;
    if (component) {
        key += " ";
        key += damage_component_key(*component);
        key += " ";
        key += damage_component_redundancy_group_key(*component);
    }
    if (system_name_matches(key, "engine") ||
        system_name_matches(key, "propulsion") ||
        system_name_matches(key, "afterburner") ||
        system_name_matches(key, "nozzle") ||
        system_name_matches(key, "fuel_feed") ||
        system_name_matches(key, "fuel_control") ||
        system_name_matches(key, "transmission")) {
        return AircraftFireZone::EngineBay;
    }
    if (system_name_matches(key, "wing") ||
        system_name_matches(key, "aileron") ||
        system_name_matches(key, "elevon") ||
        system_name_matches(key, "flap") ||
        system_name_matches(key, "spar")) {
        return AircraftFireZone::Wing;
    }
    if (system_name_matches(key, "radar") ||
        system_name_matches(key, "sensor") ||
        system_name_matches(key, "avionics") ||
        system_name_matches(key, "data_link") ||
        system_name_matches(key, "mission") ||
        system_name_matches(key, "command") ||
        system_name_matches(key, "navigation") ||
        system_name_matches(key, "operator") ||
        system_name_matches(key, "power") ||
        system_name_matches(key, "electrical")) {
        return AircraftFireZone::MissionBay;
    }
    if (system_name_matches(key, "fuselage") ||
        system_name_matches(key, "fuel") ||
        system_name_matches(key, "cockpit") ||
        system_name_matches(key, "crew") ||
        system_name_matches(key, "hydraulic")) {
        return AircraftFireZone::Fuselage;
    }
    return AircraftFireZone::None;
}

double component_mechanism_threshold_scale(
    const WarheadProfile& profile,
    const std::string& system
) {
    const std::string family = warhead_effect_family(profile);
    double scale = 1.0;

    if (system_is_air_control_surface(system)) {
        if (family == "continuous_rod") {
            scale = 1.35;
        } else if (family == "fragmentation" || family == "blast_fragmentation") {
            scale = 1.10;
        } else if (family == "hit_to_kill") {
            scale = 1.15;
        } else if (family == "blast") {
            scale = 0.75;
        }
    } else if (system_is_air_sensor(system) || system_name_matches(system, "avionics")) {
        if (family == "hit_to_kill") {
            scale = 1.30;
        } else if (family == "fragmentation" || family == "blast_fragmentation") {
            scale = 1.20;
        } else if (family == "continuous_rod") {
            scale = 0.90;
        } else if (family == "blast") {
            scale = 0.80;
        }
    } else if (system_is_air_propulsion(system)) {
        if (family == "hit_to_kill") {
            scale = 1.20;
        } else if (family == "blast" || family == "fragmentation" ||
                   family == "blast_fragmentation") {
            scale = 1.05;
        } else if (family == "continuous_rod") {
            scale = 0.95;
        }
    } else if (system_is_air_fuel(system)) {
        if (family == "blast") {
            scale = 1.25;
        } else if (family == "fragmentation" || family == "blast_fragmentation") {
            scale = 1.10;
        } else if (family == "continuous_rod") {
            scale = 0.85;
        } else if (family == "hit_to_kill") {
            scale = 0.95;
        }
    } else if (system_is_crew_or_cockpit(system)) {
        if (family == "hit_to_kill") {
            scale = 1.25;
        } else if (family == "fragmentation" || family == "blast_fragmentation") {
            scale = 1.20;
        } else if (family == "continuous_rod") {
            scale = 1.05;
        } else if (family == "blast") {
            scale = 0.90;
        }
    } else if (system_is_air_structure(system)) {
        if (family == "blast") {
            scale = 1.25;
        } else if (family == "continuous_rod") {
            scale = 1.20;
        } else if (family == "hit_to_kill") {
            scale = 1.15;
        }
    }

    return std::clamp(scale, 0.55, 1.45);
}

double component_authored_mechanism_threshold_scale(
    const WarheadProfile& profile,
    const DamageComponent& component
) {
    const std::string family = warhead_effect_family(profile);
    const auto exact = component.mechanism_threshold_scales.find(family);
    if (exact != component.mechanism_threshold_scales.end()) {
        return std::clamp(exact->second, 0.35, 2.40);
    }
    if ((family == "fragmentation" || family == "blast_fragmentation") &&
        component.mechanism_threshold_scales.find("fragmentation") !=
            component.mechanism_threshold_scales.end()) {
        return std::clamp(
            component.mechanism_threshold_scales.at("fragmentation"),
            0.35,
            2.40);
    }
    if (family == "blast_fragmentation" &&
        component.mechanism_threshold_scales.find("blast") !=
            component.mechanism_threshold_scales.end()) {
        return std::clamp(
            component.mechanism_threshold_scales.at("blast"),
            0.35,
            2.40);
    }
    return 1.0;
}
