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
- `SimulationKernelWeaponReleaseService` exists as a forwarding adapter and is
  the next major decomposition target.

## Maturity Matrix

| Surface | State | Evidence | Notes |
| --- | --- | --- | --- |
| Kernel header boundary | active / pass | [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h) | The header owns service pointers rather than public service inheritance. |
| Engagement event store | active / pass | [simulation_kernel_engagement_event_store.cpp](../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp) | Store owns event state and export behavior. |
| Engagement DTO split | active / partial | [engagement_event_recorder.h](../../../../src/core/interfaces/engagement_event_recorder.h) | DTO path exists; legacy overload remains. |
| Weapon release service | active / residual | [simulation_kernel_services.cpp](../../../../src/core/engine/simulation_kernel_services.cpp) | Still forwards through `SimulationKernel&`. |
| Full build validation | held | `cmake --build build --target ef_py -j2` | Held by unrelated dirty `default_effects_model.cpp` / warhead detail fields. |

## Residual Register

| Residual | Owner | Required next move | Validation |
| --- | --- | --- | --- |
| `SimulationKernelWeaponReleaseService` is still a kernel forwarding adapter. | `TM04-C` | Move release decision, launcher mutation, munition spawn, and launch-event recording into a real service with explicit dependencies. | Object builds plus air/naval release runtime tests. |
| Effects damage recorder still exposes a long-argument overload. | `TM04-D` | Complete DTO call-site migration or explicitly contain the legacy overload. | Engagement capture and munition damage adapter tests. |
| Naval release may still need kernel-owned damage/debug behavior. | `TM04-E` | Source-check whether a narrow damage bridge is required after `TM04-C`. | Naval launch adapter and CIWS mission-command tests. |
| Full `ef_py` build is blocked by unrelated dirty effects-model work. | Integration owner | Re-run once blocker is resolved; do not fold the blocker into TM04 unless re-scoped. | `cmake --build build --target ef_py -j2`. |

## Recommended Next Action Order

1. Run `TM04-C` release-service migration with a disjoint write scope.
2. Run `TM04-D` DTO migration only after scheduling ownership of shared weapon
   API call sites.
3. Evaluate `TM04-E` damage bridge from source facts exposed by `TM04-C`.
4. Run `TM04-F` integration validation and publish `TM04-G` closeout.

## Explicitly Refused Overclaims

- TM04 does not prove full `SimulationKernel` decomposition yet.
- TM04 does not close P7 launch/fire-control architecture.
- TM04 does not retire public raw-runtime or compatibility APIs.
- TM04 does not resolve unrelated `default_effects_model.cpp` dirty-work
  failures.
