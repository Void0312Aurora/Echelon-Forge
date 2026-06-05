# Environment Substrate G0 Terrain System Architecture

Status: `2026-06-05` shared terrain-system architecture design for
[README.md](README.md). This document refines the terrain portion of the G0
environment-substrate plan. It does not implement a terrain generator, movement
model, LOS model, cover model, or domain runtime.

## Purpose

The first serious ground scenario is the immediate driver because it needs
terrain, buildings, roads, vegetation, and tactical areas before it can
honestly move toward mechanized movement or village contact. That does not make
the terrain system ground-exclusive. Airfields, runways, coastal strips,
islands, littoral clutter, ports, rivers, and future domains should migrate onto
the same terrain branch inside the environment substrate instead of each domain
growing a private map schema.

The current runtime only supports a small terrain query/setup surface. This
document defines a structural terrain branch that can grow from the current
primitives without hardcoding one village, one service branch, or one schema.
It is subordinate to the wider environment-substrate manifest, which also needs
branches for atmosphere/weather, wind, illumination, maritime/ocean, hydrology,
and dynamic environment state.

The design goal is a terrain substrate that can represent tens or hundreds of
square kilometers through deterministic manifests, tiled/layered data, catalogs,
validators, derived products, and lossy projections into the current runtime.

This design is informed by two read-only diagnostics packets recorded in
[environment_substrate_g0_subagent_dispatch_20260605.md](environment_substrate_g0_subagent_dispatch_20260605.md):
one over the C++ environment/query/setup surfaces, and one over the Python
scenario compiler/runtime setup surfaces.

## Current Terrain Foundation

| Current surface | What it supports today | What it cannot support yet |
| --- | --- | --- |
| `IEnvironmentModel` | elevation lookup, LOS stub, weather attenuation stub, terrain-cell lookup, rectangular zones, wind/maritime state | no terrain manifest, no tiled storage contract, no road graph, no building geometry, no authoritative ground movement semantics |
| `DefaultEnvironmentModel` | `flat`/legacy elevation mode, 20 km by 20 km 100 m raster base, SoftDirt/HardPacked checkerboard, rectangular overlays with surface properties | not scalable world generation, no hydrology, no soil/geology stack, no feature catalog, no terrain provenance |
| `WorldTerrainAssignment` | per-world global terrain type such as `flat` or `legacy` | no detailed terrain layers, no regional heterogeneity except zones |
| `WorldZoneDefinition` | rectangle-like surface overrides with name, center, width, length, heading, surface code | no polygon/line/multilayer geometry, no road width/load/speed semantics, no tree density/species, no building height/material/interior |
| Scenario compiler/runtime | compiles `environment.terrain_type` and `environment.zones`, rotates projected zones with world yaw, applies setup through maintained batch/facade paths | not manifest-aware, not generator-aware, no rich terrain provenance or derived-product lifecycle |
| Existing tests | verify terrain defaults, explicit legacy compatibility, zone setup payloads, batch setup behavior | do not validate terrain realism, generator determinism, or ground mobility/LOS behavior |

Design consequence: the new terrain system must sit above the current query and
setup primitives. The current primitives become compatibility targets, not the
canonical terrain model.

Two immediate risk points shape the architecture:

- Extending `WorldZoneDefinition` would turn a compatibility projection DTO into
  a false canonical terrain schema.
- Continuing to rely on loose `environment.zones` dictionaries would allow
  unsupported or misspelled terrain semantics to degrade into default surface
  setup instead of failing closed.

## Shared Domain Boundary

The terrain system is shared environment infrastructure:

- Air can consume it for runways, taxiways, airfield surfaces, approach terrain,
  obstacles, and weather/terrain projection boundaries.
- Naval can consume it for coastlines, islands, ports, littoral corridors,
  rivers, wetlands, and shore-side infrastructure.
- Ground can consume it for roads, buildings, vegetation, soil, tactical areas,
  and later terrain-aware movement/LOS products.
- Future domains should add components, catalogs, projection profiles, and
  derived products without taking over the schema root.

The ground task remains the incubation surface because the first missing
requirements came from land scenarios. Implementation ownership should still be
named as shared `environment_substrate`.

## Relation To Other Environment Branches

Terrain must not become the container for every environmental concern. The G0
root manifest should expose a branch registry, and this terrain design occupies
only the `terrain` branch inside it.

| Branch | Relationship to terrain | G0 boundary |
| --- | --- | --- |
| `atmosphere_weather` | Weather can affect visibility, attenuation, mud, snow, or flight context, but it is not a terrain layer. | Manifest-compatible branch only; no weather simulation release. |
| `wind_field` | Wind can share coordinate frames and time windows with terrain, fires, flight, and smoke later. | Project only to accepted global wind setup fields until richer profiles exist. |
| `illumination` | Sun/time/light context may later affect visibility and shadows over terrain. | Metadata only until visual/sensing gates. |
| `maritime_ocean` | Sea state and waves meet terrain at shorelines, ports, islands, and littoral strips. | Shared naval/littoral branch; no hydrodynamics release. |
| `hydrology` | Inland water and wetness can belong to terrain and connect to maritime/coastal state. | Runtime mobility/LOS/effects remain held. |
| `dynamic_environment` | Smoke, fire, flooding, destruction, and contamination may modify terrain-derived products later. | Reserve IDs/hooks only in current G0 static substages. |

Cross-branch objects should use `branch_membership[]` and components, not schema
inheritance. For example, a flooded coastal road can combine `terrain`,
`hydrology`, `maritime_ocean`, and later `dynamic_environment` membership while
remaining one validated environment object.

## Terrain System Boundary

The terrain system is a static shared environment-substrate package with five
responsibilities:

- store versioned terrain manifests;
- validate layered terrain objects and components;
- run deterministic generator plugins;
- build derived terrain products when separate gates allow them;
- project supported subsets into maintained runtime setup surfaces.

It explicitly does not:

- update entity positions;
- decide passability at runtime;
- block line of sight at runtime;
- grant cover, concealment, suppression, damage, or combat effects;
- replace `IEnvironmentModel` or `WorldZoneDefinition` in current G0 substages;
- become a single-domain map schema.

## Proposed Package Shape

G1 should begin in Python because the first slice is static contracts,
validation, fixture data, and projection tests. C++ terrain ownership for any
domain can wait until a later runtime release gate.

```text
python/scenario/environment_substrate/
  __init__.py
  manifest.py
  components.py
  validation.py
  projection.py
  terrain/
    __init__.py
    schema.py
    catalog.py
    layers.py
    generators.py
    derived_products.py
    projection_profiles.py
```

Focused tests should live under:

```text
tests/scenario/test_environment_substrate_manifest.py
tests/scenario/test_environment_substrate_projection.py
tests/scenario/test_terrain_system_schema.py
tests/scenario/test_terrain_system_projection.py
```

No G1 file should edit C++ runtime code.

## Core Data Model

```text
TerrainManifest
  manifest_id
  schema_version
  coordinate_frame
  extent
  tile_scheme
  generation
  layer_stack[]
  terrain_objects[]
  terrain_relationships[]
  catalogs[]
  projection_profiles[]
  validation_evidence[]
```

```text
TerrainObject
  object_id
  object_kind
  geometry
  tile_refs[]
  layer_membership[]
  components[]
  properties{}
  provenance
```

`object_kind` is descriptive. Runtime meaning comes from components and derived
products, not from hardcoded labels.

## Layer Stack

The terrain system should support layered composition. Layers are ordered and
composable, so geology/soil, hydrology, vegetation, buildings, roads, and
tactical overlays can be added without changing the schema root.

| Layer | Role | Required attributes before runtime use |
| --- | --- | --- |
| `base_elevation` | height field, contour source, terrain relief | elevation source, resolution, vertical datum, uncertainty |
| `terrain_morphology` | slope, embankment, ditch, berm, cut/fill | slope range, height/depth, geometry, confidence |
| `soil_surface` | soil, compaction, mud, snow, roughness | material class, wetness, roughness, seasonal state |
| `hydrology` | streams, ponds, drainage, flooded areas | water depth, bank geometry, flow/current, fordability metadata |
| `vegetation` | forest, tree line, orchard, shrub, grass | species group, canopy height, trunk spacing, density, undergrowth |
| `built_structure` | buildings, walls, bridges, bunkers | footprint, height, floors, material, entrance/window hints |
| `infrastructure` | roads, tracks, alleys, bridges, paths | network nodes, width, surface, load class, speed metadata, connectivity |
| `tactical_overlay` | contact line, objective, village block, assembly area | semantic type, side/control, confidence, time window |
| `hazard_overlay` | minefield, obstacle belt, contaminated area | hazard type, marking, activation, confidence |
| `dynamic_overlay` | future mutable state such as destruction, smoke, fire, flood | reserved IDs only in G0-J |

This structure answers the "geology plus vegetation" problem directly: base and
surface layers can exist independently of vegetation, and validators check their
compatibility without forcing a single feature schema.

## Catalog And Components

Catalog entries are reusable recipes. A road, forest, or building is a catalog
composition, not a schema root.

| Catalog example | Geometry | Required components | Projection rule |
| --- | --- | --- | --- |
| `rural_gravel_road` | line plus corridor width or polygon | `surface_material`, `network`, `mobility_modifier` | may project to Asphalt/HardPacked rectangle only if explicitly rectangle-simplified |
| `field_track` | line corridor | `surface_material`, `network`, optional `seasonal_state` | may project only as low-fidelity surface zone; no movement speed claim |
| `shelterbelt_tree_line` | polygon strip | `vegetation`, optional `occlusion`, optional `cover_concealment` | no LOS/cover projection in G0-J |
| `village_house_light` | footprint polygon plus height | `structure`, `surface_material`, optional `occlusion`, optional `damageable` | may remain manifest-only until building projection is accepted |
| `farm_field` | polygon | `soil_surface`, optional `vegetation`, optional `hydrology` | may project to SoftDirt if a lossy profile says dropped attributes are acceptable |
| `runway_paved_surface` | polygon or rectangle | `surface_material`, `terrain_morphology`, optional `tactical_semantic` | may project to Concrete without creating an air-only schema |
| `littoral_shoreline_strip` | polygon or polyline corridor | `hydrology`, `terrain_morphology`, `surface_material`, optional `tactical_semantic` | may inform naval/littoral context while runtime effects remain held |
| `port_hardstand` | polygon | `surface_material`, `infrastructure`, optional `ownership_control` | may be shared by naval logistics and ground tasking without separate schemas |
| `assembly_area` | polygon | `tactical_semantic`, optional `ownership_control` | can be referenced by tasking/status without physics claims |

Road dimensions, trafficability, tree density, species group, building height,
wall material, entrances, and surface condition are component attributes. They
must not be flattened into a single road/forest/building schema.

## Generator Architecture

A future terrain generator should be plugin-based and deterministic.

```text
TerrainGenerationRequest
  request_id
  generator_id
  generator_version
  deterministic_seed
  extent
  tile_scheme
  realism_target
  catalog_refs[]
  constraints[]
  evidence_refs[]
```

Generator stages should be composable:

1. Frame and tile setup: extent, coordinate frame, tile grid, deterministic seed
   partitioning.
2. Base terrain: elevation, slope, roughness, major landforms.
3. Hydrology: drainage, streams, wet areas, crossings.
4. Surface and soil: material class, compaction, seasonal mud/snow/wetness.
5. Infrastructure: road/path graph first, then corridor geometry and bridges.
6. Built environment: settlement blocks, parcels, building footprints, walls.
7. Vegetation: biomes, field edges, tree lines, forests, density/species mix.
8. Tactical overlays: bases, contact line, objective areas, assembly areas.
9. Validators and projection profiles.

Algorithmically, the system should prefer a hybrid approach:

- deterministic procedural generation for broad background layers;
- graph-based generation for roads, paths, and infrastructure connectivity;
- constraint solving for settlement layout, bridge/crossing placement, and
  tactical relationships;
- catalog-driven feature instancing for vegetation/buildings/obstacles;
- later optional import adapters for GIS or hand-authored authoritative data.

This avoids hand-writing huge maps while keeping every generated object
inspectable and reproducible.

## Tiling And Scale

Large land areas should be tile-aware from the first schema:

- tile IDs must be deterministic and stable;
- objects can span tiles but must declare owning tile and covered tiles;
- validators should enforce extent bounds and cross-tile references;
- derived products can be built per tile plus border halos;
- projection can emit only the subset needed for the current scenario/world.

The G0-J contract can store small fixtures, but the schema should already reserve
tile fields so later generator work does not require a breaking rewrite.

## Projection Boundary

Current runtime projection supports only:

- `WorldTerrainAssignment.terrain_type`;
- `WorldZoneDefinition` rectangle-like surface zones.

Therefore projection profiles must be explicit:

```text
TerrainProjectionProfile
  profile_id
  target_surface
  allowed_object_kinds[]
  required_components[]
  geometry_simplification
  surface_code_mapping
  dropped_attribute_policy
  fail_closed_reasons[]
```

Projection rules:

- unsupported geometry fails closed unless the profile explicitly allows
  omission;
- unsupported field names or ambiguous surface mappings fail closed;
- dropped attributes must be recorded in projection evidence;
- no projection may claim movement speed, LOS blockage, cover, or damage;
- rich manifest provenance remains authoritative after lossy projection.

## Derived Product Gates

Derived products are the bridge from static terrain data to future runtime
behavior. They must have separate contracts and release gates.

| Product | Requires | Future use | Current status |
| --- | --- | --- | --- |
| `terrain_surface_map` | base elevation, soil/surface layers | query/debug and projection sanity | held |
| `road_graph` | infrastructure/network components | route planning and convoy movement | held |
| `movement_cost_grid` | soil, slope, hydrology, vegetation, mobility components | terrain-aware movement | held |
| `passability_mask` | obstacles, hydrology, buildings, actor class rules | stuck/off-route checks | held |
| `los_occlusion_index` | elevation, vegetation, structures, occlusion components | contact/report and sensing | held |
| `cover_concealment_index` | vegetation, structure, terrain morphology | firefight/cover behavior | held |
| `tactical_area_graph` | tactical overlay, ownership, infrastructure | tasking/report semantics | held |

## Implementation Roadmap

| Step | Goal | Write set | Release boundary |
| --- | --- | --- | --- |
| `T0` | Terrain system architecture and diagnostics evidence. | task package docs only | accepted G0 documentation |
| `T1 / G0-J-A-B` | Static shared environment manifest schema and validators. | `python/scenario/environment_substrate/**`, focused `tests/scenario/**` | accepted G0-J static contract; no runtime behavior |
| `T2 / G0-J-C` | Tiny deterministic fixture and projection tests. | fixture/test files plus projection contract | accepted G0-J contract tests; no generator release |
| `T3 / G0-K` | Generator plugin skeleton and request contract. | Python generator package and tests | no runtime projection unless separately accepted |
| `T4 / G0-L` | Projection integration into scenario compiler/runtime setup. | scenario compiler/runtime setup plus tests | only lossy zone projection |
| `T5 / G0-M` | First derived product contract. | derived-product package and tests | no movement/LOS effect without runtime gate |
| `T6 / G0-N` | C++ shared terrain query adapter. | new C++ package, bindings, tests | separate runtime release vote |

The first implementation slice is now the accepted G0-J shared static contract:
schema, registries, validators, deterministic fixture, and projection contract
tests. It proves that rich features can exist as static manifest data and that
unsupported runtime claims fail closed.

## Acceptance Boundary

This terrain system design can support G0 acceptance only when:

- the current terrain foundation is described as compatibility primitives;
- the terrain schema is layered, tiled, catalog-driven, and component-based;
- the terrain system is explicitly shared across air, naval, ground, and future
  domains;
- road/building/vegetation details are attributes and components, not schema
  roots;
- generator, projection, derived products, and runtime query ownership are
  separated into later gates;
- movement, LOS, cover, fires, damage, and combat remain held.
