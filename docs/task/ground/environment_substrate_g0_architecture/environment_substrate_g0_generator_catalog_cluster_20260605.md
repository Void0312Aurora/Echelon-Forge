# Environment Substrate G0-K Generator Catalog Task Clusters

Status: `2026-06-06` accepted finite G0-K task-cluster plan for
[environment_substrate_g0_generator_catalog_20260605.md](environment_substrate_g0_generator_catalog_20260605.md).

## Boundary Decision

G0-K may define and implement generator request contracts, tile/seed
partitioning, catalog admission, deterministic fixture output, and validation
gates inside the shared Python environment-substrate package. It must not
integrate runtime projection, edit C++ runtime, add scenarios, or claim
movement, LOS, cover, fires, damage, combat, weather simulation, hydrodynamics,
hydrology effects, or dynamic environment mutation.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `G0-K-A Request/Tiling Preflight` | Huygens read-only diagnostics | inherited parent / xhigh | Inspect generator/compiler surfaces and define deterministic request, tile, seed, and provenance contract requirements. | none; diagnostics packet only | No edits, no generator code, no scenario/runtime integration, no derived products. | Worker packet cites inspected files and lists request fields, seed/tile rules, provenance, rejected shortcuts, and implementation blockers. | Packet returned `pass`. | Parallel with G0-K-B/C; depends on accepted G0-J. | 1 | pass |
| `G0-K-B Catalog Admission Preflight` | Pascal read-only diagnostics | inherited parent / xhigh | Define generic catalog descriptor/admission rules for terrain, buildings, vegetation, infrastructure, tactical areas, atmosphere/weather, wind, maritime, and hydrology objects. | none; diagnostics packet only | No schema hardcoding for road/forest/building/village; no runtime claims; no edits. | Worker packet maps catalog examples to branch/component/layer requirements and fail-closed admission rules. | Packet returned `pass`. | Parallel with G0-K-A/C; depends on accepted G0-J. | 1 | pass |
| `G0-K-C Determinism And Validator Preflight` | Carson read-only diagnostics | inherited parent / xhigh | Define focused tests, fixture determinism gates, and validator failures needed before implementation. | none; diagnostics packet only | No implementation, no runtime projection, no generated fixture checked in unless a later implementation cluster accepts it. | Worker packet names test files, assertions, validation reason codes, and unstable randomness/provenance failure cases. | Packet returned `pass`. | Parallel with G0-K-A/B; depends on accepted G0-J. | 1 | pass |
| `G0-K-D Integration Map` | main thread integration | n/a | Integrate A/B/C packets into a finite G0-K implementation plan. | `docs/task/ground/environment_substrate_g0_architecture/*.md`, parent ground README/progress/queue docs | No runtime projection, no C++ runtime, no scenarios, no derived products. | Local review of packets plus `git diff --check` for touched docs. | Implementation write set named and residuals preserved. | Serial after G0-K-A/B/C return. | 1 | pass |
| `G0-K-E1 Request And Tile Contract` | main thread implementation | n/a | Implement deterministic generator request, evidence refs, tile scheme, canonical bytes, and seed derivation. | `python/scenario/environment_substrate/generator.py`, `python/scenario/environment_substrate/__init__.py`, focused tests | No scenario compiler reuse, no runtime projection, no ambient randomness. | Focused pytest for request validation and deterministic output. | Request/tile contract validates and fails closed with stable reason codes. | Depends on G0-K-D. | 1 | pass |
| `G0-K-E2 Catalog Admission Contract` | main thread implementation | n/a | Implement catalog descriptors, catalog admission validation, and default descriptor fixtures. | `python/scenario/environment_substrate/catalog.py`, `python/scenario/environment_substrate/__init__.py`, focused tests | No feature-label schema roots, no behavior claims from labels. | Focused pytest for catalog refs, required components, branch/layer mismatch, and held claims. | Catalog admission rejects invalid descriptors and generated manifests with stable reason codes. | Parallel-safe with E1 only by file, integrated serially in tests. | 1 | pass |
| `G0-K-E3 Deterministic Manifest Fixture` | main thread implementation | n/a | Build a deterministic in-memory generated manifest fixture from request + catalog descriptors. | `python/scenario/environment_substrate/generator.py`, `tests/scenario/test_environment_substrate_contracts.py` | No checked-in generated data artifact, no runtime setup payload. | Focused pytest plus existing G0-J regressions. | Same request yields byte-identical manifest metadata; different seed changes generated output while preserving lineage. | Depends on E1/E2. | 1 | pass |
| `G0-K-F Documentation And Acceptance` | main thread integration | n/a | Record G0-K implementation acceptance and sync parent status. | G0 package docs plus parent ground README/progress/queue docs | No archive unless a maintained replacement exists. | Focused pytest and `git diff --check`. | G0-K accepted only for Python generator/catalog contract; historical G0-L/G0-M residuals are superseded by G0 closure. | Serial after E1/E2/E3 validation. | 1 | accepted |

## Dispatch Rules

- Reuse existing agents only; do not create new conversation threads.
- Every worker packet must map to exactly one G0-K-A/B/C cluster.
- Diagnostics workers are read-only and must not edit, stage, commit, or
  reformat files.
- Implementation write set is limited to
  `python/scenario/environment_substrate/catalog.py`,
  `python/scenario/environment_substrate/generator.py`,
  `python/scenario/environment_substrate/__init__.py`,
  `tests/scenario/test_environment_substrate_contracts.py`, and status
  docs.
- Do not split the same normative table across workers.
- Keep generator/catalog contracts separate from G0-L runtime projection and
  G0-M derived products.
- Treat current `WorldZoneDefinition` projection as compatibility evidence only.
- Preserve G0-J as accepted static contract input; do not rename it back to G1.

## Worker Packet Requirements

Every worker must return:

```md
status: pass | partial | blocked | failed
touched files: none expected
files inspected:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

The packet must also list rejected alternatives and explicit held capability
claims.

## Validation Plan

Documentation validation for this dispatch:

```bash
git diff --check -- docs/task/ground/environment_substrate_g0_architecture docs/task/ground/README.md docs/task/ground/README.zh.md docs/task/ground/ground_current_progress_20260524.md docs/task/ground/ground_current_progress_20260524.zh.md docs/task/ground/ground_subagent_dispatch_queue_20260521.md docs/task/ground/ground_subagent_dispatch_queue_20260521.zh.md
```

Current G0-K focused validation plus G0-J contract regression:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py
# 22 passed
```

## Acceptance Criteria

G0-K implementation is accepted only because:

- G0-K-A/B/C packet requirements are integrated;
- request/tile/seed/provenance contract validates and fails closed;
- catalog descriptor/admission rules reject feature-label schema roots;
- generated fixture output is deterministic and in-memory only;
- implementation write scope remains finite and separate from runtime projection;
- all movement, LOS, cover, fires, damage, combat, weather simulation,
  hydrodynamics, hydrology effects, and dynamic mutation claims remain held.

## Residual Map

- G0-K accepted implementation is limited to Python request/tile/catalog contracts and
  deterministic fixture generation.
- The historical G0-K residual for G0-L is superseded by accepted G0-L
  projection setup plus compiler data ingestion; runtime setup application
  remains held.
- The historical G0-K residual for G0-M is superseded by accepted metadata-only
  derived products; runtime consumers remain held.
- Ground route movement remains under the separate G6-D3/G6-F release path.
