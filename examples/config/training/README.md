# Training Config Notes

This folder contains the maintained JSON configs consumed by [train.py](/home/void0312/CMO/train.py).

## Maintained Surface

- [default_ppo.json](/home/void0312/CMO/examples/config/training/default_ppo.json)
  - Minimal generic fallback used by `train.py --train_config` when no config is provided.
- [curriculum/](/home/void0312/CMO/examples/config/training/curriculum)
  - Reusable curriculum/randomization snippets.
- [frozen/](/home/void0312/CMO/examples/config/training/frozen/README.md)
  - Maintained post-freeze leader and execution-layer training entry points.

Avoid adding ad hoc experiment JSON files directly under this directory. New maintained runs should go under `frozen/` or a deliberately named active subdirectory with a README that explains ownership and acceptance criteria.

## Frozen Baseline

The maintained leader-layer entry points now live under [frozen](/home/void0312/CMO/examples/config/training/frozen/README.md).

- Use [leader_task_only_frozen_v1.json](/home/void0312/CMO/examples/config/training/frozen/leader_task_only_frozen_v1.json) for task-only/common-core leader runs.
- Use [leader_c2_frozen_v1.json](/home/void0312/CMO/examples/config/training/frozen/leader_c2_frozen_v1.json) for reporting/full-chain leader runs.
- Use [leader_task_only_retrain_v1.json](/home/void0312/CMO/examples/config/training/frozen/leader_task_only_retrain_v1.json) and [leader_c2_retrain_v1.json](/home/void0312/CMO/examples/config/training/frozen/leader_c2_retrain_v1.json) for the new post-freeze retraining line.
- Both configs point directly at the frozen execution artifact under `experiments/_archive_20260322_test_results/...` rather than relying on historical path remapping.

## Archive

Historical configs are retained under [examples/config/Archive/training](/home/void0312/CMO/examples/config/Archive/training) for provenance only:

- [pre_freeze_experiments](/home/void0312/CMO/examples/config/Archive/training/pre_freeze_experiments/README.md)
  - Older root-level `p2/p3/p4/p5`, takeoff-departure, and transformer experiment configs.
- [leader_legacy](/home/void0312/CMO/examples/config/Archive/training/leader_legacy/README.md)
  - Historical `p6_*/p7_*` leader-layer configs.

Archived configs are not maintained training entry points. If one needs to be revived, copy it into a maintained active directory and update its scenario pairing, runtime assumptions, and acceptance target.

## Leader Performance Knobs

Leader-layer configs can reduce frozen execution-policy inference cost with:

- `leader_env.execution_action_repeat`
  - Reuses one low-level execution action for multiple 60 Hz simulation steps.
  - `1` means predict every low-level step.
  - `2` means one prediction is reused for two low-level steps.
  - Larger values improve throughput but reduce low-level control bandwidth.

This knob is implemented in [leader_env.py](/home/void0312/CMO/gym_envs/leader_env.py) and is reported by [leader_perf_probe.py](/home/void0312/CMO/tools/diagnostics/leader_perf_probe.py).

## Visual Performance Knobs

Execution-layer configs can reduce ARB observation cost with:

- `env.visual_downsample`
  - Changes the ARB render resolution directly.
  - This is not "render native resolution and average-pool afterward".
  - Native ARB is `48x96x10`.
  - `visual_downsample=2` renders `24x48x10`.
  - `visual_downsample=4` renders `12x24x10`.

- `env.visual_update_interval`
  - Reuses the previous visual tensor between refreshes.
  - This reduces visual generation frequency, but it is separate from render resolution.

The direct low-resolution render path is implemented in [simulation_kernel.cpp](/home/void0312/CMO/src/core/engine/simulation_kernel.cpp) and [visual_system.h](/home/void0312/CMO/src/systems/visual/visual_system.h).

## Runtime Parallelism

Training runtime config also supports:

- `runtime.shared_memory_vec_env`
  - Uses [shared_memory_vec_env.py](/home/void0312/CMO/python/rl/shared_memory_vec_env.py) instead of standard `SubprocVecEnv` when `n_envs > 1`.
  - Worker processes write observations into parent-owned shared memory.
  - Pipe traffic is reduced to reward/done/info/reset metadata, which avoids large per-step observation serialization costs.

- `runtime.world_batch_vec_env`
  - Uses [world_batch_vec_env.py](/home/void0312/CMO/python/rl/world_batch_vec_env.py) for execution-layer training instead of `DummyVecEnv`/`SubprocVecEnv`.
  - This routes execution rollouts through one `ef_py.WorldBatchRuntime`, so stepping and readback use batch C++ APIs instead of per-env Python loops.
  - The maintained post-freeze execution `p5` configs now use this path with
    `batch_observation_backend=compiled` and `batch_visual_backend=compiled`.
  - Maintained baseline: exact world stepping remains CPU
    `SimulationKernel::step()`. The retained `gpu_host/fullgpu` helper line is
    now benchmark-only and no longer part of the default execution path.

- `runtime.world_batch_threads`
  - Controls `ef_py.WorldBatchRuntime.set_worker_threads()`.
  - Default is `1`.
  - Use `0` only if you explicitly want auto mode.
  - Current Phase 4 benchmark on this codebase shows that aggressive intra-runtime threading can be slower than `1`, because a single world step is still too cheap relative to thread scheduling overhead.
  - If you added more CPU, the safer first move is usually increasing `n_envs`; treat `world_batch_threads` as a measured tuning knob, not a “more is always faster” switch.

- The earlier single-process batched/shared-runtime leader route is no longer the maintained baseline in this repo.
  - Use [leader_perf_probe.py](/home/void0312/CMO/tools/diagnostics/leader_perf_probe.py) to compare the maintained `subproc`, `shared`, and `dummy` backends instead of relying on the old experimental flags.

## Useful Probes

- Leader throughput:

```bash
./.venv/bin/python tools/diagnostics/leader_perf_probe.py \
  --scenario scenarios/takeoff/takeoff.json \
  --train_config examples/config/training/frozen/leader_c2_frozen_v1.json \
  --n_envs 4 \
  --leader_steps 32 \
  --vec_backend subproc
```

- Leader throughput with shared-memory vec env:

```bash
./.venv/bin/python tools/diagnostics/leader_perf_probe.py \
  --scenario scenarios/takeoff/takeoff.json \
  --train_config examples/config/training/frozen/leader_c2_frozen_v1.json \
  --n_envs 4 \
  --leader_steps 32 \
  --vec_backend shared
```

- Visual downsample sweep:

```bash
./.venv/bin/python tools/diagnostics/benchmark_visual_resolution.py --help
```

- Phase 4 execution batch-runtime rollout benchmark:

```bash
./.venv/bin/python tools/diagnostics/benchmark_world_batch_vec_env_phase4.py \
  --scenario scenarios/combined/takeoff_to_landing_continuous_train_v1.json \
  --n-envs 8 \
  --steps 128 \
  --mission-obs-mode nav_v2
```

- Phase 4 maintained `p5` mainline bridge benchmark:

```bash
./.venv/bin/python tools/diagnostics/benchmark_policy_observation_bridge_phase4.py \
  --case p5like_visual_mainline \
  --n-envs 8 \
  --rollout-steps 64 \
  --rollout-repeats 2 \
  --flight-shaping-backend compiled

./.venv/bin/python tools/diagnostics/benchmark_policy_observation_bridge_phase4.py \
  --case experimental_p5like_visual_gpuhost_visual \
  --allow-experimental \
  --n-envs 8 \
  --rollout-steps 64 \
  --rollout-repeats 2 \
  --flight-shaping-backend compiled
```

- Phase 4 retained experimental helper A/B benchmark:

```bash
./.venv/bin/python tools/diagnostics/benchmark_policy_observation_bridge_phase4.py \
  --case experimental_p5like_visual_all_gpuhost \
  --allow-experimental \
  --n-envs 8 \
  --rollout-steps 64 \
  --rollout-repeats 2 \
  --flight-shaping-backend gpu_host
```
