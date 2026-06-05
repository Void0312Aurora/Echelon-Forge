# Environment Substrate G0 Closure Acceptance

Status: `2026-06-06` accepted complete G0 closure for the shared environment
substrate design-and-implementation line.

## Closure Decision

G0 is closed as a shared environment-substrate contract baseline. The accepted
line now covers:

- G0-A architecture/design records for branch-aware, component-based
  environment manifests;
- G0-J static manifest contract, default registries, validators, deterministic
  fixture, and projection contract tests;
- G0-K generator/catalog request, tile, seed, provenance, catalog admission, and
  deterministic in-memory generated manifest fixture;
- G0-L projection setup payload plus strict scenario compiler ingestion of
  inert payloads into merged `environment.zones`;
- G0-M first metadata-only derived-product indexes.

This closure has no remaining G0-internal held slice. The remaining held items
are downstream release gates, not incomplete G0 work.

## Explicit Non-Release Boundary

Still not released by G0:

- runtime setup application;
- scenario-producing terrain generator plugins or checked-in generated terrain
  artifacts;
- road graph, movement-cost grid, passability mask, runtime LOS occlusion,
  cover/concealment runtime products, tactical-area runtime graph;
- route following, speed updates, terrain-aware movement, sensing, fires,
  damage, combat, suppression, reward/termination binding, observation/export;
- weather simulation, hydrodynamics, hydrology effects, or dynamic environment
  mutation.

## Evidence

| Slice | Evidence | Result |
| --- | --- | --- |
| Architecture/design | [architecture plan](environment_substrate_g0_architecture_plan_20260605.md), [terrain system architecture](environment_substrate_g0_terrain_system_architecture_20260605.md) | accepted |
| G0-J static manifest | [static manifest acceptance](environment_substrate_g0_static_manifest_contract_acceptance_20260605.md) | accepted |
| G0-K generator/catalog | [generator/catalog acceptance](environment_substrate_g0_generator_catalog_acceptance_20260606.md) | accepted |
| G0-L setup payload | [projection setup acceptance](environment_substrate_g0_projection_setup_acceptance_20260606.md) | accepted |
| G0-L-F scenario ingestion | [scenario ingestion acceptance](environment_substrate_g0_scenario_ingestion_acceptance_20260606.md) | accepted |
| G0-M derived products | [derived products acceptance](environment_substrate_g0_derived_products_acceptance_20260606.md) | accepted |

## Validation

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_manifest.py tests/scenario/test_environment_substrate_projection.py tests/scenario/test_environment_substrate_generator_catalog.py tests/scenario/test_environment_substrate_projection_setup.py tests/scenario/test_environment_substrate_scenario_ingestion.py tests/scenario/test_environment_substrate_derived_products.py tests/scenario/test_scenario_compiler.py
# 59 passed
```

Documentation validation for closure:

```bash
git diff --check -- docs/task/ground/environment_substrate_g0_architecture docs/task/ground/README.md docs/task/ground/README.zh.md docs/task/ground/ground_current_progress_20260524.md docs/task/ground/ground_current_progress_20260524.zh.md docs/task/ground/ground_subagent_dispatch_queue_20260521.md docs/task/ground/ground_subagent_dispatch_queue_20260521.zh.md python/scenario/environment_substrate python/scenario/compiler tests/scenario
# clean
```

## Next Work Posture

Future work should open separate release packages rather than extending G0:

- runtime setup application;
- runtime consumers for derived products;
- route movement and terrain-aware movement gates;
- LOS/cover/fires/damage/combat gates;
- large-area environment generation and generated scenario artifacts.
