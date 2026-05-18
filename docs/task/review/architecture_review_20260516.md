<!-- Machine-translated draft generated on 2026-05-18 from docs/task/review/architecture_review_20260516.zh.md. Review before treating this file as authoritative. -->

# Project Structure and Architecture Design Review Report

Status: `2026-05-16` First full review completed; `2026-05-16` Annotations supplemented  
Scope: C++ kernel, ECS component system, runtime layering, Python training infrastructure, build system, documentation and tests  

Related follow-up plan:  

- [Architecture Review Follow-up Freeze Plan](architecture_review_followup_freeze_20260516.zh.md)  

## 1. Background  

This document is based on the first comprehensive review of the repository, covering design evaluations across `src/`, `python/`, `gym_envs/`, `tests/`, `tools/`, `docs/`, build configuration, etc. The goal is to identify strengths, risks, and areas for improvement in the current architecture, and to freeze a traceable list of issues.  

## 2. Review Scope  

- `src/` — C++ ECS kernel, layering boundaries, facade contract  
- `python/` — RL runtime, training entry, policy/tasking  
- `gym_envs/` — Gymnasium environment wrapper and scenario loader  
- `tests/` — Test coverage and architecture tests  
- `docs/` — Documentation system completeness  
- `CMakeLists.txt` — Build system and dependency management  
- `.gitignore` — Version control scope  

## 3. Architectural Strengths  

### 3.1 Clear, testable layering dependency direction  

Dependency direction:  

```text
interfaces/python → runtime/facade → core/engine + core/mission
    → systems → models / components / content
```

- [src/README.md](../../../src/README.md) and per-layer READMEs clearly define what is allowed and prohibited in each layer  
- [docs/plan/architecture/src_layered_refactor_freeze.zh.md](../../plan/architecture/src_layered_refactor_freeze.zh.md) freezes execution records of WP1-WP7  
- [tests/architecture/test_runtime_facade_layering.py](../../../tests/architecture/test_runtime_facade_layering.py) and [test_cmake_target_readiness.py](../../../tests/architecture/test_cmake_target_readiness.py) turn architectural constraints into automated checks  

Assessment: Making architectural constraints testable in a codebase is extremely rare, and this is the standout strength.  

### 3.2 Facade pattern rational  

[RuntimeFacade](../../../src/runtime/facade/runtime_facade.h) is the only external contract from the C++ layer, providing typed request/result interfaces:  
- `BatchWorldSetupRequest` / `BatchWorldSetupResult`  
- `ExecutionBatchStepRequest` / `ExecutionBatchStepResult`  
- `ObservationBatchRequest` / `ObservationBatchPacket`  

On the Python side, `_RuntimeFacadeAdapter` centralizes adaptation, and `WorldBatchRuntime` accesses it directly (architecture tests forbid spreading beyond the adapter).  

### 3.3 ECS (Flecs v4.0) selection fits the domain  

Air combat simulation involves many heterogeneous entities (aircraft, missiles, sensors, communication links). Flecs' system ordering + pipeline naturally match phased execution. `SimulationKernel`'s `exact_stage_inventory` makes pipeline stages explicit, providing a clear map for GPU migration.  

### 3.4 Semantic separation of Command/Tasking  

Previously mixed DTO in `components/physics/action.h` has been split into:  
- `components/command/` — low-level instructions (PilotAction, MissionCommand, CommandLink)  
- `components/tasking/` — high-level task semantics (TaskOrder, LeaderIntent, PilotReport)  
- Each subdomain further divided into `common/`, `air/`, `naval/`  

This corresponds exactly to the routing hierarchy `TaskOrder → LeaderIntent → MissionCommand → execution-layer control` described in the HMoE design document.  

### 3.5 Systematic documentation structure  

| Directory | Responsibility |
|-----------|----------------|
| `docs/manual/` | Current-main-line code map and capability list |
| `docs/plan/` | Architecture freeze plans and execution work packages |
| `docs/forward/` | Unscheduled forward-looking designs |
| `docs/standards/` | Coding and design standards |
| `docs/task/` | Short-lived task documentation |

[src_layer_map.md](../../manual/src_layer_map.md) provides a "problem → location guide"—directing you to the appropriate directory based on the type of issue.  

### 3.6 Experiment management and archival  

- `experiments/` follows `YYYYMMDD_purpose` naming convention  
- `examples/config/training/` split into `active/` and `frozen/`  
- `tools/archive/` specifically archives old diagnostic scripts  

---

## 4. Items for Improvement (Ordered by Priority)  

### 4.1 🔴 Missing CI/CD configuration  

**Location**: Repository root  

**Observation**: No `.github/workflows/` or any CI configuration file. The repository has 50+ test files, mixed C++ and Python builds, but lacks an automated validation pipeline.  

**Impact**:  
- No automated quality gate before PR merges  
- Multi-platform build compatibility (Linux only? CUDA variant?) not checked  
- Regression relies on manual effort  

**Suggestion**: Prioritize a minimal CI (build ef_core + ef_py → pytest core suite), then expand to matrix builds.  

**Annotation (`2026-05-16`)**:  

- Adopted.  
- The repository currently lacks any CI definition; this does not match the existing test scale and mixed C++/Python build reality.  
- The follow-up should first take a Linux mainline minimal smoke test as Phase 1, without defaulting to CUDA matrix, long training, or cooperative/HMoE large regression in the initial CI.  

### 4.2 🟡 CMake target splitting not yet executed  

**Location**: [CMakeLists.txt](../../../CMakeLists.txt)  

**Observation**: Although `CMakeLists.txt` defines source groups such as `EF_CORE_ENGINE_SOURCES`, `EF_CORE_MISSION_SOURCES`, all are ultimately compiled into a single `ef_core` static library.  

**Impact**:  
- Any `.cpp` change triggers full rebuild of `ef_core`  
- Cannot enforce dependency direction at CMake link time  
- WP7 candidate target order is clear but not executed: `ef_components → ef_models → ef_systems → ef_mission_runtime → ef_sim_core → ef_runtime_facade`  

**Suggestion**: Execute as FP2 (Freeze Plan 2), splitting source groups into independent CMake targets one by one.  

**Annotation (`2026-05-16`)**:  

- Partially adopted.  
- The factual observation "source groups defined but targets not split" is valid.  
- However, it is not recommended to make it the primary follow-up line, nor to implement the entire target chain listed at once.  
- A better strategy is to first finalize CI and entry/version strategy, then freeze an incremental target split plan separately.  

### 4.3 🟡 `SimulationKernel` public API too broad  

**Location**: [src/core/engine/simulation_kernel.h](../../../src/core/engine/simulation_kernel.h)  

**Observation**: The header is ~200 lines with 50+ public methods, simultaneously handling lifecycle, factory injection, environment configuration, command injection (three sets of interfaces), observation queries, weapon firing, exact-stage trace, and more.  

**Impact**:  
- Violates Interface Segregation Principle  
- Unit tests require mocking the entire kernel  
- New capabilities have no clear home  

**Suggestion**: Split into `SimulationKernel` (lifecycle) + `KernelCommandInterface` + `KernelObservationInterface` + `KernelEnvironmentInterface`, composed by the facade.  

**Annotation (`2026-05-16`)**:  

- Partially adopted.  
- The diagnosis that `SimulationKernel`'s public surface is too broad is valid.  
- However, introducing multiple new public interface classes directly is not recommended right now, as it would affect bindings, tests, and existing owner semantics.  
- A safer route: keep `SimulationKernel` as owner without breaking existing public names, then gradually sink command, observation, and environment related implementations into narrower helper / adapter / facade composition layers.  

### 4.4 🟡 Python entry scripts too large  

**Location**:  
- [train.py](../../../train.py) — 1127 lines  
- [world_model_train.py](../../../world_model_train.py) — ~3000+ lines  

**Observation**: Top-level entry scripts mix argument parsing, environment construction, training loops, callback registration, checkpoint management, and other responsibilities.  

**Impact**:  
- Adding a new training mode requires modifying the global entry point  
- Training loop logic cannot be reused inside `python/rl/`  
- Code navigation is difficult  

**Suggestion**: Move core training loop logic into `python/rl/training/` (new subdomain); `train.py` should only handle CLI parsing and dispatch.  

**Annotation (`2026-05-16`)**:  

- Partially adopted; the problem itself is valid.  
- [train.py](../../../train.py) and [world_model_train.py](../../../world_model_train.py) have indeed exceeded the complexity a single entry script should carry.  
- However, the placement should not be mechanically unified into `python/rl/training/`:  
  - `train.py` is better suited for a general `python/training/` or equivalent main package;  
  - `world_model_train.py` should form an independent training subdomain under `python/world_model/`.  
- The current action should first freeze the first-phase consolidation of `train.py`, not couple it with the large-scale refactoring of `world_model_train.py`.  

### 4.5 🟢 Ambiguous directory naming  

**Location**:  
- `src/components/systems/`  
- `src/systems/systems/`  
- `src/core/engine/`  

**Observation**:  
- Nested `systems` is unclear; `components/systems` actually means "platform system components (sensor/comm/navigation)", while `systems/systems` means "per-frame mutation logic for platform systems"  
- `core/engine` is easily confused with facade/runtime engine concepts  

**Impact**: Persistent cognitive confusion for newcomers (or AI agents).  

**Suggestion**: The freeze document has already marked this as an open issue. Proposed:  
- `components/systems` → `components/platform`  
- `systems/systems` → `systems/platform`  
- `core/engine` → `core/sim`  

**Annotation (`2026-05-16`)**:  

- Partially adopted.  
- The judgment "naming ambiguity exists" is accurate, especially `components/systems` vs `systems/systems`.  
- However, the risk assessment "pure rename, low risk" is too optimistic; the true cost will affect include paths, READMEs, tests, and freeze documents.  
- Directory rename should not be the primary follow-up line now. If executed later, it should be frozen separately, prioritizing the single most misleading point rather than changing all three at once.  

### 4.6 🟢 External dependencies downloaded on-the-fly via FetchContent  

**Location**: [CMakeLists.txt:20-49](../../../CMakeLists.txt)  

**Observation**:  
```cmake
FetchContent_Declare(flecs GIT_TAG v4.0.0)
FetchContent_Declare(spdlog GIT_TAG v1.13.0)
FetchContent_Declare(nanobind GIT_TAG v1.9.2)
FetchContent_Declare(nlohmann_json GIT_TAG v3.11.3)
```

**Impact**:  
- Cannot build offline  
- Dependency versions scattered in CMakeLists.txt, no centralized management  
- No hash verification (FetchContent does not check content integrity)  

**Suggestion**: Consider vcpkg manifest or Conan. Minimum cost solution: add `URL_HASH` parameter to `FetchContent_Declare`.  

**Annotation (`2026-05-16`)**:  

- Partially adopted.  
- The offline build and dependency governance issues with the current `FetchContent` approach are valid.  
- However, the "minimum cost solution" phrasing needs correction: the current syntax is `GIT_REPOSITORY + GIT_TAG`, which does not directly support `URL_HASH`.  
- A more realistic near-term fix:  
  - First tighten third-party dependencies from tag pin to commit SHA pin;  
  - If hash verification is later needed, either switch to archive URLs or introduce a package manager.  
- `vcpkg/Conan` should remain a future evaluation item, not an immediate action for this round.  

### 4.7 🟢 `.gitignore` excludes key development directories  

**Location**: [.gitignore](../../../.gitignore#L56-L63)  

**Observation**: `scenarios/`, `datasets/`, `experiments/`, `output/` are completely excluded by gitignore.  

**Impact**:  
- `scenarios/`: scene definitions have no version history. If scenes are managed through another channel, this should be documented in README.  
- `experiments/`: training run records have no git history, making it impossible to recover "which config and seed were used for a given training run" from commit history.  

**Suggestion**: Handle separately:  
- `scenarios/` may be worth removing from gitignore (or creating a separate scenarios repository with versioned references)  
- `experiments/` consider Git LFS, or keep current strategy but add versioned recording of experiment metadata  

**Annotation (`2026-05-16`)**:  

- Partially adopted, with `scenarios/` as higher priority.  
- There is a clear conflict between [.gitignore](../../../.gitignore) and [README.md](../../../README.md) regarding `scenarios/`: the former ignores it, the latter describes it as a mainline input.  
- In contrast, keeping `experiments/`, `datasets/`, `output/` ignored better suits the current research workflow; it is not advisable to bring large generated artifacts into the main repository for the sake of "version completeness".  
- Therefore, the follow-up task should first clarify and address the versioning strategy for `scenarios/`, then decide whether a separate repository or inclusion in the main repository is appropriate.  

### 4.8 🟢 Fragmented build directories  

**Observation**: The repository has multiple build directories:  
- `build/`  
- `build-gpu/`  
- `build-workshop/`  
- `build-facade-local/`  

**Impact**: Managing multiple build targets relies on manual switching via environment variables `CMO_BUILD_DIR` and `PYTHONPATH`, which is error-prone.  

**Suggestion**: README already recommends `build-workshop` as convention, but suggests centralizing management in `tools/maintenance/cmo_env.sh` and adding a `cmo_env_validate` check.  

**Annotation (`2026-05-16`)**:  

- Adopted.  
- The "centralized management" part is partially done: the repository now includes [tools/maintenance/cmo_env.sh](../../../tools/maintenance/cmo_env.sh) as a unified entry point for `.venv`, `CMO_BUILD_DIR`, and `PYTHONPATH`.  
- Still to be completed:  
  - Add an explicit `cmo_env_validate` or equivalent validation command;  
  - Gradually switch README/script examples from scattered handwritten environment variables to the unified entry point.  

---

## 5. Non-Goals  

This review does not include:  
- Rewriting the physics model or changing `SimulationKernel::step()` semantics  
- Changing default training runtime backend  
- Deleting legacy command surface  
- Proposing a new GPU exact-step mainline  
- Breaking API renames  

---

## 6. Recommended Execution Order  

| Priority | Item | Expected Benefit | Risk |
|----------|------|------------------|------|
| P0 | Add CI automation | Prevent regression | Low |
| P1 | CMake target splitting (WP7 second half) | Incremental compilation + link-level checks | Medium (need per-target verification) |
| P1 | Split training loop in train.py | Code maintainability | Medium (must keep CLI compatibility) |
| P2 | SimulationKernel interface split | Testability + extensibility | Medium-High (changes API surface) |
| P2 | Resolve directory naming ambiguity | Readability | Low (pure rename) |
| P3 | Harden dependency management | Offline build + security | Low |
| P3 | Review .gitignore strategy | Version traceability | Low (but strategic impact) |

## 7. Open Questions (Candidates for next freeze plan)  

- Whether to rename `src/interfaces/python` to `src/bindings/python`  
- Whether to rename `gpu` to `accelerators/gpu`  
- Whether to introduce a package manager (vcpkg/Conan) to replace FetchContent  
- Version management strategy for scenarios: separate repository vs. un-gitignore vs. Git LFS  

**Annotation (`2026-05-16`)**:  

- This round will not treat `interfaces/python -> bindings/python` or `gpu -> accelerators/gpu` as active tasks.  
- `vcpkg/Conan` remains a future evaluation topic and will not enter the current freeze plan.  
- The version management strategy for `scenarios` remains an active issue and will enter a clear work package in the subsequent freeze plan.
