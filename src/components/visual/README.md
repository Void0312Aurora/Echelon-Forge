<!-- Machine-translated draft generated on 2026-05-18 from src/components/visual/README.md. Review before treating this file as authoritative. -->

# `src/components/visual` Boundary

`components/visual` stores ECS state and data caches related to visual observation.

## Allowed

- Visual sensor state.
- Lightweight data that visual observation systems need to read and write.

## Prohibited

- Renderer, image encoding, Python view binding, or GPU kernel.
- Sensor scanning behavior itself.
- Mission/runtime orchestration.

## Migration Notes

Visual system behavior is placed in `systems/visual`, GPU visual helpers are placed in `gpu/`. This directory only retains component data.
