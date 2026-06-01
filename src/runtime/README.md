# `src/runtime` Boundary

`runtime/` holds the maintained application-layer C++ runtime contract. It organizes the lower-level owners and APIs from `core/` into interfaces that the frontend, training environment, and binding layer can depend on for the long term.

Current runtime documentation should use a multi-domain/common-first stance:
air execution is the mature path, naval tasking/engagement evidence is exposed
through maintained contracts and facade packets, and ground is setup/evidence
aware only. Do not describe a full ground runtime here until the lower-level
owner and schema exist.

## Allowed

- Stable request/result types.
- Facade, capability query, and batch runtime operation entry points.
- Combined calls to `core/engine` and `core/mission`.
- Common command/tasking contracts, air/naval maintained slices, ground-bootstrap setup evidence, and engagement evidence exports.

## Forbidden

- ECS system implementation.
- Python/nanobind bindings.
- Training scripts, scene loading scripts, or CLI.
- GPU exact-step semantic replacement.
- Ground movement, sensing, fires, damage, or full ground-domain runtime behavior.

## Subdirectory Conventions

- `contracts/`: Stable DTOs shared by facade, engine, and binding; must not contain runtime owner or engine headers.
- `facade/`: Current maintained typed runtime facade.

## Current Entry Points for Reading

- [contracts/README.md](contracts/README.md)
- [facade/README.md](facade/README.md)

## Current File Locations

- `contracts/`
  - `world_batch_contracts.h`, `engagement_contracts.h`, `platform_capability_contracts.h`
- `facade/`
  - `runtime_facade.h`, `runtime_facade.cpp`, `runtime_facade_types.h`

## Migration Notes

New mainline capabilities should first take the form of a facade request/result, then be bound by Python or other interface layers. Do not let external callers continue to expand their direct dependency on `WorldBatchRuntime` or `SimulationKernel`.
