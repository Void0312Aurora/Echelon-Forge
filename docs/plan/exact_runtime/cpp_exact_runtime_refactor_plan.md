# C++ Exact Runtime Refactor Plan

Navigation:

- [README.md](/home/void0312/Workshop/CMO/docs/plan/README.md)
- [system_layering_and_engine_encapsulation_plan.md](/home/void0312/Workshop/CMO/docs/plan/architecture/system_layering_and_engine_encapsulation_plan.md)
- [architecture_and_performance_research_followup.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture/architecture_and_performance_research_followup.zh.md)

Status: Draft follow-on implementation plan on 2026-04-03.  
Document role:

- This document describes a candidate next mainline acceleration/refactor path.
- It is not yet a separately frozen execution plan.
- No implementation should expand under this document until its scope is explicitly re-frozen.

This is the live candidate plan for the next mainline acceleration effort.

The key decision is:

- GPU exact-step remains the target backend.
- The next implementation priority is not more helper-level CUDA tuning.
- The next implementation priority is a C++ refactor that makes the exact
  simulation and execution-layer runtime explicit, data-oriented, and batchable.

## Why This Plan Exists

Three facts are now stable across docs, code, and diagnostics:

1. The coarse route-segment line is closed and is not being promoted into the
   training mainline.
2. The helper-first GPU line produced only modest end-to-end benefit and is now
   blocked more by host/runtime structure than by CUDA kernel math.
3. The repo already has a substantial C++ core, but hot-path ownership is still
   split across:
   - C++ exact world stepping
   - Python mission/episode state
   - Python observation/reward/termination orchestration
   - experimental exact CPU/GPU cached-session runtime plumbing

Relevant references:

- [execution_coarse_grained_route_segments.md](/home/void0312/Workshop/CMO/docs/plan/archive/execution_coarse_grained_route_segments.md)
- [gpu_exact_world_step_rearchitecture_plan.md](/home/void0312/Workshop/CMO/docs/plan/archive/gpu_exact_world_step_rearchitecture_plan.md)
- [gpu_execution_mainline_integration_checklist.md](/home/void0312/Workshop/CMO/docs/plan/exact_runtime/gpu_execution_mainline_integration_checklist.md)
- [system_layering_and_engine_encapsulation_plan.md](/home/void0312/Workshop/CMO/docs/plan/architecture/system_layering_and_engine_encapsulation_plan.md)
- [architecture_and_performance_research_followup.zh.md](/home/void0312/Workshop/CMO/docs/plan/architecture/architecture_and_performance_research_followup.zh.md)
- [simulation_kernel.cpp](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel.cpp)
- [world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.cpp)
- [scenario_loader.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py)

## Current Diagnosis

### 1. What is already in C++

The repo already has a real compiled core:

- exact world step truth source:
  [simulation_kernel.cpp](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel.cpp)
- multi-world owner/runtime shell:
  [world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.cpp)
- compiled execution helpers:
  [execution_step_runtime.cpp](/home/void0312/Workshop/CMO/src/core/mission/runtime/execution_step_runtime.cpp)
  [execution_frame_runtime.cpp](/home/void0312/Workshop/CMO/src/core/mission/runtime/execution_frame_runtime.cpp)
  [execution_episode_runtime.cpp](/home/void0312/Workshop/CMO/src/core/mission/runtime/execution_episode_runtime.cpp)
- exact-state contract and experimental GPU backend:
  [exact_stage_inventory.cpp](/home/void0312/Workshop/CMO/src/core/engine/exact_stage_inventory.cpp)
  [src/gpu/experimental](/home/void0312/Workshop/CMO/src/gpu/experimental)

This means the project is not choosing between "Python" and "C++" from
scratch. It is choosing whether the remaining hot-path ownership should now be
consolidated into the compiled side.

### 2. What still remains in Python hot paths

The execution hot path still crosses Python too often:

- `ScenarioLoader` still owns a large amount of mutable episode state:
  - waypoint progress
  - approach progress
  - reward bookkeeping
  - termination bookkeeping
  - command-chain synchronization shell
  - mission observation/state preparation
- `compute_full_step(...)` still performs high-frequency orchestration even when
  individual reward/termination helpers are compiled.
- `WorldBatchVecEnv` still depends on Python-side loader ownership to complete
  step semantics.

Relevant code:

- [scenario_loader.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py)
- [world_batch_vec_env.py](/home/void0312/Workshop/CMO/python/rl/runtime/world_batch_vec_env.py)
- [universal_env.py](/home/void0312/Workshop/CMO/gym_envs/universal_env.py)

### 3. Why the current GPU line plateaus

The current exact-step GPU work has already shown that:

- parity and stage-local replay infrastructure are valuable
- resident/device-side replay can become extremely fast in isolation
- end-to-end runtime still gets dominated by extract/apply/materialization and
  Python/runtime glue unless those contracts are restructured first

So the real blocker is no longer "missing kernels" alone.  
The blocker is that the exact step, episode state machine, and batch runtime are
still not owned by one stable compiled contract.

### 4. Why the existing batch-prepare layer is not yet enough

The new batch preparation helper is a good direction, but it is still not the
mainline episode controller:

- [execution_episode_batch_prepare.cpp](/home/void0312/Workshop/CMO/src/core/mission/episode/execution_episode_batch_prepare.cpp)

Today it is still simplified compared with the real Python path:

- waypoint/approach wiring is incomplete
- runway/on-runway/task context is simplified
- several episode-state transitions are still derived in Python

So it should be treated as a seed for the new ownership model, not as the final
runtime boundary.

## Decision

The project should now re-architecture around this sequence:

1. Keep `SimulationKernel` as the exact CPU truth source.
2. Move execution-layer episode ownership from Python into C++.
3. Introduce a stable compiled episode/controller contract above the world-step
   contract.
4. Attach `WorldBatchRuntime` to that compiled episode/controller contract.
5. Only then promote exact CPU backend work and resume exact GPU backend
   cutover on the same contracts.

In short:

`CPU truth source -> compiled episode runtime -> compiled exact CPU backend -> exact GPU backend`

not:

`more helper kernels -> more runtime patching -> hope end-to-end speed follows`

## Freeze Decisions

Until the new C++ runtime boundary exists:

- freeze new coarse-grained surrogate lines unless they directly support
  diagnostics
- freeze helper-level GPU micro-optimizations unless they unblock the new
  backend contract
- do not promote the cached exact-step backend to an unconditional default in
  maintained training
- keep all current parity traces, stage comparators, and resident-state probes
  as regression infrastructure

## Target Architecture

### A. `SimulationKernel` stays the semantic authority

`SimulationKernel` remains the truth source for:

- exact stage ordering
- exact ECS semantics
- baseline debugging and archived trace generation

It should continue to expose:

- exact stage inventory
- stage contract metadata
- replay/trace hooks

Relevant files:

- [simulation_kernel.h](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel.h)
- [simulation_kernel.cpp](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel.cpp)

### B. Add a compiled `ExecutionEpisodeState`

Introduce a compiled state object that owns the mutable per-episode fields now
held by `ScenarioLoader`.

This state should cover at least:

- mission command runtime copy
- waypoint list runtime ownership / active index / leg origin / previous
  distance
- approach tracking history (`dme`, `loc`, `gs` previous values)
- off-runway counters
- reward milestone flags (`liftoff_awarded`, `gear_bonus_awarded`, etc.)
- termination reason / mission phase / post-waypoint transition state
- cached route reference / route metadata

Candidate files:

- `src/core/mission/execution_episode_state.h`
- `src/core/mission/execution_episode_state.cpp`

### C. Add a compiled `ExecutionEpisodeController`

Introduce a C++ controller that owns one execution episode and performs the full
step contract:

1. ingest current truth/instrument state
2. update mission/waypoint/approach behavior state
3. build mission observation / reward / termination inputs
4. run compiled episode/frame/step runtime
5. emit a compact step result for Python/VecEnv consumption

This controller should become the compiled equivalent of the current Python
sequence:

- `ScenarioLoader.update_behaviors(...)`
- `build_universal_observation(...)`
- `ScenarioLoader.compute_full_step(...)`
- `build_step_info(...)`

Candidate files:

- `src/core/mission/execution_episode_controller.h`
- `src/core/mission/execution_episode_controller.cpp`

### D. Elevate `WorldBatchRuntime` from world owner to episode-runtime owner

`WorldBatchRuntime` should own not only worlds, but also compiled episode
controllers for worlds that participate in maintained execution rollouts.

It should expose stable batch contracts such as:

- `prime_execution_episode_batch(...)`
- `step_execution_episode_batch(...)`
- `get_execution_episode_outputs_batch(...)`
- `reset_execution_episode_batch(...)`

This is the layer that should hide whether the underlying exact step is:

- `SimulationKernel::step()`
- compiled exact CPU backend
- exact GPU backend

Relevant files:

- [world_batch_runtime.h](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.h)
- [world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.cpp)

### E. Exact-step backend becomes a private implementation detail

Once the episode controller boundary exists, the exact-step backend should sit
below it.

That backend should satisfy one stable contract:

- accept exact packed state / state store
- execute the exact ordered stage contracts
- update learner-facing state surfaces needed by the episode controller

This backend may have multiple implementations:

- live ECS truth path
- compiled exact CPU backend
- exact GPU backend

### F. Python becomes a thin orchestration layer

After cutover, Python should retain:

- training orchestration
- scenario/config loading compatibility
- diagnostics entrypoints
- environment wrapper compatibility

Python should stop owning:

- step-time episode mutation
- reward/termination bookkeeping
- exact-step backend semantics
- batch runtime internal scheduling semantics

## Ownership Boundaries After Refactor

### `SimulationKernel`

Owns:

- exact CPU truth semantics
- ECS world lifecycle
- trace and replay authority

Does not own:

- maintained execution-layer episode bookkeeping
- batch training-facing step result assembly

### `ExecutionEpisodeController`

Owns:

- per-episode mutable execution state
- mission/waypoint/approach behavior transitions
- compiled step/frame/episode evaluation wiring

Does not own:

- scenario file parsing
- SB3/Gym interface semantics

### `WorldBatchRuntime`

Owns:

- world pool
- episode controller pool
- backend selection and state synchronization
- batch stepping/readback contract

### Python (`ScenarioLoader`, `UniversalEnv`, `WorldBatchVecEnv`)

Owns:

- compatibility shims
- config and debug entrypoints
- training framework adaptation

Should no longer own:

- hot-path episode state

## Work Packages

### WP1. Freeze the episode-state contract

Goal:

- make the mutable execution episode state explicit and serializable

Deliverables:

- `ExecutionEpisodeState` struct
- parity-friendly snapshot/export helpers
- tests that compare Python-owned state vs compiled state on fixed scripted
  scenarios

Primary files:

- new `src/core/mission/execution_episode_state.*`
- [scenario_loader.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py)
- [python_module.cpp](/home/void0312/Workshop/CMO/src/interfaces/python/python_module.cpp)

Acceptance:

- the compiled state can represent the current Python episode bookkeeping
  without dropping fields

### WP2. Replace the simplified batch-prepare layer with a real step-input builder

Goal:

- make the batch builder semantically complete, not approximate

Deliverables:

- complete `ExecutionEpisodeRuntimeInputs` preparation from live state
- full waypoint/approach/safety/objective coverage
- removal of "simplified for now" branches from the main batch-prep path

Primary files:

- [execution_episode_batch_prepare.h](/home/void0312/Workshop/CMO/src/core/mission/episode/execution_episode_batch_prepare.h)
- [execution_episode_batch_prepare.cpp](/home/void0312/Workshop/CMO/src/core/mission/episode/execution_episode_batch_prepare.cpp)

Acceptance:

- batch-prepared episode inputs match the existing single-step Python path on
  curated test scenarios

### WP3. Introduce the compiled episode controller in shadow mode

Goal:

- run the C++ episode controller alongside the current Python path and compare
  outputs before cutover

Deliverables:

- `ExecutionEpisodeController`
- shadow-mode compare helper
- opt-in `WorldBatchVecEnv` shadow-compare diagnostics with reset/autoreset
  controller-state resync
- parity diagnostics for:
  - reward total
  - termination
  - status vector
  - mission observation
  - step info fields

Primary files:

- new `src/core/mission/execution_episode_controller.*`
- [scenario_loader.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py)
- new tests under `tests/runtime/`

Acceptance:

- controller shadow mode matches the legacy Python path on maintained execution
  scenarios and fixed scripted traces

Current progress on 2026-04-04:

- `ExecutionEpisodeController` exists in `ef_py` and can evaluate/step owned
  episode state.
- `ScenarioLoader` exposes a per-step controller shadow compare helper and
  parity tests for objective, route, approach, and takeoff-shaping cases.
- `WorldBatchVecEnv` now has an opt-in
  `execution_episode_controller_shadow_compare` diagnostic path that runs the
  compiled controller in shadow mode during rollout steps and resyncs controller
  state on reset/autoreset.

### WP4. Attach compiled episode control to `WorldBatchRuntime`

Goal:

- let maintained execution rollouts step through compiled episode controllers,
  not through Python-owned episode state

Deliverables:

- `WorldBatchRuntime` controller ownership
- batch step/result APIs for execution episodes
- opt-in world-batch execution path using compiled episode control

Primary files:

- [world_batch_runtime.h](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.h)
- [world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.cpp)
- [python_module.cpp](/home/void0312/Workshop/CMO/src/interfaces/python/python_module.cpp)
- [world_batch_vec_env.py](/home/void0312/Workshop/CMO/python/rl/runtime/world_batch_vec_env.py)

Acceptance:

- maintained execution rollouts can run through the compiled episode controller
  with CPU truth stepping and no Python episode-state ownership

### WP5. Promote the compiled exact CPU backend

Goal:

- move from "live ECS truth step only" to a compiled exact CPU backend behind
  the same controller/runtime boundary

Deliverables:

- data-oriented exact CPU state store
- exact CPU backend implementing the same named stage contracts
- per-stage parity gate vs live ECS truth

Primary files:

- new `src/core/engine/exact_cpu_backend.*`
- new `src/core/engine/exact_state_store.*`
- [simulation_kernel.cpp](/home/void0312/Workshop/CMO/src/core/engine/simulation_kernel.cpp)
- [world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.cpp)

Acceptance:

- compiled exact CPU backend replays the same exact-state stage contracts as the
  live ECS truth source

### WP6. Reattach the exact GPU backend

Goal:

- port the now-stable exact CPU backend contracts to CUDA

Deliverables:

- exact GPU backend below the same controller/runtime contract
- device-resident execution only after the controller/runtime boundary is
  stable

Primary files:

- [src/gpu/experimental](/home/void0312/Workshop/CMO/src/gpu/experimental)
- [src/gpu/README.md](/home/void0312/Workshop/CMO/src/gpu/README.md)
- [exact_stage_inventory.cpp](/home/void0312/Workshop/CMO/src/core/engine/exact_stage_inventory.cpp)

Acceptance:

- maintained runtime can switch exact backend without changing Python episode
  ownership

## Phased Modification Plan

### Phase 0. Boundary Freeze And Instrumentation

Scope:

- freeze the new ownership decision
- add missing comparison hooks so future cutovers are measurable

Changes:

- document the ownership boundary
- add episode-controller parity fixtures
- tighten runtime stats naming for write-back/materialization/sync

Exit:

- one diagnostic run can compare:
  - legacy Python episode path
  - compiled controller shadow path
  - exact CPU/GPU backend path beneath it

### Phase 1. `ExecutionEpisodeState` Landing

Scope:

- move mutable episode state definition to C++

Changes:

- add `ExecutionEpisodeState`
- add export/import helpers for tests
- teach Python loader to mirror this state instead of being its only owner

Exit:

- the state contract is explicit, testable, and no longer hidden in Python
  instance fields

### Phase 2. Complete Batch Input Preparation

Scope:

- remove approximation from compiled execution input construction

Changes:

- expand `execution_episode_batch_prepare`
- wire full waypoint/approach/objective/safety inputs
- remove current simplifications from the maintained path

Exit:

- prepared batch inputs are sufficient to reproduce current execution-step
  semantics

### Phase 3. C++ Episode Controller Shadow Cut

Scope:

- implement controller without changing maintained default behavior yet

Changes:

- add controller class
- run controller in shadow mode from Python/runtime tests
- log/compare parity on maintained scenarios

Exit:

- controller parity is stable enough for opt-in cutover

### Phase 4. `WorldBatchRuntime` Cutover

Scope:

- make the compiled controller the maintained execution-layer owner under
  `WorldBatchRuntime`

Changes:

- runtime owns controllers
- `WorldBatchVecEnv` reads compact batch outputs instead of relying on
  `ScenarioLoader.compute_full_step(...)`
- `ScenarioLoader` shrinks to config/debug adapter duties

Exit:

- maintained `p5` execution path no longer depends on Python-owned hot-path
  episode state

### Phase 5. Exact CPU Backend Promotion

Scope:

- move exact stepping behind the controller/runtime boundary

Changes:

- exact CPU backend becomes a selectable runtime backend
- live ECS step remains truth reference and debug path

Exit:

- exact CPU backend matches live truth stage-by-stage

### Phase 6. Exact GPU Backend Promotion

Scope:

- resume GPU cutover on the new stable contracts

Changes:

- GPU backend ports exact CPU backend contracts
- device-resident state is kept below controller/runtime boundary

Exit:

- exact GPU backend is no longer fighting Python-owned episode state and
  runtime write-back semantics at the same time

## Immediate First Implementation Batch

The first implementation batch should be intentionally narrow:

1. Add `ExecutionEpisodeState` and its Python test/export surface.
2. Expand `execution_episode_batch_prepare` until it can represent the real
   maintained execution-step inputs without simplification.
3. Add a shadow `ExecutionEpisodeController` for one maintained execution
   scenario family.
4. Add parity tests that compare:
   - reward
   - termination
   - status
   - mission observation
   - compact step info

This first batch should not yet:

- rewrite the leader runtime
- replace `SimulationKernel` truth stepping
- promote the exact GPU backend further
- widen coarse-grained surrogates

## Suggested File Plan

### New files

- `src/core/mission/execution_episode_state.h`
- `src/core/mission/execution_episode_state.cpp`
- `src/core/mission/execution_episode_controller.h`
- `src/core/mission/execution_episode_controller.cpp`
- `tests/runtime/test_execution_episode_controller_parity.py`
- `tools/diagnostics/compare_execution_episode_controller_parity.py`

### Existing files likely to change early

- [execution_episode_batch_prepare.h](/home/void0312/Workshop/CMO/src/core/mission/episode/execution_episode_batch_prepare.h)
- [execution_episode_batch_prepare.cpp](/home/void0312/Workshop/CMO/src/core/mission/episode/execution_episode_batch_prepare.cpp)
- [world_batch_runtime.h](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.h)
- [world_batch_runtime.cpp](/home/void0312/Workshop/CMO/src/core/engine/world_batch_runtime.cpp)
- [python_module.cpp](/home/void0312/Workshop/CMO/src/interfaces/python/python_module.cpp)
- [scenario_loader.py](/home/void0312/Workshop/CMO/gym_envs/scenario_loader/core.py)
- [world_batch_vec_env.py](/home/void0312/Workshop/CMO/python/rl/runtime/world_batch_vec_env.py)

## Acceptance Criteria

### Correctness

- stage-local exact-step parity remains zero-drift on declared packed-state
  surfaces
- compiled episode controller matches current maintained Python execution logic
  on curated scenarios
- maintained runtime keeps CPU fallback behavior on non-CUDA builds

### Performance

- compiled episode cutover must improve maintained execution rollout wall-clock
  beyond noise
- exact GPU promotion should not be reconsidered until the controller/runtime
  cut removes the current extract/apply/Python bottleneck

### Maintainability

- one explicit owner for execution hot-path episode state
- one explicit runtime boundary above exact-step backend selection
- Python envs stop duplicating mission/termination bookkeeping logic

## Stop-Loss Rules

Stop or re-scope if any of the following happen:

- the new C++ state/controller boundary cannot represent current maintained
  semantics without excessive Python fallback branches
- parity failures cluster in mission/waypoint ownership because the boundary is
  still too low-level
- measured gains after controller cutover remain in the noise floor even before
  exact GPU promotion

If that happens, the next adjustment should be to simplify the runtime boundary,
not to add more local helper optimizations.

## Summary

The next mainline move is not "more CUDA first."  
The next mainline move is:

- make execution hot-path ownership explicit in C++
- let `WorldBatchRuntime` own compiled execution episodes
- keep `SimulationKernel` as truth
- then promote exact CPU and exact GPU backends beneath that stable runtime
  contract

That is the shortest path from the current mixed ownership model to a backend
that can actually deliver GPU speedup without fighting the Python control plane.
