# WP22-D Command DTO And Legacy Surface Retirement

Status: `2026-05-22` source-verified refresh complete, A-001 follow-up
landed, and the latest default-factory seed narrowing slice locally passed.
Maintained typed setup now uses the maintained validator plus a batch-owned
typed spawn helper; explicit legacy compatibility setup remains named and
separate. `default_unit_factory.h` no longer direct-includes `legacy_command.h`;
the remaining spawn-time legacy seed is isolated in
`default_factory_legacy_spawn_compat.h` and is still not typed control-state
ownership. Broader command/DTO retirement remains open.

WP22 residual note for the 2026-05-23 re-baseline: `R1-B` default-factory
projection deletion remains blocked after `R1-A`. Repeated deletion attempts are
a planning smell, not a new dispatch target. The finite residual cluster now
splits R1 into pending transport shell narrowing, debug/diagnostics mirror
retirement, and exact-stage contract demotion/alignment; default-factory
projection deletion stays deferred until those three sub-slices complete.

Noether pass: allowlists are not closure evidence. Remaining seams only stay
open if they are named with replacement, owner, and failing guard.
`control_input_resolution.h`, `command_link.h`, and `operation_system.h`
remain named compatibility-owner seams, while the default-factory spawn seed
now lives in `default_factory_legacy_spawn_compat.h`. That helper is explicit
quarantine, not typed control-state replacement.
The eighth-wave Harvey slice is accepted only as `partial`: the default factory
now seeds a typed `MissionCommand` shell before projecting compatibility state,
but `MovementCommand` / `LaggedCommand` projection remains behavior-bearing and
blocks `L-001b` retirement.

Guard wording checkpoint:
`control_input_resolution.h`, `command_link.h`, and `operation_system.h` remain
named compatibility-owner seams;
`default_factory_legacy_spawn_compat.h` owns the remaining spawn-time legacy-command seed and still blocks closure until typed control-state replacement lands;
`MissionCommand`, `TaskOrder`, `LeaderIntent`, and `PilotReport` are now marked
as compatibility transport shells with owner-slice projection helpers, which is
guarded quarantine rather than DTO retirement;
allowlist is not closure evidence;
every open seam still requires replacement, owner, and failing guard.

Inputs:

- [WP22 main plan](legacy_compatibility_retirement_wp22_20260522.md)
- [WP22-A fact ledger](wp22_retirement_fact_ledger_cluster_20260522.md)
- [WP22-C runtime escape-hatch closure](wp22_runtime_escape_hatch_closure_cluster_20260522.md)

## Purpose

Retire C++ legacy command fallbacks, aggregate DTO shells, and type-name setup
compatibility where they still act as maintained implementation surfaces. WP22-D
is not allowed to count compatibility preservation as closure evidence.

## Source-Verified Scope Snapshot

| ID | Verified live fact | Source anchors | Retirement mode | Implementation dependency |
|----|--------------------|----------------|-----------------|---------------------------|
| `L-001` | `legacy_command.h` is still a maintained surface. The direct-include allowlist has narrowed, but it is still not closure evidence: `control_input_resolution.h`, `command_link.h`, and `operation_system.h` remain named compatibility-owner seams, and maintained paths still read `MovementCommand` or `ActionCommand`. | `src/components/command/air/control_input_resolution.h:5`; `src/components/command/command_link.h:3`; `src/systems/core/operation_system.h:8`; `src/systems/naval/embarked_air_ops_system.h:11`; `src/systems/combat/damage_system.h:9`; `src/systems/physics/ground_contact_system.h:177`; `src/systems/physics/force_system.h:75-78`; `src/systems/physics/instrument_system.h:182-183`; `src/systems/physics/propulsion_system.h:40-47`; `src/systems/systems/logistics_system.h:90-94` | `migrate` | Can start now on maintained callers and guards. Do not claim retirement while those systems still consume legacy command truth. |
| `L-001a` | `control_input_resolution.h` is only a partial bridge. It centralizes selected fallback checks, but propulsion, force, instrument, and ground-contact logic still carry their own legacy-resolution behavior. | `src/components/command/air/control_input_resolution.h:17-48`; `src/systems/physics/propulsion_system.h:40-47`; `src/systems/physics/ground_contact_system.h:177`; `src/systems/physics/force_system.h:75-78`; `src/systems/physics/instrument_system.h:182-183` | `quarantine` | Can run in parallel with `L-001`. Finish the single bridge before removing per-system fallback code. |
| `L-001b` | Aircraft spawn legacy command seeding is now quarantined behind `SpawnCompatibilityLegacyCommandSeed` in `default_factory_legacy_spawn_compat.h`; `default_unit_factory.h` calls the named helper and no longer direct-includes `legacy_command.h`. This is still not typed control-state/default initialization replacement. | `src/components/command/default_factory_legacy_spawn_compat.h`; `src/models/core/default_unit_factory.h`; `tests/architecture/test_wp22_default_factory_legacy_seed_guard.py`; `tests/architecture/test_wp9_guard_enforcement.py` | `quarantine / scoped pass` | Must coordinate with `WP22-E` on broader `default_unit_factory.h` splits. Do not treat the helper seam as typed control-state replacement. |
| `L-001c` | Eighth-wave typed seed reduction added a typed `MissionCommand` shell during flight-model spawn and projects the remaining compatibility seed from `MissionCommandCore`. This reduced duplicate `ActionCommand` seeding but did not retire the legacy control-state projection. | `src/models/core/default_unit_factory.h`; `src/components/command/default_factory_legacy_spawn_compat.h`; `tests/architecture/test_wp22_default_factory_legacy_seed_guard.py`; `tests/runtime/mission/test_mission_command_split_semantics.py`; `tests/runtime/naval/test_naval_legacy_movement_debug.py` | `partial / blocker evidence` | Next implementation must inventory and replace the spawn-time `MovementCommand` / `LaggedCommand` control path rather than widening the compatibility helper. |
| `L-001d` | `R1-B` default-factory projection deletion remains blocked after `R1-A`. The residual blocker is now a finite cluster, not a single helper seam: pending transport shell narrowing, debug/diagnostics mirror retirement, and exact-stage contract demotion/alignment must complete first. | `docs/task/simulation_architecture/archive/wp22_legacy_compatibility_retirement/wp22_remaining_task_clusters_20260523.md`; `src/components/command/default_factory_legacy_spawn_compat.h`; `src/interfaces/python/bindings_core.cpp`; `src/core/engine/exact_stage_inventory.cpp` | `blocked / residual cluster` | Do not dispatch another default-factory deletion attempt until the finite R1 residual cluster returns complete packets. |
| `A-001` | Maintained typed setup now consumes `validate_maintained_typed_platform_spawn_request(...)` and materializes through `WorldBatchRuntime::spawn_typed_platform_unit(...)` without rebuilding a `WorldSpawnRequest`. Explicit legacy compatibility typed setup remains named separately. | `src/runtime/facade/runtime_facade.cpp`; `src/core/engine/world_batch_runtime.cpp`; `src/core/engine/world_batch_runtime.h`; `src/interfaces/python/bindings_runtime.cpp`; `tests/architecture/platform_spawn/test_boundary_guards.py`; `tests/runtime/facade/test_runtime_facade.py` | `scoped pass` | Keep guards that prevent maintained typed setup from reintroducing `compatibility_type_name_materialization` or legacy request-shape rematerialization. |
| `S-001` | Aggregate DTO shells remain live but are now explicitly compatibility transport shells. `MissionCommand`, `TaskOrder`, `LeaderIntent`, and `PilotReport` still inherit cross-domain air/naval slices; owner-slice projection helpers and world-batch assignment wrapper guards make the transport role explicit. | `src/components/command/mission_command.h`; `src/components/tasking/task_order.h`; `src/components/tasking/leader_intent.h`; `src/components/tasking/pilot_report.h`; `src/runtime/contracts/world_batch_contracts.h`; `tests/architecture/test_wp22_dto_domain_shell_guard.py` | `migrate / guarded quarantine` | Next implementation must migrate maintained consumers toward domain owner slices or variant DTOs. Coordinate with `WP22-E` if the same headers are being structurally split. |
| `S-002` | Air recovery/takeoff and formation fields are duplicated across three DTO stages, so flat-shell truth still spans command, tasking, and leader layers. | `src/components/command/air/mission_command_air.h:18-31`; `src/components/tasking/air/task_order_air.h:68-108`; `src/components/tasking/air/leader_intent_air.h:137-163` | `migrate` | Can run in parallel with `S-001`. Do not change semantics silently while deduplicating field ownership. |
| `S-003` | Naval lifecycle data is still asymmetric across aggregate DTOs. `MissionCommandNaval` carries stationing and helo-launch fields, while tasking/intent/report retain warfare-role and OTC fields separately. | `src/components/command/naval/mission_command_naval.h:42-50`; `src/components/tasking/naval/task_order_naval.h:115-119`; `src/components/tasking/naval/leader_intent_naval.h:169-172`; `src/components/tasking/naval/pilot_report_naval.h:184-186` | `migrate` | Can start now, but any change that alters runtime mission-command mapping must coordinate with `WP22-E` if inline combat ordering is touched. |

## Reproducible Commands

These commands were used for this source pass and should be rerun by any
implementation worker before claiming retirement progress.

```bash
git diff --check
rg -n "legacy_command\\.h|MovementCommand|ActionCommand|LaggedCommand" src tests
rg -n "WorldSpawnRequest|TypedPlatformSpawnRequest|spawn_unit\\(|typed_platform_spawn_requests|compatibility_path_preserved" src tests
rg -n "struct .*: .*Air, .*Naval|struct World(MissionCommand|TaskOrder|LeaderIntent|PilotReport)Assignment|recovery_base_id|takeoff_procedure_id|warfare_role_code|officer_in_tactical_command|reference_entity_id|launch_helo|recover_helo" src/components src/runtime tests
```

Observed outcomes from this pass:

- `git diff --check`: no whitespace or conflict-marker output.
- Legacy command `rg`: confirmed direct system includes, factory spawn seeding,
  command-API seeding, and live debug/binding exposure.
- Legacy direct-include allowlist: reduced to
  `control_input_resolution.h`, `command_link.h`,
  `default_factory_legacy_spawn_compat.h`, `operation_system.h`, and the
  compatibility umbrella `physics/action.h`, but this remains a blocker
  register rather than closure proof.
- Typed spawn focused validation: maintained typed setup uses the maintained
  validator and batch-owned typed spawn helper; explicit legacy compatibility
  typed setup keeps the named compatibility bridge.
- Eighth-wave local recheck: default-factory/WP9 guards, mission/naval focused
  tests, and the WP22 focused architecture sweep passed, but the result remains
  `partial` because `MovementCommand` / `LaggedCommand` are still projected in
  the compatibility helper.
- Aggregate DTO `rg`: confirmed composite air/naval structs and world-batch
  aggregate assignment wrappers are still live.

## Parallel And Dependency Rules

| Work slice | Dispatch posture | Rule |
|------------|------------------|------|
| `L-001`, `L-001a`, `S-001`, `S-002`, `S-003` | `can run now with coordination` | Safe to start on consumer inventory, bridge consolidation, DTO guard authoring, and migration seams. Do not flip maintained public setup ownership in this slice. |
| `L-001b` | `coordinate with WP22-E` | Shares `default_unit_factory.h` and spawn-init ownership with structural decomposition. Only one worker should edit the spawn/legacy-command initialization range at a time. |
| `A-001` | `scoped pass / guard follow-up` | Maintained typed setup is first-class for this facade path; keep explicit compatibility setup separate and guarded. |
| Header decomposition touching mission/tasking DTO files | `coordinate with WP22-E` | If `WP22-E` splits `world_batch_contracts.h` or DTO headers, `WP22-D` must avoid simultaneous ownership changes in the same line ranges. |
| Runtime-facade public setup semantics | `wait for WP22-C` | Do not change `runtime_facade.cpp:261-504` in parallel with `WP22-C` boundary work. |

## Fail And Pass Gate

Fail this stream if any of the following remains true after an implementation
claim:

- maintained systems still resolve command truth from independent
  `MovementCommand` or `ActionCommand` fallback logic outside the single bridge;
- the narrowed direct-include allowlist is treated as closure evidence instead
  of a named blocker register with replacement, owner, and failing guard;
- aircraft/default spawn still seeds legacy command state as the maintained
  control truth with no replacement seam;
- maintained `TypedPlatformSpawnRequest` again requires
  `compatibility_path_preserved = true` or materializes through a legacy
  request-shape bridge;
- aggregate DTO shells remain the unguarded domain truth for maintained logic.

Pass only if all of the following are source-backed:

- maintained command resolution flows through a single typed or bridge-owned
  compatibility seam;
- new maintained callers cannot include or depend on `legacy_command.h`
  outside an explicit compatibility allowlist;
- the remaining allowlist entries are reduced to owner-bound compatibility
  seams rather than open-ended residuals;
- typed setup no longer depends on legacy `type_name` materialization as the
  maintained path;
- mission/tasking DTO ownership is domain-scoped or guarded so flat-shell
  truth is no longer first-class.

## Noether Guard Register

| Gate | Current fact | Why this is still blocked |
|------|--------------|---------------------------|
| `G-101` | `control_input_resolution.h`, `command_link.h`, and `operation_system.h` still own explicit `legacy_command.h` seams | The allowlist is intentionally narrow, but it still marks live compatibility ownership that must be replaced, not accepted. |
| `G-102` | `default_factory_legacy_spawn_compat.h` owns the named `SpawnCompatibilityLegacyCommandSeed` seam while `default_unit_factory.h` calls it through a narrow helper | This is explicit quarantine, not typed control-state replacement. |
| `G-103` | Maintained typed setup uses `validate_maintained_typed_platform_spawn_request(...)` and `WorldBatchRuntime::spawn_typed_platform_unit(...)` | Keep the positive guard preventing maintained legacy rematerialization. |
| `G-104` | Flight-model spawn now seeds a typed `MissionCommand` shell before projecting compatibility state | This is progress, but `MovementCommand` / `LaggedCommand` still carry behavior-bearing spawn control state and must be replaced before closure. |

## Return Packet

- `status`: `pass` for this source-verification and documentation-refresh pass;
  implementation retirement remains mixed and dependency-gated.
- `touched files`:
  `docs/task/simulation_architecture/archive/wp22_legacy_compatibility_retirement/wp22_command_dto_legacy_surface_retirement_cluster_20260522.md`,
  `docs/task/simulation_architecture/archive/wp22_legacy_compatibility_retirement/wp22_command_dto_legacy_surface_retirement_cluster_20260522.zh.md`
- `commands run`:
  `git diff --check`;
  `rg -n "legacy_command\\.h|MovementCommand|ActionCommand|LaggedCommand" src tests`;
  `rg -n "WorldSpawnRequest|TypedPlatformSpawnRequest|spawn_unit\\(|typed_platform_spawn_requests|compatibility_path_preserved" src tests`;
  `rg -n "struct .*: .*Air, .*Naval|struct World(MissionCommand|TaskOrder|LeaderIntent|PilotReport)Assignment|recovery_base_id|takeoff_procedure_id|warfare_role_code|officer_in_tactical_command|reference_entity_id|launch_helo|recover_helo" src/components src/runtime tests`
- `remaining blockers`:
  `L-001b` remains a compatibility seed seam in
  `default_factory_legacy_spawn_compat.h` until typed control-state/default
  initialization replaces it;
  aggregate DTO shells still carry cross-domain truth.
  `L-001d` records the new residual-cluster block: `R1-B` default-factory
  projection deletion stays deferred until the finite R1 sub-slices complete.
- `integration notes`:
  `WP22-D` may start on legacy-command consumer migration, single-bridge
  consolidation, and DTO guard authoring now.
  Maintained typed setup is now first-class for the runtime-facade path; do not
  collapse it back into explicit legacy compatibility setup.
  Any `default_unit_factory.h`, `default_factory_legacy_spawn_compat.h`, or
  shared DTO-header work must be serialized with `WP22-E`.
- `WP22-D implementation dispatch allowed?`: `yes`, but only for
  `L-001`, `L-001a`, `S-001`, `S-002`, and `S-003`.
  `A-001` is a scoped pass; only its regression guard follow-up remains while
  broader DTO and default-factory work stays open.

## First-Wave Implementation Snapshot

| Field | Value |
|------|-------|
| `status` | `blocked` |
| `commands run` | `git diff --check` -> pass; focused typed setup/facade tests now pass; legacy-command scans still show broader consumer/DTO work. |
| `remaining blockers` | broader `ActionCommand` consumers remain; `default_factory_legacy_spawn_compat.h` keeps a named compatibility seed seam; aggregate DTO shells still carry cross-domain truth. |
| `integration notes` | Keep the single-bridge migration open, keep A-001 positive guards, and do not treat the narrowed allowlist as closure evidence. |

## Verification Notes

- This document records source-backed retirement facts only. No implementation
  changes were performed in this pass.
- No `pytest` validation was run in this pass because the task scope was
  fact re-verification and cluster-document refresh, not runtime behavior
  change.
- This note remains open: `WP22-F` is still not eligible, and `R1-B` deletion
  remains blocked until the finite residual cluster completes.
- Do not translate this packet into acceptance language. The verified result is
  that the listed legacy surfaces are still live and still require retirement.
