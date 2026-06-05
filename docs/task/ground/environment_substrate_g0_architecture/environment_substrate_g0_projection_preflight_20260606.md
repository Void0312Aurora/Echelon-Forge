# Environment Substrate G0-L Projection Preflight

Status: `2026-06-06` G0-L preflight returned `pass`; projection setup payload
and strict scenario compiler ingestion are accepted. Runtime setup application
remains held.

Language:

- English canonical:
  `environment_substrate_g0_projection_preflight_20260606.md`
- Chinese companion:
  [environment_substrate_g0_projection_preflight_20260606.zh.md](environment_substrate_g0_projection_preflight_20260606.zh.md)

Inputs:

- G0 package README: [README.md](README.md)
- Accepted G0-J static contract:
  [environment_substrate_g0_static_manifest_contract_20260605.md](environment_substrate_g0_static_manifest_contract_20260605.md)
- Accepted G0-K generator/catalog contract:
  [environment_substrate_g0_generator_catalog_20260605.md](environment_substrate_g0_generator_catalog_20260605.md)
- Current projection contract:
  [projection.py](../../../../python/scenario/environment_substrate/projection.py)
- Accepted G0-L projection setup payload:
  [environment_substrate_g0_projection_setup_acceptance_20260606.md](environment_substrate_g0_projection_setup_acceptance_20260606.md)
- Accepted G0-L-F scenario compiler ingestion:
  [environment_substrate_g0_scenario_ingestion_acceptance_20260606.md](environment_substrate_g0_scenario_ingestion_acceptance_20260606.md)
- Scenario/runtime source inventory:
  [environment_substrate_g0_source_inventory_20260605.md](environment_substrate_g0_source_inventory_20260605.md)

## Purpose

G0-L is the next environment-substrate continuation after G0-K. Its job is to
move validated compatibility projection output toward current scenario/world
setup surfaces without pretending that terrain runtime behavior exists.

The only plausible first target is a lossy `world_zone_definition` projection
for rectangular, surface-only objects that already pass G0-J/G0-K validators.
The A/B/C preflight packets returned `pass`. The accepted G0-L line now covers
an inert projection setup payload contract and a strict compiler ingestion hook
that consumes accepted payloads into merged `environment.zones`. It still does
not apply runtime setup.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| G0-J projection contract | accepted | [projection.py](../../../../python/scenario/environment_substrate/projection.py), projection tests | Emits contract evidence; does not apply setup. |
| G0-K generated manifest fixture | accepted | [G0-K acceptance](environment_substrate_g0_generator_catalog_acceptance_20260606.md) | In-memory only; no checked-in generated artifacts. |
| Projection setup payload contract | accepted implementation slice | [G0-L setup acceptance](environment_substrate_g0_projection_setup_acceptance_20260606.md) | Python payload/evidence only; no setup application. |
| Scenario compiler ingestion | accepted implementation slice | [G0-L-F ingestion acceptance](environment_substrate_g0_scenario_ingestion_acceptance_20260606.md) | Strict data ingestion into merged scenario zones only; no runtime setup application. |
| Runtime setup application | held | this record | Needs separate release package. |
| C++ runtime behavior | held | G0 residual map | No new runtime terrain ownership or behavior. |
| Derived products | metadata-only G0-M accepted; runtime products held | [G0-M acceptance](environment_substrate_g0_derived_products_acceptance_20260606.md) | No road graph, movement-cost grid, passability mask, runtime LOS, or cover product. |

## Scope

In scope for G0-L preflight:

- inspect Python scenario compiler/setup ingestion paths for environment zones;
- inspect C++ world setup and batch setup contracts for `WorldZoneDefinition`;
- define the minimum projection request/evidence payload needed before
  implementation;
- define focused tests and reason codes for fail-closed projection integration;
- decide whether a finite G0-L implementation write set can be opened.

Out of scope:

- editing scenario compiler/runtime code before preflight packets return;
- C++ runtime edits or new world-query ownership;
- generated scenario files or checked-in generated environment artifacts;
- projection of non-rect geometry, buildings, vegetation, roads, hydrology
  effects, weather cells, wind/maritime behavior, dynamic state, or derived
  products into runtime behavior;
- movement, passability, route following, LOS, cover, fires, damage, combat, or
  observation/export.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `G0-L-A Scenario Compiler Surface Preflight` | Inspect Python scenario compiler/setup surfaces and identify whether projected world zones have a maintained ingestion path. | Accepted G0-K. | Packet returns accepted candidates, blockers, and held risks. | pass |
| `G0-L-B Runtime Setup Surface Preflight` | Inspect C++ batch/world setup contracts for `WorldZoneDefinition` compatibility and runtime side effects. | Accepted G0-K. | Packet returns accepted candidates, blockers, and held risks. | pass |
| `G0-L-C Test And Validator Gate Preflight` | Define focused tests, reason codes, and fail-closed gates required before G0-L implementation. | Accepted G0-K. | Packet returns required tests and reason codes. | pass |
| `G0-L-D Integration Decision` | Integrate A/B/C packets and decide whether implementation can open. | A/B/C returned. | Finite projection setup payload write set is accepted; compiler ingestion continues through G0-L-F; runtime application remains held. | pass |
| `G0-L-E Projection Setup Payload Contract` | Implement inert payload/evidence conversion for accepted world-zone projections. | G0-L-D pass. | Focused tests pass and no runtime setup is applied. | accepted |
| `G0-L-F Scenario Compiler Ingestion` | Wire accepted projection setup payloads into scenario compiler ingestion. | G0-L-E accepted plus closure continuation. | Strict compiler data ingestion accepted with focused tests; runtime setup application remains held. | accepted |

## Task Clusters

- Task cluster plan:
  [environment_substrate_g0_projection_preflight_cluster_20260606.md](environment_substrate_g0_projection_preflight_cluster_20260606.md)

## Dispatch Rules

- Reuse existing agents only; do not create new conversation threads.
- Diagnostics workers are read-only and must not edit, stage, commit, or
  reformat files.
- Every worker packet must map to exactly one G0-L-A/B/C cluster.
- Do not split the same normative table across workers.
- Do not implement projection integration until G0-L-D accepts a finite write
  set.
- Keep G0-L projection separate from G0-M derived products and separate ground
  route-move release votes.

## Acceptance Gate

G0-L projection is accepted through scenario compiler ingestion because:

- G0-L-A/B/C returned `pass`;
- the candidate projection target is limited to accepted compatibility setup
  fields, initially `world_zone_definition`;
- the accepted write set is finite and Python-only;
- projection evidence preserves source manifest/object/catalog/provenance IDs;
- fail-closed behavior is defined for unknown profiles, unsupported targets,
  non-rect geometry, dropped rich attributes, branch/catalog mismatch, and held
  runtime claims;
- scenario compiler ingestion is strict, namespaced, provenance-preserving, and
  fail-closed before layout metadata can default invalid surfaces;
- all movement, LOS, cover, fires, damage, combat, weather simulation,
  hydrodynamics, hydrology effects, dynamic mutation, and runtime
  derived-product consumer claims remain held.

## Residuals

- Runtime setup application remains held.
- G0-M metadata-only derived products are accepted separately.
- Ground route movement remains governed by a separate G6-D3/G6-F release path.
