# Environment Runtime Task Clusters

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/systems/environment/work/active/environment_runtime/environment_runtime_task_clusters_20260928.md`
Owner: `systems/environment`
Last verified: `2026-09-28`

Status: `2026-09-28` finite task-cluster plan for
[Environment Runtime](README.md). `P0-A` accepted `2026-09-28`.

## Boundary Decision

This package owns the layered runtime environment state, its vertical datum,
tile model, water-body contract, declared variation, clock-driven sun, ocean
acoustic environment data, and the domain-neutral query interface. It does not
own any consumer's physics or decisions. Consumer migrations change another
owner's files only to replace an environment read with a shared query; moving
Ground logic back to Ground is the one planned exception, and it relocates
existing Ground behavior without changing it.

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A` | main thread | main thread / session model / high | Freeze scope and the layered runtime contract. | this directory; environment owner and systems indexes | code | doc link and bilingual audits | owner approves | first | 1 | accepted |
| `P1-A` | read-only worker | n/a | Inventory every environment read on `main` and its ad hoc mapping. | inventory note in this directory | code | cited file/line evidence | every read classified | after `P0-A` | 1 + 1 repair | planned |
| `P1-B` | read-only worker | n/a | Classify each Ground-branch addition to the shared files as shared, Ground-owned, or retired. | inventory note in this directory | code | cited commit/file/line evidence from `origin/work/army-mechanisms` | every addition classified | after `P0-A`; parallel with `P1-A` | 1 + 1 repair | planned |
| `P2-A` | main thread | n/a | Contract: layer set, vertical datum, tile and resolution model, water-body contract, out-of-tile behavior, domain-neutral query API. | contract doc in this directory; interface header draft | implementation | contract review; header compiles | owner approves the contract | after `P1-A..B` | 1 + 1 repair | planned |
| `P3-A` | future worker | n/a | Multi-tile, multi-layer raster with vertical datum; elevation, bathymetry, landcover queries. | `src/core/interfaces/environment_model.h`, `src/models/environment/`; tests | Ground passability | native raster/tile tests | land tile and ocean grid query together on one datum | after `P2-A`; serial | 2 + 1 repair | planned |
| `P3-B` | future worker | n/a | Water bodies (sea and freshwater) and coastline queries. | environment model; substrate projection; tests | fording, navigation decisions | water-body and coastline tests | query distinguishes sea, river, lake with declared attributes | after `P3-A` | 2 + 1 repair | planned |
| `P3-C` | future worker | n/a | Declared time/space variation of weather, wind, sea state (wind sea and swell); visibility and precipitation attenuation. | environment model; tests | forecasting | seed-determinism tests | variation reproducible under seed | after `P3-A`; parallel with `P3-B` | 2 + 1 repair | planned |
| `P3-D` | future worker | n/a | Clock-driven sun from date, time, and geodetic anchor. | environment model; tests | lunar illumination | published solar-geometry references | reference values match | after `P3-A` and Geodetic Frame `P2-A` | 2 | planned |
| `P3-E` | future worker | n/a | Ocean acoustic environment data slots: sound-speed or temperature/salinity/depth inputs, layer depth, bottom class, ambient noise. | environment model; data contract; tests | propagation physics | contract tests | data queryable by position and depth | after `P3-A`; parallel | 2 | planned |
| `P4-A` | future worker | n/a | Migrate Ground native terrain loading onto `P3-A..B`; move `GroundStance`-dependent effects, passability, transition cost, and field-semantic observations into Ground; remove Ground includes and methods from shared files. | shared environment files; `src/systems/domains/ground/`, `src/models/domains/ground/`; kernel and binding seams | changing Ground behavior | Ground native-terrain acceptance tests; include-direction gate | shared files include no domain header; Ground tests green | after `P3-B`; serial | 2 + 1 repair | planned |
| `P4-B` | future worker | n/a | Move remaining consumers (ship motion sea state, maritime radar adapter, optical sensing) onto the queries. | consumer read sites only | consumer behavior changes | consumer suites | no ad hoc reads remain in migrated consumers | after `P3-C..D`; serial per owner | 2 + 1 repair | planned |
| `P4-C` | future worker | n/a | Scenario schema for layered environment, tiles, datum, and variation; substrate/compiler validation; replay metadata including rasters. | `python/scenario/`; substrate validators; replay; tests | viz redesign | scenario contract tests | scenarios declare or inherit a documented default; replay captures the environment | after `P3-A`; parallel with `P4-A` | 2 | planned |
| `P5-A` | main thread | n/a | Cross-domain regression and throughput delta. | validation record | fixing consumer behavior | air, ground, naval suites; throughput run | every changed result explained | after `P4-A..C` | 1 + 1 repair | planned |
| `P6-A` | main thread | n/a | Acceptance; promote the runtime contract to an environment standard; sync indexes. | this directory; environment standards; indexes | late implementation | doc audits | acceptance complete | after `P5-A` | 1 | planned |

## Dispatch Rules

- One packet maps to one cluster.
- `P3-A` and `P4-A` change shared runtime surfaces and run serially.
- `P4-A` works on this branch lineage; conflicts with
  `origin/work/army-mechanisms` are resolved at merge, not pre-empted by editing
  that branch.
- Follow the [Subagent Usage Policy](../../../../../engineering/automation/standards/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
cluster:
touched files:
commands/outcomes:
reference values and sources used:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

```bash
cmake --build build-independent-win --target ef_test ef_py
build-independent-win/ef_test.exe
python -m pytest -q tests/runtime tests/scenario tests/architecture/composition \
  tests/architecture/governance/test_cpp_include_direction.py
```

## Acceptance Criteria

- Shared environment files include no domain header.
- Migrated consumers read only through the shared queries.
- One vertical datum across land, water surface, and depth.
- Variation is deterministic under seed and replayable.

## Residual Map

Immediate:

- `P0-A` owner review.

Follow-on:

- ocean data line (importers and synthetic ocean generator), after `P2-A`;
- restoring the WIP-archived synthetic terrain generator and derivations.

Deferred:

- numerical weather, ocean, and river-flow models; live data ingestion.
