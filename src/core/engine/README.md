# `src/core/engine` Boundary

`core/engine` owns the single-world simulation kernel and the batch world owner. It is the mainline home of CPU exact world-step semantics and the scheduler for the lower-level ECS systems.

## Allowed

- `SimulationKernel` lifecycle, reset, step, spawn, and query APIs.
- `WorldBatchRuntime` multi-world ownership, batched reset/step, and batched command/observation operations.
- Orchestration of ECS component and system registration.
- Composition logic with `content/` and `models/`.

## Forbidden

- Python bindings.
- Mission-command JSON codecs, episode transitions, and reward breakdown logic.
- GPU kernel implementations.
- Facade request/result type definitions.

## Current Structure

The `SimulationKernel` public API stays in `simulation_kernel.h`. The implementation is split by responsibility:

- `simulation_kernel_systems.cpp`
  ECS component registration and system registration order.
- `simulation_kernel_command_api.cpp`
  Legacy movement/action commands, command links, digital pilot/tasking setters/getters, and message commands.
- `simulation_kernel_command_surface.*`
  Narrow non-owning command/read surfaces used by batch/facade-facing code so new
  call sites do not need to depend directly on the full `SimulationKernel`
  public API.
- `simulation_kernel_observation_api.cpp`
  Unit/agent observation, detections, health/fuel/messages, and observation diagnostics.
- `simulation_kernel_visual_api.cpp`
  ARB visual scene collection and visual tensor rendering APIs.
- `simulation_kernel_weapon_api.cpp`
  Missile launch APIs and launch-time missile/sensor tuning.
- `exact_stage_inventory.cpp`
  Exact-stage inventory, contract inventory, and manual trace frame helpers.
- `simulation_kernel.cpp`
  Constructor/destructor, model injection, reset/step, unit spawning, and database/environment configuration.

`SimulationKernel` keeps its broad public API for compatibility with Python
bindings and existing tests. New C++ call sites should prefer the narrow command
surface when they only need command/tasking writes or command/tasking reads.

## Dependency Direction

This layer may depend on `systems/`, `models/`, `components/`, `content/`, and `core/interfaces`. It does not depend on `runtime/facade` or `interfaces/python`.
