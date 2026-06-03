# Engineering Governance P1

Status: `2026-06-03` active partial local-pass remediation slice; `P1-A` and `P1-B` are implemented locally, broader runtime/callback slices remain held.

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

This subproject implements the next bounded remediation slice after P0. It
targets verified correctness and architecture-guard issues that can be fixed
without broad runtime rewrites: a stale architecture test and the main scenario
compiler's missing centralized shape validation.

It intentionally does not claim that all P1 work is complete. Runtime facade
adapter probing and diagnostics callback decomposition remain separate slices
because they touch broader, currently noisy surfaces.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Stale architecture guard | local-pass | `tests/architecture/test_wp22_structural_guardrails.py`; focused test passed | Updates the guard to current split-file structure; does not change weapon effects runtime behavior. |
| Scenario compiler shape validation | local-pass | `python/scenario/compiler/validation.py`; `service.py`; `merge.py`; `tests/scenario/test_scenario_compiler.py`; focused suite passed | Validates consumed shape only; does not introduce a full JSON Schema or domain semantic validator. |
| Runtime facade/world-batch capability probing | held | prior review residual | Deferred pending a separate bounded adapter slice and wider runtime validation. |
| Cooperative diagnostics callback split | held | prior review residual; active A5/A6 worktree noise | Deferred to avoid overlapping unrelated callback edits. |

## Scope

In scope:

- Repair stale architecture guardrails that fail because code was structurally
  split while the guard still searched old inline text.
- Add a small, centralized scenario compiler shape validator for fields consumed
  by the main compile path and prefab merge path.
- Add focused tests for invalid scenario roots and invalid shape cases that were
  previously silently coerced or ignored.
- Record validation evidence and residual work honestly.

Out of scope:

- Changing weapon effects runtime logic.
- Replacing scenario compilation with a full JSON Schema system.
- Adding semantic validation for every domain-specific scenario field.
- Refactoring runtime facade adapters, world-batch adapters, or diagnostics
  callbacks in this slice.
- Cleaning unrelated worktree changes.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze P1 scope after P0. | P0 local remediation exists. | P1 clusters and non-goals are recorded. | pass |
| `P1-A Guard Repair` | Make stale architecture guard match current split implementation. | Failing guard is reproducible. | Focused architecture guard passes. | pass |
| `P1-B Compiler Guard` | Add centralized compiler shape validation. | Existing compiler tests pass before edit. | Focused scenario compiler suite passes with negative tests. | pass |
| `P1-C Adapter Narrowing` | Reduce duplicated runtime capability probing. | P1-A/B accepted and runtime surface is quiet. | Separate adapter slice exists with broad runtime validation. | held |
| `P1-D Callback Split` | Split diagnostics callback responsibilities. | A5/A6 callback edits settle. | Separate callback slice exists with training diagnostics tests. | held |
| `P2 Closure` | Sync docs, residuals, and parent review index. | P1-A/B validation complete. | Status reflects implemented and held items. | active |

## Task Clusters

- Task cluster plan: `engineering_governance_p1_task_clusters_20260603.md`

## Outputs And Evidence

- `tests/architecture/test_wp22_structural_guardrails.py`
- `python/scenario/compiler/validation.py`
- `python/scenario/compiler/service.py`
- `python/scenario/compiler/merge.py`
- `tests/scenario/test_scenario_compiler.py`
- This task subproject and parent review index entries.

Validation evidence:

- `./.venv/bin/python -m pytest tests/architecture/test_wp22_structural_guardrails.py::test_a2_structured_air_effects_do_not_write_rl_score_authority -q` passed.
- `./.venv/bin/python -m pytest tests/architecture/test_wp22_structural_guardrails.py -q` passed, 17 tests.
- `./.venv/bin/python -m pytest tests/scenario/test_scenario_compiler.py -q` passed.
- `./.venv/bin/python -m ruff check ...` passed for touched Python files.
- `git diff --check -- ...` passed for touched P1 files.
- Scenario/prefab shape scan passed for 50 JSON files under `scenarios/`,
  `examples/scenarios/`, and `examples/config/prefabs/`.

## Acceptance Gate

This subproject can mark the implemented P1-A/P1-B slice accepted only when:

- The architecture guard asserts the current structural ownership rather than
  an obsolete inline text anchor.
- The main scenario compiler path rejects invalid consumed shapes instead of
  silently coercing them to empty containers.
- Prefab import shape errors are reported before merge mutation.
- Focused local tests and any residual blockers are recorded.

The broader P1 program remains incomplete until held adapter and callback slices
receive their own task records and validation.

## Residuals And Next Steps

- Run the full architecture guard file again before accepting this slice into a
  clean branch if further parallel edits land.
- Decide whether scenario compiler validation should later become a published
  JSON Schema or stay as a lightweight internal shape guard.
- Split runtime facade/world-batch capability probing in a separate P1-C task.
- Split cooperative diagnostics callback responsibilities in a separate P1-D
  task after active A5/A6 edits settle.

## Archive

Historical or superseded remediation records should move to `archive/README.md`
only after a replacement current-status or closeout surface exists.
