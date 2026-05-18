# `src/` Layer Boundaries

Status: `2026-05-10` layering refactor guardrails.  
This document defines the responsibilities of directories under `src/` and the permitted dependency directions. It does not describe a one-off relocation target; it sets boundaries for future splits, renames, and new code.

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

- `components/`: ECS components and stable DTO-like data structures.
- `systems/`: Flecs system registration and per-tick mutation logic.
- `models/`: replaceable domain model implementations.
- `content/`: content schemas, unit definitions, and loaders.
- `core/`: C++ runtime orchestration, the single-world kernel, batch runtime, and mission/episode runtime.
- `runtime/`: the maintained application-layer C++ runtime contract, especially the facade.
- `interfaces/`: language bindings and external interface adapters.
- `gpu/`: GPU helpers, packet runtime, and explicit experimental probes.
- `tools/`: development-time and experimental tools; they do not enter the mainline runtime contract.

## Recommended Reading

- [components/README.md](components/README.md)
- [components/command/README.md](components/command/README.md)
- [components/command/common/README.md](components/command/common/README.md)
- [components/command/air/README.md](components/command/air/README.md)
- [components/tasking/README.md](components/tasking/README.md)
- [components/tasking/common/README.md](components/tasking/common/README.md)
- [components/tasking/air/README.md](components/tasking/air/README.md)
- [components/tasking/naval/README.md](components/tasking/naval/README.md)
- [core/README.md](core/README.md)
- [core/engine/README.md](core/engine/README.md)
- [core/mission/README.md](core/mission/README.md)
- [core/mission/runtime/README.md](core/mission/runtime/README.md)
- [core/mission/episode/README.md](core/mission/episode/README.md)
- [core/mission/episode/detail/README.md](core/mission/episode/detail/README.md)
- [runtime/README.md](runtime/README.md)
- [runtime/contracts/README.md](runtime/contracts/README.md)
- [runtime/facade/README.md](runtime/facade/README.md)
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
