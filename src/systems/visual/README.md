# `src/systems/visual` Boundary

`systems/visual` contains the ECS scheduling and per-tick update logic for visual observation systems.

## Allowed

- Visual sensor systems.
- Combined updates to visual components and spatial query results.

## Forbidden

- Visual component definitions.
- GPU CUDA kernels.
- Python image/DLPack bindings.
- Mission episode or facade logic.

## Migration Notes

GPU acceleration helpers belong in `gpu/`; Python view export belongs in `interfaces/python`; this directory is only responsible for ECS system behavior.
