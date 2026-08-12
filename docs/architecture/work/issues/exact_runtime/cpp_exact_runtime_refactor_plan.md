# C++ Exact Runtime Refactor Plan

Language:
- English canonical: `cpp_exact_runtime_refactor_plan.md`
- Chinese companion: not maintained (English-only work surface).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/architecture/work/issues/exact_runtime/cpp_exact_runtime_refactor_plan.md`
Owner: `architecture/exact-runtime`
Last verified: `2026-08-08`
Content status: migrated candidate plan; historical landed-state claims remain
bounded to the cited I43 snapshot and require current revalidation.

Navigation:

- [Architecture Documentation](../../../README.md)
- [system_layering_and_engine_encapsulation_plan.md](../system_layering_and_engine_encapsulation_plan.md)
- [architecture_and_performance_research_followup.md](../architecture_and_performance_research_followup.md)

Status: draft issue. The document records a 2026-04-03 proposal and a
2026-07-21 I43 landed-fact census; neither snapshot supplies current execution
authorization. See "T4 Census (I43)" after Work Packages for its evidence
boundary.
Document role:

- This document describes a candidate next mainline acceleration/refactor path.
- It is not yet a separately frozen execution plan.
- No implementation should expand under this document until its scope is explicitly re-frozen.

This is a retained candidate plan, not a live acceleration program.

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

- execution_coarse_grained_route_segments.md (`git show 70c07a77:docs/plan/archive/exact_runtime/execution_coarse_grained_route_segments.md`)
- gpu_exact_world_step_rearchitecture_plan.md (`git show 70c07a77:docs/plan/archive/exact_runtime/gpu_exact_world_step_rearchitecture_plan.md`)
- [gpu_execution_mainline_integration_checklist.md](gpu_execution_mainline_integration_checklist.md)
- [system_layering_and_engine_encapsulation_plan.md](../system_layering_and_engine_encapsulation_plan.md)
- [architecture_and_performance_research_followup.md](../architecture_and_performance_research_followup.md)
- [simulation_kernel.cpp](../../../../../src/core/engine/simulation_kernel.cpp)
- [world_batch_runtime.cpp](../../../../../src/core/engine/world_batch_runtime.cpp)
- [gym_envs/scenario_loader/core.py](../../../../../gym_envs/scenario_loader/core.py)

## Current Diagnosis

### 1. What is already in C++

The repo already has a real compiled core:

- exact world step truth source:
  [simulation_kernel.cpp](../../../../../src/core/engine/simulation_kernel.cpp)
- multi-world owner/runtime shell:
  [world_batch_runtime.cpp](../../../../../src/core/engine/world_batch_runtime.cpp)
- compiled execution helpers:
  [execution_step_runtime.cpp](../../../../../src/core/mission/runtime/execution_step_runtime.cpp)
  [execution_frame_runtime.h](../../../../../src/core/mission/runtime/execution_frame_runtime.h)
  [execution_episode_runtime.cpp](../../../../../src/core/mission/runtime/execution_episode_runtime.cpp)
- exact-state contract and experimental GPU backend:
  [exact_stage_inventory.cpp](../../../../../src/core/engine/exact_stage_inventory.cpp)
  [src/gpu/experimental](../../../../../src/gpu/experimental)

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

- [gym_envs/scenario_loader/core.py](../../../../../gym_envs/scenario_loader/core.py)
- [world_batch_vec_env.py](../../../../../python/rl/runtime/world_batch_vec_env.py)
- [universal_env.py](../../../../../gym_envs/universal_env.py)

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

- [execution_episode_batch_prepare.cpp](../../../../../src/core/mission/episode/execution_episode_batch_prepare.cpp)

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

- [simulation_kernel.h](../../../../../src/core/engine/simulation_kernel.h)
- [simulation_kernel.cpp](../../../../../src/core/engine/simulation_kernel.cpp)

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

- [world_batch_runtime.h](../../../../../src/core/engine/world_batch_runtime.h)
- [world_batch_runtime.cpp](../../../../../src/core/engine/world_batch_runtime.cpp)

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
- [gym_envs/scenario_loader/core.py](../../../../../gym_envs/scenario_loader/core.py)
- [python_module.cpp](../../../../../src/interfaces/python/python_module.cpp)

Acceptance:

- the compiled state can represent the current Python episode bookkeeping
  without dropping fields

Recorded progress at 2026-07-21 (I43): landed. `ExecutionEpisodeState`
(`src/core/mission/episode/execution_episode_state.*`) is the canonical
mutable-episode-state struct. `gym_envs/scenario_loader/runtime_state.py`'s
`build_execution_episode_state`/`apply_execution_episode_state`/
`apply_execution_episode_runtime_fields` mirror it bidirectionally between
`ExecutionEpisodeState` and the `ScenarioLoader` instance fields; both the
shadow-compare path (WP3) and the opt-in mainline path (WP4) drive through
this same mirror, so it is load-bearing infrastructure for the ownership
boundary itself, not a superseded duplicate (see "T4 Census (I43)" below).

### WP2. Replace the simplified batch-prepare layer with a real step-input builder

Goal:

- make the batch builder semantically complete, not approximate

Deliverables:

- complete `ExecutionEpisodeRuntimeInputs` preparation from live state
- full waypoint/approach/safety/objective coverage
- removal of "simplified for now" branches from the main batch-prep path

Primary files:

- [execution_episode_batch_prepare.h](../../../../../src/core/mission/episode/execution_episode_batch_prepare.h)
- [execution_episode_batch_prepare.cpp](../../../../../src/core/mission/episode/execution_episode_batch_prepare.cpp)

Acceptance:

- batch-prepared episode inputs match the existing single-step Python path on
  curated test scenarios

Recorded progress at 2026-07-21 (I43): landed for the declared scope.
`execution_episode_batch_prepare.{h,cpp}` materializes
`ExecutionEpisodeRuntimeInputs` from `StepEvaluationBatchConfig`/
`StepEvaluationBatchEnvState`; the I41 register row (`t6_residual_ledger.md`
§7.3) found `WorldBatchRuntime` already reads/writes the resulting
`ExecutionEpisodeController` batch state through nine methods. The remaining
gap sits upstream of this WP's own scope: Python
(`gym_envs/scenario_loader/step_evaluation.py::build_step_evaluation_batch_env_state`)
still hand-gathers `truth`/`inst` into `StepEvaluationBatchEnvState` every
step, because WP2 was scoped to the prepare-from-env-state step, not the
gather-env-state-from-truth step. That gather step is tracked as WP4/T4
follow-on work, not a WP2 regression (see "T4 Census (I43)" below).

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
- [gym_envs/scenario_loader/core.py](../../../../../gym_envs/scenario_loader/core.py)
- new tests under `tests/runtime/`

Acceptance:

- controller shadow mode matches the legacy Python path on maintained execution
  scenarios and fixed scripted traces

Recorded progress at 2026-04-04:

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

- [world_batch_runtime.h](../../../../../src/core/engine/world_batch_runtime.h)
- [world_batch_runtime.cpp](../../../../../src/core/engine/world_batch_runtime.cpp)
- [python_module.cpp](../../../../../src/interfaces/python/python_module.cpp)
- [world_batch_vec_env.py](../../../../../python/rl/runtime/world_batch_vec_env.py)

Acceptance:

- maintained execution rollouts can run through the compiled episode controller
  with CPU truth stepping and no Python episode-state ownership

Recorded progress at 2026-07-21 (I43): partially landed, opt-in.
`WorldBatchRuntime` owns a pooled `ExecutionEpisodeController` per world, and
Python has a working `execution_episode_controller_mainline` cutover
constructor flag on `WorldBatchVecEnv`
(`python/rl/runtime/world_batch/_execution_episode_mixin.py`) that steps
batches through `WorldBatchRuntime.step_execution_batch(...)` and bypasses
`ScenarioLoader.compute_full_step` entirely when enabled. It defaults to
`False` and is not yet feature-complete relative to the default path --
`_air_combat_post_launch_mixin.py` explicitly disables the post-launch
assessment feature under it, and it requires the compiled flight-shaping
backend. The exit criterion this section already states --  "maintained
`p5` execution path no longer depends on Python-owned hot-path episode
state" -- is therefore **not yet met**; `compute_full_step` remains the real
default. See "T4 Census (I43)" below for the full dual-ownership survey this
iteration ran before concluding no retirement was safe yet.

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
- [simulation_kernel.cpp](../../../../../src/core/engine/simulation_kernel.cpp)
- [world_batch_runtime.cpp](../../../../../src/core/engine/world_batch_runtime.cpp)

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

- [src/gpu/experimental](../../../../../src/gpu/experimental)
- [src/gpu/README.md](../../../../../src/gpu/README.md)
- [exact_stage_inventory.cpp](../../../../../src/core/engine/exact_stage_inventory.cpp)

Acceptance:

- maintained runtime can switch exact backend without changing Python episode
  ownership

## T4 Census (I43, 2026-07-21): Python Per-Step Builder Dual-Ownership Survey

Unified Architecture Program T4 ("Support WP4 hot-path switchover to
`WorldBatchRuntime`; retire Python per-step builders superseded by C++
ownership; re-freeze the exact-runtime plan document") opened with a
repo-wide census of hand-written Python per-step DTO construction under
`python/**` and `gym_envs/**`, cross-referenced against the C++ paths this
plan describes above. This section is additive: it supersedes no earlier
text and records the census plus its disposition for the next T4 slice.

### What the census found: three coexisting tiers, not one legacy path

The Python execution-step hot path
(`gym_envs/scenario_loader/step_evaluation.py`,
`execution_runtime/mainline.py`, `execution_runtime/shadow.py`, and the
`python/rl/runtime/world_batch/_execution_episode_mixin.py`/
`_observation_mixin.py` mixins) is not one Python-owned path with a single
C++ replacement waiting to land. It is three coexisting tiers, each with
real, distinct, currently-exercised consumers:

1. **Per-term consumption of the aggregated compiled product** --
   `ScenarioLoader.compute_full_step` is the real default orchestrator
   (governed by `use_compiled_execution_step_runtime`, default `True`): on
   the default path it consumes the sub-products of one aggregated
   `compute_execution_episode_runtime` call (prepared inside
   `_prepare_step_evaluation`) term by term, with per-term Python
   bookkeeping around them; genuinely per-term compiled calls
   (`compute_safety_runtime`/`compute_approach_reward_terms`/...) occur on
   cache-miss/partial-product paths and on the escape hatch when the flag
   is forced `False` -- a real, tested escape hatch
   (`tests/runtime/execution/test_scenario_loader_execution_step_runtime.py`),
   not a theoretical one, and the only tier that still functions there.
2. **Batch frame-product prepare** (`execution_step_batch_prepare=True` on
   `WorldBatchVecEnv`) -- Python hand-builds `StepEvaluationBatchConfig`/
   `StepEvaluationBatchEnvState` per env and calls
   `ef_py.prepare_step_evaluations_batch` once for the whole batch; the
   reward/termination extraction (tier 1's term-by-term `_add_reward_term`
   bookkeeping) still runs afterward in Python. Real and tested
   (`test_world_batch_vec_env_reuses_cached_step_evaluation_for_reward_tail`).
3. **Execution-episode-controller mainline**
   (`execution_episode_controller_mainline=True`) -- this is the tier WP4
   above describes, and it already exists in code: Python builds
   `WorldExecutionEpisodeStepRequest` per env and
   `WorldBatchRuntime.step_execution_batch(...)` owns the rest, with
   `ScenarioLoader.compute_full_step` never called. It defaults to `False`
   and `_air_combat_post_launch_mixin.py` explicitly disables the
   post-launch-assessment feature under it, so tier 3 is not yet
   feature-complete relative to tiers 1/2, and WP4's own exit criterion is
   not yet met (see the WP4 progress note above).

None of the three tiers is dead. Each has a distinct, named production
trigger (a constructor flag) or a dedicated regression test, matching this
plan's own Freeze Decision to "keep all current parity traces, stage
comparators, and resident-state probes as regression infrastructure." The
T4 double-ownership risk the program README names ("divergent
double-ownership during migration") is therefore confirmed present and
deliberate at this commit, not a defect to patch by this slice.

### One narrower pair, investigated and closed as held (not retired)

`gym_envs/scenario_loader/step_evaluation.py::prepare_step_evaluation`
dispatches `if loader._compiled_execution_episode_enabled(): ... elif
loader._compiled_execution_frame_enabled(): ...` between
`ExecutionEpisodeRuntimeInputs`/`compute_execution_episode_runtime`
(episode tier) and `ExecutionFrameRuntimeInputs`/
`compute_execution_frame_runtime` (frame tier). Both enabler predicates
share the identical gate (`use_compiled_execution_step_runtime` plus an
`hasattr` check that is always true together against the same compiled
`ef_py` binary, since both bindings live in the same translation unit with
no conditional compilation between them), so the `elif` cannot be reached by
any production configuration. A full-repo reference census confirmed this:
the only caller that ever observes the frame branch is
`test_scenario_loader_execution_step_runtime.py`, which monkeypatches
`loader._compiled_execution_episode_enabled`/`_compiled_execution_frame_enabled`
directly to force it, specifically to exercise the "frame" arm of the
`defer_compiled_runtime`/`compact_output` mechanism. `ExecutionFrameRuntimeInputs`/
`compute_execution_frame_runtime` remain real, separately used C++ assets:
`tests/runtime/mission/test_mission_runtime.py` calls the compiled function
directly, and
`tests/runtime/execution/test_execution_step_runtime.py::ExecutionEpisodeRuntimeTests::test_frame_compatibility_runtime_matches_episode_owner_across_batch_boundaries`
pins frame/episode numerical equivalence as a compatibility contract in its
own right. Only the Python dispatch's `elif` arm is unreachable in
production, and it is unreachable by construction (monkeypatch-only), not by
accident or drift. Disposition: held, not retired -- deleting it would edit
a directly-exercised test for zero behavior change on its own, so it is
registered here as a named, understood residual for whichever iteration
next revisits `prepare_step_evaluation`'s dispatch, rather than an isolated
deletion this slice would have to justify alone.

### Disposition and next-trigger condition

None of the three hot-path tiers qualifies for retirement at this commit:
every tier is either the real default consumer path (tier 1) or carries its
own dedicated, currently-green regression/parity test (tiers 2-3, and the
frame/episode dispatch above). The census's method-level sweep (a full
reference count over the ~591 functions/methods defined in the 29
stepping-layer modules) did, however, surface eight dead per-step builder
*interfaces* -- zero references anywhere outside their definition sites
(production, tests, tools, and fixtures all clean) -- and this slice retired
them per the I14 dead-interface-removal precedent: five `ScenarioLoader`
forwarding shells whose call sites had already sunk to the owning
module-level free functions (`_build_mission_nav_products`,
`_compute_mission_observation_products`, `_build_step_info_runtime_inputs`,
`_consume_compiled_episode_runtime`, `_build_waypoint_reward_inputs`; the
free functions themselves remain maintained tier-1/2 infrastructure), and
three methods superseded by the C++-backed batch paths --
`_WorldBatchVecEnvObservationMixin._collect_observations` (callers now drive
`_read_truth_and_inst_batch` + `_build_observations_from_cached_state`
directly), `_WorldBatchVecEnvExecutionEpisodeMixin.`
`_execution_episode_controller_state_requires_reprime` (the reprime decision
flows through the compiled `execution_episode_ready` instead of a
Python-side state digest), and `CooperativeWorldBatchVecEnv.`
`_build_slot_observation` (superseded by the batched
`compute_execution_observation_batch` path riding
`ef_py.compute_execution_observation_batch_numpy`). All eight are private
names, so the Non-Goals public-surface clause is untouched, and the removal
is zero-behavior-change by construction. The trigger condition for the next
real (tier-level) retirement is explicit: once tier 3
(`execution_episode_controller_mainline`) covers the post-launch-assessment
path and every tier 1/2 `flight_shaping_backend` option, and is promoted
from opt-in to default, tier 1's `compute_full_step` term-by-term
orchestration becomes the retirement target this program's README already
names.

### Default-flip addendum (I82, 2026-07-27): covered cells resolved, flip HELD pending performance

This addendum records a partial trigger of the condition above, with the
flip itself HELD. With the coverage matrix landed (I80) and the disposition
adjudicated (I81/I91), the `execution_episode_controller_mainline`
constructor default moved from a hard `False` to an unset sentinel resolved
at construction
(`WorldBatchVecEnv._resolve_execution_episode_controller_mainline_default`).
The resolver encodes the full covered-cell ownership rule -- compiled/auto
flight shaping, post-launch assessment not configured, action mode in the
parity-pinned whitelist (`full`/`takeoff2`/`takeoff4`, each with its own
cross-layer parity pin; whitelist polarity, so new action modes default to
the Python path), no scripted opponents declared in the scenario, no second
entity side declared in the scenario, no tier-2
`execution_step_batch_prepare` opt-in, and the runtime episode-controller
APIs present -- but the flip is DISARMED behind the module constant
`_CONTROLLER_DEFAULT_FLIP_ARMED = False`
(python/rl/runtime/world_batch/vec_env.py): while it is `False`, every
unset default resolves to the Python-orchestrated path, and a cell the rule
would have flipped reports the named reason
`default_off_covered_cell_flip-held-pending-performance` through the
resolution introspection attribute.

Held ruling (2026-07-27, issued under explicit owner delegation -- the
owner's "允许代签" authorization -- and recorded as a delegated program
ruling, not as human expert judgment): the plan's Acceptance Criteria
require the compiled episode cutover to improve maintained execution
rollout wall-clock beyond noise, and the slice's own hot-path measurement
showed the controller path 20-30% SLOWER on the inline micro fixture
(n_envs=1 medians 0.297 vs 0.244 s/100 steps; n_envs=8 medians 2.409 vs
1.869). The default flip is therefore held pending representative-scenario
wall-clock evidence; per the program's performance boundary, that
performance work routes to the exact-runtime line, which owns the arming
condition (a representative-scenario measurement showing the controller
path improves maintained rollout beyond noise).

Everything else the slice built is kept. Every non-covered configuration
resolves to the Python-orchestrated path with a named reason and never
errors (gpu_host stays HELD on the Python path; post-launch-configured runs
bind the red line because the mainline hard-disables the assessment;
`naval_station3` keeps the Python-owned naval reward surface -- direct
evidence: the controller path does not produce
`naval_station_error_penalty`; multi-side scenarios keep the Python-owned
combat products -- direct evidence: the controller path reports generic
`timeout` where tier 1 reports `combat_win`/`combat_timeout`; scripted
opponents are Python-stepped by `update_behaviors`, which the mainline
replaces with `update_command_chain_only`). Explicit `True`/`False` keep
their exact pre-flip semantics -- the public kwarg name is unchanged, and
the covered-cell cross-layer parity evidence (explicit controller vs
explicit Python path) stays green as explicit-opt-in parity. Tier-1
retirement did NOT happen in this slice: `compute_full_step` orchestration,
the post-launch mixin, the shadow comparator, and the tier-2 reward tail
all remain reachable from the excluded cells and from explicit `False`, so
the shrink-only deletion list for this slice is empty by adjudication
(deletion trails a later slice, after the excluded cells gain
controller-side owners and the flip arms). Evidence:
tests/runtime/exact/test_execution_controller_option_parity.py (held-flip
default-resolution pins on the covered cells, explicit-opt-in cross-layer
parity pins, excluded-cell resolution pins, and the recorded hot-path
measurement).

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
- `tests/runtime/execution/test_execution_episode_controller_parity.py`
- `tools/diagnostics/compare_execution_episode_controller_parity.py`

### Existing files likely to change early

- [execution_episode_batch_prepare.h](../../../../../src/core/mission/episode/execution_episode_batch_prepare.h)
- [execution_episode_batch_prepare.cpp](../../../../../src/core/mission/episode/execution_episode_batch_prepare.cpp)
- [world_batch_runtime.h](../../../../../src/core/engine/world_batch_runtime.h)
- [world_batch_runtime.cpp](../../../../../src/core/engine/world_batch_runtime.cpp)
- [python_module.cpp](../../../../../src/interfaces/python/python_module.cpp)
- [gym_envs/scenario_loader/core.py](../../../../../gym_envs/scenario_loader/core.py)
- [world_batch_vec_env.py](../../../../../python/rl/runtime/world_batch_vec_env.py)

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
