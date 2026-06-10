# `src/components` Boundary

`components/` stores only ECS components, lightweight value types, and stable DTO-like structs. Types here may be read or bound by `systems/`, `core/`, `runtime/facade`, and `interfaces/python`, but they must not own runtime orchestration logic.

The current component surface is multi-domain rather than flight-only: air remains the most complete execution surface, naval has maintained platform plus command/tasking DTO slices, and ground now has a narrow tasking/status owner slice plus native schema evidence. Do not treat those ground-aware primitives as a complete land-domain component model.

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
- `domains/`: domain-owned component slices. Existing domains are `air/`,
  `naval/`, and `ground/`; new domains should be added here instead of at the
  `components/` root.
- `combat/`: cross-domain combat state such as health, scoring, and shared
  weapon/damage primitives. Domain-specific combat components live under
  `domains/<domain>/combat/`.
- `physics/`: shared physical state, dynamics, forces, instruments,
  performance state, and current ground-contact primitives.
- `systems/`: cross-domain platform-system state components for
  communications, data links, sensors, sonar, electronic warfare, navigation,
  logistics, and similar areas.
- `visual/`: visual-sensor input and output state.
- `command/`: shared command shell, command links, legacy command DTOs, and
  command common foundations. Domain-specific command components live under
  `domains/<domain>/command/`.
- `tasking/`: shared tasking shell and common C2/tasking foundations.
  Domain-specific tasking components live under `domains/<domain>/tasking/`.

## Current Entry Points

- [basic/README.md](basic/README.md)
- [domains/README.md](domains/README.md)
- [combat/README.md](combat/README.md)
- [physics/README.md](physics/README.md)
- [systems/README.md](systems/README.md)
- [visual/README.md](visual/README.md)
- [command/README.md](command/README.md)
- [tasking/README.md](tasking/README.md)

## Current File Layout

- `basic/`
  - `common.h`, `environment_data.h`, `tags.h`
- `domains/`
  - `air/platform/flight_dynamics_tuning.h`
  - `air/combat/damage_air.h`, `air/combat/weapon_air.h`
  - `air/command/mission_command_air.h`, `air/command/control_input_resolution.h`
  - `air/tasking/air_tasking_enums.h`, `air/tasking/task_order_air.h`,
    `air/tasking/leader_intent_air.h`, `air/tasking/pilot_report_air.h`
  - `naval/platform/ship_platform.h`, `naval/platform/submarine_platform.h`,
    `naval/platform/embarked_air_ops.h`
  - `naval/combat/damage_naval.h`, `naval/combat/weapon_naval.h`
  - `naval/command/mission_command_naval.h`
  - `naval/tasking/naval_tasking_enums.h`, `naval/tasking/task_order_naval.h`,
    `naval/tasking/leader_intent_naval.h`, `naval/tasking/pilot_report_naval.h`
  - `ground/combat/damage_ground.h`, `ground/combat/weapon_ground.h`
  - `ground/command/mission_command_ground.h`
  - `ground/tasking/ground_tasking_enums.h`, `ground/tasking/task_order_ground.h`,
    `ground/tasking/leader_intent_ground.h`, `ground/tasking/pilot_report_ground.h`
- `combat/`
  - `common/damage_common.h`, `common/weapon_common.h`
  - `health.h`, `scoring.h`
- `physics/`
  - `dynamics.h`, `forces.h`, `instruments.h`, `performance.h`, `control_law.h`, `propulsion_readouts.h`
  - `action.h` remains only as a command/tasking compatibility umbrella
- `systems/`
  - `comm.h`, `data_link.h`, `ew.h`, `logistics.h`, `navigation.h`, `sensor.h`, `sonar.h`, `track_management.h`
- `visual/`
  - `visual_sensor.h`
- `command/`
  - `pilot_action.h`, `mission_command.h`, `command_link.h`, `legacy_command.h`
  - `common/mission_command_core.h`, `common/comm_message.h`
- `tasking/`
  - `task_order.h`, `leader_intent.h`, `pilot_report.h`, `tasking_enums.h`
  - `common/*` contains shared C2/tasking foundations
  - `ground/*` is intentionally limited to G0/G1 tasking/status and native schema boundary fields; land movement, sensing, fires, damage, terrain, and combat runtime remain held.

## Migration Notes

`physics/action.h` currently carries both command and tasking types. New shared
command/tasking types should go into `components/command` or
`components/tasking`; domain-specific extensions should go into
`components/domains/<domain>/{command,tasking}`. Do not keep expanding
`components/physics/action.h`.
