<!-- Machine-translated draft generated on 2026-05-18 from src/models/core/README.md. Review before treating this file as authoritative. -->

# `src/models/core` Boundaries

`models/core` holds base model implementations, such as the default unit factory implementation.

## Allowed

- Default unit factory.
- Conversion and instantiation helpers for `content/` unit definitions.

## Forbidden

- World lifecycle ownership.
- ECS system registration.
- Python binding or facade.

## Migration Notes

The owner of the instantiation process should still be in `core/engine`; this directory only provides model implementations and factory strategies.
