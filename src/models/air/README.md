<!-- Machine-translated draft generated on 2026-05-18 from src/models/air/README.md. Review before treating this file as authoritative. -->

# `src/models/air` Boundary

`models/air` holds default model implementations related to aviation and flight control.

## Allowed

- Default implementations of control models.
- Pure computational logic related to flight control and aerodynamic response.

## Disallowed

- ECS system registration.
- `SimulationKernel` lifecycle.
- Python binding or training configuration parsing.

## Migration Notes

If a model needs to become a replaceable contract, first add to `core/interfaces`, then provide the default implementation in this directory.
