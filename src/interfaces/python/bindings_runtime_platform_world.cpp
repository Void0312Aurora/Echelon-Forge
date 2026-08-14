#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "runtime/facade/runtime_facade.h"

void bind_runtime_platform_world(nb::module_ &m) {
    nb::class_<WorldTerrainAssignment> world_terrain_assignment_class(m, "WorldTerrainAssignment");
    world_terrain_assignment_class.def(nb::init<>());
#define EF_WORLD_TERRAIN_ASSIGNMENT_FIELD(type, name, default_value)                               \
    world_terrain_assignment_class.def_rw(#name, &WorldTerrainAssignment::name);
#include "runtime/contracts/detail/platform/world_terrain_assignment.inc"

    nb::class_<WorldWindAssignment> world_wind_assignment_class(m, "WorldWindAssignment");
    world_wind_assignment_class.def(nb::init<>());
#define EF_WORLD_WIND_ASSIGNMENT_FIELD(type, name, default_value)                                  \
    world_wind_assignment_class.def_rw(#name, &WorldWindAssignment::name);
#include "runtime/contracts/detail/platform/world_wind_assignment.inc"

    nb::class_<WorldSunAssignment>(m, "WorldSunAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldSunAssignment::world_index)
        .def_rw("azimuth_deg", &WorldSunAssignment::azimuth_deg)
        .def_rw("elevation_deg", &WorldSunAssignment::elevation_deg);

    nb::class_<WorldZoneDefinition> world_zone_definition_class(m, "WorldZoneDefinition");
    world_zone_definition_class.def(nb::init<>());
#define EF_WORLD_ZONE_DEFINITION_FIELD(type, name, default_value)                                  \
    world_zone_definition_class.def_rw(#name, &WorldZoneDefinition::name);
#include "runtime/contracts/detail/platform/world_zone_definition.inc"

    nb::class_<WorldSpawnRequest> world_spawn_request_class(m, "WorldSpawnRequest");
    world_spawn_request_class.def(nb::init<>());
#define EF_WORLD_SPAWN_REQUEST_FIELD(type, name, default_value)                                    \
    world_spawn_request_class.def_rw(#name, &WorldSpawnRequest::name);
#include "runtime/contracts/detail/platform/world_spawn_request.inc"
}
