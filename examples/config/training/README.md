# Training Config Notes

This folder contains the maintained JSON configs consumed by [train.py](../../../train.py).

Status taxonomy used by the training config entry surface:

- `Authoritative`
  - The default maintained starting point for a config family.
- `Active Mainline`
  - Maintained in-progress configs that define the current forward-moving training lanes.
- `Frozen Baseline`
  - Maintained stable configs preserved for reproducible post-freeze training and validation.
- `Compatibility`
  - Maintained bridge configs kept only to preserve a current contract or workflow shape while still avoiding direct archive dependencies.
- `Archived`
  - Historical configs retained only for provenance, result lookup, or lineage review.

## Maintained Surface

- [default_ppo.json](default_ppo.json)
  - `Authoritative` minimal generic fallback used by `train.py --train_config` when no config is provided.
- [curriculum/](curriculum)
  - `Authoritative` reusable curriculum/randomization snippets.
- [frozen/](frozen/README.md)
  - `Frozen Baseline` maintained post-freeze leader and execution-layer training entry points. These are not the current forward-moving training mainline.
- [active/](active/README.md)
  - `Active Mainline` maintained in-progress training entries across the cooperative flight/combined, air-combat `1v1`, and naval `N4` smoke/probe lanes.

Avoid adding ad hoc experiment JSON files directly under this directory. New maintained runs should go under `frozen/` or a deliberately named active subdirectory with a README that explains ownership and acceptance criteria.

## Frozen Baseline

The maintained frozen baselines now live under [frozen](frozen/README.md).

- Use [leader_task_only_frozen_v1.json](frozen/leader_task_only_frozen_v1.json) for task-only/common-core leader runs.
- Use [leader_c2_frozen_v1.json](frozen/leader_c2_frozen_v1.json) for reporting/full-chain leader runs.
- Use [leader_task_only_retrain_v1.json](frozen/leader_task_only_retrain_v1.json) and [leader_c2_retrain_v1.json](frozen/leader_c2_retrain_v1.json) for the frozen retraining line.
- Both configs point directly at the frozen execution artifact under `experiments/_archive_20260322_test_results/...` rather than relying on historical path remapping.

## Archive

Historical configs are retained under [examples/config/Archive/training](../Archive/training) for provenance only:

- [pre_freeze_experiments](../Archive/training/pre_freeze_experiments/README.md)
  - Older root-level `p2/p3/p4/p5`, takeoff-departure, and transformer experiment configs.
- [leader_legacy](../Archive/training/leader_legacy/README.md)
  - Historical `p6_*/p7_*` leader-layer configs.

## Current Forward Lines

- [active/](active/README.md)
  - Current in-progress entries cover cooperative flight/combined routes, air-combat `1v1` HMoE probes, and naval `N4` pre-fire runtime gates.
  - Ground is not an active RL training line yet. Maintained ground evidence is limited to tasking/native-schema bootstrap coverage while movement, terrain, sensing, fires, damage, and full ground runtime behavior remain held.

- Cooperative HMoE control script:
  - [run_hmoe_cooperative_takeoff_to_cruise_control.sh](../../../scripts/run_hmoe_cooperative_takeoff_to_cruise_control.sh)
  - Runs the paired shared-vs-HMoE cooperative takeoff-to-cruise control line using the `*_shared_fair_v1` and `*_hmoe_fair_v1` configs.

Archived configs are not maintained training entry points. If one needs to be revived, copy it into a maintained active directory and update its scenario pairing, runtime assumptions, and acceptance target.

Maintained docs, contracts, and bridge entry points should not point directly at `examples/config/Archive/**`. If an older behavior must stay reachable, promote or preserve a maintained `Frozen Baseline` or `Compatibility` config outside `Archive` first.

## Leader Performance Knobs

Leader-layer configs can reduce frozen execution-policy inference cost with:

- `leader_env.execution_action_repeat`
  - Reuses one low-level execution action for multiple 60 Hz simulation steps.
  - `1` means predict every low-level step.
  - `2` means one prediction is reused for two low-level steps.
  - Larger values improve throughput but reduce low-level control bandwidth.

This knob is implemented in [leader_env.py](../../../gym_envs/leader_env.py) and is reported by [leader_perf_probe.py](../../../tools/diagnostics/leader_perf_probe.py).

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

The direct low-resolution render path is implemented in [simulation_kernel.cpp](../../../src/core/engine/simulation_kernel.cpp) and [visual_system.h](../../../src/systems/visual/visual_system.h).

## Runtime Parallelism

Training runtime config also supports:

- `runtime.shared_memory_vec_env`
  - Uses [shared_memory_vec_env.py](../../../python/rl/runtime/shared_memory_vec_env.py) instead of standard `SubprocVecEnv` when `n_envs > 1`.
  - Worker processes write observations into parent-owned shared memory.
  - Pipe traffic is reduced to reward/done/info/reset metadata, which avoids large per-step observation serialization costs.

- `runtime.world_batch_vec_env`
  - Uses [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py) for execution-layer training instead of `DummyVecEnv`/`SubprocVecEnv`.
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
  - Use [leader_perf_probe.py](../../../tools/diagnostics/leader_perf_probe.py) to compare the maintained `subproc`, `shared`, and `dummy` backends instead of relying on the old experimental flags.

## Useful Probes

- Training-time non-finite probe:
  - `train.py` supports an opt-in runtime non-finite tensor probe via
    `--nonfinite_probe`.
  - When enabled, the maintained PPO training path records rollout, feature,
    latent, action-head, loss, gradient, and post-step parameter finite checks
    and aborts on the first `NaN/Inf`, writing a JSON report.
  - Use `--nonfinite_probe_report <path>` to override the default report
    location inside the experiment directory.
  - The probe is intended for unstable runs that need exact failure capture; it
    is not the default training path.

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
./.venv/bin/python tools/diagnostics/benchmark.py --family visual_resolution --family-help
```

- Phase 4 execution batch-runtime rollout benchmark:

```bash
./.venv/bin/python tools/diagnostics/benchmark.py --family world_batch_vec_env -- \
  --scenario scenarios/combined/takeoff_to_landing_continuous_train_v1.json \
  --n-envs 8 \
  --steps 128 \
  --mission-obs-mode nav_v2
```

- Phase 4 maintained `p5` mainline bridge benchmark:

```bash
./.venv/bin/python tools/diagnostics/benchmark.py --family policy_observation_bridge -- \
  --case p5like_visual_mainline \
  --n-envs 8 \
  --rollout-steps 64 \
  --rollout-repeats 2 \
  --flight-shaping-backend compiled

./.venv/bin/python tools/diagnostics/benchmark.py --family policy_observation_bridge -- \
  --case experimental_p5like_visual_gpuhost_visual \
  --allow-experimental \
  --n-envs 8 \
  --rollout-steps 64 \
  --rollout-repeats 2 \
  --flight-shaping-backend compiled
```

- Phase 4 retained experimental helper A/B benchmark:

```bash
./.venv/bin/python tools/diagnostics/benchmark.py --family policy_observation_bridge -- \
  --case experimental_p5like_visual_all_gpuhost \
  --allow-experimental \
  --n-envs 8 \
  --rollout-steps 64 \
  --rollout-repeats 2 \
  --flight-shaping-backend gpu_host
```
