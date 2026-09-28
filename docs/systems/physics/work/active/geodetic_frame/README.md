# Geodetic Frame

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/systems/physics/work/active/geodetic_frame/README.md`
Owner: `systems/physics`
Last verified: `2026-09-28`

Status: `2026-09-28` active. `P0 Boundary` accepted; `P1 Evidence` passed with the
[P1-A inventory](geodetic_frame_p1a_inventory_20260928.md) (12 must-migrate sites).
`P2` implementation is next.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- [Cross-Domain Systems](../../../../README.md)
- [Gradient Realism Principles](../../../../standards/gradient_realism_principles.md)
- [Physics Engine Upgrade Roadmap](../../issues/physics_engine_roadmap.md) (draft planning input)
- [Carrier Strike Group Engagement](../../../../../domains/naval/work/active/carrier_strike_group_engagement/README.md)
  — first demand case
- [Subproject Creation Standard](../../../../../engineering/automation/rules/subproject_creation_standard.md)
- Code: `src/components/basic/common.h` (`Transform`), `src/components/systems/navigation.h`,
  `src/components/physics/instruments.h`, `src/components/systems/sensor.h`,
  `src/models/systems/default_sensor_model.cpp`

## Purpose

The runtime places every entity in a flat local East-North-Up frame relative to
the scenario origin (`Transform` in `src/components/basic/common.h`). That frame
is adequate for the tens of kilometres that current air, ground, and naval
scenarios span. Carrier strike group scenarios span several hundred kilometres,
and across that distance earth curvature changes radar and radio horizons,
sensor line of sight, great-circle navigation, missile ranges, and data-link
reach. Latitude and longitude now exist only as EGI/navigation fields.

This package gives the whole simulation one geodetic frame: an explicit earth
model, a defined relation between the local simulation frame and geodetic
coordinates, and curvature-aware geometry queries that every domain uses. It is
cross-domain infrastructure. The naval carrier group program is the first demand
case, and no domain owns the frame.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Simulation frame | flat local ENU | `Transform` (`src/components/basic/common.h`) | no earth model, no curvature |
| Geodetic fields | navigation-only; hard-coded anchor | EGI conversion in `src/systems/systems/navigation_system.h:9-48` uses a fixed Nellis AFB anchor, equirectangular | 3.7 km error at 250 km east; the Arnis WGS84 origin is dropped by the importer; no scenario anchor exists |
| Radar horizon | per-sensor proxy flag; **the gate never rejects** | `enforce_radar_horizon` (`src/components/systems/sensor.h`); `default_sensor_model.cpp:256-273` limits at `max(max_range, horizon)` after a range gate already applied | geometric `3570·(√h1+√h2)` constant, not 4/3; see the [P1-A inventory](geodetic_frame_p1a_inventory_20260928.md) |
| Data-link horizon | the only binding horizon | `src/systems/systems/data_link_system.h:48-52` | geometric `3.57` km constant, 13.4 % short of the 4/3 radio horizon |
| Terrain line of sight | environment model | `IEnvironmentModel::check_line_of_sight` (`src/core/interfaces/environment_model.h`) | terrain only; no earth bulge |

## Scope

In scope:

- a declared earth model, starting with a spherical earth and a documented path
  to WGS-84 ellipsoidal geometry, with the choice recorded as a scenario input;
- the relation between the local simulation frame and geodetic coordinates:
  a scenario geodetic anchor, conversions both ways, and the declared error
  bound of the local frame at a given distance from the anchor;
- curvature-aware geometry queries: geometric and refracted horizon distance,
  earth-bulge line-of-sight obstruction, great-circle range and bearing;
- migrating the existing radar-horizon proxy onto the shared query;
- regression evidence that air, ground, and naval scenarios either keep their
  results or change by the documented, curvature-caused amount.

Out of scope:

- atmospheric refraction beyond the standard effective-earth-radius factor;
  anomalous ducting stays with sensing and environment;
- terrain elevation models and geoid undulation;
- changing entity motion integration to a geodetic state; motion stays in the
  local frame unless a later decision says otherwise;
- any domain-specific use of the queries, which each consuming owner performs.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze scope, earth-model choice, and frame contract. | owner approval | README and task clusters approved | accepted |
| `P1 Evidence` | Inventory every place that assumes a flat frame or computes a horizon. | `P0` | inventory classifies each site as must-migrate, may-stay, or out of scope | accepted ([inventory](geodetic_frame_p1a_inventory_20260928.md)) |
| `P2 Implementation` | Earth model, anchor, conversions, geometry queries. | `P1` | native and Python tests pass against reference values | planned |
| `P3 Integration` | Move sensing horizon and line of sight onto the queries; expose the anchor in scenarios. | `P2` | consumers call the shared queries; proxy flag retired or wrapped | planned |
| `P4 Validation` | Cross-domain regression and throughput check. | `P3` | air, ground, naval suites pass or change by the documented amount | planned |
| `P5 Closure` | Acceptance and indexes. | `P4` | acceptance record; lasting contract promoted to a physics standard | planned |

## Task Clusters

- [geodetic_frame_task_clusters_20260928.md](geodetic_frame_task_clusters_20260928.md)

## Outputs And Evidence

- earth-model and frame components with a scenario-level geodetic anchor;
- shared geometry query API used by sensing;
- reference-value tests (horizon distance, great-circle range) with sources;
- cross-domain regression record and a throughput delta;
- a physics standard describing the frame contract.

## Acceptance Gate

This package can be marked accepted only when:

- the earth model, the anchor, and both conversions have tests against
  published reference values;
- every consumer that `P1` classified as must-migrate calls the shared queries;
- air, ground, and naval regression suites pass, or each changed result is
  explained by curvature and recorded;
- the local-frame error bound is documented and enforced for scenario extents;
- no domain-specific behavior is added inside this package.

## Residuals And Next Steps

- `P0` owner review.
- Ellipsoidal (WGS-84) geometry is planned as a second step after the spherical
  model; which scenarios require it is decided in `P1`.
- Whether motion itself must move to a geodetic state is out of scope and needs
  a separate decision if `P4` shows the local frame is insufficient.

## Archive

Accepted records move to `docs/systems/physics/reviews/`. The frame contract is
promoted to a physics standard.
