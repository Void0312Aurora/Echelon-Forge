<!-- Machine-translated draft generated on 2026-05-18 from docs/plan/runtime_facade/runtime_facade_layering_cleanup_freeze.zh.md. Review before treating this file as authoritative. -->

# Runtime Facade Layering Cleanup and Decoupling Freeze Execution Plan

Document Navigation:

- [README.md](../README.md)
- [system_layering_and_engine_encapsulation_plan.zh.md](../architecture/system_layering_and_engine_encapsulation_plan.zh.md)
- [architecture_and_performance_research_followup.zh.md](../architecture/architecture_and_performance_research_followup.zh.md)
- [runtime_facade_contract_plan.zh.md](runtime_facade_contract_plan.zh.md)
- [runtime_facade_task_bootstrap_plan.zh.md](runtime_facade_task_bootstrap_plan.zh.md)

Status: `2026-05-10` Next batch of candidate freeze execution plans.  
Document positioning:

- This document is used to carry over the next round of code cleanup after the first batch of `runtime facade` has been landed.
- The goal of this round is not to add new acceleration capabilities, but to tighten boundaries, reduce inter-layer leakage, and ensure that the maintained frontend depends only on the facade.
- If this document is adopted as a freeze execution order, code implementation in this round is only allowed to revolve around the `WP1-WP7` listed herein.

Current execution progress:

- [x] `WP1` Facade API stability classification has been annotated in `RuntimeFacade::runtime()` and the Python binding block.
- [x] `WP2` The facade/direct runtime branches of `WorldBatchVecEnv` have been converged into `_RuntimeFacadeAdapter`; the main class no longer caches raw runtime/facade handles.
- [x] `WP3` New facade-level `BatchWorldSetupRequest` / `BatchWorldSetupResult` have been added; `scenario_runtime` preferentially uses typed setup request.
- [x] `WP4` New `ObservationBatchRequest` has been added; `WorldBatchVecEnv` state readback preferentially goes through the facade observation packet.
- [x] `WP5` Python bindings have annotated maintained facade surface and simulation compatibility surface.
- [x] `WP6` New `tests/architecture/runtime_facade/test_layering.py` has been added as a dependency direction regression check.
- [x] `WP7` Target split readiness has recorded include blocking, split order, and the threshold for entering the next batch of target splits; CMake sources have been grouped according to future target source groups.

## I. Current Assessment

The first batch of facade bootstrap tasks has been completed:

- `src/runtime/facade/runtime_facade_types.h`
- `src/runtime/facade/runtime_facade.h`
- `src/runtime/facade/runtime_facade.cpp`
- `tests/runtime/facade/test_runtime_facade.py`
- The reset / step main paths of `WorldBatchVecEnv` have begun using facade-first.

However, from the current code, the facade is still more of a thin wrapper layer rather than a stable layered boundary:

1. `RuntimeFacade` still exposes `runtime()`, but it has been annotated as a compatibility / diagnostics escape hatch.
2. The facade and direct runtime fallback of `WorldBatchVecEnv` have been converged into `_RuntimeFacadeAdapter`; the main class no longer caches bare handles `_runtime_facade` / `_batch_runtime`.
3. The public interface of `RuntimeFacade` still largely forwards `WorldBatchRuntime::*_batch` methods one-to-one.
4. `runtime_facade_types.h` no longer directly includes `world_batch_runtime.h`; facade-facing world-batch DTOs have been extracted into `runtime/contracts/world_batch_contracts.h`.
5. `python_module.cpp` simultaneously exposes low-level probe/runtime APIs and maintained facade APIs, with no distinction in stability between the mainline frontend and diagnostics entry points.
6. `ef_core` is still a large monolithic target; build boundaries cannot yet constrain the dependency direction of contracts / facade / simulation / physics.

Therefore, the next step should not continue to expand GPU helpers, exact backend, or new training features; a round of layering cleanup should be done first.

## II. Goals for This Round

The goal of this round is to establish a verifiable dependency direction:

`WorldBatchVecEnv / UniversalEnv -> RuntimeFacade -> WorldBatchRuntime -> SimulationKernel`

And ensure that the maintained frontend no longer directly depends on:

- The mainline batch step / setup / readback methods of `WorldBatchRuntime`
- The low-level entity and component reading/writing of `SimulationKernel`
- Interfaces in `python_module.cpp` used only for probe / diagnostics

After this round is completed, the next round can more safely advance:

- Observation / reward / info contract deepening
- Device-view / DLPack facade exits
- Resident-state or exact backend toggle
- CMake target-level splits

## III. Non-Goals

This round will NOT do:

- Exact GPU backend mainline switch
- Resident-state mainline integration
- Full rewrite of `ScenarioLoader`
- Complete split of physics engine independent target
- Deletion of all low-level Python bindings
- Changing the default backend selection of the maintained `p5`

Low-level APIs can continue to exist, but must be marked as a diagnostics / compatibility surface, not a dependency surface for the maintained frontend.

## IV. Freeze Work Packages

### WP1: Define Facade API Stability Classification

Goal:

- Distinguish maintained facade API, compatibility API, and diagnostics API in documentation and code comments.
- Clarify that `RuntimeFacade::runtime()` can only be used as a temporary compatibility escape hatch, not as a dependency for the maintained frontend.

Main files:

- [runtime_facade.h](../../../src/runtime/facade/runtime_facade.h)
- [python_module.cpp](../../../src/interfaces/python/python_module.cpp)
- [runtime_facade_contract_plan.zh.md](runtime_facade_contract_plan.zh.md)

Acceptance:

- Documentation lists facade API stability.
- All escape hatches in code have clear naming or comments.

### WP2: Converge `WorldBatchVecEnv` Runtime Access Path

Goal:

- Ensure that the maintained main path of `WorldBatchVecEnv` accesses batch runtime capabilities only through `RuntimeFacade`.
- Converge the direct `WorldBatchRuntime` fallback into a single compatibility adaptation point, rather than scattered throughout step/reset/readback helper functions.

Main files:

- [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)

Suggested implementation:

- Add an internal `_RuntimeFacadeAdapter` or equivalent thin adaptation object.
- `WorldBatchVecEnv` internally only calls adapter methods.
- The adapter can temporarily handle facade / legacy runtime fallback internally.

Acceptance:

- The main body of `WorldBatchVecEnv` no longer has scattered checks for `_runtime_facade is not None`.
- The main body of `WorldBatchVecEnv` no longer directly calls `_batch_runtime.*_batch` mainline methods.
- Existing world-batch tests continue to pass.

### WP3: Complete Facade-level Setup / Reset Request

Goal:

- Frontend no longer directly calls `apply_world_setup_batch(...)` via multiple parallel arrays.
- Add facade-level typed request so that world setup becomes part of the facade contract.

Candidate types:

- `BatchWorldSetupRequest`
- `BatchWorldSetupResult`

Main files:

- [runtime_facade_types.h](../../../src/runtime/facade/runtime_facade_types.h)
- [runtime_facade.h](../../../src/runtime/facade/runtime_facade.h)
- [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp)
- [scenario_runtime.py](../../../python/scenario_runtime.py)
- [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)

Acceptance:

- `load_compiled_scenario_batch(...)` can use typed setup request on `RuntimeFacade`.
- Old parallel array entry remains as compatibility API, but maintained paths go through typed request.

### WP4: Converge Observation / State Readback Contract

Goal:

- Frontend uses facade-level `ObservationBatchPacket` or request/result to get readback, instead of calling multiple underlying getters separately.
- Reserve contract space for future device-view / partial-sync.

Candidate types:

- `ObservationBatchRequest`
- Extended `ObservationBatchPacket`

Main files:

- [runtime_facade_types.h](../../../src/runtime/facade/runtime_facade_types.h)
- [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp)
- [world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py)

Acceptance:

- `_read_truth_and_inst_by_refs(...)` uses facade packet.
- Execution controller mainline step result and observation packet combined path is covered by tests.
- No changes to existing observation numeric semantics.

### WP5: Isolate Mainline Bindings from Diagnostics Bindings

Goal:

- Keep low-level bindings in `python_module.cpp`, but clearly separate maintained facade bindings and diagnostics / probe bindings into sections.
- Prepare for future file or target splits.

Main files:

- [python_module.cpp](../../../src/interfaces/python/python_module.cpp)

Acceptance:

- Facade block, simulation compatibility block, and diagnostics block in the binding file are clearly separated.
- New or updated tests ensure that the maintained `WorldBatchVecEnv` does not depend on `ef_py.WorldBatchRuntime` as a main path capability probe object.

### WP6: Add Dependency Direction Regression Checks

Goal:

- Use lightweight tests to protect the layering cleanup results of this round.

Suggested checks:

- `python/rl/world_batch_vec_env.py` does not directly instantiate `ef_py.WorldBatchRuntime`, except in compatibility adaptation points.
- The maintained frontend does not call `RuntimeFacade.runtime()`.
- New DTOs in facade public headers do not continue to expand direct dependency on engine internal headers.

Main files:

- New `tests/architecture/runtime_facade/test_layering.py`
- Or merge into [tests/runtime/facade/test_runtime_facade.py](../../../tests/runtime/facade/test_runtime_facade.py)

Acceptance:

- Architecture checks can run in normal pytest.
- Check failure information points to specific violating files and symbols.

### WP7: Record Preconditions for Next Round Target Split

Goal:

- Do not force-split `ef_core` in this round, but record the minimal preconditions for the next round of CMake target split.

Candidate target order:

1. `ef_contracts`
2. `ef_mission_runtime`
3. `ef_simulation_engine`
4. `ef_runtime_facade`
5. `ef_models_default`

Acceptance:

- At the end of this round, a new target split readiness record is added.
- Record which include dependencies still prevent target split.

Current record:

- Currently `ef_core` still compiles engine, mission runtime, facade, content loader, and default model sources together.
- Added `src/runtime/contracts/` and extracted `WorldEntityRef`, world setup assignments, command/tasking assignments, and `WorldExecutionEpisodeStepRequest` from `world_batch_runtime.h` into `runtime/contracts/world_batch_contracts.h`.
- `runtime_facade_types.h` no longer directly includes `core/engine/world_batch_runtime.h`.
- `runtime_facade.h` hides the underlying engine owner via forward declaration and `std::unique_ptr<WorldBatchRuntime>`; the full `world_batch_runtime.h` include is only retained in `runtime_facade.cpp`.
- `world_batch_runtime.h` directly includes `simulation_kernel.h`, `execution_episode_controller.h`, observation, and physics action/instrument component headers.
- `simulation_kernel.h` directly includes component headers, `unit_data.h`, `observation.h`, and aggregates physics / systems / combat / visual systems and default unit factory in `.cpp`.
- `python_module.cpp` is still a wide binding layer, simultaneously including facade, simulation runtime, mission runtime, GPU helpers, models snapshot, and component headers.
- `CMakeLists.txt` has expressed future target boundaries using `EF_CORE_ENGINE_SOURCES`, `EF_CORE_MISSION_SOURCES`, `EF_RUNTIME_FACADE_SOURCES`, `EF_MODEL_DEFAULT_SOURCES`, `EF_CONTENT_SOURCES`, `EF_PYTHON_BINDING_SOURCES`, and GPU source groups.

Therefore, the next batch cannot directly extract `ef_runtime_facade` alone. The dependency of facade public headers on engine public headers must first be reduced.

Minimal split preconditions:

1. Done: Separated facade-facing DTOs from `WorldBatchRuntime` headers, covering:
   - `WorldEntityRef`
   - world setup assignments / spawn request
   - execution episode step request
2. Done: `runtime_facade_types.h` no longer directly includes `world_batch_runtime.h`.
3. Keep `WorldBatchRuntime`'s internal dependency `SimulationKernel` API within the simulation engine target; facade only wraps it via `.cpp`.
4. Pre-split `python_module.cpp` binding blocks at least by file or include group:
   - facade bindings
   - simulation compatibility bindings
   - mission runtime bindings
   - diagnostics / GPU helper bindings
5. Before target split, the existing passing test suite must be preserved to avoid mixing semantic changes during the split.
6. Done: Use architecture checks to constrain `ef_core` and `ef_py` to only consume grouped source variables, no longer directly listing source files.

Recommended target split order:

1. `ef_contracts`
   - Content: pure DTO / enum / small value types.
   - First batch candidates: facade DTO, mission runtime DTO, `WorldEntityRef`, and world setup request.
   - Should not link Flecs, nanobind, CUDA, or model implementations.
2. `ef_mission_runtime`
   - Content: runtime evaluation from `src/core/mission/*` that does not depend on `SimulationKernel`.
   - Feasibility is currently high, but must first confirm each mission header does not backward-include engine headers.
3. `ef_simulation_engine`
   - Content: `SimulationKernel`, `WorldBatchRuntime`, geometry runtime, systems orchestration.
   - Continue linking Flecs, model interfaces, and default model implementations.
4. `ef_runtime_facade`
   - Content: `RuntimeFacade`.
   - Depends on `ef_contracts` and `ef_simulation_engine`, but public headers only expose `ef_contracts`.
5. `ef_models_default`
   - Content: default control / sensor / environment / effects / guidance / unit factory.
   - Currently `SimulationKernel` still directly uses the default unit factory, so this step should come after simulation engine boundary cleanup.

Not recommended split approaches:

- Do not split `ef_runtime_facade` target first. Currently facade public headers still leak engine headers to callers.
- Do not split physics engine target first. Currently physics systems are directly registered and scheduled by `SimulationKernel`; interface boundaries are not yet formed.
- Do not advance exact GPU or resident-state simultaneously with target splits. That would conflate build boundary issues with backend semantics.

Minimal target preparation already in place for this round:

- Created `src/runtime/contracts/` directory.
- Moved facade-facing DTOs from `world_batch_runtime.h` into `runtime/contracts/world_batch_contracts.h`.
- Made `runtime_facade_types.h` no longer include `world_batch_runtime.h`.
- Added architecture check to prohibit `runtime/contracts/*.h` and `runtime/facade/*_types.h` from including `core/engine/*`.
- Added architecture check to prohibit `ef_core` / `ef_py` targets from directly listing source files again.
- Temporarily not changing CMake targets, only using include direction checks to verify contract extraction.

## V. Recommended Execution Order

1. `WP1`
2. `WP2`
3. `WP3`
4. `WP4`
5. `WP5`
6. `WP6`
7. `WP7`

Among these, `WP2-WP4` are the core of this round; `WP5-WP7` are used to prevent the cleanup results from drifting again.

## VI. Verification Set

Minimum regression set:

```bash
CMO_BUILD_DIR=build-facade-local \
LD_LIBRARY_PATH=/home/void0312/Workshop/CMO/build-facade-local/_deps/flecs-build:/home/void0312/Workshop/CMO/build-facade-local \
./.venv/bin/python -m pytest \
  tests/runtime/facade/test_runtime_facade.py \
  tests/runtime/execution/test_execution_episode_controller.py \
  tests/runtime/execution/test_execution_episode_state.py \
  tests/runtime/execution/test_execution_episode_batch_prepare.py \
  tests/world_batch/test_world_batch_runtime.py \
  tests/world_batch/test_world_batch_vec_env.py
```

If new architecture checks:

```bash
./.venv/bin/python -m pytest tests/architecture/runtime_facade/test_layering.py
```

## VII. Completion Criteria

This round must satisfy all of the following when completed:

1. The main path of `WorldBatchVecEnv` (maintained) depends only on facade or facade adapter.
2. `RuntimeFacade::runtime()` is no longer called by the maintained frontend main class; migration period is limited to explicit compatibility adapter.
3. World setup and observation readback each have at least one facade-level typed request/result entry.
4. Low-level `WorldBatchRuntime` Python bindings are still available for diagnostics, but are no longer the main dependency for the maintained frontend.
5. Regression tests pass, and a new dependency direction check is added.
6. The default execution / visual / observation backend of maintained `p5` has not changed.

## VIII. Next Steps

The current round `WP1-WP7` has been concluded. Subsequent tasks require a separate freeze plan and will not continue under this document.

After this round, the next batch of tasks will choose one of the following to freeze independently:

- Facade-level device observation view
- Host observation return contract deepening
- Resident-state / exact backend facade switch
- `ef_core` target split
- Further sinking of `ScenarioLoader` episode ownership

These future directions are outside the scope of this round's implementation.
