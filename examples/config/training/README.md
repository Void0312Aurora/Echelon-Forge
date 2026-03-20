# Training Config Notes

This folder contains JSON configs consumed by [train.py](/home/void0312/CMO/train.py).

## Leader Performance Knobs

Leader-layer configs can reduce frozen execution-policy inference cost with:

- `leader_env.execution_action_repeat`
  - Reuses one low-level execution action for multiple 60 Hz simulation steps.
  - `1` means predict every low-level step.
  - `2` means one prediction is reused for two low-level steps.
  - Larger values improve throughput but reduce low-level control bandwidth.

This knob is implemented in [leader_env.py](/home/void0312/CMO/gym_envs/leader_env.py) and is reported by [leader_perf_probe.py](/home/void0312/CMO/tools/leader_perf_probe.py).

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

- `runtime.batched_execution_inference`
  - Keeps the older experimental single-process batched leader inference path.
  - This is still available for investigation, but it has historically measured worse wall-clock FPS than multi-process env stepping.

## Useful Probes

- Leader throughput:

```bash
./.venv/bin/python tools/leader_perf_probe.py \
  --scenario scenarios/takeoff/takeoff.json \
  --train_config examples/config/training/p7_leader_layer_c2_reporting_generalization_fast_v1.json \
  --n_envs 4 \
  --leader_steps 32 \
  --vec_backend subproc
```

- Leader throughput with shared-memory vec env:

```bash
./.venv/bin/python tools/leader_perf_probe.py \
  --scenario scenarios/takeoff/takeoff.json \
  --train_config examples/config/training/p7_leader_layer_c2_reporting_generalization_fast_v1.json \
  --n_envs 4 \
  --leader_steps 32 \
  --vec_backend shared
```

- Visual downsample sweep:

```bash
./.venv/bin/python tools/diagnostics/benchmark_visual_resolution.py --help
```
