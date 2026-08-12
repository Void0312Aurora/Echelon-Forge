# Environment Substrate G0 Static Manifest Contract Acceptance

Status: `2026-06-05` accepted G0-J static manifest contract substage. This
acceptance covers Python-side shared environment substrate contracts and focused
tests only.

## Accepted Scope

Accepted:

- shared package namespace `python/scenario/environment_substrate/`;
- default branch, component, and layer registries;
- static `EnvironmentManifest` / `EnvironmentObject` data structures;
- deterministic static environment fixture;
- fail-closed manifest validation;
- contract-only `world_zone_definition` compatibility projection evidence;
- focused tests under `tests/scenario/`.

Not accepted:

- generator plugins;
- scenario compiler/runtime projection integration;
- C++ terrain/environment runtime ownership;
- movement, passability, route following, LOS, cover, fires, damage, combat,
  weather simulation, hydrodynamics, hydrology effects, or dynamic environment
  mutation.

## Evidence Matrix

| Requirement | Evidence | Result |
| --- | --- | --- |
| Shared namespace, not a ground-private package. | [package](../../../../../python/scenario/environment_substrate) | pass |
| Default registry includes terrain and non-terrain environment branches. | [components.py](../../../../../python/scenario/environment_substrate/components.py), manifest tests | pass |
| Static manifest serializes deterministically. | [test_environment_substrate_contracts.py](../../../../../tests/scenario/test_environment_substrate_contracts.py) | pass |
| Validators reject missing branch, missing component attributes, untyped behavior properties, and held capability claims. | [validation.py](../../../../../python/scenario/environment_substrate/validation.py), manifest tests | pass |
| Projection rejects unsupported rich features instead of silently defaulting. | [projection.py](../../../../../python/scenario/environment_substrate/projection.py), projection tests | pass |
| No runtime behavior is released. | G0-J scope and cluster boundary | pass |

## Validation

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py
# 10 passed
```

## Acceptance Decision

Accepted as G0-J static manifest contract. The next environment-substrate
substage should be G0-K generator/catalog work only after it defines
deterministic generator requests, tile/seed partitioning, catalog admission,
fixture output, and validation evidence without runtime release claims.

## Residual Boundary

The original G0-J residual for G0-K is superseded by the accepted
[G0-K generator/catalog contract](environment_substrate_g0_generator_catalog_20260605.md).
The original G0-J residual for G0-L/G0-M is superseded by accepted G0-L
projection setup plus compiler data ingestion and accepted G0-M metadata-only
derived products. Runtime setup application, runtime consumers, movement, LOS,
cover, fires, damage, combat, weather simulation, hydrodynamics, hydrology
effects, and dynamic environment mutation remain held.
