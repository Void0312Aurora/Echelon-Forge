# WP22 Remaining Task Clusters

Status: `2026-05-23` re-baseline after the owner rejected the prior WP21/WP22
closure posture. This document replaces ad-hoc "next wave" dispatching with a
finite residual cluster plan. `R1-B` default-factory projection deletion remains
blocked after `R1-A`, so deletion stays deferred until the residual R1 sub-slices
below complete. `R3` must still be re-scoped before any more implementation or
closure dispatch. This document does not declare WP22 complete, and it does not
make `WP22-F` eligible.

Inputs:

- [WP22 main plan](legacy_compatibility_retirement_wp22_20260522.md)
- [WP22 fact ledger](wp22_retirement_fact_ledger_cluster_20260522.md)
- [WP22 dispatch queue](wp22_subagent_dispatch_queue_20260522.md)
- [Architecture refactoring audit](../../review/architecture_refactoring_audit_20260522.md)

## Current Blocking Facts

| Fact | Current state | Consequence |
|------|---------------|-------------|
| `Epicurus command-link packet` | `partial`; current workspace still needs repair/verification. Architecture guard previously failed on `deliver_pending_command(cmd[i], pending[i], current_time);`, and runtime link QoS had a stale or behavior-changing `current_control_state_active` expectation. | No closure or broader command projection deletion can proceed before this stabilization gate returns a complete packet. |
| `MissionCommandControlState` | Owns heading/speed/altitude target and lagged mirrors, but not throttle/brake/nose-wheel or full action semantics. | `MovementCommand`, `LaggedCommand`, `ActionCommand`, and pending action transport cannot be deleted yet. |
| `default_factory_legacy_spawn_compat.h` | Still projects behavior-bearing `MovementCommand` / `LaggedCommand` mirrors. | `R1-B` default-factory projection deletion remains blocked after `R1-A`; repeated deletion attempts are a planning smell, not a new dispatch target. |
| Aggregate DTO shells | `MissionCommand`, `TaskOrder`, `LeaderIntent`, and `PilotReport` are guarded as compatibility transport shells, not retired. | `S-001/S-002/S-003` need maintained-consumer migration or stronger owner-slice boundaries. |
| `Exact-stage inventory` | `src/core/engine/exact_stage_inventory.cpp` still declares the exact-stage contracts for `CommandLinkMovement`, `CommandLinkAction`, `CommandLinkMission`, `ActionMapping`, `CommandLag`, `FlightControl`, `ComputeForces`, `GroundContact`, `UpdateInstruments`, and `FuelConsumption`. | Exact-stage contract demotion/alignment must complete before default-factory projection deletion is revisited. |
| `Diagnostics/debug movement mirror bindings` | `src/interfaces/python/bindings_core.cpp` still exposes quarantined debug movement mirror helpers, including `debug_get_pending_movement_command`, `debug_get_pending_action_command`, `debug_get_legacy_movement_command`, and `debug_set_legacy_movement_command`. | Debug/diagnostics mirror retirement remains part of the residual R1 cluster. |
| Public escape hatches | `RuntimeFacade::runtime()`, `WorldBatchRuntime::world()`, public `batch_runtime` / `vec_env.batch_runtime`, diagnostics bindings, explicit legacy mode, and fallback cadence remain compatibility/diagnostics surfaces until replacement APIs exist. | `WP22-C/E/F` cannot close until maintained callers are guarded or migrated and public compatibility use is explicit. |
| Structural debt | `runtime_facade.cpp`, `default_unit_factory.h`, `bindings_core.cpp`, and `exact_stage_inventory.cpp` remain large mixed surfaces. | Structural work is still needed, but it must not be mistaken for legacy retirement by itself. |

## Finite Cluster Plan

| Cluster | Status | Scope | Exit gate |
|---------|--------|-------|-----------|
| `WP22-R0 Current Partial Stabilization` | ready, must run first | Complete the command-link pending transport narrowing left by Epicurus. Keep movement delivery typed-state-owned and action pending transport quarantined. | Focused runtime link/mission tests pass, architecture command guards pass, `ef_py` builds, `git diff --check` clean. |
| `WP22-R1 Finite Residual Cluster` | queued after R0; `R1-B` remains blocked after `R1-A` | Finish the only remaining R1 work as a finite cluster: pending transport shell narrowing, debug/diagnostics mirror retirement, and exact-stage contract demotion/alignment. Keep default-factory projection deletion deferred until all three sub-slices return complete packets. | `R1-B` default-factory projection deletion stays deferred; repeated deletion attempts are a planning smell, not a new dispatch target. |
| `WP22-R2 DTO Domain-Shell Retirement` | parallel-ready; re-scope required before more ad-hoc implementation | Move maintained consumers away from aggregate command/tasking shells toward owner-slice or domain-specific DTOs. Keep transport-shell compatibility explicit. | DTO-shell guard proves maintained logic consumes owner slices or explicit projections, not flat aggregate truth. |
| `WP22-R3 Adapter Raw-World Replacement Re-scope` | must re-scope before more implementation or closure dispatch | Replace maintained adapter raw-world methods with facade-owned request/result APIs before any public escape-hatch deletion. Public runtime/world/batch access and diagnostics bindings stay compatibility-only until those APIs exist. | The three finite sub-slices below each return a complete packet; only then can public escape-hatch deletion be considered. |
| `WP22-R4 Structural Decomposition And Acceptance Prep` | dependency-gated | Split remaining large surfaces only after R0-R3 ownership is stable; then run closure audit. | No unowned default legacy path remains; closure audit and acceptance can be drafted only here. |

Hard cap:

- R0 may take one repair round.
- R1 is capped at the three named sub-slices below; do not invent additional R1 dispatches.
- R3 must be re-scoped into the finite replacement cluster below before any additional implementation or closure dispatch.
- R2 has reached its implementation cap; do not dispatch more ad-hoc implementation without a formal re-scope.
- R4/WP22-F is serial and not dispatchable until R0-R3 return complete packets.

## R1 Residual Sub-slices

| Sub-slice | Scope | Exit gate |
|-----------|-------|-----------|
| `R1-1 Pending transport shell narrowing` | Narrow `PendingMovementCommand` and `PendingActionCommand` so maintained delivery consumes typed payloads and the legacy transport shells stay diagnostics-only or are removed from maintained paths. | Pending movement/action transport no longer acts as maintained command truth. |
| `R1-2 Debug/diagnostics mirror retirement` | Retire or hard-quarantine the debug movement mirror bindings in `bindings_core.cpp`, including legacy movement getters/setters and pending transport debug views. | Diagnostics access is explicit and does not bypass typed state for maintained callers. |
| `R1-3 Exact-stage contract demotion/alignment` | Demote the exact-stage inventory from maintained implementation truth to a guarded contract ledger aligned with typed ownership, bridge compatibility projections, and the remaining optional operation/command-link mirror signatures. | `exact_stage_inventory.cpp` no longer blocks the residual R1 cluster or default-factory projection deletion. |

## R3 Replacement Sub-slices

| Sub-slice | Scope | Exit gate |
|-----------|-------|-----------|
| `R3-1 Scenario-loader construction` | Move scenario-loader construction off raw-world calls and onto facade-owned request/result inputs. | Scenario-loader construction no longer requires new maintained raw-world access. |
| `R3-2 World layout/time-step access` | Expose world layout and time-step reads through facade-owned request/result APIs instead of raw adapter methods. | Layout/time-step data is read through the replacement API, not through new maintained raw-world call sites. |
| `R3-3 Visual compatibility export/candidate helpers` | Centralize visual compatibility export and candidate helper assembly behind the facade-owned path. | Visual helper assembly no longer depends on new maintained raw-world access. |

## First Dispatch Set

| Dispatch | Cluster | Model / reasoning | Write scope | Why parallel-safe |
|----------|---------|-------------------|-------------|-------------------|
| `WP22-R0-A command-link stabilization` | R0 | `gpt-5.4`, xhigh | `src/components/command/command_link.h`, `src/systems/systems/command_link_system.h`, `src/core/engine/simulation_kernel_command_api.cpp`, `tests/runtime/link/test_command_link_qos.py`, `tests/architecture/test_wp9_guard_enforcement.py` | Owns the current partial packet and must not touch DTO, runtime facade, binding, or factory files. |
| `WP22-R2-A DTO owner-slice migration` | R2 | `gpt-5.4`, high | command/tasking DTO headers and `tests/architecture/test_wp22_dto_domain_shell_guard.py`; no runtime facade or command-link edits | Independent from R0 command-link stabilization. |
| `WP22-R3-A adapter raw-world replacement re-scope` | R3 | `gpt-5.4-mini`, xhigh | docs and queue sync only; no code changes | Re-align the finite replacement cluster, keep public escape hatches compatibility-only, and preserve bilingual status before any future implementation dispatch. |

## Deferred Dispatches

| Dispatch | Dependency | Reason |
|----------|------------|--------|
| `WP22-R1-B default-factory projection deletion` | `R1-1`, `R1-2`, and `R1-3` complete | `R1-B` remains blocked after `R1-A`; repeated deletion attempts are a planning smell, not evidence of readiness. |
| `WP22-R4-A closure preflight` | R0-R3 complete | Running closure now would only reproduce "not eligible" evidence. |

## Worker Packet Requirements

Each worker must return:

- `status`: `pass`, `partial`, `blocked`, or `failed`.
- `touched files`: exact file list.
- `commands/outcomes`: every command run and result.
- `remaining paths`: any legacy, compatibility, diagnostics, or transport shell left live.
- `integration notes`: behavior risks and files the main thread must verify.

Rules:

- Workers are not alone in the codebase and must not revert unrelated edits.
- Closed, timed-out, or interrupted threads are transport events only, not evidence.
- `partial` never unlocks downstream closure.
- No worker may claim WP22 complete, `R1-B` unblocked, or `WP22-F` eligible.
