<!-- Machine-translated draft generated on 2026-05-18 from src/content/README.md. Review before treating this file as authoritative. -->

# `src/content` Boundary

`content/` stores content schemas, unit definitions, and loaders. It describes "what units and static configurations exist" and does not own runtime behavior.

## Allowed

- Unit definition types.
- Loaders for JSON or other content formats.
- Static content validation and transformation.

## Prohibited

- Simulation step, mission episode, reward, or termination logic.
- Python binding.
- Training configuration governance.
- Direct management of ECS world lifecycle.

## Dependency Direction

`core/engine` and `models/core` may consume `content/`. `content/` does not depend on `core/engine`, `runtime/facade`, or `interfaces/python`.
