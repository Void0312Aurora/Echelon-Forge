# Environment Substrate G0-L-F Scenario Ingestion Acceptance

Status: `2026-06-06` accepted G0-L-F scenario compiler ingestion for inert
projection setup payloads. This closes the compiler-ingestion slice only; it
does not apply runtime setup or release terrain behavior.

## Accepted Scope

Accepted:

- `ingest_projection_setup_payloads_into_scenario()` under
  `python/scenario/environment_substrate/scenario_ingestion.py`;
- `ScenarioCompiler` ingestion hook after scenario import/merge and before
  merged-shape validation and runtime metadata compilation;
- namespaced input under
  `environment.environment_substrate.projection_setup_payloads`;
- conversion of already accepted G0-L projection setup payload zones into
  `environment.zones`;
- removal of consumed setup payloads from the scenario metadata namespace;
- preserved ingestion evidence under
  `environment.environment_substrate.projection_ingestion_evidence`;
- fail-closed rejection for contract mismatch, invalid surfaces, duplicate zone
  names, forbidden `world_index`, missing provenance, dropped rich attributes,
  and held runtime claims;
- focused tests under
  `tests/scenario/test_environment_projection_contracts.py`.

Not accepted:

- runtime setup application;
- C++ runtime edits, bindings, DTO changes, or new world-query ownership;
- generated scenario artifacts;
- movement, passability, route following, LOS, cover, fires, damage, combat,
  weather simulation, hydrodynamics, hydrology effects, or dynamic mutation.

## Evidence Matrix

| Requirement | Evidence | Result |
| --- | --- | --- |
| Compiler ingestion happens before layout metadata is compiled. | `ScenarioCompiler._compile_from_data()` plus ingestion test | pass |
| Payloads are strict and do not fall through to `SoftDirt` defaulting. | scenario ingestion invalid-surface test and layout surface assertion | pass |
| Ingestion is data-only and does not apply runtime setup. | ingestion evidence field `no_runtime_setup_application` | pass |
| Consumed payloads are removed and provenance evidence remains. | scenario ingestion test | pass |
| Runtime behavior and held capability claims remain refused. | rejection tests and G0 held-boundary docs | pass |

## Validation

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_projection_contracts.py
# 5 passed
```

Included in the G0 closure suite:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py tests/scenario/test_scenario_compiler.py
# 59 passed
```

## Acceptance Decision

Accepted as the final G0-L data-ingestion slice. The compiler may now ingest an
already accepted projection setup payload into the merged scenario data. The
runtime setup application gate remains outside G0 closure.
