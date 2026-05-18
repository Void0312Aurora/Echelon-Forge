# `src/` Layered Refactoring Freeze Plan

Status: `2026-05-11` Freeze execution version; `WP1` to `WP7` completed.
Document positioning:

- This document freezes a significant but phased restructuring of the `src/` structure.
- The goal of this round is to first establish directory boundaries, responsibility documentation, and low-risk splitting paths, rather than immediately rewriting runtime semantics.
- If this document is adopted as an execution order, code implementation is only permitted to expand on the work packages listed herein.
- This document does not authorize the direct movement of behavioral code; except for READMEs and compatibility entry points, code splitting must be executed and validated sequentially according to subsequent work packages.

Validation criteria: When this plan involves Python tests, they should be executed by default using the repository's virtual environment, i.e., `./.venv/bin/python -m pytest`, with `PYTHONPATH=build-workshop` pointing to the current C++/nanobind build artifacts. Do not use the system Python interpreter as the final validation standard.

## 1. Current Assessment

`src/` is not a completely out-of-control monolith, but several boundary hotspots have already emerged that will continue to absorb complexity:

1. `src/components/physics/action.h` mixes pilot action, mission command, task order, leader intent, pilot report, legacy movement/action command, and command link.
2. `src/core/engine/simulation_kernel.cpp` simultaneously handles ECS system registration, spawn API, command API, weapon launch, agent observation, visual observation, and exact-stage inventory.
3. `src/interfaces/python/python_module.cpp` simultaneously handles core type bindings, runtime/facade bindings, GPU helper bindings, DLPack views, and diagnostic interfaces.
4. `src/core/mission/episode/execution_episode_controller.cpp` has already extracted detail helpers; the subsequent risk is whether the directory boundaries among mission runtime, episode controller, and controller details remain clear.
5. `src/components/systems` and `src/systems/systems` are overly broad in naming and lack clear business domain boundaries.
6. `src/gpu` simultaneously hosts maintained GPU helpers and experimental probe history; although the exact-step old line has been removed, directory responsibilities still need clarification.

The common risk of these issues is that future development will continue to cram new functionality into the "most convenient" large files or broad directories, causing the architecture documentation to diverge from the code reality again.

## 2. Target Layering

Target dependency direction:

```text
bindings/python
  -> runtime/facade
    -> core/batch
      -> core/sim
        -> systems
          -> models / components / content

accelerators/gpu
  -> core/mission or systems data packets
  -> no ownership of simulation truth state
```

Target directory semantics:

- `components/`
  - ECS data-only components and stable DTO-like structs.
  - Do not place system logic, runtime controllers, or Python binding helpers.
- `systems/`
  - Flecs system registration and per-frame mutation logic.
  - Only consume components / models / core interfaces.
- `models/`
  - Replaceable model implementations, such as control, sensor, environment, effects, guidance.
- `core/`
  - C++ runtime orchestration, simulation kernel, batch runtime, mission/episode pure runtime.
- `runtime/facade/`
  - Typed request/result boundaries depended upon by maintained frontends.
- `interfaces/python` or future `bindings/python`
  - Python exposure layer, only for bindings and lightweight conversions, does not own domain logic.
- `gpu` or future `accelerators/gpu`
  - Acceleration helpers and experimental probes, do not own canonical world-step semantics.

## 3. Non-Goals

This round will not do:

- Rewrite physics models or change `SimulationKernel::step()` semantics.
- Change the default runtime backend for training configurations.
- Delete the legacy command surface.
- Forcefully move all directories to the final target structure.
- Split the `ef_core` CMake target in one go.
- Delete low-level Python bindings.
- Introduce a new GPU exact-step mainline.

This round allows adding new compatibility umbrella headers and READMEs; behavior-preserving include splits, file splits, and binding segmentation are allowed.

## 4. Frozen Work Packages

### WP1: Establish `src/` Level README Guardrails

Goal:

- Add READMEs to the `src/` top-level and existing major directories.
- Clearly specify what each layer is allowed to contain, what it must not contain, dependency direction, and migration notes.

Main files:

- `src/README.md`
- `src/components/README.md`
- `src/systems/README.md`
- `src/core/README.md`
- `src/runtime/README.md`
- `src/interfaces/README.md`
- `src/gpu/README.md`
- `src/models/README.md`
- `src/content/README.md`

Validation:

- README covers existing major layers.
- README explicitly forbids continuing to stuff new tasking/command types into `components/physics`.
- README explicitly states that the Python binding layer must not carry domain logic.

Execution status:

- Completed: READMEs added to all existing directories under `src/`.
- Completed: READMEs added for new target directories `components/command` and `components/tasking`.
- Not started: Behavioral code movement, include migration, and CMake target splitting.

### WP2: Split Target Boundaries of `components/physics/action.h`

Goal:

- Establish command/tasking target directories and READMEs.
- When subsequently splitting `action.h` into `command` and `tasking` headers, there is a clear landing point.

Target structure:

```text
src/components/command/
  README.md
  pilot_action.h
  mission_command.h
  command_link.h
  legacy_command.h

src/components/tasking/
  README.md
  tasking_enums.h
  task_order.h
  leader_intent.h
  pilot_report.h
```

Code splitting suggestions for this round:

1. First add new target headers and let the old `components/physics/action.h` serve as an umbrella include.
2. Then gradually update C++ includes to the new paths.
3. Finally mark `action.h` as a compatibility header.

Validation:

- New directory README clearly describes command/tasking boundaries.
- Any future new command/tasking component has a new directory to belong to.
- The old include compatibility period does not break existing Python bindings or C++ compilation.

Execution status:

- Completed: Added `components/command/{pilot_action.h, mission_command.h, legacy_command.h, command_link.h}`.
- Completed: Added `components/tasking/{tasking_enums.h, task_order.h, leader_intent.h, pilot_report.h}`.
- Completed: `components/physics/action.h` downgraded to compatibility umbrella include.
- Completed: `components/systems/comm.h` no longer owns `CommMsgType` / `PilotReport` definitions; they are now provided by `components/tasking/pilot_report.h`.
- Completed: Main code under `src` no longer directly includes `components/physics/action.h`.
- Verified: `cmake --build build-workshop --target ef_core ef_py -j2` passes.

### WP3: Split Binding Partitions of `python_module.cpp`

Goal:

- Split the Python bindings from a single 3000+ line file into several binding units.
- Only split the binding structure; do not change exposed API names.

Target structure:

```text
src/interfaces/python/
  python_module.cpp
  bindings_core.cpp
  bindings_command.cpp
  bindings_episode.cpp
  bindings_runtime.cpp
  bindings_gpu.cpp
  binding_utils.h
```

Validation:

- `python_module.cpp` only responsible for the `NB_MODULE` aggregation call.
- Command/tasking type bindings concentrated in `bindings_command.cpp`.
- GPU helper / DLPack bindings concentrated in `bindings_gpu.cpp`.
- Existing Python runtime/facade tests pass.

Execution status:

- Completed: Added `binding_utils.h` and partition files `bindings_{command,core,episode,runtime,gpu}.cpp`.
- Completed: `python_module.cpp` reduced to the `NB_MODULE` aggregation entry, registering in order `command -> core -> episode -> runtime -> gpu`.
- Completed: `CMakeLists.txt` integrates all binding units into `ef_py`.
- Completed: `src/interfaces/python/README.md` updated to describe current partition responsibilities.
- Verified: `cmake --build build-workshop --target ef_py -j2` passes.
- Verified: Smoke check with `PYTHONPATH=build-workshop ./.venv/bin/python` shows `RuntimeFacade`, `WorldBatchRuntime`, `SimulationKernel`, command/tasking types, and GPU helper symbols are all visible.
- Verified: `PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/test_gpu_runtime_bindings.py` passes — `26 passed`.

### WP4: Split `SimulationKernel` Boundary Files

Goal:

- Keep `SimulationKernel` as the single world orchestration API, but split its implementation into responsibility files.

Target structure:

```text
src/core/engine/
  simulation_kernel.cpp              # constructor, reset, step, model injection
  simulation_kernel_systems.cpp      # ECS component/system registration
  simulation_kernel_command_api.cpp
  simulation_kernel_observation_api.cpp
  simulation_kernel_visual_api.cpp
  simulation_kernel_weapon_api.cpp
  exact_stage_inventory.cpp
```

Validation:

- `simulation_kernel.cpp` no longer bears observation/visual/weapon details.
- Exact-stage inventory is moved out of the kernel's main implementation.
- `SimulationKernel` public API unchanged.

Execution status:

- Completed: `simulation_kernel.cpp` shrunk to constructor/destructor, model injection, reset/step, spawn, database/environment configuration.
- Completed: Added `simulation_kernel_systems.cpp` to host ECS component registration and system registration order.
- Completed: Added `simulation_kernel_command_api.cpp` to host legacy commands, command links, digital pilot/tasking, and message commands.
- Completed: Added `simulation_kernel_observation_api.cpp`, `simulation_kernel_visual_api.cpp`, `simulation_kernel_weapon_api.cpp`.
- Completed: Added `exact_stage_inventory.cpp`; exact-stage inventory and trace helpers moved out of the main implementation file.
- Completed: `CMakeLists.txt` integrates WP4 new engine implementation units into `ef_core`.
- Completed: `src/core/engine/README.md` updated to reflect current responsibility boundaries.
- Verified: `cmake --build build-workshop --target ef_core ef_py -j2` passes.
- Verified: `PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/test_gpu_runtime_bindings.py tests/runtime/test_execution_episode_batch_prepare.py tests/runtime/test_execution_episode_controller.py tests/runtime/test_execution_episode_state.py` passes — `38 passed`.

### WP5: Split `ExecutionEpisodeController` — Mission Transition and Breakdown

Goal:

- Split the controller from a "state machine + JSON parser + transition planner + reward breakdown" into testable helpers.

Target structure:

```text
src/core/mission/
  runtime/
  episode/
    execution_episode_controller.cpp
    detail/
      episode_transition_runtime.cpp
      episode_reward_breakdown.cpp
      mission_command_codec.cpp
```

Validation:

- JSON mission command round-trip logic concentrated in codec.
- Post-waypoint / landing transition logic concentrated in transition runtime.
- Reward breakdown summary concentrated in breakdown helper.
- Controller only coordinates state import/export, prepare/evaluate/step.

Execution status:

- Completed: Added `mission_command_codec.{h,cpp}` to centralize mission-command JSON round-trip, route waypoint materialization, and mission target update.
- Completed: Added `episode_transition_runtime.{h,cpp}` to centralize route guidance target update, post-waypoint transition, and landing transition arm/vector update.
- Completed: Added `episode_reward_breakdown.{h,cpp}` to centralize reward breakdown summary and stable JSON output.
- Completed: `execution_episode_controller.cpp` shrunk to coordination of state import/export, prepare/evaluate/step, and runtime products apply.
- Completed: `src/core/mission` physically split into `runtime/`, `episode/`, and `episode/detail/`; the root directory no longer carries flat `.h/.cpp` files.
- Verified: `cmake --build build-workshop --target ef_core ef_py -j2` passes.
- Verified: `PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/test_execution_episode_controller.py tests/runtime/test_execution_episode_state.py tests/runtime/test_execution_episode_batch_prepare.py tests/runtime/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/runtime/test_scenario_loader_execution_step_runtime.py tests/test_gpu_runtime_bindings.py` passes — `45 passed`.
- Verified: `PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/test_execution_episode_controller.py tests/runtime/test_execution_episode_state.py tests/runtime/test_execution_episode_batch_prepare.py tests/runtime/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/runtime/test_scenario_loader_execution_step_runtime.py tests/test_gpu_runtime_bindings.py tests/test_cuda_import_order.py tests/world_batch/test_world_batch_vec_env.py` passes — `71 passed, 8 subtests passed`.

### WP6: Tighten the Facade Escape Hatch

Goal:

- Continue to enforce the facade-first principle.
- `RuntimeFacade::runtime()` is kept for compatibility, but must not become a dependency for new mainline code.

Validation:

- README and architecture tests mark `runtime()` as only allowed for diagnostics / compatibility.
- When adding new mainline capability, a facade request/result must be designed first.

Execution status:

- Completed: `RuntimeFacade::runtime()` retained as a compatibility / diagnostics escape hatch.
- Completed: The maintained main path of `WorldBatchVecEnv` accesses facade-shaped APIs via `_RuntimeFacadeAdapter`; direct `RuntimeFacade.runtime()` calls are only allowed within that adapter.
- Completed: The main `WorldBatchVecEnv` class no longer caches raw handles to `_batch_runtime` / `_runtime_facade`; ScenarioLoader low-level world access, legacy visual readback, and visual batch helper all go through adapter methods.
- Completed: Architecture tests prohibit maintained main classes or new code, outside the adapter, from directly calling `RuntimeFacade.runtime()`, directly instantiating `ef_py.WorldBatchRuntime`, caching raw runtime/facade handles, or re-exposing `.compat_runtime`.
- Verified: `PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/architecture/test_runtime_facade_layering.py` passes — `5 passed`.
- Verified: `PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/architecture/test_runtime_facade_layering.py tests/world_batch/test_world_batch_vec_env.py tests/runtime/test_runtime_facade.py tests/test_cuda_import_order.py` passes — `36 passed`.

### WP7: CMake Target Split Preparation

Goal:

- Do not force split targets yet, but make directory and file boundaries support future splits.

Candidate target order:

1. `ef_components`
2. `ef_models`
3. `ef_systems`
4. `ef_mission_runtime`
5. `ef_sim_core`
6. `ef_runtime_facade`
7. `ef_python_bindings`
8. `ef_gpu_helpers`

Validation:

- New READMEs clearly define target boundaries.
- New file ownership does not cross-layer reverse dependencies.
- CMake no longer adds unbounded "mixed bag" source files.

Execution status:

- Completed: Added `src/runtime/contracts/` as a candidate starting point for the subsequent `ef_contracts` target.
- Completed: Extracted `WorldEntityRef`, world setup assignments, command/tasking assignments, and `WorldExecutionEpisodeStepRequest` from `world_batch_runtime.h` into `runtime/contracts/world_batch_contracts.h`.
- Completed: `runtime_facade_types.h` no longer directly includes `core/engine/world_batch_runtime.h`.
- Completed: `RuntimeFacade` public header uses forward declaration of `WorldBatchRuntime` and `std::unique_ptr`; the full definition of the underlying engine owner is only included in `.cpp`.
- Completed: Added architecture check that prohibits `runtime/contracts/*.h` and `runtime/facade/*_types.h` from including `core/engine/*`, and confirmed that the facade public header does not directly include `world_batch_runtime.h`.
- Completed: `CMakeLists.txt` has been split by future target boundaries into `EF_CORE_ENGINE_SOURCES`, `EF_CORE_MISSION_RUNTIME_SOURCES`, `EF_CORE_MISSION_EPISODE_SOURCES`, `EF_CORE_MISSION_EPISODE_DETAIL_SOURCES`, `EF_CORE_MISSION_SOURCES`, `EF_RUNTIME_FACADE_SOURCES`, `EF_MODEL_DEFAULT_SOURCES`, `EF_CONTENT_SOURCES`, `EF_PYTHON_BINDING_SOURCES`, and GPU source groups; the `ef_core` / `ef_py` targets no longer list source files flatly.
- Completed: Added CMake target readiness architecture check to prevent `ef_core` / `ef_py` from reverting to boundless source file flattening.
- Completed: Updated `src/README.md` with rules for CMake source group ownership.
- Verified: `cmake --build build-workshop --target ef_core ef_py -j2` passes.
- Verified: `PYTHONPATH=build-workshop ./.venv/bin/python -m pytest -q tests/architecture/test_runtime_facade_layering.py tests/architecture/test_cmake_target_readiness.py tests/world_batch/test_world_batch_vec_env.py tests/runtime/test_runtime_facade.py tests/world_batch/test_world_batch_runtime.py tests/test_cuda_import_order.py tests/test_gpu_runtime_bindings.py` passes with `62 passed`.

## 5. Execution Order

Recommended order:

1. `WP1 + WP2`: First, establish directory documentation and command/tasking target boundaries.
2. `WP3`: Split Python binding files to reduce the cost of future type moves.
3. `WP4`: Split `SimulationKernel` implementation files.
4. `WP5`: Split episode controller internal business helpers.
5. `WP6`: Add architecture tests and restrict facade escape hatches.
6. `WP7`: Decide on CMake target splitting based on the results of the previous splits.

## 6. Freeze Rules

- Any cross-layer movement must maintain public API compatibility unless a separate freeze document is created.
- All compatible umbrella headers must be annotated with the migration target.
- New directories must include a README.
- New core types must first determine their layer; they are not allowed to be placed in old broad directories for include convenience.
- New Python bindings are not allowed to inline domain logic; they must first form an API in the C++ runtime/facade.
- New GPU helpers are not allowed to change the canonical CPU truth path unless a separate exact backend freeze document is created.

## 7. Open Questions

This plan closes at `WP7`. The following issues are reserved as candidates for the next freeze plan and will not be implemented further in this plan:

- Should `src/interfaces/python` be renamed to `src/bindings/python`?
- Should `components/systems` and `systems/systems` be renamed to `components/comm`, `systems/comm` or `components/platform`, `systems/platform`?
- Should `core/engine` be renamed to `core/sim` in the next round to avoid confusion with facade/runtime engine concepts?
- Should `gpu` be renamed to `accelerators/gpu` in the next round to make the boundary between "GPU helper" and "core runtime truth" clearer?
