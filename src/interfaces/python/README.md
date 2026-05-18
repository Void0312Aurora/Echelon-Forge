# `src/interfaces/python` Boundary

`interfaces/python` is the nanobind exposure layer. It exposes `runtime/facade`, required compatibility APIs from `core`, and the relevant data types to Python. It should not implement domain behavior here.

## Allowed

- `NB_MODULE` aggregation and binding functions.
- Python exposure of C++ enums, structs, and classes.
- Lightweight conversion from Python arguments into C++ requests/results.
- Binding-layer view adapters such as DLPack.

## Forbidden

- Task JSON interpretation, episode transitions, or reward breakdown.
- Physics, sensors, weapons, or control-law implementations.
- New long-lived mainline APIs that bypass `RuntimeFacade`.
- Training configuration governance or scenario directory governance.

## Current Structure

`python_module.cpp` keeps only `NB_MODULE`, `set_log_level`, and the calls that register partitioned bindings. Each binding unit is maintained by responsibility:

- `bindings_core.cpp`
  Low-level compatibility types, `SimulationKernel`, and legacy diagnostics entry points.
- `bindings_command.cpp`
  Command/tasking enums plus `PilotAction`, `MissionCommand`, `TaskOrder`, `LeaderIntent`, `PilotReport`, and `CommPacket`.
- `bindings_episode.cpp`
  Mission/runtime/reward/termination/episode-controller data structures and pure runtime functions.
- `bindings_runtime.cpp`
  `WorldBatchRuntime`, `RuntimeFacade`, and facade request/result types.
- `bindings_gpu.cpp`
  GPU helpers, batch observation/visual helpers, and DLPack / `GpuTensorView` adapters.
- `binding_utils.h`
  Shared nanobind includes, partition registration declarations, and numpy owner helpers.

When adding new bindings, place them in the matching partition first. Only cross-partition nanobind utilities should go into `binding_utils.h`.

## Migration Notes

Keeping low-level bindings for `SimulationKernel` and `WorldBatchRuntime` is acceptable for the compatibility period. New mainline capabilities should prefer binding `RuntimeFacade`.
