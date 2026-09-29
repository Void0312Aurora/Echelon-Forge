# Geodetic Frame Task Clusters

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/systems/physics/work/active/geodetic_frame/geodetic_frame_task_clusters_20260928.md`
Owner: `systems/physics`
Last verified: `2026-09-28`

Status: `2026-09-28` finite task-cluster plan for [Geodetic Frame](README.md).
`P0-A` accepted `2026-09-28`; `P1-A` accepted `2026-09-28` ([inventory](geodetic_frame_p1a_inventory_20260928.md)); `P2-A`/`P2-B` accepted `2026-09-28`; `P3-A` accepted `2026-09-29`.

## Boundary Decision

This package owns the earth model, the local-to-geodetic frame relation, and the
shared curvature geometry queries. It does not own any domain's use of them,
motion integration, terrain, or refraction beyond the standard effective-radius
factor. Every cluster that changes a shared runtime surface runs serially.

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A` | main thread | main thread / session model / high | Freeze scope, earth-model choice, frame contract. | this directory; `docs/systems/README*` index | code | doc link and bilingual audits | owner approves | first | 1 | accepted |
| `P1-A` | read-only worker | low (read-only inventory) / ran on default; target sonnet / low | Inventory flat-frame and horizon assumptions across `src/`, `python/`, `gym_envs/`. | inventory note in this directory | code changes | cited file/line evidence | every site classified | after `P0-A` | 1 + 1 repair | accepted |
| `P2-A` | future worker | high (shared frame contract) / main thread / high | Earth model plus scenario geodetic anchor; ENU-geodetic conversions both ways. | new frame component/header; scenario loader anchor field; tests | motion changes | native tests against reference coordinates | round-trip error within declared bound | after `P1-A`; serial | 2 + 1 repair | accepted |
| `P2-B` | future worker | high (shared frame contract) / main thread / high | Geometry queries: horizon distance (geometric and effective-radius), earth-bulge LOS, great-circle range/bearing. | frame query API; tests | ducting | reference-value tests with sources | all queries match references | after `P2-A` | 2 + 1 repair | accepted |
| `P3-A` | main thread | high (shared sensing surface) / main thread / high; no independent review (change under the 2000-line large-iteration threshold) | Move the sensing radar-horizon proxy and LOS onto the shared queries. | `default_sensor_model.cpp`, `sensor.h`; sensing tests | new sensor physics | sensing and naval sensor tests | proxy flag retired or wrapped; no direct horizon math left | after `P2-B`; serial | 2 + 1 repair | accepted `2026-09-29` (`405b32fc`) |
| `P3-B` | future worker | moderate / sonnet / medium | Expose the anchor and earth model through scenarios, bindings, and replay. | scenario schema; Python bindings; replay metadata | viz redesign | scenario contract tests | scenarios declare an anchor or inherit a documented default | after `P2-A`; parallel with `P3-A` | 2 | planned |
| `P4-A` | main thread | high (cross-domain regression) / main thread / high | Cross-domain regression plus throughput delta. | validation record | fixing domain behavior | air, ground, naval suites; throughput run | every changed result explained | after `P3-A..B` | 1 + 1 repair | planned |
| `P5-A` | main thread | n/a | Acceptance record; promote frame contract to a physics standard. | this directory; physics standards; indexes | late implementation | doc audits | acceptance complete | after `P4-A` | 1 | planned |

## P3-A Record (`2026-09-29`)

Commits `9234ea86` (format-only) and `405b32fc` (migration) on
`work/naval-mechanisms`.

- Every sensor type except sonar is gated in `DefaultSensorModel::scan` by
  `within_smooth_earth_horizon`, which compares the local-frame horizontal
  separation against `geodesy::two_way_horizon_arc_m` plus the declared maritime
  ducting bonus. Radio sensors use the 4/3 factor; visual and infrared use the
  NGA Pub. No. 9 (Bowditch, Table 12) optical factor `1 / 0.8321`.
- `antenna_height_m` means the mount height above the platform reference point
  for every platform; the missile seeker mounts at 0 m. Ship targets use their
  radar-significant height, ESM targets the emitting antenna, other targets their
  own `z`.
- `enforce_radar_horizon` is retired from `Sensor`, the loader, the defaults, the
  database, and the tests. The data link and the experimental GPU comm probe use
  the same 4/3 arc; no `3570`/`3.57` horizon constant is left in `src/`.
- Validation: `ef_test` 189/189 on Linux gcc 13 and MSVC 14.44; HEI
  `pytest tests/runtime tests/architecture/composition` 953 passed and 1 failed,
  the same bootstrap import-plan cache failure as on the pre-change base; the
  include-direction gate passes.
- Measured behavior change with the real DDG-51 suite: ESM on a DDG emitter drops
  from 120 km to about 33 km, and surface radar tracks end near 60 km
  (SPY-1D 43.9 km horizon + 18 km ducting). Before the change, ESM also
  "tracked" a T-AKE-1 with no radar at 120 km.

Residuals for later clusters, not `P3-A` scope:

- `append_rwr_detection_from_radar` registers a warning within
  `1.5 · max_range` of the emitter's own scan and inherits the radar's horizon
  only when the radar detects the RWR carrier; an RWR-carrying target the radar
  does not see gets no warning. That is unchanged behavior, owned by sensing.
- Terrain line of sight (`IEnvironmentModel::check_line_of_sight`) still has no
  earth-bulge term; it belongs to [Environment Runtime](../../../../environment/work/active/environment_runtime/README.md) `P3-A`.
- EGI latitude/longitude still uses the hard-coded Nellis anchor; it moves with
  the scenario anchor in `P3-B`.
- `P4-A` cross-domain regression and throughput delta are still to run.

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
