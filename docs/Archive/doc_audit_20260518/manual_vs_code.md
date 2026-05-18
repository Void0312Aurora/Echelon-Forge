# Manual Docs vs Code Review

## engine_capabilities.md

### Verified
- ECS (flecs)-based `SimulationKernel`: verified (`src/core/engine/simulation_kernel.h/.cpp`)
- Fixed dt default 60Hz: verified (`time_step = 1.0 / 60.0`)
- Unit assembly from JSON in `examples/config/database/`: verified (4 unit defs)
- `Transform`, `Velocity`, `FlightModel`, `LandingGear`, `Mass`, `Propulsion`, `FuelSystem`: all verified
- `DefaultControlModel` with Stick Path + Autopilot Path: verified
- `IEnvironmentModel` with `AtmosphericData`, `SurfaceType`, `TerrainCell`: verified
- `ef_py.SimulationKernel.set_action(...)` / `set_stick_command(...)`: verified in `bindings_core.cpp`

### Mismatches
- **System pipeline ordering**: doc lists ~7 stages; actual code in `simulation_kernel_systems.cpp` has ~25 stages including ForceClear, AeroState, Propulsion, Force, Aerodynamics, GroundContact, RotationalIntegration, LeapfrogIntegration, Navigation, etc. Severity: P2 (simplification is misleading about actual physics path)

- **"MovementSystem: Integrates Velocity to update position and heading"**: `register_movement_system()` is **commented out** in `simulation_kernel_systems.cpp` line 184. Position integration is now done by Leapfrog. Severity: P1

---

## physics_engine_inventory.md

### Verified
- `SimulationKernel::step()` calls `ecs.progress(dt)`: verified
- All component definitions (`Transform`, `Velocity`, `ActionCommand`, `ActionSpaceConfig`, `MovementCommand`, `CommandLag`, `LaggedCommand`, `CommandLink`, `FlightModel`, `LandingGear`, `Mass`, `Propulsion`, `FuelSystem`, `MassProperties`): all verified in correct paths
- `IEnvironmentModel::get_atmosphere_at()` / `get_terrain_at()`: verified
- `DefaultControlModel` with both paths: verified
- `examples/config/database/aircraft/units/*.json`: verified (4 files)
- `examples/config/database/aircraft/modules/engines/*.json`: verified (2 files)
- `load_unit_definitions_json()`, `DefaultUnitFactory::spawn()`: verified
- Python bindings (`set_action`, `set_stick_command`, `set_command`): all verified
- `gym_envs/universal_env.py`, `gym_envs/leader_env.py`: verified
- `world_batch_vec_env.py`, `cooperative_world_batch_vec_env.py`: verified
- Legacy `f16_*.py` files correctly described as not maintained

### Mismatches
- **System registration order**: lists 11 stages in incorrect order; actual code has ~25 stages with different ordering (Guidance and Movement swapped, etc). Severity: P2

- **Claimed path: `src/systems/systems/logistics.h`**: Does not exist. The components are in `src/components/systems/logistics.h`. The system is `src/systems/systems/logistics_system.h`. Severity: P1

- **"MovementSystem" described as active integration path**: Movement system is **disabled**; replaced by Leapfrog integration (`leapfrog_system.h`). Severity: P1

---

## visualization_guide.md

### Verified
- SSH forwarding, .venv, PYTHONPATH, LD_PRELOAD: environment instructions (N/A for code verification)

### Mismatches
- **Claimed script: `python3 examples/viz/perception_viz.py`**: **FILE DOES NOT EXIST**. Actual files: `run_viz.py`, `viz_runner.py`. Severity: P0 (user following guide gets immediate error)

---

## landing_task_notes.md

### Verified
- Landing command code semantics (`command_code = 4` = ILS landing): verified in `default_control_model.cpp`
- Landing reward hooks naming convention: matches reward system
- Maintained training config: `examples/config/training/frozen/execution/p4_landing_retrain_v1.json` — exists
- Historical archive config: exists
- Scenario files (`landing_ils_final_train_v1.json`, `landing_ils_final_eval_v1.json`): both exist

### Mismatches
- **All absolute paths use `/home/void0312/CMO/`**: Repo root is `/home/void0312/Workshop/CMO/`. Severity: P1 (wrong root for all paths)
- **Historical experiment paths at `/home/void0312/CMO/experiments_tmp/`**: Directory does not exist at either location. Severity: P1

---

## takeoff_to_cruise_mixedmode_notes.md

### Verified
- Training config, historical config, training scenario, eval scenario: all verified
- Route rotation fix implementation: verified in `gym_envs/scenario_loader/route_generation.py`
- Viz command: `examples/viz/viz_runner.py` — exists and uses correct flag style

### Mismatches
- **All absolute paths use `/home/void0312/CMO/`**: Same root mismatch. Severity: P1
- **Claimed file: `gym_envs/scenario_loader.py`**: This is a **directory**, not a `.py` file. The route rotation code lives in `gym_envs/scenario_loader/route_generation.py`. Severity: P1
- **Historical experiments at `experiments_tmp/`**: Does not exist. Severity: P1
- **4 regression test files claimed** (`test_route_generator_world_yaw_alignment.py`, `test_route_generator_rotates_with_world_heading.py`, `test_route_generator_multileg_eval_distribution.py`, `test_flyby_sequence_past_fix_guard.py`): **NONE EXIST**. Severity: P2

---

## src_layer_map.md

### Verified
- ALL referenced README files, source files, architecture documents: every single path verified. This document is fully accurate.

No mismatches found.

---

## Summary

| Severity | Count | Key Items |
|----------|-------|-----------|
| P0 | 1 | `visualization_guide.md` references non-existent `perception_viz.py` |
| P1 | 8 | Wrong repo root in landing/takeoff notes, disabled MovementSystem claimed as active, wrong file paths in physics inventory, experiment dirs missing |
| P2 | 4 | Simplified pipeline ordering, missing regression test files |
