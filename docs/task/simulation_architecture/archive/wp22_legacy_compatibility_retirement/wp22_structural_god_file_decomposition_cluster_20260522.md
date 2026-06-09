# WP22-E Structural God-File Decomposition

Status: `2026-05-22` current structural implementation wave locally accepted
for the two entry-header split slices. `counterfactual_replay_contracts.h` is
now an umbrella header below the `1500` threshold, and
`runtime_window_coordinator.h` is now below the `1000` threshold. Later
integration also split the validation family headers, retired the manual naval
post-`step()` fire loop into a named helper system, narrowed direct GPU visual
binding raw-world access behind a named `WorldBatchRuntime` helper, and moved
default-factory legacy seed ownership into `default_factory_legacy_spawn_compat.h`.
WP22-E remains open because `runtime_facade.cpp`, `default_unit_factory.h`,
broad bindings, `WorldBatchRuntime` service breadth, and public
compatibility/diagnostics escape hatches remain structural debt.
The eighth-wave Banach and Planck slices narrow two structural seams:
maintained binding reads now use kernel-owned query methods, and visual-binding
compatibility scene assembly now lives in a private helper. These are scoped
passes only; broad bindings, diagnostics/legacy raw ECS, public raw `world()`,
and the wider `WorldBatchRuntime` service surface remain open.

Noether pass: structural residuals are now allowed to remain only as named
blockers with owner plus failing guard. WP22-E does not pass if a source claim
tries to close while the new entry-header thresholds regress or if structural
debt is accepted as residual without a guard. `PilotWeaponRelease` and naval
mission weapon release now both route through named helper systems.
`default_unit_factory.h` no longer direct-includes `legacy_command.h`, but the
new `default_factory_legacy_spawn_compat.h` seed seam remains evaluation/guard
only until typed control-state replacement lands.

Guard wording checkpoint:
`counterfactual_replay_contracts.h` entry header is below `1500` lines;
`runtime_window_coordinator.h` entry header is below `1000` lines;
`counterfactual_replay_contract_validation.h` is now a thin umbrella over
validation family headers;
`PilotWeaponRelease` and naval mission weapon release now route through named
helper systems;
`default_factory_legacy_spawn_compat.h` owns the remaining default-factory
legacy seed seam and is still evaluation/guard-only in this pass.
`bindings_core.cpp` now separates maintained, diagnostics, legacy, and
diagnostics-override registration helpers; maintained binding reads now route
through kernel-owned query methods. The broad binding surface and
diagnostics/legacy raw-ECS blocks remain open.

Inputs:

- [WP22 main plan](legacy_compatibility_retirement_wp22_20260522.md)
- [WP22-A fact ledger](wp22_retirement_fact_ledger_cluster_20260522.md)

## Purpose

Turn the largest old implementation files from tolerated structural debt into
explicit behavior-preserving extraction work with owners, tests, and guards.
WP22-E cannot mark any god-file surface as acceptable residual while the source
still shows mixed responsibilities or live compatibility escape hatches.

## Source-Verified Scope Snapshot

| ID | Verified live fact | Source anchors | Retirement mode | Implementation dependency |
|----|--------------------|----------------|-----------------|---------------------------|
| `F-001` | `counterfactual_replay_contracts.h` is now a `130`-line umbrella header, and `counterfactual_replay_contract_validation.h` is now a thin umbrella over helper/replay/counterfactual/experiment validation family headers. | `wc -l src/runtime/contracts/counterfactual_replay_contracts.h src/runtime/contracts/counterfactual_replay_contract_validation.h src/runtime/contracts/counterfactual_replay_*validation*.h`; validation family headers under `src/runtime/contracts/` | `pass for validation-family split` | Keep the family ownership explicit and guard against umbrella regression. |
| `F-002` | `runtime_facade.cpp` is still a 2809-line mixed TU that contains typed-spawn compatibility materialization and raw runtime escape-hatch access. | `wc -l src/runtime/facade/runtime_facade.cpp`; `src/runtime/facade/runtime_facade.cpp:261-279`; `src/runtime/facade/runtime_facade.cpp:320-478`; `src/runtime/facade/runtime_facade.cpp:2360-2364` | `migrate` | Must coordinate with `WP22-C` on raw-runtime boundaries and with `WP22-D` on typed setup ownership. Do not edit shared boundary ranges in parallel. |
| `F-003` | `runtime_window_coordinator.h` is now a `405`-line entry header, with selection, callback, cadence-trace, and execution helpers in named companion headers. | `wc -l src/runtime/facade/runtime_window_coordinator.h src/runtime/facade/runtime_window_coordinator_*.h`; `src/runtime/facade/runtime_window_coordinator_selection_helpers.h`; `src/runtime/facade/runtime_window_coordinator_callback_helpers.h`; `src/runtime/facade/runtime_window_coordinator_cadence_trace_helpers.h`; `src/runtime/facade/runtime_window_coordinator_execution_helpers.h` | `migrate / pass for entry-header slice` | Entry-header split passed. Keep helper ownership explicit and do not reopen runtime-boundary semantics in this stream. |
| `F-004` | `default_unit_factory.h` is still a `1459`-line mixed header that builds capability bundles and spawn plans and performs entity spawn. It no longer direct-includes `legacy_command.h`; the remaining legacy command seed is isolated in `default_factory_legacy_spawn_compat.h`, which still blocks typed control-state closure. | `wc -l src/models/core/default_unit_factory.h src/components/command/default_factory_legacy_spawn_compat.h`; `src/models/core/default_unit_factory.h:14`; `src/models/core/default_unit_factory.h:1259-1277`; `src/components/command/default_factory_legacy_spawn_compat.h:3-58` | `migrate / scoped seed-narrowing pass` | Must coordinate with `WP22-D` because spawn ownership and legacy-command retirement share this file/helper pair. Only one worker should own the spawn-init range at a time. The helper seam remains evaluation/guard-only until typed control-state replacement lands. |
| `F-005` | Runtime contract headers total `11`, and `9/11` are already over 300 lines. This is still a live mixed-responsibility cluster, not a closed residual. | `find src/runtime/contracts -maxdepth 1 -name '*.h' -print0 | xargs -0 wc -l | sort -n`; `src/runtime/contracts/fidelity_profile_contracts.h`; `src/runtime/contracts/world_batch_contracts.h`; `src/runtime/contracts/parity_budget_contracts.h`; `src/runtime/contracts/counterfactual_replay_contracts.h` | `migrate` | Can start now on constants/types/validation extraction. Do not split the same normative table across concurrent workers. |
| `S-004` | `WorldBatchRuntime` still exposes a fat public surface, including raw `world()` access, setup, mutation, export, and query responsibilities. Direct `bindings_gpu.cpp` raw-world drilling is closed, and visual-binding compatibility scene assembly has been extracted to a private helper, but the batch service remains broad. | `src/core/engine/world_batch_runtime.h:65-68`; `src/core/engine/world_batch_runtime.h:137-142`; `src/core/engine/world_batch_runtime.cpp:337-342`; `src/core/engine/world_batch_runtime.cpp:1105-1130`; `src/core/engine/world_batch_visual_binding_compatibility_helper.h`; `src/interfaces/python/bindings_gpu.cpp:520-527` | `migrate / scoped service split pass` | Must coordinate with `WP22-C` because service-split decisions depend on the maintained facade/runtime boundary. |
| `S-005` | `bindings_core.cpp` still exposes `75` `.def` entries, but registration is now explicitly split into maintained, diagnostics-introspection, legacy-compatibility, and diagnostics-override helpers. Maintained binding reads now use kernel-owned query methods and no longer rely on a local raw-entity lookup; diagnostics and legacy helper blocks still raw-drill intentionally. | `wc -l src/interfaces/python/bindings_core.cpp src/interfaces/python/bindings_gpu.cpp`; `src/interfaces/python/bindings_core.cpp`; `src/core/engine/simulation_kernel.h`; `src/core/engine/simulation_kernel_observation_api.cpp`; `tests/architecture/test_wp22_structural_guardrails.py` | `quarantine / maintained seam pass` | Next work should reduce the broad public binding surface or migrate more maintained APIs toward facade/kernel-owned methods while keeping debug/legacy blocks explicitly quarantined. Coordinate with `WP22-C` before changing public maintained bindings. |
| `S-006` | The inline ordering residual is retired for this slice. `PilotWeaponRelease` and naval mission weapon release both register through named helper systems, and the old manual naval post-step query loop is absent. | `src/core/engine/simulation_kernel_systems.cpp`; `src/systems/combat/pilot_weapon_release_system.h`; `src/systems/naval/naval_mission_weapon_release_system.h`; `src/core/engine/simulation_kernel.cpp` | `pass for ordering helper seams` | Keep helper registration guarded and treat broader execution-phase dependency design as future structural debt, not this blocker. |

## Reproducible Commands

These commands were used for this source pass and should be rerun by any
implementation worker before claiming decomposition progress.

```bash
git diff --check
find src/runtime/contracts -maxdepth 1 -name '*.h' -print0 | xargs -0 wc -l | sort -n
wc -l src/runtime/facade/runtime_facade.cpp src/runtime/facade/runtime_window_coordinator.h src/models/core/default_unit_factory.h src/components/command/default_factory_legacy_spawn_compat.h src/interfaces/python/bindings_core.cpp
rg -n "PilotWeaponRelease|register_pilot_weapon_release_system|query<const MissionCommand, const NavalWeaponSystem>|RuntimeFacade::runtime\\(|^\\s*\\.def\\(\"" src/interfaces/python/bindings_core.cpp src/core/engine/simulation_kernel_systems.cpp src/core/engine/simulation_kernel.cpp src/runtime/facade/runtime_facade.cpp
rg -n "^struct |^inline constexpr |validate_" src/runtime/contracts/counterfactual_replay_contracts.h
rg -n "class WorldBatchRuntime|WorldBatchRuntime::world\\(|collect_visual_binding_compatibility_scenes_batch|spawn_units_batch\\(|apply_world_setup\\(|export_|set_|get_|clear_|reset_" src/core/engine/world_batch_runtime.h src/core/engine/world_batch_runtime.cpp
rg -n "build_platform_capability_bundle_template|resolve_platform_spawn_plan|compatibility_path_preserved|legacy_command|default_factory_legacy_spawn_compat|spawn\\(" src/models/core/default_unit_factory.h src/components/command/default_factory_legacy_spawn_compat.h
```

Observed outcomes from this pass:

- `git diff --check`: no whitespace or conflict-marker output.
- Contract-header count: `11` total headers, `9` above 300 lines.
- God-file counts should be remeasured before each structural dispatch; latest
  local check observed `runtime_facade.cpp = 2951`,
  `runtime_window_coordinator.h = 405`, `default_unit_factory.h = 1459`,
  `default_factory_legacy_spawn_compat.h = 58`, and `bindings_core.cpp = 965`.
- Binding-surface count: `75` `.def` entries in `bindings_core.cpp:433-962`.
- Eighth-wave binding recheck: maintained reads now use kernel-owned methods
  such as `get_instrument_state`, `get_egi_state`, `get_unit_heading`,
  `get_unit_type`, and `is_unit_active`; diagnostics/legacy raw ECS remains
  quarantined rather than retired.
- Eighth-wave service split: visual-binding compatibility scene assembly moved
  into `world_batch_visual_binding_compatibility_helper.h`; public
  `WorldBatchRuntime::world()` remains an explicit compatibility/diagnostics
  escape hatch.
- Ordering `rg`: confirmed `PilotWeaponRelease` and naval mission weapon
  release now route through named helper systems. `simulation_kernel_systems.cpp`
  no longer carries registered-in-place inline `OnUpdate` exceptions, and the
  old manual naval query loop is absent.

## Parallel And Dependency Rules

| Work slice | Dispatch posture | Rule |
|------------|------------------|------|
| `F-001`, `F-003`, `F-005` | `can run now` | Behavior-preserving extraction can start immediately if it does not alter public semantics. |
| `S-005` | `can run now with coordination` | Broad binding-surface reduction or additional facade/kernel-owned maintained methods may start now, but public maintained binding changes must stay aligned with `WP22-C`. |
| `F-002`, `S-004` | `wait for WP22-C coordination` | Any split that changes `RuntimeFacade::runtime()`, `WorldBatchRuntime::world()`, or maintained runtime service boundaries must not race `WP22-C`. |
| `F-004` | `coordinate with WP22-D` | Spawn-plan extraction and legacy-command seeding are shared ownership areas with `WP22-D`; include both `default_unit_factory.h` and `default_factory_legacy_spawn_compat.h`. |
| `S-006` | `scoped pass / guard follow-up` | Keep named helper-system ordering guards; broader phase/dependency design is future structural work. |
| Shared normative tables or the same line range | `serialize ownership` | No concurrent worker may split the same contract table or the same `runtime_facade.cpp` / `default_unit_factory.h` line range. |

## Fail And Pass Gate

Fail this stream if any of the following remains true after an implementation
claim:

- god files are relabeled as acceptable residuals without a landed split or a
  concrete guard against further growth;
- a source pass claims Noether-style closure while `counterfactual_replay_contracts.h`
  rises back above `1500` lines or `runtime_window_coordinator.h` rises back
  above `1000` lines;
- a structural split changes runtime behavior but the behavior change is not
  owned and validated by the corresponding `WP22-C` or `WP22-D` stream;
- raw runtime escape hatches, broad bindings, or unresolved ordering blockers are
  left live while being described as retired;
- `PilotWeaponRelease` or naval mission weapon release drifts away from named
  helper-system registration or reintroduces a manual query loop;
- concurrent workers split the same normative table or boundary range.

Pass only if all of the following are source-backed:

- at least one high-value structural split lands without behavior change;
- remaining large files have an owner, a next split seam, and a guard against
  growth rather than residual acceptance;
- maintained-vs-debug binding ownership is explicit;
- runtime-ordering exceptions are either extracted into explicit systems/phases
  or left as named blockers with guards.

## Noether Guard Register

| Gate | Current fact | Why this is still blocked |
|------|--------------|---------------------------|
| `G-001` | `counterfactual_replay_contracts.h = 130` lines; `counterfactual_replay_contract_validation.h = 4` lines plus validation family headers | Entry-header and validation-family split passed; prevent umbrella regression. |
| `G-002` | `runtime_window_coordinator.h = 405` lines | Entry-header threshold passed; maintain helper ownership and prevent regression above `1000` lines. |
| `G-003` | `PilotWeaponRelease` and naval mission weapon release now route through named helper systems | Keep `simulation_kernel_systems.cpp` free of registered-in-place inline `OnUpdate` exceptions and prevent manual query-loop regression. |
| `G-004` | `default_factory_legacy_spawn_compat.h` keeps a named `SpawnCompatibilityLegacyCommandSeed` seam and `default_unit_factory.h` calls it through a narrow helper | This is quarantined seed ownership, not typed control-state replacement. |
| `G-005` | Maintained binding reads use kernel-owned query methods; diagnostics/legacy blocks still raw-drill | Maintained raw-entity reads are closed for this slice, but broad public binding count and debug/legacy raw ECS remain structural debt. |
| `G-006` | Visual-binding compatibility scene assembly is now private helper code; public `WorldBatchRuntime::world()` remains live | This narrows one service seam without retiring the public compatibility/diagnostics escape hatch or the broader fat service surface. |

## First-Wave Implementation Snapshot

| Field | Value |
|------|-------|
| `status` | `partial` |
| `commands run` | `git diff --check` -> pass; `find src/runtime/contracts -maxdepth 1 -name '*.h' -print0 | xargs -0 wc -l | sort -n` -> `11` headers, `9` above 300 lines; `wc -l src/runtime/facade/runtime_facade.cpp src/runtime/facade/runtime_window_coordinator.h src/models/core/default_unit_factory.h src/interfaces/python/bindings_core.cpp` -> `2809 / 1299 / 1457 / 965`; focused structural guard now includes explicit line-threshold and inline-order blocker gates |
| `remaining blockers` | runtime-facade boundary mix remains structural debt; factory spawn and legacy-command ownership remain coupled through `default_factory_legacy_spawn_compat.h`; public raw `WorldBatchRuntime::world()` remains a compatibility/diagnostics surface; fat service and broad binding surfaces remain live |
| `integration notes` | Continue the high-value structural splits, but serialize `runtime_facade.cpp` work with `WP22-C` and `default_unit_factory.h` work with `WP22-D`; do not count file-count reduction alone as success, and do not call the remaining thresholds or inline blocker “residual closure” |

## Return Packet

- `status`: `pass` for this source-verification and documentation-refresh pass;
  structural retirement itself remains mixed and dependency-gated.
- `touched files`:
  `docs/task/simulation_architecture/archive/wp22_legacy_compatibility_retirement/wp22_structural_god_file_decomposition_cluster_20260522.md`,
  `docs/task/simulation_architecture/archive/wp22_legacy_compatibility_retirement/wp22_structural_god_file_decomposition_cluster_20260522.zh.md`
- `commands run`:
  `git diff --check`;
  `find src/runtime/contracts -maxdepth 1 -name '*.h' -print0 | xargs -0 wc -l | sort -n`;
  `wc -l src/runtime/facade/runtime_facade.cpp src/runtime/facade/runtime_window_coordinator.h src/models/core/default_unit_factory.h src/components/command/default_factory_legacy_spawn_compat.h src/interfaces/python/bindings_core.cpp`;
  `rg -n "PilotWeaponRelease|register_pilot_weapon_release_system|query<const MissionCommand, const NavalWeaponSystem>|RuntimeFacade::runtime\\(|^\\s*\\.def\\(\"" src/interfaces/python/bindings_core.cpp src/core/engine/simulation_kernel_systems.cpp src/core/engine/simulation_kernel.cpp src/runtime/facade/runtime_facade.cpp`;
  `rg -n "^struct |^inline constexpr |validate_" src/runtime/contracts/counterfactual_replay_contracts.h`;
  `rg -n "class WorldBatchRuntime|WorldBatchRuntime::world\\(|collect_visual_binding_compatibility_scenes_batch|spawn_units_batch\\(|apply_world_setup\\(|export_|set_|get_|clear_|reset_" src/core/engine/world_batch_runtime.h src/core/engine/world_batch_runtime.cpp`;
  `rg -n "build_platform_capability_bundle_template|resolve_platform_spawn_plan|compatibility_path_preserved|legacy_command|default_factory_legacy_spawn_compat|spawn\\(" src/models/core/default_unit_factory.h src/components/command/default_factory_legacy_spawn_compat.h`
- `remaining blockers`:
  `F-002` runtime-facade boundary mix remains live;
  `F-004` factory spawn and legacy-command ownership remain coupled through
  `default_factory_legacy_spawn_compat.h`;
  `S-004` public raw `WorldBatchRuntime::world()` and fat service surface remain
  live, while direct GPU binding raw-world access and visual-binding scene
  assembly are now behind named helpers;
  `S-005` maintained binding reads now use kernel-owned query methods, while
  diagnostics/legacy raw ECS and broad binding count remain open;
  `S-006` helper-system ordering now has a scoped pass and must keep regression guards.
- `integration notes`:
  `WP22-E` may start immediately on `F-001`, `F-003`, `F-005`, and scoped
  binding-surface quarantine.
  `WP22-E` must serialize any `runtime_facade.cpp` boundary work with `WP22-C`
  and any `default_unit_factory.h` / `default_factory_legacy_spawn_compat.h`
  spawn work with `WP22-D`.
  Do not count file-count reduction alone as success; the split must preserve
  behavior and expose a tighter ownership seam.
- `WP22-E implementation dispatch allowed?`: `yes`, but only for
  `F-001`, `F-003`, `F-005`, and scoped `S-005` work.
  `F-002`, `F-004`, and `S-004` remain coordination-gated; `S-006` is guard follow-up.

## Verification Notes

- This document records source-backed decomposition facts only. No structural
  code changes were performed in this pass.
- No `pytest` validation was run in this pass because the task scope was
  fact re-verification and cluster-document refresh, not runtime behavior
  change.
- Do not treat file size alone as the problem statement. The verified debt is
  mixed responsibility plus live compatibility escape hatches and ordering
  exceptions.

## Current Structural Implementation Snapshot

| Field | Value |
|------|-------|
| `status` | `partial`: `F-001` validation-family split, `F-003` entry-header split, `S-006` helper-system ordering, maintained binding query ownership, and visual-binding helper extraction passed; broader structural retirement remains open. |
| `commands run` | `git diff --check` -> pass; `python3 -m pytest -q tests/architecture/test_wp22_default_factory_legacy_seed_guard.py tests/architecture/test_wp22_structural_guardrails.py tests/architecture/runtime_facade/test_layering.py -k "wp22 or bindings or world_batch_runtime or gpu_visual_binding or visual_binding_raw_world_access or escape_hatch or batch_runtime"` -> `32 passed, 16 deselected`; `cmake --build build-workshop --target ef_py -j4` -> pass in the returned implementation packets. |
| `remaining blockers` | `runtime_facade.cpp = 2951`; `default_unit_factory.h = 1459` plus behavior-bearing `default_factory_legacy_spawn_compat.h`; broad binding surface remains; diagnostics/legacy raw ECS remains quarantined; raw `WorldBatchRuntime::world()` remains a public compatibility/diagnostics surface; `WorldBatchRuntime` still has a fat service surface. |
| `integration notes` | Next structural dispatch should avoid the already-split entry headers, validation-family split, helper-system ordering slice, maintained binding query seam, and visual-binding helper unless tightening guards. Prefer independent slices: runtime facade boundary split, factory/spawn typed control-state replacement, broad binding-surface reduction, or another world-batch service decomposition. |
