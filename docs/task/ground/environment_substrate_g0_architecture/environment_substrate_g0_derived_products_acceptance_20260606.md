# Environment Substrate G0-M Derived Products Acceptance

Status: `2026-06-06` accepted G0-M first derived-product contract slice for
metadata-only environment indexes. This does not release movement, LOS, cover,
or runtime consumers.

## Accepted Scope

Accepted:

- `EnvironmentDerivedProductRequest`, `EnvironmentDerivedProduct`,
  `EnvironmentDerivedProductBundle`, and `EnvironmentDerivedProductResult`
  under `python/scenario/environment_substrate/derived_products.py`;
- `build_environment_derived_products()` for validated `EnvironmentManifest`
  inputs;
- `surface_zone_index`, derived from the accepted `world_zone_definition`
  projection profile, with strict no-dropped-attribute evidence;
- `occlusion_candidate_index`, a metadata-only candidate index over
  `occlusion`, `structure`, and `vegetation` components;
- explicit bundle metadata that sets `no_runtime_consumer_release` and
  `no_held_capability_release`;
- fail-closed rejection for unknown products, held product kinds, held
  capability claims, missing request IDs, missing product kinds, and missing
  projection profile IDs for surface-zone indexes;
- focused tests under
  `tests/scenario/test_environment_substrate_contracts.py`.

Not accepted:

- road graph, movement-cost grid, passability mask, LOS occlusion index,
  cover/concealment index, or tactical-area graph;
- runtime consumers for the accepted metadata products;
- movement, passability, route following, LOS behavior, cover behavior, fires,
  damage, combat, weather simulation, hydrodynamics, hydrology effects, or
  dynamic mutation.

## Evidence Matrix

| Requirement | Evidence | Result |
| --- | --- | --- |
| Derived product requests are deterministic and metadata-only. | derived products deterministic bundle test | pass |
| Surface-zone index reuses accepted projection evidence. | `surface_zone_index` test | pass |
| Occlusion candidates are indexed without LOS/cover release. | `occlusion_candidate_index` test and evidence flags | pass |
| Held product kinds are rejected. | `passability_mask` rejection test | pass |
| Held capability claims are rejected. | `line_of_sight` rejection test | pass |
| Surface-zone index requires an explicit projection profile. | missing-profile rejection test | pass |

## Validation

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py
# 4 passed
```

Included in the G0 closure suite:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py tests/scenario/test_scenario_compiler.py
# 59 passed
```

## Acceptance Decision

Accepted as G0-M metadata/index contract closure. These products are contract
artifacts that future gates may consume after separate release votes; they do
not themselves enable movement, LOS, cover, fires, damage, or combat behavior.
