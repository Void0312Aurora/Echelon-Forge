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

    nb::class_<WorldGeodeticAnchorAssignment>(m, "WorldGeodeticAnchorAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldGeodeticAnchorAssignment::world_index)
        .def_rw("latitude_deg", &WorldGeodeticAnchorAssignment::latitude_deg)
        .def_rw("longitude_deg", &WorldGeodeticAnchorAssignment::longitude_deg)
        .def_rw("height_m", &WorldGeodeticAnchorAssignment::height_m);

    nb::class_<WorldMaritimeAssignment>(m, "WorldMaritimeAssignment")
        .def(nb::init<>())
        .def_rw("world_index", &WorldMaritimeAssignment::world_index)
        .def_rw("configured", &WorldMaritimeAssignment::configured)
        .def_rw("sea_state", &WorldMaritimeAssignment::sea_state)
        .def_rw("wave_heading_deg", &WorldMaritimeAssignment::wave_heading_deg)
        .def_rw("wave_period_s", &WorldMaritimeAssignment::wave_period_s);

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
