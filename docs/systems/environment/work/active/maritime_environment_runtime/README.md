# Maritime Environment Runtime

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/systems/environment/work/active/maritime_environment_runtime/README.md`
Owner: `systems/environment`
Last verified: `2026-09-28`

Status: `2026-09-28` planning. Scope and task clusters are drafted; `P0 Boundary`
is active and no implementation cluster has started.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- [Environment Systems](../../../README.md) — owner README; its G0/G1 boundary
  says a runtime package must open here with its own scope
- [Cross-Domain Systems](../../../../README.md)
- [Gradient Realism Principles](../../../../standards/gradient_realism_principles.md)
- [Geodetic Frame](../../../../physics/work/active/geodetic_frame/README.md) — sibling package
- [Carrier Strike Group Engagement](../../../../../domains/naval/work/active/carrier_strike_group_engagement/README.md)
  — first demand case
- [Subproject Creation Standard](../../../../../engineering/automation/rules/subproject_creation_standard.md)
- Code: `src/core/interfaces/environment_model.h`, `src/models/environment/`,
  `python/scenario/runtime/kernel_apply.py`

## Purpose

The environment model already carries wind, a sun direction, and a maritime state
(sea state, wave heading, wave period), all set once from the scenario and held
constant. Consumers read them ad hoc: ship motion scales speed by sea state,
surface radar applies sea clutter, and optical sensing uses the sun elevation.

Scenarios that last hours and span hundreds of kilometres need that state to be
a runtime authority. It must vary in time and space, be derived consistently from
one declared source, and be read by every domain through one interface. That
includes flight-deck operations and aircraft recovery limits, surface and
undersea sensing, and ship motion. This package makes the maritime and
atmospheric environment that runtime authority. It is cross-domain
infrastructure; the naval carrier group program is the first demand case, and
Air and Ground consume the same state.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Wind | scenario constant with a shear term | `set_wind` (`environment_model.h`); `default_environment_model.cpp` | uniform in space, constant in time |
| Sun / illumination | scenario constant azimuth and elevation | `set_sun_direction`; `default_sensor_model.cpp` optical factor | no clock-driven day/night |
| Maritime state | scenario constant | `set_maritime_state` / `get_maritime_state` | one sea state for the whole world; no swell/wind-sea split |
| Consumers | ad hoc | `ship_motion_system.h` sea-state scale; maritime radar adapter | each consumer applies its own mapping |
| Ocean acoustics | absent | none | no sound-speed profile, layer depth, or ambient-noise field |
| Runtime environment authority | not authorized before this package | [owner README G0/G1 boundary](../../../README.md) | this package opens it for the maritime and atmospheric state only |

## Scope

In scope:

- a runtime environment state with declared time and space variation: wind,
  sea state split into wind sea and swell, visibility and precipitation
  attenuation, and a clock-driven sun position that gives day and night from the
  scenario date, time, and geodetic anchor;
- an ocean acoustic environment as data: sound-speed profile, mixed-layer depth,
  bottom depth class, and ambient noise from sea state and shipping. Propagation
  physics that uses it belongs to the undersea sensing consumer, not here;
- one query interface that every domain reads, with the existing ad hoc
  consumers moved onto it;
- scenario schema for declaring the environment and its variation, validated by
  the existing substrate and compiler routes.

Out of scope:

- weather forecasting, numerical ocean or atmosphere models, and coupled
  air-sea dynamics;
- terrain passability, cover, and ground line of sight, which remain on their
  existing lines;
- any consumer's physics: ship seakeeping, aircraft recovery limits, sonar
  propagation, and radar clutter models belong to their owners;
- live real-world data ingestion.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze scope and the environment-state contract. | owner approval | README and task clusters approved | active |
| `P1 Evidence` | Inventory every environment read and ad hoc mapping. | `P0` | each consumer classified | planned |
| `P2 Implementation` | Runtime state with time/space variation; clock-driven sun; acoustic environment data. | `P1`, geodetic anchor from [Geodetic Frame](../../../../physics/work/active/geodetic_frame/README.md) `P2-A` for sun position | tests against declared inputs and published solar geometry | planned |
| `P3 Integration` | Move consumers onto the query interface; scenario schema. | `P2` | no ad hoc environment reads remain in migrated consumers | planned |
| `P4 Validation` | Cross-domain regression and throughput check. | `P3` | air, ground, naval suites pass or change by documented amounts | planned |
| `P5 Closure` | Acceptance and indexes. | `P4` | acceptance record; contract promoted to an environment standard | planned |

## Task Clusters

- [maritime_environment_runtime_task_clusters_20260928.md](maritime_environment_runtime_task_clusters_20260928.md)

## Outputs And Evidence

- runtime environment state and query interface;
- scenario schema for environment declaration and variation;
- clock-driven solar geometry with reference tests;
- ocean acoustic environment data contract;
- cross-domain regression record and throughput delta;
- an environment standard for the runtime contract.

## Acceptance Gate

This package can be marked accepted only when:

- every migrated consumer reads the environment through the one query interface;
- solar geometry matches published reference values for test dates and places;
- time and space variation is declared by the scenario, deterministic under a
  seed, and reproducible in replay;
- air, ground, and naval regression suites pass, or each changed result is
  explained and recorded;
- no consumer physics is added inside this package.

## Residuals And Next Steps

- `P0` owner review.
- Clock-driven sun position depends on the geodetic anchor; until it lands, the
  existing scenario sun declaration stays authoritative.

## Archive

Accepted records move to `docs/systems/environment/reviews/`; the runtime
contract is promoted to an environment standard.
