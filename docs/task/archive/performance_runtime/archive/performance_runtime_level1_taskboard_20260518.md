# Level-1 Runtime Optimization Taskboard

Status: `2026-05-18` active execution taskboard.  
Scope: confirmed Level-1 implementation optimization tasks after the realism
freeze.

Related documents:

- [runtime performance optimization ladder](performance_runtime_optimization_ladder_20260518.md)
- [level-1 implementation optimization analysis](performance_runtime_level1_implementation_analysis_20260518.md)

Purpose:

- Convert the current Level-1 hotspot analysis into an ordered task set.
- Separate already-completed narrow fixes from still-open hotspots.
- Make subsequent performance work follow a staged taskboard instead of
  opportunistic spot edits.

---

## 1. Candidate Confirmation

The current Level-1 candidate pool has been re-checked against:

1. existing benchmark samples;
2. current runtime step chains;
3. hot-path timing fields already emitted by runtime benchmarks;
4. the first completed narrow fixes in this round.

Result:

- two candidates are now confirmed-and-started;
- three candidates remain confirmed-and-open;
- no Level-2 or Level-3 item is allowed to enter this taskboard by default.

## 2. Completed / Started Items

### L1-ENTRY-01: Diagnostics/runtime entry correctness

Status: completed.

Scope:

- ensure diagnostics imports prefer the repo build runtime instead of stale
  site-packages bindings;
- keep benchmark and runtime entrypoints measuring the intended runtime.

Current outcome:

- benchmark CLI and suite entrypoints are usable again;
- regression coverage was added for import order.

### L1-OBS-01: Remove redundant visual refresh in `WorldBatchVecEnv`

Status: completed in first-pass form.

Scope:

- stop re-refreshing per-env visual cache immediately after batch refresh during
  observation attach.

Current outcome:

- narrow implementation fix landed;
- targeted regression test added.

### L1-STATE-01: Flatten cooperative step state reads

Status: completed in first-pass form.

Scope:

- replace per-world cooperative state reads during step with a single exact
  flattened batch read, then redistribute locally.

Current outcome:

- narrow implementation fix landed;
- targeted regression test added.

## 3. Confirmed Open Tasks

These are the remaining confirmed Level-1 tasks that should drive the next
rounds.

### L1-OBS-02: Reduce Python observation assembly churn

Priority: `P0`  
Status: second-pass analysis completed; first-pass completed, second-pass implementation tightening landed with neutral overall measurements.

Evidence:

- `obs_build_ms` is a visible hotspot in `UniversalEnv`, `WorldBatchVecEnv`,
  and cooperative timing output.
- Current compiled paths still do per-env/per-slot:
  - `np.asarray(...)`
  - `reshape(...)`
  - Python `dict` assembly
  - optional `proprio` stitching

Primary files:

- [python/rl/runtime/world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)
- [python/rl/runtime/cooperative_world_batch_vec_env.py](../../../python/rl/runtime/cooperative_world_batch_vec_env.py)

Task goal:

- reduce Python-side allocation, reshaping, and object-construction churn
  without changing observation contract or semantics.

Current outcome:

- compiled observation assembly paths now consistently reuse lightweight
  float32 view conversion helpers instead of repeating ad hoc wrappers;
- regression coverage was added to keep compiled observation outputs on the
  expected `float32` contract;
- latest narrow benchmark pass showed a positive movement on the observation
  slice:
  - `world_batch_vec_env` sample: `obs_build_ms ~= 0.137` in the current pass;
  - cooperative smoke sample: `obs_build_ms ~= 3.169` in the current pass.

Acceptance:

- observation equality/regression tests stay green;
- targeted benchmark shows `obs_build_ms` improvement or at minimum a justified
  neutral result with measured breakdown.

### L1-TAIL-01: Tighten reward/info tail materialization

Priority: `P1`
Status: first-pass completed.

Evidence:

- hot path still ends in per-env/per-slot `compute_full_step(...)` plus
  `build_step_info(...)` or `build_step_info_minimal(...)`;
- timing fields show a visible `reward_info_ms` tail in batch runtimes.

Primary files:

- [python/rl/runtime/world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)
- [python/rl/runtime/cooperative_world_batch_vec_env.py](../../../python/rl/runtime/cooperative_world_batch_vec_env.py)
- [gym_envs/universal_env.py](../../../gym_envs/universal_env.py)

Task goal:

- confirm where full info is still built unnecessarily;
- reduce exact-but-unneeded tail materialization on hot paths.

Current outcome:

- `WorldBatchVecEnv` now reuses the same-step cached `step_evaluation` when
  entering `compute_full_step(...)` on the regular batch path, instead of
  rebuilding that preparation inside the reward tail;
- the execution-episode-controller mainline path now skips redundant Python
  `build_step_info(...)` materialization when exact `step_info_fields` have
  already been returned by the facade contract;
- narrow regression coverage was added for both reuse paths;
- current compiled/no-visual timing sample moved in the expected direction:
  - previous recorded sample: `reward_info_ms ~= 0.0536`, `total_ms ~= 0.3837`
  - current sample: `reward_info_ms ~= 0.0502`, `total_ms ~= 0.3663`

Acceptance:

- terminal/full/off `step_info_mode` semantics stay unchanged;
- `reward_info_ms` or total step time improves on the affected benchmark path.

### L1-BEHAV-01: Tighten Python behavior/sync staging

Priority: `P1`
Status: first-pass completed.

Evidence:

- cooperative timing still shows visible `behavior_update_ms` and
  `command_sync_ms`;
- batch paths still serialize parts of behavior update and sync staging in Python.

Primary files:

- [python/rl/runtime/world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)
- [python/rl/runtime/cooperative_world_batch_vec_env.py](../../../python/rl/runtime/cooperative_world_batch_vec_env.py)
- related loader behavior code under
  [gym_envs/scenario_loader/](../../../gym_envs/scenario_loader/)

Task goal:

- reduce Python orchestration overhead and redundant exact sync boundaries
  without redesigning behavior semantics.

Current outcome:

- `CooperativeWorldBatchVecEnv` now distinguishes between reset/override
  carry-over command-chain dirtiness and steady-state step execution;
- the cooperative path no longer performs an unconditional pre-step full
  command-chain flush on every step, and instead only does that extra flush
  when a world is still marked dirty before the step begins;
- the post-behavior/post-director command-chain flush remains in place, so the
  next exact world step still sees the intended commands;
- targeted regression coverage was added for both:
  - dirty-world first-step pre-sync still happens;
  - steady-state steps skip the redundant pre-sync;
- current cooperative smoke-style timing probe moved in the expected direction:
  - previous recorded sample: `command_sync_ms ~= 0.504`, `step_time_ms ~= 6.522`
  - current probe: `command_sync_ms ~= 0.262`, `step_time_ms ~= 6.630`
- a second narrow implementation tightening also landed in
  `ScriptedCooperativeCoordinationDirector`:
  - world-level `leader_overrides` are no longer recopied inside every slot apply;
  - steady-state director apply no longer rebuilds the `mission_cmd` mapping
    unconditionally and now skips a set of same-value Python field writes;
  - targeted regression coverage was added to lock both:
    - stable director updates reuse the existing `mission_cmd` mapping object;
    - takeoff-clearance progression still advances correctly.
- the second-pass analysis also established an important boundary:
  - `update_scripted_opponents(...)` is currently duplicated per slot loader in
    a cooperative world;
  - however, different slot loaders can bind the same scripted red controller
    to different `target_id` values, so collapsing that work to once-per-world
    is no longer an obvious Level-1 exact optimization and needs a separate
    owner/target-selection semantic decision first.
