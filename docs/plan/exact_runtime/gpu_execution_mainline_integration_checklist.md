# GPU Execution Mainline Integration Checklist

Status: Open on 2026-04-18 after narrowing the maintained `p5` default back to
the compiled CPU-mainline visual path.
This is the live follow-on checklist for turning the closed Phase 0-4 GPU
runtime work into maintained execution-layer acceleration.
It is a GPU integration tracking checklist, not the general architecture
authority and not a substitute for a separately frozen task boundary when scope
needs to change.
The exact-step migration line is now split into
[gpu_exact_world_step_rearchitecture_plan.md](/home/void0312/Workshop/CMO/docs/plan/archive/gpu_exact_world_step_rearchitecture_plan.md),
which freezes the new "CPU truth source -> exact GPU backend" re-architecture.

## Scope

This checklist is intentionally narrower than the research/design document in
[gpu_execution_runtime_research_and_design.md](/home/void0312/Workshop/CMO/docs/plan/archive/gpu_execution_runtime_research_and_design.md).
It only tracks work needed to integrate GPU-assisted execution into:

- execution-layer `train.py` rollouts for the maintained post-freeze `p5` path
- frozen leader configs that depend on the maintained execution artifact
- maintained runtime boundaries in `ef_py`, `WorldBatchRuntime`, and
  `WorldBatchVecEnv`

Standalone probes and experimental APIs do not count as "mainline" by
themselves.

## What Counts As Mainline

For this repo, "mainline" means all of the following are true:

- the path is reachable from [train.py](/home/void0312/Workshop/CMO/train.py) without
  patching local code for each run
- the maintained execution configs can select it directly
- the path has a stable Python binding contract, not only a probe binary
- CPU fallback behavior remains correct on non-CUDA builds

The current maintained execution `p5` configs live under
[examples/config/training/frozen/execution](/home/void0312/Workshop/CMO/examples/config/training/frozen/execution).

## Current Snapshot

### Already Integrated At A Maintained Boundary

- [x] Optional CUDA build scaffolding exists in
  [CMakeLists.txt](/home/void0312/Workshop/CMO/CMakeLists.txt).
- [x] `train.py` prefers `build-gpu` when a CUDA-enabled `ef_py` module exists.
- [x] `WorldBatchVecEnv` can batch visual generation across worlds through
  `ef_py.compute_world_batch_visual_observation_batch_numpy(...)`.
- [x] `WorldBatchVecEnv` can batch execution observation packing through
  `ef_py.compute_execution_observation_batch_numpy(...)`.
- [x] The maintained post-freeze execution `p5` configs already expose a
  maintained world-batch path with:
  - `runtime.world_batch_vec_env=true`
  - `batch_observation_backend=compiled`
  - `batch_visual_backend=compiled`
  - `env.execution_step_runtime_mode=compiled`
- [x] The older mixed `gpu_host` visual lane and broader all-`gpu_host`
  observation/visual lanes remain reproducible only as explicit diagnostics,
  not as the maintained default.
- [x] `WorldBatchRuntime` exposes maintained broadphase helpers for sensor,
  visual, and comm candidate lists.
- [x] The world-batch visual helper already consumes the maintained visual
  candidate helper before scene collection.
- [x] `WorldBatchRuntime` exposes packed-flight extraction / apply / experiment
  stepping APIs for the Phase-4 packed-state path.

### Not Yet Mainline-Complete

- [ ] Single-world
  [UniversalEnv](/home/void0312/Workshop/CMO/gym_envs/universal_env.py) does not use the
  world-batch GPU helper path.
- [ ] Python training still carries host-side rollout storage / VecEnv
  compatibility overhead even though the maintained CUDA path now has
  DLPack-backed device export and rollout-inference consumption.
- [ ] GPU flight-shaping kernels are now integrated behind an explicit backend
  flag, but they are not yet promoted as the maintained default reward path.
- [ ] Mission / reward / termination evaluation remains CPU-side in
  [ScenarioLoader](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py).
- [ ] Live sensor and comm systems do not consume GPU broadphase or GPU narrow
  phase in the hot path.
- [ ] The maintained default `WorldBatchRuntime.step_batch()` path still
  relies on CPU `SimulationKernel::step()` semantics; the new exact cached
  first-scope backend remains explicit opt-in runtime research infrastructure,
  not a maintained rollout default.
- [ ] The Phase-4 packed-flight GPU step does not yet match the full exact ECS
  world-step semantics.

## Immediate Consistency Gaps

These should be cleaned up before further acceleration work, otherwise the repo
will keep carrying multiple incompatible ideas of what "current `p5`" means.

- [x] Active continuous artifact docs now separate the maintained execution
  config from the historical artifact-provenance config in
  [reference_artifacts.md](/home/void0312/Workshop/CMO/docs/reference_artifacts.md).
- [x] The maintained post-freeze execution docs point to
  [frozen/execution/p5_continuous_retrain_v1.json](/home/void0312/Workshop/CMO/examples/config/training/frozen/execution/p5_continuous_retrain_v1.json)
  and
  [frozen/execution/p5_continuous_coldstart_retrain_v2.json](/home/void0312/Workshop/CMO/examples/config/training/frozen/execution/p5_continuous_coldstart_retrain_v2.json).
- [x] Frozen leader configs now reference the maintained post-freeze execution
  `p5` config lineage instead of the historical top-level `p5` config.

Acceptance for this cleanup:

- one execution config lineage is marked as the maintained source of truth for
  `p5`
- docs and frozen leader dependencies either point to the same config, or
  explicitly document why they intentionally differ

## Integration Order

### 1. Baseline Hygiene

- [x] Choose one maintained execution `p5` config lineage and make the docs
  consistent.
- [x] Add an explicit note in the maintained config docs explaining why
  both maintained `p5` batch backends stay on `compiled` by default and why
  `gpu_host` remains benchmark-only.
- [x] Record the expected hardware/build matrix:
  - CPU-only build
  - CUDA build without available runtime device
  - CUDA build with available runtime device

Primary files:

- [docs/reference_artifacts.md](/home/void0312/Workshop/CMO/docs/reference_artifacts.md)
- [examples/config/training/frozen/execution/README.md](/home/void0312/Workshop/CMO/examples/config/training/frozen/execution/README.md)
- [examples/config/training/frozen/execution/p5_continuous_retrain_v1.json](/home/void0312/Workshop/CMO/examples/config/training/frozen/execution/p5_continuous_retrain_v1.json)
- [examples/config/training/frozen/execution/p5_continuous_coldstart_retrain_v2.json](/home/void0312/Workshop/CMO/examples/config/training/frozen/execution/p5_continuous_coldstart_retrain_v2.json)
- [examples/config/training/frozen/leader_c2_frozen_v1.json](/home/void0312/Workshop/CMO/examples/config/training/frozen/leader_c2_frozen_v1.json)
- [examples/config/training/frozen/leader_task_only_frozen_v1.json](/home/void0312/Workshop/CMO/examples/config/training/frozen/leader_task_only_frozen_v1.json)

### 2. Stabilize The Current GPU-Assisted CPU-Step Lane

This is the current highest-confidence production path:

- CPU exact stepping remains authoritative
- batch observation stays on the compiled CPU helper
- batch visual stays on the compiled CPU helper
- retained `gpu_host` helper experiments stay explicit opt-in only

Checklist:

- [x] Keep `WorldBatchVecEnv` as the maintained execution rollout backend for
  the post-freeze execution `p5` path.
- [x] Add a reproducible throughput benchmark for the maintained `p5` scenario
  covering:
  - legacy single-world path
  - world-batch compiled path
  - world-batch compiled path with `gpu_host` visual
- [x] Add run-time logging or benchmark output that records which visual backend
  was actually used and whether CUDA was available.

Primary files:

- [train.py](/home/void0312/Workshop/CMO/train.py)
- [python/rl/runtime/world_batch_vec_env.py](/home/void0312/Workshop/CMO/python/rl/runtime/world_batch_vec_env.py)
- [tools/diagnostics/benchmark.py](/home/void0312/Workshop/CMO/tools/diagnostics/benchmark.py)
- [tests/world_batch/test_world_batch_vec_env.py](/home/void0312/Workshop/CMO/tests/world_batch/test_world_batch_vec_env.py)

Acceptance:

- maintained `p5` rollout launches cleanly on both CPU-only and CUDA builds
- visual semantics remain within existing tolerance
- the maintained benchmark keeps experimental `gpu_host` comparisons explicit
  and shows whether any helper is actually worth re-enabling on target hardware

Notes:

- `train.py` now prints both requested and effective maintained world-batch
  visual/reward backend selections on the execution path.
- `benchmark.py --family world_batch_vec_env`
  records CUDA probe information plus requested/effective visual and
  observation backends for maintained `p5` scenario A/B runs.

### 3. Integrate GPU Flight Shaping Before Touching Exact World Step

This is the first missing GPU kernel that is both:

- already implemented at probe level
- numerically exact against the current reference
- more arithmetic-dense than observation packing

Checklist:

- [x] Add a maintained Python binding for batched GPU flight-shaping evaluation.
- [x] Thread that helper into the reward path in
  [ScenarioLoader](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py), behind an
  explicit backend flag.
- [x] Keep exact CPU reward semantics as the fallback and contract reference.
- [ ] Measure real end-to-end `p5` step improvement before promoting any new
  default.

Primary files:

- [src/gpu/gpu_flight_shaping_runtime.h](/home/void0312/Workshop/CMO/src/gpu/gpu_flight_shaping_runtime.h)
- [src/gpu/gpu_flight_shaping_runtime.cpp](/home/void0312/Workshop/CMO/src/gpu/gpu_flight_shaping_runtime.cpp)
- [src/gpu/gpu_flight_shaping_runtime_cuda.cu](/home/void0312/Workshop/CMO/src/gpu/gpu_flight_shaping_runtime_cuda.cu)
- [src/interfaces/python/python_module.cpp](/home/void0312/Workshop/CMO/src/interfaces/python/python_module.cpp)
- [gym_envs/scenario_loader.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py)
- [tests/runtime/test_mission_runtime.py](/home/void0312/Workshop/CMO/tests/runtime/test_mission_runtime.py)

Acceptance:

- reward totals remain numerically aligned with the current compiled runtime
- terminal / truncation behavior does not drift
- maintained `p5` benchmarks show a real step-time win at production batch sizes

### 4. Expose Device-Resident Outputs To The Learner

The current `gpu_host` path is structurally capped because the Python training
side still consumes host NumPy arrays.

Checklist:

- [x] Expose DLPack or an equivalent device tensor export for visual and
  observation outputs.
- [x] Add a rollout-inference path that can consume the current batch directly
  on CUDA for policy/value forward passes.
- [ ] Remove NumPy staging from rollout-buffer storage and learner update
  inputs end-to-end.
- [ ] Re-evaluate `batch_observation_backend=gpu_host` only after this zero-copy
  consumer path exists.

Primary files:

- [src/interfaces/python/python_module.cpp](/home/void0312/Workshop/CMO/src/interfaces/python/python_module.cpp)
- [src/gpu/gpu_visual_runtime.h](/home/void0312/Workshop/CMO/src/gpu/gpu_visual_runtime.h)
- [src/gpu/gpu_execution_observation_runtime.h](/home/void0312/Workshop/CMO/src/gpu/gpu_execution_observation_runtime.h)
- [python/models/transformer.py](/home/void0312/Workshop/CMO/python/models/transformer.py)
- [train.py](/home/void0312/Workshop/CMO/train.py)

Acceptance:

- current-rollout policy/value inference can consume learner-facing tensors on
  the CUDA path without a host round-trip
- full rollout-buffer storage still requires a later follow-on change
- CPU-only runs still work without code changes
- rollout and learner memory ownership is explicit and testable

Notes:

- The maintained CUDA training process must import `torch` before `ef_py` when
  both are used in the same process; the direct DLPack bridge now relies on
  that import order.
- `tools/diagnostics/benchmark.py --family policy_observation_bridge` is the
  maintained A/B harness for `bridge on/off` rollout comparison.
- That same harness now also records requested/effective
  `flight_shaping_backend` plus the latest visual/flight-shaping runtime stats,
  and supports a `--flight-shaping-backend` override for maintained `p5`-like
  A/B measurement.
- The next frozen follow-on for this phase is
  [gpu_execution_phase4_rollout_hot_path_freeze.md](/home/void0312/Workshop/CMO/docs/plan/exact_runtime/gpu_execution_phase4_rollout_hot_path_freeze.md),
  which isolates `WorldBatchVecEnv` host-copy semantics before any further
  default changes.
- Initial Phase 4C results from that freeze show `observation_return_mode=view`
  is valid and sometimes slightly faster, but the maintained `p5` gain
  collapses toward noise at larger batch sizes, so the maintained default
  stays `copy` for now.
- Current A/B runs after introducing a device-resident rollout buffer show a
  clearer split:
  - `collect_rollouts()` remains mixed to negative because the exact env step,
    action handoff, rewards/dones, and VecEnv compatibility path are still
    host-heavy.
  - `train()` becomes much faster because rollout minibatches no longer round
    trip through NumPy before each learner update.
  - As of the 2026-04-18 `p5` compare, the maintained default stays on the
    compiled visual path; the mixed `gpu_host` visual path remains a benchmark
    reference only because it is functional but slower on the current
    production workload.

### 5. Expand GPU Interaction Integration By Real Runtime Consumer

Phase 3 is available at the runtime boundary, but only visual currently has a
real maintained consumer.

Checklist:

- [ ] Decide whether sensor and comm should first use the maintained broadphase
  helper APIs, or skip directly to deeper live-system integration.
- [ ] Add one maintained sensor or comm call-site consumer before attempting any
  broader narrow-phase rewrite.
- [ ] Keep the exact "candidate superset, no misses" contract as the acceptance
  rule.

Primary files:

- [src/core/engine/world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.cpp)
- [src/gpu/gpu_interaction_broadphase_runtime.h](/home/void0312/Workshop/CMO/src/gpu/gpu_interaction_broadphase_runtime.h)
- [src/models/systems/default_sensor_model.cpp](/home/void0312/Workshop/CMO/src/models/systems/default_sensor_model.cpp)
- [tests/test_gpu_runtime_bindings.py](/home/void0312/Workshop/CMO/tests/test_gpu_runtime_bindings.py)

Acceptance:

- no true interaction is missed relative to the current reference path
- at least one maintained runtime consumer exists beyond visual

### 6. Keep Exact GPU World Stepping Separate Until Semantic Parity Exists

The current packed-flight GPU step is useful research infrastructure, but it is
not yet a drop-in replacement for exact `SimulationKernel::step()`.

Active exact-migration follow-on:

- [gpu_exact_world_step_migration_plan.md](/home/void0312/Workshop/CMO/docs/plan/archive/gpu_exact_world_step_migration_plan.md)
- Current status as of `2026-03-27`: the new re-architecture line has now
  reached exact cached-session parity for deterministic single-world,
  `world_count=4`, and `world_count=16` first-scope aircraft fixtures on the
  8-step fixed-seed sweep (`first_cpu_divergence_step=0`,
  `final_cached_component_digests_match=true`). The same `world_count=16`
  fixture now also matches through the explicit experimental
  `WorldBatchExactStepBackend` runtime-switch path
  (`--runtime-step-batch-backend`). `WorldBatchRuntime` still keeps that
  backend as an explicit opt-in experiment, and it remains outside the
  maintained `p5` default even though the broader batch gate is now closed.
  The latest lazy-sync follow-on also removes per-step live-world write-back
  from that experimental runtime path, and the newest `2026-03-27`
  resident-fast-path follow-on also removes in-step D2H materialization from
  the covered `step_batch()` body (`chain_device_to_host_ms == 0.0` before any
  explicit extract / live-world access). A later `2026-03-27` quiescent-path
  follow-on now also skips the CPU command-lane batch entirely for the current
  benchmark-style runtime-step fixture (`chain_command_lane_ms == 0.0` on the
  covered rows). The newest narrowing pass also swaps that path to a smaller
  resident `pilot + world_time` projection instead of cloning and repacking the
  whole cached state batch first. The latest `2026-03-27` no-missile follow-on
  then teaches the resident replay to skip the guidance counter memset, the
  guidance kernel launch, and the counter D2H copy entirely when the uploaded
  batch has no missile rows. A later `2026-03-27` quiescent follow-on then
  fuses that same `pilot + world_time` resident sync with the no-missile
  aircraft-only replay itself, collapsing the covered runtime-step hot path to
  one H2D copy plus one CUDA launch/sync. The latest matrix now reports warm
  runtime-step speedups of about `0.194x` at `world_count=1`, `0.197x` at
  `world_count=4`, and `0.583x` at `world_count=16`, with
  `chain_host_to_device_ms` down near `0.008-0.009 ms`, while warm write-back
  and `chain_command_lane_ms` stay at `0.0`. A follow-up stream conversion now
  also moves the resident CUDA carrier off `cudaDeviceSynchronize()` onto a
  dedicated cache stream with reusable timing events, but the fresh
  `world_count=1,4,16` matrix still settles around `0.096 ms`, `0.099 ms`, and
  `0.108 ms` warm runtime-step time with only `0.136x`, `0.190x`, and
  `0.439x` warm runtime-step speedup. The newest raw resident-projection
  follow-on then replaces the hot-path pageable projection vector with a
  reusable pinned host buffer, lets the no-missile graph reuse a fixed memcpy
  source without per-step node-param updates, and preallocates that buffer
  during upload so the first runtime step no longer absorbs a multi-second lazy
  allocation spike. The latest matrix now lands around `0.089 ms`, `0.092 ms`,
  and `0.100 ms` warm runtime-step time with warm chain totals near
  `0.077 ms`, `0.080 ms`, and `0.081 ms`, first-step cold cost back near
  `20.3 ms`, and approximate warm runtime-step speedups of `0.150x`,
  `0.200x`, and `0.571x`. The newest quiescent/no-missile resident follow-on
  now also advances `world_time_s` directly inside the device carrier so the
  covered hot path can skip projection H2D entirely, and a subsequent
  cached-graph pass recovers most of the added launch overhead from that first
  direct-kernel version. A stable rerun matrix now lands around `0.111 ms`,
  `0.096 ms`, and `0.099 ms` warm runtime-step time with warm chain totals near
  `0.078 ms`, `0.079 ms`, and `0.082 ms`, keeps warm write-back,
  `chain_command_lane_ms`, and `chain_host_to_device_ms` at `0.0`, and
  measures approximate warm runtime-step speedups of `0.121x`, `0.193x`, and
  `0.466x`. The experimental runtime path is still not promotion-ready: the
  remaining blockers are now more clearly runtime slowdown versus CPU and fixed
  replay/runtime-glue cost rather than write-back burden or H2D
  materialization.

Checklist:

- [ ] Do not wire `step_packed_flight_states_experiment_batch(...)` into the
  maintained exact `p5` path as a hidden replacement for
  `WorldBatchRuntime.step_batch()`.
- [ ] If exact GPU world stepping becomes a target, first define the exact state
  parity boundary against the current ECS simulation core.
- [ ] Only after that parity boundary is explicit should `WorldBatchRuntime`
  gain an optional GPU world-step backend.

Primary files:

- [src/core/engine/world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.cpp)
- [src/core/engine/simulation_kernel.cpp](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel.cpp)
- [src/core/engine/world_batch_runtime.h](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.h)
- [src/gpu/README.md](/home/void0312/Workshop/CMO/src/gpu/README.md)
- [src/gpu/experimental/README.md](/home/void0312/Workshop/CMO/src/gpu/experimental/README.md)
- [tests/test_gpu_runtime_bindings.py](/home/void0312/Workshop/CMO/tests/test_gpu_runtime_bindings.py)

Acceptance:

- fixed-seed equivalence exists against the exact ECS step, not only the packed
  Phase-4 reference
- rollback / fallback to the current CPU exact path remains trivial

## Recommended First Code Target

After the doc/config cleanup, the first actual acceleration integration target
should be:

1. GPU flight-shaping mainline integration
2. training-side device-resident tensor export
3. only then reconsider broader GPU observation defaults

This order matches the current evidence:

- visual already has a maintained runtime consumer
- observation `gpu_host` alone is not a strong production win at the current
  maintained batch sizes
- flight shaping is the next implemented kernel with real arithmetic density
- exact GPU world stepping still has a semantic gap against the ECS core

## Guardrails

- Do not replace the simulator with another engine.
- Do not promote probe-only binaries to "mainline complete" status.
- Do not switch maintained exact `p5` rollouts to the Phase-4 packed-flight step
  before exact parity exists.
- Do not spend more time optimizing host-readback observation packing before a
  zero-copy consumer path exists.
