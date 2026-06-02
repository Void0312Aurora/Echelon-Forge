# Default Effects Modularization

Status: `2026-06-02 closed / archived / DFM-P3F structure-spatial helper pass`.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent task index: [A2 high-fidelity air-combat damage model](../README.zh.md)
- Agent subproject standard: [subproject_creation_standard.zh.md](../../../../agent/rules/subproject_creation_standard.zh.md)
- Subagent policy: [subagent_usage_policy.zh.md](../../../../standards/governance/subagent_usage_policy.zh.md)
- Triggering assessment: [Echelon Forge comprehensive assessment](../../../../evaluation/echelon_forge_comprehensive_assessment_20260601.zh.md)
- Code surface: [default_effects_model.cpp](../../../../../src/models/weapons/default_effects_model.cpp)

## Purpose

This subproject freezes the task list for structurally splitting and stabilizing
`src/models/weapons/default_effects_model.cpp`. The goal is maintainability:
make the default effects model navigable, keep helper linkage local, preserve
runtime behavior, and create explicit validation gates for future edits.

The subproject does not promote A2 fidelity authority, Pk authority,
deterministic fuze authority, or industrial admission. It only governs the
code-structure and regression task surface for the default effects model.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Main translation unit split | closed-pass | `default_effects_model.cpp` now includes private detail fragments and is reduced to orchestration. | This does not prove physics or vulnerability calibration authority. |
| Direct hit helper | pass | `detail/default_effects_direct_hit_detail.inc`; `DFM-P4` runtime fixtures | Fixed-RNG direct component and protected-system fallback routes are covered by runtime fixtures, not by a C++ golden harness. |
| Spatial projection helper | pass | `detail/default_effects_spatial_projection_detail.inc`; `DFM-P4` runtime fixtures | Broad and non-broad near-miss routes are covered by runtime fixtures. |
| System effect helper | pass | `detail/default_effects_system_effect_detail.inc` | Extracted behavior has build/runtime guard coverage, not line-by-line golden comparison. |
| Air platform resolution helper | pass-for-structure | `detail/default_effects_air_platform_resolution_detail.inc` | Platform-only, aircraft sensor/avionics, aircraft propulsion/fuel, aircraft control/hydraulic, aircraft crew-role, aircraft mission/combat, aircraft structure-spatial, and aircraft fire-zone consequence blocks now have named helpers. |
| Verification | pass-for-current-slice | `cmake --build build --target ef_core -j2`; `cmake --build build --target ef_py -j2`; `155 passed` runtime guard | No dedicated C++ unit suite exists for this model yet. |

## Scope

In scope:

- Keep `default_effects_model.cpp` as the local entry point for
  `make_default_effects_model`.
- Split private implementation helpers under `src/models/weapons/detail/`.
- Preserve behavior, formulas, RNG handling, result fields, and pointer
  lifetimes.
- Record finite task clusters, validation commands, closure gates, and residuals.
- Add narrow regression fixtures for direct hit, protected-system fallback,
  broad spatial projection, non-broad component projection, and structured
  air-platform early return.

Out of scope:

- Replacing the effects model architecture or public `IEffectsModel` contract.
- Promoting any evidence row, candidate package, or source scan to authoritative
  stock runtime capability.
- Changing warhead physics formulas, fragility curves, or vulnerability source
  authority as part of a structure-only cleanup.
- Solving the project-wide absence of a C++ unit-test framework.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze scope, authority, and task list. | A2 assessment flags `default_effects_model.cpp` as oversized. | README and task clusters exist and parent index links them. | pass |
| `P1 Extraction` | Move monolithic helper logic into local detail fragments. | Buildable baseline. | Direct, spatial, system-effect, result, state, warhead, geometry, component, legacy helpers compile. | pass |
| `P2 Internal Cleanup` | Reduce duplicate formulas and scratch updates. | P1 helper boundaries compile. | Shared component-scale and warhead-sample helpers are used. | pass |
| `P3 Air Resolution Split` | Thin air-platform consequence internals without formula drift. | P2 pass. | Mechanism-load, scale aggregation, platform-only, sensor/avionics, propulsion/fuel, control/hydraulic, crew-role, mission/combat, structure-spatial, fire-zone, finalize, and future consequence blocks are named helpers. | pass / DFM-P3F structure-spatial helper pass |
| `P4 Regression Fixtures` | Add narrow behavior fixtures for high-risk paths. | P1-P3 build. | Dedicated fixture or runtime snapshot tests cover named paths. | direct/spatial/early-return pass |
| `P5 Closure` | Sync docs, status, archive, and residuals. | P4 pass or explicit held residual. | Acceptance gate, current status, and archive record are updated. | closed / archived |

## Task Clusters

- Task cluster plan: [default_effects_modularization_task_clusters_20260601.md](default_effects_modularization_task_clusters_20260601.md)
- Current status: [default_effects_modularization_current_status_20260601.md](default_effects_modularization_current_status_20260601.md)
- Round-1 acceptance: [default_effects_modularization_acceptance_20260601.md](default_effects_modularization_acceptance_20260601.md)
- Closure sync: [default_effects_modularization_closure_sync_20260602.md](default_effects_modularization_closure_sync_20260602.md)
- Archive closeout: [archive/default_effects_modularization_closeout_20260602.md](archive/default_effects_modularization_closeout_20260602.md)

## Outputs And Evidence

- [default_effects_model.cpp](../../../../../src/models/weapons/default_effects_model.cpp)
- `src/models/weapons/detail/default_effects_*_detail.inc`
- [weapons README](../../../../../src/models/weapons/README.md)
- [weapons README.zh.md](../../../../../src/models/weapons/README.zh.md)
- Build gate: `cmake --build build --target ef_core -j2`
- Runtime guard: `CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build python -m pytest tests/runtime/air_combat/test_weapon_guidance_realism_guards.py --tb=short -ra`

## Acceptance Gate

This subproject can be marked accepted only when:

- `ef_core` builds after a clean include-order check.
- Existing runtime guard tests pass.
- Dedicated golden or fixture tests cover the named direct, spatial, and air
  platform early-return paths, or those fixture gaps are explicitly marked held.
- `src/models/weapons/detail/` is tracked together with the modified entry file.
- README/status/task-cluster surfaces refuse broader realism or authority claims.

## Residuals And Next Steps

- Keep the accepted direct, spatial, and structured air-platform early-return
  runtime fixtures green when future tasks touch this surface.
- Consider a later C++ unit-test harness only as a separate project-wide testing
  initiative.
- The previously held aircraft structure-spatial helper extraction is complete;
  any further air-platform restructuring must be re-scoped as a new finite task
  with formulas, authority strings, and public contracts preserved.

## Archive

- Archive index: [archive/README.md](archive/README.md)
- Final closeout: [archive/default_effects_modularization_closeout_20260602.md](archive/default_effects_modularization_closeout_20260602.md)
