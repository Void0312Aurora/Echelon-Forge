# Environment Runtime

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/systems/environment/work/active/environment_runtime/README.md`
Owner: `systems/environment`
Last verified: `2026-10-29`

Status: `2026-10-29` active. `P0 Boundary` accepted by the owner on `2026-09-28`;
`P1 Evidence` (`P1-A`, `P1-B`) passed on `2026-10-29`, see the
[P1 inventory](environment_runtime_p1_inventory_20261029.md). No implementation
cluster has started.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- [Environment Systems](../../../README.md) — owner README; its G0/G1 boundary
  says a runtime package must open here with its own scope
- [Cross-Domain Systems](../../../../README.md)
- [Gradient Realism Principles](../../../../standards/gradient_realism_principles.md)
- [Public Data Source Admission Standard](../../../../../research/standards/public_data_source_admission.md)
- [Geodetic Frame](../../../../physics/work/active/geodetic_frame/README.md) — sibling package
- Demand cases:
  [Carrier Strike Group Engagement](../../../../../domains/naval/work/active/carrier_strike_group_engagement/README.md)
  (naval) and the Ground native-terrain line, on `main` since `2026-10-01`
  ([accepted record](../../../../../domains/ground/reviews/ground_arnis_native_terrain_v1_20260924/README.md))
- [Subproject Creation Standard](../../../../../engineering/automation/rules/subproject_creation_standard.md)
- Code: `src/core/interfaces/environment_model.h`, `src/models/environment/`,
  `python/scenario/environment_substrate/`, `python/scenario/runtime/kernel_apply.py`

## Purpose

The offline environment substrate is already a shared, cross-domain contract:
one manifest with ordered layers for physical base, terrain surface, hydrology,
atmosphere and weather, wind, illumination, maritime ocean, vegetation, built
structure, and infrastructure. The runtime does not follow that model. It holds
one global raster, one global maritime state, and constant wind and sun, and the
only runtime terrain line — Ground's native Arnis raster, on an unmerged branch —
adds Ground-specific types and includes directly into the shared interface and
implementation.

This package makes the layered environment a single runtime authority that every
domain reads through domain-neutral queries. It covers land, freshwater, sea, and
atmosphere on one vertical datum, in multiple tiles and resolutions, with declared
time and space variation. It also moves Ground's native terrain runtime onto this
shared authority, leaving Ground-specific movement and observation logic in the
Ground domain.

Data acquisition for the ocean is a separate, later line of this owner (see
[Residuals](#residuals-and-next-steps)); this package defines the runtime layers
and contracts that data must fill.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Offline layered substrate | accepted G0, on `main` | `python/scenario/environment_substrate/components.py` (`maritime_ocean` layer 38, `hydrology` 30, `wind_field` 36, `illumination` 37) | data contract only; no runtime authority |
| Arnis land/near-shore import | accepted phase 1, on `main` | `tools/environment/arnis/`; `importers/arnis_bundle.py` | OSM + USGS 3DEP + ESA WorldCover; water is footprint and surface elevation only — no depth, temperature, or salinity |
| Runtime terrain | one global raster | `RasterGrid` in `src/models/environment/default_environment_model.cpp` | no multi-tile, no multi-layer, unspecified vertical datum |
| Ground native terrain | accepted by Ground `2026-09-24`; on `main` since `2026-10-01` (merge `85abc7ce6`) | `be2de24af` and the army stack #82–#85 | Ground-owned methods, types and policies inside shared files, without domain includes; see the [P1 inventory](environment_runtime_p1_inventory_20261029.md) |
| Maritime state | scenario constant, global | `set_maritime_state` / `get_maritime_state` | no swell/wind-sea split, no spatial field |
| Wind, sun | scenario constants | `set_wind`, `set_sun_direction` | no clock-driven day/night |
| Ocean data | absent | none | no bathymetry, temperature/salinity profile, or ambient noise |

The shared interface now contains a reversible bathymetry admission seam:
`IEnvironmentModel::get_bathymetry_along_segment` returns a domain-neutral
minimum water depth plus explicit availability, horizontal/vertical frame,
source, surface elevation, and step-time metadata. The default environment
returns `Unavailable`; it does not synthesize an ocean floor. Naval motion
consumes this seam only when an entity opts into `SubmarineBathymetryPolicy`.
Missing, dry, out-of-coverage, invalid-datum, inconsistent-frame, or
time-ambiguous observations hold depth and horizontal movement, while entities without
the policy preserve the legacy open-water profile. A valid observation is
defined over the full proposed horizontal step, so a provider must account for
a rising seabed within that segment before returning `Valid`.
Heading can still evolve within the existing turn limit during a held step.
This initial slice is native-only opt-in: no content-loader or Agent observation
surface enables or exposes the environmental truth. The policy is admitted in
the component graph and reflected for state transfer; the resulting composition
identity and provenance are regenerated. The synthetic fixtures are test data,
not an admitted ocean atlas.

### Ground coupling on `main`

The `2026-09-28` findings on `origin/work/army-mechanisms` at `3cee10ff` are
superseded. Measured on `main` at `3d7df0818` (`2026-10-29`, P1-B):

- Neither shared file includes a domain header. `16fb9bcda` removed the
  `ground_tasking_enums.h` include, the `movement_effects.h` include and
  `get_ground_transition_movement_observation` before the army stack merged.
- `environment_model.h` still declares Ground methods and types:
  `get_ground_field_semantic_observation`, `get_ground_transition_observation`,
  `load_arnis_field_overlay`, `GroundFieldSemanticObservation` and
  `GroundTransitionObservation`. `get_ground_slope_deg` is domain-neutral but
  misnamed.
- `get_terrain_at` still treats `Water` as blocking and returns `Obstacle`
  outside the loaded raster, while `get_terrain_elevation` returns the
  procedural hill there. Both are Ground passability semantics, and the two
  queries disagree off the raster.

The [P1 inventory](environment_runtime_p1_inventory_20261029.md) classifies every
environment read and every Ground item, and records the decision for the
unmerged army terrain line-of-sight query.

## Scope

In scope:

- **Layered runtime state** aligned with the substrate layer order: elevation
  (land) and bathymetry (water) on one vertical datum, landcover, freshwater and
  sea water bodies, coastline and shoreline, atmosphere and weather, wind,
  illumination, and the maritime ocean state;
- **one vertical datum** for land elevation, water surface, and water depth, with
  the datum recorded in every bundle;
- **multi-tile, multi-resolution rasters** so a metre-scale land tile and a
  kilometre-scale ocean grid can be queried together; edges and gaps have
  declared behavior instead of a fail-closed obstacle;
- **domain-neutral queries** that report what the environment *is* at a point or
  along a segment: surface class, elevation, depth, water-body kind, slope,
  landcover, sea state, wind, visibility, sun, acoustic environment data.
  Whether that is passable, navigable, or concealing is decided by each domain;
- **declared time and space variation** for weather, wind, and sea state, with a
  clock-driven sun from scenario date, time, and geodetic anchor;
- **freshwater bodies as first-class water**, sharing the water-body contract with
  the sea: kind (river, lake, reservoir, sea), surface elevation, depth, and
  optional flow, salinity, and temperature slots. This package fills only what a
  source supplies and leaves the rest unset with a recorded residual. River
  crossing, fording, and bridging behavior stay with Ground;
- **ocean acoustic environment as data**: sound-speed profile or its temperature,
  salinity, and depth inputs, mixed-layer depth, bottom class, ambient noise.
  Propagation physics belongs to sensing;
- **migrating Ground's native terrain runtime** onto the shared state and queries
  (see Phase Plan), with the Ground-specific movement and observation logic moved
  back to the Ground domain.

Out of scope:

- ocean and freshwater data acquisition (the later ocean data line);
- weather forecasting, numerical ocean/atmosphere models, coupled air-sea
  dynamics, hydrodynamic river models;
- any consumer physics or decision: ship seakeeping, aircraft recovery limits,
  sonar propagation, radar clutter, Ground passability, fording, and movement
  cost;
- live real-world data ingestion.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze scope and the layered runtime contract. | owner approval | README and task clusters approved | accepted |
| `P1 Evidence` | Inventory every environment read, the `main` runtime, and the Ground branch's shared-file changes. | `P0` | each read site and each Ground addition classified as shared, Ground-owned, or retired | pass `2026-10-29` ([inventory](environment_runtime_p1_inventory_20261029.md)) |
| `P2 Contract` | Layered state, vertical datum, water-body contract, tile model, domain-neutral query API. | `P1` | contract documented and covered by native tests | planned |
| `P3 Implementation` | Multi-tile rasters, water bodies, coastline, varying weather/sea state, clock-driven sun, acoustic data. | `P2`; geodetic anchor from [Geodetic Frame](../../../../physics/work/active/geodetic_frame/README.md) `P2-A` for sun position and tile placement | native and Python tests pass against declared inputs and references | planned |
| `P4 Migration` | Move Ground's native terrain onto the shared runtime; move Ground logic back to Ground; move remaining consumers onto the queries. | `P3` | shared files include no domain header; Ground acceptance tests rerun green | planned |
| `P5 Validation` | Cross-domain regression and throughput. | `P4` | air, ground, naval suites pass or change by documented amounts | planned |
| `P6 Closure` | Acceptance, standards, indexes. | `P5` | acceptance record; runtime contract promoted to an environment standard | planned |

### Ground migration

Ground native terrain is on `main`, so the migration starts from `main`.

- Shared: raster loading and tiling, elevation and landcover queries, water-body
  and coastline queries, raw slope from elevation.
- Ground-owned: `GroundStance`-dependent movement effects, passability,
  transition cost, field-semantic observations. These move to
  `src/systems/domains/ground/` or `src/models/domains/ground/` and are built on
  the shared queries.
- Retired from the shared interface: the Ground field-semantic and transition
  methods and structs in `environment_model.h`. The Ground include and the
  `models` → `systems` edge were already removed by `16fb9bcda`.
- The Ground package's accepted tests are the migration's regression evidence;
  any changed result is recorded, not re-tuned.

## Task Clusters

- [environment_runtime_task_clusters_20260928.md](environment_runtime_task_clusters_20260928.md)

## Outputs And Evidence

- layered runtime environment state and domain-neutral query interface;
- vertical-datum, tile, and water-body contracts;
- scenario schema for environment declaration and variation;
- clock-driven solar geometry with reference tests;
- ocean acoustic environment data contract;
- migrated Ground terrain with rerun Ground acceptance tests;
- cross-domain regression record and throughput delta;
- an environment standard for the runtime contract.

## Acceptance Gate

This package can be marked accepted only when:

- `src/core/interfaces/environment_model.h` and `src/models/environment/**`
  include no domain header and declare no domain-specific type or method;
- every migrated consumer reads the environment only through the shared queries;
- land elevation, water surface, and water depth share one declared vertical
  datum, and every bundle records it;
- a scenario can combine a land tile and an ocean grid, and a query outside all
  tiles returns a declared result instead of `Obstacle`;
- solar geometry matches published references;
- variation is deterministic under a seed and reproducible in replay;
- Ground's accepted native-terrain tests pass on the migrated code, or each
  changed result is explained and recorded;
- air, ground, and naval regression suites pass, or changes are explained;
- no consumer physics or domain decision is added inside this package.

## Residuals And Next Steps

- `P2-A` contract (main thread), using the P1 inventory's decisive findings:
  one out-of-tile result for elevation and surface, a declared vertical datum,
  absolute versus above-terrain heights for line of sight, and earth curvature.
- **Ocean data line** (this owner, opens after `P2 Contract`): importers for
  bathymetry, temperature/salinity climatology, sea state and wind, and coastline
  from admitted public sources, plus a seeded synthetic ocean generator for
  mirror and fictional scenarios. Candidate sources are recorded, not admitted,
  until they pass the [admission standard](../../../../../research/standards/public_data_source_admission.md).
- Freshwater depth, flow, and temperature have little public coverage; until a
  source is admitted they stay unset with a residual, and Ground river crossing
  consumes the water-body contract when it needs them.
- The synthetic terrain generator and zone/road derivations exist only in the
  `2026-09-19` WIP archive (`D:/workshop/Research/Echelon-Forge-WIP-archive-20260919-160114/`);
  restoring them is a separate substrate decision.
- Clock-driven sun depends on the geodetic anchor; until it lands, the scenario
  sun declaration stays authoritative.

## Archive

Accepted records move to `docs/systems/environment/reviews/`; the runtime
contract is promoted to an environment standard.
