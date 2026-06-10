# Engineering Governance P1

Status: `2026-06-04` closed local-pass remediation slice. `P1-A`, `P1-B`,
bounded `P1-C`, and the scoped `P1-D` diagnostics callback split are
implemented and validated locally.

Language:

- English canonical: `README.md`
- Chinese companion: `README.zh.md`

Inputs:

- [Review task area](../README.md)
- [Engineering Governance P0](../engineering_governance_p0/README.md)
- [Engineering discipline review](../../../evaluation/engineering_discipline_review_20260603.md)
- [Architecture claim verification](../../../evaluation/architecture_review_claim_verification_20260603.zh.md)
- [Agent subproject standard](../../../agent/rules/subproject_creation_standard.md)
- [Subagent usage policy](../../../standards/governance/subagent_usage_policy.md)

## Purpose

This subproject implements the P1 remediation work that followed P0. It fixes
the verified P1 issues that had clear owner boundaries: a stale architecture
guard, missing centralized shape validation in the scenario compiler path,
duplicated adapter-owned capability probing, and the broad
`CMODiagnosticsCallback` diagnostics owner.

The closure boundary is explicit. `P1-C` centralizes
`RuntimeFacadeAdapter`-owned capability probing through a capability snapshot;
it does not claim a full adapter or world-batch class hierarchy split. That
larger adapter decomposition is future architecture work, not a held residual
inside this P1 task. `P1-D` is closed for the diagnostics callback owner:
step scalars, action/policy/HMoE/A5/A6/leader/reward/runway logging, terminal
reward windows, preterm snapshots, and cooperative event-window aggregation now
live behind focused helpers in `python/training/diagnostics.py`.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Stale architecture guard | local-pass | `tests/architecture/structural_boundaries`; focused test passed | Updates the guard to current split-file structure; does not change weapon effects runtime behavior. |
| Scenario compiler shape validation | local-pass | `python/scenario/compiler/validation.py`; `service.py`; `merge.py`; `tests/scenario/test_scenario_compiler.py`; focused suite passed | Validates consumed shape only; does not introduce a full JSON Schema or domain semantic validator. |
| Runtime facade/world-batch capability probing | local-pass | `python/rl/runtime/world_batch/adapter.py`; `tests/world_batch/test_world_batch_vec_env.py`; focused world-batch tests passed | Adds a centralized capability snapshot for adapter-owned probing; does not split world-batch env classes or the full adapter. |
| Diagnostics callback helper extraction | local-pass | `python/training/diagnostics.py`; `python/training_callbacks.py`; training diagnostics tests passed | Moves diagnostics calculation and event-window state out of `CMODiagnosticsCallback`; does not change RL algorithm behavior or logged key semantics. |
| Task and evaluation documentation | local-pass | This subproject, parent review index, and architecture evaluation updates | Records P1 as closed without claiming unrelated architecture work is complete. |

## Scope

In scope:

- Repair stale architecture guardrails that failed because code was structurally
  split while the guard still searched old inline text.
- Add a small, centralized scenario compiler shape validator for fields consumed
  by the main compile path and prefab merge path.
- Add a small, centralized runtime facade adapter capability snapshot so core
  adapter-owned probing is not scattered through each writer/reader method.
- Extract diagnostics calculations and state from `CMODiagnosticsCallback` into
  `python/training/diagnostics.py`, while preserving existing callback wrapper
  entry points and logged scalar keys.
- Add focused tests for invalid scenario roots, invalid shape cases, adapter
  capability refresh after facade replacement, and diagnostics helper behavior.
- Record validation evidence and closure boundaries honestly.

Out of scope:

- Changing weapon effects runtime logic.
- Replacing scenario compilation with a full JSON Schema system.
- Adding semantic validation for every domain-specific scenario field.
- Splitting the full runtime adapter or world-batch env class hierarchy.
- Changing RL algorithms, reward semantics, A5/A6 behavior, or training config.
- Cleaning unrelated worktree changes.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze P1 scope after P0. | P0 local remediation exists. | P1 clusters and non-goals are recorded. | pass |
| `P1-A Guard Repair` | Make stale architecture guard match current split implementation. | Failing guard is reproducible. | Focused architecture guard passes. | pass |
| `P1-B Compiler Guard` | Add centralized compiler shape validation. | Existing compiler tests pass before edit. | Focused scenario compiler suite passes with negative tests. | pass |
| `P1-C Adapter Narrowing` | Reduce duplicated runtime capability probing. | P1-A/B local-pass and runtime surface is quiet. | Capability snapshot is implemented and focused world-batch validation passes. | pass |
| `P1-D Diagnostics Callback Split` | Move diagnostics calculation and event-window state out of `CMODiagnosticsCallback`. | P1-C local-pass and callback responsibilities are identified. | Training diagnostics helpers cover policy, HMoE, actions, leader, rewards, A5/A6, runway/gear, basic step scalars, terminal/preterm windows, and cooperative aggregation. | pass |
| `P2 Closure` | Sync docs, residuals, and parent review index. | P1-A/B/C/D validation complete. | Status reflects a closed P1 slice and future work is not listed as held P1. | pass |

## Task Clusters

- Task cluster plan: `engineering_governance_p1_task_clusters_20260603.md`

## Outputs And Evidence

- `tests/architecture/structural_boundaries`
- `python/scenario/compiler/validation.py`
- `python/scenario/compiler/service.py`
- `python/scenario/compiler/merge.py`
- `python/rl/runtime/world_batch/adapter.py`
- `python/rl/runtime/world_batch/__init__.py`
- `python/training/diagnostics.py`
- `python/training_callbacks.py`
- `tests/scenario/test_scenario_compiler.py`
- `tests/world_batch/test_world_batch_vec_env.py`
- `tests/training/test_cooperative_diagnostics_callback.py`
- `tests/training/test_a6_event_value_diagnostics_callback.py`
- This task subproject and parent review index entries.

Validation evidence:

- `./.venv/bin/python -m pytest tests/architecture/structural_boundaries/test_domain_separation_boundaries.py::test_a2_structured_air_effects_do_not_write_rl_score_authority -q` passed.
- `./.venv/bin/python -m pytest tests/architecture/structural_boundaries -q` passed, 17 tests.
- `./.venv/bin/python -m pytest tests/scenario/test_scenario_compiler.py -q` passed.
- Scenario/prefab shape scan passed for 50 JSON files under `scenarios/`,
  `examples/scenarios/`, and `examples/config/prefabs/`.
- `./.venv/bin/python -m pytest tests/world_batch/test_world_batch_vec_env.py -k "adapter_capability_snapshot or legacy_task_order_batch_writer_is_removed or task_order_reverse_projection_stays_removed or task_order_write_routes_through_maintained_helper or apply_launch_requests or step_worlds" -q` passed, 6 selected tests.
- `./.venv/bin/python -m pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q` passed, 17 tests.
- `./.venv/bin/python -m ruff check ...` passed for touched Python files.
- `git diff --check -- ...` passed for touched P1 files.

## Acceptance Gate

This P1 subproject is accepted when:

- The architecture guard asserts the current structural ownership rather than
  an obsolete inline text anchor.
- The main scenario compiler path rejects invalid consumed shapes instead of
  silently coercing them to empty containers.
- Prefab import shape errors are reported before merge mutation.
- RuntimeFacadeAdapter-owned capability checks use a named capability snapshot
  and refresh when tests swap the facade object.
- `CMODiagnosticsCallback` no longer owns diagnostics calculations or
  terminal/preterm/cooperative window state; it delegates to
  `python/training/diagnostics.py`.
- Focused tests prove helper behavior and preserve existing logged scalar keys.
- Documentation states this P1 slice as closed without claiming future adapter,
  JSON Schema, domain semantic validation, or broader runtime refactors are
  complete.

## Residuals And Next Steps

Closed P1 does not leave held P1 work. The following are separate future tasks
if they become priority:

- Full runtime adapter/world-batch env class hierarchy split.
- Optional public JSON Schema or deeper domain semantic validation for scenario
  content.
- Broader architecture refactors already tracked by the main architecture
  review, such as `DefaultUnitFactory::spawn()` and world-batch env duplication.
- Re-run focused validation before merging if parallel edits touch the same
  architecture guard, compiler, adapter, or training diagnostics files.

## Archive

Historical or superseded remediation records should move to `archive/README.md`
only after a replacement current-status or closeout surface exists.
