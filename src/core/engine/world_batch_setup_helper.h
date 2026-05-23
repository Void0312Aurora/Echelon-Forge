#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

#include "core/engine/simulation_kernel.h"
#include "runtime/contracts/world_batch_contracts.h"

namespace world_batch_setup {

inline void maybe_apply_time_step(
    SimulationKernel& world,
    std::size_t world_index,
    const std::vector<double>& time_steps
) {
    if (time_steps.empty()) {
        return;
    }

    const double dt = time_steps.size() == 1 ? time_steps[0] : time_steps[world_index];
    if (std::isfinite(dt) && dt > 0.0) {
        world.set_time_step(dt);
    }
}

inline void apply_terrain_assignments(
    SimulationKernel& world,
    const std::vector<WorldTerrainAssignment>& assignments,
    const std::vector<std::size_t>& grouped_indices
) {
    for (const std::size_t item_index : grouped_indices) {
        const std::string& terrain_type = assignments[item_index].terrain_type.empty()
            ? WorldTerrainAssignment{}.terrain_type
            : assignments[item_index].terrain_type;
        world.set_terrain_type(terrain_type);
    }
}

inline void apply_setup_terrain_assignments(
    SimulationKernel& world,
    const std::vector<WorldTerrainAssignment>& assignments,
    const std::vector<std::size_t>& grouped_indices
) {
    if (grouped_indices.empty()) {
        world.set_terrain_type(WorldTerrainAssignment{}.terrain_type);
        return;
    }
    apply_terrain_assignments(world, assignments, grouped_indices);
}

inline void apply_wind_assignments(
    SimulationKernel& world,
    const std::vector<WorldWindAssignment>& assignments,
    const std::vector<std::size_t>& grouped_indices
) {
    for (const std::size_t item_index : grouped_indices) {
        const auto& item = assignments[item_index];
        world.set_wind(item.speed_mps, item.dir_from_deg, item.shear_mps_per_km);
    }
}

inline void append_zones(
    SimulationKernel& world,
    const std::vector<WorldZoneDefinition>& zones,
    const std::vector<std::size_t>& grouped_indices
) {
    for (const std::size_t item_index : grouped_indices) {
        const auto& zone = zones[item_index];
        world.add_zone(zone.name, zone.x, zone.y, zone.width, zone.length, zone.heading, zone.surface_type);
    }
}

inline void replace_zones(
    SimulationKernel& world,
    const std::vector<WorldZoneDefinition>& zones,
    const std::vector<std::size_t>& grouped_indices
) {
    world.clear_zones();
    append_zones(world, zones, grouped_indices);
}

inline std::uint32_t resolve_reset_seed(
    std::size_t world_index,
    std::size_t world_count,
    const std::vector<std::uint32_t>& seeds
) {
    std::uint32_t seed = static_cast<std::uint32_t>(42 + world_index);
    if (seeds.size() == world_count) {
        seed = seeds[world_index];
    } else if (seeds.size() == 1) {
        seed = static_cast<std::uint32_t>(seeds[0] + static_cast<std::uint32_t>(world_index));
    }
    return seed;
}

template <typename SpawnFn>
inline void apply_world_setup(
    SimulationKernel& world,
    std::size_t world_index,
    std::size_t world_count,
    const std::vector<std::uint32_t>& seeds,
    const std::vector<WorldTerrainAssignment>& terrain_assignments,
    const std::vector<std::size_t>& terrain_grouped_indices,
    const std::vector<WorldWindAssignment>& wind_assignments,
    const std::vector<std::size_t>& wind_grouped_indices,
    const std::vector<WorldZoneDefinition>& zones,
    const std::vector<std::size_t>& zone_grouped_indices,
    const std::vector<WorldSpawnRequest>& requests,
    const std::vector<std::size_t>& spawn_grouped_indices,
    const std::vector<double>& time_steps,
    std::vector<std::uint64_t>* out_entity_ids,
    SpawnFn&& spawn_fn
) {
    maybe_apply_time_step(world, world_index, time_steps);
    apply_setup_terrain_assignments(world, terrain_assignments, terrain_grouped_indices);
    apply_wind_assignments(world, wind_assignments, wind_grouped_indices);
    replace_zones(world, zones, zone_grouped_indices);
    world.reset(resolve_reset_seed(world_index, world_count, seeds));

    if (out_entity_ids == nullptr) {
        return;
    }
    for (const std::size_t item_index : spawn_grouped_indices) {
        (*out_entity_ids)[item_index] = spawn_fn(world, requests[item_index]);
    }
}

}  // namespace world_batch_setup
