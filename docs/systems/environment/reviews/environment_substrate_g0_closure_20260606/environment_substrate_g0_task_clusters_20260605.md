# Environment Substrate G0 Task Clusters

Status: `2026-06-05` accepted finite G0 architecture/design substage with
branch-expansion diagnostics integrated for [README.md](README.md), updated on
`2026-06-06` through complete G0 closure. G0 is the overall
design-and-implementation line; this record now indexes the architecture
clusters plus the accepted G0-J/K/L/M implementation substages.

## Boundary

This cluster plan designs the environment-substrate architecture and accepted
implementation map. It now records accepted static manifests, deterministic
generator/catalog contracts, inert projection setup plus compiler data
ingestion, and metadata-only derived products. It does not implement runtime
setup application, movement, LOS, cover, fires, damage, or combat behavior.

Supporting records:

- Source inventory:
  [environment_substrate_g0_source_inventory_20260605.md](environment_substrate_g0_source_inventory_20260605.md)
- Architecture plan:
  [environment_substrate_g0_architecture_plan_20260605.md](environment_substrate_g0_architecture_plan_20260605.md)
- Terrain system architecture:
  [environment_substrate_g0_terrain_system_architecture_20260605.md](environment_substrate_g0_terrain_system_architecture_20260605.md)
- Subagent diagnostics:
  [environment_substrate_g0_subagent_dispatch_20260605.md](environment_substrate_g0_subagent_dispatch_20260605.md)

## Finite Clusters

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `G0-A Source Inventory` | main thread / diagnostics | n/a | Inventory current C++ environment model, zone/world setup, scenario compiler/runtime setup, and ground task boundaries. | `environment_substrate_g0_source_inventory_20260605*.md` | No code, no generator, no runtime capability claims. | Read cited files; `git diff --check` for task docs. | Source inventory records what exists and what it does not prove. | No dependency; can run before architecture clusters. | 1 | pass |
| `G0-B Ontology And Component Registry` | main thread | n/a | Define generic `EnvironmentObject`, branch registry, component registry, open layer-stack semantics, catalog boundary, and capability requirements by realism grade. | `environment_substrate_g0_architecture_plan_20260605*.md`, README sync | No hardcoded road/forest/building/weather/wind/sea-state schema roots. | Architecture review against source inventory and user extensibility requirement. | Components and branches are extensible; feature labels are catalog entries composed from components. | Depends on `G0-A`; serial with `G0-C` while editing the same plan. | 1 | pass |
| `G0-C Manifest, Projection, Validators` | main thread | n/a | Define manifest shape, validator classes, lossy projection boundary to `WorldZoneDefinition`, and derived-product placeholders. | `environment_substrate_g0_architecture_plan_20260605*.md`, README sync | No manifest parser, no projection code, no derived product implementation. | Projection and validator sections explicitly fail closed for unsupported features. | Projection is explicitly lossy and current-runtime-compatible only; rich manifest remains authoritative for later gates. | Depends on `G0-A`; serial with `G0-B` while editing the same plan. | 1 | pass |
| `G0-E Terrain System Architecture` | main thread plus diagnostics workers | inherited parent / read-only diagnostics | Analyze current terrain foundation and define shared, layered/tiled terrain-system architecture, generator boundaries, projection profiles, and derived-product gates. | `environment_substrate_g0_terrain_system_architecture_20260605*.md`, `environment_substrate_g0_subagent_dispatch_20260605*.md`, README/task-cluster sync | No terrain generator implementation, no C++ domain runtime, no movement/LOS/cover/fires/damage/combat release, no single-domain terrain ownership. | C++ and Python diagnostics return `pass`; local evidence records current setup limitations and held capabilities. | Terrain system keeps current C++/Python surfaces as compatibility/query consumers and defines shared manifest-first structure above them. | Depends on `G0-A`; diagnostics can run in parallel, integration serial. | 1 | pass |
| `G0-F Non-Terrain Environment Branch Inventory` | read-only diagnostics worker | inherited parent / xhigh | Inventory existing atmosphere/weather, wind, illumination/sun, maritime/ocean, hydrology, and dynamic-environment hints in current C++ and Python setup surfaces. | none; diagnostics packet only | No edits, no new schema, no runtime capability claims, no terrain-only ownership. | Worker packet cites inspected files and maps current surfaces to branch implications and gaps. | Returned packet identifies what exists today, what is compatibility setup only, and what must remain held. | Parallel with `G0-G` and `G0-H`; depends on current branch-registry draft. | 1 | pass |
| `G0-G Branch Ontology And Component Gap Review` | read-only diagnostics worker | inherited parent / xhigh | Review the branch registry and component model for cross-branch environment objects and identify missing branch/component/catalog rules. | none; diagnostics packet only | No edits, no generator, no branch-specific runtime behavior, no replacement of current docs as authority. | Worker packet reviews G0 architecture docs and returns branch/component gaps plus rejected alternatives. | Returned packet can be integrated into architecture plan without expanding G0-J beyond static manifest/validators. | Parallel with `G0-F` and `G0-H`; depends on current branch-registry draft. | 1 | pass |
| `G0-H Projection And Validator Gate Review` | read-only diagnostics worker | inherited parent / xhigh | Review how branch-aware manifests could fail closed when projected to current `WorldTerrainAssignment`, `WorldZoneDefinition`, wind, maritime, and scenario setup fields. | none; diagnostics packet only | No projection code, no parser implementation, no runtime branch behavior. | Worker packet maps accepted compatibility projections, rejected projections, validator classes, and held gates. | Returned packet defines G0-J validator/projection evidence requirements for static contract work. | Parallel with `G0-F` and `G0-G`; depends on current branch-registry draft. | 1 | pass |
| `G0-D Implementation Package Map` | main thread | n/a | Name current and future G0 implementation files/tests and synchronize parent ground docs. | Ground parent docs plus this task package docs. | No generator code and no runtime release in this substage. | Parent README/progress/queue point to this package; `git diff --check` clean. | Ground README/progress/queue are synchronized; route/terrain/LOS/fires remain held. | Depends on `G0-B`, `G0-C`, and `G0-E`; closure is serial. | 1 | pass |
| `G0-I Branch Expansion Integration` | main thread integration | n/a | Integrate returned `G0-F/G/H` diagnostics into source inventory, architecture plan, terrain-branch plan, task clusters, and parent docs if warranted. | `docs/systems/environment/reviews/environment_substrate_g0_closure_20260606/*.md`, `docs/domains/ground/README*.md`, `docs/systems/environment/README*.md`, `docs/systems/environment/reviews/environment_substrate_g0_closure_20260606/README*.md` | No generator implementation and no runtime release in this substage. | Local review of worker packets plus `git diff --check` for touched docs. | Branch expansion evidence is integrated or explicitly rejected, and remaining held capabilities are preserved. | Serial after `G0-F/G/H` return. | 1 | pass |
| `G0-L-F Scenario Compiler Ingestion` | main thread implementation | n/a | Wire accepted projection setup payloads into scenario compiler data ingestion. | `python/scenario/environment_substrate/scenario_ingestion.py`, `python/scenario/compiler/service.py`, package exports, focused tests, G0 package docs | No runtime setup application, no C++ edits, no generated scenario artifacts, no movement/LOS/cover/fires/damage/combat. | Focused ingestion pytest and G0 closure suite. | Strict ingestion is accepted and fail-closed; runtime setup remains held. | Depends on accepted G0-L-E. | 1 | accepted |
| `G0-M Metadata Derived Products` | main thread implementation | n/a | Implement first metadata-only derived-product indexes. | `python/scenario/environment_substrate/derived_products.py`, package exports, focused tests, G0 package docs | No road graph, movement-cost grid, passability mask, runtime LOS/cover product, tactical-area runtime graph, or runtime consumers. | Focused derived-product pytest and G0 closure suite. | Metadata/index products accepted without runtime capability claims. | Depends on accepted G0-L boundary. | 1 | accepted |

## Dispatch Rules

- Do not edit archived G0-G6 ground evidence packages.
- Do not create terrain generator code in G0.
- Do not extend `WorldZoneDefinition` into a canonical terrain schema in G0.
- Do not add scenario files that claim movement, LOS, cover, fires, damage, or
  combat.
- Treat `WorldZoneDefinition` as compatibility projection, not as the full
  environment schema.
- Treat terrain as the first detailed branch, not as the whole environment
  substrate; atmosphere/weather, wind, illumination, maritime/ocean, hydrology,
  and dynamic environment branches must remain merge targets.
- Every worker packet must map to exactly one assigned `G0-F`, `G0-G`, or `G0-H`
  diagnostics cluster.
- Diagnostics workers are read-only and must not create new conversation
  threads, edit files, stage changes, or commit.
- Keep later G0 implementation write-scope finite, named, and release-gated.

## Worker Packet Requirements

Any delegated diagnostics packet must return:

- files inspected;
- existing mechanism summary;
- proposed architecture decision;
- rejected alternatives;
- acceptance or blocker status;
- explicit held capability claims.

## Validation Plan

G0 validation is documentation and architecture validation:

```bash
git diff --check -- docs/systems/environment/reviews/environment_substrate_g0_closure_20260606 docs/domains/ground/README.md docs/domains/ground/README.zh.md docs/systems/environment/README.md docs/systems/environment/README.zh.md docs/systems/environment/reviews/environment_substrate_g0_closure_20260606/README.md docs/systems/environment/reviews/environment_substrate_g0_closure_20260606/README.zh.md
```

Focused code tests are required for implementation substages such as accepted
G0-J, G0-K, G0-L, and G0-M, and remain separate from architecture-only
diagnostics.

G0 closure validation:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py tests/scenario/test_scenario_compiler.py
# 59 passed
```

## Acceptance Criteria

G0 is accepted only if:

- the source inventory and architecture proposal are present;
- the branch registry and component registry are generic and extensible;
- validators, projection, and derived-product boundaries are named;
- terrain-system architecture separates shared layered/tiled manifest data from
  current compatibility projection/query consumers;
- atmosphere/weather, wind, illumination, maritime/ocean, hydrology, and dynamic
  environment branches are represented as merge targets under the same
  environment manifest root;
- terrain ownership is not single-domain; air, naval, ground, and future domains
  can migrate onto the same substrate;
- G0-J/G0-K/G0-L/G0-M implementation scope is finite and testable;
- all movement, LOS, cover, fires, damage, combat, and full ground runtime claims
  remain held.

## Residual Map

- G0-J static manifest contract is now accepted:
  [environment_substrate_g0_static_manifest_contract_20260605.md](environment_substrate_g0_static_manifest_contract_20260605.md).
  It includes static data structures, registries, validators, deterministic
  fixture, and fail-closed projection contract tests only.
- G0-K generator/catalog contract is now accepted:
  [environment_substrate_g0_generator_catalog_20260605.md](environment_substrate_g0_generator_catalog_20260605.md).
  It includes Python request/tile/catalog contracts, deterministic seed
  derivation, catalog admission, and in-memory fixture generation only.
- G0-L projection setup payload contract is now accepted:
  [environment_substrate_g0_projection_setup_acceptance_20260606.md](environment_substrate_g0_projection_setup_acceptance_20260606.md).
  It includes Python inert payload/evidence conversion for already validated
  `world_zone_definition` projections only.
- G0-L-F scenario compiler ingestion is now accepted:
  [environment_substrate_g0_scenario_ingestion_acceptance_20260606.md](environment_substrate_g0_scenario_ingestion_acceptance_20260606.md).
  It includes strict data ingestion into merged scenario zones only; runtime
  setup application remains held.
- G0-M metadata-only derived products are now accepted:
  [environment_substrate_g0_derived_products_acceptance_20260606.md](environment_substrate_g0_derived_products_acceptance_20260606.md).
  They include `surface_zone_index` and `occlusion_candidate_index` contract
  products only.
- G0 is closed by
  [environment_substrate_g0_closure_acceptance_20260606.md](environment_substrate_g0_closure_acceptance_20260606.md).
  Runtime setup application, runtime consumers, weather simulation,
  hydrodynamics, hydrology effects, dynamic environment mutation, movement, LOS,
  cover, fires, damage, and combat remain behind later gates.
