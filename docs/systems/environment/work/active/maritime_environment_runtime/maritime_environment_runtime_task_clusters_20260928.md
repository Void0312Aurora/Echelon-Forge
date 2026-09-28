# Maritime Environment Runtime Task Clusters

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/systems/environment/work/active/maritime_environment_runtime/maritime_environment_runtime_task_clusters_20260928.md`
Owner: `systems/environment`
Last verified: `2026-09-28`

Status: `2026-09-28` finite task-cluster plan for
[Maritime Environment Runtime](README.md). No cluster has started.

## Boundary Decision

This package owns the runtime maritime and atmospheric environment state, its
declared variation, the clock-driven sun, the ocean acoustic environment as
data, and the single query interface. It does not own any consumer's physics.
Consumer migrations change another owner's files only to replace an ad hoc
environment read with the query; behavior changes go to that owner.

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A` | main thread | n/a | Freeze scope and the environment-state contract. | this directory; environment owner README index | code | doc link and bilingual audits | owner approves | first | 1 | active |
| `P1-A` | read-only worker | n/a | Inventory every wind, sun, maritime, and visibility read and its ad hoc mapping. | inventory note in this directory | code changes | cited file/line evidence | every consumer classified | after `P0-A` | 1 + 1 repair | planned |
| `P2-A` | future worker | n/a | Runtime state with declared time/space variation; wind sea and swell split; visibility and precipitation attenuation. | `src/core/interfaces/environment_model.h`, `src/models/environment/`; tests | forecasting | native tests against declared inputs; seed determinism | state reproducible under seed | after `P1-A`; serial | 2 + 1 repair | planned |
| `P2-B` | future worker | n/a | Clock-driven sun position from scenario date/time and geodetic anchor. | environment model; tests | lunar illumination | tests against published solar geometry | reference values match | after `P2-A` and Geodetic Frame `P2-A` | 2 | planned |
| `P2-C` | future worker | n/a | Ocean acoustic environment data: sound-speed profile, layer depth, bottom class, ambient noise. | environment model; data contract; tests | propagation physics | contract tests | data queryable by position and depth | after `P2-A`; parallel with `P2-B` | 2 | planned |
| `P3-A` | future worker | n/a | Move existing consumers onto the query interface. | consumer read sites only (ship motion, maritime radar adapter, optical sensing) | consumer behavior changes | consumer suites | no ad hoc reads in migrated consumers | after `P2-A`; serial per owner | 2 + 1 repair | planned |
| `P3-B` | future worker | n/a | Scenario schema for environment declaration and variation; substrate and compiler validation; replay metadata. | `python/scenario/runtime/`, compiler, substrate validators; tests | viz redesign | scenario contract tests | scenarios declare or inherit a documented default | after `P2-A`; parallel with `P3-A` | 2 | planned |
| `P4-A` | main thread | n/a | Cross-domain regression and throughput delta. | validation record | fixing consumer behavior | air, ground, naval suites; throughput run | every changed result explained | after `P3-A..B` | 1 + 1 repair | planned |
| `P5-A` | main thread | n/a | Acceptance; promote contract to an environment standard. | this directory; environment standards; indexes | late implementation | doc audits | acceptance complete | after `P4-A` | 1 | planned |

## Dispatch Rules

- One packet maps to one cluster.
- `P2-A` and `P3-A` change shared runtime surfaces and run serially.
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
python -m pytest -q tests/runtime tests/scenario tests/architecture/composition
```

## Acceptance Criteria

- Migrated consumers read only through the query interface.
- Solar geometry matches references.
- Variation is deterministic under seed and replayable.

## Residual Map

Immediate:

- `P0-A` owner review.

Follow-on:

- terrain-coupled environment (coastal effects), with the ground environment line.

Deferred:

- numerical weather and ocean models; live data ingestion.
