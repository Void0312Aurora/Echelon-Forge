# Engineering Governance P1

Status: `2026-06-04` active partial local-pass remediation slice; `P1-A`, `P1-B`, bounded `P1-C`, and narrow `P1-D1`/`P1-D2`/`P1-D3` are implemented locally, broader callback and adapter-split slices remain held.

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
without broad runtime rewrites: a stale architecture test, the main scenario
compiler's missing centralized shape validation, and a narrow runtime facade
adapter capability-probing convergence.

It intentionally does not claim that all P1 work is complete. The first P1-C
adapter slice only centralizes capability resolution in `RuntimeFacadeAdapter`,
and the first P1-D1 callback slice only extracts policy-distribution
diagnostics behind a compatibility wrapper. P1-D2 extracts HMoE policy route
and parameter diagnostics behind a second compatibility wrapper. P1-D3 extracts
action diagnostics behind a third compatibility wrapper. Broader adapter
splitting and full diagnostics callback decomposition remain separate follow-on
slices.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Stale architecture guard | local-pass | `tests/architecture/test_wp22_structural_guardrails.py`; focused test passed | Updates the guard to current split-file structure; does not change weapon effects runtime behavior. |
| Scenario compiler shape validation | local-pass | `python/scenario/compiler/validation.py`; `service.py`; `merge.py`; `tests/scenario/test_scenario_compiler.py`; focused suite passed | Validates consumed shape only; does not introduce a full JSON Schema or domain semantic validator. |
| Runtime facade/world-batch capability probing | local-pass | `python/rl/runtime/world_batch/adapter.py`; `tests/world_batch/test_world_batch_vec_env.py`; focused world-batch tests passed | Adds a centralized capability snapshot for adapter-owned probing; does not split world-batch env classes or the full adapter. |
| Policy-distribution diagnostics helper | local-pass | `python/training/diagnostics.py`; `python/training_callbacks.py`; focused training diagnostics tests passed | Extracts one diagnostics responsibility behind the existing callback method; does not split the full callback class. |
| HMoE diagnostics helper | local-pass | `python/training/diagnostics.py`; `python/training_callbacks.py`; `tests/training/test_cooperative_diagnostics_callback.py`; focused training diagnostics tests passed | Extracts HMoE route/parameter stat recording and preserves parameter-stat throttling; does not split cooperative, leader, or action diagnostics. |
| Action diagnostics helper | local-pass | `python/training/diagnostics.py`; `python/training_callbacks.py`; `tests/training/test_cooperative_diagnostics_callback.py`; focused training diagnostics tests passed | Extracts full/hybrid action logging and preserves full-action brake plus combat switch semantics; does not split cooperative or leader diagnostics. |
| Cooperative diagnostics callback split | held | prior review residual | Broader split remains deferred to separate packets after each responsibility has a bounded write set. |

## Scope

In scope:

- Repair stale architecture guardrails that fail because code was structurally
  split while the guard still searched old inline text.
- Add a small, centralized scenario compiler shape validator for fields consumed
  by the main compile path and prefab merge path.
- Add a small, centralized runtime facade adapter capability snapshot so core
  adapter-owned probing is not scattered through each writer/reader method.
- Extract policy-distribution diagnostics into a focused helper while preserving
  the existing `CMODiagnosticsCallback` method as a compatibility wrapper.
- Extract HMoE policy route/parameter diagnostics into a focused helper while
  preserving the callback's parameter-stat throttle state.
- Extract full/hybrid action diagnostics into a focused helper while preserving
  the existing callback wrapper and logged scalar keys.
- Add focused tests for invalid scenario roots and invalid shape cases that were
  previously silently coerced or ignored, and for adapter capability refresh
  after facade replacement in tests.
- Record validation evidence and residual work honestly.

Out of scope:

- Changing weapon effects runtime logic.
- Replacing scenario compilation with a full JSON Schema system.
- Adding semantic validation for every domain-specific scenario field.
- Broadly splitting runtime facade adapters, world-batch env classes, or
  diagnostics callbacks in this slice.
- Cleaning unrelated worktree changes.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze P1 scope after P0. | P0 local remediation exists. | P1 clusters and non-goals are recorded. | pass |
| `P1-A Guard Repair` | Make stale architecture guard match current split implementation. | Failing guard is reproducible. | Focused architecture guard passes. | pass |
| `P1-B Compiler Guard` | Add centralized compiler shape validation. | Existing compiler tests pass before edit. | Focused scenario compiler suite passes with negative tests. | pass |
| `P1-C Adapter Narrowing` | Reduce duplicated runtime capability probing. | P1-A/B local-pass and runtime surface is quiet. | Capability snapshot is implemented and focused world-batch validation passes. | pass |
| `P1-D1 Policy Helper` | Extract policy-distribution diagnostics behind the current callback wrapper. | P1-C local-pass and callback edit surface is narrow. | Focused cooperative/A6 diagnostics tests pass. | pass |
| `P1-D2 HMoE Helper` | Extract HMoE route/parameter diagnostics behind the current callback wrapper. | P1-D1 local-pass. | Focused training diagnostics tests prove route logging and parameter-stat throttling. | pass |
| `P1-D3 Action Helper` | Extract full/hybrid action diagnostics behind the current callback wrapper. | P1-D2 local-pass. | Focused training diagnostics tests prove full-action brake and combat switch logging. | pass |
| `P1-D Callback Split` | Split remaining diagnostics callback responsibilities. | Each remaining responsibility has a bounded packet. | Separate full callback split exists with training diagnostics tests. | held |
| `P2 Closure` | Sync docs, residuals, and parent review index. | P1-A/B/C/D1/D2/D3 validation complete. | Status reflects implemented and held items. | active |

## Task Clusters

- Task cluster plan: `engineering_governance_p1_task_clusters_20260603.md`

## Outputs And Evidence

- `tests/architecture/test_wp22_structural_guardrails.py`
- `python/scenario/compiler/validation.py`
- `python/scenario/compiler/service.py`
- `python/scenario/compiler/merge.py`
- `python/rl/runtime/world_batch/adapter.py`
- `python/rl/runtime/world_batch/__init__.py`
- `python/training/diagnostics.py`
- `python/training_callbacks.py`
- `tests/scenario/test_scenario_compiler.py`
- `tests/world_batch/test_world_batch_vec_env.py`
- This task subproject and parent review index entries.

Validation evidence:

- `./.venv/bin/python -m pytest tests/architecture/test_wp22_structural_guardrails.py::test_a2_structured_air_effects_do_not_write_rl_score_authority -q` passed.
- `./.venv/bin/python -m pytest tests/architecture/test_wp22_structural_guardrails.py -q` passed, 17 tests.
- `./.venv/bin/python -m pytest tests/scenario/test_scenario_compiler.py -q` passed.
- `./.venv/bin/python -m ruff check ...` passed for touched Python files.
- `git diff --check -- ...` passed for touched P1 files.
- Scenario/prefab shape scan passed for 50 JSON files under `scenarios/`,
  `examples/scenarios/`, and `examples/config/prefabs/`.
- `./.venv/bin/python -m pytest tests/world_batch/test_world_batch_vec_env.py -k "adapter_capability_snapshot or legacy_task_order_batch_writer_is_removed or task_order_reverse_projection_stays_removed or task_order_write_routes_through_maintained_helper or apply_launch_requests or step_worlds" -q` passed, 6 selected tests.
- `./.venv/bin/python -m pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q` passed, 11 tests.

## Acceptance Gate

This subproject can mark the implemented P1-A/P1-B slice accepted only when:

- The architecture guard asserts the current structural ownership rather than
  an obsolete inline text anchor.
- The main scenario compiler path rejects invalid consumed shapes instead of
  silently coercing them to empty containers.
- Prefab import shape errors are reported before merge mutation.
- RuntimeFacadeAdapter-owned capability checks use a named capability snapshot
  and refresh when tests swap the facade object.
- Policy-distribution diagnostics are isolated in `python/training/diagnostics.py`
  without changing the existing callback entry point.
- HMoE route/parameter diagnostics are isolated in
  `python/training/diagnostics.py`, with callback-owned throttling behavior
  preserved by test.
- Full/hybrid action diagnostics are isolated in
  `python/training/diagnostics.py`, with full-action brake and combat-switch
  behavior preserved by test.
- Focused local tests and any residual blockers are recorded.

The broader P1 program remains incomplete until held callback and broader
adapter/world-batch class split slices receive their own task records and
validation.

## Residuals And Next Steps

- Run the full architecture guard file again before accepting this slice into a
  clean branch if further parallel edits land.
- Decide whether scenario compiler validation should later become a published
  JSON Schema or stay as a lightweight internal shape guard.
- Decide whether a later adapter split should introduce `typing.Protocol`
  interfaces around loader/runtime surfaces now that adapter-owned probing has a
  centralized capability snapshot.
- Continue P1-D by splitting cooperative, leader, reward, and event-window
  diagnostics in bounded packets; P1-D1/D2/D3 only extracted policy
  distribution, HMoE, and action diagnostics.

## Archive

Historical or superseded remediation records should move to `archive/README.md`
only after a replacement current-status or closeout surface exists.
