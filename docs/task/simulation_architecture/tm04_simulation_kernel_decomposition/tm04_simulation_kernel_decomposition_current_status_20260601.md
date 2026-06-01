# TM04 SimulationKernel Decomposition Current Status

Status: `2026-06-01` active current-status checkpoint for
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

## Maturity Matrix

| Surface | State | Evidence | Notes |
| --- | --- | --- | --- |
| Kernel header boundary | active / pass | [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h) | The header owns service pointers rather than public service inheritance. |
| Engagement event store | active / pass | [simulation_kernel_engagement_event_store.cpp](../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp) | Store owns event state and export behavior. |
| Engagement DTO split | active / partial | [engagement_event_recorder.h](../../../../src/core/interfaces/engagement_event_recorder.h) | DTO path exists; legacy overload remains. |
| Weapon release service | active / pass | [simulation_kernel_weapon_release_service.cpp](../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp) | Kernel public weapon APIs are compatibility wrappers; core release flow no longer forwards through `SimulationKernel&`. |
| Effects DTO migration | active / partial | [engagement_event_recorder.h](../../../../src/core/interfaces/engagement_event_recorder.h) | Diagnostics mapped remaining legacy overload callers in `damage_system.h` and debug damage paths; implementation is not yet open. |
| Naval damage bridge | active / partial | [simulation_kernel_weapon_release_service.cpp](../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp) | Non-CIWS naval damage now uses an explicit injected proximity-hit callback; a named bridge interface remains a residual. |
| Full build validation | pass | `cmake --build build --target ef_py -j2` | Passed locally during Round 1 acceptance. |

## Residual Register

| Residual | Owner | Required next move | Validation |
| --- | --- | --- | --- |
| Effects damage recorder still exposes a long-argument overload. | `TM04-D` | Complete DTO call-site migration for `damage_system.h` and debug damage paths, or explicitly contain the legacy overload. | Engagement capture and munition damage adapter tests. |
| Naval release still uses an injected proximity-hit callback for non-CIWS damage. | `TM04-E` | Promote or reject a narrow `IWeaponReleaseDamageBridge`-style interface. | Naval launch adapter, CIWS mission-command, and direct-fire event-linkage tests. |
| Full `ef_py` build passed but broad structural guard suite still has unrelated A2/default-effects dirty-work risk. | Integration owner | Keep TM04 validation focused unless a separate A2/default-effects lane is in scope. | Focused TM04 guards plus `cmake --build build --target ef_py -j2`. |

## Recommended Next Action Order

1. Schedule `TM04-D` implementation after the release-service commit lands,
   including `damage_system.h` and debug damage DTO call sites.
2. Schedule `TM04-E` implementation only as a narrow damage bridge decision;
   non-CIWS naval damage is the remaining source-backed coupling.
3. Run `TM04-F` integration validation after the DTO/bridge residuals are
   implemented or explicitly blocked.

## Explicitly Refused Overclaims

- TM04 does not prove full `SimulationKernel` decomposition yet.
- TM04 does not close P7 launch/fire-control architecture.
- TM04 does not retire public raw-runtime or compatibility APIs.
- TM04 does not resolve unrelated `default_effects_model.cpp` dirty-work
  failures.
