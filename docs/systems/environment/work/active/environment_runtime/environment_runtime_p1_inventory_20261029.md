# Environment Runtime — P1 Environment-Read And Ground-Coupling Inventory

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/systems/environment/work/active/environment_runtime/environment_runtime_p1_inventory_20261029.md`
Owner: `systems/environment`
Last verified: `2026-10-29`

Language: English canonical only; no Chinese companion (high-churn inventory record).

Parent: [Environment Runtime](README.md), clusters `P1-A` and `P1-B`.

Status: `2026-10-29` pass. Read-only survey of `src/`, `python/`, `gym_envs/` and
`tools/` on `main` at `3d7df0818`, plus the unmerged
`codex/army-ground-integration` branch (merge base `71912e2a7`). The main thread
re-checked the decisive findings against the source. Nothing was built or run.

Abbreviations: `EM.h` = `src/core/interfaces/environment_model.h`,
`DEM.cpp` = `src/models/environment/default_environment_model.cpp`.

## Correction to the package baseline

The README recorded Ground native terrain as "not on `main`" and listed
Ground-coupling findings measured on `origin/work/army-mechanisms` at
`3cee10ff`. Both are stale:

- Ground native terrain reached `main` on `2026-10-01` through the army stack,
  merge `85abc7ce6` (PR #85). `be2de24af feat(ground): consume Arnis terrain
  rasters natively` is part of it.
- Neither shared file includes a domain header any more. `16fb9bcda` removed
  the `ground_tasking_enums.h` include, the `movement_effects.h` include from
  `DEM.cpp`, and `get_ground_transition_movement_observation` before that
  merge.

Ground-specific methods, types and policies are still inside the shared files;
they now reach them without includes. P4-A therefore starts from `main`, not
from a branch merge.

## Summary

| Cluster | `shared` | `ground-owned` | `retire` | Bypasses `IEnvironmentModel` |
| --- | --- | --- | --- | --- |
| P1-A reads on `main` (34 rows) | 22 | 4 | 8 | 9 |
| P1-B Ground items on `main` (25) | 11 | 14 | 0 (2 already retired by `16fb9bcda`) | n/a |
| P1-B additions on `codex/army-ground-integration` (9) | 9 | 0 | 0 | n/a |

Classes:

- `shared`: domain-neutral; stays on the shared runtime.
- `ground-owned`: Ground logic or types in shared files; P4-A moves them into
  the Ground domain.
- `retire`: dead, duplicated or superseded.

## Decisive findings

1. **Ground content is on `main` without domain includes.** The P4 exit
   condition "shared files include no domain header" already holds. What still
   fails the package goal: four Ground methods and two Ground structs in `EM.h`
   (`get_ground_field_semantic_observation`, `get_ground_transition_observation`,
   `load_arnis_field_overlay`, `GroundFieldSemanticObservation`,
   `GroundTransitionObservation`; `get_ground_slope_deg` is shared but
   misnamed), plus 14 ground-owned items in `DEM.cpp` and the kernel.
2. **Elevation and surface disagree outside the raster.** Off an Arnis raster,
   `get_terrain_elevation` returns the procedural 2000 m Gaussian hill
   (`DEM.cpp:480-482`) while `get_terrain_at` returns `Obstacle`
   (`DEM.cpp:627-633`). `3f89cf199` on the army branch measured about 88.7°
   slopes at the raster edge from this. P2-A must define out-of-tile behavior
   once, for both queries.
3. **No vertical datum exists.** The Arnis bundle declares
   `source_provider_native_unspecified` (`arnis_bundle.py:980`) and the loader
   ignores datum (origin z = 0, `DEM.cpp:923`). Consumers each assume their own
   zero: ship z is forced to 0 (row 16), submarines require a surface at 0
   (row 17), sensors and data links use `max(0, z)` (row 12), runway elevation
   is authored separately (row 32).
4. **`check_line_of_sight` has no along-path terrain occlusion over land**
   (`DEM.cpp:485-516`). It samples the path only when maritime state is
   configured and both endpoints are near z = 0; otherwise it checks only that
   the endpoints are above terrain. The army branch's terrain line-of-sight
   query is the first real along-path test.
5. **The two `IEnvironmentModel` implementations have diverged.** The GPU visual
   snapshot model (`gpu_visual_runtime.cpp:47-196`) ignores Arnis elevation,
   wind and sun, uses a hard-coded hill, and drops `step_x`/`step_y` from the
   snapshot (`DEM.cpp:1021-1029`).
6. **Maritime state is one global value with a per-platform fallback,
   implemented three times** (rows 13–15), and the Python binding drops the
   `configured` flag.

## Decision for the army line of sight

**Terrain line of sight is domain-neutral in its contract.** The branch's
`get_terrain_line_of_sight_observation` takes two points and two heights and
returns a status with an explicit `Unknown` and provenance. It carries no Ground
type and no stance. Its only consumer,
`src/systems/domains/ground/direct_fire_line_of_sight.h:67`, keeps stance and
eye height on the Ground side. Air, naval and sensing could call it.

**Its implementation is Ground-scale only:**

- heights are above terrain at each endpoint, while aircraft and ships carry
  absolute z;
- it answers only over a loaded Arnis raster and returns `Unknown` on
  procedural or `flat` terrain, which is the default scenario terrain;
- a path leaving the tile returns `Unknown` (`SampleOutsideRaster`);
- it has no earth-curvature term.

So the branch can land the query as a **shared** query now. P2-A then decides
absolute versus above-terrain heights, out-of-tile behavior, curvature and the
`TerrainElevationSource` enum. It must not replace `check_line_of_sight` for
sensors until those are settled, because sensors would lose results wherever it
answers `Unknown`.

A textual dry-run merge of the branch onto `main` merges both shared files
without conflict markers; conflicts appear only in `CMakeLists.txt` and five
documentation files.

## P1-A: environment reads on `main`

| # | Site | Query or ad hoc mapping | Consumer | Class |
| --- | --- | --- | --- | --- |
| 1 | `src/models/physics/aerodynamics_common.h:57-63`; callers `aero_state_system.h:57`, `aerodynamics_system.h:290`, `propulsion_system.h:92`, `default_guidance_model.cpp:1424` | `get_atmosphere_at`; standard-atmosphere zero-wind fallback `:33-62` | air, weapons | shared |
| 2 | `src/systems/domains/air/aerodynamics_system.h:199-200` | `get_terrain_elevation` → ground-effect height | air | shared |
| 3 | `default_control_model.cpp:73`; `instrument_system.h:58` | `get_terrain_at().runway_heading` | air | shared |
| 4 | `src/systems/physics/instrument_system.h:126-127, :208` | elevation → radar altitude; atmosphere → OAT and wind | air | shared |
| 5 | `src/systems/physics/ground_contact_system.h:178, :243, :311-317` | elevation plus `SurfaceType` → friction and off-road stress | air (gear) | shared |
| 6 | `navigation_system.h:48`; `default_unit_factory.h:1365` | `environment_local_to_geodetic` | navigation | shared |
| 7 | `src/systems/systems/navigation_system.h:58` | `alt_radar = max(0, z)` flat-ground fallback | navigation | retire, bypass |
| 8 | `src/systems/physics/leapfrog_system.h:80-85` | hard floor at `z < -5 m` | integrated bodies | retire, bypass |
| 9 | `src/models/systems/default_sensor_model.cpp:465-467` | `check_line_of_sight` | sensing | shared |
| 10 | `default_sensor_model.cpp:472-474` | `get_weather_attenuation` (provider returns 0.0, `DEM.cpp:518-520`) | sensing | shared (stub) |
| 11 | `default_sensor_model.cpp:481` | `get_sun_direction` → glare | sensing | shared |
| 12 | `default_sensor_model.cpp:226-236, :259-272`; `data_link_system.h:18-24, :50-56` | horizon from `geodesy::EarthModel{}`, not the environment's earth model; height `max(0, z)` | sensing, comms | shared, bypass |
| 13 | `src/models/domains/naval/naval_sensor_maritime_adapter.h:13-30` | `get_maritime_state` with `ShipPlatform` fallback | naval sensing | shared |
| 14 | `src/models/systems/default_acoustic_model.cpp:80-97` | copy of row 13's helper | naval acoustics | retire (duplicate) |
| 15 | `src/systems/domains/naval/ship_motion_system.h:160-170` | `get_maritime_state` with `ShipPlatform` fallback | naval | shared |
| 16 | `ship_motion_system.h:208` | `transform.z = 0.0` hard-coded sea level | naval | retire, bypass |
| 17 | `src/systems/domains/naval/submarine_motion_system.h:103-127` | `get_bathymetry_along_segment`; requires surface elevation 0 | naval | shared |
| 18 | `movement_system.h:30, :95, :100`; `movement_effects.h:120-121` | elevation, `get_terrain_at`, `get_ground_slope_deg` | ground | shared |
| 19 | `movement_system.h:129`; `movement_effects.h:108` | `get_ground_transition_observation` | ground | ground-owned |
| 20 | `src/core/engine/simulation_kernel.cpp:418, :430` | terrain and slope probe | ground probe | shared |
| 21 | `simulation_kernel.cpp:440-442, :466, :484, :503` | stance movement effects, field semantics, transition | ground probe | ground-owned |
| 22 | `bindings_core_kernel_diagnostics_ground.cpp:16-76`; `python/rl/ground/native_probe.py:186-196, :246-255, :361-363, :464-480` | Python Ground probe surface | ground RL | ground-owned |
| 23 | `simulation_kernel.cpp:374-376, :560, :569`; `bindings_core_kernel_maintained.cpp:79, :95, :102` | sun (fallback `{0, 0.7071, 0.7071}`), anchor, maritime state; binding drops `configured` | all | shared |
| 24 | `src/systems/visual/visual_system.h:148, :179, :187, :345, :376, :385` | ray cast against elevation and surface | visual, RL obs | shared |
| 25 | `src/gpu/gpu_visual_runtime.cpp:47-196`; snapshot via `world_batch_visual_binding_compatibility_helper.h:112` → `DEM.cpp:1010-1055` | second `IEnvironmentModel` through `dynamic_cast`; hard-coded hill, zero wind, fixed sun, endpoint-only LOS | visual | retire, bypass |
| 26 | `DEM.cpp:485-516` | LOS endpoint check; path sampling only on the maritime branch | provider | shared |
| 27 | `DEM.cpp:480-482` | procedural 2000 m hill, also returned off an Arnis raster | provider | retire |
| 28 | `DEM.cpp:398, :414` | `weather_zones_` written, never read | provider | retire |
| 29 | `cuda_resident_flight_dynamics_fixture_contract.h:34-37`; `cuda_resident_backend.cpp:229` | no environment; zero-wind standard-atmosphere constants; terrain rejected | air (CUDA) | shared, bypass |
| 30 | `python/rl/ground/infantry_proxy.py:390-680` | reads the bundle raster directly; own slope and grid transform | ground RL | retire, bypass |
| 31 | `python/rl/ground/native_env.py:32-60` | `np.memmap` of the elevation raster for observation bounds | ground RL | ground-owned, bypass |
| 32 | `gym_envs/scenario_loader/spatial_runtime/geometry.py:164` → `spatial_query_runtime.cpp:185-187` | runway `elev_m` authored separately, default 0.0 | air | shared, bypass |
| 33 | `gym_envs/observation_view.py:197-198`; `gym_envs/universal_env_parts/observations.py:195-196` | indirect: contact `terrain_z`, instrument wind | air RL | shared |
| 34 | `python/scenario/runtime/kernel_apply.py:364-417`; `batch_apply.py:97-140`; `world_batch_setup_helper.h:48-138`; `world_batch_runtime.cpp:595-604` | setters for terrain profile, wind, sun, maritime, anchor, zones; `kernel_apply.py:366-398` swallows exceptions | scenario | shared |

No tool under `tools/` calls the native environment. Five test fakes implement
`IEnvironmentModel` and must follow any P2-A interface change:
`test_structural_failure_system.cpp`, `test_ground_movement.cpp`,
`test_submarine_bathymetry.cpp` (two), `test_ground_contact_solver.cpp`.

## P1-B: Ground items in the shared files on `main`

| Item | File:line | Commit | Class |
| --- | --- | --- | --- |
| `get_ground_slope_deg` (gradient only) | `EM.h:64-80` | `1c19bd021` | shared, rename |
| `GroundFieldSemanticObservation` | `EM.h:111-119` | `4e1a0b4cf` | ground-owned |
| `GroundTransitionObservation` | `EM.h:121-129` | `108becbac` | ground-owned |
| `load_arnis_terrain_bundle` | `EM.h:159` | `be2de24af` | shared (future tile loader) |
| `load_arnis_field_overlay` | `EM.h:164` | `4e1a0b4cf` | ground-owned |
| `get_ground_field_semantic_observation` | `EM.h:166-169` | `4e1a0b4cf` | ground-owned |
| `get_ground_transition_observation` | `EM.h:171-176` | `108becbac` | ground-owned |
| `ArnisFeatureGeometry`, geometry helpers, `bridge_at`, `river_at` | `DEM.cpp:44-48, :68-120` | `bb83b5abf` | shared |
| `river_features`, `bridge_features` | `DEM.cpp:61-62` | `bb83b5abf` | shared |
| `tree_line_features`, `settlement_features`, `field_overlay_loaded` | `DEM.cpp:63-65` | `4e1a0b4cf` | ground-owned |
| `arnis_metric_bundle`, `index_for`, `get_elevation`, `get_landcover` | `DEM.cpp:66, :122-169` | `be2de24af` | shared |
| bundle readers | `DEM.cpp:174-238` | `be2de24af`, `bb83b5abf` | shared |
| `read_field_overlay`, evidence check, field distance | `DEM.cpp:240-364` | `4e1a0b4cf` | ground-owned |
| `surface_for_landcover` nodata → `Obstacle` | `DEM.cpp:366-377` | `be2de24af` | ground-owned policy (the class map itself is shareable) |
| `vegetation_density_for_landcover` | `DEM.cpp:379-395` | `d309ab2ff` | shared |
| Arnis elevation branch | `DEM.cpp:476-479` | `be2de24af` | shared |
| Arnis branch of `get_terrain_at` | `DEM.cpp:589-626` | `be2de24af`, `bb83b5abf` | shared |
| off-raster → `Obstacle` | `DEM.cpp:627-633` | `be2de24af` | ground-owned |
| field-semantic implementation | `DEM.cpp:666-711` | `4e1a0b4cf` | ground-owned |
| transition implementation (5 m sampling; `Water`/`Obstacle` impassable) | `DEM.cpp:713-743` | `108becbac` | ground-owned |
| `load_arnis_terrain_bundle` implementation; no vertical datum | `DEM.cpp:790-949` | `be2de24af` | shared |
| `load_arnis_field_overlay` implementation | `DEM.cpp:951-963` | `4e1a0b4cf` | ground-owned |
| kernel include of `systems/domains/ground/movement_effects.h` (engine → systems is allowed by `cpp_include_graph.py:264-270`) | `simulation_kernel.cpp:19` | `8250112a9` | ground-owned seam |
| kernel terrain and slope probe | `simulation_kernel.cpp:414-433` | `75e2680b3` | shared |
| kernel stance, field and transition probes | `simulation_kernel.cpp:435-520` | `8250112a9`, `ab37752fd` | ground-owned |

## P1-B: additions on `codex/army-ground-integration`

From `346d2db17` (terrain line of sight) and `3f89cf199` (slope window kept
inside the raster). Line numbers are on the branch.

| Item | File:line | Class |
| --- | --- | --- |
| `kGroundSlopeSampleHalfSpanM = 5.0` | `EM.h:33-35` | shared, rename |
| `get_ground_slope_deg` refactor, `ground_slope_deg_from_gradient` | `EM.h:45-63` | shared, rename |
| `TerrainLineOfSightStatus`, `TerrainLineOfSightUnknownReason`, `TerrainLineOfSightObservation` | `EM.h:117-129, :136-154` | shared |
| `TerrainElevationSource {None, ArnisMetricRaster}` | `EM.h:131-134` | shared; generalize to tiles in P2-A |
| `get_terrain_line_of_sight_observation` (default `Unknown`) | `EM.h:156-165` | shared |
| `cell_step_x/y`, `cell_for`, `index_for` refactor | `DEM.cpp:122-157` | shared |
| `elevation_gradient` (raster cells only, one-sided at edges) | `DEM.cpp:159-194` | shared |
| `get_ground_slope_deg` override (NaN off the raster) | `DEM.cpp:539-557` | shared |
| line-of-sight implementation | `DEM.cpp:819-887` | shared |

## Uncertainties

- Merge commits for PRs #82–#84 were not located individually; #85 carries the
  stack.
- Nothing was built or tested; the branch merge result is textual only.
- The introducing commits of the kernel slope, field and transition wrappers
  were not checked one by one.
- `infantry_proxy.py` is classed `retire` on the judgement that the native
  probe replaces it; it is still exported from `python/rl/ground/__init__.py`,
  so retiring it is a Ground package decision.
- `load_arnis_field_overlay` is classed `ground-owned` because Ground is its only
  consumer. Tree lines and settlements could instead become shared vegetation
  and built-structure layers in P2-A.
- Dynamic Python dispatch beyond the `hasattr` checks in `kernel_apply.py` was not
  traced, and `examples/` was not surveyed.
