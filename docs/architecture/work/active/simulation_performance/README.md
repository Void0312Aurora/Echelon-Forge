# Simulation Performance

Status: `2026-10-01` in progress on `work/simulation-performance` (base `e1e077cb`,
local commits only, nothing pushed to origin). The detection mechanism and the first native
step-path optimizations are landed and measured. Work then fanned out into three directions
on their own branches (native simulation, RL training loop, CUDA kernels), each merged back
after verification.

Language:
- English canonical: `README.md`
- Chinese companion: not required yet; high-churn implementation slice (English-only).

Document kind: `task`
Lifecycle: `active`
Canonical: `docs/architecture/work/active/simulation_performance/README.md`
Owner: `architecture/performance`
Last verified: `2026-10-01`

Inputs:

- [Architecture and performance research follow-up](../../issues/architecture_and_performance_research_followup.md)
  (draft research snapshot; this package supplies the fresh evidence it asks for).
- [Diagnostics tools](../../../../../tools/diagnostics/README.md), which hold the benchmark family.

## Detection Mechanism

`native_world_batch_step` is a benchmark family under `tools/diagnostics/benchmarks/`. It
drives `ef_py.WorldBatchRuntime` directly over a worlds × units × threads sweep and reports
the following for each case:

- wall ms per batch step and world-steps per second;
- process CPU / wall (cores the process actually kept busy);
- **worker-pool occupancy** = busy thread time / (dispatch wall × participating threads),
  read from the native `WorldBatchRuntime.worker_pool_stats()`;
- with `--system-timing`, per-system Flecs time shares from the diagnostics-only
  `set_system_timing_enabled()` / `system_timings()` (off on the maintained path).

`--baseline <json> --max-regression <fraction>` compares a run case-by-case against a saved
one and exits 2 on a throughput loss, so a change can be gated on it. The suite
`examples/config/diagnostics/benchmark_suite_native_world_batch_occupancy.json` bundles the
scaling sweep and the single-thread system profile. On builds that predate the native
diagnostics the family degrades to throughput only, so it A/B-compares against old trees.

## Landed

| Commit | Change | Behaviour |
| --- | --- | --- |
| `8b943d39` | Persistent `WorldBatchWorkerPool` replaces per-call `std::thread` spawn/join in every batch operation; occupancy accounting | Same chunk-to-thread mapping and first-exception propagation; nested, concurrent or post-`fork()` dispatch runs inline |
| `8d7f4a78` | `native_world_batch_step` benchmark, registry entry, suite config, READMEs | Diagnostics only |
| `31eb6579` | Air-damage component classification split into pure classifiers, memoized per thread | Bit-identical; `aircraft_damage_derivation` suite diffs it against a verbatim copy of the old derivation |
| `9b3bcb5d` | RWR_Reset / MAWS_Update compile their missile query once per world | Same uncached query, same iteration order |
| `2ee59a7e` | Air-combat reward enable scans fetch the reward/meta config once | Same meta-first lookup and float coercion |

Fan-out branches, merged into `work/simulation-performance`:

| Direction | Commit | Change | Behaviour |
| --- | --- | --- | --- |
| RL training | `4426cffc` | Tasking-profile resolution memoized by candidate value (only `None`, `str`, `ServiceProfile`); live loader state still read every call | Rollout fingerprint identical; reassignment contract test |
| RL training | `16316d08` | Reward implicit-enable scans skip keys absent from the config | Rollout fingerprint identical; enable-semantics test |
| RL training | `e30e3416` | Command-chain change snapshots read all fields with one cached `attrgetter` | Falls back to the per-field loop on any missing attribute |
| RL training | `09bccca9` | Tasking adapter proxies read `sys.modules` before `import_module` | Laziness unchanged |
| RL training | `0c968e79` | Per-env step evaluation reuses the batch-built mission observation inputs | Python-owned modes still rebuild; bit-identical test |
| RL training | `25e48ab7` | `world_batch_vec_env --rollout-fingerprint`: SHA-1 over obs/reward/done/info | Diagnostics only |
| Native sim | `0014b413` | Structural breakup evaluation reuses precomputed component keys (no per-lookup `std::string`) | Same 51 lookups, order and thresholds |
| Native sim | `c41bb46b` | ResupplyLogic / NavalUnderwayResupply compile their provider query once per world | Same uncached query |
| CUDA | `e7b266b0`, `02c30102` | `ef_cuda_resident_window_probe` (window wall time, nsys/ncu target) with a bit-exact `--digest` over resident state | Diagnostics only |
| CUDA | `29d9e7a7` | `window_commit_body_kernel` block size derived from the occupancy API (smallest whole-warp block at maximum residency; 32 on RTX 3090) instead of a fixed 128 | Digest identical to the fixed-128 build at 1–65536 worlds |

## Evidence

The measurements below come from HEI, a Release build with GCC 13.3, 88 cores, and the
F-16C_Block50 in opposing pairs at dt 0.05 s. The host is a shared desktop, so the numbers
come from interleaved A/B rounds. The results are in `~/sim_perf_results/` on HEI.

Cumulative `9b3bcb5d` against `e1e077cb`, in world-steps/s:

| Worlds × units | 1 thread | 8 threads | 16 threads | 32 threads |
| --- | --- | --- | --- | --- |
| 1 × 2 | 9.4k → 16.2k (×1.72) | — | — | — |
| 8 × 2 | 10.2k → 15.1k (×1.49) | 15.9k → 57.3k (×3.60) | 15.8k → 70.0k (×4.42) | 16.1k → 41.2k (×2.56) |
| 32 × 2 | 9.7k → 13.8k (×1.42) | 37.2k → 92.1k (×2.48) | 35.7k → 109.7k (×3.08) | 21.0k → 155.1k (×7.38) |
| 64 × 2 | 9.8k → 14.8k (×1.52) | 45.8k → 94.3k (×2.06) | 38.5k → 165.7k (×4.30) | 24.5k → 196.5k (×8.02) |
| 64 × 8 | 3.1k → 6.2k (×1.99) | 22.3k → 38.8k (×1.74) | 33.7k → 56.4k (×1.67) | 32.6k → 86.9k (×2.67) |

Before the pool, adding threads beyond about 16 made batches slower. At 32 worlds × 2 units,
32 threads ran at 14% CPU utilization because thread creation dominated. Pool occupancy is
now 70–95% across the sweep.

At 32 worlds × 2 units on one thread, the per-system share of
`AircraftDamageStateUpdate` fell from 40% to 20%. The remaining top systems are
`StructuralFailureUpdate` (10–15%), `RWR_Reset`, `FlightControl` and `UpdateInstruments`.

Verification at `9b3bcb5d`:

- `ef_test` passes 197/197.
- The `tests/architecture` + `tests/world_batch` red set and the `tests/runtime/air_combat`
  red set are identical to `e1e077cb`: 29 and 6 pre-existing reds, none added.

Fan-out evidence (HEI, interleaved A/B, shared host):

- RL training loop, `world_batch_vec_env` 32 envs × 16 threads: 0.69–0.72 → 0.61–0.64
  ms/env-step. By segment: reward/info 0.15 → 0.13, observation build 0.20 → 0.17–0.18,
  behavior update 0.15 → 0.135, command sync 0.115 → 0.10. The rollout fingerprint matches
  `2ee59a7e` for takeoff and for the air-combat 1v1 C2-ROE scenario (checked independently
  by the main thread), and for a waypoint/C2 and a naval scenario (checked by the agent).
- Native simulation, 32 worlds, 1 thread: the `StructuralFailureUpdate` share fell from
  10.8–11.4% to 7.8–8.4% at 2 units per world, and from 15.8–16.4% to 10.7–11.0% at 8. The
  wall-time change stays inside host noise.
- CUDA resident backend (RTX 3090, nvcc 12.0, host g++-12), body-kernel median from nsys:
  - 256 worlds: 85.9 → 60.1 µs.
  - 4096 worlds: 86.6 → 63.8 µs. ncu: 32 × 128 → 128 × 32 grid, SM throughput 28.5 → 38.1%.
  - 16384 worlds: −13%.
  - 16 and 65536 worlds: unchanged.
  - Window wall time is set by host transfers and syncs (about 130 µs per window at 1–16
    worlds) and did not move.

CUDA build recipe on HEI: `-DEF_ENABLE_CUDA_EXPERIMENTS=ON -DEF_ENABLE_CUDA_RESIDENT_BACKEND=ON
-DCMAKE_CUDA_ARCHITECTURES=86 -DCMAKE_CUDA_COMPILER=/usr/bin/nvcc
-DCMAKE_CUDA_HOST_COMPILER=/usr/bin/g++-12`, plus the usual dependency and constexpr flags.
`ncu` and `nsys` live in `/usr/local/cuda/bin` (`sudo -n ncu` works).

## Open

1. **Native: `AircraftDamageStateUpdate` is again the top system** (23% of the step at 2
   units, 36% at 8). In `derive_aircraft_damage_from_component_state`, three string-keyed map
   lookups per component (system, redundancy group, group availability) cost about 25% of
   the step. Proposed fix: a non-serialized per-component cache of map-node pointers, rebuilt
   when the component topology changes. It needs its own differential test.
2. **Native: sensor and acoustic models still build a query on every scan**
   (`default_sensor_model.cpp`, `default_acoustic_model.cpp`, about 5% at 2 units). The
   models are per kernel, so the fix is to register the query in `SensorSystem` /
   `SonarSystem` and pass it to `scan()`. That changes the `ISensorModel` / `IAcousticModel`
   interface.
3. **Native: per-entity `e.get_mut<>()` lookups** in the damage and flight-control systems
   (`ecs_get_id` + `ecs_map_get_deref_` about 12% inclusive).
4. **RL: leader `update` re-resolves the same candidate lists 2–3 times per step**
   (about 1.3 s per 96 steps × 32 envs). This needs one shared per-step resolution.
   `ScenarioLoader.__getattr__` (184k calls) needs a change to loader ownership that the
   architecture gates cover. Also per-step `deepcopy(buf_infos)` and the flight-shaping
   config re-read.
5. **CUDA: host overhead sets the floor.** Each window does 3 whole-slot D2D copies, 3 syncs
   and 3 status reads. Merging stages into one sync changes the transfer ledger pinned in
   `cuda_resident_performance_contract.h`, so it needs a contract decision first. The full
   grid is FP64-bound; FMA contraction would gain up to about 14% but breaks CPU bit-parity.
   The fixed-air fixture goes non-finite after 17–31 windows at dt 0.125 s, which is a model
   limit.
