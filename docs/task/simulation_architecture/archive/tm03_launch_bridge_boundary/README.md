# TM03 Launch Bridge Boundary

Status: closed on `2026-05-25` with a scoped implementation pass.

TM03 follows TM01-B. Its job is to turn the source-backed
`systems -> SimulationKernel` weapon-release residual into a finite design and
dispatch surface before any implementation worker touches P7 launch/fire-control
code.

Governance:

- Follow the [Subagent Usage Policy](../../../../standards/governance/subagent_usage_policy.md).
- Keep the first pass documentation-only unless the task cluster explicitly
  authorizes a code slice.
- Do not reopen WP24, TM01, or TM02.
- Stop after the declared cluster round cap instead of adding follow-up waves.

Planning surface:

- [TM03 Launch Bridge Boundary Task Clusters](tm03_launch_bridge_boundary_task_clusters_20260525.md)

## Initial Source-Backed Finding

The initial residual was narrow and concrete:

| Source | Current behavior | Boundary concern |
|--------|------------------|------------------|
| `src/systems/combat/pilot_weapon_release_system.h` | Includes `core/engine/simulation_kernel.h`, captures `SimulationKernel&`, and calls `fire_weapon_from_pilot_action(...)`. | `systems/` per-tick ECS logic reaches back into the core world owner instead of consuming a narrow model/service interface. |
| `src/systems/naval/naval_mission_weapon_release_system.h` | Includes `core/engine/simulation_kernel.h`, captures `SimulationKernel&`, and calls `fire_naval_weapon_from_mission_command(...)`. | Same boundary issue for naval mission-command release. |
| `src/core/engine/simulation_kernel_systems.cpp` | Registers both helpers with `*this` at phases 6.58 and 6.59. | The bridge is explicit and centralized, but still couples systems to the core owner. |

The architecture reference is [src/systems/README.md](../../../../../src/systems/README.md),
which says `systems/` consumes components/models and is registered by
`core/engine`.

## Selected Seam

TM03-B selected a narrow C++ service interface:

- `src/core/interfaces/weapon_release_service.h` owns
  `IWeaponReleaseService`.
- `SimulationKernel` implements the interface by forwarding to the maintained
  weapon API surface.
- The two release helpers accept `IWeaponReleaseService&` instead of
  `SimulationKernel&`.
- `simulation_kernel_systems.cpp` remains the centralized registration owner and
  passes a named `weapon_release_service` reference.

Rejected alternatives:

- A component/event request queue would be larger than the residual and would
  reopen P7 launch/fire-control scheduling semantics.
- Copying target selection or weapon launch logic into `systems/` would violate
  the boundary and duplicate maintained weapon API behavior.
- A broad runtime facade would exceed the TM03 two-helper scope.

## Scope

TM03 may prepare or implement a narrow replacement seam for the two launch
bridges only if the design cluster accepts a concrete shape.

Allowed replacement directions:

- a small launch service interface owned outside `systems/`;
- a component/event request emitted by systems and consumed by core/engine;
- a model-facing wrapper if it preserves `systems/` boundaries and does not copy
  `SimulationKernel` ownership into another system helper.

Explicit non-goals:

- Do not redesign all P7 launch/fire-control semantics.
- Do not rewrite `simulation_kernel_weapon_api.cpp`.
- Do not change weapon envelope, ammo, target selection, damage, or effects
  behavior.
- Do not migrate naval/air command semantics beyond the two bridge call sites.
- Do not claim raw-runtime or compatibility retirement.

## Exit State

TM03 can close only after one of these outcomes:

- `accepted design`: a narrow replacement seam is selected with file ownership,
  tests, and migration gates;
- `scoped implementation pass`: the two systems no longer include
  `core/engine/simulation_kernel.h` and focused weapon/architecture tests pass;
- `blocked`: the bridge remains live with a named blocker, owner, replacement
  condition, validation gap, and forced review trigger.

TM03 must not report broader P7 closure unless a separate accepted task lane
exists for it.

## Validation Evidence

TM03-C/TM03-D closed with the following focused validation on `2026-05-25`:

- `git diff --check`: passed.
- `rg -n '#include "core/engine/simulation_kernel.h"|SimulationKernel&' src/systems/combat/pilot_weapon_release_system.h src/systems/naval/naval_mission_weapon_release_system.h`: no matches.
- `cmake --build build-workshop --target ef_py -j4`: passed.
- `PYTHONPATH=build-workshop python -m pytest -q tests/architecture/structural_boundaries/test_structural_guardrails.py`: `15 passed`.
- `PYTHONPATH=build-workshop python -m pytest -q tests/runtime/air_combat/test_weapon_roe_runtime.py tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py`: `11 passed`.
- `PYTHONPATH=build-workshop python -m pytest -q tests/runtime/naval/test_naval_ship_database.py -k "mission_command_can_trigger_ciws or mission_command_ciws_release"`: `2 passed, 20 deselected`.

## Close-Out

TM03 closes the TM01-B source-backed launch-bridge residual for the two explicit
release helpers:

- `src/systems/combat/pilot_weapon_release_system.h` no longer includes
  `core/engine/simulation_kernel.h` or accepts `SimulationKernel&`.
- `src/systems/naval/naval_mission_weapon_release_system.h` no longer includes
  `core/engine/simulation_kernel.h` or accepts `SimulationKernel&`.
- `IWeaponReleaseService` is the maintained narrow seam between the helper
  systems and the existing weapon API behavior.
- Architecture guards now prevent the helper headers from regressing to a direct
  `SimulationKernel` dependency.

Residuals outside TM03 remain explicitly open only if owned by another lane:
broad P7 launch/fire-control redesign, public raw-runtime retirement, and wider
compatibility cleanup were not part of this closure.
