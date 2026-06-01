# Default Effects Modularization Task Clusters

Status: `2026-06-01 finite task-cluster plan for default_effects_modularization/README.md`.

Parent subproject:

- [README.md](README.md)
- [README.zh.md](README.zh.md)

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
| `DFM-P3` | main thread or worker | inherited / xhigh for worker | Further split air-platform resolution internals into named helper stages. | `src/models/weapons/detail/default_effects_air_platform_resolution_detail.inc` | Do not alter consequence coefficients or loss-state semantics. | `cmake --build build --target ef_core -j2`; runtime guard; subagent read-only review if delegated. | Mechanism-load fallback, scale aggregation, finalize, and any future consequence helpers compile with unchanged tests. | Depends on `DFM-P2`; serial because file is a dense consequence surface. | 2 | partial |
| `DFM-P4` | future worker | inherited / xhigh | Add narrow regression fixtures for direct and spatial behavior paths. | `tests/runtime/air_combat/**` or a new dedicated fixture path; no source edits unless required by test harness | Do not introduce a project-wide C++ test framework in this cluster. | Fixed-RNG tests for direct component, direct protected-system fallback, broad spatial, non-broad component spatial, and platform-loss early return. | Fixtures pass and document exact covered behavior. | Depends on `DFM-P1-P3` build passing; may run in parallel only with docs-only status updates. | 2 | planned |
| `DFM-P5` | diagnostics worker | inherited / xhigh | Read-only behavior equivalence review after any structural patch. | none | No edits. | Static code review plus reported risks and test gaps. | Packet reports `pass` or concrete findings. | May run parallel with non-overlapping local work; cannot replace local build/test gates. | 1 | pass |
| `DFM-P6` | integration worker | inherited / xhigh | Closure sync: update status, parent links, acceptance/residuals, and archive boundary. | subproject docs, parent A2 README entries, `src/models/weapons/README*` if needed | No new implementation. | `git diff --check`; link/path review; build/test evidence copied from current run. | Acceptance or held residuals are explicit; untracked detail files are called out. | Serial after implementation/test clusters. | 1 | planned |

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
CMO_BUILD_DIR=/home/void0312/Workshop/CMO/build python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
git diff --check -- src/models/weapons/default_effects_model.cpp src/models/weapons/detail src/models/weapons/README.md src/models/weapons/README.zh.md docs/task/air_combat/a2_high_fidelity_damage_model/default_effects_modularization
```

## Acceptance Criteria

- `DFM-P0`, `DFM-P1`, `DFM-P2`, and `DFM-P3` pass or explicitly hold remaining
  split residuals.
- `DFM-P4` passes, or fixture gaps are moved to a named held residual with a
  replacement validation path.
- `DFM-P6` syncs parent README links and status language.
- No wider realism, authority, Pk, or deterministic-fuze claim is introduced.

## Residual Map

Immediate:

- Ensure `src/models/weapons/detail/` is tracked with the entry file in any final commit.
- Keep build and runtime guard green after any follow-up split.

Follow-on:

- Add dedicated fixed-RNG regression fixtures for direct, spatial, and early-return paths.
- Consider extracting named aircraft consequence blocks from air-platform resolution if tests stay green.

Deferred:

- Project-wide C++ unit-test framework.
- Public model/plugin API reshaping.
- Authority promotion or industrial admission work.
