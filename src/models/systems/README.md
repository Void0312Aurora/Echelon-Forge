# `src/models/systems` Boundary

`models/systems` stores platform-system related model implementations, e.g., the default sensor and acoustic model implementations.

The directory is multi-domain aware for sensing/contacts, including air/visual
sensor behavior and naval/acoustic helpers. Ship-specific maritime sensor state
is routed through `models/naval/naval_sensor_maritime_adapter.h` rather than
owned directly in the generic sensor model. It does not own full ground sensing
or land C2 runtime behavior.

## Allowed

- Replaceable computational models for platform systems such as sensor, acoustic/sonar, track, data-link, etc.
- Pure C++ logic that only depends on `core/interfaces` and component data.

## Prohibited

- Flecs system tick.
- Component definitions.
- Python binding or facade.
- Full ground sensing, terrain-control, or fires runtime.

## Migration Notes

The directory name is similar to `systems/systems`; new files must express the model type with specific business names to avoid generalized expansion.
