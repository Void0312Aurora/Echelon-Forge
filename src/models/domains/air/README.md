# `src/models/domains/air` Boundary

`models/domains/air` holds default model implementations related to aviation, flight
control, and air-owned effects consequence helpers.

## Allowed

- Default implementations of control models.
- Pure computational logic related to flight control and aerodynamic response.
- Air-owned default effects consequence helpers consumed through common effects routing.

## Disallowed

- ECS system registration.
- `SimulationKernel` lifecycle.
- Python binding or training configuration parsing.

## Migration Notes

If a model needs to become a replaceable contract, first add to `core/interfaces`, then provide the default implementation in this directory.

`default_effects_air_domain.h` is an owner helper for the shared default effects
model. It is not a standalone effects model entry point.
