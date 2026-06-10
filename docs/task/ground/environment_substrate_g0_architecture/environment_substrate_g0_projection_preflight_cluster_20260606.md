# Environment Substrate G0-L Projection Preflight Task Clusters

Status: `2026-06-06` accepted finite G0-L projection setup and compiler
ingestion task-cluster plan for
[environment_substrate_g0_projection_preflight_20260606.md](environment_substrate_g0_projection_preflight_20260606.md).

## Boundary Decision

G0-L may inspect projection integration paths, define gates, implement a
Python-only inert projection setup payload contract, and wire accepted payloads
into scenario compiler data ingestion. It may not apply world setup, edit C++
runtime, project generated manifests into checked-in scenarios, or claim
movement, LOS, cover, fires, damage, combat, weather simulation, hydrodynamics,
hydrology effects, dynamic mutation, or runtime derived-product consumers.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `G0-L-A Scenario Compiler Surface Preflight` | Huygens read-only diagnostics | inherited parent / xhigh | Inspect Python scenario compiler/setup surfaces and identify whether projected `world_zone_definition` payloads have a maintained ingestion path. | none; diagnostics packet only | No edits, no runtime setup application, no scenario files. | Worker packet cites inspected Python files and names accepted candidates or blockers. | Packet returned `pass`. | Parallel with G0-L-B/C; depends on accepted G0-K. | 1 | pass |
| `G0-L-B Runtime Setup Surface Preflight` | Pascal read-only diagnostics | inherited parent / xhigh | Inspect C++ batch/world setup contracts for `WorldZoneDefinition` compatibility and runtime side effects. | none; diagnostics packet only | No C++ edits, no new runtime terrain behavior, no derived products. | Worker packet cites inspected C++ files and names accepted candidates or blockers. | Packet returned `pass`. | Parallel with G0-L-A/C; depends on accepted G0-K. | 1 | pass |
| `G0-L-C Test And Validator Gate Preflight` | Carson read-only diagnostics | inherited parent / xhigh | Define focused tests, reason codes, and fail-closed gates needed before any G0-L implementation. | none; diagnostics packet only | No implementation, no projection integration. | Worker packet names tests, assertions, rejection reason codes, and held capability risks. | Packet returned `pass`. | Parallel with G0-L-A/B; depends on accepted G0-K. | 1 | pass |
| `G0-L-D Integration Decision` | main thread integration | n/a | Integrate A/B/C packets and decide whether a finite G0-L implementation write set can open. | G0 package docs plus parent ground README/progress/queue docs | No runtime application; no runtime claims. | Local packet review plus `git diff --check` for touched docs. | Finite Python-only projection setup payload write set accepted; compiler ingestion continues through G0-L-F. | Serial after G0-L-A/B/C return. | 1 | pass |
| `G0-L-E Projection Setup Payload Contract` | main thread implementation | n/a | Implement inert payload/evidence conversion for accepted `world_zone_definition` projections. | `python/scenario/environment_substrate/projection_setup.py`, package exports, focused tests | No scenario compiler ingestion, no runtime setup application, no C++ edits. | Focused pytest for deterministic payload, evidence preservation, strict surface codes, dropped attributes, and held claims. | Payload contract accepted only as Python setup evidence. | Depends on G0-L-D. | 1 | accepted |
| `G0-L-F Scenario Compiler Ingestion` | main-thread integration / implementation | n/a | Wire accepted projection setup payloads into scenario compiler data ingestion. | `python/scenario/environment_substrate/scenario_ingestion.py`, `python/scenario/environment_substrate/__init__.py`, `python/scenario/compiler/service.py`, `tests/scenario/test_environment_projection_contracts.py`, G0 package docs | No runtime setup application, no C++ edits, no generated scenario artifacts, no movement, LOS, cover, fires, damage, combat, or runtime derived-product consumers. | Focused ingestion pytest plus G0 closure suite. | Strict ingestion accepted, payloads fail closed, runtime setup remains held. | Depends on G0-L-E. | 1 | accepted |

## Worker Packet Requirements

Every worker must return:

```md
status: pass | partial | blocked | failed
touched files: none expected
files inspected:
commands/outcomes:
accepted projection candidates:
fail-closed blockers:
held capability risks:
integration notes:
```

G0-L-C may replace `accepted projection candidates` with `required tests` and
`fail-closed reason codes`.

## Validation Plan

Documentation validation for this dispatch:

```bash
git diff --check -- docs/task/ground/environment_substrate_g0_architecture docs/task/ground/README.md docs/task/ground/README.zh.md docs/task/ground/ground_current_progress_20260524.md docs/task/ground/ground_current_progress_20260524.zh.md docs/task/ground/ground_subagent_dispatch_queue_20260521.md docs/task/ground/ground_subagent_dispatch_queue_20260521.zh.md
```

Current G0-J/G0-K/G0-L/G0-M focused validation:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py tests/scenario/test_scenario_compiler.py
# 59 passed
```

## Acceptance Criteria

G0-L projection setup payload is accepted because:

- all three read-only packets returned `pass`;
- a finite Python-only write set is named and remains disjoint from derived products and
  movement/LOS/combat runtime behavior;
- accepted projection targets are limited to compatibility setup fields;
- compiler ingestion is strict data ingestion and runtime setup remains held;
- focused tests and fail-closed reason codes are implemented for the payload
  and ingestion contracts.

## Residual Map

- Runtime setup application remains held.
- G0-M metadata-only derived products are accepted separately.
- Ground movement/LOS/cover/fires/damage/combat remain held under separate
  release gates.
