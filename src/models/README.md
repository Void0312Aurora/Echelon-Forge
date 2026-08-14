# `src/models` Boundary

`models/` stores replaceable domain-model implementations. It provides capabilities such as control, environment, sensors, effects, guidance, and unit factories to `systems/` and `core/engine`.

The model layer is multi-domain aware but uneven in maturity. Air control, air
effects, and execution-adjacent models remain the deepest paths under
`domains/air`. Naval support under `domains/naval` includes
platform/sensor/acoustic/weapon-mount helpers and explicit effects placeholder
routing. Ground support under `domains/ground` is limited to unit-factory
capability evidence and explicit effects placeholder routing; it does not claim
full ground runtime maturity.

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

- `core/`: Foundational model implementations such as unit factories.
- `domains/`: domain-owned model implementations and adapters. Existing domain
  owners are `air/`, `naval/`, and `ground/`; new domain model owners should be
  added here instead of at the `models/` root.
- `environment/`: Environment models and snapshots.
- `systems/`: Platform-system models such as sensors and acoustic helpers.
- `weapons/`: Effects, guidance, and naval weapon-mount helpers.

## Current Entry Points for Reading

- [core/README.md](core/README.md)
- [domains/README.md](domains/README.md)
- [environment/README.md](environment/README.md)
- [systems/README.md](systems/README.md)
- [weapons/README.md](weapons/README.md)

## Current File Locations

- `core/`
  - `default_unit_factory.h`
- `domains/`
  - `air/default_control_model.cpp`, `air/default_effects_air_domain.h`
  - `naval/default_effects_naval_domain.h`, `naval/naval_sensor_maritime_adapter.h`
  - `ground/default_effects_ground_domain.h`
- `environment/`
  - `default_environment_model.cpp`, `default_environment_snapshot.h`
- `systems/`
  - `default_sensor_model.cpp`, `default_acoustic_model.cpp`
- `weapons/`
  - `default_effects_model.cpp`, `default_guidance_model.cpp`,
    `naval_weapon_mounts.h`, `detail/default_effects_domain_routing_detail.h`

## Migration Notes

Before adding a new model, first check whether `core/interfaces` already defines the contract. If it does not, add the interface boundary before introducing the default implementation.
