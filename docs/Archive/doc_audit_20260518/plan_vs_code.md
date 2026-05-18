# Plan Docs vs Implementation Status

## 1. architecture/system_layering_and_engine_encapsulation_plan.md

### Stale/Not Implemented (P0)
- **`IPhysicsBackend`, `ISimulationRuntime`, `IBatchSimulationRuntime`, `IExecutionEpisodeRuntime`, `ISimulationDiagnostics`** — these interfaces do NOT exist anywhere in the codebase. No headers, no implementations.
- **`PhysicsWorldState`, `PhysicsStepContext`, `PhysicsStepResult`, `PhysicsDebugTrace`** — these DTO types do NOT exist.

### Not Implemented (P1)
- **Proposed target directory layout** (`src/contracts/`, `src/physics/`, `src/simulation/`, `src/adapters/`, `python/frontend/`) — never materialized. Codebase retains original layout.
- **Proposed CMake target split** (`ef_contracts`, `ef_physics`, `ef_simulation`, `ef_runtime`) — never happened. All code still in single `ef_core` target.

### Note
This is an architecture draft, not a frozen execution plan. Full implementation was not expected.

---

## 2. architecture/src_layered_refactor_freeze.md

### Completed (WP1-WP7 all verified)
- **WP1** (READMEs): All 9 READMEs exist under src/ directories.
- **WP2** (command/tasking split): `src/components/command/` and `src/components/tasking/` exist with expected files. `action.h` compatibility header present.
- **WP3** (Python bindings split): All 5 `bindings_*.cpp` files exist. `python_module.cpp` reduced from 3000+ to 23 lines.
- **WP4** (SimulationKernel boundary): All 7 listed files exist.
- **WP5** (EpisodeController split): All 3 detail files exist. `mission/` correctly split into `runtime/` and `episode/`.
- **WP6** (Facade escape hatches): Architecture test exists at `tests/architecture/test_runtime_facade_layering.py`.
- **WP7** (CMake target prep): All source group variables in CMakeLists.txt.

### Mismatches (P2)
- **WP4 list incomplete**: `simulation_kernel_damage_debug_api.cpp` (67 lines) exists in `src/core/engine/` but not listed.
- **Unresolved rename questions**: `src/interfaces/python` → `src/bindings/python`, `components/systems` + `systems/systems` renames, `core/engine` → `core/sim`, `gpu` → `accelerators/gpu` — none happened.

---

## 3. runtime_facade/runtime_facade_contract_plan.md

### Completed
- Core files exist: `src/runtime/facade/runtime_facade_types.h`, `runtime_facade.h`, `runtime_facade.cpp`
- `WorldBatchVecEnv` uses `_RuntimeFacadeAdapter`

### Not Implemented (P1)
- **8 proposed DTOs** (`RuntimeCapabilities`, `RuntimeBatchConfig`, `BatchWorldSetupRequest`, `BatchResetRequest`, `ExecutionBatchStepRequest`, `ExecutionBatchStepResult`, `RuntimeStateSnapshot`, `ObservationBatchPacket`) — not implemented as independent contract types. Actual facade API is closer to `WorldBatchRuntime` forwarding.
- **9 proposed method signatures** — not exposed as described. Actual API shapes differ.

---

## 4. runtime_facade/runtime_facade_task_bootstrap_plan.md

### Completed (WP1-WP6 all verified)
- `runtime_facade_types.h`, `runtime_facade.h`, `runtime_facade.cpp` exist
- `tests/runtime/test_runtime_facade.py` exists
- Benchmark artifact at `docs/plan/results/wp6_benchmark_world_batch_vec_env_phase4.json`

### Stale (P1-P2)
- **Line counts outdated**: `python_module.cpp` was 2958 → now 23 lines (WP3 split). `scenario_loader/core.py` was 5009 → now 1141.

---

## 5. runtime_facade/runtime_facade_layering_cleanup_freeze.md

### Completed (WP1-WP7 all verified)
- `_RuntimeFacadeAdapter` confirmed in `world_batch_vec_env.py`
- Architecture test exists

### Not Implemented (P1)
- **WP7 CMake target split never happened**: `ef_contracts`, `ef_mission_runtime`, `ef_simulation_engine`, `ef_runtime_facade`, `ef_models_default` still not separate targets. Only `ef_core` and `ef_py` exist.

---

## 6-10. exact_runtime/ GPU Plans (5 documents)

### Completed
- `observation_return_mode` with `copy`/`view` modes implemented
- Regression tests exist
- ~50% of `gpu_execution_mainline_integration_checklist.md` items checked

### NOT Implemented (P0)
- **`exact_cpu_backend.*`** — proposed files do not exist
- **`exact_gpu_backend.*`** — no GPU backend code
- **`gpu_resident_state.h` / `.cu`** — no GPU resident state implementation
- **Phase A files** (`device_memory_pool.h/.cu`, optimized SoA packing)
- **Phase B files** (`gpu_ground_contact.cu`, `gpu_force_system.cu`, `gpu_aerodynamics.cu`)
- **Phase C files** (`gpu_control_law.cu`, `gpu_leapfrog.cu`)
- **Phase D diagnostic tools** (`benchmark_exact_world_step_performance.py`, etc.)
- **CMake target `gpu_exact_world_step`** does not exist

### NOT Implemented (P0-P1)
- UniversalEnv does NOT use GPU batch helper path
- Mission/reward/termination still CPU-side in ScenarioLoader
- Default `WorldBatchRuntime.step_batch()` still uses CPU `SimulationKernel::step()`
- GPU flight shaping not promoted to default reward path
- Real-time sensor/comm not using GPU wide-phase

---

## 11. cooperative/multi_agent_cooperative_training_foundation_and_performance_plan.md

### Completed (WP1-WP6 all verified)
- `CooperativeWorldBatchVecEnv` exists with tests
- `nav_v2_formation_v1` observation mode connected
- `train.py` has `cooperative_execution` agent layer branch
- `cooperative_director.py` exists
- `multi_agent_benchmark.py` with tests exists
- Cooperative cruise scenario exists

### Stale (P2)
- Line counts outdated: `scenario_loader/core.py` went from 5009 → 1141; `world_batch_vec_env.py` from 1660 → 1620

---

## 12. cooperative/p8_cooperative_execution_pipeline_findings_and_plan.md

### Completed (A1-A4 verified)
- All described tests exist (with slight test name differences)

### Mismatch (P2)
- Test name `test_loader_mission_observation_current_contract_ignores_formation_offsets` documented vs actual `test_loader_nav_v2_current_contract_still_ignores_formation_offsets`

---

## 13. architecture/architecture_and_performance_research_followup.md

### Stale (P1)
- **Line counts severely outdated**:
  - `scenario_loader/core.py`: claimed 5009, actual 1141
  - `world_batch_vec_env.py`: claimed 1660, actual 1620
  - `universal_env.py`: claimed 807, actual 344
  - `python_module.cpp`: claimed 2958, actual 23

---

## Summary

| Severity | Count | Key Items |
|----------|-------|-----------|
| P0 | 15+ | Architecture interfaces + DTOs never created; exact_cpu/gpu backends not implemented; gpu_resident_state, device_memory_pool, all GPU Phase A-D files missing |
| P1 | 8 | CMake target split never happened; contract DTOs/methods not matching; line counts outdated; directory renames not done |
| P2 | 6 | Unlisted files; unresolved rename questions; test name inaccuracies |
