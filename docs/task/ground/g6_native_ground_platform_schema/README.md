# G6-E Native Ground Platform Schema

Status: `2026-05-25` opened for `G6-E0 Native Ground Platform Schema Planning`.
No runtime schema, movement scenario, movement behavior, terrain, sensing,
fires, damage, or combat implementation is released by this package.

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

## Current Blocker

The accepted `G6-D1/D2` preflight found:

- `examples/config/database/ground/units/ground_platoon_starter.seed` is a
  planning seed and is intentionally not auto-loaded.
- `src/components/basic/common.h::UnitType` has no `Ground` value.
- `src/content/unit_definition_loader.cpp::parse_unit_type()` rejects
  `Ground`.
- `src/interfaces/python/bindings_core.cpp` exposes no `ef_py.UnitType.Ground`.
- `DefaultUnitFactory` has no built-in ground definition or materialization
  rule.
- `SimulationKernel::spawn_unit(..., "Ground", ...)` returns null through
  `resolved_platform_spawn_plan_type_name_not_found`.

Therefore `ground_platoon_flat_route_move_v1` remains held.

## Output

- [G6-E native ground platform schema cluster](g6_native_ground_platform_schema_cluster_20260525.md)

No scenario, runtime behavior, movement model, weapon model, terrain model, or
observation export file is part of `G6-E0`.

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

A later implementation release may close this package only when all of these
are true:

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

## Residuals

- After this schema package closes, a separate release vote is still required
  before any `G2` route-move scenario can be implemented.
- Movement evidence gates from G6-D2 remain the future gate for
  `ground_platoon_flat_route_move_v1`.
- G3+ terrain-aware movement, G4 contact report, G5 fires, G6 damage, and G7
  sustainment remain separate packages.
