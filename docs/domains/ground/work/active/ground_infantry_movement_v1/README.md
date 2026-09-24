# Ground Infantry Movement v1

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `work-package`
Lifecycle: `active`
Canonical: `docs/domains/ground/work/active/ground_infantry_movement_v1/README.md`
Owner: `domains/ground`
Accepted: `2026-09-24`

## Purpose

Admit the first maintained native movement slice for a single dismounted Ground
fixture without pretending that the land domain already has route planning,
formations, or full physics.

## Contract

- `Ground_Infantry_Soldier_MVP` is loaded with native `UnitType::Ground` identity.
- An active `MissionCommand` with `ground_task_mode = MoveStatic` supplies NAV
  heading and requested speed.
- `GroundInfantryMovement` is registered as
  `builtin.system.ground_infantry_movement` at default composition stage 34.
- The system reads the shared `IEnvironmentModel` at the current position. It
  applies surface multipliers (paved 1.0, hard-packed 0.90, soft dirt 0.75,
  water/obstacle 0.0) and a bounded slope multiplier, then advances a horizontal
  kinematic step. Invalid or inactive commands stop the unit.
- The default provider can explicitly load a verified Arnis `arnis_cmo_bundle.v1`
  continuous elevation and landcover raster pair. Sampling preserves the
  bundle's local metric origin and signed grid steps; permanent water and
  unknown cells are fail-closed for movement. This is an explicit provider
  load operation, not automatic runtime setup.
- Command transport remains the maintained command path; the focused test sets
  zero link latency only to isolate the movement stage.
- `GroundStance` accepts `Stand`, `Crouch`, and `Prone` through the maintained
  command shell. It changes movement cost only (1.0, 0.65, and 0.35); it does
  not imply cover, concealment, exposure, or weapon behavior. A separate
  bounded direct-fire slice is admitted for the infantry fixture; it is not
  part of this movement package.
- The native movement system asks the environment owner for a sampled transition
  observation over the one-tick segment. The default Arnis provider samples at
  most 5 m intervals, reports water/obstacle blockers, and admits a declared
  bridge segment as a bounded crossing surface.

## Explicit non-goals

This package does not admit route following, waypoint planning, formation
behavior, acceleration, fatigue, cover/concealment, line of sight, indirect
fires, suppression, logistics, or RL policy training. The native provider now
consumes bounded Arnis hydrology and bridge road vectors; tree lines,
settlements, structures, route graphs, and general passability remain later
packages. The movement consumer blocks any sampled one-tick segment that
intersects water or an unknown/obstacle cell without advancing the transform;
this is a local transition check, not a route graph or general path planner.

## Evidence

- `tests/runtime/ground/test_ground_infantry_native_unit.py`
- `tests/architecture/composition/test_simulation_composition_contract.py`
- `tests/architecture/composition/test_runtime_composition_evidence_contract.py`
- `tests/architecture/composition/test_runtime_profile_projection_contract.py`
- `src/runtime/contracts/composition/default_compatibility_manifest.v1.generated.h`
- `src/runtime/contracts/composition/runtime_composition_evidence.v1.generated.h`

The 2026-09-24 batch was built with the repository's pinned Windows
dependencies. The focused movement/training Python suite passed `5 passed`;
the previous native movement regression suite passed `36 passed, 1 skipped`; the
composition lifecycle, composition evidence, and backend-provider migration
doctest binaries passed. The Cordis conformance binary requires its documented
request/lock/manifest arguments and was not treated as a no-argument smoke test.
