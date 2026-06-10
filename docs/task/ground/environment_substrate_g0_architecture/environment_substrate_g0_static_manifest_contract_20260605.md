# Environment Substrate G0 Static Manifest Contract

Status: `2026-06-05` accepted G0-J implementation substage for the shared
environment substrate. This is part of Environment Substrate G0, not a separate
G1 phase.

Language:

- English canonical:
  `environment_substrate_g0_static_manifest_contract_20260605.md`
- Chinese companion:
  [environment_substrate_g0_static_manifest_contract_20260605.zh.md](environment_substrate_g0_static_manifest_contract_20260605.zh.md)

Inputs:

- G0 package README: [README.md](README.md)
- G0 architecture plan:
  [environment_substrate_g0_architecture_plan_20260605.md](environment_substrate_g0_architecture_plan_20260605.md)
- G0 acceptance:
  [environment_substrate_g0_acceptance_20260605.md](environment_substrate_g0_acceptance_20260605.md)

## Purpose

`G0-J` turns the accepted G0 design into the smallest testable static contract.
It introduces a shared Python package for environment manifest data structures,
default branch/component/layer registries, fail-closed manifest validation, a
deterministic fixture, and a contract-level compatibility projection.

This substage intentionally stops before generator plugins, scenario compiler
integration, C++ runtime ownership, movement, LOS, cover, fires, damage, combat,
weather simulation, hydrodynamics, hydrology effects, and dynamic environment
mutation.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| G0 architecture | accepted | [G0 acceptance](environment_substrate_g0_acceptance_20260605.md) | Architecture evidence only. |
| Static manifest schema | accepted | [manifest.py](../../../../python/scenario/environment_substrate/manifest.py) | Static data structures only. |
| Registries | accepted | [components.py](../../../../python/scenario/environment_substrate/components.py) | Default descriptors; no runtime consumers. |
| Validators | accepted | [validation.py](../../../../python/scenario/environment_substrate/validation.py) | Fail-closed contract checks only. |
| Compatibility projection contract | accepted | [projection.py](../../../../python/scenario/environment_substrate/projection.py) | Emits contract evidence; does not apply runtime setup. |
| Generator/runtime/derived products | outside G0-J | G0 residuals, this record, and later closure records | G0-K/G0-L/G0-M are accepted separately; runtime setup and consumers remain held. |

## Scope

In scope:

- Add `python/scenario/environment_substrate/` as a shared package namespace.
- Define `EnvironmentManifest`, `EnvironmentObject`, branch membership,
  components, geometry, generation metadata, and projection profiles.
- Define default registries for terrain, atmosphere/weather, wind, illumination,
  maritime/ocean, hydrology, and dynamic environment branches.
- Validate manifest structure, required component attributes, branch/layer/profile
  references, held capability claims, and untyped behavior properties.
- Provide one deterministic static fixture.
- Provide a contract-only `world_zone_definition` projection that records
  evidence and rejects unsupported rich features.

Out of scope:

- Terrain generation or generator plugin implementation.
- Scenario compiler/runtime integration.
- C++ environment runtime ownership.
- Movement, passability, route following, LOS, cover, fires, damage, combat,
  weather simulation, hydrodynamics, hydrology effects, or mutable environment
  state.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `G0-J-A Static Schema` | Add shared manifest/registry data structures. | G0 architecture accepted. | Static dataclasses import and serialize deterministically. | accepted |
| `G0-J-B Validators` | Add fail-closed manifest validation. | Static schema present. | Missing branches, attributes, untyped behavior, and held claims reject. | accepted |
| `G0-J-C Projection Contract` | Add contract-only compatibility projection. | Validators present. | Zone projection emits evidence and rejects unsupported rich features. | accepted |
| `G0-J-D Documentation Sync` | Record acceptance and residuals. | Tests pass. | Parent and package docs named G0-J accepted and G0-K held at G0-J closeout; current G0-K acceptance supersedes that residual. | accepted |

## Task Clusters

- Task cluster plan:
  [environment_substrate_g0_static_manifest_contract_cluster_20260605.md](environment_substrate_g0_static_manifest_contract_cluster_20260605.md)
- Acceptance:
  [environment_substrate_g0_static_manifest_contract_acceptance_20260605.md](environment_substrate_g0_static_manifest_contract_acceptance_20260605.md)

## Outputs And Evidence

- Shared package:
  [python/scenario/environment_substrate](../../../../python/scenario/environment_substrate)
- Focused tests:
  [test_environment_substrate_contracts.py](../../../../tests/scenario/test_environment_substrate_contracts.py),
  [test_environment_projection_contracts.py](../../../../tests/scenario/test_environment_projection_contracts.py)
- Validation:
  `PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py`
  returned `10 passed`.

## Acceptance Gate

This G0 substage is accepted because:

- the package namespace is shared, not service/domain-specific;
- the branch registry includes terrain plus atmosphere/weather, wind,
  illumination, maritime/ocean, hydrology, and dynamic environment branches;
- validators fail closed for missing registries, missing required component
  attributes, untyped behavior properties, held capability claims, and unsupported
  projection targets;
- projection tests prove unsupported rich features do not silently fall through
  to current loose setup defaults;
- no runtime behavior is released.

## Residuals And Next Steps

- The original G0-J residual that held `G0-K` generator/catalog work is
  superseded by the accepted
  [G0-K generator/catalog contract](environment_substrate_g0_generator_catalog_20260605.md),
  which covers request contracts, deterministic tiling, catalogs, seed evidence,
  and in-memory fixture generation only.
- The original G0-J residual that held G0-L projection integration is superseded
  by accepted G0-L projection setup plus compiler data ingestion; runtime setup
  application remains held.
- The original G0-J residual that held G0-M derived products is superseded by
  accepted metadata-only `surface_zone_index` and `occlusion_candidate_index`
  products. Runtime consumers and richer products such as road graph,
  movement-cost grid, passability mask, runtime LOS/cover, weather attenuation
  field, and maritime state field remain held.
- Ground route movement remains governed by the separate G6-D3/G6-F-style release
  vote.

## Archive

This record is a current accepted G0 evidence record. Superseded notes should
move under a local `archive/` only after a maintained replacement README/status or
acceptance surface points to them.
