# `src/models/core` Boundaries

`models/core` holds base model implementations, such as the default unit factory implementation.

The default unit factory is now multi-domain aware at the content/materialization
edge: it can attach naval platform/stores/weapon components and emit typed setup
capability evidence for early ground-aware units. Ground mobility is currently
recorded as deferred flat mobility evidence, not as a full land movement model.

## Allowed

- Default unit factory.
- Conversion and instantiation helpers for `content/` unit definitions.
- Platform capability bundle and resolved-spawn evidence derived from content definitions.

## Forbidden

- World lifecycle ownership.
- ECS system registration.
- Python binding or facade.
- Native ground movement/sensing/fires/damage runtime or maintained ground tasking schema.

## Migration Notes

The owner of the instantiation process should still be in `core/engine`; this directory only provides model implementations and factory strategies.
