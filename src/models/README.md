# `src/models` Boundary

`models/` stores replaceable domain-model implementations. It provides capabilities such as control, environment, sensors, effects, guidance, and unit factories to `systems/` and `core/engine`.

The model layer is multi-domain aware but uneven in maturity. Air control, air
effects, and execution-adjacent models remain the deepest paths. Naval support
includes platform/sensor/acoustic/weapon-mount helpers and explicit effects
placeholder routing. Ground support is limited to unit-factory capability
evidence and explicit effects placeholder routing; it does not claim full
ground runtime maturity.

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
- `ground/`: Ground-owned model placeholder routing where runtime fidelity is not yet implemented.
- `naval/`: Naval-owned model adapters and placeholder routing.
- `systems/`: Platform-system models such as sensors and acoustic helpers.
- `weapons/`: Effects, guidance, and naval weapon-mount helpers.

## Current Entry Points for Reading

- [air/README.md](air/README.md)
- [core/README.md](core/README.md)
- [environment/README.md](environment/README.md)
- [ground/README.md](ground/README.md)
- [naval/README.md](naval/README.md)
- [systems/README.md](systems/README.md)
- [weapons/README.md](weapons/README.md)

## Current File Locations

- `air/`
  - `default_control_model.cpp`, `default_effects_air_domain.h`
- `core/`
  - `default_unit_factory.h`
- `environment/`
  - `default_environment_model.cpp`, `default_environment_snapshot.h`
- `ground/`
  - `default_effects_ground_domain.h`
- `naval/`
  - `default_effects_naval_domain.h`, `naval_sensor_maritime_adapter.h`
- `systems/`
  - `default_sensor_model.cpp`, `default_acoustic_model.cpp`
- `weapons/`
  - `default_effects_model.cpp`, `default_guidance_model.cpp`,
    `naval_weapon_mounts.h`, `detail/default_effects_domain_routing_detail.inc`

## Migration Notes

Before adding a new model, first check whether `core/interfaces` already defines the contract. If it does not, add the interface boundary before introducing the default implementation.
