# Environment Substrate G0-K Generator Catalog

Status: `2026-06-06` accepted G0-K generator/catalog contract substage. This
record started as the `2026-06-05` preflight dispatch; it now records the
returned diagnostics, finite implementation slice, and acceptance boundary.

Language:

- English canonical:
  `environment_substrate_g0_generator_catalog_20260605.md`
- Chinese companion:
  [environment_substrate_g0_generator_catalog_20260605.zh.md](environment_substrate_g0_generator_catalog_20260605.zh.md)

Inputs:

- G0 package README: [README.md](README.md)
- G0 architecture plan:
  [environment_substrate_g0_architecture_plan_20260605.md](environment_substrate_g0_architecture_plan_20260605.md)
- G0 terrain-system architecture:
  [environment_substrate_g0_terrain_system_architecture_20260605.md](environment_substrate_g0_terrain_system_architecture_20260605.md)
- Accepted G0-J static contract:
  [environment_substrate_g0_static_manifest_contract_20260605.md](environment_substrate_g0_static_manifest_contract_20260605.md)
- G0-K acceptance:
  [environment_substrate_g0_generator_catalog_acceptance_20260606.md](environment_substrate_g0_generator_catalog_acceptance_20260606.md)
- Subagent usage policy:
  [../../../standards/governance/subagent_usage_policy.md](../../../standards/governance/subagent_usage_policy.md)

## Purpose

G0-K is the environment-substrate substage after G0-J. It turns the static
manifest contract into a deterministic generator/catalog contract without
claiming runtime behavior. The preflight workers returned `pass`, and the main
thread accepted a finite implementation: request/tile/seed/provenance data,
catalog descriptors/admission rules, and deterministic in-memory manifest
fixture generation.

The first useful generator target is not a bespoke ground schema. It is a
shared environment-substrate generator contract that can later create terrain,
buildings, vegetation, infrastructure, tactical areas, weather/wind/maritime
context, and hydrology objects as catalog-composed `EnvironmentObject` records.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| G0 architecture | accepted | [README.md](README.md) | Shared design only; no runtime release. |
| G0-J static contract | accepted | [G0-J acceptance](environment_substrate_g0_static_manifest_contract_acceptance_20260605.md) | Static manifest, validators, fixture, and contract projection tests only. |
| G0-K request/tile/seed contract | accepted | [generator.py](../../../../python/scenario/environment_substrate/generator.py), focused tests | Python contract only; no scenario compiler/runtime integration. |
| G0-K catalog admission rules | accepted | [catalog.py](../../../../python/scenario/environment_substrate/catalog.py), focused tests | Catalog labels remain recipes; no movement/LOS/cover/fires/damage/combat semantics. |
| G0-K deterministic fixture | accepted | [test_environment_substrate_generator_catalog.py](../../../../tests/scenario/test_environment_substrate_generator_catalog.py) | In-memory generated manifest only; no checked-in generated artifact. |
| Runtime projection and derived products | outside G0-K | G0 residual map and later closure records | G0-L/G0-M are accepted separately; runtime setup and consumers remain held. |

## Scope

Accepted in G0-K:

- define and validate deterministic generator request fields;
- define tile/extent/seed partitioning and provenance rules;
- define catalog descriptor and catalog admission rules;
- define deterministic fixture output expectations;
- add focused validation and determinism tests;
- keep terrain as the first detailed branch while preserving non-terrain
  branches under the same environment root.

Out of scope:

- scenario compiler/runtime integration;
- C++ runtime ownership;
- checked-in generated scenario/environment artifacts;
- derived products such as road graphs, movement-cost grids, passability masks,
  LOS indexes, cover indexes, or tactical-area graphs;
- movement, passability, LOS, cover, fires, damage, combat, weather simulation,
  hydrodynamics, hydrology effects, or mutable environment state;
- creating new conversation threads.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `G0-K-A Request/Tiling Preflight` | Define deterministic request, tile, seed, and provenance contract. | G0-J accepted. | Worker packet returns inspected files, required fields, and rejected shortcuts. | pass |
| `G0-K-B Catalog Admission Preflight` | Define generic catalog descriptors and admission rules. | G0-J accepted. | Worker packet maps road/building/vegetation/infrastructure/tactical/weather objects to components without schema hardcoding. | pass |
| `G0-K-C Determinism And Validator Preflight` | Define fixture and validation gates for implementation. | G0-J accepted. | Worker packet names focused tests and fail-closed rejection cases. | pass |
| `G0-K-D Integration Map` | Integrate worker packets into a finite implementation plan. | G0-K-A/B/C returned. | Main thread names bounded implementation write set and residuals. | pass |
| `G0-K-E Implementation` | Implement request/tile/catalog contracts and deterministic fixture. | Integrated preflight evidence. | Focused tests pass and runtime claims remain held. | pass |
| `G0-K-F Acceptance` | Record accepted scope and sync parent status. | Focused tests pass. | G0-K accepted only for Python contract and fixture generation. | accepted |

## Task Clusters

- Task cluster plan:
  [environment_substrate_g0_generator_catalog_cluster_20260605.md](environment_substrate_g0_generator_catalog_cluster_20260605.md)

## Outputs And Evidence

Accepted outputs:

- G0-K-A/B/C read-only worker packets integrated into the cluster plan;
- [catalog.py](../../../../python/scenario/environment_substrate/catalog.py);
- [generator.py](../../../../python/scenario/environment_substrate/generator.py);
- [package exports](../../../../python/scenario/environment_substrate/__init__.py);
- [focused generator/catalog tests](../../../../tests/scenario/test_environment_substrate_generator_catalog.py);
- [G0-K acceptance record](environment_substrate_g0_generator_catalog_acceptance_20260606.md).

## Acceptance Gate

G0-K is accepted because:

- G0-K-A/B/C all returned `pass` and were integrated;
- the implementation write set is finite and disjoint from runtime projection;
- deterministic seed/tile/catalog behavior has focused tests;
- validators reject omitted or mismatched request/catalog fields, unsupported
  schema roots, branch mismatches, and held runtime claims;
- parent G0 docs keep G0-K implementation separate from G0-L projection and
  G0-M derived products.

## Residuals And Next Steps

- G0-K is accepted only for Python request/tile/catalog contracts and
  deterministic in-memory fixture generation.
- The historical G0-K residual for G0-L is superseded by accepted G0-L
  projection setup plus compiler data ingestion; runtime setup application
  remains held.
- The historical G0-K residual for G0-M is superseded by accepted metadata-only
  derived products; runtime consumers remain held.
- Ground movement and combat remain governed by separate ground release gates.

## Archive

This is a current G0-K record. Superseded G0-K dispatch notes should move under
a future local `archive/` only after a maintained README/status or acceptance
surface points to the replacement.
