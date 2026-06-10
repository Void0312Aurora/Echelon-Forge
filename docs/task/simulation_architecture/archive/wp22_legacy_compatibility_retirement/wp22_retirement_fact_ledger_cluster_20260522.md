# WP22-A Retirement Fact Ledger And Kill List

Status: `2026-05-22` WP21 owner-rejected; source-backed ledger updated. The
latest implementation wave is locally accepted for seven scoped slices:
`RTE-003` production raw-loader cleanup, `RTE-007` setup/type/schema ownership,
`A-001` maintained typed setup promotion, `F-001` validation-family split, and
`F-003` entry-header split, plus direct GPU visual-binding raw-world quarantine
and default-factory legacy seed helper extraction. The latest guard wave also
accepted DTO transport-shell marking, `bindings_core.cpp`
maintained/diagnostics/legacy registration separation, and repo-level
`batch_runtime` consumer guard hardening. The eighth wave closed the maintained
binding raw-entity seam and accepted a private visual-binding service
extraction. The ninth wave added a scoped pass for `WorldBatchRuntime` setup
orchestration split and a read-only pass for typed command-control replacement
inventory. That inventory identifies `MissionCommandControlState` as the next
minimal typed seam. Meitner returned a `partial / interrupted / unvalidated`
implementation packet; the main thread fixed its `CommandLag` target-overwrite
risk and reran the focused guards/build. The tenth wave then closed the
remaining typed ingress/link sync blocker and hardened the corresponding guards.
Default-factory typed seed work remains `partial` because `MovementCommand` /
`LaggedCommand` projection is still a compatibility mirror, not retired
ownership.
WP22 remains open because
runtime/facade compatibility escape hatches, default-factory typed
control-state replacement, real aggregate DTO retirement, fat world-batch
services, broad public bindings, and broader structural blockers remain live.

Closure note:

- Lagrange, Laplace, and Raman returned usable findings that seed this ledger.
- The Python source-pass subagent timed out and was closed without a complete
  return packet.
- Turing re-dispatched the bounded `WP22-B0` read-only Python verification and
  returned a complete packet with `status: blocked`, `touched files: none`.
- Therefore the Python source-pass gap is no longer missing evidence; it is a
  source-verified blocker. `WP22-B` has now cleared maintained-business
  retirement, and the remaining import-time `ef_py.TaskOrder` unlock in
  `command_chain_cache` is a validation-only C/F guard-lane follow-up, not a
  blocker.

The next fact-verification and documentation-hardening batch returned packets.
Zeno and Arendt returned pass packets; Tesla returned a partial packet for the
bounded `RTE-003` runtime slice. The follow-on implementation wave then returned
four scoped pass packets, accepted only for those slices. This is progress
evidence, not closure evidence.

Latest scoped-pass sync:

- `Singer` is accepted as a scoped `pass` for the operation/command-link mirror dependency reduction slice. The main thread rechecked `architecture WP9/WP22/DTO` focused guards, `runtime/naval` focused tests, `ef_py` build, and `git diff --check`, and also fixed `tests/architecture/compatibility_quarantine/test_guard_enforcement.py::_compile_and_run` with `-x none` before link args.
- `Nietzsche` is accepted as a scoped `pass` for the naval maintained DTO consumer migration slice. The same main-thread verification passed, and the slice keeps `command_code` compatibility fallback live.
- These are scoped passes only; they do not change `WP22 overall` from open, and they do not make `WP22-F` eligible.

Second-wave refresh:

- `WP22-B` now passes for maintained-business retirement: `common_core_profile`
  and `loading.py` are compatibility-only guard surfaces, the raw sim seam has
  moved to C/F compatibility guard ownership, and the remaining import-time
  `ef_py.TaskOrder` unlock in `command_chain_cache` is validation-only.
- `WP22-D` now passes because legacy command consumers have been migrated or
  quarantined behind the bridge, leaving only the specific bridge/default-factory
  seam on the allowlist.
- WP22-specific tests pass, and the aggregate sweep now passes after WP16/WP20
  drift cleanup, so the third-wave follow-up is active.

## Corrected Audit Facts

| Audit area | Corrected fact | Source anchors | Implication |
|------------|----------------|----------------|-------------|
| `F-005` contract-header count | Runtime contract headers total `11`; `9/11` exceed 300 lines, not "7 of 9". `8/9` large headers mix constants, DTOs, and inline helper/validation responsibilities. | `src/runtime/contracts/backend_profile_contracts.h:11`; `src/runtime/contracts/counterfactual_replay_contracts.h:16`; `src/runtime/contracts/world_batch_contracts.h:47` | Split planning must use the corrected count and mixed-responsibility wording. |
| `L-001` legacy command consumers | Audit wording about "`legacy_command.h` has 11 active consumers" is imprecise. There are `10` direct system includes and at least `12` maintained users once bridge/indirect use is counted. `control_input_resolution.h` is only a partial bridge; `propulsion_system.h` still carries legacy throttle fallback. | `src/components/command/legacy_command.h:6`; `src/systems/core/operation_system.h:34`; `src/systems/physics/propulsion_system.h:38`; `src/systems/systems/command_link_system.h:20`; `src/components/command/air/control_input_resolution.h:13`; `src/systems/physics/ground_contact_system.h:178`; `src/systems/physics/propulsion_system.h:44` | `WP22-D` must treat legacy command retirement as active maintained-path migration, not closure residue. |
| `L-002` raw escape hatch wording | "`default path`" wording is overstated. `RuntimeFacade.runtime()` is no longer the main maintained default API, but raw escape remains alive; `RuntimeFacadeAdapter` still caches raw runtime and `WorldBatchRuntime::world()` remains public. The former direct GPU binding raw-world residual is now routed through `WorldBatchRuntime::collect_visual_binding_compatibility_scenes_batch(...)`. `runtime_facade.cpp:592` is maintained typed setup evidence, not raw drilling. | `python/rl/runtime/world_batch/adapter.py:49`; `tests/architecture/runtime_facade/test_runtime_escape_hatches.py`; `src/runtime/facade/runtime_facade.cpp:592`; `src/runtime/facade/runtime_facade.cpp:2498`; `src/core/engine/world_batch_runtime.h:65`; `src/core/engine/world_batch_runtime.cpp:337`; `src/interfaces/python/bindings_gpu.cpp:520`; `src/core/engine/world_batch_runtime.cpp:1105` | `WP22-C` should classify public raw access as `quarantine`, not "already retired"; direct GPU binding raw-world use is a scoped pass. |
| `A-003` WP21-gated wording | WP21-accepted typed/setup and facade progress did not by itself retire legacy setup/runtime surfaces. WP22 follow-up has since promoted maintained typed setup in `RuntimeFacade.apply_world_setup`, while explicit legacy compatibility setup, `legacy` runtime mode, and raw escape hatches remain quarantined surfaces. | `src/runtime/facade/runtime_facade.cpp`; `src/core/engine/world_batch_runtime.cpp`; `python/env_config.py`; `python/rl/runtime/world_batch/adapter.py` | Keep the distinction between maintained typed setup pass and remaining compatibility/diagnostics residuals. |
| `S-004` world-batch surface size | `WorldBatchRuntime` exposes `41` public methods, not `36`, across at least seven responsibility groups, and still exposes raw `world()`. | `src/core/engine/world_batch_runtime.h:15`; `src/core/engine/world_batch_runtime.h:30`; `src/core/engine/world_batch_runtime.h:45`; `src/core/engine/world_batch_runtime.cpp:526`; `src/core/engine/world_batch_runtime.cpp:703`; `src/core/engine/world_batch_runtime.cpp:817` | `WP22-E` must split by service seam, not accept the fat runtime shell. |
| `S-005` Python binding characterization | `bindings_core.cpp` exposes `75` `.def` entries in the `431-956` range, not "55+", and multiple lambdas still drill into `self.get_world().entity(...)`. Direct GPU visual batching no longer calls `.world(` from `bindings_gpu.cpp`, so the remaining binding debt is broad maintained/debug surface mix rather than that specific residual. | `src/interfaces/python/bindings_core.cpp:431`; `src/interfaces/python/bindings_core.cpp:433`; `src/interfaces/python/bindings_core.cpp:708`; `src/interfaces/python/bindings_core.cpp:949`; `src/interfaces/python/bindings_gpu.cpp:520` | `WP22-E` should quarantine direct-kernel bindings behind explicit debug/diagnostics allowlists and keep the GPU direct raw-world guard. |
| `S-006` inline-system wording | Superseded by later implementation packets: `PilotWeaponRelease` and naval mission weapon release now register through named helper systems, and the manual naval post-step query loop is absent. | `src/core/engine/simulation_kernel_systems.cpp`; `src/systems/combat/pilot_weapon_release_system.h`; `src/systems/naval/naval_mission_weapon_release_system.h`; `src/core/engine/simulation_kernel.cpp` | `WP22-E` should keep helper-system ordering guards and treat broader phase/dependency design as future structural debt. |

## Kill List

| ID | Surface | Status | Retirement | Owner | Replacement | Guard / validation |
|----|---------|--------|------------|-------|-------------|--------------------|
| `RTE-001` | `RuntimeFacade.runtime()` raw escape hatch | Not mainline default, still live compatibility/diagnostics surface; adapter caches raw runtime. | `quarantine` | `WP22-C` | Facade APIs, `run_wp10_window()`, adapter batch methods | No new maintained `.runtime()` callers outside allowlist. `python -m pytest -q tests/architecture/runtime_facade -k "runtime_facade_runtime_consumers or leader_world_batch_runtime_does_not_call_runtime_facade_runtime"` |
| `RTE-002` | `vec_env.batch_runtime` public compatibility view | Publicly exposed, test-protected compatibility view. | `quarantine` | `WP22-C` | `runtime_facade`, `RuntimeFacadeAdapter`, explicit vec-env accessors | No new production `.batch_runtime.` consumers. `python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k batch_runtime && python -m pytest -q tests/architecture/runtime_facade -k batch_runtime` |
| `RTE-003` | `loader.sim` in runtime wrappers | Production `loader.sim.*` / `loader.sim,` usage is now empty in `gym_envs` and `python/rl`; remaining occurrences are explicit test/guard strings. | `pass for production raw-loader cleanup` | `WP22-C` / C/F guard lane | Named loader-backed compatibility seams, typed mission-command helpers, facade/bridge-owned setters | `rg -n "loader\\.sim\\.|loader\\.sim," gym_envs python/rl -S` -> no matches |
| `RTE-004` | `execution_step_runtime_mode="legacy"` | Not default; valid only as a quarantined compatibility opt-in guarded by `runtime_compatibility_enabled=True`. | `quarantine / explicit opt-in` | `WP22-C` | Maintained path fixed to `compiled`; `legacy` only via explicit compat opt-in | `python -m pytest -q tests/runtime/core/test_env_config.py -k runtime_mode && python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_step_runtime_mode or runtime_compatibility"` |
| `RTE-005` | `CMO_EXECUTION_STEP_RUNTIME` / `set_execution_step_runtime_mode(None)` | Silent global legacy selection is removed; `None` normalizes to `compiled`, loader init explicitly sets `compiled`, and the env/None-setter scan is empty. | `pass for silent-selection removal` | `WP22-C` | Explicit parameter/fixture only; no env-silent runtime selection | `rg -n "CMO_EXECUTION_STEP_RUNTIME|set_execution_step_runtime_mode\\(None\\)" gym_envs python tests -S` -> no matches |
| `RTE-006` | `compatibility_fallback_world_batch_step_worlds_wp16c` | Non-default fallback retained only as a named compatibility cadence path and guarded by tests. | `quarantine / explicit fallback` | `WP22-C` | `RuntimeFacade.run_wp10_window()` maintained path; fallback remains opt-in/diagnostic only | `python -m pytest -q tests/world_batch/test_single_world_batch_runtime.py -k compatibility_fallback` |
| `RTE-007` | `terrain_type` non-legacy default | Terrain source, compiler metadata, runtime apply, facade setup, and world-batch setup now share explicit non-legacy default ownership. Missing/blank terrain resolves to `flat` with `default_mainline`; explicit legacy terrain is named compatibility. | `pass for setup/type/schema slice` | `WP22-C` with `WP22-D` dependency | Explicit schema value or synchronized non-legacy default enum | `cmake --build build-workshop --target ef_py -j4 && bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "terrain or world_setup or setup"` |
| `PY-001` | `leader_tasking.py` hardcoded `_air_profile.build_kernel_mission_command(loader)` | Maintained path retired; `leader_tasking` now routes kernel mission-command build through the bridge. | `pass for maintained-business scope` | `WP22-B` | `tasking_bridge.build_kernel_mission_command(loader)` | `python -m pytest -q tests/architecture/command_tasking/test_tasking_bridge_guardrails.py -k kernel_dispatch` |
| `PY-002` | `leader_tasking.py` direct `loader.sim.*` writes | Maintained tasking raw writes retired; raw synchronization is centralized behind `LoaderOwnedRawSimCompatibilityFacade` and the production `loader.sim` scan is empty. | `pass for maintained-business scope` | `WP22-B` with `WP22-C` guard ownership | Facade/tasking-bridge setters and named compatibility seam | `rg -n "loader\\.sim\\." python/rl/tasking python/rl/runtime gym_envs -S` -> no matches |
| `PY-003` | Raw truth read via `get_agent_observation()` | Maintained policy reads now route through loader-owned policy observation/instrument seams instead of direct raw truth helpers. | `pass for maintained-business scope` | `WP22-B` with `WP22-C` coordination | Observation/information-state facade / loader-owned policy seams | `python -m pytest -q tests/architecture/command_tasking/test_tasking_bridge_guardrails.py -k policy_state_reads` |
| `PY-004` | Raw `loader.mission_cmd` dict patterns | Maintained tasking/runtime-state consumers use typed mission-command helpers and views; raw `mission_cmd` dict remains a scenario-loader compatibility payload, not a tasking bypass. | `pass for maintained-business scope / compatibility payload remains` | `WP22-B` with shared loader/runtime-state coordination | Typed `MissionCommand` adapter / DTO | `python -m pytest -q tests/architecture/command_tasking/test_tasking_bridge_guardrails.py -k typed_mission_command_helpers` |
| `PY-005` | `common_core_profile.py` air/default coupling and `ef_py` injection | Air-only default/profile helpers are retired from the maintained common-core layer; production `ef_py =` monkey-patching is banned by guard. | `pass for maintained-business scope` | `WP22-B` | Bridge-owned profile dispatch and import boundary | `python -m pytest -q tests/architecture/command_tasking/test_tasking_bridge_guardrails.py -k common_core_profile` |
| `L-001` | `legacy_command.h` and `MovementCommand` / `ActionCommand` / `LaggedCommand` | Maintained C++ mainline path; audit consumer count understated. | `migrate` | `WP22-D` | `PilotAction`, `MissionCommand`, single command-resolution bridge | `rg -n "legacy_command\\.h|MovementCommand|ActionCommand|LaggedCommand" src/systems src/components tests` |
| `L-001a` | `control_input_resolution.h` partial bridge | Centralizes some fallback, not unique entrypoint. | `quarantine` | `WP22-D` | Single bridge-owned compatibility shim | `rg -n "active_legacy_movement_command|resolved_pilot_or_legacy_throttle|resolve_pilot_or_legacy_ground_control" src tests` |
| `L-001b` | Spawn-time seeding of legacy command state | Aircraft spawn legacy command seeding is quarantined in `default_factory_legacy_spawn_compat.h`; `default_unit_factory.h` calls the named helper and no longer direct-includes `legacy_command.h`. The helper now also seeds `MissionCommandControlState`, but still materializes `MovementCommand` / `LaggedCommand` as compatibility mirrors. | `partial / guarded quarantine` | `WP22-D` | Neutral `PilotAction` plus typed control-state seed; legacy DTOs must remain mirror-only or be deleted where safe | `python -m pytest -q tests/architecture/platform_spawn/test_default_factory_legacy_seed_guard.py tests/architecture/compatibility_quarantine/test_guard_enforcement.py -k "legacy_command or default_factory or command"` |
| `A-001` | `WorldSpawnRequest.type_name` / `spawn_unit(type_name)` maintained typed setup blocker | Maintained typed setup now consumes the maintained validator and materializes through a batch-owned typed helper without rebuilding `WorldSpawnRequest`; explicit legacy compatibility setup remains named separately. | `pass for maintained typed setup / compatibility branch remains` | `WP22-D` with `WP22-C` coordination | Keep `typed_platform_spawn_requests` first-class and preserve explicit legacy compatibility path separation. | `python -m pytest -q tests/architecture/platform_spawn/test_runtime_setup_consume_bridge.py tests/architecture/platform_spawn/test_boundary_guards.py tests/runtime/facade/test_runtime_facade.py -k "typed_platform_spawn or world_setup or setup"` |
| `S-001` | Flat aggregate DTO shells | `MissionCommand`, `TaskOrder`, `LeaderIntent`, and `PilotReport` remain present, but are now explicitly marked as compatibility transport shells with owner-slice projection helpers; world-batch assignment wrappers are guarded as transport-only. This is guard/quarantine, not retirement. | `migrate / guarded quarantine` | `WP22-D` with `WP22-E` coordination | Domain/lifecycle-specific slices or variant DTOs consumed by maintained code | `python -m pytest -q tests/architecture/command_tasking/test_dto_domain_shell_guard.py && rg -n "struct .*: .*Air, .*Naval|World(MissionCommand|TaskOrder|LeaderIntent|PilotReport)Assignment|get_.*_batch|set_.*_batch" src tests` |
| `S-002` | Air recovery/takeoff duplication | Fields duplicated across three DTO stages. | `migrate` | `WP22-D` | Shared air slice plus bridge-owned projection rules | `rg -n "recovery_base_id|recovery_runway_id|recovery_approach_type|takeoff_procedure_id|takeoff_clearance_id|takeoff_interval_s|runway_slot_id|formation_" src/components/command src/components/tasking tests` |
| `S-003` | Naval DTO asymmetry | Asymmetric lifecycle splits still bleed through aggregate DTOs. | `migrate` | `WP22-D` | Explicit naval-stage DTOs and projection rules | `rg -n "MissionCommandNaval|TaskOrderNaval|LeaderIntentNaval|PilotReportNaval|warfare_role_code|officer_in_tactical_command|reference_entity_id|launch_helo|recover_helo" src/components tests` |
| `F-001` | `counterfactual_replay_contracts.h` | Entry header is now a 130-line umbrella, and the former 1643-line validation follow-up has been split into a 4-line validation umbrella plus replay/counterfactual/experiment/helper validation family headers. | `pass for validation-family split` | `WP22-E` | Keep validation family ownership explicit and prevent umbrella regression. | `wc -l src/runtime/contracts/counterfactual_replay_contracts.h src/runtime/contracts/counterfactual_replay_contract_validation.h src/runtime/contracts/counterfactual_replay_*validation*.h` |
| `F-002` | `runtime_facade.cpp` | Large mixed TU still combines spawn, counterfactual, export, window, and compatibility surfaces; latest local line count is `2951`. | `migrate` | `WP22-E` with `WP22-C` dependency | Split into core/spawn/counterfactual/export/window files | `wc -l src/runtime/facade/runtime_facade.cpp && rg -n 'RuntimeFacade::runtime\\(|using namespace runtime::counterfactual|run_counterfactual|run_wp10_window|export_engagement_event_packet' src/runtime/facade/runtime_facade.cpp` |
| `F-003` | `runtime_window_coordinator.h` | Entry header is now 405 lines and delegates selection/callback/cadence/execution helpers to named companion headers. | `migrate / pass for entry-header slice` | `WP22-E` | Keep helper ownership explicit and prevent regression above threshold. | `wc -l src/runtime/facade/runtime_window_coordinator.h src/runtime/facade/runtime_window_coordinator_*.h` |
| `F-004` | `default_unit_factory.h` / `default_factory_legacy_spawn_compat.h` | Still a large mixed factory header. Spawn now seeds a typed `MissionCommand` shell before projecting the remaining compatibility seed, but `default_factory_legacy_spawn_compat.h` still includes `legacy_command.h` and owns behavior-bearing `MovementCommand` / `LaggedCommand` projection. | `partial / typed-seed reduction` | `WP22-E` with `WP22-D` dependency | Replace the `MovementCommand` / `LaggedCommand` projection with typed command-control state before claiming retirement. | `wc -l src/models/core/default_unit_factory.h src/components/command/default_factory_legacy_spawn_compat.h && python -m pytest -q tests/architecture/platform_spawn/test_default_factory_legacy_seed_guard.py` |
| `F-005` | Large mixed runtime contract headers | `9/11` large headers carry mixed responsibilities. | `migrate` | `WP22-E` with `WP22-C/D` dependency | `*_constants.h`, `*_types.h`, `*_validation.cpp` | `find src/runtime/contracts -maxdepth 1 -name '*.h' -print0 | xargs -0 wc -l | sort -n` |
| `L-002` | `RuntimeFacade.runtime()` / `WorldBatchRuntime::world()` raw access | Maintained facade internals no longer drill through public raw accessors; `runtime()` / `world()` remain explicit compatibility/diagnostics escape hatches. | `pass for maintained facade internals / quarantine remains` | `WP22-C` | Facade-owned narrow methods; keep raw access opt-in only | `python -m pytest -q tests/architecture/runtime_facade -k "runtime_facade_cpp_maintained_paths_do_not_drill_through_raw_runtime_or_world"` |
| `A-002` | Implicit ECS order via registration order and manual loops | `PilotWeaponRelease` and naval mission weapon release now both register through named helper systems; the manual post-`step()` naval query loop is absent. | `pass for naval fire-loop seam` | `WP22-E` with `WP22-D` dependency | Keep helper-system ordering guards; broader phase/dependency work is future structural debt. | `python -m pytest -q tests/architecture/structural_boundaries tests/runtime/naval -k "weapon or mission or fire"` |
| `S-004` | `WorldBatchRuntime` fat surface | `41` public methods across at least seven responsibilities. Visual-binding compatibility scene assembly and setup orchestration have been extracted into private helpers, but public raw `world()` and broader setup/command/episode/query responsibilities remain. | `migrate / scoped service split pass` | `WP22-E` with `WP22-C` dependency | Continue extracting setup/command/episode/query services without changing public raw-world compatibility semantics. | `python -m pytest -q tests/architecture/runtime_facade -k "world_batch_runtime or gpu_visual_binding or visual_binding_raw_world_access or escape_hatch"` |
| `S-005` | Broad `SimulationKernel` Python bindings | `75` direct `.def` bindings remain. `bindings_core.cpp` registration is separated by role, and maintained binding entity reads now use kernel-owned query methods rather than local raw ECS lookup. Diagnostics and legacy blocks still raw-drill intentionally. | `quarantine / maintained seam pass` | `WP22-E` with `WP22-C` dependency | Reduce broad public binding surface or migrate maintained APIs toward facade/kernel-owned methods while keeping debug/legacy quarantined. | `python -m pytest -q tests/architecture/structural_boundaries -k "bindings"` |
| `S-006` | Inline `PilotWeaponRelease` `OnUpdate` exception | The inline exception is retired for this slice; registration now delegates to `register_pilot_weapon_release_system(ecs, *this)`. | `pass for ordering residual slice` | `WP22-E` with possible `WP22-D` dependency | Dedicated combat helper system plus guard preventing inline regression | `rg -n 'PilotWeaponRelease|register_pilot_weapon_release_system' src/core/engine/simulation_kernel_systems.cpp src/systems` |

## First-Wave Implementation Outcomes

| Stream | Local result | Evidence summary | Implication |
|--------|--------------|------------------|-------------|
| `WP22-B` | `historical blocked, superseded by later pass` | Earlier `leader_tasking` path was blocked by raw truth/instrument replacement. Later WP22-B packets retired the maintained-business path and moved raw-loader ownership to the C/F guard lane. | Keep the historical blocker only as provenance; do not reopen maintained-business blocker semantics. |
| `WP22-C` | `historical partial, superseded for RTE-003/RTE-005/RTE-007` | Earlier runtime opt-in/quarantine tests passed while raw-loader seams and setup ownership remained open. Russell, Bernoulli, and Hubble later closed production raw-loader cleanup, silent-selection removal, and setup/type/schema ownership. | Current C lane is `L-002` raw facade/world access plus guard follow-up for explicit compatibility surfaces. |
| `WP22-D` | `historical blocked, superseded by later passes for command bridge and A-001` | Air-control bridge initially landed while broader consumers remained. Later guard work migrated/quarantined legacy command consumers behind bridge/default-factory seams, and A-001 promoted maintained typed setup. | Remaining D work is default-factory typed control-state replacement and aggregate DTO/domain shell retirement, not the old direct-sim or A-001 blocker. |
| `WP22-E` | `historical partial, superseded for entry-header and PilotWeaponRelease slices` | Constants/helper split and structural guard landed; later Carver/Noether/Parfit closed the entry-header and inline weapon-release slices. | Structural decomposition can continue on validation split, runtime facade TU, broad bindings, default factory, and naval fire-loop ordering. |
| `WP22-F` | `not eligible` | No closure evidence yet; it can only consume a locked-down B-E evidence set. | Serial closure stays deferred. |

## Parallel Readiness

| Stream / item set | Readiness | Rule |
|-------------------|-----------|------|
| `WP22-C`: `RTE-001`, `RTE-002`, `RTE-004`, `RTE-005`, `RTE-006` | `ready` | Quarantine/guard work can start now from verified runtime evidence. |
| `WP22-D`: `L-001`, `L-001a`, `L-001b`, `S-001`, `S-002`, `S-003` | `ready with coordination` | Can start, but public boundary flips must coordinate with `WP22-C` and structural follow-on. |
| `WP22-E`: `F-001`, `F-003`, `F-005`, `S-005`, `S-006` | `ready with guard discipline` | Structural splits/quarantines can start if public boundary ownership does not drift. |
| `WP22-B`: `PY-001` to `PY-005` | `source-verified retired for maintained-business scope` | `WP22-B` now passes for maintained-business retirement; the remaining import-time `ef_py.TaskOrder` unlock in `command_chain_cache` is a validation-only C/F guard-lane follow-up. |
| `RTE-003` | `pass for production raw-loader cleanup` | Production `loader.sim.*` / `loader.sim,` scan is now empty; only explicit test/guard strings remain. |
| `RTE-007` | `pass for setup/type/schema slice` | Source, rebuilt binding verification, facade setup, world-batch setup, compiler metadata, and runtime apply now agree on non-legacy default ownership. |
| `A-001` | `scoped pass` | Maintained facade execution now consumes the maintained typed setup validator and batch-owned typed spawn helper; explicit compatibility branch remains separate. |
| `F-002` | `dependency-gated` | Must not race against `WP22-C` on `runtime_facade.cpp` public/raw-access lines. |
| `F-004` | `partial / seed seam pass` | Legacy command seed ownership is quarantined; broader factory split remains structural debt. |
| `L-002` | `scoped pass / quarantine remains` | Maintained facade internals and direct GPU binding raw-world access no longer drill through public raw world access; public `runtime()` / `world()` escape hatches remain compatibility/diagnostics only. |
| `A-002` | `scoped pass` | Naval post-step fire loop is retired into a named helper system; broader execution-phase design remains future structural debt. |
| `S-004` | `dependency-gated` | World-batch service split depends on `WP22-C` finalizing maintained facade/query boundaries. |

## Seventh-Wave Verification Round

| Stream | Status | Evidence summary | Implication |
|--------|--------|------------------|-------------|
| `Pauli` | `pass` | Aggregate command/tasking DTOs and world-batch assignment wrappers are now explicitly marked as compatibility transport shells with owner-slice projection helpers; focused DTO/shell guards and `ef_py` build pass. | `S-001` is guarded but not retired; next work must migrate maintained consumers to owner slices or domain-specific DTOs. |
| `Ramanujan` | `pass` | `bindings_core.cpp` registration is split by maintained/diagnostics/legacy role, and architecture guards ensure maintained/override helper blocks do not directly spell `self.get_world().entity(...)`; focused binding guards and `ef_py` build pass. | `S-005` is better quarantined but still broad; next work should reduce maintained raw-entity seams or move maintained queries behind kernel-owned methods. |
| `Beauvoir` | `preflight-only` | Repo-level non-test Python `batch_runtime` consumer guard now scans outside the explicit compatibility/diagnostics allowlist; docs and audit summary keep `WP22-F` not eligible with `0` acceptance reviews. | Guard hardening does not retire public escape hatches; `WP22-F` remains blocked. |

## Eighth-Wave Verification Round

| Stream | Status | Evidence summary | Implication |
|--------|--------|------------------|-------------|
| `Harvey` | `partial` | Default-factory spawn now seeds a typed `MissionCommand` shell and projects compatibility commands from `MissionCommandCore`; focused guards, mission/naval tests, and `ef_py` build pass. | `F-004/L-001b` remains blocked by behavior-bearing `MovementCommand` / `LaggedCommand` projection. Next work must inventory and replace that typed control path. |
| `Banach` | `pass` | Maintained binding reads moved to kernel-owned query methods; local `lookup_entity(...)` is gone from `bindings_core.cpp`; focused binding guards and `ef_py` build pass. | `S-005` maintained raw-entity seam is closed for this slice; broad binding count and diagnostics/legacy raw ECS remain open. |
| `Planck` | `pass` | Visual-binding compatibility scene assembly moved into a private helper; runtime facade layering guards and `ef_py` build pass. | `S-004` has one service seam extracted, but `WorldBatchRuntime` remains fat and public raw `world()` remains quarantined. |

## Ninth-Wave Verification Round

| Stream | Status | Evidence summary | Implication |
|--------|--------|------------------|-------------|
| `Maxwell` | `pass` | Added `src/core/engine/world_batch_setup_helper.h`; `WorldBatchRuntime::apply_world_setup_batch` setup orchestration and terrain/wind/zone/reset seed resolution now run through a private helper. | `S-004` gained a second service seam, but public `WorldBatchRuntime::world()` remains a compatibility/diagnostics escape hatch and `WP22-F` stays not eligible. |
| `Hooke typed-control inventory` | `pass / read-only` | No files edited. Inventory identified `default_factory_legacy_spawn_compat.h`, `operation_system.h`, and `control_system.h` as the smallest first implementation seam, and recommended `MissionCommandControlState` beside `MissionCommandCore`. | Enables the Meitner implementation dispatch, but does not itself retire `MovementCommand` / `LaggedCommand`. |
| `Poincare docs cleanup` | `partial / no edits` | Stopped after discovery; no audit or diff-check was run in the packet. | Main thread owns minimal queue/ledger sync; no closure evidence. |
| `Meitner typed-control implementation` | `partial / main-thread repaired` | Worker stopped unvalidated after adding `MissionCommandControlState` and routing operation/control/default-control toward it. Main thread fixed `CommandLag` lagged initialization so it no longer overwrites freshly written targets, then reran focused architecture guards `21 passed`, mission/naval/link tests `18 passed`, `ef_py` build, and `git diff --check`. | This was not retirement by itself; it exposed the ingress/link gap consumed by the tenth wave. |
| `Descartes typed-control fact verification` | `partial / read-only` | No files edited. Confirmed typed state was still a source-of-truth island and identified command ingress/link plus default-factory compatibility projection as remaining blockers. | Read-only blocker evidence only; not closure. |
| `Averroes typed ingress/link sync` | `pass` | Non-ship immediate `set_unit_command` and deferred `CommandLinkMovement` now update `MissionCommandControlState` first and refresh legacy mirrors afterward; stick command is named as a quarantined legacy-only DTO write. Main-thread recheck: `ef_py` build passed, runtime mission/naval/link suite `19 passed`, `git diff --check` clean. | `PendingMovementCommand`, legacy movement debug, stick DTO compatibility, `ActionCommand` / `PendingActionCommand`, downstream mirror consumers, and default-factory compatibility projection remain open. |
| `Parfit typed-control guard hardening` | `pass` | Architecture guards now anchor default-factory helper as compatibility-only with typed-state seeding, require command ingress to use bridge helpers, and guard the bridge typed-state mirror helpers. Main-thread recheck: default-factory/WP9/structural suite `21 passed`, `git diff --check` clean. | Guard hardening is not closure; it prevents regression while the remaining compatibility seams are migrated. |
| `Copernicus forced-retirement fact check` | `partial / read-only` | No files edited. Confirmed `WP22-F eligibility = no` and re-anchored live legacy movement mirrors, pending command transport shells, debug legacy movement hooks, and default-factory projection. | Read-only blocker evidence only; not closure. |
| `Gauss default-factory typed control-state ownership` | `pass` | Spawn default ownership is now explicitly `MissionCommandControlState`; legacy movement/lagged mirrors are projected at apply time rather than stored in the seed struct. Main-thread recheck with Dalton patch: `ef_py` build passed, architecture suite `21 passed`, runtime mission/naval/link suite `19 passed`, `git diff --check` clean. | Scoped semantic narrowing only; mirrors remain live because downstream consumers still require them. |
| `Dalton command mirror consumer migration` | `partial` | `control_input_resolution.h` and `force_system.h` moved toward state-first consumer resolution; the patch is locally buildable and passes focused architecture/runtime gates after main-thread recheck. | `propulsion_system.h`, `instrument_system.h`, and `ground_contact_system.h` still lack typed throttle/brake semantics; embarked-air, debug/pending transport, operation/link mirrors remain open. |
| `Boole debug/pending transport narrowing` | `pass` | Debug legacy movement setter now syncs through bridge helpers, and legacy/pending getters are labeled diagnostics mirror or diagnostics transport shell. Main-thread recheck passed runtime/architecture/build/diff gates. | Debug and pending surfaces still exist as diagnostics/transport shells; not deletion. |
| `Hume embarked-air state-first write-chain` | `pass` | Launch/recover writes no longer depend on a pre-existing `MovementCommand*`; bridge helpers materialize typed state and mirrors as needed. Main-thread recheck passed runtime/architecture/build/diff gates. | Remaining command-control blockers are outside embarked-air: command-link, operation, default-factory projection, and DTO/runtime surfaces. |
| `Curie air-control typed resolver` | `partial / main-thread repaired` | Curie left instrument and ground-contact on raw source-pointer branches; main thread wired physics consumers to consume `ResolvedAirControlInput` from the bridge. Main-thread recheck: architecture suite `23 passed`, runtime suite `20 passed`, `ef_py` build passed, `git diff --check` clean. | Throttle/brake are still compatibility fallback inside the bridge because `MissionCommandControlState` has no throttle/brake owner. This is scoped narrowing, not full command retirement. |
| `Bohr operation-system mirror quarantine` | `pass` | Operation local legacy seed/refresh helpers moved behind bridge-owned helpers; main-thread recheck passed architecture, mission runtime, build, and diff-check. | Operation system signatures still carry legacy mirror components; not deletion. |
| `Schrodinger default-factory projection fact check` | `blocked / read-only` | No files edited. Confirmed spawn-time `MovementCommand` / `LaggedCommand` projection cannot be deleted yet. | Blocking consumers remain in air-control bridge fallback, operation mirrors, command-link delivery, and movement readers. |

Local validation: runtime facade layering focused guard `10 passed, 26 deselected`; world_batch setup focused tests `3 passed, 21 deselected`; `cmake --build build-workshop --target ef_py -j4` passed; `git diff --check` clean.

## Blockers

| ID | Blocking surface | Why blocked | Required next step |
|----|------------------|-------------|--------------------|
| `PY-B0-001` | Source-verified Python bypass set | `WP22-B0` returned `status: blocked`, `touched files: none`; all five `PY-001` through `PY-005` kill-list items were live at source-pass time, but `WP22-B` has now cleared maintained-business retirement. | The remaining import-time `ef_py.TaskOrder` unlock in `command_chain_cache` is validation-only under the C/F guard lane; do not re-open maintained-business blocker semantics. |

## Second-Wave Results

| Stream | Local result | Evidence summary | Implication |
|--------|--------------|------------------|-------------|
| `WP22-B` | `pass` | Policy-read seam landed, `common_core_profile` and `loading.py` are compatibility-only guard surfaces, and the raw sim seam now belongs to the C/F compatibility guard lane. WP22-specific tests pass. | Maintained-business retirement is complete; remaining import-time `TaskOrder` validation is C/F lane follow-up. |
| `WP22-D` | `pass` | Legacy command consumers have been migrated or quarantined behind the bridge; the direct-include allowlist is now limited to the specific bridge/default-factory seams. WP22-specific tests pass. | Command DTO and legacy-surface retirement can proceed into the third-wave documentation sync and guard cleanup, but not acceptance yet. |
| `Validation sweep` | `pass` | WP22-specific tests pass, and the aggregate sweep now passes after WP16/WP20 drift cleanup. | Drift cleanup is complete; fourth-sync follow-up now focuses on the TaskOrder import unlock, the RTE-003/RTE-007 next slice, and documentation sync. |
| `WP22 overall complete?` | `open` | B and D are complete packets; C and E remain open, and F is not eligible. | Closed threads are transport only, not completion evidence. |

## Current Verification Round

| Stream | Status | Evidence summary | Implication |
|--------|--------|------------------|-------------|
| `Zeno` | `pass` | Restored the datalink command cleanup variable, rebuilt `ef_py`, and verified terrain/setup slices: `7` passed across focused facade/world-batch commands. | The previous `data_link_system.h:284` build blocker is closed. |
| `Tesla` | `partial` | Runtime reward/info call sites in `python/rl/runtime` now use named loader-backed seams, and focused runtime tests pass. Repo-level raw loader seams remain outside the bounded slice. | Do not upgrade `RTE-003` to pass; dispatch narrower residual seams next. |
| `Arendt` | `pass` | Documentation sync was complete when returned, but it predated Zeno's build fix and therefore required this factual correction. | Documentation sync is accepted only after this correction; no acceptance review is created. |

## Follow-Up Verification Round

| Stream | Status | Evidence summary | Implication |
|--------|--------|------------------|-------------|
| `Russell` | `pass` | Production `loader.sim.*` / `loader.sim,` scan is empty; runtime facade guard, WP22 tasking bridge guard, and focused mission/execution tests passed in the return packet. | `RTE-003` can be consumed as scoped pass for production raw-loader cleanup. |
| `Bernoulli` | `pass` | Silent env/default legacy selection is removed; `legacy`, `batch_runtime`, raw runtime fallback, and fallback cadence remain explicit compatibility opt-ins with focused tests passing. | `RTE-005` can be consumed as scoped pass; `RTE-001/002/004/006` remain guarded compatibility surfaces. |
| `Parfit` | `pass` | `PilotWeaponRelease` now registers through `register_pilot_weapon_release_system(ecs, *this)`; structural/WP9 guards and `ef_py` build passed in the packet. | `S-006` can be consumed as scoped pass for the pilot helper-system slice. |
| `Raman` | `done` | Queue sync recorded scoped passes and kept `WP22-F` ineligible; doc closure audit still reports `0` canonical acceptance reviews and `8/8` zh peers. | Documentation sync is accepted only as status tracking, not closure evidence. |

## Fifth-Wave Verification Round

| Stream | Status | Evidence summary | Implication |
|--------|--------|------------------|-------------|
| `Hooke` | `pass` | Maintained facade internals now use facade/batch-owned narrow methods; `ef_py` build, runtime facade layering guard, and runtime facade tests pass. | `L-002` can be consumed as scoped pass for maintained facade internals; repo-level diagnostics residuals remain allowlisted follow-up. |
| `Socrates` | `pass` | Default factory legacy seed moved behind `SpawnCompatibilityLegacyCommandSeed`; default-factory/WP9 guards pass. | `L-001b/F-004` seed ownership is quarantined; typed control-state replacement remains future work. |
| `Epicurus` | `blocked, superseded by main-thread follow-up` | Contract-level maintained typed setup evidence and blocker guards landed, but runtime facade maintained execution was outside that worker's write scope. | Follow-up implementation closed A-001 in the maintained facade path; keep Epicurus as provenance, not current blocker. |
| `Main-thread A-001 follow-up` | `pass` | Maintained typed setup now validates via `validate_maintained_typed_platform_spawn_request(...)`, materializes through `WorldBatchRuntime::spawn_typed_platform_unit(...)`, exposes `setup_surface` to Python, and passes focused setup/facade guards. | `WP22-F` is still not automatic; remaining residuals are default-factory control-state replacement, aggregate DTO shells, compatibility/diagnostics escape hatches, and structural/binding debt. |
| `Pascal` | `pass` | Direct GPU visual binding raw-world access moved behind `WorldBatchRuntime::collect_visual_binding_compatibility_scenes_batch(...)`; build, architecture guard, and focused GPU binding test pass. | Public raw world access remains compatibility/diagnostics; broad world-batch service split remains open. |
| `Bohr` | `pass after main-thread behavior-preservation fix` | Default factory legacy seed ownership moved to `default_factory_legacy_spawn_compat.h`; `default_unit_factory.h` no longer direct-includes `legacy_command.h`; build and focused guards pass. | Typed control-state/default initialization replacement remains open. |
| `Poincare` | `timeout/shutdown` | Closure preflight returned no complete packet. | No closure evidence; `WP22-F` remains not eligible. |
| `Hume` | `pass` | Naval post-step manual query loop moved into `register_naval_mission_weapon_release_system(ecs, *this)`; structural/naval/build checks pass. | `A-002` can be consumed as scoped pass for naval fire-loop ordering seam. |
| `Mencius` | `pass after integration recheck` | Counterfactual validation monolith split by family; initial build blocker cleared by Hooke; structural/build checks pass. | `F-001` validation-family split can be consumed as scoped pass. |
