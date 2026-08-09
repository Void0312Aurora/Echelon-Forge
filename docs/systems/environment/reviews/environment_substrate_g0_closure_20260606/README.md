# Ground Environment Substrate G0 Architecture

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/systems/environment/reviews/environment_substrate_g0_closure_20260606/README.md`
Owner: `systems/environment/reviews`
Last verified: `2026-08-08`
Review basis: `2026-06-06` G0 closure evidence; this is not an active dispatch surface.

Status: retained closure review; `2026-06-06` accepted and closed the G0 design-and-implementation line for
the shared component-based environment substrate. Accepted substages include
the G0 architecture/design records, G0-J static manifest contract, G0-K
generator/catalog contract, G0-L projection setup payload plus strict scenario
compiler ingestion, and G0-M metadata-only derived products. The closed G0 line
still does not release runtime setup application, movement, LOS, cover, fires,
damage, or full terrain-runtime/domain behavior.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Ground owner: [Ground Mission Domain](../../../../domains/ground/README.md)
- Current environment boundary: [Environment Systems](../../../../systems/environment/README.md)
- Ground specialization baseline:
  [Ground Specialization Baseline](../../../../domains/ground/standards/specialization_baseline.md)
- Runtime terrain/query primitives:
  [../../../../src/core/interfaces/environment_model.h](../../../../../src/core/interfaces/environment_model.h),
  [../../../../src/models/environment/default_environment_model.cpp](../../../../../src/models/environment/default_environment_model.cpp),
  [../../../../src/runtime/contracts/world_batch_contracts.h](../../../../../src/runtime/contracts/world_batch_contracts.h)
- Scenario compiler/generation surfaces:
  [../../../../python/scenario/compiler](../../../../../python/scenario/compiler)
- Source inventory:
  [environment_substrate_g0_source_inventory_20260605.md](environment_substrate_g0_source_inventory_20260605.md)
- Architecture implementation plan:
  [environment_substrate_g0_architecture_plan_20260605.md](environment_substrate_g0_architecture_plan_20260605.md)
- Terrain system architecture:
  [environment_substrate_g0_terrain_system_architecture_20260605.md](environment_substrate_g0_terrain_system_architecture_20260605.md)
- Subagent diagnostics dispatch:
  [environment_substrate_g0_subagent_dispatch_20260605.md](environment_substrate_g0_subagent_dispatch_20260605.md)
- Acceptance:
  [environment_substrate_g0_acceptance_20260605.md](environment_substrate_g0_acceptance_20260605.md)
- Accepted G0-J static manifest contract:
  [environment_substrate_g0_static_manifest_contract_20260605.md](environment_substrate_g0_static_manifest_contract_20260605.md)
- Accepted G0-K generator/catalog contract:
  [environment_substrate_g0_generator_catalog_20260605.md](environment_substrate_g0_generator_catalog_20260605.md)
- Accepted G0-L projection setup payload:
  [environment_substrate_g0_projection_preflight_20260606.md](environment_substrate_g0_projection_preflight_20260606.md)
  and
  [environment_substrate_g0_projection_setup_acceptance_20260606.md](environment_substrate_g0_projection_setup_acceptance_20260606.md)
- Accepted G0-L-F scenario compiler ingestion:
  [environment_substrate_g0_scenario_ingestion_acceptance_20260606.md](environment_substrate_g0_scenario_ingestion_acceptance_20260606.md)
- Accepted G0-M metadata-only derived products:
  [environment_substrate_g0_derived_products_acceptance_20260606.md](environment_substrate_g0_derived_products_acceptance_20260606.md)
- G0 closure acceptance:
  [environment_substrate_g0_closure_acceptance_20260606.md](environment_substrate_g0_closure_acceptance_20260606.md)
- G0-Viz visualization follow-on:
  [environment_substrate_g0_viz_overlay_sync_acceptance_20260606.md](environment_substrate_g0_viz_overlay_sync_acceptance_20260606.md)

## Purpose

This subproject opens the first environment-substrate follow-on from the ground
planning lane, but the environment substrate itself is shared infrastructure.
The ground scenario is the immediate pressure that exposes the missing terrain,
built-environment, vegetation, infrastructure, and tactical-area substrate; the
resulting architecture must remain usable by air, naval, ground, and future
domains instead of becoming a private schema for any one domain.

Terrain is the first branch to receive detailed architecture because it is the
first missing substrate for the planned land scenario. It is not the whole
environment object. The same `EnvironmentManifest` and `EnvironmentObject`
boundary must also have room for atmosphere, weather, wind, illumination/sun,
maritime/ocean state, hydrology, and later dynamic environment branches.

G0 is the design and implementation lane for this shared substrate. Design is a
substage of G0, not the whole of G0: the current accepted design substages name
the ownership map, component registry shape, manifest/projection boundary,
validator plan, and accepted write-scope. G0-J implements the first static
contract, G0-K implements the first deterministic generator/catalog contract and
in-memory fixture path, and G0-L implements an inert projection setup payload
contract plus strict compiler ingestion for already validated world-zone
projections. G0-M implements the first metadata-only derived-product indexes.
The closed G0 implementation intentionally stops before runtime setup
application, movement models, building LOS, or combat runtime.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Ground bootstrap | accepted | [accepted baseline](../../../../domains/ground/standards/specialization_baseline.md) | Does not release terrain-aware runtime behavior. |
| Native ground schema | accepted | `Ground_Platoon_MVP`, `UnitType::Ground` evidence in current progress | Identity only; no movement or terrain behavior. |
| Current C++ terrain model | available primitive | [source inventory](environment_substrate_g0_source_inventory_20260605.md) | Shared query/zone surface, not canonical terrain ownership. |
| Scenario compiler/runtime setup | compiler data ingestion accepted; runtime setup held | [G0-L-F ingestion acceptance](environment_substrate_g0_scenario_ingestion_acceptance_20260606.md), [source inventory](environment_substrate_g0_source_inventory_20260605.md) | Compiler can ingest inert payloads into merged scenario zones; runtime setup application is not released. |
| Environment substrate architecture | accepted G0 plan | [architecture plan](environment_substrate_g0_architecture_plan_20260605.md), [acceptance](environment_substrate_g0_acceptance_20260605.md) | Shared environment plan; no generator or runtime behavior. |
| Terrain system architecture | accepted G0 design | [terrain system architecture](environment_substrate_g0_terrain_system_architecture_20260605.md), [diagnostics dispatch](environment_substrate_g0_subagent_dispatch_20260605.md) | Defines cross-domain layered/tiled terrain substrate structure; no terrain generator or domain runtime. |
| G0-J static manifest contract | accepted implementation substage | [G0-J static contract](environment_substrate_g0_static_manifest_contract_20260605.md) | Static Python contract, validators, fixture, and contract projection only; no runtime integration. |
| G0-K generator/catalog contract | accepted implementation substage | [G0-K record](environment_substrate_g0_generator_catalog_20260605.md), [G0-K acceptance](environment_substrate_g0_generator_catalog_acceptance_20260606.md) | Python request/tile/catalog contract and deterministic in-memory fixture only; no runtime integration. |
| G0-L projection setup and compiler ingestion | accepted implementation substage | [G0-L preflight](environment_substrate_g0_projection_preflight_20260606.md), [G0-L setup acceptance](environment_substrate_g0_projection_setup_acceptance_20260606.md), [G0-L-F ingestion acceptance](environment_substrate_g0_scenario_ingestion_acceptance_20260606.md) | Python inert setup payload plus strict compiler data ingestion only; no runtime setup application. |
| G0-M metadata-only derived products | accepted implementation substage | [G0-M acceptance](environment_substrate_g0_derived_products_acceptance_20260606.md) | Contract/index products only; no movement, LOS, cover, or runtime consumers. |
| G0-Viz tactical map overlay sync | accepted visualization follow-on | [G0-Viz acceptance](environment_substrate_g0_viz_overlay_sync_acceptance_20260606.md) | Draws accepted G0 data on the tactical map only; no runtime setup application, movement, LOS, cover, or terrain behavior. |
| Ground route/terrain/LOS/fires | held | ground progress and dispatch queue | Must remain held until separate release gates. |

## Scope

In scope:

- Define the terrain system as shared environment infrastructure that can serve
  air, naval, ground, and future domains.
- Define the environment-substrate root so terrain is one branch inside a wider
  environment object that can also absorb atmosphere, weather, wind,
  illumination/sun, maritime/ocean, and hydrology branches.
- Define a component-based `EnvironmentObject` manifest architecture with
  extensible components and catalogs.
- Define default layer-stack semantics without making the stack closed.
- Define generator plugin boundaries and deterministic seed/provenance rules.
- Define validators for object identity, geometry, references, component
  completeness, layer compatibility, and projection safety.
- Define runtime projection from rich manifest to current `terrain_type` plus
  `WorldZoneDefinition` compatibility surfaces.
- Define and implement the first metadata-only derived-product contracts, while
  keeping road graph, movement-cost grid, passability mask, runtime
  LOS/occlusion, cover/concealment, and tactical-area graph behind later gates.
- Define the terrain-system architecture for layered terrain, tiling, catalogs,
  generator stages, projection profiles, and derived-product gates.
- Produce and maintain accepted implementation package maps for G0 substages.

Out of scope:

- A runtime or scenario-producing terrain generator implementation beyond the
  G0-K deterministic in-memory fixture.
- Runtime setup application or runtime consumers for accepted metadata products.
- A new C++ terrain runtime for any domain.
- Route following, speed updates, passability behavior, stuck/off-route checks,
  LOS occlusion, cover, fires, damage, suppression, or combat.
- Hardcoding road, forest, village, or building as the core schema boundary.
- Replacing current `WorldZoneDefinition` setup contracts.

## Architecture Direction

The detailed design is in
[environment_substrate_g0_architecture_plan_20260605.md](environment_substrate_g0_architecture_plan_20260605.md).
The short form is:

The target architecture is:

```text
Scenario Intent
  -> Generator Plugins
  -> Component-Based Environment Manifest
  -> Validators
  -> Derived Products
  -> Runtime Projection
  -> Query / Simulation Consumers
```

The core object shape should stay generic:

```text
EnvironmentObject
  identity
  branch_membership[]
  geometry
  layer_membership
  components[]
  properties{}
  provenance
```

Feature labels such as road, treeline, building, trench, minefield, flooded
field, weather cell, wind layer, sea-state area, or village block are catalog
entries. Runtime capability comes from components such as mobility, occlusion,
cover, material, structure, vegetation, network, hydrology,
atmospheric_profile, weather_effect, wind_field, illumination, maritime_state,
tactical semantic, hazard, and damageable.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `G0-A Architecture Implementation Plan` | Freeze architecture, ownership, component registry, manifest/projection boundary, and accepted implementation map. | Accepted ground bootstrap baseline and current src terrain inventory. | README, task clusters, source inventory, component registry proposal, manifest/projection/validator plan, and acceptance gate are synchronized. | accepted |
| `G0-J Static Manifest Contract` | Implement schema/contract and validators for static manifests. | Accepted G0 architecture/design substages. | Deterministic manifest fixture and validators pass without runtime claims. | accepted |
| `G0-K Generator Catalog Contract` | Implement deterministic generator request/tile/catalog contracts. | Accepted G0-J manifest contract. | Generator creates reproducible in-memory environment manifests with catalog provenance. | accepted |
| `G0-L Projection` | Project manifest subsets into current scenario/world setup surfaces. | Accepted G0-K generator output. | Inert setup payload/evidence conversion and strict scenario compiler data ingestion are accepted; runtime setup application remains held. | accepted |
| `G0-M Derived Products` | Introduce first derived products for later movement/LOS gates. | Accepted G0-L compiler ingestion boundary. | Metadata-only surface-zone and occlusion-candidate indexes validate without overclaiming runtime behavior. | accepted |

## Task Clusters

- Task cluster plan:
  [environment_substrate_g0_task_clusters_20260605.md](environment_substrate_g0_task_clusters_20260605.md)

## Outputs And Evidence

G0 should produce:

- [source inventory](environment_substrate_g0_source_inventory_20260605.md) for
  existing C++ terrain/query and scenario compiler/runtime setup surfaces;
- [architecture implementation plan](environment_substrate_g0_architecture_plan_20260605.md)
  for component registry, branch registry, catalog boundary, manifest,
  validators, projection, and derived products;
- [terrain system architecture](environment_substrate_g0_terrain_system_architecture_20260605.md)
  for layered/tiled terrain, generator boundaries, projection profiles, and
  derived-product gates;
- [subagent diagnostics dispatch](environment_substrate_g0_subagent_dispatch_20260605.md)
  recording read-only C++ and Python terrain-foundation analysis packets;
- [acceptance record](environment_substrate_g0_acceptance_20260605.md);
- [accepted G0-J static manifest contract](environment_substrate_g0_static_manifest_contract_20260605.md);
- [accepted G0-K generator/catalog contract](environment_substrate_g0_generator_catalog_20260605.md);
- [G0-K acceptance record](environment_substrate_g0_generator_catalog_acceptance_20260606.md);
- [accepted G0-L projection setup payload contract](environment_substrate_g0_projection_setup_acceptance_20260606.md);
- [G0-L projection preflight and task map](environment_substrate_g0_projection_preflight_20260606.md);
- [accepted G0-L-F scenario compiler ingestion](environment_substrate_g0_scenario_ingestion_acceptance_20260606.md);
- [accepted G0-M metadata-only derived products](environment_substrate_g0_derived_products_acceptance_20260606.md);
- [G0 closure acceptance](environment_substrate_g0_closure_acceptance_20260606.md);
- accepted file/package write-scope for G0-J implementation;
- guardrails that keep movement, LOS, cover, fires, damage, and combat held.

## Acceptance Gate

This subproject can be marked accepted only when:

- the G0 architecture plan names the component registry, layer semantics,
  environment branch registry, manifest shape, validator plan, projection plan,
  and future consumer gates;
- current `src` terrain/query primitives are represented honestly as shared
  primitives, not as a full terrain runtime;
- the terrain-system plan keeps current C++/Python setup as compatibility
  projection/query surfaces and defines layered, tiled, component-based terrain
  data above them;
- parent ground README, progress tracker, and dispatch queue point to this
  package as the accepted environment-substrate G0 follow-on;
- G0-L-F strict compiler ingestion and G0-M metadata-only derived products are
  covered by focused tests and acceptance records;
- `git diff --check` is clean for touched docs;
- no runtime setup application, movement, LOS, cover, fires, damage, or combat
  capability is claimed or released.

## Residuals And Next Steps

- G0-J has implemented and accepted only the static manifest contract, registries,
  validators, deterministic fixture, and contract-level projection tests.
- G0-K has accepted only the Python generator/catalog contract, deterministic
  request/tile/seed/provenance rules, catalog admission, and in-memory generated
  manifest fixture.
- G0-L has accepted the Python projection setup payload contract and strict
  scenario compiler ingestion for already validated `world_zone_definition`
  projection output.
- G0-M has accepted metadata-only `surface_zone_index` and
  `occlusion_candidate_index` products.
- G0 has no remaining internal held slice after the closure acceptance. Runtime
  setup application, runtime consumers, movement, LOS, cover, fires, damage,
  and combat remain downstream release gates.
- Route movement remains governed by a separate G6-D3/G6-F-style release vote.
- The implementation package is named shared `environment_substrate`, while the
  task record remains indexed from ground as the incubating demand lane.

## Archive

Superseded G0 design records move under this subproject's future `archive/`
only after a current README/status or acceptance surface points to the
replacement.
