# Geodetic Frame — P1-A Flat-Frame And Curvature Inventory

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/systems/physics/work/active/geodetic_frame/geodetic_frame_p1a_inventory_20260928.md`
Owner: `systems/physics`
Last verified: `2026-09-28`

Language: English canonical only; no Chinese companion (high-churn inventory record).

Parent: [Geodetic Frame](README.md), cluster `P1-A`.

Status: `2026-09-28` pass. Read-only survey of `src/`, `python/`, `gym_envs/`,
`tools/`, `examples/viz/`, and `examples/config/` on `work/naval-mechanisms` at
`aa700d52`. The main thread re-verified the three decisive findings (dead
horizon gate, geometric constant, hard-coded EGI anchor) against the source.

## Summary

| Class | Count | Meaning |
| --- | --- | --- |
| `must-migrate` | 12 | result materially wrong at 100–500 km without curvature |
| `may-stay` | 30 | local-scale math; flat-frame error negligible |
| `out-of-scope` | 9 | viz-only, tooling, or owned by another package |
| gap | 1 | no scenario-level geodetic anchor exists |

Decisive findings:

1. **The maritime radar-horizon gate is dead code.** `default_sensor_model.cpp:256-273`
   limits at `max(sensor.max_range, horizon) + ducting`, but the preceding gate
   (`:250-253`) already rejects `dist > max_range + ducting`, so the horizon can
   never reject a contact. SPY-1D (185 km configured) detects surface ships about
   141 km past a 43.9 km 4/3-earth horizon.
2. **The horizon constant is geometric, not 4/3-effective.**
   `horizon_distance_m` (`:126-130`) is `3570·(√h1+√h2)` m, i.e. `√(2Rh)` with
   `R = 6371 km`. The standard 4/3 radio/radar horizon is `4120·(√h1+√h2)`; the
   geometric value is 13.4 % short. The data-link horizon
   (`src/systems/systems/data_link_system.h:48-52`) uses the same geometric
   constant and is the only horizon that actually limits anything today.
3. **No horizon or earth-bulge line of sight elsewhere.** Air/littoral radar,
   IR, visual, ESM, and missile seekers have only a 3-D range gate;
   `check_line_of_sight` checks terrain only. SLQ-32 ESM (220 km) reaches about
   6× past a 36 km surface horizon.
4. **Two unrelated implicit anchors.** EGI latitude/longitude
   (`src/systems/systems/navigation_system.h:9-13`) is a hard-coded Nellis AFB
   anchor with an equirectangular conversion (3.7 km error at 250 km east,
   14.4 km at 500 km). The Arnis exporter writes a WGS84 origin
   (`provenance.coordinate_system.origin_wgs84`, `bundle.bbox_wgs84`) that the
   Python importer validates and then drops. No scenario declares an anchor.
5. **Range and bearing can stay flat.** Flat vs great-circle range differs by
   ≤ 0.03 % at 500 km; grid bearings differ from true north by meridian
   convergence (1.65° at 250 km east, 36°N).

## Reference Values

`R = 6 371 000 m`; effective radius `Re = (4/3)R = 8 494 667 m`.

| Quantity | Formula | Values |
| --- | --- | --- |
| Geometric horizon | `d = √(2R·h) = 3.5696 km·√h[m]` | the code's `3570` / `3.57` constant |
| 4/3 effective horizon | `d = √(2Re·h) = 4.1218 km·√h[m]` | geometric / 4/3 = 0.866 |
| Two-ended horizon, 20 m vs 10 km | `K(√h1+√h2)` | 372.9 km geometric / 430.6 km 4/3 |
| Two-ended horizon, ship 30 m vs 30 m | same | 39.1 / 45.2 km |
| Two-ended horizon, SPY-1D 32 m vs 25 m bias | same | 38.0 / 43.9 km |
| Hidden height, 20 m antenna | `(d − √(2Re·h1))² / (2Re)` | 100 km: 392 m; 300 km: 4666 m; 500 km: 13 650 m (4/3) |
| Sea-level mid-path bulge | `d² / (8Re)` | 100 km: 147 m; 300 km: 1325 m; 500 km: 3679 m (4/3) |
| Tangent-plane drop | `R(1 − cos(s/R))` | 100 km: 785 m; 500 km: 19.6 km (4.5° vertical tilt) |
| Flat vs great-circle pair range | haversine of the azimuthal-equidistant inverse | 500 km pair 250 km off-anchor: +0.13 km (0.026 %) |
| Flat vs true elevation angle | `atan2(b·cosθ − a, b·sinθ)` | 300 km, 20 m → 10 km: 1.91° flat vs 0.55° true |
| Meridian convergence | `Δλ·sin φ` | 250 km east at 36°N: 1.65° |
| Sphere vs WGS-84 | radius of curvature 6335–6400 km | horizon ±0.28 %; smaller than the uncertainty in the refraction factor |

## Must-Migrate Sites

| Site | File:line | What it computes | Error at scale | Note |
| --- | --- | --- | --- | --- |
| Frame definition | `src/components/basic/common.h:103-108` | `Transform{x,y,z}` "local ENU relative to scenario origin" | strict tangent plane: 19.6 km height error at 500 km | define the frame as a map projection with `z` = height above the sphere; the struct can stay |
| EGI geodetic conversion | `src/systems/systems/navigation_system.h:9-13, 42-48` | lat/lon from a hard-coded Nellis anchor, equirectangular | 3.7 km at 250 km E; 14.4 km at 500 km E | only native ENU→geodetic conversion; ignores the scenario |
| Radar horizon helper | `src/models/systems/default_sensor_model.cpp:126-130` | `3570·(√h1+√h2)` | 13.4 % short of 4/3 | replace with the shared query |
| Radar horizon gate | `default_sensor_model.cpp:256-273` | `max(max_range, horizon) + ducting`, SurfaceMaritime only | never rejects (dead) | migration changes naval detection ranges sharply |
| Missing horizon, other sensors | `default_sensor_model.cpp:239-253` | 3-D range gate for air/littoral radar, IR, visual, ESM | e.g. 10 m radar vs 100 m target: 54 km horizon vs 100 km range | the range value is fine; the horizon/LOS gate is missing |
| ESM receiver | `default_sensor_model.cpp:179-213`; `src/components/systems/ew.h:45-47` | `dist ≤ max_detection_range_m` | SLQ-32 vs 30 m emitter: 35.6 km horizon vs 220 km | shares the scan loop; horizon block is radar-only |
| Terrain line of sight | `src/core/interfaces/environment_model.h:30-32`; `src/models/environment/default_environment_model.cpp:150-181` | terrain samples on a straight segment | no earth bulge (147 m / 1.3 km / 3.7 km at 100 / 300 / 500 km) | add a bulge term in the shared query |
| Sensor horizon configuration | `src/components/systems/sensor.h:16-20, 43-44, 51`; `src/content/unit_definition.h:47-55`; `src/content/unit_definition_loader.cpp:392` | `antenna_height_m`, `target_height_bias_m`, `enforce_radar_horizon` | — | retire or wrap the flag (`P3-A`) |
| Maritime target height | `src/models/domains/naval/naval_sensor_maritime_adapter.h:84-93` | target height = max(bias, 0.25·height_above_waterline) | a 30 m mast counts as 7.5 m | height semantics must be defined for the shared query |
| Missile seeker | `src/core/engine/simulation_kernel_weapon_release_service.cpp:647-686, 920-954`; gate `src/models/weapons/default_guidance_model.cpp:1403` | seeker lock `range ≤ seeker_lock_range` (30–60 km), horizon flag hard-coded off | 5 m skimmer vs 30 m mast: 31.8 km 4/3 horizon | covered once the scan gains a horizon with correct flags |
| Data-link horizon | `src/systems/systems/data_link_system.h:17-23, 40-52` | geometric `3.57(√h1+√h2)` km | 13.4 % short of 4/3 radio horizon | non-ship units at `z = 0` get `h = 0` |
| Arnis anchor propagation | `python/scenario/environment_substrate/importers/arnis_bundle.py:504-523, 1591-1594, 1906-1934` | validates projection id, keeps only local extent | — | carry the WGS84 origin into the scenario anchor (`P3-B`) |

Gap: no scenario-level geodetic anchor field exists anywhere in
`python/scenario/**` or `gym_envs/scenario_loader/**`; spawns are raw `x,y,z`.

## May-Stay Sites (grouped)

- Sensor range, SNR, burn-through, bearing, elevation, and flat track
  reconstruction (`default_sensor_model.cpp:100-115, 311-331, 389-436`;
  `src/systems/systems/track_manager_system.h:27-100`) — self-consistent in the
  grid frame; elevation must change together with the sensor if curved
  elevation is ever returned.
- RWR registration and observation (`default_sensor_model.cpp:154-177`;
  `simulation_kernel_observation_api.cpp:684-718`) — inherits the radar gate.
- Sonar range and bearing (`src/models/systems/default_acoustic_model.cpp`) —
  under 30 km.
- Naval weapon release range, guidance, seeker filters, fuze and effects
  geometry — under about 100 km of flight or metre scale.
- Ship station keeping, UNREP separation, base supply radius, embarked
  distance helper — local.
- Route and ILS spatial queries (`src/core/geometry/spatial_query_runtime.cpp`)
  — 128 m cross-track over a 500 km grid leg; needs the anchor only when
  waypoints are authored in latitude/longitude.
- Gravity and flight dynamics along `−z` — correct when `z` is height above the
  sphere.
- Terrain elevation, sun direction (environment-owned), GPU visual runtime
  (implements `IEnvironmentModel`; keep in sync), Python route, tasking, naval
  screen, reward, and observation helpers, wind conversion, substrate zone
  projection.
- Arnis exporter projection: local spherical Web Mercator, `R = 6 371 000 m`,
  origin at the bbox centre, both axes scaled by `cos φ0`. Fine for single tiles
  (fixture ±166 m); scale error 1.8 % at 250 km and 3.8 % at 500 km, so it must
  not be reused for theatre-scale scenarios.
- Latitude/longitude pass-throughs into instruments, observations, and
  bindings — carry the EGI error; values change when EGI is fixed (RL
  observation indices 24/25).

## Out-Of-Scope Sites

Ducting bonus (sensing/environment), command-link latency (no range gate
today), EW decoy spawning, viz anchor and tactical/3-D map rendering, Arnis CLI,
experimental GPU probes (duplicate `3.57` constant; update if kept), and
diagnostics tooling.

## Tests That Pin Flat-Frame Behavior

- `tests/runtime/naval/test_naval_sensor_realism_runtime.py:16-17` places naval
  tests about 1414 km from the origin; any enforced local-frame error bound
  must rely only on relative geometry or move these fixtures.
- Same file `:114-189` (ducting, expects detection at 50 km) will flip once the
  horizon binds: 4/3 limit ≈ 31.9 km + 16.2 km ducting = 48.1 km. How ducting
  composes with the horizon is a sensing decision.
- Same file `:36-112` ("horizon blocks") is actually blocked by `max_range`
  46.3 km and still passes after migration.
- `tests/scenario/test_environment_substrate_arnis_bundle.py:39, 460` pins the
  projection identifier; `tests/viz/test_strategic_scale_seeds.py:54-76` pins the
  bbox-midpoint anchor.
- `tests/runtime/core/test_scalar_helper_owners.py:148-198` and
  `tests/runtime/navigation/test_coarse_route_propagator.py` pin flat bearing and
  distance helpers bit-for-bit.
- No test pins the EGI Nellis latitude/longitude values.

## Implications For P2

- Keep range and bearing in the local frame; change horizon, line of sight,
  and the geodetic conversion.
- Define the simulation frame as a projection with `z` as height above the
  sphere, not a strict tangent plane.
- A spherical earth is sufficient for `P2`: sphere vs WGS-84 moves horizons by
  ≤ 0.3 %, far less than the uncertainty in the refraction factor.
- The horizon uses the 4/3 effective radius by default, with `k` declared as an
  input so sensing and environment can change it for ducting conditions.
- Expect a large naval regression in `P4`: SPY-1D surface detection falls from
  185 km to about 44 km. That is a correction, and it is recorded, not
  re-tuned.
