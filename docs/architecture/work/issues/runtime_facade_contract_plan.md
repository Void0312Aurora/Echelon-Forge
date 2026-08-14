# Runtime Facade Interface Contract Proposal

Language:
- English canonical: `runtime_facade_contract_plan.md`
- Chinese companion: not maintained (English-only work surface).

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/architecture/work/issues/runtime_facade_contract_plan.md`
Owner: `architecture/runtime-facade`
Last verified: `2026-08-13`
Content status: migrated interface proposal; current public surfaces and code
must be re-censused before any portion is promoted into an active task.

Document Navigation:

- [Architecture Documentation](../../README.md)
- [system_layering_and_engine_encapsulation_plan.md](system_layering_and_engine_encapsulation_plan.md)
- [architecture_and_performance_research_followup.md](architecture_and_performance_research_followup.md)
- runtime_facade_task_bootstrap_plan.zh.md (`git show 3dc34673:docs/plan/archive/runtime_facade/runtime_facade_task_bootstrap_plan.zh.md`)
- runtime_facade_layering_cleanup_freeze.zh.md (`git show 3dc34673:docs/plan/archive/runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md`)

Status: draft issue derived from the `2026-05-10` interface proposal; it is
not an active execution contract.

Current-state note (2026-08-13): the compiled episode-controller experiment,
its `ExecutionBatchStepRequest`/`ExecutionBatchStepResult` facade surface, and
the controller state prime/step/export APIs were retired. The capability field
is retained as a negative capability (`false`). Controller-specific interfaces
below describe the historical proposal, not the current facade contract.

Document Positioning:

- This document answers "What facade boundary should the frontend under maintenance depend on, and how should the core request/response/handle be defined."
- This document is the interface design basis for the runtime facade, but it is not an automatically effective frozen execution order.
- Any implementation work derived from this proposal must have its scope closed through a separately frozen execution plan.

This document proposes a `runtime facade` contract direction intended to isolate the frontend from the underlying
`WorldBatchRuntime` / `SimulationKernel` / `ExecutionEpisodeController`.

Related Documents:

- [system_layering_and_engine_encapsulation_plan.md](system_layering_and_engine_encapsulation_plan.md)
- [architecture_and_performance_research_followup.md](architecture_and_performance_research_followup.md)
- [cpp_exact_runtime_refactor_plan.md](exact_runtime/cpp_exact_runtime_refactor_plan.md)
- runtime_facade_layering_cleanup_freeze.zh.md (`git show 3dc34673:docs/plan/archive/runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md`)

## I. Document Purpose

This document answers five questions:

1. What problem does `runtime facade` aim to solve.
2. What is its relationship with `WorldBatchRuntime` and `SimulationKernel`.
3. Through what interface should the frontend under maintenance interact with the backend.
4. How this contract reserves interfaces for future C++ sinking, CUDA, resident-state, and remote service orientation.
5. Which interfaces should be implemented first in the first batch, and which should temporarily stay out of the mainline.

## II. Why Runtime Facade Must Be Introduced Now

The current repository already has strong compile-side runtime capabilities, but it still lacks a stable upper-layer contract.

Current issues:

1. The Python frontend still directly depends on many underlying runtime behaviors.
2. `python_module.cpp` directly exposes a large number of low-level APIs, making it easy for the frontend to bypass the boundary.
3. `WorldBatchVecEnv` still assembles a lot of request / state mirror / step consume logic on its own.
4. If C++ ownership, CUDA device-resident path, or service-oriented runtime continue to be promoted, these frontends will continue to suffer from unstable interfaces.

Therefore, a clear goal is needed now:

`The frontend no longer depends on the fragmented capabilities of the underlying runtime, but on a set of maintained, use-case-oriented stable facade interfaces.`

## III. Facade Role Positioning

### 1. Facade is Not a New Engine

`runtime facade` is not a new engine to replace the simulation engine.
Its positioning is:

- Expose stable contracts to the frontend
- Hide the combination details of underlying engines
- Aggregate multiple runtime capability points from the underlying layer
- Provide a stable upper boundary for future backend switching or deployment forms

That is:

- `SimulationKernel` is still responsible for precise world semantics
- `WorldBatchRuntime` is still responsible for batch runtime and world ownership
- `ExecutionEpisodeController` is still responsible for compiled episode ownership
- `runtime facade` is responsible for organizing these capabilities into an API set that the frontend can depend on

### 2. Direct Service Targets of Facade

The direct service targets of the first phase facade should include:

- `WorldBatchVecEnv`
- `UniversalEnv`
- Training entry `train.py`
- Diagnostic benchmark tools
- Future visualization or service-oriented frontends

### 3. Core Constraints of Facade

The facade must simultaneously satisfy:

1. Batch-oriented, not only single-world oriented.
2. Typed request/response oriented, not free-assembled dictionaries.
3. Reserve exit points for device-resident / DLPack.
4. Support gradual migration, not a one-time rewrite of all frontends.

## IV. Facade Design Goals

### Goal 1: Stabilize Use Case Boundaries

The frontend should interact with the backend through these high-level use cases:

- world/batch initialization
- scenario/layout application
- reset
- step
- observation retrieval
- runtime state import/export
- diagnostics/trace requests

Rather than directly calling:

- Certain kernel internal set/get component methods
- Certain phased probe helpers
- Certain low-level controller internal functions

### Goal 2: Shield Underlying Ownership Changes

These future changes should not require the frontend to be rewritten:

- `ScenarioLoader` no longer holds authoritative episode state
- `ExecutionEpisodeController` becomes the main owner
- `WorldBatchRuntime` adds physics backend selection
- `WorldBatchRuntime` adds resident-state mode
- observation switches from host copy to device view

### Goal 3: Natively Support Performance Optimization

The facade design must consider from the start:

- batch request/response
- Reduce Python round trips
- Device view export
- Optional zero-copy data paths
- Minimal-sync / partial-sync contract

Otherwise, new performance bypasses will continue to grow on top of the facade.

## V. What Facade Should Not Do

`runtime facade` should not assume:

- Physics computation
- Mission semantic decision logic itself
- Frontend strategy logic
- Training algorithm logic
- Low-level probe detail exposure

It is not:

- `ScenarioLoader v2`
- Another name for `WorldBatchVecEnv`
- A verbatim copy of `python_module.cpp`

## VI. Target Interface Layering

It is recommended to split the facade contract into four interface groups, rather than one large class.

### A. Runtime Lifecycle Facade

Responsible for:

- Runtime creation and destruction
- Batch/world capacity configuration
- Base capability negotiation

Suggested responsibilities:

- Create runtime session
- Configure worker_threads
- Query backend capabilities
- Query device capabilities

### B. Scenario / World Setup Facade

Responsible for:

- Applying compiled scenario content
- World layout application
- Batch reset
- Seed / randomization entry

Suggested responsibilities:

- Load database
- Load unit definitions
- Apply world setup/layout
- Reset batch

### C. Execution Step Facade

Responsible for:

- Execution mainline reset/step
- Request packaging
- Compiled episode state priming
- Observation / reward / done / info result return

This is the core facade under maintenance.

### D. Diagnostics / Export Facade

Responsible for:

- Diagnostic data export
- Trace / state snapshot
- Candidate queries
- Experiment-only GPU or exact-state hooks

This group of interfaces can first be retained as "secondary stable interfaces," not requiring the same strict freezing as the mainline rollout contract.

## VII. Proposed Core Contract Objects

The following defines "facade-level objects," not direct mappings of underlying internal structures.

### 1. RuntimeCapabilities

Purpose:

- Let the frontend know which mainline capabilities the current runtime possesses

Suggested fields:

- `supports_batch_runtime`
- `supports_compiled_episode_controller`
- `supports_compiled_execution_step`
- `supports_gpu_visual`
- `supports_gpu_observation`
- `supports_gpu_flight_shaping`
- `supports_device_observation_view`
- `supports_resident_state`
- `supports_exact_gpu_backend`
- `supports_shadow_compare`

Note:

- This is the facade capability negotiation object
- The frontend should no longer probe everywhere via `hasattr(ef_py, ...)`

### 2. RuntimeBatchConfig

Purpose:

- Define the long-term configuration for batch runtime, rather than passing repeatedly each step

Suggested fields:

- `world_count`
- `worker_threads`
- `mission_obs_mode`
- `include_visual`
- `include_proprio`
- `observation_return_mode`
- `execution_step_runtime_mode`
- `flight_shaping_backend`
- `execution_episode_controller_mode`
- `policy_observation_bridge_enabled`

### 3. BatchWorldSetupRequest

Purpose:

- Initialize or reset a batch of worlds

Suggested fields:

- `seeds`
- `terrain_assignments`
- `wind_assignments`
- `zone_definitions`
- `spawn_requests`
- `time_steps`
- `randomization_overrides`

### 4. BatchResetRequest

Purpose:

- Express "which worlds to reset, with which seeds, whether to rebuild layout"

Suggested fields:

- `target_world_indices`
- `seed_base` or `seeds`
- `rebuild_layout`
- `randomization_overrides`

### 5. ExecutionBatchStepRequest

Purpose:

- Express all high-level inputs for the mainline step call

Suggested fields:

- `pilot_action_assignments`
- `mission_command_assignments`
- `task_order_assignments`
- `leader_intent_assignments`
- `pilot_report_assignments`
- `step_mode`
- `observation_request`
- `timing_enabled`

Note:

- The first phase does not require carrying all low-level debug switches here
- Should prioritize serving the main rollout path under maintenance

### 6. ExecutionBatchStepResult

Purpose:

- As the unified output object for the mainline `step()` under maintenance

Suggested fields:

- `observations`
- `rewards`
- `terminated`
- `truncated`
- `infos`
- `runtime_timing`
- `controller_state_changed_flags`
- `status_vectors`

### 7. RuntimeStateSnapshot

Purpose:

- Unify the representation of importable/exportable runtime state

Suggested fields:

- `execution_episode_states`
- `mission_commands`
- `task_orders`
- `leader_intents`
- `pilot_reports`
- `truth_observations`
- `instrument_states`

First phase suggests freezing only:

- `ExecutionEpisodeState` as the stable main object

Other content can be added gradually by purpose.

### 8. ObservationBatchPacket

Purpose:

- Unify the observation packet exposed to the frontend

Suggested fields:

- `host_observation_dict`
- `device_observation_view`
- `layout_metadata`
- `terminal_observation_mask`

Note:

- It is not a simple numpy dict
- It does not directly expose underlying GPU tensors
- It is the facade-level unified observation packet

## VIII. Proposed Main Interface Set

Below are the facade-level interfaces recommended for freezing in the first phase.

### 1. `create_runtime_session(config) -> RuntimeSessionHandle`

Purpose:

- Create a runtime session under maintenance

Corresponds to current underlying:

- `WorldBatchRuntime(world_count)`
- Basic parameter and capability initialization

### 2. `get_runtime_capabilities(session) -> RuntimeCapabilities`

Purpose:

- Get the externally available capabilities of the current session

Advantages:

- Replace the scattered `hasattr` probing logic in the frontend

### 3. `apply_batch_world_setup(session, request) -> BatchWorldSetupResult`

Purpose:

- Batch apply world setup/layout

Corresponds to current underlying:

- `apply_world_setup_batch(...)`

### 4. `reset_execution_batch(session, request) -> ExecutionBatchResetResult`

Purpose:

- Mainline execution reset entry under maintenance

It should be internally responsible for:

- Reset worlds
- Prime execution episode state
- Build initial observation packet

The frontend should no longer assemble on its own:

- reset -> read truth -> read inst -> sync command chain -> build obs

### 5. `step_execution_batch(session, request) -> ExecutionBatchStepResult`

Purpose:

- Mainline step API under maintenance

It should be internally responsible for:

- Apply actions/commands
- Step worlds
- Compiled episode mainline or legacy fallback
- Aggregate observation / reward / termination / info

The frontend should no longer stitch these phases on its own.

### 6. `export_runtime_state(session, request) -> RuntimeStateSnapshot`

Purpose:

- Export current runtime state under maintenance

First phase primarily serves:

- Shadow compare
- Debug
- Resumable rollout

### 7. `import_runtime_state(session, request) -> ImportResult`

Purpose:

- Import runtime state

First phase primarily serves:

- Controller priming
- Exact state roundtrip test
- Future resumable training / diagnostics

### 8. `get_observation_packet(session, request) -> ObservationBatchPacket`

Purpose:

- Fetch the current observation packet separately

Primarily serves:

- Read observations after reset
- Certain diagnostic or polling scenarios

### 9. `run_diagnostics(session, request) -> DiagnosticsResult`

Purpose:

- Unified encapsulation of diagnostic entry

First phase does not need to merge all probes, but it is recommended to reserve a unified facade entry.

## IX. Mainline and Experimental Interface Classification

It is recommended to classify facade interfaces into two stability levels.

### Level 1: Mainline Interfaces Under Maintenance

Interfaces that must be stable:

- `create_runtime_session`
- `get_runtime_capabilities`
- `apply_batch_world_setup`
- `reset_execution_batch`
- `step_execution_batch`
- `export_runtime_state`
- `import_runtime_state`
- `get_observation_packet`

These interfaces are the main dependency targets for future frontends.

### Level 2: Experimental and Diagnostic Interfaces

Interfaces that can retain room for evolution:

- exact-state packed import/export
- Exact GPU backend opt-in entry
- Candidate helper probes
- Stage trace / parity compare
- Resident-state experiment-only hooks

They can continue to be exposed by the underlying runtime or diagnostics facade, but should not pollute the mainline step contract.

## X. Mapping Relationship with Existing `WorldBatchRuntime`

The existing [world_batch_runtime.h](../../../../src/core/engine/world_batch_runtime.h)
already has many basic capabilities and is suitable as the base for the facade.

### Currently Available Base Capabilities

- `reset_batch`
- `step_batch`
- `apply_world_setup_batch`
- `set_*_batch`
- `prime_execution_episode_controller_batch`
- `step_execution_episode_results_batch`
- `export_execution_episode_states_batch`
- `get_*_batch`
- GPU broadphase candidate helpers

### Currently Missing Upper-Level Integration Capabilities

What is missing is the aggregation and freezing that the facade should do, not the underlying primitives:

1. High-level request/result contract for reset/step
2. Capability negotiation object
3. Unified expression of observation packet
4. Host/device dual-view abstraction
5. Clear classification of mainline and experimental lines

Therefore:

- Rewriting `WorldBatchRuntime` is not recommended
- It is recommended to build the facade layer on top of it

## XI. Device-View and Zero-Copy Reservation

The facade design must explicitly support three observation return modes:

### Mode A: Host copy

Most conservative, highest compatibility.

### Mode B: Host view

Used for single-process world-batch mainline optimization.

### Mode C: Device view

Aimed at:

- DLPack
- Torch direct consumer
- Future device-resident rollout path

Therefore, the facade contract should allow:

- `observation_access_mode = copy | view | device_view`

Rather than scattering this concept across frontend wrapper implementations.

## XII. Gradual Migration Strategy

### Phase 1: Only Define Contracts, No Ownership Changes

Goal:

- First define facade-level types and APIs
- Internally still call existing `WorldBatchRuntime` and loader helper logic

Success criteria:

- New or refactoring frontends can start depending on the facade contract

### Phase 2: Switch `WorldBatchVecEnv` to Facade

Goal:

- Keep behavior unchanged
- Change current request build / step consume / observation fetch to use facade

Success criteria:

- `WorldBatchVecEnv` no longer directly depends on too many underlying runtime details

### Phase 3: Narrow `ScenarioLoader` Role

Goal:

- `ScenarioLoader` is no longer a runtime backend shell
- Only retain the scenario adaptation and frontend helper role

Success criteria:

- Clear boundary between compiled ownership mainline and loader mirror mainline

### Phase 4: Add Facade-Level Backend Switch for Resident-State / Exact Backend

Goal:

- Future backend selection does not affect the frontend contract

## XIII. First Batch Implementation Suggestions (Design Decomposition, Not Execution Freeze)

Note: This section is used to decompose the interface landing order. The actual first batch execution scope is subject to the subsequent frozen document
runtime_facade_task_bootstrap_plan.zh.md (`git show 3dc34673:docs/plan/archive/runtime_facade/runtime_facade_task_bootstrap_plan.zh.md`).

Update note: The first batch `WP1-WP6` has been completed; the next batch candidate layering cleanup scope has been converged into
runtime_facade_layering_cleanup_freeze.zh.md (`git show 3dc34673:docs/plan/archive/runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md`).

It is suggested to split the implementation into four minimal work packages.

### WP1: Freeze Facade Contract Objects

Output:

- Facade document
- Type sketches
- Naming freeze

Recommended priority objects:

- `RuntimeCapabilities`
- `RuntimeBatchConfig`
- `BatchResetRequest`
- `ExecutionBatchStepRequest`
- `ExecutionBatchStepResult`
- `ObservationBatchPacket`

### WP2: Add Facade Adapter Prototype Layer

Output:

- A minimal Python-facing facade wrapper
- First wrap `WorldBatchRuntime`

Goal:

- Do not change behavior
- First change dependency direction

### WP3: Connect `WorldBatchVecEnv`'s reset/step Path to Facade

Output:

- Frontend starts depending on facade, not directly assembling runtime plumbing

### WP4: Reserve Interfaces for Device-View and Capability Negotiation

Output:

- Add capability negotiation to facade
- Reserve device-view fields in observation packet

## XIV. Things Not Recommended to Do Immediately

The following are not recommended to be done together with the first phase of facade:

- Merge all probe APIs into the facade at once
- Incorporate exact GPU backend into mainline facade at once
- Forcibly implement a remote RPC version in facade's first phase
- Large-scale renaming or directory migration of frontends at once

First, establish contracts, then gradually switch traffic; this carries lower risk.

## XV. Final Recommendation

The first phase goal of `runtime facade` is not to "invent a large and complete new runtime system," but to:

1. Freeze the upper boundary that the frontend under maintenance should depend on.
2. Package the fragmented underlying runtime capabilities into stable use-case APIs.
3. Reserve unified interfaces for future C++ ownership, CUDA resident-state, device view, and service-oriented deployment.

Therefore, the most appropriate implementation strategy is:

- First, freeze the documentation
- Then, build a minimal facade prototype
- Then, integrate `WorldBatchVecEnv`
- Then, continue to drive deeper backend ownership refactoring

In this way, the true decoupling between frontend and backend will start to happen, rather than remaining at the conceptual level.
