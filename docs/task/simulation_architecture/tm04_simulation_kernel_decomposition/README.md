# TM04 SimulationKernel Decomposition

Status: `2026-06-01` active bounded decomposition lane for the
`SimulationKernel` god-class cleanup.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; high-churn implementation slice
  summarized in [../README.zh.md](../README.zh.md)

Related authority:

- Parent task domain: [Simulation Architecture](../README.md)
- Subproject standard:
  [subproject_creation_standard.md](../../../agent/rules/subproject_creation_standard.md)
- Subagent governance:
  [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)
- Assessment trigger:
  [Echelon Forge comprehensive assessment, 2026-06-01](../../../evaluation/echelon_forge_comprehensive_assessment_20260601.zh.md)
- Predecessor lane:
  [TM03 Launch Bridge Boundary](../archive/tm03_launch_bridge_boundary/README.md)

## Purpose

TM04 turns the observed `SimulationKernel` god-class problem into a maintained,
finite execution surface. It continues after TM03's launch-bridge boundary and
the first decomposition pass that moved engagement-event storage out of the
kernel body.

The lane preserves public behavior and API compatibility while moving concrete
ownership out of `SimulationKernel`. It is not a broad P7 launch/fire-control
redesign, a damage-model rewrite, or a general compatibility-retirement wave.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Kernel public inheritance | active / pass | [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h) owns `std::unique_ptr<IWeaponReleaseService>` and `std::unique_ptr<SimulationKernelEngagementEventStore>` rather than publicly inheriting the release/event recorder interfaces. | This proves ownership separation at the header boundary, not that all responsibilities have left the kernel. |
| Engagement event store | active / pass | [simulation_kernel_engagement_event_store.h](../../../../src/core/engine/simulation_kernel_engagement_event_store.h) and [simulation_kernel_engagement_event_store.cpp](../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp) own launch/effects event buffers, generated IDs, damage snapshots, sorting, reset, and clear behavior. | Event recording is extracted, but the damage and weapon APIs still call into the store through the kernel. |
| Engagement DTO boundary | active / partial | [engagement_event_types.h](../../../../src/core/engine/engagement_event_types.h), [engagement_event_recorder.h](../../../../src/core/interfaces/engagement_event_recorder.h), and [engagement_launch_recorder.h](../../../../src/core/interfaces/engagement_launch_recorder.h) split recent-event types, damage event DTOs, and launch recording. | `IEngagementEventRecorder` still keeps the legacy long-argument overload until call sites are fully migrated. |
| Release service | active / residual | [simulation_kernel_services.cpp](../../../../src/core/engine/simulation_kernel_services.cpp) contains `SimulationKernelWeaponReleaseService`, which forwards to `SimulationKernel` public weapon APIs. | This is still a `SimulationKernel&` adapter, not an independent release coordinator with explicit dependencies. |
| Runtime validation | active / partial | Focused object builds and structural/runtime engagement tests have passed in the current work stream. | Full `ef_py` build is held by unrelated dirty work in `src/models/weapons/default_effects_model.cpp` and related warhead detail fields. |

## Scope

In scope:

- Move weapon-release decision, launcher mutation, munition spawn, and launch
  event recording behind a real service with explicit dependencies.
- Complete DTO-based effects damage event recording and keep generated IDs,
  damage snapshots, trace fields, and before/after derivation in the event
  store.
- Introduce narrow bridges, if needed, for damage application paths used by
  naval deck gun and CIWS release.
- Keep architecture guardrails that prevent moved state and service
  responsibilities from flowing back into `SimulationKernel`.
- Maintain focused air/naval launch, engagement capture, and structural tests.

Out of scope:

- No full P7 launch/fire-control redesign.
- No public API removal unless a later accepted task lane explicitly owns it.
- No broad rewrite of `src/models/weapons/default_effects_model.cpp` or the
  damage model.
- No GPU, backend, resident-state, facade, or training capability claim.
- No claim that `SimulationKernel` is fully decomposed until the acceptance gate
  below is satisfied.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze TM04 scope and authority. | Assessment finding, TM03 residual, and current code facts exist. | README, status, cluster, dispatch, acceptance, and parent indexes published. | pass |
| `P1 Event Store` | Keep engagement event state outside `SimulationKernel`. | Event-store extraction exists. | Store owns event buffers and focused guards prevent direct implementation drift back into damage API. | active / partial |
| `P2 Release Service` | Replace the `SimulationKernel&` release adapter with a real service. | `IWeaponReleaseService` seam exists. | Service depends on explicit world/factory/recorder interfaces and no longer forwards through `SimulationKernel` for the core release flow. | planned |
| `P3 Effects DTO` | Collapse effects recording onto DTO-shaped calls. | `EngagementEffectsDamageEventRecord` exists. | Primary call sites use the DTO path and legacy long-argument overload is reduced or retired under compatibility rules. | planned |
| `P4 Damage Bridge` | Isolate release paths from direct kernel damage/debug behavior. | Release-service migration exposes remaining damage coupling. | A narrow damage bridge exists or the remaining call sites are source-backed residuals. | planned |
| `P5 Validation` | Rebuild and test maintained behavior. | Implementation clusters complete. | Focused architecture, engagement, air, and naval tests pass; full build is rerun once unrelated blocker is cleared. | planned |
| `P6 Closure` | Publish acceptance or blocked closeout. | Validation evidence is current. | Acceptance record and parent index reflect pass/blocked state without overclaim. | planned |

## Task Clusters

- Task cluster plan:
  [tm04_simulation_kernel_decomposition_task_clusters_20260601.md](tm04_simulation_kernel_decomposition_task_clusters_20260601.md)
- Current status:
  [tm04_simulation_kernel_decomposition_current_status_20260601.md](tm04_simulation_kernel_decomposition_current_status_20260601.md)
- Dispatch queue:
  [tm04_simulation_kernel_decomposition_dispatch_queue_20260601.md](tm04_simulation_kernel_decomposition_dispatch_queue_20260601.md)
- Round 1 dispatch:
  [tm04_simulation_kernel_decomposition_round1_dispatch_20260601.md](tm04_simulation_kernel_decomposition_round1_dispatch_20260601.md)
- Acceptance gate:
  [tm04_simulation_kernel_decomposition_acceptance_20260601.md](tm04_simulation_kernel_decomposition_acceptance_20260601.md)

## Outputs And Evidence

- C++ service and store boundaries under `src/core/engine/` and
  `src/core/interfaces/`.
- Structural guards in
  [test_wp22_structural_guardrails.py](../../../../tests/architecture/test_wp22_structural_guardrails.py).
- Engagement runtime shape tests under
  [tests/runtime/engagement](../../../../tests/runtime/engagement).
- Air and naval launch runtime tests listed in the task-cluster validation plan.
- This subproject's current-status, dispatch, and acceptance records.

## Acceptance Gate

This subproject can be marked accepted only when:

- `SimulationKernel` no longer owns the core release decision, launcher mutation,
  munition spawn, launch-event creation, or engagement-event buffering behavior
  directly.
- Any remaining `SimulationKernel` methods in the release path are thin public
  compatibility wrappers with source-backed justification.
- Effects damage recording has a maintained DTO path and either retires or
  explicitly contains the legacy long-argument recorder overload.
- Focused architecture, engagement, air-launch, naval-launch, and build
  validation pass, or any failed command is recorded as an unrelated external
  blocker.
- Parent indexes and archive/current-status boundaries are synchronized.

## Residuals And Next Steps

- Immediate: migrate `SimulationKernelWeaponReleaseService` from a forwarding
  adapter into an explicit release service.
- Immediate: finish DTO call-site migration for effects damage event recording.
- Follow-on: decide whether naval release needs an `IWeaponDamageApplier` or
  equivalent damage bridge.
- Held: full P7 fire-control redesign, public raw-runtime retirement, and broad
  damage-model changes.

## Archive

Archive records live under [archive/](archive/README.md). Archived files are
historical provenance only; the current authority for TM04 starts from this
README and the dated current-status/task-cluster documents above.
