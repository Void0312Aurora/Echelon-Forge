# `src/models` Boundary

`models/` stores replaceable domain-model implementations. It provides capabilities such as control, environment, sensors, effects, guidance, and unit factories to `systems/` and `core/engine`.

The model layer is multi-domain aware but uneven in maturity. Air control and
execution-adjacent models remain the deepest path; naval support includes
platform/sensor/acoustic/weapon-mount helpers; ground support is limited to
unit-factory capability evidence such as deferred flat mobility and land
tactics metadata.

## Allowed

- Default model implementations.
- Pure C++ computational logic for replaceable models.
- Helpers that depend only on component data and contracts from `core/interfaces`.
- Unit-factory capability evidence for typed setup, including naval and early ground-aware metadata.

## Forbidden

- ECS system registration.
- Runtime owners, batch owners, or facades.
- Python bindings.
- Training configuration or scenario orchestration.
- Full ground movement, sensing, terrain, fires, or damage model implementation before the corresponding interfaces and runtime owner exist.

## Subdirectory Conventions

- `air/`: Aviation models such as flight control.
- `core/`: Foundational model implementations such as unit factories.
- `environment/`: Environment models and snapshots.
- `systems/`: Platform-system models such as sensors and acoustic helpers.
- `weapons/`: Effects, guidance, and naval weapon-mount helpers.

## Current Entry Points for Reading

- [air/README.md](air/README.md)
- [core/README.md](core/README.md)
- [environment/README.md](environment/README.md)
- [systems/README.md](systems/README.md)
- [weapons/README.md](weapons/README.md)

## Current File Locations

- `air/`
  - `default_control_model.cpp`
- `core/`
  - `default_unit_factory.h`
- `environment/`
  - `default_environment_model.cpp`, `default_environment_snapshot.h`
- `systems/`
  - `default_sensor_model.cpp`, `default_acoustic_model.cpp`
- `weapons/`
  - `default_effects_model.cpp`, `default_guidance_model.cpp`, `naval_weapon_mounts.h`

## Migration Notes

Before adding a new model, first check whether `core/interfaces` already defines the contract. If it does not, add the interface boundary before introducing the default implementation.
