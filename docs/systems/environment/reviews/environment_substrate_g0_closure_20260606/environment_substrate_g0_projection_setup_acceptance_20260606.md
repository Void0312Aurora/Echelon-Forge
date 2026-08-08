# Environment Substrate G0-L Projection Setup Acceptance

Status: `2026-06-06` accepted G0-L projection setup payload contract. This
acceptance covers Python-side conversion of an already validated
`world_zone_definition` projection result into an inert setup payload with
evidence. It does not apply runtime setup; scenario compiler ingestion is
accepted separately by the G0-L-F continuation.

## Accepted Scope

Accepted:

- read-only G0-L-A/B/C diagnostics packets returned `pass`;
- `build_world_zone_projection_setup_payload()` under
  `python/scenario/environment_substrate/projection_setup.py`;
- deterministic `EnvironmentProjectionSetupPayload` metadata;
- preservation of source manifest/object/catalog/component/profile/provenance
  evidence for every projected zone;
- strict surface-code admission for the current `WorldZoneDefinition`
  compatibility surface;
- fail-closed rejection for unknown profiles, invalid surface codes, dropped
  rich attributes, and held runtime claims;
- focused tests under
  `tests/scenario/test_environment_projection_contracts.py`.

Not accepted:

- runtime setup application;
- C++ runtime edits, bindings, DTO changes, or new world-query ownership;
- wind, maritime, hydrology, weather, illumination, dynamic environment, road,
  building, vegetation, LOS, cover, or derived-product projection;
- movement, passability, route following, fires, damage, combat, weather
  simulation, hydrodynamics, hydrology effects, or dynamic mutation.

## Evidence Matrix

| Requirement | Evidence | Result |
| --- | --- | --- |
| G0-L-A/B/C preflight packets returned pass. | [G0-L cluster](environment_substrate_g0_projection_preflight_cluster_20260606.md) | pass |
| Payload builder does not apply runtime setup. | [projection_setup.py](../../../../../python/scenario/environment_substrate/projection_setup.py) | pass |
| Payload preserves projection evidence and source IDs. | [projection setup tests](../../../../../tests/scenario/test_environment_projection_contracts.py) | pass |
| Surface mapping is strict and no implicit `SoftDirt` default is used. | projection setup tests | pass |
| Dropped rich attributes remain rejected for this slice. | projection setup tests | pass |
| Held runtime claims remain rejected. | projection setup tests | pass |

## Validation

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py
# 27 passed
```

## Acceptance Decision

Accepted as the first G0-L implementation slice: projection setup payload
contract only. The next G0-L continuation has been accepted separately as
strict scenario-compiler ingestion with a finite write set and focused tests.

## Residual Boundary

- Scenario compiler ingestion of projection payloads is accepted separately in
  [G0-L-F ingestion acceptance](environment_substrate_g0_scenario_ingestion_acceptance_20260606.md).
- Runtime setup application remains held.
- G0-M metadata-only derived products are accepted separately.
- Ground route movement remains governed by a separate G6-D3/G6-F release path.
- Movement, LOS, cover, fires, damage, combat, weather simulation,
  hydrodynamics, hydrology effects, and dynamic mutation remain held.
