# Ground Arnis Native Terrain v1

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `work-package`
Lifecycle: `active`
Canonical: `docs/domains/ground/work/active/ground_arnis_native_terrain_v1/README.md`
Owner: `domains/ground`
Accepted: `2026-09-24`

## Purpose

Make the existing Arnis eastern-plain fixture useful to the maintained native
Ground movement slice without silently treating fixture metadata as runtime
truth.

## Admitted contract

- `SimulationKernel.load_arnis_terrain_bundle(bundle_root)` is the explicit
  provider entry point.
- The provider accepts only `arnis_cmo_bundle.v1` bundles that declare
  `no_held_capability_release=true`.
- Elevation and landcover artifacts must have matching positive shapes,
  matching finite origin/step metadata, safe child paths, exact byte lengths,
  and finite little-endian float elevations.
- The native environment samples the signed metric grid directly. Permanent
  water and unknown/nodata cells stop the bounded infantry movement slice;
  crop/grass/tree-like classes remain soft dirt but now carry distinct
  vegetation-density observations and a bounded movement-speed penalty.
- `SimulationKernel.get_ground_terrain_observation(x, y)` exposes the native
  sample as `(elevation, surface_type, friction, roughness,
  vegetation_density)` for training-side adapters and diagnostics.
- `SimulationKernel.get_ground_slope_deg(x, y)` exposes the same bounded local
  5 m terrain-gradient sample used by Ground movement. It is an observation of
  slope only; it does not claim climbability, fatigue, or full terrain physics.
- `SimulationKernel.load_arnis_field_overlay(path)` plus
  `get_ground_field_semantic_observation(x, y)` admits metadata-only tree-line
  and settlement distance/bearing flags after the continuous bundle is loaded.
- The native provider consumes the Arnis hydrology and bridge road vectors for
  bounded point sampling: river corridors are water and declared bridge
  segments override them as hard-packed crossing surfaces.
- `SimulationKernel.get_ground_transition_observation(from_x, from_y, to_x,
  to_y)` samples a local segment at 5 m intervals and returns passability plus
  water/obstacle/bridge evidence. This is a bounded transition probe only; it
  does not provide a route graph, waypoint planner, cover, or line of sight.
- `SimulationKernel.get_ground_transition_movement_observation(...)` reuses the
  same segment samples to return minimum/average combined movement multipliers
  for a selected stance. Ground movement consumes the average after the local
  transition is admitted; this remains a segment-cost observation, not a route
  cost grid or general passability product.
- Loading is transactional: an invalid candidate returns `false` without
  replacing the current provider raster.

## Explicit non-goals

This package does not provide route graphs, general passability or line-of-sight
queries, tree-line/settlement cover semantics, or connect RL training to native
reset/step/replay. The field overlay observation is metadata-only and does not
change movement, passability, concealment, cover, or fire-control authority.
It also does not claim automatic runtime setup or full terrain physics.

## Evidence

- `tests/runtime/ground/test_ground_infantry_native_unit.py`
- `tests/training/test_ground_infantry_contracts.py`
- `src/models/environment/default_environment_model.cpp`
- `src/core/engine/simulation_kernel.cpp`

The 2026-09-24 batch was built with the pinned Windows dependencies. The
Arnis movement test and Ground training contract tests passed (`5 passed`).
The remaining route/passability, cover/observation, and RL gates remain
explicitly open.
