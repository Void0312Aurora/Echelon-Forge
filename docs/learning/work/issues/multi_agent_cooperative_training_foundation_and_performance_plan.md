# Multi-Agent Cooperative Training Foundation and Performance Plan

Language:
- English canonical: `multi_agent_cooperative_training_foundation_and_performance_plan.md`
- Chinese companion: [multi_agent_cooperative_training_foundation_and_performance_plan.zh.md](multi_agent_cooperative_training_foundation_and_performance_plan.zh.md)

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/learning/work/issues/multi_agent_cooperative_training_foundation_and_performance_plan.md`
Owner: `learning/cooperative-training`
Last verified: `2026-08-08`
Content status: migrated research snapshot; it supplies direction and risks,
not an active implementation package or acceptance authority.

Status: draft issue based on the `2026-05-11` research snapshot.

Document scope:

- This document plans a true multi-agent cooperative training foundation, not an extended note for single-aircraft formation hints.
- The goal is to unify the roster, observations, actions, coordination, and training entry points for multiple controllable entities within the same world.
- This document also treats performance optimization as a first-class constraint, because multi-agent setups naturally amplify observation, inference, synchronization, and memory overhead.
- This document does not authorize immediately introducing a dedicated `TwoShipEnv`-style silo; interfaces must target `N` controllable entities within the same world.

## I. Core Assessment

The current repository already contains partial building blocks related to cooperative execution, but it does not yet have a true multi-agent foundation:

- `ScenarioRuntime` / `ScenarioLoader` can already spawn multiple entities in the same world, but `agent_id` still selects only the first `is_agent: true` entity.
- `UniversalEnv` is still a single-`agent_id` observation, action, and reward loop.
- `WorldBatchRuntime` / `RuntimeFacade` already support batched access via `WorldEntityRef(world_index, entity_id)`, but the Python training/environment layer is still not organized by entity roster.
- `LeaderTrainingEnv` has validated the layered idea of "high-level coordination + execution-layer flight," but it is still a single executing-aircraft window, not a multi-aircraft cooperative environment.

Therefore, the first step in multi-agent cooperative training is not to "build another two-ship environment," but to fill in:

```text
the roster / refs / observation / action / coordination mapping layer
for multiple controllable entities within the same world
```

## II. Design Boundaries

### 2.1 Multi-agent is not multi-world

`n_envs` addresses the number of parallel worlds, not the number of agents within a single world.

This plan focuses on:

- A single world containing multiple controllable entities.
- Those entities may share one policy, or different policies may be assigned by role.
- Those entities may be partially scripted and partially driven by learned policies.

### 2.2 The coordination layer is not the aircraft itself

The leader layer / coordination director is responsible for generating formation and cooperative intent; it is not the leader aircraft itself.

Recommended chain:

```text
C2 / TaskOrder
  -> Coordination Director
  -> per-platform MissionCommand / LeaderIntent
  -> per-platform execution policy
  -> PilotAction
  -> WorldBatchRuntime step
```

### 2.3 Observations must follow the realistic-availability principle

Execution-layer inputs may only come from realistically available information products:

- Own cockpit / instruments
- Mission system / radio / datalink
- Visual / radar / IRST / RWR
- Modeled relative information about friendly aircraft

Global ground truth, internal reward errors, or simulator-private state must not be injected into the policy merely for training convenience.

## III. Existing Infrastructure

Infrastructure that can be reused directly:

- `RuntimeFacade` / `WorldBatchRuntime`
  - Batched writes of `PilotAction`, `MissionCommand`, `TaskOrder`, `LeaderIntent`, and `PilotReport`
  - Batched reads of `AgentObservation`, `InstrumentState`, and command/tasking/report data
- `ScenarioRuntime`
  - Already capable of spawning multiple entities and preserving `entities: name -> entity_id`
- `ScenarioLoader`
  - Already has data chains such as `mission_command`, `contacts`, `visual`, `track`, and `leader_intent`
- `LeaderBatchedVecEnv`
  - Already validates batched inference and shared runtime scheduling
- `WorldBatchVecEnv`
  - Already provides the world-batch run, reset, step, and readback framework

Current gaps:

- Missing roster constraints
- Missing observation/action routing for multiple entities in one world
- Missing multi-agent policy routing
- Missing performance budget and benchmark guardrails

## IV. Performance Risks

Multi-agent cooperative training amplifies the following costs:

1. Observation cost
   - `contacts` / `visual` / `datalink` / `radar` products are replicated per agent
   - Large tensor repacking and Python/C++ boundary overhead
2. Inference cost
   - A shared policy requires a larger batch
   - Multi-role policies increase the number of forward passes
3. Step cost
   - Action writes, state readback, and reward aggregation all scale up per agent
4. Synchronization cost
   - When multiple agents share a world, waiting on any one member affects the entire batch step
5. Memory cost
   - Rollout buffers, observation cache, visual cache, and track cache all scale with agent count
6. Serialization cost
   - Python `dict` / `list` / `numpy` structures are expensive in hot paths

## V. Optimization Principles

1. Preserve a single world-step ground-truth source first; do not split simulation truth apart.
2. Reuse the batch runtime and facade first; do not build a dedicated two-ship runtime.
3. Separate metadata such as `roster`, `role`, and `policy_route` from execution-policy inputs.
4. Prefer packed arrays / structured batches for observations instead of deeply nested Python `dict`s.
5. Prioritize batched forward passes for shared policies; role-based multi-policy setups must also retain a batch entry point.
6. Enable high-cost inputs such as visual, radar, and contacts on demand, and by default only for the most necessary members or the lowest feasible frequency.
7. Benchmark first, then optimize; do not write a pile of branches and guess about performance.

## VI. Recommended Work Packages

### WP1: Roster and Entity Reference Layer

- Make the scenario / loader explicitly return the active controllable roster.
- Use `world_index / entity_id / entity_name / role_code / element_id` as the unified reference.
- Clarify the ownership of leader / wingman / passive entities.

### WP2: Multi-Agent Observation / Action Contract

- Define the minimal observation package structure for multiple entities in one world.
- Define per-agent action routing and policy routing.
- Preserve the realistic-availability principle and forbid new training-only role fields from going directly into the policy.

### WP3: VecEnv and Training Entry Refactor

- Allow the training entry to support rollout for multiple agents within one world.
- Support both shared-policy and role-split-policy routing.
- Keep the existing single-agent entry path compatible.

Recorded progress in the cited snapshot:

- A training entry with `agent_layer = "cooperative_execution"` has been added.
- `python/rl/cooperative_world_batch_vec_env.py` has been added to expand active roster members within the same world into flat VecEnv slots while sharing the same world step / reset.
- Shared-policy cooperative rollout is already working, while the original `execution` / `leader` entries remain unchanged.
- At this stage, role-split policy support still remains at the roster / `policy_route` metadata layer and VecEnv helper-query layer; it has not yet been connected to a multi-policy training loop in `train.py`.
- Smoke tests, SB3 rollout tests, and training-entry contract tests have been added to verify that the two-aircraft cooperative execution path runs successfully.

### WP4: Coordination Layer and Scripted Director

- Decouple leader / cooperative intent from the aircraft execution body itself.
- Support a scripted coordination director first, then gradually support an RL director.

Recorded progress in the cited snapshot:

- A world-level scripted coordination director has been connected in `python/rl/cooperative_world_batch_vec_env.py`.
- The director updates each slot's `mission_cmd / task_order / leader_intent / pilot_report` on a per-world basis, then reuses the existing batch command chain for dispatch.
- Targeted tests have been added to confirm that different members in cooperative execution can receive different formation offsets while the training entry remains usable.

### WP5: Performance Baseline and Benchmark

- Establish a unified benchmark for single-agent, two-agent, and multi-agent cases.
- Record per-agent step time, policy forward time, observation build time, and memory footprint.
- Measure Python assembly, C++ runtime, GPU helper, and model inference separately.

Recorded progress in the cited snapshot:

- `python/rl/support/multi_agent_benchmark.py` and `scripts/benchmark_multi_agent.py` have been added to provide a repeatable performance baseline entry point.
- The current baseline covers:
  - `single_agent`
  - `leader`
  - `cooperative_execution`
  - `all` aggregate mode
- The cooperative path now fills in `collect_step_timing / last_step_timing / last_reset_timing` inside `CooperativeWorldBatchVecEnv`, aligning it with the existing single-world / leader / world-batch timing metrics.
- A formal cooperative cruise scenario has been added:
  - `scenarios/cruise/cooperative_cruise_waypoints_paramroute_navv2_formation_train_v1.json`
- Benchmark smoke tests have been added and validated:
  - `tests/runtime/multi_agent/test_multi_agent_benchmark.py`
  - `tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py`
- The current cooperative smoke baseline can already emit per-step JSON metrics, including:
  - `per_agent_step_time_ms`
  - `action_prepare_ms`
  - `batch_step_ms`
  - `state_read_ms`
  - `behavior_update_ms`
  - `command_sync_ms`
  - `obs_build_ms`
  - `reward_info_ms`
  - `rss_bytes`

Current WP5 assessment:

- The baseline entry point is in place and can serve as the before-optimization control for WP6.
- Larger multi-world / multi-slot tables have not yet been formed, and frozen-model leader inference has not yet been logged together with cooperative shared-policy rollout in the same experiment set; that belongs to expanded WP5 sampling and no longer blocks entry into WP6.

### WP6: Performance Optimization

- Apply C++ / batched processing to high-frequency observation packing.
- Add caching and low-frequency update strategies for contacts / visual / track generation.
- Use batched inference for shared policies and route-aware batching for multi-policy setups.

Suggested cut points:

- First watch `obs_build_ms`, `state_read_ms`, and `behavior_update_ms`; these are already directly observable in the cooperative baseline.
- The suggested first-batch optimization priorities are:
  1. Batch processing and caching for cooperative observation build
  2. Batched convergence for cooperative state read / packet export
  3. Batched inference integration for shared-policy forward passes

Recorded progress in the cited snapshot:

- The first round of hotspot convergence for the cooperative runtime has been completed, with changes concentrated in `python/rl/cooperative_world_batch_vec_env.py` and the training / benchmark entry points, without changing simulation semantics.
- Optimizations that have been connected and validated:
  - Cooperative state read now reuses `_RuntimeFacadeAdapter.read_truth_and_instruments(...)`, removing the second mapping from per-world packets into Python `dict`s.
  - Cooperative visual observation now has a complete per-slot cache and truly respects `visual_update_interval`.
  - Cooperative observation build now uses existing batch-capable facilities:
    - `batch_observation_backend`
    - `batch_visual_backend`
  - The `agent_layer = "cooperative_execution"` branch in `train.py` now receives and prints the cooperative observation / visual backend.
  - `python/rl/support/multi_agent_benchmark.py` now supports reading the cooperative runtime backend from training configuration and echoing the effective backend in benchmark notes.
- Validation added or updated:
  - `tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py`
  - `tests/runtime/multi_agent/test_multi_agent_benchmark.py`
  - `tests/training/test_training_cli_contracts.py`
- The `step-eval` entry in `ScenarioLoader.compute_full_step(...)` has been changed to optionally consume cached data, and the cooperative VecEnv now directly reuses the prepared `step_evaluation`, avoiding redundant rebuilds on the reward hot path.
- Regression tests have been added to confirm that when the cache hits, `step-eval` is no longer rebuilt and reward / termination / status remain consistent with the baseline.
- Current `.venv` benchmark smoke:
  - `n_envs=1`: `step_time_ms ~= 1.28`, `reward_info_ms ~= 0.087`
  - `n_envs=4`: `step_time_ms ~= 4.76`, `reward_info_ms ~= 0.348`

First-round WP6 benchmark conclusions:

- Under the current cooperative-cruise smoke baseline, the default `auto -> legacy` path is more reliable. The compiled observation path has been connected, but it has not yet consistently outperformed legacy at the current 2-slot / 8-slot scale, so it remains an explicit opt-in capability rather than the default mainline path.
- With `n_envs=1`, 2 slots, 8 steps, and the default backend (`legacy`), the current cooperative benchmark is approximately:
  - `step_time_ms ~= 1.22`
  - `per_agent_step_time_ms ~= 0.61`
  - `obs_build_ms ~= 0.49`
  - `state_read_ms ~= 0.015`
- Compared with the smoke baseline before WP6 began from WP5 (approximately `step_time_ms ~= 1.31`, `obs_build_ms ~= 0.54`, `state_read_ms ~= 0.070`), the current results show:
  - The state-read path has converged significantly
  - Observation build has also decreased
  - The cooperative path now has comparable guardrails for the observation backend / visual backend
- With `n_envs=4` and 8 slots, the current default smoke result is approximately:
  - `step_time_ms ~= 4.97`
  - `per_agent_step_time_ms ~= 0.62`
  - `obs_build_ms ~= 2.36`
  - `behavior_update_ms ~= 1.02`
  This indicates that once cooperative execution scales to multiple worlds, the new top hotspots are more focused on:
  1. Per-slot `update_behaviors(...)`
  2. Per-slot reward / info aggregation
  3. Further fused / batched observation build within the world

Current WP6 assessment:

- The first round of cooperative runtime hotspot remediation has been completed and has passed smoke tests, benchmarks, and training-entry contract tests.
- At this stage, the compiled cooperative observation backend should not be made the default; further switching should remain benchmark-driven.
- If WP6 continues deeper, the suggested updated priorities are:
  1. `behavior_update_ms`: evaluate when it is safe to switch to a narrower `command-chain-only` / mainline runtime path
  2. `reward_info_ms`: reduce per-slot Python info / `step-eval` rebuilds
  3. Re-evaluate the fused observation path at larger world / slot scales

### Follow-on WP6 Breakdown

To prevent "performance optimization" from continuing to sprawl, the follow-on WP6 work should be limited to the four loops below, and each loop must be tied to both benchmarks and regression tests:

#### WP6.1: Converge `behavior_update_ms`

- Goal: reduce the behavior-update overhead for each slot.
- Only two categories of judgment are allowed:
  - Whether a narrower `update_command_chain_only(...)` can be used safely in cooperative scenarios
  - Whether the update frequency of the world-level scripted director can be reduced one level further
- Not allowed:
  - Directly switching all cooperative scenarios to command-chain-only
  - Skipping waypoint / transition semantics just for speed
- Acceptance:
  - The existing cooperative smoke must not regress
  - Under the `n_envs=4` baseline, `behavior_update_ms` must decrease measurably, or we must confirm there is no safe benefit and stop

Current results:

- The first round of convergence has been completed. `ScriptedCooperativeCoordinationDirector` now skips repeated updates when the world-level dirty state has not changed.
- This step does not change mission / formation semantics; it only avoids rewriting the same formation and role metadata on every step.
- Smoke tests and benchmarks have been rerun. Under the 4-world, 8-slot baseline, `behavior_update_ms` dropped from about `1.02 ms` to about `0.74 ms`, and `step_time_ms` dropped from about `4.97 ms` to about `4.09 ms`.
- Regression tests have been added to lock in the "do not update repeatedly when unchanged" behavior.

Current WP6.1 assessment:

- Completed and verified.
- If we continue pushing down `behavior_update_ms`, the next step is evaluation of a narrower `command-chain-only` / mainline runtime path, not more micro-tuning of the scripted director.

#### WP6.2: Converge `reward_info_ms`

- Goal: reduce Python info / `step-eval` rebuilds around per-slot `compute_full_step(...)`.
- Preferred path:
  - Reuse cached `step_evaluation`
  - Enable batch prepare only under homogeneous mission configurations
- Not allowed:
  - Simplifying reward semantics merely to save time
  - Bypassing the existing safety / approach / landing evaluation chain
- Acceptance:
  - `reward_info_ms` decreases in the cooperative benchmark
  - Results remain consistent with the existing smoke / reward regressions

Recorded status in the cited snapshot:

- Completed.
- The cooperative VecEnv now passes the cached `step_evaluation` directly, and `compute_full_step(...)` no longer rebuilds `step-eval` when the cache hits.
- Regression tests already cover cache-hit consistency against the baseline.

#### WP6.3: Re-evaluate `obs_build_ms`

- Goal: decide whether the compiled observation backend is worth enabling by default at larger slot scales.
- Benchmark-driven only; no new observation fields.
- Focused comparisons:
  - `legacy` vs `compiled`
  - `n_envs=1 / 4 / 8`
  - `include_visual=false / true`
- Acceptance:
  - Reach a clear conclusion on the default strategy
  - If compiled cannot consistently outperform legacy, keep it as explicit opt-in

Recorded status in the cited snapshot:

- Completed.
- Historical benchmarks showed that compiled observation had not consistently
  outperformed the legacy observation path on the cooperative-cruise smoke
  setup. That result is retained as performance context only.
- The current active cooperative configuration uses
  `batch_observation_backend=compiled` and `batch_visual_backend=compiled`;
  `batch_observation_backend=legacy` is no longer a maintained input.

#### WP6.4: Close the Baseline Matrix

- Goal: avoid having all future optimizations rely on only one smoke case.
- Fix at least three comparison groups:
  - `1 world / 2 slots`
  - `4 worlds / 8 slots`
  - `visual on/off`
- Fixed recorded metrics:
  - `step_time_ms`
  - `per_agent_step_time_ms`
  - `obs_build_ms`
  - `state_read_ms`
  - `behavior_update_ms`
  - `reward_info_ms`
  - `rss_bytes`
- After this step, WP6 moves into a "whether to continue optimizing" decision rather than continuing to expand scope.

Recorded status in the cited snapshot:

- Completed.
- The fixed matrix results are:
  - `1 world / 2 slots / visual off`: `step_time_ms ~= 1.334`, `obs_build_ms ~= 0.594`, `state_read_ms ~= 0.0188`, `behavior_update_ms ~= 0.235`, `reward_info_ms ~= 0.0907`
  - `1 world / 2 slots / visual on`: `step_time_ms ~= 1.801`, `obs_build_ms ~= 1.107`, `state_read_ms ~= 0.0150`, `behavior_update_ms ~= 0.206`, `reward_info_ms ~= 0.0783`
  - `4 worlds / 8 slots / visual off`: `step_time_ms ~= 4.126`, `obs_build_ms ~= 2.058`, `state_read_ms ~= 0.0562`, `behavior_update_ms ~= 0.754`, `reward_info_ms ~= 0.300`
  - `4 worlds / 8 slots / visual on`: `step_time_ms ~= 6.533`, `obs_build_ms ~= 4.340`, `state_read_ms ~= 0.0532`, `behavior_update_ms ~= 0.719`, `reward_info_ms ~= 0.299`
  - `8 worlds / 16 slots / visual off`: `step_time_ms ~= 7.812`, `obs_build_ms ~= 4.015`, `state_read_ms ~= 0.108`, `behavior_update_ms ~= 1.382`, `reward_info_ms ~= 0.595`
  - `8 worlds / 16 slots / visual on`: `step_time_ms ~= 13.264`, `obs_build_ms ~= 8.759`, `state_read_ms ~= 0.101`, `behavior_update_ms ~= 1.364`, `reward_info_ms ~= 0.596`
- Conclusion: compiled observation still does not show a stable advantage across the current cooperative scaling matrix, and the cost is higher when visual is enabled, so it remains explicit opt-in and is not promoted to the default mainline path.

## VII. Acceptance Criteria

At minimum, the following must be verified:

- Multiple controllable entities can be managed simultaneously within the same world.
- Each agent can receive its own observation and its own action.
- Both shared-policy and role-policy setups can run.
- The two-aircraft scenario can complete smoke tests stably.
- Under multi-agent conditions, per-step overhead has a quantifiable baseline and optimization result.

## VIII. Current Mainline Status and Next Steps

Current mainline assessment:

- The cooperative execution foundation, shared-policy cooperative rollout, scripted coordination director, benchmark guardrails, and first round of performance convergence have largely been completed.
- The two-aircraft cooperative cruise path now has a closed loop for training, evaluation, and visual inspection.
- Key errors in the cruise visualization pipeline have been fixed:
  - `Lead/Wing` is no longer misclassified as `Facility`
  - F-16 model rendering has been restored
  - Under `--zero_randomization`, aircraft heading now matches the true eastbound initial flight direction

Therefore, "continuing to fix the cooperative cruise foundation" is no longer treated as a mainline blocker. The next mainline should shift to:

```text
Two-aircraft cooperative takeoff training preparation
-> cooperative takeoff/departure training line
```

The next steps are recommended in the following order:

1. Freeze the current cooperative cruise baseline
   - Preserve the current active cruise config as the validated cruise starting point for cooperative execution.
   - Record the visual verification conclusions to avoid reintroducing model-heading / world-yaw issues later.

2. Inventory directly reusable takeoff assets
   - Reuse the existing single-aircraft takeoff / departure scenarios, rewards, curriculum randomization, and `scripted_takeoff` controller.
   - Prefer referencing the frozen single-aircraft takeoff config and the `takeoff_to_cruise` bridge path, rather than building a cooperative takeoff mechanism from scratch.

3. Define the entry point for two-aircraft cooperative takeoff training
   - In phase one, prioritize cooperative departure training with "two aircraft on the same runway, a shared takeoff/departure procedure, and a shared policy."
   - Phase one does not rewrite the full ground taxi / tower system. Instead, it supplements the existing `MissionCommand -> TaskOrder -> LeaderIntent -> execution policy` chain with the minimum takeoff-clearance semantics:
     - `takeoff_procedure_id`: single / interval / wing takeoff type
     - `takeoff_clearance_id`: hold short / line up and wait / cleared for takeoff / rolling / airborne / abort
     - `takeoff_interval_s`: release interval for interval departure
     - `runway_slot_id`: center / left / right runway occupancy
   - `command_code` should remain the coarse-grained `takeoff / departure`; do not keep embedding specific takeoff types into macro command codes.
   - In phase one, observations should use a dedicated cooperative-takeoff mission-observation variant that carries only mission / clearance semantics realistically available to pilots, without introducing simulator-private ground truth.
   - Preserve the realistic-availability principle and do not expose simulator-private ground truth to the policy.
   - First converge the success criteria on:
     - Safe liftoff
     - Runway / departure-axis keeping
     - Basic formation with no mutual interference
     - Smooth handoff into the subsequent cruise command chain after departure

4. Do not expand to more complex two-aircraft landing or full mission before the takeoff line is working
   - First solve cooperative takeoff/departure action coupling, runway occupancy, spacing, and early-climb stability.
   - Once cooperative takeoff is stable, then consider bridging it with the existing cooperative cruise into a combined task.

## IX. Non-Goals

- Do not immediately introduce a new dedicated `TwoShipEnv` silo.
- Do not feed the policy with global ground truth, internal reward errors, or simulator-private state.
- Do not begin large-scale performance rewrites without a benchmark in place.
- Do not treat exact GPU world-step as a prerequisite for the multi-agent foundation.
