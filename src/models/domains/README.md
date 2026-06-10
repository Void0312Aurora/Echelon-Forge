# `src/models/domains` Boundary

`models/domains` owns replaceable model implementations, adapters, and explicit
placeholder routes that are specific to a concrete domain. New domain model
owners should be added here instead of at the `models/` root.

## Layout

- `air/`: aviation control and air-owned default effects helpers.
- `naval/`: naval model adapters and explicit naval placeholder effects routes.
- `ground/`: ground placeholder effects routes and owner-shell helpers that keep
  ground concepts out of generic model files.

## Dependency Direction

Domain models may depend on component data and `core/interfaces` contracts.
They must not register ECS systems, own runtime/facade behavior, or depend on
bindings and training configuration.
