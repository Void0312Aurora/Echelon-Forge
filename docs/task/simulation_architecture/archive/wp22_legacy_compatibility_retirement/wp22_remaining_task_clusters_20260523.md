# WP22 Remaining Task Clusters

Status: frozen / superseded by
[`WP23 Legacy Retirement Recovery And Reset`](../wp23_legacy_retirement_recovery/legacy_retirement_recovery_wp23_20260523.md).
This document is historical evidence only. It must not be used as an active
residual queue or as authorization for another WP22 wave.

Historical pre-freeze status: `2026-05-23` re-baseline after the owner rejected the prior WP21/WP22
closure posture. This document replaces ad-hoc "next wave" dispatching with a
finite residual cluster plan. `R1-B` default-factory projection deletion remains
blocked after `R1-A`, so deletion stays deferred until the residual R1 sub-slices
below complete. `R3` is now limited to the three finite replacement sub-slices
below; no broader adapter raw-world work or escape-hatch deletion is dispatchable
here. This document does not declare WP22 complete, and it does not make
`WP22-F` eligible.

`R2` is now formally re-scoped around the accepted `MissionCommand`
owner-slice migration pass. The remaining R2 work is finite and source-backed:
`TaskOrder`, `LeaderIntent`, `PilotReport`, and the world-batch assignment shell
family. This packet is docs-only; it does not authorize implementation,
`WP22-F`, `R4`, or closure.

Inputs:

- [WP22 main plan](legacy_compatibility_retirement_wp22_20260522.md)
- [WP22 fact ledger](wp22_retirement_fact_ledger_cluster_20260522.md)
- [WP22 dispatch queue](wp22_subagent_dispatch_queue_20260522.md)
- [Architecture refactoring audit](../../../review/architecture_refactoring_audit_20260522.md)

## Current Blocking Facts

| Fact | Current state | Consequence |
|------|---------------|-------------|
| `Command-link pending transport packet` | `scoped pass`; delayed movement delivery is now typed-state-owned and pending action delivery has an explicit typed air-control overlay projection. | This stabilizes R0/R1-1 only. It does not delete pending shells, `ActionCommand`, default-factory projections, or public compatibility escape hatches. |
| `MissionCommandControlState` | Owns heading/speed/altitude target and lagged mirrors, but not throttle/brake/nose-wheel or full action semantics. | `MovementCommand`, `LaggedCommand`, `ActionCommand`, and pending action transport cannot be deleted yet. |
| `default_factory_legacy_spawn_compat.h` | Still projects behavior-bearing `MovementCommand` / `LaggedCommand` mirrors. | `R1-B` default-factory projection deletion remains blocked after `R1-A`; repeated deletion attempts are a planning smell, not a new dispatch target. |
| Aggregate DTO shells | `MissionCommand`, `TaskOrder`, `LeaderIntent`, and `PilotReport` are guarded as compatibility transport shells, not retired. | `S-001/S-002/S-003` need maintained-consumer migration or stronger owner-slice boundaries. |
| `Exact-stage inventory` | `src/core/engine/exact_stage_inventory.cpp` is now a guarded contract ledger rather than a maintained-truth register. | R1-3 is a scoped pass, but ledger demotion does not authorize default-factory projection deletion. |
| `Diagnostics/debug movement mirror bindings` | `src/interfaces/python/bindings_core.cpp` still exposes quarantined debug movement mirror helpers, including `debug_get_pending_movement_command`, `debug_get_pending_action_command`, `debug_get_legacy_movement_command`, and `debug_set_legacy_movement_command`. | R1-2 is accepted only as hard quarantine/narrowing; diagnostics helpers still exist and remain non-maintained surfaces. |
| Public escape hatches | `RuntimeFacade::runtime()`, `WorldBatchRuntime::world()`, public `batch_runtime` / `vec_env.batch_runtime`, diagnostics bindings, explicit legacy mode, and fallback cadence remain compatibility/diagnostics surfaces until replacement APIs exist. | `WP22-C/E/F` cannot close until maintained callers are guarded or migrated; these surfaces stay quarantine-only and are not deletion candidates. |
| Structural debt | `runtime_facade.cpp`, `default_unit_factory.h`, `bindings_core.cpp`, and `exact_stage_inventory.cpp` remain large mixed surfaces. | Structural work is still needed, but it must not be mistaken for legacy retirement by itself. |

## R2 Residual Owner-Slice Targets

MissionCommand owner-slice migration is already accepted and is not reopened
here. The residual R2 list is finite and source-backed; these are the only
next owner-slice targets that should be discussed, and each stays
compatibility-explicit until its guard passes.

| Target | Source-backed owner slices / guards | What remains live | Hard stop |
|--------|-------------------------------------|-------------------|-----------|
| `TaskOrder` | `TaskOrderCore`, `TaskOrderAir`, `TaskOrderNaval`; `src/components/tasking/task_order.h` remains a flat compatibility/transport shell. | Maintained callers can still reach the umbrella shell instead of an owner-slice projection. | Stop as `blocked` if the packet would invent a new DTO shape or widen the shell beyond the existing source slices. |
| `LeaderIntent` | `LeaderIntentCore`, `LeaderIntentAir`, `LeaderIntentNaval`; `src/components/tasking/leader_intent.h` remains a flat compatibility/transport shell. | Maintained callers can still reach the umbrella shell instead of an owner-slice projection. | Stop as `blocked` if any maintained caller still needs flat-shell truth outside explicit compatibility projection. |
| `PilotReport` | `PilotReportCore`, `PilotReportAir`, `PilotReportNaval`; `src/components/tasking/pilot_report.h` remains a flat compatibility/transport shell. | Maintained callers can still reach the umbrella shell instead of an owner-slice projection. | Stop as `blocked` if the packet would move transport responsibility into a new maintained DTO instead of the existing owner slices. |
| World-batch assignment shells | `WorldMissionCommandAssignment`, `WorldTaskOrderAssignment`, `WorldLeaderIntentAssignment`, `WorldPilotReportAssignment`, plus `world_batch_assignment_compatibility_shell(...)`. | The wrappers remain live and transport-only, with `shell_type` markers and guard helpers in source. | Stop as `partial` or `blocked` if the change would make these wrappers first-class maintained truth or drop their explicit transport-only contract. |

Hard-stop conditions:

- Return `blocked` if source still shows flat-shell truth on a maintained path,
  or if the packet would have to invent a new DTO shape or widen a compatibility
  shell beyond the existing source slices.
- Return `partial` if only some maintained consumers can move while the flat
  shell must remain live for the rest, or if the packet can only prove guard
  narrowing instead of retirement.
- Stop immediately if the next step would touch a public escape hatch such as
  `RuntimeFacade::runtime()`, `WorldBatchRuntime::world()`, public
  `batch_runtime` / `vec_env.batch_runtime`, or diagnostics bindings; those
  belong outside R2.
- In every case, do not authorize implementation, `WP22-F`, `R4`, or closure
  from this packet.

## Finite Cluster Plan

| Cluster | Status | Scope | Exit gate |
|---------|--------|-------|-----------|
| `WP22-R0 Current Partial Stabilization` | scoped pass accepted | Complete the command-link pending transport narrowing left by Epicurus. Keep movement delivery typed-state-owned and action pending transport quarantined. | Focused runtime link/mission tests pass, architecture command guards pass, `ef_py` builds, `git diff --check` clean. |
| `WP22-R1 Finite Residual Cluster` | scoped pass for `R1-1`, `R1-2`, and `R1-3`; deletion still blocked | Finish the only remaining R1 work as a finite cluster: pending transport shell narrowing, debug/diagnostics mirror retirement, and exact-stage contract demotion/alignment. Keep default-factory projection deletion deferred until live mirror consumers are proven replaceable. | `R1-B` default-factory projection deletion stays deferred; repeated deletion attempts are a planning smell, not a new dispatch target. |
| `WP22-R2 DTO Domain-Shell Retirement` | scoped `MissionCommand` pass; finite residual list limited to `TaskOrder`, `LeaderIntent`, `PilotReport`, and world-batch assignment shells; docs-only formal re-scope required before more implementation | Move maintained consumers away from aggregate command/tasking shells toward owner-slice or domain-specific DTOs. Keep transport-shell compatibility explicit. | DTO-shell guard proves maintained logic consumes owner slices or explicit projections, not flat aggregate truth. |
| `WP22-R3 Adapter Raw-World Replacement Re-scope` | scoped stable for `R3-1`, `R3-2`, and `R3-3`; no further R3 implementation dispatch | Replace maintained adapter raw-world methods with facade-owned request/result APIs before any public escape-hatch deletion is considered. Public runtime/world/batch access and diagnostics bindings stay compatibility-only until those APIs exist. | R3 no longer has a finite implementation dispatch open, but public escape-hatch deletion stays blocked and is not closure evidence. |
| `WP22-R4 Structural Decomposition And Acceptance Prep` | dependency-gated | Split remaining large surfaces only after R0-R3 ownership is stable; then run closure audit. | No unowned default legacy path remains; closure audit and acceptance can be drafted only here. |

Current `R2` note (`2026-05-23`): the `TaskOrder` shared-core guard slice, the
Python command-chain `LeaderIntent` / `PilotReport` projection slice, and the
Python binding owner-slice exposure slice are accepted only as `partial`
evidence. Peirce moved the Python command-chain snapshot path onto the bound
`LeaderIntent` / `PilotReport` owner-slice helpers, and Nash did the same for
the `TaskOrder` command-chain snapshot by consuming the bound
`task_order_shared_core`, `task_order_air_owner_slice`, and
`task_order_naval_owner_slice` helper views. Feynman removed the `TaskOrder`
Python binding visibility blocker, and Kierkegaard confirmed the remaining R2
path is no longer snapshot visibility but live whole-shell transport through
`WorldTaskOrderAssignment`, `WorldLeaderIntentAssignment`,
`WorldPilotReportAssignment`, vec-env assignment writes, and broader
batch/facade/public binding APIs. Beauvoir's readiness preflight found no stale
docs that authorize closure. Cicero then centralized Python assignment writes
behind named compatibility transport helpers, and Boyle confirmed that existing
`TaskOrderCore` / `TaskOrderAir` / `TaskOrderNaval` owner-slice projections are
not by themselves a replacement public batch write/read contract. Hubble has
now defined the guard-first `TaskOrderMaintainedBatchContract` and
`WorldTaskOrderMaintainedAssignment`; the next R2 serial step is wiring that
maintained contract through runtime/facade/binding/Python write/read APIs while
keeping old shell APIs explicit compatibility-only surfaces. This does not
unblock R4, `WP22-F`, DTO shell retirement, or public escape-hatch deletion.

Hard cap:

- R0 repair is complete; do not redispatch it.
- R1 is capped at the three named scoped-pass sub-slices below; do not invent additional R1 dispatches.
- R3 is limited to the three finite replacement sub-slices below; all three are scoped passes and no further R3 implementation dispatch is allowed here.
- R2 implementation is capped to the source-backed assignment transport and
  batch/facade whole-shell seams listed below; the next serial slice is
  `TaskOrder` maintained runtime/facade/binding API wiring. Do not reopen
  owner-slice binding, command-chain snapshot work, or direct shell deletion
  unless validation regresses.
- R4/WP22-F is serial and not dispatchable while R2 residual owner-slice work,
  public compatibility escape hatches, default-factory projection, and
  structural/binding debt remain open.

## R1 Residual Sub-slices

| Sub-slice | Scope | Exit gate |
|-----------|-------|-----------|
| `R1-1 Pending transport shell narrowing` | `scoped pass`: narrowed `PendingMovementCommand` and `PendingActionCommand` so maintained delayed movement delivery consumes typed payloads and action pending delivery has an explicit typed overlay projection. | Pending movement no longer acts as maintained command truth; action pending shell remains quarantined compatibility transport. |
| `R1-2 Debug/diagnostics mirror retirement` | `scoped pass`: debug movement mirror bindings in `bindings_core.cpp` are hard-quarantined as diagnostics-only or legacy override surfaces, including legacy movement getter/setter and pending transport debug views. | Diagnostics access is explicit and does not bypass typed state for maintained callers. |
| `R1-3 Exact-stage contract demotion/alignment` | `scoped pass`: demoted the exact-stage inventory from maintained implementation truth to a guarded contract ledger aligned with typed ownership, diagnostics shells, bridge compatibility projections, and the remaining optional operation/command-link mirror signatures. | `exact_stage_inventory.cpp` is no longer a maintained-truth register; it stays as guarded contract evidence while `R1-B` remains blocked. |

## R3 Replacement Sub-slices

| Sub-slice | Write scope | Exit gate | Blocked public escape hatch |
|-----------|-------------|-----------|-----------------------------|
| `R3-1 Scenario-loader construction` | `scoped pass`: `python/rl/runtime/world_batch/adapter.py` loader construction path now uses a named runtime-world-layout request/result seam instead of adding maintained raw-world construction call sites. | Scenario-loader construction no longer needs a new maintained raw-world call site. | `RuntimeFacade::runtime()`, `WorldBatchRuntime::world()`, and `vec_env.batch_runtime` remain quarantine-only; no deletion-ready status. |
| `R3-2 World layout/time-step access` | `scoped pass`: `python/rl/runtime/world_batch/adapter.py::world()` now returns a controlled proxy for layout/time-step reads, and `get_time_step()` prefers facade/runtime helper access with adapter-owned fallback before raw-world compatibility. | Layout/time-step data is read through the replacement seam, not through new maintained raw-world call sites. | `WorldBatchRuntime::world()`, explicit `legacy` mode, diagnostics bindings, and raw-world compatibility forwarding remain quarantine-only. |
| `R3-3 Visual compatibility export/candidate helpers` | `scoped pass`: facade-owned visual candidate assembly now routes through named compatibility helpers and GPU wrappers keep facade-owned and compatibility-runtime paths explicit. | Visual helper assembly no longer depends on new maintained raw-world access. | `RuntimeFacade::runtime()`, `WorldBatchRuntime::world()`, `vec_env.batch_runtime`, and diagnostics bindings remain quarantine-only. |

Current `R3` note (`2026-05-23`): `R3-1`, `R3-2`, and `R3-3` are scoped passes. Public `RuntimeFacade::runtime()`, `WorldBatchRuntime::world()`, `vec_env.batch_runtime`, explicit `legacy` mode, diagnostics bindings, and raw-world compatibility forwarding remain quarantine-only blockers, so this is not public escape-hatch deletion readiness or WP22 closure evidence.

## First Dispatch Set

| Dispatch | Cluster | Model / reasoning | Write scope | Why parallel-safe |
|----------|---------|-------------------|-------------|-------------------|
| `WP22-R0-A command-link stabilization` | R0 | `gpt-5.4`, xhigh | `src/components/command/command_link.h`, `src/systems/systems/command_link_system.h`, `src/core/engine/simulation_kernel_command_api.cpp`, `tests/runtime/link/test_command_link_qos.py`, `tests/architecture/test_wp9_guard_enforcement.py` | Owns the current partial packet and must not touch DTO, runtime facade, binding, or factory files. |
| `WP22-R2-A DTO owner-slice re-scope` | R2 | `gpt-5.4-mini`, xhigh | docs and queue sync only; no code changes | Convert the accepted `MissionCommand` pass into the finite residual list for `TaskOrder`, `LeaderIntent`, `PilotReport`, and world-batch assignment shells; keep implementation, `WP22-F`, `R4`, and closure out of scope. |
| `WP22-R2-B Python binding owner-slice exposure` | R2 | `gpt-5.4`, xhigh | `src/interfaces/python/bindings_command.cpp`, focused binding/DTO guard tests, and minimal Python visibility tests | Expose existing `LeaderIntent` / `PilotReport` owner-slice types and projection helpers to Python without inventing new DTO shapes or widening compatibility shells; return `partial` or `blocked` if whole-shell transport is still required. |
| `WP22-R2-C Python command-chain bound owner-slice consumption` | R2 | `gpt-5.4`, xhigh | `python/rl/runtime/world_batch/command_chain_cache.py`, focused world-batch/cooperative command-chain tests, and minimal binding-surface assertions if needed | Replace hand-maintained `LeaderIntent` / `PilotReport` owner-slice snapshots with snapshots taken from the bound owner-slice helper views where feasible; keep assignment wrappers transport-only and return `partial` if whole-shell transport remains live. |
| `WP22-R2-D TaskOrder Python owner-slice exposure` | R2 | `gpt-5.4`, xhigh | `src/interfaces/python/bindings_command.cpp`, binding/DTO guard tests, and minimal TaskOrder command-chain visibility tests | Expose existing `TaskOrderCore` / `TaskOrderAir` / `TaskOrderNaval` owner slices and projection helpers to Python without inventing DTO shapes or widening compatibility shells; return `partial` if whole-shell transport remains live. |
| `WP22-R2-E residual whole-shell fact check` | R2 | `gpt-5.4-mini`, xhigh | read-only source inspection | Produce exact anchors for remaining `TaskOrder`, `LeaderIntent`, `PilotReport`, and assignment-wrapper whole-shell paths after Peirce, separating compatibility-only transport from maintained truth. |
| `WP22-R2-F TaskOrder command-chain bound owner-slice consumption` | R2 | `gpt-5.4`, xhigh | `python/rl/runtime/world_batch/command_chain_cache.py`, focused world-batch/cooperative command-chain tests, and minimal TaskOrder snapshot assertions | Replace the whole-shell `TaskOrder` command-chain snapshot with snapshots from bound `ef_py.task_order_*` owner-slice helper views; keep `WorldTaskOrderAssignment` transport-only and return `partial` while transport wrappers remain live. |
| `WP22-R3-A adapter raw-world replacement re-scope` | R3 | `gpt-5.4-mini`, xhigh | docs and queue sync only; no code changes | Re-align the finite replacement cluster, keep public escape hatches compatibility-only, and preserve bilingual status before any future implementation dispatch. |

## Deferred Dispatches

| Dispatch | Dependency | Reason |
|----------|------------|--------|
| `WP22-R1-B default-factory projection deletion` | `R1-1`, `R1-2`, and `R1-3` complete | `R1-B` remains blocked after `R1-A`; repeated deletion attempts are a planning smell, not evidence of readiness. |
| `WP22-R4-A closure preflight` | R2 residual work, public compatibility escape hatches, default-factory projection, and structural/binding debt resolved | Running closure now would only reproduce "not eligible" evidence. |

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
