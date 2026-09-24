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
  crop/grass/tree-like classes currently share the soft-dirt movement cost.
- `SimulationKernel.get_ground_terrain_observation(x, y)` exposes the native
  sample as `(elevation, surface_type, friction, roughness,
  vegetation_density)` for training-side adapters and diagnostics.
- Loading is transactional: an invalid candidate returns `false` without
  replacing the current provider raster.

## Explicit non-goals

This package does not consume Arnis vector features, infer bridges from
hydrology, provide route/passability or line-of-sight queries, or connect RL
training to native reset/step/replay. It also does not claim automatic runtime
setup or full terrain physics.

## Evidence

- `tests/runtime/ground/test_ground_infantry_native_unit.py`
- `tests/training/test_ground_infantry_contracts.py`
- `src/models/environment/default_environment_model.cpp`
- `src/core/engine/simulation_kernel.cpp`

The 2026-09-24 batch was built with the pinned Windows dependencies. The
Arnis movement test and Ground training contract tests passed (`5 passed`).
The remaining vector semantic, passability, bridge, observation, and RL gates
remain explicitly open.
