# `src/` Layer Boundaries

Status: `2026-06-01` multi-domain layering guardrails.
This document defines the responsibilities of directories under `src/` and the permitted dependency directions. It does not describe a one-off relocation target; it sets boundaries for future splits, renames, and new code.

## Current Domain Posture

The maintained `src/` surface is now multi-domain. Air/execution remains the
most mature path, while common DTO/contracts are expected to carry data shared
by air, naval, and early ground-aware setup flows.

- Air: mature command, tasking, mission/episode, physics, observation, and RL-facing execution paths.
- Naval: maintained platform components, command/tasking owner slices, ship/submarine/embarked-air token runtime, and tasking/engagement evidence surfaces are present. This is not a claim that a complete naval mission runtime exists.
- Ground: early bootstrap only. `UnitType::Ground` and typed-platform capability evidence exist, and shared terrain assignment plus aircraft/terrain ground-contact primitives are available. These are not a land-domain terrain or movement runtime; ground movement, sensing, terrain ownership, fires, damage, and full ground runtime remain held.

## Dependency Direction

The mainline dependency direction should remain:

```text
interfaces/python
  -> runtime/facade
    -> core/engine and core/mission
      -> systems
        -> models / components / content

gpu
  -> core/runtime data packets or systems-visible packets
  -> no ownership of canonical world-step truth
```

Lower layers may define data, models, and system logic. Upper layers own composition, batch execution, facades, and language bindings. Any reverse dependency must first be recorded in a freeze plan.

## Directory Responsibilities

- `components/`: ECS components and stable DTO-like data structures, including the common command/tasking foundation, air/naval slices, and ground-bootstrap-aware setup boundaries.
- `systems/`: Flecs system registration and per-tick mutation logic, including air/physics systems, naval token runtime, and ground-contact primitives.
- `models/`: replaceable domain model implementations and unit-factory capability evidence.
- `content/`: content schemas, unit definitions, and loaders for air, naval, and early ground-aware setup data.
- `core/`: C++ runtime orchestration, the single-world kernel, batch runtime, and mission/episode runtime.
- `runtime/`: the maintained application-layer C++ runtime contract, especially the facade and shared DTO contracts.
- `interfaces/`: language bindings and external interface adapters.
- `gpu/`: GPU helpers, packet runtime, and explicit experimental probes.
- `tools/`: development-time and experimental tools; they do not enter the mainline runtime contract.

## Recommended Reading

- [components/README.md](components/README.md)
- [components/domains/README.md](components/domains/README.md)
- [components/command/README.md](components/command/README.md)
- [components/command/common/README.md](components/command/common/README.md)
- [components/domains/air/command/README.md](components/domains/air/command/README.md)
- [components/domains/naval/command/README.md](components/domains/naval/command/README.md)
- [components/domains/naval/platform/README.md](components/domains/naval/platform/README.md)
- [components/tasking/README.md](components/tasking/README.md)
- [components/tasking/common/README.md](components/tasking/common/README.md)
- [components/domains/air/tasking/README.md](components/domains/air/tasking/README.md)
- [components/domains/naval/tasking/README.md](components/domains/naval/tasking/README.md)
- [content/README.md](content/README.md)
- [core/README.md](core/README.md)
- [core/engine/README.md](core/engine/README.md)
- [core/mission/README.md](core/mission/README.md)
- [core/mission/runtime/README.md](core/mission/runtime/README.md)
- [core/mission/episode/README.md](core/mission/episode/README.md)
- [core/mission/episode/detail/README.md](core/mission/episode/detail/README.md)
- [runtime/README.md](runtime/README.md)
- [runtime/contracts/README.md](runtime/contracts/README.md)
- [runtime/facade/README.md](runtime/facade/README.md)
- [models/README.md](models/README.md)
- [models/domains/README.md](models/domains/README.md)
- [models/core/README.md](models/core/README.md)
- [models/systems/README.md](models/systems/README.md)
- [systems/README.md](systems/README.md)
- [systems/domains/README.md](systems/domains/README.md)
- [systems/domains/air/README.md](systems/domains/air/README.md)
- [systems/domains/naval/README.md](systems/domains/naval/README.md)
- [interfaces/README.md](interfaces/README.md)
- [interfaces/python/README.md](interfaces/python/README.md)
- [gpu/README.md](gpu/README.md)

## CMake Source Groups

We still keep a single `ef_core` target, but the source files in `CMakeLists.txt` are already grouped along future target boundaries:

- `EF_CORE_ENGINE_SOURCES`
- `EF_CORE_GEOMETRY_SOURCES`
- `EF_CORE_MISSION_RUNTIME_SOURCES`
- `EF_CORE_MISSION_EPISODE_SOURCES`
- `EF_CORE_MISSION_EPISODE_DETAIL_SOURCES`
- `EF_CORE_MISSION_SOURCES`
- `EF_RUNTIME_FACADE_SOURCES`
- `EF_MODEL_DEFAULT_SOURCES`
- `EF_CONTENT_SOURCES`
- `EF_PYTHON_BINDING_SOURCES`
- `EF_GPU_MAINTAINED_HELPER_SOURCES`
- `EF_GPU_EXPERIMENT_SOURCES`

New source files should first be placed into an explicit source group. Do not append `src/...` files directly to `add_library(ef_core)` or `nanobind_add_module(ef_py)`.

## Prohibitions

- Do not stuff command, tasking, mission, runtime, or binding logic into an existing broad directory just because the include path is convenient.
- Do not implement domain logic in `interfaces/`; put it in `core/` or `runtime/facade` first.
- Do not let `gpu/` become an alternative implementation of the CPU truth path unless you also create a separate freeze document for an exact backend.
- Do not add a top-level directory without a README, or a new cross-layer aggregation directory.

## Migration Principles

- Add README files and compatibility umbrella headers before moving includes.
- Keep the public API and Python-exposed names stable before splitting implementation files.
- Narrow oversized files first, then consider splitting CMake targets.
- When an old path enters a compatibility period, document the target path in the README or in header comments.
