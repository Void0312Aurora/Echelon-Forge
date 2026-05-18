# `src/components` Boundary

`components/` stores only ECS components, lightweight value types, and stable DTO-like structs. Types here may be read or bound by `systems/`, `core/`, `runtime/facade`, and `interfaces/python`, but they must not own runtime orchestration logic.

## Allowed

- Plain data fields, default values, and lightweight enums.
- State components that map directly to ECS storage.
- Command/tasking DTOs that move across layers without executing business workflows.
- Small helper methods that do not depend on a Flecs world.

## Forbidden

- System registration, tick/update logic, physics integration, or mission state machines.
- Python/nanobind binding helpers.
- Control logic related to `SimulationKernel`, `WorldBatchRuntime`, or `RuntimeFacade`.
- Logic that needs to read databases, load scenarios, or access a runtime owner.

## Subdirectory Conventions

- `basic/`: foundational components such as entity tags, factions, positions, and environment data.
- `combat/`: combat-state components such as damage, health, weapon mounts, and scoring.
- `physics/`: physical state, dynamics, forces, instruments, and performance state.
- `systems/`: platform-system state components for communications, data links, sensors, electronic warfare, navigation, logistics, and similar areas.
- `visual/`: visual-sensor input and output state.
- `naval/`: naval platform state components for ships, submarines, and embarked air operations.
- `command/`: target directory for pilot actions, mission commands, command links, and legacy command DTOs.
- `tasking/`: target directory for task orders, leader intent, pilot reports, and C2/tasking enums.

## Current Entry Points

- [basic/README.md](basic/README.md)
- [combat/README.md](combat/README.md)
- [physics/README.md](physics/README.md)
- [systems/README.md](systems/README.md)
- [visual/README.md](visual/README.md)
- [naval/README.md](naval/README.md)
- [command/README.md](command/README.md)
- [tasking/README.md](tasking/README.md)

## Current File Layout

- `basic/`
  - `common.h`, `environment_data.h`, `tags.h`
- `combat/`
  - `damage.h`, `health.h`, `scoring.h`, `weapon.h`
- `physics/`
  - `dynamics.h`, `forces.h`, `instruments.h`, `performance.h`, `control_law.h`
  - `action.h` remains only as a compatibility umbrella
- `systems/`
  - `comm.h`, `data_link.h`, `ew.h`, `logistics.h`, `navigation.h`, `sensor.h`, `track_management.h`
- `visual/`
  - `visual_sensor.h`
- `naval/`
  - `ship_platform.h`, `submarine_platform.h`, `embarked_air_ops.h`
- `command/`
  - `pilot_action.h`, `mission_command.h`, `command_link.h`, `legacy_command.h`
  - `common/mission_command_core.h`, `common/comm_message.h`
  - `air/mission_command_air.h`, `air/control_input_resolution.h`
  - `naval/mission_command_naval.h`
- `tasking/`
  - `task_order.h`, `leader_intent.h`, `pilot_report.h`, `tasking_enums.h`
  - `common/*`, `air/*`, and `naval/*` are the entry points for the split subdomains

## Migration Notes

`physics/action.h` currently carries both command and tasking types. New command/tasking types should go into `components/command` or `components/tasking`; do not keep expanding `components/physics/action.h`.
