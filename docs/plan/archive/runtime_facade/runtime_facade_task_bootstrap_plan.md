<!-- Machine-translated draft generated on 2026-05-18 from docs/plan/runtime_facade/runtime_facade_task_bootstrap_plan.zh.md. Review before treating this file as authoritative. -->

# Runtime Facade Task Launch Preparation Plan

Document Navigation:

- [README.md](../README.md)
- [system_layering_and_engine_encapsulation_plan.zh.md](../architecture/system_layering_and_engine_encapsulation_plan.zh.md)
- [architecture_and_performance_research_followup.zh.md](../architecture/architecture_and_performance_research_followup.zh.md)
- [runtime_facade_contract_plan.zh.md](runtime_facade_contract_plan.zh.md)
- [runtime_facade_layering_cleanup_freeze.zh.md](runtime_facade_layering_cleanup_freeze.zh.md)

Status: `2026-05-10` execution record frozen (first batch `WP1-WP6` completed).  
Document positioning:

- This document was previously used to freeze the first batch of runtime facade launch tasks, and is now retained as an execution record.
- This document only covers the freezing scope, completion status, regression results, and benchmark artifacts for `WP1-WP6`.
- If subsequent work continues on facade contract deepening, device-view, resident-state, exact backend, etc., a separate freeze execution document must be created or updated.
- The next batch of candidate layering cleanup work has been consolidated into
  [runtime_facade_layering_cleanup_freeze.zh.md](runtime_facade_layering_cleanup_freeze.zh.md).

This document is used to transform
[runtime_facade_contract_plan.zh.md](runtime_facade_contract_plan.zh.md)
into executable first batch of tasks; this batch of tasks has now been fully completed.

Implementation progress:

- Already added `src/runtime/facade/runtime_facade_types.h`
- Already added `src/runtime/facade/runtime_facade.h`
- Already added `src/runtime/facade/runtime_facade.cpp`
- `RuntimeFacade` and the first batch of facade types have been exposed in [python_module.cpp](../../../src/interfaces/python/python_module.cpp)
- Added [test_runtime_facade.py](../../../tests/runtime/facade/test_runtime_facade.py) as the minimal regression entry point

Current phase description:

- This document only freezes the first batch of tasks, i.e., `WP1` to `WP6`
- `WP4` mainline path access has been completed
- Facade still directly wraps `WorldBatchRuntime`
- `WorldBatchVecEnv.reset()` main path has been prioritized for facade access
- `WorldBatchVecEnv.step_wait()` main path, execution episode controller mainline / shadow compare sub-paths, and batch action dispatch / command-chain synchronization / state readback have all been switched to facade-first
- Single world autoreset still retains local world apply logic, but subsequent readback and command-chain synchronization have been aligned with the facade-first main path
- Currently, no further expansion of unfrozen facade contract deepening scope is allowed; any subsequent work on `observation / reward / info` contract deepening, device-view, resident-state, exact backend, etc., must be independently projectized and refrozen before launch

Related documents:

- [system_layering_and_engine_encapsulation_plan.zh.md](../architecture/system_layering_and_engine_encapsulation_plan.zh.md)
- [architecture_and_performance_research_followup.zh.md](../architecture/architecture_and_performance_research_followup.zh.md)
- [runtime_facade_contract_plan.zh.md](runtime_facade_contract_plan.zh.md)
- [runtime_facade_layering_cleanup_freeze.zh.md](runtime_facade_layering_cleanup_freeze.zh.md)

## Zero. Freeze Execution Boundary

This round only allows execution of the following frozen scope:

1. `WP1` Facade contract object definition
2. `WP2` Facade prototype layer implementation
3. `WP3` Python binding entry point
4. `WP4` `WorldBatchVecEnv` mainline path integration
5. `WP5` Regression test completion and verification
6. `WP6` Baseline verification

This round does not allow execution of the following unfrozen content:

- Adding any contract deepening work beyond `WP`
- Extending `ExecutionBatchStepResult` into a new high-level DTO family
- Advancing facade-level `device_view`, resident-state, exact backend toggles
- Major splitting of `ScenarioLoader` or further ownership sinking
- Any "convenient further optimizations" not explicitly written in this document

Execution rules:

1. If a certain piece of work does not directly serve the acceptance criteria of `WP1` to `WP6`, it must not be started.
2. If a certain piece of work requires a new scope, this document must be modified and frozen first before entering implementation.
3. Any increments that already exist in the current code but are not written into the frozen targets of this document shall not be used as a basis for continued expansion.

## Zero Point One. Current WP Status

- `WP1`: Completed
- `WP2`: Completed
- `WP3`: Completed
- `WP4`: Completed
- `WP5`: Completed
- `WP6`: Completed

The first batch of frozen tasks has been fully completed.

Baseline results and test results record:

1. `WP5` frozen test suite:
   `tests/world_batch/test_world_batch_vec_env.py`
   `tests/runtime/execution/test_execution_episode_controller.py`
   `tests/runtime/execution/test_execution_episode_state.py`
   `tests/runtime/execution/test_execution_episode_batch_prepare.py`
   `tests/runtime/facade/test_runtime_facade.py`
   Result: `41 passed`
2. `WP6` `benchmark.py --family world_batch_vec_env`
   Output file:
   [wp6_benchmark_world_batch_vec_env_phase4.json](../results/wp6_benchmark_world_batch_vec_env_phase4.json)
3. `WP6` `benchmark.py --family policy_observation_bridge`
   Currently `build-facade-local` lacks the CUDA runtime bridge binding required by this script; the script returns as expected:
   `CUDA runtime is not available for the bridge benchmark.`

## I. Objective

The first batch does not aim to complete the full architectural switch in one go, but to achieve the following three launch goals:

1. First freeze a maintainable version of the facade contract and the minimum set of objects.
2. Set up a prototype facade layer that does not change behavior.
3. Have some mainline paths of `WorldBatchVecEnv` start depending on the facade instead of directly piecing together underlying runtime details.

## II. Launch Principles

### Principle 1: Change dependency direction first, then semantic ownership

That is, in the first phase, the interior of facade is allowed to still call:

- `WorldBatchRuntime`
- `ScenarioLoader` auxiliary logic
- current observation building paths

But the frontend dependency direction must be changed first.

### Principle 2: Switch reset/step main paths first, do not unify all probes at once

The first phase only serves the main execution rollout path under maintenance.

It is not required to unify in the first batch:

- exact-state probe
- experimental GPU backend switch
- all diagnostics helpers

### Principle 3: All changes must be verifiable by regression

The first batch must be verifiable against existing tests and benchmarks.

## III. First Batch Delivery Scope

### In Scope

- Facade contract object definition
- Facade prototype implementation skeleton
- Initial integration of `WorldBatchVecEnv` reset/step paths
- Capability negotiation object
- Observation packet shell
- Minimal regression test

### Out Of Scope

- Full splitting of `ScenarioLoader`
- Mainline switch to exact GPU backend
- Mainline integration of resident-state
- RPC/service deployment
- Major directory migration
- Facade contract deepening not individually frozen

## IV. Suggested Work Package Breakdown

### WP1: Define Facade Contract Objects

Objective:

- Establish facade-level request/response/capability types at the code level

Suggested file locations:

- `src/runtime/facade/runtime_facade_types.h`
- Later if needed: `src/runtime/facade/runtime_facade_types.cpp`

Suggested first batch types:

- `RuntimeCapabilities`
- `RuntimeBatchConfig`
- `BatchResetRequest`
- `ExecutionBatchStepRequest`
- `ExecutionBatchStepResult`
- `ObservationBatchPacket`

Acceptance criteria:

- Type names and field semantics are consistent with the document
- The first batch of fields does not need to be perfect, but must stably describe the mainline reset/step use cases

### WP2: Implement Minimal Facade Prototype Layer

Objective:

- Add a facade class that wraps `WorldBatchRuntime`

Suggested file locations:

- `src/runtime/facade/runtime_facade.h`
- `src/runtime/facade/runtime_facade.cpp`

Suggested first batch interfaces:

- `create_session` or constructor
- `capabilities()`
- `reset_execution_batch(...)`
- `step_execution_batch(...)`
- `export_runtime_state(...)`

Implementation strategy:

- First phase can directly delegate to existing `WorldBatchRuntime`
- Allow temporary calls to loader auxiliary logic if necessary

Acceptance criteria:

- Does not change current maintenance semantics
- Facade can independently carry reset/step main use cases

### WP3: Add Python Binding Entry Point

Objective:

- Allow Python frontend to call the new facade prototype

Suggested file location:

- [python_module.cpp](../../../src/interfaces/python/python_module.cpp)

Suggested new bound objects:

- `RuntimeFacade`
- `RuntimeCapabilities`
- Facade-level request/result types

Acceptance criteria:

- Python side can instantiate the facade
- Can call reset/step from Python

### WP4: Integrate `WorldBatchVecEnv`

Objective:

- Have one mainline path of `WorldBatchVecEnv` start depending on facade

Suggested scope:

- First switch `reset()`
- Then switch `step_wait()` main path

Note:

- First phase does not require deleting all old logic
- Can keep a fallback path for now
- Currently implemented incremental strategy: `reset()` switches main path first, then the runtime orchestration responsibility of `step_wait()` is gradually shifted to facade-first

Acceptance criteria:

- Existing mainline tests do not regress
- Observation, reward, termination semantics remain consistent

### WP5: Supplement Regression Tests

Objective:

- Protect the first batch of switching with existing runtime and world-batch tests

Key test files:

- [tests/world_batch/test_world_batch_vec_env.py](../../../tests/world_batch/test_world_batch_vec_env.py)
- [tests/runtime/execution/test_execution_episode_controller.py](../../../tests/runtime/execution/test_execution_episode_controller.py)
- [tests/runtime/execution/test_execution_episode_state.py](../../../tests/runtime/execution/test_execution_episode_state.py)
- [tests/runtime/execution/test_execution_episode_batch_prepare.py](../../../tests/runtime/execution/test_execution_episode_batch_prepare.py)

Suggested new test directions:

- Facade reset behavior consistent with existing reset
- Facade step output consistent with existing mainline path
- Capability negotiation result stable

Freeze completion standard supplement:

- At least complete the verification of key runtime/world-batch tests listed in this document
- Do not replace `WP5` completion declaration with scattered targeted subsets

Execution result:

- Completed verification of the frozen test suite listed in the document
- Fixed runtime environment:
  `CMO_BUILD_DIR=build-facade-local`
  `LD_LIBRARY_PATH=/home/void0312/Workshop/CMO/build-facade-local/_deps/flecs-build:/home/void0312/Workshop/CMO/build-facade-local`
- Result: `41 passed`

### WP6: Supplement Baseline Verification

Objective:

- Confirm that introducing facade does not degrade mainline performance

Suggested benchmark file:

- [tools/diagnostics/benchmark.py](../../../tools/diagnostics/benchmark.py)

Acceptance criteria:

- Introducing facade should not significantly reduce current mainline throughput
- Any small extra overhead must be offset by clear benefits in subsequent ownership and contract stability

Freeze completion standard supplement:

- At least run the benchmark script listed in this document and record results
- Do not declare the first batch overall closed before `WP6` is completed

Execution result:

- Run `benchmark.py --family world_batch_vec_env`
  Record file:
  [wp6_benchmark_world_batch_vec_env_phase4.json](../results/wp6_benchmark_world_batch_vec_env_phase4.json)
  Summary:
  `n_envs=8`
  `dummy_reset_ms=10.051270`
  `world_batch_reset_ms=11.891172`
  `reset_speedup=0.85x`
  `dummy_ms_per_env_step=0.392506`
  `world_batch_ms_per_env_step=0.292365`
  `step_speedup=1.34x`
- Run `benchmark.py --family policy_observation_bridge`
  Current result is not a performance number but a precondition failure record:
  The `ef_py` of current `build-facade-local` does not include the CUDA runtime bridge binding required by this script, so the script returns
  `CUDA runtime is not available for the bridge benchmark.`
  This result has been recorded as part of this freeze execution record, rather than expanding scope to add a new build chain

## V. Suggested Implementation Order

Suggested order:

1. `WP1` Type freeze
2. `WP2` C++ facade prototype
3. `WP3` Python binding
4. `WP5` Minimal regression test
5. `WP4` `WorldBatchVecEnv.reset()` integration
6. `WP4` `WorldBatchVecEnv.step_wait()` integration
7. `WP6` Baseline review

Reasoning:

- First establish contracts and types
- Then gradually migrate frontend traffic
- Avoid inventing a "fake facade" in Python first

## VI. Suggested Minimal Code Skeleton

First phase can adopt a very conservative structure:

```text
src/runtime/facade/
  runtime_facade_types.h
  runtime_facade.h
  runtime_facade.cpp
```

Suggested minimal class form in `runtime_facade.h`:

- `class RuntimeFacade`
- Internally holds `WorldBatchRuntime`
- Provides facade-level reset / step / export_state / capabilities

The key here is not to make it very generic on the first attempt, but to extract the dependency boundary first.

## VII. Precondition Checks

Before starting implementation, confirm the following preconditions:

1. Current `WorldBatchRuntime` as the base is sufficiently stable.
2. Existing tests for `ExecutionEpisodeState` / `ExecutionEpisodeController` are green.
3. `WorldBatchVecEnv` mainline benchmark script is available for before/after comparison.
4. Do not simultaneously perform large-scale `ScenarioLoader` semantic restructuring in the same round.

## VIII. Risk List

### Risk 1: Facade just adds another layer without changing dependency direction

Mitigation:

- Have at least one mainline path of `WorldBatchVecEnv` go through the facade in the first phase

### Risk 2: Facade design is too close to current implementation details

Mitigation:

- Name request/response with high-level use case names
- Avoid simply copying all `WorldBatchRuntime::*_batch` methods one-to-one

### Risk 3: Facade Phase 1 scope is too large

Mitigation:

- Only serve the reset/step mainline under maintenance
- Keep probes/diagnostics as secondary interfaces

### Risk 4: Semantic drift during switching

Mitigation:

- Protect with existing shadow compare, episode state roundtrip, world-batch tests

### Risk 5: Re-architecting `ScenarioLoader` at the same time causing task explosion

Mitigation:

- Facade Phase 1 allows internal temporary dependence on loader auxiliary logic
- `ScenarioLoader` splitting is a separate task for the next batch

## IX. Subsequent Candidate Items (Require Separate Freeze)

If the first batch is completed, the most natural continuation items for the next batch are:

1. Splitting the execution-state adapter of `ScenarioLoader`
2. Introducing `device_view` in facade-level observation packet
3. Facade-level capability negotiation integrating GPU helper capabilities
4. Facade-level backend mode reserving resident-state / exact backend toggle bits

Note:

- This section only lists candidate directions and does not constitute the current frozen execution scope
- Any item in this section must be separately documented or version-frozen before implementation, and only after the first batch `WP1` to `WP6` is completed

## X. Historical Launch Milestones (Completed)

### M1: Contract Established

Completion criteria:

- Facade type definitions completed
- Documentation and code naming consistent

### M2: Prototype Invokable

Completion criteria:

- Python side can instantiate facade
- Can perform one reset/step main invocation

### M3: Frontend Begins Traffic Migration

Completion criteria:

- At least one mainline path of `WorldBatchVecEnv` integrated with facade

### M4: Regression and Baseline Pass

Completion criteria:

- Existing core tests pass
- Benchmark shows no significant regression

## XI. Final Suggestion

This round of launch should not aim to "look like a major refactoring", but should aim to:

1. Freeze the dependency boundary of the frontend under maintenance first.
2. Insert the facade prototype into the mainline with minimal cost.
3. Establish a stable entry point for subsequent C++ ownership sinking, CUDA resident-state, and device-view observation path.

Thus, the most recommended execution approach is:

- First complete `WP1 + WP2 + WP3`
- Then switch `WorldBatchVecEnv.reset()`
- Then switch `step_wait()`
- Finally close with tests and benchmarks

This minimizes launch cost while best aligning with the current repository's evolution pace.
