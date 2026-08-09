# Environment Substrate G0 Acceptance

Status: `2026-06-05` accepted G0 design-and-implementation boundary for the
shared environment substrate, updated on `2026-06-06` through complete G0
closure. This acceptance now covers architecture/design records, G0-J static
manifest contract implementation, G0-K generator/catalog contracts, G0-L
projection setup plus strict scenario compiler ingestion, and G0-M
metadata-only derived products. It does not release runtime setup application,
movement, LOS, cover, fires, damage, combat, weather simulation,
hydrodynamics, hydrology effects, or dynamic environment mutation.

## Scope Accepted

G0 is accepted as the finite design-and-implementation line for a
component-based, branch-aware, shared environment substrate. The accepted root is
`EnvironmentManifest` / `EnvironmentObject`, with terrain as the first detailed
branch and atmosphere/weather, wind, illumination, maritime/ocean, hydrology, and
dynamic environment retained as merge targets under the same manifest root. The
accepted implementation substages are G0-J static manifests/validators, G0-K
generator/catalog contracts, G0-L projection setup and compiler data ingestion,
and G0-M metadata-only derived products.

## Criteria Review

| Criterion | Evidence | Result |
| --- | --- | --- |
| Component registry, layer semantics, branch registry, manifest shape, validators, projection plan, and consumer gates are named. | [architecture plan](environment_substrate_g0_architecture_plan_20260605.md) | pass |
| Current `src` terrain/query primitives are represented as shared primitives, not a full terrain runtime. | [source inventory](environment_substrate_g0_source_inventory_20260605.md) | pass |
| Terrain plan separates shared layered/tiled data from compatibility projection/query consumers. | [terrain system architecture](environment_substrate_g0_terrain_system_architecture_20260605.md) | pass |
| Current Ground owner, environment boundary, and closure index remain linked. | [Ground owner](../../../../domains/ground/README.md), [environment owner](../../../../systems/environment/README.md), [closure index](README.md) | pass |
| Branch-expansion diagnostics are integrated or rejected locally. | [subagent dispatch](environment_substrate_g0_subagent_dispatch_20260605.md), [task clusters](environment_substrate_g0_task_clusters_20260605.md) | pass |
| G0-J static manifest implementation is finite and tested. | [G0-J static contract](environment_substrate_g0_static_manifest_contract_20260605.md), [G0-J acceptance](environment_substrate_g0_static_manifest_contract_acceptance_20260605.md) | pass |
| G0-K generator/catalog contract is finite and tested. | [G0-K record](environment_substrate_g0_generator_catalog_20260605.md), [G0-K acceptance](environment_substrate_g0_generator_catalog_acceptance_20260606.md) | pass |
| G0-L projection setup plus scenario compiler ingestion is finite and tested. | [G0-L setup acceptance](environment_substrate_g0_projection_setup_acceptance_20260606.md), [G0-L-F ingestion acceptance](environment_substrate_g0_scenario_ingestion_acceptance_20260606.md) | pass |
| G0-M derived products are metadata-only and tested. | [G0-M acceptance](environment_substrate_g0_derived_products_acceptance_20260606.md) | pass |
| G0 closure leaves no internal held slice while preserving downstream held gates. | [G0 closure acceptance](environment_substrate_g0_closure_acceptance_20260606.md) | pass |
| No runtime setup application, movement, LOS, cover, fires, damage, or combat capability is claimed or released. | README scope, task clusters residual map, source inventory held boundaries | pass |

## Validation

Documentation validation:

```bash
git diff --check -- docs/systems/environment/reviews/environment_substrate_g0_closure_20260606 docs/domains/ground/README.md docs/domains/ground/README.zh.md docs/systems/environment/README.md docs/systems/environment/README.zh.md docs/systems/environment/reviews/environment_substrate_g0_closure_20260606/README.md docs/systems/environment/reviews/environment_substrate_g0_closure_20260606/README.zh.md
```

Code validation for the G0-J static contract implementation:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py
# 10 passed
```

Code validation for the G0-K generator/catalog continuation:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py
# 22 passed
```

Code validation for G0 closure:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py tests/scenario/test_scenario_compiler.py
# 59 passed
```

## Continuation Decision

G0 now includes the accepted G0-J static manifest contract lane, the accepted
G0-K generator/catalog contract lane, the accepted G0-L projection setup plus
compiler ingestion lane, and the accepted G0-M metadata-only derived-product
lane. The accepted write set remains shared `environment_substrate`
infrastructure under `python/scenario/environment_substrate/`, the strict
compiler data-ingestion hook in `python/scenario/compiler/service.py`, and
focused `tests/scenario/` contract tests. G0 is closed; future runtime work must
open a separate release package.

## Held Boundary

The following remain held after this acceptance as downstream gates, not as
incomplete G0 work:

- runtime or scenario-producing terrain generator plugins and large-area
  generation beyond the accepted G0-K in-memory fixture;
- runtime setup application and runtime consumers for metadata products;
- movement, passability, route following, LOS, cover, fires, damage, combat, and
  observation/export;
- weather simulation, hydrodynamics, hydrology effects, and dynamic environment
  mutation;
- any claim that wind or maritime setup values imply a domain behavior release.
