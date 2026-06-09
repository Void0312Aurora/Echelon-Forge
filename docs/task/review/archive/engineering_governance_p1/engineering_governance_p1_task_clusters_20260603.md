# Engineering Governance P1 Task Clusters

Status: `2026-06-04` closed finite task-cluster record for the P1 remediation
slice. `P1-A`, `P1-B`, bounded `P1-C`, scoped `P1-D`, and `P1-E` closure are
local-pass.

Parent subproject: [Engineering Governance P1](README.md)

## Boundary Decision

This P1 slice fixes verified, bounded architecture and correctness issues. It
does not expand into broad runtime adapter splits, world-batch class hierarchy
work, full scenario JSON Schema publication, or RL behavior tuning.

The diagnostics callback split is closed for the P1 owner boundary:
`CMODiagnosticsCallback` now adapts SB3 lifecycle hooks and delegates
diagnostics calculation/state to `python/training/diagnostics.py`. A future
adapter split is not a held P1 cluster; it requires a separate task record if it
becomes priority.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P1-A` | main thread | n/a | Repair the stale A2 structured-air architecture guard so it tracks current split-file ownership. | `tests/architecture/structural_boundaries/test_structural_guardrails.py` | Runtime behavior changes, weapon damage tuning | `pytest tests/architecture/structural_boundaries/test_structural_guardrails.py::test_a2_structured_air_effects_do_not_write_rl_score_authority -q` | Focused guard passes and still asserts Score writes stay out of structured-air path. | First; serial | 1 | pass |
| `P1-B` | main thread | n/a | Add centralized shape validation to the main scenario compiler and prefab merge path. | `python/scenario/compiler/validation.py`, `python/scenario/compiler/service.py`, `python/scenario/compiler/merge.py`, `tests/scenario/test_scenario_compiler.py` | Full JSON Schema, domain semantic validation, loader/runtime rewrite | `pytest tests/scenario/test_scenario_compiler.py -q` | Invalid consumed shapes fail closed; existing compiler tests pass. | After P1-A; serial in this run | 2 | pass |
| `P1-C` | main thread | n/a | Reduce duplicated RuntimeFacadeAdapter-owned capability probing through a bounded capability snapshot. | `python/rl/runtime/world_batch/adapter.py`, `python/rl/runtime/world_batch/__init__.py`, `tests/world_batch/test_world_batch_vec_env.py` | Callback refactors, training config changes, full adapter split, world-batch env base-class extraction | `pytest tests/world_batch/test_world_batch_vec_env.py -k "adapter_capability_snapshot or legacy_task_order_batch_writer_is_removed or task_order_reverse_projection_stays_removed or task_order_write_routes_through_maintained_helper or apply_launch_requests or step_worlds" -q` | Capability snapshot exists, refreshes on facade swap, and focused world-batch tests pass. | After P1-A/B; serial due runtime surface | 2 | pass |
| `P1-D1` | main thread | n/a | Extract policy-distribution diagnostics from `CMODiagnosticsCallback` into a focused helper while preserving the current callback method. | `python/training/diagnostics.py`, `python/training_callbacks.py` | RL algorithm changes, A5/A6 behavior tuning | `pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q` | Existing diagnostics tests pass and the callback wrapper remains available. | After P1-C; serial due callback touch | 1 | pass |
| `P1-D2` | main thread | n/a | Extract HMoE route/parameter diagnostics while preserving parameter-stat throttling. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | RL algorithm changes, changing HMoE stat keys | same training diagnostics focused tests | Existing callback route/param stats still log; helper test proves parameter stats remain throttled. | After P1-D1; serial | 1 | pass |
| `P1-D3` | main thread | n/a | Extract full/hybrid action diagnostics while preserving logged scalar keys. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | RL algorithm changes, changing action schema semantics | same training diagnostics focused tests | Helper test proves full-action brake and combat switch semantics. | After P1-D2; serial | 1 | pass |
| `P1-D4` | main thread | n/a | Extract leader observation/info/reward diagnostics while preserving logged scalar keys. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | RL algorithm changes, changing leader stat keys | same training diagnostics focused tests | Helper test proves observation, bucket, C2, and reward semantics. | After P1-D3; serial | 1 | pass |
| `P1-D5` | main thread | n/a | Extract step reward-term diagnostics while preserving logged scalar keys. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | RL algorithm changes, changing reward stat keys | same training diagnostics focused tests | Helper test proves reward-term mean and missing-key behavior. | After P1-D4; serial | 1 | pass |
| `P1-D6` | main thread | n/a | Extract A6 first-event info diagnostics while preserving logged scalar keys. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_a6_event_value_diagnostics_callback.py` | RL algorithm changes, changing A6 stat keys or label semantics | same training diagnostics focused tests | Helper test proves label-count and stable-zero behavior. | After P1-D5; serial | 1 | pass |
| `P1-D7` | main thread | n/a | Extract A5 event info diagnostics while preserving logged scalar keys. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | RL algorithm changes, changing A5 stat keys or release-discipline semantics | same training diagnostics focused tests | Helper test proves event-rate, rejection, state, and component logging. | After P1-D6; serial | 1 | pass |
| `P1-D8` | main thread | n/a | Extract runway/gear step info diagnostics while preserving logged scalar keys. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | RL algorithm changes, changing runway/gear stat keys | same training diagnostics focused tests | Helper test proves runway, cross-track tail, gear-collapse, and gear-stress logging. | After P1-D7; serial | 1 | pass |
| `P1-D9` | main thread | n/a | Extract basic reward/instrument/ILS step scalar logging and effective-action array selection. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | RL behavior changes, changing scalar keys | same training diagnostics focused tests | Helper test proves reward, instrument, and ILS scalars remain stable. | After P1-D8; serial | 1 | pass |
| `P1-D10` | main thread | n/a | Move terminal/preterm reward windows and cooperative/stateful event-window aggregation out of the callback class. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | RL behavior changes, changing termination/cooperative stat keys | same training diagnostics focused tests | `TrainingEventDiagnosticsWindow` owns state and direct tests prove terminal, preterm, role, and world-window metrics. | After P1-D9; serial | 1 | pass |
| `P1-E` | main thread | n/a | Record task status, evidence, and parent review/evaluation links. | `docs/task/review/engineering_governance_p1/**`, `docs/task/review/README*`, `docs/evaluation/architecture_review_20260603*`, `docs/evaluation/architecture_review_claim_verification_20260603.zh.md`, `docs/evaluation/architecture_structure_assessment_20260603.zh.md` | Claiming unrelated future adapter/world-batch or JSON Schema work is complete | Markdown inspection; `git diff --check` | Docs mark P1 closed and move future work out of held P1 status. | Last; serial | 1 | pass |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not create a new conversation thread for this work.
- Do not allow two workers to edit the same task status table, scenario
  compiler validation module, runtime adapter, or callback file concurrently.
- Future full adapter splitting, world-batch env base-class extraction, or
  `typing.Protocol` loader contracts require a separate task record.
- Follow [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md)
  only when the execution environment can dispatch workers without creating new
  conversation threads.

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

```bash
./.venv/bin/python -m pytest tests/architecture/structural_boundaries/test_structural_guardrails.py::test_a2_structured_air_effects_do_not_write_rl_score_authority -q
./.venv/bin/python -m pytest tests/scenario/test_scenario_compiler.py -q
./.venv/bin/python -m pytest tests/world_batch/test_world_batch_vec_env.py -k "adapter_capability_snapshot or legacy_task_order_batch_writer_is_removed or task_order_reverse_projection_stays_removed or task_order_write_routes_through_maintained_helper or apply_launch_requests or step_worlds" -q
./.venv/bin/python -m pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q
./.venv/bin/python -m ruff check python/scenario/compiler/validation.py python/scenario/compiler/service.py python/scenario/compiler/merge.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch/__init__.py python/training/diagnostics.py python/training_callbacks.py tests/scenario/test_scenario_compiler.py tests/architecture/structural_boundaries/test_structural_guardrails.py tests/world_batch/test_world_batch_vec_env.py tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py
git diff --check -- tests/architecture/structural_boundaries/test_structural_guardrails.py python/scenario/compiler/validation.py python/scenario/compiler/service.py python/scenario/compiler/merge.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch/__init__.py python/training/diagnostics.py python/training_callbacks.py tests/scenario/test_scenario_compiler.py tests/world_batch/test_world_batch_vec_env.py tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py docs/task/review/engineering_governance_p1 docs/task/review/README.md docs/task/review/README.zh.md docs/evaluation/architecture_review_20260603.md docs/evaluation/architecture_review_20260603.zh.md docs/evaluation/architecture_review_claim_verification_20260603.zh.md docs/evaluation/architecture_norms_correctness_review_20260603.zh.md docs/evaluation/architecture_structure_assessment_20260603.zh.md
```

## Acceptance Criteria

- P1-A architecture guard passes locally and asserts current ownership.
- P1-B scenario compiler tests pass locally and include negative shape cases.
- P1-C adapter-owned probing uses a named capability snapshot and focused tests
  prove it refreshes after facade swaps.
- P1-D diagnostics helpers own policy, HMoE, action, leader, reward, A5/A6,
  runway/gear, basic step scalar, terminal/preterm, and cooperative window
  behavior without changing logged scalar keys.
- `CMODiagnosticsCallback` remains as a small SB3 lifecycle adapter rather than
  the owner of diagnostics calculation and state.
- P1-E documentation marks this P1 task closed while refusing to claim future
  adapter/world-batch, JSON Schema, domain semantic validation, or broad runtime
  refactors are complete.

## Validation Evidence

```text
test_a2_structured_air_effects_do_not_write_rl_score_authority: pass
tests/architecture/structural_boundaries/test_structural_guardrails.py: pass, 17 passed
tests/scenario/test_scenario_compiler.py: pass, 23 passed
world-batch adapter focused tests: pass, 6 selected passed
training diagnostics focused tests: pass, 17 passed
ruff check for touched Python files: pass
git diff --check for touched P1 files: pass
scenario/prefab shape scan: pass, 50 JSON files
```

## Residual Map

No held P1 clusters remain.

Future task candidates, outside this P1 closure:

- Full runtime adapter/world-batch env class split.
- Optional public JSON Schema or deeper scenario semantic validation.
- Broader architecture refactors tracked by the main architecture review.
