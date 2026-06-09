# `src/systems` Boundary

`systems/` contains ECS system registration and per-tick mutation logic. Code here consumes `components/` and `models/`, and is registered and scheduled by `core/engine`.

This layer is multi-domain aware but not uniformly mature: air execution now has
an explicit owner directory, physics keeps shared primitives, naval has ship/submarine and embarked-air token systems,
and ground is limited to terrain/ground-contact primitives rather than a full
land movement, sensing, fires, or damage runtime.

## Allowed

- Flecs system/query registration functions.
- Per-tick update logic for ECS components.
- Calls into swappable model implementations in `models/`.
- Use of model interfaces from `core/interfaces`.
- Bounded naval platform/runtime ticks and shared ground-contact physics primitives.

## Forbidden

- Defining new ECS components or command/tasking DTOs.
- Owning world lifecycle, batch runtime, episode controllers, or facades.
- Python bindings or external API adapters.
- Reading training configs, scenario files, or directly managing multiple worlds.
- Native ground-domain runtime loops before the movement/sensing/fires/damage ownership split is defined.

## Subdirectory Conventions

- `core/`: common operation/lifecycle systems.
- `air/`: air-domain flight control, aero state, propulsion, and aerodynamic effects.
- `physics/`: shared physics primitives such as force clearing, force projection, integration, ground contact, instruments, and related logic.
- `combat/`: damage, guidance, and combat effect systems.
- `systems/`: platform-system runtime such as command link, data link, EW, logistics, navigation, sensor, and track manager.
- `naval/`: ship/submarine motion and embarked aviation token-level runtime.
- `visual/`: visual observation systems.

## Current Entry Points

- [core/README.md](core/README.md)
- [air/README.md](air/README.md)
- [physics/README.md](physics/README.md)
- [combat/README.md](combat/README.md)
- [systems/README.md](systems/README.md)
- [naval/README.md](naval/README.md)
- [visual/README.md](visual/README.md)

## Current File Locations

- `core/`
  - `operation_system.h`
- `air/`
  - `aero_state_system.h`, `aerodynamics_system.h`, `control_system.h`, `propulsion_system.h`
- `physics/`
  - `force_clear_system.h`, `force_system.h`, `ground_contact_system.h`
  - `instrument_system.h`, `leapfrog_system.h`, `movement_system.h`, `rotational_system.h`
- `combat/`
  - `damage_system.h`, `guidance_system.h`, `pilot_weapon_release_system.h`
- `systems/`
  - `command_link_system.h`, `data_link_system.h`, `ew_system.h`
  - `logistics_system.h`, `navigation_system.h`, `sensor_system.h`, `sonar_system.h`, `track_manager_system.h`
- `naval/`
  - `ship_motion_system.h`, `submarine_motion_system.h`, `embarked_air_ops_system.h`, `naval_mission_weapon_release_system.h`
- `visual/`
  - `visual_system.h`

## Migration Notes

`systems/systems` is too broad a name. New platform systems can stay there temporarily, but the next round of renaming should converge on a clearer domain name such as `systems/platform` or `systems/avionics`.
