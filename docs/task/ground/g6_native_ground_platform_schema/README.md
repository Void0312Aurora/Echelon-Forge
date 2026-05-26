# G6-E Native Ground Platform Schema

Status: `2026-05-26` accepted for `G6-E0 Native Ground Platform Schema
Planning`, `G6-E1` source-inventory/design preflight, `G6-E2` native schema
implementation, and `G6-E3` integration/release vote. This package releases
one loadable/spawnable native ground platform schema only. It does not release
route movement, movement behavior, terrain, sensing, fires, damage, or combat.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; this is a high-churn planning slice.

Inputs:

- [G6-D route-move release decision](../g6_route_move_release_decision/README.md)
- [Ground current progress](../ground_current_progress_20260524.md)
- [Ground bootstrap plan](../ground_domain_bootstrap_plan_20260521.md)
- [Ground standards overview](../../../standards/ground/README.md)
- [Subagent usage policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

Convert the `G6-D1/D2` native-schema blocker into a bounded implementation
package before any route-move scenario is attempted.

This package answers one release question:

What is the smallest runtime-loadable native ground platform schema that can be
implemented through the shared unit-definition, capability-bundle, spawn, and
binding surfaces without creating a private ground runtime stack?

## Closed Native Schema Blocker

The accepted `G6-D1/D2` preflight found:

- `examples/config/database/ground/units/ground_platoon_starter.seed` was a
  planning seed and is intentionally not auto-loaded.
- `src/components/basic/common.h::UnitType` had no `Ground` value.
- `src/content/unit_definition_loader.cpp::parse_unit_type()` rejected
  `Ground`.
- `src/interfaces/python/bindings_core.cpp` exposed no `ef_py.UnitType.Ground`.
- `DefaultUnitFactory` had no ground capability evidence.
- `SimulationKernel::spawn_unit(..., "Ground", ...)` returned null through
  `resolved_platform_spawn_plan_type_name_not_found`.

`G6-E2` closes the native identity/schema part of that blocker with
`Ground_Platoon_MVP`. `ground_platoon_flat_route_move_v1` remains held until a
later route-move release vote accepts movement evidence.

## E1 Design Result

`G6-E1` selects the smallest implementation path:

- public identity should be `UnitType::Ground`;
- the first auto-loadable JSON should use `type = "Ground"` and source name
  `Ground_Platoon_MVP`;
- materialization should reuse the existing type-name/default-factory spawn
  path;
- Python identity evidence should use existing `SimulationKernel.get_unit_type()`
  plus the new `ef_py.UnitType.Ground` enum value;
- no typed-platform/facade path is required for E2;
- no movement-specific component is required for E2.

The first implementation should make a static or caller-initial-velocity ground
entity loadable/spawnable/inspectable. Route following and movement updates
remain later work.

## E2/E3 Evidence

`G6-E2` implements the accepted E1 path:

- `UnitType::Ground` is public runtime identity.
- `type = "Ground"` is admitted by unit-definition loading.
- `examples/config/database/ground/units/ground_platoon_mvp.json` is
  auto-loadable database content with source name `Ground_Platoon_MVP`.
- `DefaultUnitFactory` emits capability-bundle evidence for
  `ground_mobility_flat_deferred` and `land_tactics` without adding a
  movement-specific component or route-following behavior.
- `ef_py.UnitType.Ground` is exposed, and the default UnitType overload maps to
  `Ground_Platoon_MVP` after the database is loaded.
- `tests/runtime/ground/test_ground_native_platform_schema.py` proves load,
  spawn, native identity, non-substitute classification, static runtime
  inspection, and fail-closed malformed-schema behavior.

`G6-E3` accepts this as native schema evidence only. It permits a later
G6-D3/G6-F route-move release vote to be proposed, but it does not itself
release route movement or any higher realism grade.

Validation:

```bash
cmake --build build-workshop --target ef_py -j2
# [100%] Built target ef_py

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/ground/test_ground_native_platform_schema.py
# 5 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q \
  tests/runtime/ground/test_ground_native_platform_schema.py \
  tests/contracts/unit/ground \
  tests/architecture/test_ground_realism_gradient_guardrails.py \
  tests/runtime/ground/test_ground_mvp_scenario.py \
  tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py \
  tests/leader/test_ground_profile_semantics.py
# 24 passed
```

## Output

- [G6-E native ground platform schema cluster](g6_native_ground_platform_schema_cluster_20260525.md)

No scenario, route movement behavior, movement model, weapon model, terrain
model, or observation export file is part of `G6-E`.

## Scope

In scope for the eventual implementation package:

- a minimal public ground unit type or equivalent maintained capability-bundle
  materialization path;
- runtime database loading for a source-controlled native ground platform
  definition;
- default factory spawn-plan admission and materialization for a native ground
  platform;
- Python identity/binding exposure sufficient to prove a spawned entity is
  ground-native;
- focused tests proving load, spawn, identity, and non-air/non-facility
  classification;
- explicit evidence that movement, terrain, sensing, fires, damage, and combat
  remain deferred.

Out of scope:

- `ground_platoon_flat_route_move_v1`;
- route following, speed/acceleration updates, stuck/off-route checks, or
  terrain passability;
- terrain-aware movement, line-of-sight sensing, contact reports, fires,
  effects, suppression, damage, or combat;
- broad facade expansion or a private `systems/ground/` runtime stack.

## Minimum Acceptance Gate

`G6-E2/E3` closes this package because all of these are true:

- the example database can load a native ground platform definition without
  treating it as `Aircraft`, `Ship`, `Submarine`, `Facility`, or `C2Node`;
- Python can assert the native ground identity through a public binding or
  maintained capability evidence;
- `SimulationKernel::spawn_unit()` or the maintained typed platform setup path
  can materialize a native ground entity;
- the spawned entity exposes stable position, heading, velocity, and health
  state through existing runtime inspection hooks;
- capability-bundle evidence names ground platform/mobility families but does
  not claim route movement;
- focused tests include at least one fail-closed negative case.

For the accepted E1 path, the implementation gate uses
`SimulationKernel::spawn_unit(..., "Ground_Platoon_MVP", ...)` and
`get_unit_type(entity_id) == int(ef_py.UnitType.Ground)`.

## Residuals

- A separate release vote is still required before any `G2` route-move scenario
  can be implemented.
- Movement evidence gates from G6-D2 remain the future gate for
  `ground_platoon_flat_route_move_v1`.
- G3+ terrain-aware movement, G4 contact report, G5 fires, G6 damage, and G7
  sustainment remain separate packages.
