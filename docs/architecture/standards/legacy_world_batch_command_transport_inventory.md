# Legacy WorldBatch Command Transport Inventory

Language:
- English canonical: `legacy_world_batch_command_transport_inventory.md`
- Chinese companion: [legacy_world_batch_command_transport_inventory.zh.md](legacy_world_batch_command_transport_inventory.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/legacy_world_batch_command_transport_inventory.md`
Owner: `architecture/runtime-contracts`
Last verified: `2026-10-10`

This inventory records the post-maintained-migration decision for the three
raw command writers. The maintained `RuntimeFacade` path uses typed
`*MaintainedAssignment` requests and is the only supported Python execution
path.

| Legacy symbol | Declared/defined in | Supported callers | Decision |
| --- | --- | --- | --- |
| `WorldBatchRuntime::set_mission_commands_batch` | `world_batch_runtime.h/.cpp`, `bindings_runtime_engine.cpp` | None in `src/`, `python/`, or supported tests | Retired |
| `WorldBatchRuntime::set_leader_intents_batch` | `world_batch_runtime.h/.cpp`, `bindings_runtime_engine.cpp` | None in `src/`, `python/`, or supported tests | Retired |
| `WorldBatchRuntime::set_pilot_reports_batch` | `world_batch_runtime.h/.cpp`, `bindings_runtime_engine.cpp` | None in `src/`, `python/`, or supported tests | Retired |

The old `World*Assignment` DTOs remain in the contract headers and tasking
binding because compatibility shells and projection helpers still use their
shape for diagnostics and evidence. They are no longer accepted by a raw
command writer. The maintained batch DTOs and facade methods remain unchanged.

## Packaging boundary

Production `ef_py` is configured with `EF_PRODUCTION_FACADE_ONLY=ON` and omits
`bindings_runtime_engine.cpp`; it therefore never exposes `WorldBatchRuntime`.
The explicit opt-in `ef_py_diagnostics` target may still expose raw runtime
read/query surfaces, but these three retired writer symbols are absent from its
binding as well. Architecture tests retain the negative guard against adding
the old names to the maintained adapter or facade path.

This is a symbol-level retirement only. It does not delete `WorldBatchRuntime`,
the compatibility-shell DTOs, or maintained command projection/replay logic.
