<!-- Machine-translated draft generated on 2026-05-18 from src/gpu/experimental/README.md. Review before treating this file as authoritative. -->

# `src/gpu/experimental` Boundary

`gpu/experimental` holds GPU probes, verification code, and temporary experiments that have not yet entered the mainline. Code here cannot be assumed as the production truth path.

## Allowed

- Performance probes.
- Parity prototypes.
- Unfrozen GPU backend experiments.

## Forbidden

- Default runtime backend.
- Unconditional dependency by the facade or training mainline.
- Behavioral substitution without explanation.

## Migration Notes

Before experimental code enters the `gpu/` main directory, it must have a freeze plan, parity boundary, and maintenance API.
