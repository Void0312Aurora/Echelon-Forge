# `src/core` Boundary

`core/` is the C++ runtime kernel layer. It owns single-world simulation, batch runtime, mission/episode runtime, geometry queries, and model interfaces. It may orchestrate the lower-level `systems/`, `models/`, `components/`, and `content/` layers, but it does not carry Python bindings or application-layer facade contracts.

The kernel layer is multi-domain aware, with air execution still the most
mature path. Naval systems and contracts are present at bounded seams; ground is
limited to setup/type/capability evidence plus shared aircraft/terrain contact
primitives, not a land-domain runtime.

## Allowed

- Runtime owners such as `SimulationKernel` and `WorldBatchRuntime`.
- Mission, objective, reward, termination, and episode controller logic.
- Geometry queries and core model interfaces.
- The stable C++ implementation foundation behind facade-facing APIs.
- Bounded orchestration of air, naval, and early ground-aware setup data through lower-layer public APIs.

## Forbidden

- nanobind/Python exposure code.
- Frontend-specific API naming and language-binding compatibility logic.
- Replacing the CPU truth path with the GPU experimental mainline.
- Defining component or model implementations directly inside `core`.
- Claiming ownership of full ground movement, sensing, fires, damage, or land-domain runtime before those lower layers exist.

## Subdirectory Conventions

- `engine/`: single-world kernel and batch runtime owners.
- `mission/`: mission/episode/objective/reward/termination runtime.
- `geometry/`: spatial query and geometry helper runtime.
- `interfaces/`: model interfaces and abstraction contracts shared across `core`.

## Reading Entry Points

- [engine/README.md](engine/README.md)
- [mission/README.md](mission/README.md)
- [geometry/README.md](geometry/README.md)
- [interfaces/README.md](interfaces/README.md)

## Current File Layout

- `engine/`
  - `simulation_kernel.h/.cpp`
  - `simulation_kernel_systems.cpp`
  - `simulation_kernel_command_api.cpp`
  - `simulation_kernel_observation_api.cpp`
  - `simulation_kernel_visual_api.cpp`
  - `simulation_kernel_weapon_api.cpp`
  - `world_batch_runtime.h/.cpp`
  - `exact_stage_inventory.cpp`
- `mission/`
  - `runtime/*`: mission, objective, reward, termination, and execution runtime
  - `episode/*`: episode state, batch preparation, controller
  - `episode/detail/*`: private helpers for transitions, codecs, and reward breakdown
- `geometry/`
  - `spatial_query_runtime.h/.cpp`
- `interfaces/`
  - `control_model.h`, `effects_model.h`, `environment_model.h`
  - `guidance_model.h`, `sensor_model.h`, `observation.h`, `unit_data.h`, `unit_factory.h`

## Migration Notes

`mission/` has already been split into the physical layers `runtime/`, `episode/`, and `episode/detail/`. New mission code should go into one of these sublayers first, while keeping `runtime/` from depending back on `episode/`.

Future `engine/` splits should continue to break implementation files apart by responsibility while keeping the public API stable.
