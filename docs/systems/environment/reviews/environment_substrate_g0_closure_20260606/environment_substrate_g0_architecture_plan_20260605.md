# Environment Substrate G0 Architecture Implementation Plan

Status: `2026-06-05` G0 architecture implementation plan for
[README.md](README.md). This plan defines the shape of the future environment
substrate package; it does not implement the package.

## Boundary Decision

The first environment substrate must be component-based and shared across
domains. Ground is the first pressure lane because land scenarios need terrain,
buildings, vegetation, infrastructure, and tactical overlays earlier than the
current air/naval MVPs, but the schema root must be a shared environment
manifest and generic environment objects. It must not be roads, forests,
buildings, villages, weather cells, wind fields, sea-state areas, or any other
feature label, and it must not be owned by the ground domain alone.

Terrain is a first detailed branch, not the whole substrate. Existing
`IEnvironmentModel` surfaces already include atmosphere, weather attenuation,
sun direction, wind, and maritime state, so G0 must preserve a branch registry
that can merge terrain with other environment branches instead of creating a
terrain-only root.

The first implementation after this G0 package is now the accepted Python-side
manifest contract and validator slice under a shared environment-substrate
namespace. C++ runtime terrain ownership, movement, LOS, cover, fires, effects,
and damage remain out of scope until separate release votes.

## Target Pipeline

```text
Scenario Intent
  -> Environment Generator Plugins
  -> Component-Based Environment Manifest
  -> Validators
  -> Derived Product Builders
  -> Runtime Projection
  -> Query / Simulation Consumers
```

The manifest is authoritative for rich static environment state. Runtime
projection is a controlled, lossy operation from this manifest into currently
maintained setup surfaces such as `WorldTerrainAssignment` and
`WorldZoneDefinition`.

## Manifest Shape

The manifest should be versioned, deterministic, and explicit about coordinate
frames and provenance.

```text
EnvironmentManifest
  manifest_id
  schema_version
  coordinate_frame
  region_extent
  branch_registry[]
  component_registry[]
  layer_registry[]
  generation
    generator_id
    generator_version
    deterministic_seed
    source_inputs[]
  catalogs[]
  layer_stack[]
  objects[]
  relationships[]
  projection_profiles[]
  validation_evidence[]
```

Each object stays generic:

```text
EnvironmentObject
  object_id
  catalog_ref
  branch_membership[]
  geometry
  layer_membership[]
  components[]
  properties{}
  provenance
```

`catalog_ref` is descriptive. Simulation meaning must come from components and
validated projections, not from the label itself. `properties{}` is
metadata-only: validators must reject any simulation behavior that appears only
as an untyped property.

## Registry Locations

G1 should make registries explicit and versioned rather than implicit in loose
objects:

- `branch_registry[]`: branch descriptors, branch ownership, allowed components,
  validators, legal dependencies/conflicts, and projection targets.
- `component_registry[]`: typed component descriptors, units, required
  attributes, consumer tags, and minimum realism grades.
- `layer_registry[]`: layer ordering, compatibility rules, and branch/layer
  relationship rules.
- `catalogs[]`: reusable feature recipes that reference branches, layers,
  components, and projection profiles without becoming schema roots.
- `projection_profiles[]`: named lossy mappings into current setup targets,
  including required evidence and dropped-attribute policy.

## Branch Registry

The manifest root owns environment branches. A branch is a typed namespace for
environment state, components, validators, projection profiles, and future
derived products. Branches can overlap over the same region or object.

| Branch family | Role | Current source hint | G0 rule |
| --- | --- | --- | --- |
| `terrain` | Surface, elevation, built features, vegetation, roads, and tactical areas. | `terrain_type`, `WorldZoneDefinition`, terrain-cell queries. | First detailed architecture branch; no runtime terrain behavior. |
| `atmosphere_weather` | Air density, pressure, temperature, humidity, weather attenuation, clouds, precipitation, visibility. | `get_atmosphere_at()`, `get_weather_attenuation()`. | Keep as manifest-compatible branch; no weather simulation release. |
| `wind_field` | Wind vectors, direction, speed, shear, gust models, altitude bands. | `set_wind()`, atmosphere wind velocity. | Can project only to current global wind setup until richer profiles exist. |
| `illumination` | Sun direction, time-of-day, light, shadow/visibility context. | `get_sun_direction()`. | Metadata only until sensing/visual gates. |
| `maritime_ocean` | Sea state, waves, wave heading/period, littoral water state. | `set_maritime_state()`, `get_maritime_state()`. | Shared with naval and littoral terrain; no hydrodynamics/effects release. |
| `hydrology` | Inland water, wetness, drainage, flooded areas, crossings. | Terrain branch needs it; current runtime lacks rich hydrology. | May bridge terrain and maritime; runtime effects held. |
| `dynamic_environment` | Mutable smoke, fire, flooding, destruction, contamination, time windows. | No maintained static manifest yet. | Reserve IDs and component hooks only in current G0 static substages. |

Each branch descriptor should include at least:

- branch ID and schema version;
- shared owner, static/dynamic status, supported geometry dimensions, and
  temporal-support model;
- allowed component families and required validators;
- accepted projection targets and explicit non-targets;
- legal branch dependencies/conflicts;
- held capability claims that this branch cannot unlock by itself.

Branch membership prevents the design from overloading terrain layers with
weather or ocean semantics. For example, a coastal storm may combine
`terrain`, `atmosphere_weather`, `wind_field`, and `maritime_ocean` objects; a
muddy village road may combine `terrain`, `hydrology`, and `dynamic_environment`
objects later, after separate gates.

`branch_membership[]` entries should carry roles, not only branch IDs:

- `primary`: branch that owns the object's main identity and validation path;
- `supporting`: branch that contributes components without taking over identity;
- `context`: branch that gives environmental context only;
- `projectable`: branch membership that may enter a named compatibility
  projection profile;
- `metadata_only`: branch data retained in the manifest but not projected;
- `reserved_dynamic`: stable future mutable-state hook with no accepted G0
  runtime behavior.

Branch membership may reference branch-scoped component IDs and projection
profile IDs. Cross-branch objects are valid only when branch descriptors allow
the combination.

## Layer Semantics

The default layer stack is open-ended and ordered by dependency, not by a fixed
closed enum.

Branches and layers are separate concepts. A branch is an ownership,
validation, and projection namespace. A layer is an ordering/composition slot
inside or across branches. Reusing names such as `hydrology` at both levels is
allowed only when docs and validators preserve that distinction.

| Layer family | Purpose | Examples | G0 rule |
| --- | --- | --- | --- |
| `physical_base` | Long-lived substrate below the surface. | geology, soil class, compaction, rock | Optional metadata in G1; no movement effect yet. |
| `terrain_surface` | Surface geometry and material. | slope class, surface roughness, mud, snow | Can project to current surface codes only when explicit. |
| `hydrology` | Water and wetness state. | stream, drainage ditch, flooded field, water table | Held for runtime effects. |
| `atmosphere_weather` | Local atmospheric or weather cells over the region. | fog area, rain band, temperature layer, cloud ceiling | Metadata/projection only; no weather dynamics. |
| `wind_field` | Wind state across altitude or area. | surface wind, shear layer, gust cell | Can only project to accepted wind setup fields. |
| `illumination` | Light and sun/time state affecting visibility later. | sun vector, time window, shadow context | Held for sensing/visual effects. |
| `maritime_ocean` | Sea/wave state and littoral water context. | sea-state area, wave corridor, surf zone | Naval/littoral context only until release gates. |
| `vegetation` | Plant cover and biological clutter. | forest patch, tree line, orchard, shrub density | Must include density/species attributes before any cover or LOS claim. |
| `built_structure` | Human-made structures. | house, wall, barn, bridge, bunker | Must include footprint and vertical attributes before any occlusion claim. |
| `infrastructure_network` | Traversable or connective infrastructure. | road, track, alley, bridge, culvert | Must include width/load/surface/connectivity metadata before movement claims. |
| `tactical_semantic` | Analyst or mission meaning. | village block, contact line, assembly area, objective area | Semantic labels do not imply physics by themselves. |
| `hazard_control_overlay` | Hazards, control, ownership, and denial. | minefield, obstacle belt, controlled sector | Held for effects until separate gates. |
| `dynamic_state_overlay` | Mutable runtime state. | destroyed bridge, fire, smoke, flooded road | G0-J static manifests can reserve IDs only. |

Objects may belong to multiple layers. Validators enforce compatibility instead
of forcing one object into exactly one layer.

## Component Registry

Components are typed records with a stable family, schema version, attributes,
consumer tags, and minimum realism grade. The registry is extensible by adding a
new component descriptor and validator, without changing the object root.

| Component family | Required meaning | Example attributes | Consumers blocked until |
| --- | --- | --- | --- |
| `surface_material` | What the object surface is made of. | material class, roughness, wetness, snow depth | Projection can map to current surface codes; movement needs future mobility gates. |
| `terrain_morphology` | Shape or slope characteristics. | elevation source, slope range, embankment height, cut/fill | Terrain-aware movement and LOS gates. |
| `mobility_modifier` | How movement might be affected. | allowed actor classes, speed multiplier, load class, seasonal closure, obstacle severity | Movement release vote. |
| `vegetation` | Plant cover details. | species group, canopy height, trunk spacing, density, undergrowth, seasonal leaf state | Cover/LOS/sensing gates. |
| `structure` | Built structure properties. | footprint, height, floors, wall material, entrances, windows, interior passability | Building LOS, cover, and damage gates. |
| `occlusion` | Potential blockage of sight or sensing. | height, opacity by sensor family, permeability, confidence | LOS/sensing gate. |
| `cover_concealment` | Tactical protection or concealment semantics. | cover arc, protection class, concealment factor, stance dependency | Cover/firefight gate. |
| `network` | Graph connectivity. | from/to nodes, width, lane count, shoulder, turn radius, grade, bridge/tunnel refs | Route graph and movement gates. |
| `hydrology` | Water, wetness, and drainage semantics. | depth, current, bank slope, fordability, flooding recurrence | Mobility and sensing gates. |
| `atmospheric_profile` | Local atmosphere state. | temperature, pressure, density, humidity, altitude band, confidence | Flight/weather consumers; no dynamics release. |
| `weather_effect` | Weather phenomena and attenuation hints. | precipitation, fog, cloud ceiling, visibility, attenuation by sensor family | Sensing/weather gate. |
| `wind_field` | Wind state. | speed, direction, shear, gust, altitude band, time window | Current global wind projection only until richer gates. |
| `illumination` | Light and sun-state hints. | sun vector, time of day, shadow confidence, light level | Visual/sensing gate. |
| `maritime_state` | Sea and wave state. | sea state, wave heading, wave period, surf severity | Naval/littoral gates. |
| `hazard` | Dangerous or denial area. | hazard kind, activation state, confidence, marking, neutralization state | Effects/damage gate. |
| `tactical_semantic` | Human operational meaning. | objective ID, control side, phase line, contact line, named area | Tasking/status may reference it; no physics claim. |
| `ownership_control` | Control and access metadata. | side, confidence, time window, access rule | Tasking and information-state gates. |
| `damageable` | Future mutable degradation. | health class, repairability, failure modes, kill criteria | Damage/runtime state gate. |

Road width, road class, tree species, tree density, building height, entrance
layout, and similar details are component attributes. They are not special
schema roots.

## Catalog Composition Examples

| Catalog entry | Geometry | Components | Notes |
| --- | --- | --- | --- |
| `rural_paved_road` | LineString or polygon corridor | `surface_material`, `network`, `mobility_modifier`, optional `damageable` | Requires width, lane count, surface class, load class, and speed metadata before movement use. |
| `shelterbelt_tree_line` | Polygon strip | `vegetation`, optional `occlusion`, optional `cover_concealment` | Requires species/density/canopy attributes before LOS or cover use. |
| `village_house_light` | Footprint polygon plus height/extrusion | `structure`, `surface_material`, optional `occlusion`, optional `cover_concealment`, optional `damageable` | Static tasking can reference it; building combat remains held. |
| `field_boundary_ditch` | LineString or narrow polygon | `terrain_morphology`, `hydrology`, optional `mobility_modifier` | Mobility impact remains held until route/movement gates. |
| `airfield_surface` | Polygon or rectangular zone | `surface_material`, optional `terrain_morphology`, optional `tactical_semantic` | Can support airfield/runway setup projection without becoming an air-only schema. |
| `coastal_littoral_strip` | Polygon or polyline corridor | `terrain_morphology`, `hydrology`, optional `surface_material`, optional `tactical_semantic` | Can support naval/littoral context without becoming a naval-only schema. |
| `fog_bank` | Polygon or volume | `weather_effect`, optional `atmospheric_profile`, optional `time_window` | Can remain manifest-only until sensing/weather projection is accepted. |
| `wind_shear_layer` | Volume or altitude band | `wind_field`, optional `atmospheric_profile` | May project to current global wind only if explicitly simplified. |
| `sea_state_patch` | Polygon or area | `maritime_state`, optional `weather_effect`, optional `time_window` | Can inform naval/littoral setup without runtime hydrodynamics claims. |
| `assembly_area` | Polygon | `tactical_semantic`, optional `ownership_control` | Can support early ground task references without claiming terrain physics. |

Catalog entries should declare:

- catalog ID and schema version;
- allowed branches, branch roles, and layers;
- accepted geometry kinds and dimensions;
- required and optional components;
- minimum realism grade and consumer tags;
- accepted projection profile refs;
- dropped-attribute policy for lossy projection;
- forbidden capability claims.

## Validator Plan

G1 validators should fail closed and return machine-readable rejection reasons.

- Structural validator: manifest ID, schema version, coordinate frame, extents,
  object IDs, component family IDs, and required fields.
- Geometry validator: accepted geometry types, finite coordinates, extents, area
  and length sanity bounds, and ring orientation where relevant.
- Reference validator: catalog refs, layer refs, object relationships, projection
  profile refs, and provenance refs.
- Component validator: required attributes by component family, units, value
  ranges, consumer tags, and minimum realism grade.
- Branch validator: known branch IDs, branch-specific component allowance, and
  legal cross-branch combinations.
- Layer validator: layer membership compatibility and illegal combinations.
- Projection validator: explicit lossy projection permission, geometry
  simplification method, surface-code mapping, and unsupported feature rejection.
- Target-contract validator: current setup targets accept only the fields they
  actually maintain, such as global terrain type, rectangular zones, global wind,
  and global maritime layout fields.
- Evidence-completeness validator: successful projections must record source
  object IDs, branch memberships, component IDs, projection profile IDs, target
  setup surfaces, simplification method, dropped attributes, provenance refs, and
  an explicit no-held-capability-release flag.
- Realism gate validator: rejects claims that a manifest enables movement, LOS,
  cover, fires, damage, combat, weather simulation, hydrodynamics, hydrology
  effects, or dynamic environment mutation unless the corresponding derived
  product and runtime gate are accepted.

Validators should return stable, machine-readable rejection reasons. Required
reason-code families include unsupported geometry, unknown branch/component,
illegal branch combination, missing required component attribute, invalid units
or ranges, unsupported target field, ambiguous mapping, dropped attribute without
permission, unknown `surface`, misspelled zone fields such as `surface_type`
where only `surface` is consumed, and held capability claim.

## Projection Plan

Projection from manifest to current setup surfaces should be explicit:

- `terrain_type`: only for global compatibility modes such as `flat` or
  `legacy`.
- `WorldZoneDefinition`: only for objects that have an accepted rectangular or
  rectangle-simplified projection profile and a mapped current surface code.
- Wind setup: only for `wind_field` objects that have an accepted global or
  altitude-band simplification profile.
- Maritime setup: only for `maritime_ocean` objects that have an accepted
  global sea-state simplification profile.
- Atmosphere/weather/illumination: remain manifest-only unless a future accepted
  projection profile maps them to maintained runtime fields.
- Projection evidence must record source object IDs, component IDs, projection
  profile ID, simplification method, and dropped attributes.
- Unsupported objects are preserved in the manifest and rejected from runtime
  projection unless a profile explicitly allows omission.

Compatibility targets for current G0 static/projection-contract substages are:

| Branch | Accepted compatibility projection | Rejected or held |
| --- | --- | --- |
| `terrain` | `terrain_type` for global `flat` or explicit legacy compatibility; `WorldZoneDefinition` only for rectangle or rectangle-simplified surface-only objects mapped to current surface codes. | Non-rect geometry without simplification, route graphs, building/vegetation LOS or cover, slope/elevation grids, movement/passability/fires/damage claims, unknown surface fields. |
| `wind_field` | `WorldWindAssignment` or runtime layout wind fields: speed, direction-from, and shear, only through an explicit simplification profile. | Wind volumes, gust cells, time evolution, smoke/drift, fire behavior, or flight-dynamics claims. |
| `maritime_ocean` | Runtime layout maritime fields: configured flag, sea state, wave heading, and wave period; explicit calm sea remains a valid override. | Area sea-state patches, surf/littoral hydrodynamics, wave fields, or naval runtime release claims. |
| `atmosphere_weather` | Manifest-only in G0-J. | Fog/rain/cloud cells projected into runtime, weather simulation, sensing attenuation release. |
| `illumination` | Manifest-only in G0-J. | Time-of-day, shadow, visual/sensing effects without a maintained projection target. |
| `hydrology` | Optional lossy terrain-surface projection to a rectangular `Water` or wet/soft surface code only if the profile records all dropped hydrology attributes. | Depth, current, fordability, drainage, flood effects, mobility, or sensing effects. |
| `dynamic_environment` | No runtime projection in G0-J; reserve stable IDs/hooks as static manifest data only. | Smoke, fire, flooding, destruction, contamination, mutable runtime state, damage, or combat effects. |

Wind and maritime projections are not neutral metadata once applied: existing
flight/naval consumers may read them. Projection evidence must therefore
distinguish "setup value accepted" from "domain behavior released."

This keeps rich environment information available for later G0-K+ gates while
allowing current scenario setup to remain compatible with the current runtime.

## Derived Product Roadmap

Derived products are not G0-J runtime features. They are future contracts with
their own release gates.

| Derived product | Inputs | Future consumer | Held capability |
| --- | --- | --- | --- |
| `road_graph` | `network`, `surface_material`, `mobility_modifier` | Route planning and convoy movement | Movement. |
| `movement_cost_grid` | terrain, hydrology, vegetation, mobility components | Terrain-aware movement | Future mobility gate. |
| `passability_mask` | obstacles, hydrology, structures, actor class rules | Stuck/off-route checks | Movement/runtime behavior. |
| `los_occlusion_index` | terrain morphology, vegetation, structures, occlusion | Sensing and contact reports | LOS/sensing. |
| `cover_concealment_index` | cover, vegetation, structures, tactical state | Firefight behavior | Cover/fires. |
| `tactical_area_graph` | tactical semantics, ownership, infrastructure | Tasking and reports | Higher-grade command behavior. |
| `weather_attenuation_field` | atmosphere/weather, visibility, precipitation, sensor family hints | Sensing and flight/ship/ground observation | Weather/sensing. |
| `wind_field_volume` | wind components, altitude bands, time windows | Flight dynamics, fires, smoke/drift | Weather/dynamics. |
| `maritime_state_field` | sea state, wave heading/period, weather, littoral geometry | Naval movement and sensor context | Maritime runtime behavior. |

## G0-J Implementation Package Map

Accepted G0-J write set inside this G0 package. The namespace is
shared on purpose; it does not live under a service/domain-specific Python
package:

- `python/scenario/environment_substrate/__init__.py`
- `python/scenario/environment_substrate/manifest.py`
- `python/scenario/environment_substrate/components.py`
- `python/scenario/environment_substrate/validation.py`
- `python/scenario/environment_substrate/projection.py`
- `tests/scenario/test_environment_substrate_contracts.py`
- `tests/scenario/test_environment_projection_contracts.py`
- [G0-J static manifest contract](environment_substrate_g0_static_manifest_contract_20260605.md)

G0-J does not edit C++ runtime code. It introduces only static manifest data
structures, registries, validators, a tiny deterministic fixture, and projection
contract tests that prove unsupported rich features fail closed instead of being
silently treated as runtime behavior.

G0-K can later add generator plugins and catalogs under the same package. G0-L
can later integrate projections with scenario compiler/runtime setup. G0-M+ can
add derived products only after explicit release votes.

## Rejected Alternatives

- Terrain-only environment root.
- Ground-owned, air-owned, or naval-owned environment schema.
- Feature-label schema roots such as road, house, fog bank, wind layer, or
  sea-state patch.
- Branch inheritance trees that make one branch own another branch's semantics.
- `WorldZoneDefinition` or loose `environment.zones` dictionaries as the
  canonical schema.
- `properties{}` as a simulation-behavior escape hatch.
- G0 implementation of a parser, generator, projection runtime, weather
  simulation, hydrodynamics, movement, LOS, cover, fires, damage, combat, or
  dynamic environment mutation.
