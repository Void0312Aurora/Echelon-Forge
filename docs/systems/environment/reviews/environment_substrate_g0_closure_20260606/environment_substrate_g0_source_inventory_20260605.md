# Environment Substrate G0 Source Inventory

Status: `2026-06-05` source inventory for
[README.md](README.md). This is evidence for the G0 architecture plan, not a
runtime release record.

## Inventory Summary

The repository already has shared environment query and setup primitives, but
it does not yet have a maintained shared environment substrate. The current
surfaces are enough to project simple terrain type, rectangular zones, wind, and
maritime state into world setup, and they are not enough to describe large-area
terrain, airfields, coastlines, ports, buildings, roads, vegetation,
atmosphere/weather cells, wind layers, illumination state, sea-state areas,
cover, LOS, or terrain-aware movement as first-class cross-domain data.

| Surface | Evidence | Current role | Boundary |
| --- | --- | --- | --- |
| `IEnvironmentModel` | [../../../../src/core/interfaces/environment_model.h](../../../../../src/core/interfaces/environment_model.h) | Shared atmosphere, elevation, LOS, weather attenuation, sun, terrain-cell, wind, terrain type, maritime state, and rectangular zone API. | Interface has no shared environment manifest, branch registry, component catalog, road/coast/airfield graph, building model, weather branch, hydrology branch, dynamic state branch, or domain mobility contract. |
| `DefaultEnvironmentModel` | [../../../../src/models/environment/default_environment_model.cpp](../../../../../src/models/environment/default_environment_model.cpp) | 20 km by 20 km 100 m raster base, simple SoftDirt/HardPacked checkerboard, gaussian legacy elevation, `flat` terrain switch, rectangular overlay zones, simple surface properties, simple atmosphere/wind defaults, fixed sun, and maritime override storage. | Procedural checkerboard, fixed/no-op query defaults, and rectangle zones are compatibility primitives, not a scalable environment generator or branch substrate. |
| Environment model boundary docs | [../../../../src/models/environment/README.md](../../../../../src/models/environment/README.md), [../../../../src/README.md](../../../../../src/README.md) | Explicitly classify terrain/environment snapshots as query models. | They prohibit treating this area as canonical terrain ownership, movement, sensing, fires, or damage runtime. |
| Batch setup contracts | [../../../../src/runtime/contracts/world_batch_contracts.h](../../../../../src/runtime/contracts/world_batch_contracts.h) | `WorldTerrainAssignment`, `WorldWindAssignment`, and `WorldZoneDefinition` carry global terrain type, global wind, and rectangular surface zones into batch setup. | Contracts cannot preserve branch membership, rich geometry, road class, building height, tree density, wind volume, weather cell, hydrology, dynamic state, provenance, or per-consumer semantics. |
| Runtime facade setup | [../../../../src/runtime/facade/runtime_facade_types.h](../../../../../src/runtime/facade/runtime_facade_types.h), [../../../../src/core/engine/world_batch_runtime.cpp](../../../../../src/core/engine/world_batch_runtime.cpp) | Single-world setup fields carry terrain, wind, zones, and a global maritime override with `maritime_configured`, sea state, wave heading, and wave period. | Maritime setup is a global compatibility override; it is not an ocean substrate, wave field, surf model, or hydrodynamics release. |
| World setup helper | [../../../../src/core/engine/world_batch_setup_helper.h](../../../../../src/core/engine/world_batch_setup_helper.h) | Applies terrain assignments, wind, zones, reset seed, and spawns to worlds. | Wind and zones are setup fields, not a branch-aware environment manifest or derived-product lifecycle; batch setup does not carry the full runtime-layout maritime branch surface. |
| Scenario compiler layout | [../../../../python/scenario/compiler/layout_template.py](../../../../../python/scenario/compiler/layout_template.py) | Compiles `environment.terrain_type`, `environment.wind`, `environment.maritime`, and `environment.zones` into layout templates with coarse setup fields. | Compiler validates consumed shapes only; it is not environment-manifest or branch-registry aware. |
| Scenario runtime setup | [../../../../python/scenario/runtime/models.py](../../../../../python/scenario/runtime/models.py), [../../../../python/scenario/runtime/world_setup.py](../../../../../python/scenario/runtime/world_setup.py), [../../../../python/scenario/runtime/kernel_apply.py](../../../../../python/scenario/runtime/kernel_apply.py), [../../../../python/scenario/runtime/batch_apply.py](../../../../../python/scenario/runtime/batch_apply.py) | Moves compiled terrain, wind, zones, spawns, yaw/randomization, maritime fields, and setup payloads to maintained runtime/facade surfaces. | Runtime setup can consume compatibility setup fields but cannot consume a rich environment manifest yet; unknown rich branch fields can be ignored without future fail-closed validators. |
| Scenario generation metadata | [../../../../python/scenario/compiler/generation_request.py](../../../../../python/scenario/compiler/generation_request.py), [../../../../python/scenario/compiler/generation_runtime.py](../../../../../python/scenario/compiler/generation_runtime.py) | Existing request/runtime artifacts already carry deterministic seed, generator version, baseline counts, provenance/evidence refs, and generated scenario data. | The supported generation kinds do not include environment-substrate generation, and runtime artifacts track zone counts rather than rich manifest provenance. |
| Terrain query/display consumers | `src/systems/physics/ground_contact_system.h`, `src/systems/visual/visual_system.h`, `src/models/systems/default_sensor_model.cpp`, GPU visual snapshots | Existing systems can consume terrain elevation, surface/friction hints, runway/off-road cues, and elevation-only LOS checks. | These are consumers of query primitives; they are not shared terrain ownership or proof of terrain-aware movement, vegetation/building LOS, or cover. |

## Existing Mechanism Details

### C++ Environment Query

- `IEnvironmentModel::TerrainCell` exposes `SurfaceType`, elevation,
  friction, roughness, vegetation density, and runway heading.
- `IEnvironmentModel` also exposes atmospheric data, weather attenuation, sun
  direction, wind setup, and maritime state.
- `DefaultEnvironmentModel` computes simple altitude-based atmosphere, returns
  no weather attenuation, exposes a fixed sun vector, and stores global wind and
  maritime override values.
- `IEnvironmentModel::add_zone()` accepts a rectangle-like zone with name,
  center, width, length, heading, and surface.
- `DefaultEnvironmentModel` assigns default surface parameters from a small
  enum set: Concrete, Asphalt, HardPacked, SoftDirt, Water, and Obstacle.
- `check_line_of_sight()` samples elevation and maritime special cases. It does
  not account for buildings, vegetation, smoke, tactical concealment, or cover.

### Scenario And Runtime Projection

- Scenario JSON currently uses `environment.terrain_type` and
  `environment.zones`, with additional loose setup fields for `environment.wind`
  and `environment.maritime`.
- The compiler maps zone `surface` strings into integer surface codes.
- The runtime can rotate projected zones with world yaw and apply them through
  `WorldZoneDefinition`; wind maps to global wind setup; maritime maps only to
  global runtime-layout override fields.
- Tests already exercise terrain-type defaults and compatibility behavior, but
  they do not validate rich terrain-substrate semantics, branch registry
  semantics, weather cells, wind volumes, maritime areas, hydrology, or dynamic
  environment state.
- Shape validation currently verifies only object/list structure consumed by the
  compiler. It does not validate terrain semantics or reject unsupported rich
  terrain fields.
- A concrete loose-schema risk exists: current compiler/runtime paths read a
  zone's `surface` field, while at least one generation-runtime fixture uses a
  `surface_type` string. Without a projection validator, this kind of mismatch
  can silently fall back to default `SoftDirt`-style setup instead of failing
  closed.

## G0 Design Consequences

- Rich environment state must live above the current zone surface as a manifest.
- `WorldZoneDefinition` should remain a lossy compatibility projection target,
  not the canonical schema.
- Terrain is only the first detailed branch. The substrate root must reserve
  branch ownership for atmosphere/weather, wind, illumination, maritime/ocean,
  hydrology, and dynamic environment state instead of making terrain absorb
  those concerns.
- Inventory claims must distinguish "API hook exists", "setup field exists", and
  "branch/runtime behavior exists." Current wind and maritime setup can affect
  existing consumers, but they are still compatibility projections rather than
  canonical branch ownership.
- The terrain branch inside the environment substrate should be shared by air,
  naval, ground, and future domains. Ground is the first pressure lane, not the
  owner of the schema.
- Feature labels such as road, forest, building, trench, or village block should
  be catalog entries composed from generic components.
- Validators must reject unsupported, misspelled, or lossy projection semantics
  explicitly; current loose `environment.zones` behavior is too permissive for
  rich terrain-substrate data.
- A future terrain generator should emit deterministic manifests plus
  provenance, then validators and projection should decide what can enter the
  existing runtime.
- Weather simulation, hydrodynamics, hydrology effects, dynamic environment
  mutation, movement, LOS, cover, sensing, fires, damage, and combat must
  continue to wait for separate derived-product and runtime release gates.
