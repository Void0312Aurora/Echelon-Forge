# Engineering Governance P1 Task Clusters

Status: `2026-06-03` finite task-cluster record for the P1 remediation slice; `P1-A` and `P1-B` are local-pass, `P1-C` and `P1-D` remain held.

Parent subproject: [Engineering Governance P1](README.md)

## Boundary Decision

This P1 slice fixes verified, narrow architecture and correctness issues. It
does not expand into broad runtime adapter or diagnostics callback refactors
while the worktree contains unrelated concurrent A5/A6 changes.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P1-A` | main thread | n/a | Repair the stale A2 structured-air architecture guard so it tracks current split-file ownership. | `tests/architecture/test_wp22_structural_guardrails.py` | Runtime behavior changes, weapon damage tuning | `pytest tests/architecture/test_wp22_structural_guardrails.py::test_a2_structured_air_effects_do_not_write_rl_score_authority -q` | Focused guard passes and still asserts Score writes stay out of structured-air path. | First; serial | 1 | pass |
| `P1-B` | main thread | n/a | Add centralized shape validation to the main scenario compiler and prefab merge path. | `python/scenario/compiler/validation.py`, `python/scenario/compiler/service.py`, `python/scenario/compiler/merge.py`, `tests/scenario/test_scenario_compiler.py` | Full JSON Schema, domain semantic validation, loader/runtime rewrite | `pytest tests/scenario/test_scenario_compiler.py -q` | Invalid consumed shapes fail closed; existing compiler tests pass. | After P1-A; serial in this run | 2 | pass |
| `P1-C` | future worker | n/a | Reduce duplicated runtime facade/world-batch capability probing through a bounded adapter slice. | future runtime adapter files only after packet is written | Callback refactors, training config changes | future focused runtime/world-batch tests | Separate packet exists with exact write set and broad validation. | Depends on P1-A/B closure; not parallel with runtime-heavy edits | 2 | held |
| `P1-D` | future worker | n/a | Split cooperative diagnostics callback responsibilities after active A5/A6 edits settle. | future callback/test files only after packet is written | RL algorithm changes, A5/A6 behavior tuning | future callback and training diagnostics tests | Separate packet exists and no overlapping callback edits are active. | Held until A5/A6 worktree noise settles | 2 | held |
| `P1-E` | main thread | n/a | Record task status, evidence, and parent review index links. | `docs/task/review/engineering_governance_p1/**`, `docs/task/review/README*` | Claiming all P1 work complete | Markdown inspection; `git diff --check` | Docs distinguish local-pass P1-A/B from held P1-C/D. | Last; serial | 1 | active |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not create a new conversation thread for this work.
- Do not allow two workers to edit the same task status table, scenario
  compiler validation module, runtime adapter, or callback file concurrently.
- P1-C and P1-D require fresh packets before implementation because their write
  sets are broader than this narrow run.
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
./.venv/bin/python -m pytest tests/architecture/test_wp22_structural_guardrails.py::test_a2_structured_air_effects_do_not_write_rl_score_authority -q
./.venv/bin/python -m pytest tests/scenario/test_scenario_compiler.py -q
./.venv/bin/python -m ruff check python/scenario/compiler/validation.py python/scenario/compiler/service.py python/scenario/compiler/merge.py tests/scenario/test_scenario_compiler.py tests/architecture/test_wp22_structural_guardrails.py
git diff --check -- tests/architecture/test_wp22_structural_guardrails.py python/scenario/compiler/validation.py python/scenario/compiler/service.py python/scenario/compiler/merge.py tests/scenario/test_scenario_compiler.py docs/task/review/engineering_governance_p1 docs/task/review/README.md docs/task/review/README.zh.md
```

## Acceptance Criteria

- P1-A architecture guard passes locally and asserts current ownership.
- P1-B scenario compiler tests pass locally and include negative shape cases.
- The task record does not mark P1-C/P1-D complete.
- Residuals are explicit enough for later packets.

## Validation Evidence

```text
test_a2_structured_air_effects_do_not_write_rl_score_authority: pass
tests/architecture/test_wp22_structural_guardrails.py: pass, 17 passed
tests/scenario/test_scenario_compiler.py: pass, 23 passed
ruff check for touched Python files: pass
git diff --check for touched P1 files: pass
scenario/prefab shape scan: pass, 50 JSON files
```

## Residual Map

Immediate:

- Re-run the focused validation before acceptance if later parallel edits touch
  architecture guardrails or scenario compiler files.

Follow-on:

- P1-C runtime facade/world-batch adapter narrowing.
- P1-D cooperative diagnostics callback split.
- Optional scenario JSON Schema publication if lightweight shape validation is
  later insufficient.

Deferred:

- Full scenario semantic validation.
- Broad runtime refactors.
