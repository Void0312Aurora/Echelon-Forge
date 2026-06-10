# Environment Substrate G0 Static Manifest Contract Cluster

Status: `2026-06-05` accepted finite G0-J implementation substage for
[environment_substrate_g0_static_manifest_contract_20260605.md](environment_substrate_g0_static_manifest_contract_20260605.md).

## Boundary Decision

`G0-J` implements only the static shared environment manifest contract, default
registries, validators, deterministic fixture, and contract-level compatibility
projection tests. It must not implement terrain generation, scenario/runtime
integration, C++ runtime ownership, movement, LOS, cover, fires, damage, combat,
weather simulation, hydrodynamics, hydrology effects, or dynamic environment
mutation.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `G0-J-A Static Schema` | main thread | n/a | Add shared manifest, branch membership, component, geometry, extent, generation, and projection-profile data structures. | `python/scenario/environment_substrate/manifest.py`, package `__init__.py` | No runtime setup, no generator, no C++ code. | Import and deterministic metadata tests. | Fixture serializes deterministically. | Starts after G0 architecture acceptance. | 1 | pass |
| `G0-J-B Registry And Validation` | main thread | n/a | Add default branch/component/layer registries and fail-closed validation. | `python/scenario/environment_substrate/components.py`, `validation.py` | No runtime capability release. | Missing branch, missing component attrs, untyped behavior, and held claims reject. | Validation returns stable reason codes. | Depends on G0-J-A. | 1 | pass |
| `G0-J-C Projection Contract` | main thread | n/a | Add contract-only `world_zone_definition` projection evidence and fail-closed rejection for unsupported rich features. | `python/scenario/environment_substrate/projection.py`, `tests/scenario/test_environment_projection_contracts.py` | No compiler/runtime integration or actual world setup application. | Focused projection tests. | Projection emits evidence and rejects dropped rich components, misspelled surface fields, non-rect geometry, and unsupported targets. | Depends on G0-J-A/B. | 1 | pass |
| `G0-J-D Documentation Sync` | main thread | n/a | Record G0-J acceptance evidence and parent docs status. | `docs/task/ground/environment_substrate_g0_architecture/*.md`, parent ground README/progress/queue docs | No archive, no generator implementation. | `git diff --check` for touched docs. | Parent docs marked G0-J accepted and G0-K held at G0-J closeout; current G0-K acceptance supersedes that residual. | Serial after tests. | 1 | pass |

## Dispatch Rules

- Keep this as shared `environment_substrate` infrastructure, even though the
  task package is indexed from the ground lane.
- Do not edit C++ runtime code in G0-J.
- Do not integrate projection into scenario compiler/runtime setup in G0-J.
- Do not add generator plugins, derived products, movement, LOS, cover, fires,
  damage, or combat behavior.
- Do not treat compatibility projection evidence as a runtime release.

## Worker Packet Requirements

No subagent packet was needed for this narrow main-thread implementation. Any
future delegated `G0-K` packet must return files inspected, implementation scope,
validation outcome, rejected alternatives, and explicit held capability claims.

## Validation Plan

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/scenario/test_environment_substrate_contracts.py tests/scenario/test_environment_projection_contracts.py
```

Result: `10 passed`.

## Acceptance Criteria

G0-J is accepted because:

- the shared package namespace exists under `python/scenario/environment_substrate/`;
- static manifests serialize deterministically;
- the branch registry includes terrain plus atmosphere/weather, wind,
  illumination, maritime/ocean, hydrology, and dynamic environment;
- validators fail closed with stable reason codes;
- projection tests prove unsupported rich terrain semantics are rejected instead
  of silently falling through to current setup defaults;
- no runtime behavior is claimed or released.

## Residual Map

- G0-K generator/catalog work was held at G0-J closeout and is now superseded by
  the accepted G0-K generator/catalog contract.
- The original G0-J residual for G0-L/G0-M is superseded by accepted G0-L
  projection setup plus compiler data ingestion and accepted G0-M metadata-only
  derived products.
- Runtime setup application and runtime derived-product consumers remain held.
- Ground route movement and terrain-aware realism remain behind separate release
  votes.
