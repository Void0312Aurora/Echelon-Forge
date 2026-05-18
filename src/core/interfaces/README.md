<!-- Machine-translated draft generated on 2026-05-18 from src/core/interfaces/README.md. Review before treating this file as authoritative. -->

# `src/core/interfaces` Boundary

`core/interfaces` holds C++ model interfaces and abstract contracts across cores. It defines the boundary between the system and models, and does not provide default implementations.

## Allowed

- Model interfaces such as control, sensor, environment, effects, guidance.
- Cross-layer contracts such as unit data, unit factory, observation.
- Small pure virtual interfaces or stable value types.

## Forbidden

- Default model implementations.
- ECS system registration.
- Runtime owner, facade, or Python binding.
- GPU backend selection logic.

## Migration Notes

Default implementations are placed in `models/`. When new model capabilities need to be reused across systems, first define the contract in this directory, then provide the implementation in `models/`.
