# Default Effects Modularization Task Clusters

Status: `2026-06-02 finite task-cluster plan / DFM-P3F structure-spatial helper pass / paused`.

Parent subproject:

- [README.md](README.md)
- [README.zh.md](README.zh.md)
- [Closure sync](default_effects_modularization_closure_sync_20260602.md)

## Boundary Decision

This task list may restructure private implementation code under
`src/models/weapons/default_effects_model.cpp` and
`src/models/weapons/detail/`. It must preserve formulas, RNG behavior,
component row pointer lifetimes, result fields, and existing public contracts.

This task list must not claim broader A2 maturity, stock runtime authority, Pk
authority, deterministic fuze release, or industrial admission.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `DFM-P0` | main thread | n/a | Create the subproject surface and freeze the finite task list. | `docs/task/air_combat/a2_high_fidelity_damage_model/default_effects_modularization/**`, parent A2 README entries | No code behavior changes. | Markdown link/path review; `git diff --check` for touched docs. | README, task clusters, status doc, and parent links exist. | Serial; gates all future dispatch. | 1 | pass |
| `DFM-P1` | main thread | n/a | Split direct hit, spatial projection, air resolution, state, result, geometry, warhead, component, and legacy helpers into private detail fragments. | `src/models/weapons/default_effects_model.cpp`, `src/models/weapons/detail/*.inc`, `src/models/weapons/README*` | No public API split; no formula changes. | `cmake --build build --target ef_core -j2`; runtime guard. | Build and runtime guard pass; helper linkage remains local. | Completed before this baseline; later edits must not reopen scope silently. | 2 | pass |
| `DFM-P2` | main thread or integration worker | inherited / xhigh for worker | Consolidate repeated component-scale and warhead-sample scratch update logic. | `src/models/weapons/detail/default_effects_warhead_detail.inc`, `default_effects_state_detail.inc`, `default_effects_direct_hit_detail.inc`, `default_effects_spatial_projection_detail.inc` | No behavior tuning; no new evidence authority strings. | `cmake --build build --target ef_core -j2`; runtime guard. | Shared helpers are used and pass existing tests. | Depends on `DFM-P1`; serial with direct/spatial edits. | 2 | pass |
| `DFM-P3` | Gibbs worker (`019e840c-2ad1-75d0-97ff-d3f5b3121586`); Curie worker (`019e842a-9b61-7960-9d11-81763304e738`) | inherited / xhigh | Further split air-platform resolution internals into named helper stages. | `src/models/weapons/detail/default_effects_air_platform_resolution_detail.inc` | Do not alter consequence coefficients or loss-state semantics. | `cmake --build build-local-win --target ef_core -j2`; full runtime guard. | Mechanism-load fallback, scale aggregation, platform-only consequence, propulsion/fuel consequence, fire-zone consequence, finalize, and any future consequence helpers compile with unchanged tests. | Depends on `DFM-P2`; current implementation budget is spent after Gibbs and Curie, so further source workers require a new re-baselined row. | 2 | pass / propulsion-fuel helper accepted |
| `DFM-P4` | Ohm worker (`019e83ce-25d8-7170-82c0-b3c856cea1d3`); Cicero fixture worker (`019e840c-e0a9-7c91-937d-226f388d4912`) | inherited / xhigh | Add narrow regression fixtures for direct and spatial behavior paths, then probe the held structured air-platform early-return fixture. | `tests/runtime/air_combat/weapon_guidance_realism/default_effects_modularization.py`; `tests/runtime/air_combat/test_weapon_guidance_realism_guards.py` only for mixin wiring | Do not introduce a project-wide C++ test framework; do not edit `src/` or docs in this worker. | Fixed-RNG tests for direct component, direct protected-system fallback, broad spatial, non-broad component spatial, and structured air-platform loss/destruct early return. | Fixtures pass and document exact covered behavior. | Fixture worker was parallel-safe with `DFM-P3` because it owned tests only and returned a packet. | 2 | pass / early-return fixture accepted |
| `DFM-P5` | Lovelace diagnostics (`019e83ce-b49b-7773-a449-71e916f89d7f`) | inherited / xhigh | Read-only fixture-design and behavior-risk review for `DFM-P4` round 1. | none | No edits. | Static code review plus reported risks and test gaps. | Packet reports `pass` or concrete findings. | Ran parallel with `DFM-P4`; did not replace local build/test gates. | 1 | pass |
| `DFM-P5B` | Feynman diagnostics (`019e842b-5927-7a92-ae65-fff4fab5f21d`) | inherited / xhigh | Read-only equivalence and next-slice review for the active `DFM-P3` continuation. | none | No edits; no implementation evidence. | Static source review and recommended validation checklist. | Packet reports integration risks, next slice, and whether more fixtures are needed. | Ran in parallel with Curie because it was read-only. | 1 | pass |
| `DFM-P3B` | Ramanujan worker (`019e8441-3a03-7012-8888-30f64fec5927`); Darwin diagnostics (`019e8441-ef53-7fe0-9707-03d9ce2daec1`) | inherited / xhigh | Re-baselined follow-on helper extraction for remaining sensor/control/crew aircraft consequence blocks; accepted slice owns sensor/avionics only. | `src/models/weapons/detail/default_effects_air_platform_resolution_detail.inc` for Ramanujan; diagnostics is read-only | No formula, coefficient, RNG, result field, authority string, public contract, or derive/clamp/apply-to-platform reorder changes. | `git diff --check`; `cmake --build build-local-win --target ef_core -j2`; `cmake --build build-local-win --target ef_py -j2`; `test_weapon_guidance_realism_guards.py -k dfm_p4`; full guard. | Sensor/avionics helper passes full guard and docs record that no additional fixture is needed. | Serial after `DFM-P3` acceptance; TM04/TM05 worktree state is unrelated and not a blocker for this DFM lane. | 2 | pass / sensor helper accepted |
| `DFM-P3C` | Ramanujan worker (`019e8441-3a03-7012-8888-30f64fec5927`); Darwin diagnostics (`019e8441-ef53-7fe0-9707-03d9ce2daec1`) | inherited / xhigh | Extract one source-only helper for aircraft lateral-fuel-storage, hydraulic-supply, and flight-control consequence blocks. | `src/models/weapons/detail/default_effects_air_platform_resolution_detail.inc` for Ramanujan; diagnostics is read-only | No formula, coefficient, RNG, result field, authority string, public contract, or derive/clamp/apply-to-platform reorder changes. | `git diff --check`; `cmake --build build-local-win --target ef_core -j2`; `cmake --build build-local-win --target ef_py -j2`; `test_weapon_guidance_realism_guards.py -k dfm_p4`; full guard. | Control/hydraulic helper slice passes build plus runtime guard and returns a packet. | Serial after `DFM-P3B` acceptance; do not edit docs or tests in the worker. TM04/TM05 remains unrelated. | 1 | pass / control-hydraulic helper accepted |
| `DFM-P3D` | Ramanujan worker (`019e8441-3a03-7012-8888-30f64fec5927`); Darwin diagnostics (`019e8441-ef53-7fe0-9707-03d9ce2daec1`) | inherited / xhigh | Extract one source-only helper for aircraft pilot, mission-crew, command-navigation, and generic crew fallback consequence blocks. | `src/models/weapons/detail/default_effects_air_platform_resolution_detail.inc` for Ramanujan; diagnostics is read-only | No formula, coefficient, RNG, result field, authority string, public contract, or derive/clamp/apply-to-platform reorder changes. | `git diff --check`; `cmake --build build-local-win --target ef_core -j2`; `cmake --build build-local-win --target ef_py -j2`; `test_weapon_guidance_realism_guards.py -k dfm_p4`; full guard. | Crew-role helper slice passes build plus runtime guard and returns a packet. | Serial after `DFM-P3C` acceptance; do not edit docs or tests in the worker. TM04/TM05 remains unrelated. | 1 | pass / crew-role helper accepted |
| `DFM-P3E` | Ramanujan worker (`019e8441-3a03-7012-8888-30f64fec5927`); Darwin diagnostics (`019e8441-ef53-7fe0-9707-03d9ce2daec1`) | inherited / xhigh | Extract one source-only helper for the aircraft-side mission/combat consequence block. | `src/models/weapons/detail/default_effects_air_platform_resolution_detail.inc` for Ramanujan; diagnostics is read-only | No formula, coefficient, RNG, result field, authority string, public contract, or derive/clamp/apply-to-platform reorder changes. | `git diff --check`; `cmake --build build-local-win --target ef_core -j2`; `cmake --build build-local-win --target ef_py -j2`; `test_weapon_guidance_realism_guards.py -k dfm_p4`; full guard. | Mission/combat helper slice passes build plus runtime guard and returns a packet. | Serial after `DFM-P3D` acceptance; do not edit docs or tests in the worker. Keep platform-level mission/combat behavior outside this helper. TM04/TM05 remains unrelated. | 1 | pass / mission-combat helper accepted |
| `DFM-P3F` | main thread | local / xhigh-equivalent review | Verify and accept the aircraft-side structure-spatial consequence helper already present in the current source, then fix the debug early-return validation crash exposed by the accepted fixture. | `src/core/engine/simulation_kernel_damage_debug_api.cpp`; status docs; `src/models/weapons/detail/default_effects_air_platform_resolution_detail.inc` as reviewed evidence | No formula, coefficient, RNG, result field, authority string, public contract, or derive/clamp/apply-to-platform reorder changes. Debug API changes may only use pre-hit target snapshots for event recording. | `git diff --check`; `cmake --build build --target ef_core -j2`; `cmake --build build --target ef_py -j2`; structured early-return fixture; `test_weapon_guidance_realism_guards.py -k dfm_p4`; full guard. | Structure-spatial helper is verified and accepted; debug API no longer reads target components after target destruct. | Serial after `DFM-P3E`; no parallel source worker. | 1 | pass / structure-spatial helper accepted |
| `DFM-P6` | integration worker | inherited / xhigh | Closure sync: update status, parent links, acceptance/residuals, and archive boundary. | subproject docs, parent A2 README entries, `src/models/weapons/README*` if needed | No authority or public API claim. | `git diff --check`; link/path review; build/test evidence copied from current run. | Acceptance and held residuals are explicit; build/test evidence references the current Windows validation path. | Serial after implementation/test clusters. | 1 | pass |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not allow two workers to edit the same source file or normative table concurrently.
- Keep `DFM-P3` serial because air-platform consequence logic has dense coupled coefficients.
- Keep `DFM-P6` serial because closure status must integrate final evidence.
- If a cluster exceeds its round cap, stop and re-scope before adding another wave.
- Follow [Subagent Usage Policy](../../../../standards/governance/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

Implementation packets must also state whether any formula, RNG, authority
string, result field, or public contract changed. The expected answer is "no"
for structure-only clusters.

## Validation Plan

```bash
cmake --build build --target ef_core -j2
cmake --build build --target ef_py -j2
CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
git diff --check -- src/models/weapons/default_effects_model.cpp src/models/weapons/detail src/core/engine/simulation_kernel_damage_debug_api.cpp src/models/weapons/README.md src/models/weapons/README.zh.md docs/task/air_combat/a2_high_fidelity_damage_model/default_effects_modularization
```

## Acceptance Criteria

- `DFM-P0`, `DFM-P1`, `DFM-P2`, `DFM-P3`, and accepted follow-on helper rows
  pass or explicitly hold remaining split residuals.
- `DFM-P4` passes, or fixture gaps are moved to a named held residual with a
  replacement validation path.
- `DFM-P6` syncs parent README links and status language. Current sync is
  recorded in
  [default_effects_modularization_closure_sync_20260602.md](default_effects_modularization_closure_sync_20260602.md).
- No wider realism, authority, Pk, or deterministic-fuze claim is introduced.

## Residual Map

Immediate:

- Keep build and runtime guard green after the platform, sensor/avionics,
  propulsion/fuel, control/hydraulic, crew-role, mission/combat,
  structure-spatial, and fire-zone consequence helper splits.
- Keep accepted `DFM-P4` / `DFM-P5` fixture hardening as the minimum regression
  floor for any further `DFM-P3` extraction.
- Keep the accepted structured air-platform early-return fixture as the
  regression floor for platform-loss/destruct early return.
- Do not send more workers against `DFM-P3`, `DFM-P3B`, `DFM-P3C`,
  `DFM-P3D`, `DFM-P3E`, or `DFM-P3F`; the current task is paused after commit.

Follow-on:

- No default-effects air-platform consequence split remains in this subproject;
  if resumed, create a new finite row with a fresh validation budget.

Deferred:

- Project-wide C++ unit-test framework.
- Public model/plugin API reshaping.
- Authority promotion or industrial admission work.
