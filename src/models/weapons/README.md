<!-- Machine-translated draft generated on 2026-05-18 from src/models/weapons/README.md. Review before treating this file as authoritative. -->

# `src/models/weapons` Boundary

`models/weapons` holds default model implementations for weapon effects, guidance, and hit detection.

## Allowed

- effects model
- guidance model
- Purely computational weapon behavior models

## Forbidden

- ECS system registration
- combat component definition
- Python binding or mission episode orchestration

## Migration Notes

System scheduling is placed in `systems/combat`, state is placed in `components/combat`, and model implementations are placed in this directory.
