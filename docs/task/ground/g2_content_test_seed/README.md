# G2 Content And Test Seed

Status: `2026-05-21` accepted by main-thread G2-C integration.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; this is a high-churn task slice.

Inputs:

- [G1 contract skeleton](../g1_contract_skeleton/README.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Ground minimal task structure](../../../standards/ground/minimal_task_structure.md)
- [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Add the first ground content and tests that prove the contract skeleton is
usable without claiming runtime behavior.

## Output

- [G2 content fixture and test cluster](g2_content_fixture_test_cluster_20260521.md)

## Dispatch Shape

G2 is split into two parallel-safe workers plus one serial integration pass:

- `G2-A`: fixture/content seed only, owning `examples/config/database/ground/**`.
- `G2-B`: contract/test seed only, owning `tests/contracts/unit/ground/**` and
  one focused ground contract runner or leader test if required.
- `G2-C`: main-thread integration after both workers return, owning this README,
  the G2 cluster, and the ground dispatch queue.

`G2-A` and `G2-B` must not edit each other's file families or this task
documentation. The main thread owns final acceptance.

## Scope

In scope:

- one or two ground content fixtures
- minimal task/scenario specs that exercise profile defaults
- contract-shape and mapping tests
- evidence that `spawn_unit(type_name)` compatibility is not becoming the
  canonical ground construction path

Out of scope:

- broad scenario catalog
- terrain realism
- movement or combat runtime

## Accepted Result

G2 is accepted with:

- first ground content root:
  `examples/config/database/ground/units/ground_platoon_starter.seed`
- local capability note:
  `examples/config/database/ground/units/CAPABILITY_NOTE.md`
- runnable starter contracts:
  `tests/contracts/unit/ground/task_order_ground_profile_defaults.json`
  `tests/contracts/unit/ground/task_order_ground_minimal_structures.json`
  `tests/contracts/unit/ground/task_order_ground_support_relationships.json`

The starter seed intentionally uses `.seed` instead of `.json` because the
current runtime database loader recursively treats `.json` files under
`examples/config/database/` as concrete unit definitions. G2 does not add a
maintained ground runtime unit schema.

## Gate

G2 is mergeable when fixtures and tests prove the G1 contract skeleton can be
loaded and normalized through maintained entry points.

Gate result: passed. The G2 contracts normalize through the accepted G1 ground
profile and common-core fields without runtime movement, terrain, sensing,
fires, weapon, damage, C++ DTO, binding, or scenario-loader changes.
