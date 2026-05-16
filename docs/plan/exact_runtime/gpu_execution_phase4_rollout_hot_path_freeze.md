# GPU Execution Phase 4C: Rollout Hot Path Freeze

Status: frozen execution plan for the next maintained Phase 4 follow-on.

Historical note on 2026-04-18:
this document records the then-current mixed `p5` helper lane. The maintained
`p5` default has since been narrowed back to `batch_visual_backend=compiled`,
and any `gpu_host/fullgpu` references here should be read as historical
benchmark context rather than the current mainline.

Related:

- [gpu_execution_mainline_integration_checklist.md](/home/void0312/Workshop/CMO/docs/plan/exact_runtime/gpu_execution_mainline_integration_checklist.md)
- [gpu_execution_runtime_research_and_design.md](/home/void0312/Workshop/CMO/docs/plan/archive/gpu_execution_runtime_research_and_design.md)
- [tools/diagnostics/benchmark.py](/home/void0312/Workshop/CMO/tools/diagnostics/benchmark.py)

## Current Baseline

The earlier Phase 4 assumption is now outdated in one important way:

- `AdaptiveKLPPO` already has a maintained CUDA rollout path.
- [device_dict_rollout_buffer.py](/home/void0312/Workshop/CMO/python/rl/policy_algo/device_dict_rollout_buffer.py) already stores dict rollout tensors on device.
- [ppo_adaptive_kl.py](/home/void0312/Workshop/CMO/python/rl/policy_algo/ppo_adaptive_kl.py) already uses the device buffer automatically when the CUDA observation bridge is active.
- The CUDA bridge therefore already removes the learner-side NumPy round trip for rollout minibatches.

Current benchmark evidence shows the split clearly:

- `train()` improves materially once device-resident minibatches are used.
- `collect_rollouts()` remains mixed to negative.
- The maintained `p5` path therefore still has a rollout-side hot path bottleneck even after the learner-side device buffer exists.

## Research Finding

The next constrained bottleneck is the host observation return contract in
[world_batch_vec_env.py](/home/void0312/Workshop/CMO/python/rl/runtime/world_batch_vec_env.py).

Today the maintained adapter still does this on every `reset()` and `step()`:

- `_obs_from_buf()` returns `deepcopy(self.buf_obs)`
- `step_wait()` returns `deepcopy(self.buf_infos)`

The observation deep copy is especially suspicious because:

- `WorldBatchVecEnv` is single-process and already owns `buf_obs`.
- The maintained CUDA bridge reads directly from `buf_obs` anyway.
- The sibling adapter [shared_memory_vec_env.py](/home/void0312/Workshop/CMO/python/rl/runtime/shared_memory_vec_env.py) already returns shared observation views instead of deep-copying observations.
- Terminal observations still need explicit copies, but the ordinary step/reset return path does not obviously need them.

## Scope

This freeze covers only the maintained rollout hot path.

In scope:

- observation return semantics for `WorldBatchVecEnv.reset()` and `WorldBatchVecEnv.step()`
- maintained training/runtime config plumbing for that behavior
- regression tests for shared-view safety boundaries
- throughput measurement on maintained `p5`-like cases

Out of scope:

- exact GPU world stepping
- reward/runtime semantic rewrites
- deep GPU integration of sensor or comm systems
- changing terminal observation ownership semantics

## Frozen Task List

- [x] Add an explicit maintained observation-return mode for `WorldBatchVecEnv`.
  Allowed values: `copy`, `view`.
  Compatibility default stays `copy`.
  Terminal observations remain copied in both modes.

- [x] Thread the observation-return mode through the maintained training/runtime entry points.
  Landed in [train.py](/home/void0312/Workshop/CMO/train.py) and
  `benchmark.py --family policy_observation_bridge`.

- [x] Lock regression coverage before any default change.
  Landed in [test_world_batch_vec_env.py](/home/void0312/Workshop/CMO/tests/world_batch/test_world_batch_vec_env.py):
  `view` mode shares memory with `buf_obs`, `copy` mode detaches, and
  `terminal_observation` stays detached.

- [x] Benchmark `copy` vs `view` on the maintained execution path.
  Primary metric: `collect_plus_train_ms_per_env_step`.
  Secondary metrics: `rollout_ms_per_env_step`, `train_ms_per_env_step`.

- [ ] Decide whether `view` becomes the maintained default.
  Gate:
  if `view` is only neutral/noisy at maintained production batch sizes, keep
  `copy` as the default and stop here.

- [ ] Consider a separate follow-on for info-copy reductions.
  `buf_infos` stays out of this freeze.

## Risks To Control

- External callers may mutate returned observations.
- Callback code may retain observation references across steps.
- Autoreset must not expose stale terminal data as the next live observation.
- `terminal_observation` must remain detached from the live `buf_obs` storage.
- Benchmark wins must be measured on `collect + train`, not just policy forward latency.

## Acceptance Criteria

- `view` mode demonstrably shares memory with `buf_obs`.
- `copy` mode preserves the old detached behavior.
- `terminal_observation` remains copied in both modes.
- Maintained unit tests pass for `WorldBatchVecEnv`.
- Benchmarks are captured in this document or the umbrella checklist before any default promotion.

## Benchmark Protocol

Use [tools/diagnostics/benchmark.py](/home/void0312/Workshop/CMO/tools/diagnostics/benchmark.py)
with the same case and seed, changing only `observation_return_mode`.

Minimum protocol:

```bash
./.venv/bin/python tools/diagnostics/benchmark.py --family policy_observation_bridge -- \
  --case p5like_visual \
  --n-envs 8 \
  --rollout-steps 64 \
  --rollout-repeats 2 \
  --observation-return-mode copy

./.venv/bin/python tools/diagnostics/benchmark.py --family policy_observation_bridge -- \
  --case p5like_visual \
  --n-envs 8 \
  --rollout-steps 64 \
  --rollout-repeats 2 \
  --observation-return-mode view
```

Compare at least:

- `bridge_on.collect_plus_train_ms_per_env_step`
- `bridge_on.rollout_ms_per_env_step`
- `bridge_on.train_ms_per_env_step`

## Initial Benchmark Result

Environment:

- interpreter: repository `.venv`
- GPU: NVIDIA GeForce RTX 3090
- scenario:
  [takeoff_to_landing_continuous_train_v1.json](/home/void0312/Workshop/CMO/scenarios/combined/takeoff_to_landing_continuous_train_v1.json)

Executed:

- `p5like_visual`, `n_envs=8`, `rollout_steps=64`, `rollout_repeats=2`
- `obs_gpuhost_novis`, `n_envs=8`, `rollout_steps=64`, `rollout_repeats=2`
- confirmatory `p5like_visual`, `n_envs=16`, `rollout_steps=64`, `rollout_repeats=3`

Key comparison: `bridge_on` only, because that is the maintained CUDA learner
path.

Results:

- `p5like_visual`, `n_envs=8`
  - `copy`: `collect+train = 0.9707 ms/env-step`
  - `view`: `collect+train = 0.9539 ms/env-step`
  - `view` faster by about `1.7%`

- `obs_gpuhost_novis`, `n_envs=8`
  - `copy`: `collect+train = 0.9319 ms/env-step`
  - `view`: `collect+train = 0.8927 ms/env-step`
  - `view` faster by about `4.2%`

- `p5like_visual`, `n_envs=16`
  - `copy`: `collect+train = 0.7957 ms/env-step`
  - `view`: `collect+train = 0.7937 ms/env-step`
  - `view` faster by about `0.25%`

Interpretation:

- The `deepcopy(self.buf_obs)` removal is not a regression.
- It can help on smaller maintained batches.
- At larger maintained batch sizes, the win collapses toward noise.
- This is not yet strong enough evidence to promote `view` as the maintained
  default.

Current decision:

- keep `observation_return_mode=copy` as the maintained default
- keep `view` available for controlled benchmarking and future promotion
- treat this phase as functionally validated but not default-worthy yet

## Freeze Rule

Do not mix this phase with exact GPU sim stepping or deeper runtime rewrites.
The purpose of this freeze is to isolate the maintained rollout hot path and
measure one narrow ownership change at a time.
