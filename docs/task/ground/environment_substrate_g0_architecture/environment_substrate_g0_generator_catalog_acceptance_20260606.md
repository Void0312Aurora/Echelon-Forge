# Environment Substrate G0-K Generator Catalog Acceptance

Status: `2026-06-06` accepted G0-K generator/catalog contract substage. This
acceptance covers Python-side deterministic request, tile, seed, catalog
admission, and in-memory generated manifest fixture behavior only.

## Accepted Scope

Accepted:

- `EnvironmentGeneratorRequest`, `EnvironmentGeneratorEvidenceRef`, and
  `EnvironmentTileScheme` request/tile contract data;
- canonical environment metadata serialization for deterministic seed material;
- deterministic seed derivation scoped by request metadata, stage, tile,
  catalog, and local key;
- default environment catalog descriptors for terrain and non-terrain
  environment branches;
- fail-closed catalog descriptor and catalog admission validation;
- deterministic in-memory generated `EnvironmentManifest` fixture output;
- focused tests under `tests/scenario/test_environment_substrate_generator_catalog.py`;
- documentation integration of returned G0-K-A/B/C worker packets.

Not accepted:

- scenario compiler/runtime projection integration;
- checked-in generated scenario/environment data artifacts;
- C++ terrain or environment runtime ownership;
- derived products such as road graphs, movement-cost grids, passability masks,
  LOS indexes, cover indexes, or tactical-area graphs;
- movement, passability, route following, LOS, cover, fires, damage, combat,
  weather simulation, hydrodynamics, hydrology effects, or dynamic environment
  mutation.

## Evidence Matrix

| Requirement | Evidence | Result |
| --- | --- | --- |
| G0-K-A/B/C worker packets are integrated. | [cluster plan](environment_substrate_g0_generator_catalog_cluster_20260605.md) | pass |
| Request, tile, seed, and provenance contract validates and fails closed. | [generator.py](../../../../python/scenario/environment_substrate/generator.py), generator/catalog tests | pass |
| Catalog descriptors are recipes, not feature-label schema roots. | [catalog.py](../../../../python/scenario/environment_substrate/catalog.py), generator/catalog tests | pass |
| Catalog admission rejects unknown refs, branch mismatch, missing components, and unsupported roots. | [catalog.py](../../../../python/scenario/environment_substrate/catalog.py), generator/catalog tests | pass |
| Generated fixture is deterministic and in-memory only. | [test_environment_substrate_generator_catalog.py](../../../../tests/scenario/test_environment_substrate_generator_catalog.py) | pass |
| G0-J static manifest regressions still pass. | manifest/projection tests | pass |
| No runtime behavior is released. | G0-K scope and residual boundary | pass |

## Validation

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_manifest.py tests/scenario/test_environment_substrate_projection.py tests/scenario/test_environment_substrate_generator_catalog.py
# 22 passed
```

## Acceptance Decision

Accepted as G0-K generator/catalog contract. The accepted implementation adds
only shared Python contract surfaces under `python/scenario/environment_substrate/`
and focused tests under `tests/scenario/`. It can be used as the evidence base
for a later G0-L projection preflight, but it does not itself project into
runtime setup or scenario compiler outputs.

## Residual Boundary

- The historical G0-K residual for G0-L is superseded by accepted G0-L
  projection setup plus compiler data ingestion; runtime setup application
  remains held.
- The historical G0-K residual for G0-M is superseded by accepted metadata-only
  derived products; runtime consumers remain held.
- Ground route movement remains under the separate G6-D3/G6-F release path.
- Movement, LOS, cover, fires, damage, combat, weather simulation,
  hydrodynamics, hydrology effects, and dynamic environment mutation remain
  held for every domain.
