# TM04 SimulationKernel Decomposition

Status: `2026-06-02` accepted bounded decomposition lane for the
`SimulationKernel` god-class cleanup slice.

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; high-churn implementation slice
  summarized in [../README.zh.md](../../README.zh.md)

Related authority:

- Parent task domain: [Simulation Architecture](../../README.md)
- Subproject standard:
  [subproject_creation_standard.md](../../../../agent/rules/subproject_creation_standard.md)
- Subagent governance:
  [Subagent Usage Policy](../../../../standards/governance/subagent_usage_policy.md)
- Assessment trigger:
  [Echelon Forge comprehensive assessment, 2026-06-01](../../../../evaluation/echelon_forge_comprehensive_assessment_20260601.zh.md)
- Predecessor lane:
  [TM03 Launch Bridge Boundary](../tm03_launch_bridge_boundary/README.md)

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
| Kernel public inheritance | pass | [simulation_kernel.h](../../../../../src/core/engine/simulation_kernel.h) owns service/store pointers rather than publicly inheriting the release/event recorder interfaces. | This proves ownership separation at the header boundary, not full god-class elimination. |
| Engagement event store | pass | [simulation_kernel_engagement_event_store.h](../../../../../src/core/engine/simulation_kernel_engagement_event_store.h) and [simulation_kernel_engagement_event_store.cpp](../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp) own launch/effects event buffers, generated IDs, damage snapshots, sorting, reset, and clear behavior. | TM05 later removed the private legacy-shaped store helper; current store internals are DTO-shaped. |
| Engagement DTO boundary | pass | [engagement_event_recorder.h](../../../../../src/core/interfaces/engagement_event_recorder.h), [engagement_effects_event_builder.h](../../../../../src/core/interfaces/engagement_effects_event_builder.h), [damage_system.h](../../../../../src/systems/combat/damage_system.h), and [simulation_kernel_damage_debug_api.cpp](../../../../../src/core/engine/simulation_kernel_damage_debug_api.cpp) use `EngagementEffectsDamageEventRecord` for effects damage recording. | The public recorder interface no longer exposes the legacy long-argument overload. |
| Release service | pass | [simulation_kernel_weapon_release_service.cpp](../../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp) owns release decisions and release-side mutation behind explicit dependencies. | Kernel public weapon APIs remain compatibility wrappers. |
| Damage bridge | pass / bounded | [weapon_release_damage_bridge.h](../../../../../src/core/interfaces/weapon_release_damage_bridge.h) names the release-to-damage dependency; [simulation_kernel.cpp](../../../../../src/core/engine/simulation_kernel.cpp) provides the compatibility adapter to existing debug damage behavior. | This does not redesign the broader damage model. |
| Runtime validation | pass | `git diff --check`, `cmake --build build-local-win --target ef_py -j2`, focused structural guards, and focused engagement/launch runtime tests passed on `2026-06-02`. | The runtime suite reported `27 passed, 2 skipped`; skips are existing test conditions. |

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
| `P1 Event Store` | Keep engagement event state outside `SimulationKernel`. | Event-store extraction exists. | Store owns event buffers and focused guards prevent direct implementation drift back into damage API. | pass |
| `P2 Release Service` | Replace the `SimulationKernel&` release adapter with a real service. | `IWeaponReleaseService` seam exists. | Service depends on explicit world/factory/recorder interfaces and no longer forwards through `SimulationKernel` for the core release flow. | pass |
| `P3 Effects DTO` | Collapse effects recording onto DTO-shaped calls. | `EngagementEffectsDamageEventRecord` exists. | Primary call sites use the DTO path; the post-TM04 private store helper residual was closed by TM05. | pass |
| `P4 Damage Bridge` | Isolate release paths from direct kernel damage/debug behavior. | Release-service migration exposes remaining damage coupling. | A narrow damage bridge names the remaining compatibility path. | pass |
| `P5 Validation` | Rebuild and test maintained behavior. | Implementation clusters complete. | Focused architecture, engagement, air, naval, and `ef_py` build validation pass. | pass |
| `P6 Closure` | Publish acceptance or blocked closeout. | Validation evidence is current. | Acceptance record and parent index reflect accepted state without overclaim. | pass |

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
  [test_wp22_structural_guardrails.py](../../../../../tests/architecture/test_wp22_structural_guardrails.py).
- Engagement runtime shape tests under
  [tests/runtime/engagement](../../../../../tests/runtime/engagement).
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

- Accepted: TM04's bounded engagement/release/effects decomposition slice is
  complete.
- Closed by TM05: the post-TM04 private legacy-shaped store helper behind the
  DTO public path.
- Held: full P7 fire-control redesign, public raw-runtime retirement, and broad
  damage-model changes.

## Archive

Archive records live under [archive/](archive/README.md). Archived files are
historical provenance only; the current authority for TM04 starts from this
README and the dated current-status/task-cluster documents above.
