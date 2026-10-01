# Simulation Performance

Status: `2026-10-01` in progress on `work/simulation-performance` (base `e1e077cb`,
local commits only, nothing pushed to origin). The detection mechanism and three native
step-path optimizations are landed and measured. The Python orchestration path is the
next target.

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

## Open

1. **Python orchestration dominates training throughput.** `world_batch_vec_env` at 32 envs
   and 16 threads spends 0.91 ms per env-step, of which the native batch step is 0.026 ms.
   The rest is reward/info (0.28), observation build (0.25), behavior update (0.18) and
   command sync (0.15). The native gains above therefore do not reach the RL loop yet. The
   cProfile hotspots are the per-step reward-config accessors in
   `gym_envs/scenario_loader/reward_runtime/air_combat.py` (`_cfg_value` and `_loader_cfg`,
   called 310k times in 96 steps) and tasking-profile resolution in
   `python/rl/tasking/bridge.py`.
2. `StructuralFailureUpdate` builds a `std::string` per component lookup in
   `structural_failure::component_failed_at` (about 37 lookups per aircraft per step).
3. Other per-step ad-hoc queries remain in the sensor and acoustic models, logistics, and
   naval logistics. The sensor and acoustic models are owned per kernel, so a cached query
   needs a world-scoped owner.
