# TM04 SimulationKernel Decomposition Acceptance Gate

Status: `2026-06-01` active acceptance gate; TM04 is not yet accepted.

Parent: [TM04 SimulationKernel Decomposition](README.md).

## Accepted Scope Target

TM04 can accept only the bounded `SimulationKernel` decomposition slice covering
engagement-event ownership, weapon-release service ownership, DTO-shaped effects
recording, focused damage bridge decisions, and synchronized validation records.

## Current Acceptance State

| Gate | State | Evidence | Required before acceptance |
| --- | --- | --- | --- |
| Public service inheritance removed from `SimulationKernel` | pass | [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h) | Keep structural guards green. |
| Engagement event store extracted | pass | [simulation_kernel_engagement_event_store.cpp](../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp) | Keep event ownership out of kernel implementation files. |
| Weapon release service is independent | open | [simulation_kernel_services.cpp](../../../../src/core/engine/simulation_kernel_services.cpp) still forwards through `SimulationKernel&`. | Complete `TM04-C`. |
| Effects damage recorder is DTO-shaped | partial | [engagement_event_recorder.h](../../../../src/core/interfaces/engagement_event_recorder.h) contains both DTO and legacy long-argument overloads. | Complete `TM04-D`. |
| Naval/damage coupling is bounded | open | To be checked during `TM04-C` / `TM04-E`. | Add a narrow bridge or record a named blocker. |
| Validation matrix is current | partial | Focused object and runtime checks passed during the current work stream; full build is held by unrelated effects-model dirty work. | Run `TM04-F` commands and record exact outcomes. |
| Parent indexes synchronized | pass | [../README.md](../README.md) and [../README.zh.md](../README.zh.md) link the TM04 entry, task clusters, status, dispatch queue, and acceptance gate. | Re-sync after final state changes. |

## Required Validation Evidence

```bash
git diff --check
ninja -C build CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_engagement_event_store.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_weapon_api.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_systems.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_observation_api.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_damage_debug_api.cpp.o
python -m pytest -q tests/architecture/test_wp22_structural_guardrails.py::test_wp22_pilot_weapon_release_moves_to_named_helper_and_simulation_kernel_systems_stays_inline_free
python -m pytest -q tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_launch_adapter_static_shape.py tests/runtime/engagement/test_munition_damage_adapter.py tests/runtime/engagement/test_air_launch_adapter.py tests/runtime/engagement/test_naval_launch_adapter.py tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
cmake --build build --target ef_py -j2
```

The final build command may be recorded as held only if the unrelated
`default_effects_model.cpp` / warhead detail blocker remains source-backed and
outside TM04.

## Forbidden Acceptance Claims

- Do not mark TM04 accepted for full `SimulationKernel` decomposition while
  `SimulationKernelWeaponReleaseService` still forwards the core release flow
  through `SimulationKernel&`.
- Do not count docs-only setup as runtime validation.
- Do not claim P7 launch/fire-control closure, damage-model maturity, raw-runtime
  retirement, backend support, or facade maturity.

## Closeout Requirement

Before TM04 can move to `accepted` or `closed`, this file must be updated with
the final command outcomes, residual map, forbidden-claim check, and parent
index synchronization state.
