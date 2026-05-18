# Level-1 Implementation Optimization Analysis

Status: `2026-05-18` active analysis draft.  
Scope: current runtime compute-chain analysis before equivalent-algorithm or
approximate optimization.

## 1. Positioning

This document intentionally stays inside Level 1 of the optimization ladder.

That means:

- no new approximate behavior;
- no semantics-changing shortcut;
- no assumption that the next step must be an algorithm rewrite.

The question here is narrower:

```text
Within the current runtime contracts and semantics,
where is the implementation-side overhead still living?
```

## 2. Current Measurement Snapshot

### 2.1 `world_batch_vec_env` aligned comparison

Historical baseline from
`docs/plan/results/wp6_benchmark_world_batch_vec_env_phase4.json`:

- `dummy_reset_ms = 10.051270`
- `world_batch_reset_ms = 11.891172`
- `dummy_ms_per_env_step = 0.392506`
- `world_batch_ms_per_env_step = 0.292365`
- `step_speedup = 1.342521`

Current aligned sample already captured on `2026-05-18` with the
`build-workshop` runtime path:

- `dummy_reset_ms = 12.701345` (`+26.37%`)
- `world_batch_reset_ms = 12.906878` (`+8.54%`)
- `dummy_ms_per_env_step = 0.506252` (`+28.98%`)
- `world_batch_ms_per_env_step = 0.393277` (`+34.52%`)
- `step_speedup = 1.287264` (`-4.12%`)

Interpretation:

- the absolute runtime is slower than the old reference;
- but the batch path still keeps a relative step advantage over the dummy path;
- therefore the situation is regression-worthy, but not collapse-level.

### 2.2 `UniversalEnv` hotspot samples

Current sampled single-world step timings:

- `air_1v1`: about `0.587 ms/step`, with `obs_build_ms ~= 0.179`
- `naval_screen`: about `0.569 ms/step`, with `obs_build_ms ~= 0.173`
- `c2_demo`: about `0.876 ms/step`, with `obs_build_ms ~= 0.433`

Interpretation:

- `c2_demo` is currently the clearest single-world hotspot;
- observation construction is a large part of that cost.

### 2.3 Cooperative sample

Current cooperative smoke sample:

- single: `step_time_ms ~= 0.772`, `obs_build_ms ~= 0.248`
- cooperative (`n_envs=4`, `8` slots total):
  - `step_time_ms ~= 5.33`
  - `per_agent_step_time_ms ~= 0.666`
  - `obs_build_ms ~= 1.16`
  - `behavior_update_ms ~= 1.13`
  - `command_sync_ms ~= 0.53`

Interpretation:

- cooperative execution still scales better on a per-agent basis than raw
  wall-clock suggests;
- but `obs_build_ms` and `behavior_update_ms` are large enough to remain first
  investigation targets.

## 3. Current Compute Chains

### 3.1 Single-world reference chain

Reference file: `gym_envs/universal_env.py`

Current step order:

1. normalize action and build `PilotAction`
2. write action to kernel
3. `sim.step()`
4. read truth and instruments
5. `loader.update_behaviors(...)`
6. build observation
7. `loader.compute_full_step(...)`
8. build `info`

This chain is the simplest reference for understanding where batch/mainline
paths later add coordination overhead.

### 3.2 `WorldBatchVecEnv` mainline chain

Reference file: `python/rl/runtime/world_batch_vec_env.py`

Current `step_wait()` order:

1. build refs and optional instrument snapshots for action preparation
2. prepare per-world actions
3. batch-set pilot actions
4. batch step runtime worlds
5. batch read truth and instruments
6. per-world `loader.update_behaviors(...)`
7. sync command chain back to the kernel
8. batch-build observations
9. prepare flight-shaping overrides
10. per-world reward/info evaluation and autoreset handling

The important point is that this path is already partially batched, but it
still returns to Python for several per-world assembly stages.

### 3.3 Cooperative mainline chain

Reference file: `python/rl/runtime/cooperative_world_batch_vec_env.py`

Current cooperative step order:

1. sync current command chain
2. prepare/apply per-slot actions grouped by world
3. batch step all worlds
4. per-world state read for each world roster
5. per-slot `loader.update_behaviors(...)`, then director update
6. sync command chain again
7. per-world observation batch build
8. per-slot reward/info evaluation
9. shared-world termination/reset handling

Compared with the single-agent chain, the extra cost comes mainly from:

- roster fan-out;
- extra Python coordination loops;
- extra observation assembly;
- shared-world termination bookkeeping.

## 4. Level-1 Hotspot Candidates

### 4.1 Duplicate visual refresh in `WorldBatchVecEnv`

Candidate location:

- `_build_observations_from_cached_state(...)` refreshes the target batch first.
- `_attach_visual_observation(...)` refreshes one env again before attaching the
  cached visual tensor.

That means the visual path appears to do:

```text
batch refresh
  -> per-env attach
  -> per-env refresh again
```

This is a classic Level-1 candidate because it looks like duplicated exact work,
not a semantic redesign.

### 4.2 Python observation assembly remains hot even on compiled paths

In both:

- `python/rl/runtime/world_batch_vec_env.py`
- `python/rl/runtime/cooperative_world_batch_vec_env.py`

the compiled observation path still performs per-env/per-slot Python work for:

- `np.asarray(...)`
- `reshape(...)`
- `dict` assembly
- optional `proprio` packing
- final observation object stitching

This is still Level 1 because the output contract is unchanged; the question is
whether we can reuse buffers/views and reduce Python allocation churn before
touching the algorithm itself.

### 4.3 Cooperative state read is still grouped per world in Python

The cooperative path currently loops over worlds and does
`read_truth_and_instruments(refs)` per world roster.

That suggests a Level-1 cleanup possibility:

- flatten the current exact reads into a larger exact batch call first;
- redistribute the returned packets back to slot state locally.

This does not need a new approximation or a new task contract; it is an
implementation-side batching cleanup inside the existing runtime surface.

### 4.4 Reward/info tail is still a Python per-env/per-slot loop

Both batch mainlines still spend hot-path time in:

- `loader.compute_full_step(...)`
- `build_step_info(...)` or `build_step_info_minimal(...)`

This does not automatically mean “rewrite the reward algorithm now.”

Level-1 first questions are narrower:

- are we materializing full info when the caller does not need it?
- are we cloning or reshaping more state than necessary?
- are there repeated exact preparations that should stay cached within the same
  step?

Only after those questions are exhausted should this area be promoted to Level 2.

### 4.5 Behavior-update and command-sync loops are still Python-serialized

The current batch paths still perform:
