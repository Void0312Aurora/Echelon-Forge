# TM04 SimulationKernel Decomposition Current Status

Status: `2026-06-02` accepted current-status checkpoint for
[TM04 SimulationKernel Decomposition](README.md).

## Changes Since Previous Checkpoint

There is no earlier TM04 checkpoint. This record starts TM04 after the first
SimulationKernel decomposition pass:

- `SimulationKernel` no longer publicly inherits release/event-recorder service
  interfaces.
- Engagement event storage and export behavior moved into
  `SimulationKernelEngagementEventStore`.
- Recent engagement event types and launch-recorder interfaces moved out of the
  kernel header.
- `EngagementEffectsDamageEventRecord` exists, but the legacy long-argument
  recorder overload still remains.
- `SimulationKernelWeaponReleaseService` moved from a `SimulationKernel&`
  forwarding adapter into a concrete release service with explicit world,
  factory, tuning, launch-recorder, damage-recorder, and proximity-damage
  callback dependencies.
- First-round dispatch is closed: `TM04-C1` passed implementation validation,
  while `TM04-D1` and `TM04-E1` passed read-only diagnostics for DTO migration
  and naval damage-bridge boundaries.
- Continuation implementation completed `TM04-D` and `TM04-E`: primary effects
  damage call sites now build `EngagementEffectsDamageEventRecord`, the public
  recorder interface no longer exposes the long-argument overload, and release
  damage coupling is named through `IWeaponReleaseDamageBridge`.

## Maturity Matrix

| Surface | State | Evidence | Notes |
| --- | --- | --- | --- |
| Kernel header boundary | pass | [simulation_kernel.h](../../../../../src/core/engine/simulation_kernel.h) | The header owns service pointers rather than public service inheritance. |
| Engagement event store | pass | [simulation_kernel_engagement_event_store.cpp](../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp) | Store owns event state/export behavior; TM05 removed the private legacy-shaped helper behind the DTO public path. |
| Engagement DTO split | pass | [engagement_event_recorder.h](../../../../../src/core/interfaces/engagement_event_recorder.h) | Public recorder surface exposes `EngagementEffectsDamageEventRecord` only. |
| Weapon release service | pass | [simulation_kernel_weapon_release_service.cpp](../../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp) | Kernel public weapon APIs are compatibility wrappers; core release flow no longer forwards through `SimulationKernel&`. |
| Effects DTO migration | pass | [engagement_effects_event_builder.h](../../../../../src/core/interfaces/engagement_effects_event_builder.h), [damage_system.h](../../../../../src/systems/combat/damage_system.h), [simulation_kernel_damage_debug_api.cpp](../../../../../src/core/engine/simulation_kernel_damage_debug_api.cpp) | Primary effects damage call sites construct DTO records before recording. |
| Naval damage bridge | pass / bounded | [weapon_release_damage_bridge.h](../../../../../src/core/interfaces/weapon_release_damage_bridge.h), [simulation_kernel_weapon_release_service.cpp](../../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp) | Non-CIWS naval damage uses a named bridge interface to the existing compatibility damage path. |
| Full build validation | pass | `cmake --build build-local-win --target ef_py -j2` | Passed locally during final acceptance. |

## Residual Register

| Residual | Owner | Required next move | Validation |
| --- | --- | --- | --- |
| Store still contained a private legacy-shaped helper to append DTO fields at TM04 acceptance. | closed by TM05 | TM05 inlined the append path around `EngagementEffectsDamageEventRecord`. | Current focused tests and `ef_py` build passed. |
| Broader P7 launch/fire-control and damage-model redesign remains out of scope. | later accepted lane | Open a separate task before changing those semantics. | Not part of TM04 validation. |

## Recommended Next Action Order

1. Keep TM04 closed as an accepted bounded decomposition slice.
2. Use a new task lane for any direct-store helper cleanup, P7 launch/fire-control
   redesign, raw-runtime retirement, or broad damage-model changes.

## Explicitly Refused Overclaims

- TM04 does not prove full `SimulationKernel` decomposition.
- TM04 does not close P7 launch/fire-control architecture.
- TM04 does not retire public raw-runtime or compatibility APIs.
- TM04 does not resolve unrelated `default_effects_model.cpp` dirty-work
  failures.
