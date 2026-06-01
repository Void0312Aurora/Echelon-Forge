# `src/content` Boundary

`content/` stores content schemas, unit definitions, and loaders. It describes "what units and static configurations exist" and does not own runtime behavior.

The content surface is multi-domain aware. It can describe air, naval, and early
ground-aware unit definitions, including `UnitType::Ground` and capability
evidence consumed by typed platform setup. Any ground tasking/native-schema
references should remain bootstrap evidence, not a claim that `src/content`
owns a maintained C++ ground command/tasking subdomain or full ground runtime.

## Allowed

- Unit definition types.
- Loaders for JSON or other content formats.
- Static content validation and transformation.
- Naval platform/stores/weapon-system definitions and ground-aware type/capability metadata.

## Prohibited

- Simulation step, mission episode, reward, or termination logic.
- Python binding.
- Training configuration governance.
- Direct management of ECS world lifecycle.
- Runtime behavior for ground movement, sensing, terrain control, fires, or damage.

## Dependency Direction

`core/engine` and `models/core` may consume `content/`. `content/` does not depend on `core/engine`, `runtime/facade`, or `interfaces/python`.
