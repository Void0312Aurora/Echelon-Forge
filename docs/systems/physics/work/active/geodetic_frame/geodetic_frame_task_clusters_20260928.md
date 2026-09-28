# Geodetic Frame Task Clusters

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/systems/physics/work/active/geodetic_frame/geodetic_frame_task_clusters_20260928.md`
Owner: `systems/physics`
Last verified: `2026-09-28`

Status: `2026-09-28` finite task-cluster plan for [Geodetic Frame](README.md).
`P0-A` accepted `2026-09-28`; `P1-A` accepted `2026-09-28` ([inventory](geodetic_frame_p1a_inventory_20260928.md)).

## Boundary Decision

This package owns the earth model, the local-to-geodetic frame relation, and the
shared curvature geometry queries. It does not own any domain's use of them,
motion integration, terrain, or refraction beyond the standard effective-radius
factor. Every cluster that changes a shared runtime surface runs serially.

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A` | main thread | n/a | Freeze scope, earth-model choice, frame contract. | this directory; `docs/systems/README*` index | code | doc link and bilingual audits | owner approves | first | 1 | accepted |
| `P1-A` | read-only worker | n/a | Inventory flat-frame and horizon assumptions across `src/`, `python/`, `gym_envs/`. | inventory note in this directory | code changes | cited file/line evidence | every site classified | after `P0-A` | 1 + 1 repair | accepted |
| `P2-A` | future worker | n/a | Earth model plus scenario geodetic anchor; ENU-geodetic conversions both ways. | new frame component/header; scenario loader anchor field; tests | motion changes | native tests against reference coordinates | round-trip error within declared bound | after `P1-A`; serial | 2 + 1 repair | planned |
| `P2-B` | future worker | n/a | Geometry queries: horizon distance (geometric and effective-radius), earth-bulge LOS, great-circle range/bearing. | frame query API; tests | ducting | reference-value tests with sources | all queries match references | after `P2-A` | 2 + 1 repair | planned |
| `P3-A` | future worker | n/a | Move the sensing radar-horizon proxy and LOS onto the shared queries. | `default_sensor_model.cpp`, `sensor.h`; sensing tests | new sensor physics | sensing and naval sensor tests | proxy flag retired or wrapped; no direct horizon math left | after `P2-B`; serial | 2 + 1 repair | planned |
| `P3-B` | future worker | n/a | Expose the anchor and earth model through scenarios, bindings, and replay. | scenario schema; Python bindings; replay metadata | viz redesign | scenario contract tests | scenarios declare an anchor or inherit a documented default | after `P2-A`; parallel with `P3-A` | 2 | planned |
| `P4-A` | main thread | n/a | Cross-domain regression plus throughput delta. | validation record | fixing domain behavior | air, ground, naval suites; throughput run | every changed result explained | after `P3-A..B` | 1 + 1 repair | planned |
| `P5-A` | main thread | n/a | Acceptance record; promote frame contract to a physics standard. | this directory; physics standards; indexes | late implementation | doc audits | acceptance complete | after `P4-A` | 1 | planned |

## Dispatch Rules

- One packet maps to one cluster.
- `P2-A`, `P2-B`, `P3-A` change shared runtime surfaces and run serially.
- Domain behavior changes found during `P4-A` are routed to the domain owner, not
  fixed here.
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
python -m pytest -q tests/runtime tests/architecture/composition
```

## Acceptance Criteria

- Reference-value tests pass for conversions and queries.
- Must-migrate consumers use the shared queries.
- Cross-domain regressions pass or are explained.

## Residual Map

Immediate:

- `P0-A` owner review.

Follow-on:

- WGS-84 ellipsoidal geometry;
- geoid and terrain elevation, with `systems/environment`.

Deferred:

- geodetic motion state.
