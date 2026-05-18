# Further Investigation into Architecture and Performance Roadmap

Document Navigation:

- [README.md](../README.md)
- [system_layering_and_engine_encapsulation_plan.zh.md](system_layering_and_engine_encapsulation_plan.zh.md)
- [runtime_facade_contract_plan.zh.md](../runtime_facade/runtime_facade_contract_plan.zh.md)
- [runtime_facade_task_bootstrap_plan.zh.md](../runtime_facade/runtime_facade_task_bootstrap_plan.zh.md)

Status: `2026-05-10` Investigation report draft.  
Document positioning:

- This document answers "why such layering, where are the performance bottlenecks, and how should subsequent roadmaps be prioritized".
- This document provides arguments and trade-off recommendations, but is not a frozen execution plan.
- Recommendations produced by this document should be distilled into contract plans, special initiatives, or new frozen task tickets.

This document is a further in-depth version of [system_layering_and_engine_encapsulation_plan.zh.md](system_layering_and_engine_encapsulation_plan.zh.md), focusing on the following questions:

1. Whether the current architecture's actual boundaries are consistent with the documentation description.
2. How the layered design should balance future extensibility, performance, and backend replacement.
3. Which slow paths should be migrated to C++ first, which are worth continuing to invest in CUDA, and whether Rust is suitable for introduction now.
4. How the next phase plan should be prioritized based on existing code and experimental results.

## Summary of Conclusions

Based on current code, tests, performance documents, and experimental clues, four clear conclusions can be given first:

1. The main structural problem of the current project is not "lack of acceleration means", but "architectural boundaries and hot path ownership are still unstable".
2. The safest and most rewarding main line for the next phase remains: continue sinking Python hot paths into C++, and on this basis push forward a more stable runtime facade and simulation/physics layering.
3. The CUDA path is no longer in a proof-of-concept stage, but an existing direction with real assets, real benchmarks, and real bottleneck conclusions. It should be incorporated into the main plan, rather than set aside as a possible future side branch.
4. Rust should not be introduced as a first priority currently. Not because Rust is infeasible, but because the repository has no existing Rust assets, and the current bottlenecks are more about runtime boundaries, data ownership, and GPU residency, rather than "C++ cannot express".

One-sentence summary:

`First stabilize the architectural boundary and the C++ main line, then advance CUDA; Rust is temporarily kept as an observation item and not entered into the near-term main implementation line.`

## 1. Current Architecture Status Investigation

### 1. Code Size and Responsibility Distribution Shows Python Still Too Heavy

Core file sizes are as follows:

- [gym_envs/scenario_loader.py](../../../gym_envs/scenario_loader/core.py): `5009` lines
- [python/rl/world_batch_vec_env.py](../../../python/rl/runtime/world_batch_vec_env.py): `1660` lines
- [gym_envs/universal_env.py](../../../gym_envs/universal_env.py): `807` lines
- [src/interfaces/python/python_module.cpp](../../../src/interfaces/python/python_module.cpp): `2958` lines
- [src/core/engine/simulation_kernel.cpp](../../../src/core/engine/simulation_kernel.cpp): `1598` lines
- [src/core/engine/world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp): `892` lines
- [src/core/mission/execution_episode_controller.cpp](../../../src/core/mission/episode/execution_episode_controller.cpp): `1207` lines

This indicates:

- The Python side is not a thin adaptation layer, but still carries a lot of runtime logic.
- Although the C++ side is already strong, it has not yet established clear interfaces and stable target boundaries to turn these capabilities into a truly dependable "backend platform".

### 2. Current Documentation and Code Are Basically Consistent in Understanding the "Execution Layer"

Although the old architecture documents are marked as archived, their judgment of real code hotspots is still basically accurate:

- [docs/Archive/architecture/layers/execution_layer.md](../../Archive/architecture/layers/execution_layer.md)
- [docs/Archive/architecture/layers/operation_physics_layer.md](../../Archive/architecture/layers/operation_physics_layer.md)

The structural risks they point out still hold today:

- `ScenarioLoader` is too heavy
- `MissionCommand` interpretation logic is scattered across Python/C++
- operation / physics / runtime / frontend are mixed

### 3. The "Nominal Boundaries" of Current Layering Already Exist, but "Execution Boundaries" Have Not Yet Truly Formed

The current directory already has a layered prototype:

- `src/core/engine`: world and kernel
- `src/core/mission`: mission/runtime
- `src/components/physics` and `src/systems/physics`: physics/control components
- `src/models/*`: default model implementations
- `src/interfaces/python`: Python binding
- `python/rl` and `gym_envs`: training and environment wrappers

But actual execution boundaries are still not stable enough, for reasons including:

- Python frontend still directly depends on many low-level runtime details.
- `python_module.cpp` exposes a collection of low-level capabilities, not a high-level runtime facade.
- `ef_core` is still a large monolith; target boundaries do not help constrain includes and ownership.

## 2. Performance and Bottleneck Investigation

### 1. Most Stable Performance Conclusion Today: Python Hot Path Remains a Primary Bottleneck

[cpp_exact_runtime_refactor_plan.md](../exact_runtime/cpp_exact_runtime_refactor_plan.md)
has already clearly pointed out:

- `ScenarioLoader` still holds a lot of episode state
- `compute_full_step(...)` still undertakes high-frequency orchestration
- `WorldBatchVecEnv` still relies on Python-side loader ownership to complete step semantics

This is not a "perceived slowness" but a structural bottleneck confirmed by the current main plan.

### 2. Compilation Batch Helpers Can Bring Benefits, but Benefits Are Limited

From measurements already in
[gpu_execution_runtime_research_and_design.md](../archive/gpu_execution_runtime_research_and_design.md),
C++ batch helpers do bring benefits to the current CPU main line, but the benefits are not decisive:

- `64 envs`
  - reset total: `164.33 ms -> 127.46 ms`
  - step total: `15.24 ms -> 14.72 ms`
  - about `1.04x` step wall-clock improvement
- `256 envs`
  - step total: `74.20 ms -> 67.27 ms`
  - about `1.10x` step wall-clock improvement

This shows:

- Simply compiling local observation packing / step preparation yields real but insufficient gains to cure architectural bottlenecks.
- The bigger bottleneck today lies in cross-layer ownership and data flow, not just the language implementation of individual helper operators.

### 3. Rollout Hot Path Bottleneck Has Been Further Identified

[gpu_execution_phase4_rollout_hot_path_freeze.md](../exact_runtime/gpu_execution_phase4_rollout_hot_path_freeze.md)
further confirms:

- Learner-side device-resident minibatch already has benefits
- `collect_rollouts()` is still not ideal
- The next constrained bottleneck in the current maintenance path is the host observation return contract

Even removing `deepcopy(self.buf_obs)`, the measured benefit is only:

- `1.7%` to `4.2%` when `n_envs=8`
- Close to noise when `n_envs=16`

This again shows:

- Simply changing Python container copy strategies is not the main battlefield.
- The truly high-value optimization is still deeper ownership sinking and stronger device-resident paths.

### 4. Exact GPU World-Step Is Still Not the Main Line Candidate

From content in
[gpu_exact_world_step_performance_and_parity_plan.md](../exact_runtime/gpu_exact_world_step_performance_and_parity_plan.md)
and
[gpu_exact_world_step_rearchitecture_plan.md](../archive/gpu_exact_world_step_rearchitecture_plan.md):

- The current exact GPU prototype is still significantly slower than CPU at small world_count
- Semantic drift still exists
- Although the warm-start path is significantly shortened, the current runtime boundary still makes it difficult to become a maintained default

Therefore:

- Exact GPU world-step should still be considered a medium-to-long-term direction
- Its prerequisite remains more stable compiled episode ownership and backend contract

## 3. Current Status Assessment of CUDA Path

### 1. CUDA Is Not a Future Idea, but Already Has Real Assets

The current repository already contains GPU helper code:

- [src/gpu/gpu_execution_observation_runtime.cpp](../../../src/gpu/gpu_execution_observation_runtime.cpp)
- [src/gpu/gpu_flight_shaping_runtime.cpp](../../../src/gpu/gpu_flight_shaping_runtime.cpp)
- [src/gpu/gpu_interaction_broadphase_runtime.cpp](../../../src/gpu/gpu_interaction_broadphase_runtime.cpp)
- [src/gpu/gpu_visual_runtime.cpp](../../../src/gpu/gpu_visual_runtime.cpp)
- Corresponding `.cu` implementations

Also probe tools:

- [src/tools/experimental/gpu_phase0](../../../src/tools/experimental/gpu_phase0)

And the build scaffold already exists:

- [CMakeLists.txt](../../../CMakeLists.txt)

### 2. CUDA Helper Value Has Been Proven by Benchmarks

According to measurements in
[gpu_execution_runtime_research_and_design.md](../archive/gpu_execution_runtime_research_and_design.md):

- object-only visual on device-resident path can achieve `16x` to `100x+` improvement relative to CPU
- terrain-aware visual can achieve `2.8x` host-readback improvement, `15x+` to `50x+` device-resident improvement
- sensor / comm / broadphase directions also show clear GPU potential

But the document also clearly points out:

- host readback is the main wall
- Only when device-resident consumers are connected, GPU helpers really enter a "different throughput level"

This means the real assessment of the current CUDA path should be:

- Worth continuing
- But must be linked with runtime facade, device-resident output, episode ownership refactoring
- Can no longer be pushed in isolation with a "single operator acceleration" mindset

### 3. Most Mature CUDA Application Directions

Combining existing assets and measurement results, the most mature and worthwhile CUDA directions to continue are, in order:

1. visual path
2. observation / bridge path
3. flight shaping path
4. broadphase candidate path
5. resident-state runtime path

Rather than immediately forcing:

1. exact full world-step replacement
2. migrating all physics stages in one go

## 4. Value Assessment of Continued C++ Sinking

### 1. Which Python Slow Paths Most Deserve to Be Migrated to C++

The Python code most worth migrating to C++ now is not all Python code, but these "high-frequency, structural, verifiable" paths:

1. Episode state ownership, mirror, route/approach/post-transition state transitions in `ScenarioLoader`
2. Main orchestration path for reward / termination / mission observation
3. Request build and state consume logic related to execution episode mainline / shadow compare in `WorldBatchVecEnv`
4. More stable facade-level batch request / batch response contract

Common characteristics of these paths:

- Execute every step
- Complex logic
- Currently cross Python/C++ boundary frequently
- Can be verified by existing tests and shadow compare

### 2. Which Parts Are Not Worth Rushing to "C++ for the Sake of C++"

The following should not be rewritten just because "Python is slow":

- Training script layer configuration and orchestration
- Experiment management and benchmark harness
- Various low-frequency tool scripts
- Peripheral logic used only in reset / diagnostics

The principle is:

- Sink hot paths first
- Stabilize contracts first
- Do not sacrifice iteration speed for language uniformity

## 5. Rust Path Assessment

### 1. Current Repository Has No Rust Assets

This investigation did not find:

- `Cargo.toml`
- `*.rs`
- Rust toolchain configuration

This means Rust is not a case of "existing semi-finished product, naturally promoted", but a situation of "introducing a new language and new toolchain from scratch".

### 2. Potential Advantages of Rust Today

From a long-term perspective, Rust might be suitable for these directions:

- Service-oriented runtime facade
- High-reliability DTO/serialization layer
- Standalone batch service or external orchestrator
- Clearer FFI boundary between Python / C++

### 3. Why Rust Is Not Suitable as a Near-Term Mainline

Currently, Rust should not be included in the near-term to-do mainline, not because of language issues, but timing issues:

1. Almost all existing high-performance assets are in C++/CUDA.
2. The biggest bottleneck today is not "C++ can't write it", but runtime ownership and host/device data flow.
3. Introducing Rust would increase:
   - New toolchain
   - New FFI boundary
   - New build complexity
   - New debugging chain
4. Before exact GPU, runtime facade, and batch runtime are stabilized, introducing a third system language would amplify complexity.

### 4. Suggested Positioning for Rust

Rust is currently suggested as:

- `Observation item`
- `Medium-to-long-term candidate`
- `Alternative implementation language for service-oriented and external runtime API`

Rather than:

- The main refactoring language for the current execution layer
- The first replacement language for the current physics / simulation backend

## 6. Layered Design Recommendations from a Future Extensibility Perspective

### 1. Layering Must Consider Both "Extensibility" and "Performance"

Conceptual layering alone is not enough; the next version of the layering design must simultaneously support:

- Replacing physics backends
- Replacing simulation backends
- Supporting multiple frontends
- Gradually introducing device-resident pipelines
- Supporting finer-grained batch and service-oriented architectures

Therefore, layering should not just be "directory reorganization", but should be oriented toward the following future capabilities:

1. exact CPU backend
2. exact GPU backend
3. reduced-fidelity backend
4. future external FDM bridge
5. local Python frontend
6. future remote/runtime service frontend

### 2. Most Critical New Layering Requirement

On top of the existing
[system_layering_and_engine_encapsulation_plan.zh.md](system_layering_and_engine_encapsulation_plan.zh.md),
it is recommended to add three performance-oriented requirements:

#### A. Facade layer must natively support batch and zero-copy

If the facade only abstracts "functionality" but not "data ownership" and "batch protocol", it will get stuck on host copies again in the future.

Therefore, the facade contract design should consider from the start:

- batch request / response
- typed packet
- optional device view / DLPack export
- sync / async compatibility space

#### B. Physics backend contract must allow resident state

If the physics backend still defaults to assuming that the CPU side is the authoritative state source every step, the future exact GPU path will remain obstructed.

Therefore, the physics backend contract should clearly support:

- host-owned state
- backend-owned resident state
- partial sync
- observation-only sync

#### C. Simulation engine contract must allow "compiled ownership, frontend mirroring"

That is:

- Authoritative state resides in the backend
- Frontend only mirrors
- Mirror can be partial or delayed

This is the foundation for truly removing Python from the hot path in the future.

## 7. Next Phase Plan Prioritization Suggestions

### First Priority: Stabilize Architectural Boundaries and C++ Ownership

This is the prerequisite for all subsequent performance paths.

Priority items to push:

1. Continue sinking execution episode ownership to C++
2. Split `ScenarioLoader` into state adapter / frontend helper / scenario adapter
3. Initial version of runtime facade contract
4. Directional CMake target splitting plan

### Second Priority: Integrate Existing CUDA Helper Line into Main Plan

This step is not about re-researching, but incorporating existing achievements into a unified architecture.

Priority items to push:

1. Facade-level integration points for visual / observation / flight shaping / broadphase
2. Unified contract for resident-state and device-resident output
3. Clear rules for switching between maintained path and experimental path

### Third Priority: Continue Selective Sinking of Python Hot Paths

After the main boundary is stabilized, continue migrating high-frequency hot paths to C++:

1. Main orchestration for reward / termination
2. Route / approach / post-transition logic
3. Mainline step request build / consume

### Fourth Priority: Assess New Entry Conditions for Exact GPU Backend

Only when these prerequisites are met should the exact GPU backend re-enter the mainline candidate:

1. Compiled episode ownership is stable
2. Frontend no longer holds authoritative state
3. Resident-state contract is stable
4. Host/device sync strategy is unified

### Fifth Priority: Rust as Medium-to-Long-Term Candidate Investigation

Currently not entering the main implementation line, but can be reserved as a follow-up topic:

- Whether it is worth implementing a service-oriented facade in Rust
- Whether DTO/serialization service has Rust advantages
- Whether there is a cleaner cross-language runtime service architecture than nanobind/C++

## 8. Suggested Follow-Up Document Topics

Note: The following content is used to illustrate suggested supplementary document topics and subsequent plan entry points, and does not constitute an automatically launched task list.

Based on this investigation, it is suggested to add or refine the following items next:

1. `runtime_facade_contract_plan`
   Describe facade batch contract, DTO, device-view contract.
2. `execution_state_adapter_split_plan`
   Describe how to split `ScenarioLoader`.
3. `cxx_hot_path_migration_matrix`
   Enumerate priority migration paths from Python -> C++.
4. `cuda_mainline_alignment_plan`
   Align existing visual/observation/flight-shaping/broadphase/resident-state lines to a unified runtime architecture.
5. `rust_evaluation_note`
   Record Rust's applicable boundaries and entry conditions separately, rather than mixing it into the current main plan.

## 9. Final Recommendations

For "future extensibility + performance optimization + careful layered design", the most reasonable overall path now is:

1. Continue to use C++ as the core backend refactoring language.
2. Treat CUDA as an existing, continuously advanceable backend capability, rather than a future consideration.
3. Reserve interfaces for future extensibility in advance at three levels: facade, ownership, and resident-state.
4. Rust temporarily does not enter the near-term main implementation line; only retain it as a medium-to-long-term service-oriented candidate.

In other words, the next step plan should not be:

- "First try if Rust will be faster"
- "First move all slow code to GPU"

But rather:

- "First stabilize backend ownership and runtime contract"
- "Then continue sinking the most valuable hot paths into C++"
- "Advance the CUDA device-resident main line based on existing assets"

This is most consistent with the real evolutionary direction of the current repository, and most likely to leave room for future expansion and performance growth without sacrificing maintainability.
