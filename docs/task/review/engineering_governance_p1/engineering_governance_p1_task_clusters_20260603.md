# Engineering Governance P1 Task Clusters

Status: `2026-06-04` finite task-cluster record for the P1 remediation slice; `P1-A`, `P1-B`, bounded `P1-C`, and narrow `P1-D1`/`P1-D2`/`P1-D3`/`P1-D4`/`P1-D5`/`P1-D6`/`P1-D7`/`P1-D8` are local-pass, while the broader `P1-D` callback split remains held.

Parent subproject: [Engineering Governance P1](README.md)

## Boundary Decision

This P1 slice fixes verified, narrow architecture and correctness issues. It
does not expand into broad runtime adapter splits or full diagnostics callback
refactors. The callback work in this slice is limited to policy-distribution,
HMoE, action, leader, step reward, A6 event-window info, A5 event info, and
runway/gear diagnostics helper extractions that preserve the existing callback
entry points.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P1-A` | main thread | n/a | Repair the stale A2 structured-air architecture guard so it tracks current split-file ownership. | `tests/architecture/test_wp22_structural_guardrails.py` | Runtime behavior changes, weapon damage tuning | `pytest tests/architecture/test_wp22_structural_guardrails.py::test_a2_structured_air_effects_do_not_write_rl_score_authority -q` | Focused guard passes and still asserts Score writes stay out of structured-air path. | First; serial | 1 | pass |
| `P1-B` | main thread | n/a | Add centralized shape validation to the main scenario compiler and prefab merge path. | `python/scenario/compiler/validation.py`, `python/scenario/compiler/service.py`, `python/scenario/compiler/merge.py`, `tests/scenario/test_scenario_compiler.py` | Full JSON Schema, domain semantic validation, loader/runtime rewrite | `pytest tests/scenario/test_scenario_compiler.py -q` | Invalid consumed shapes fail closed; existing compiler tests pass. | After P1-A; serial in this run | 2 | pass |
| `P1-C` | main thread | n/a | Reduce duplicated RuntimeFacadeAdapter-owned capability probing through a bounded capability snapshot. | `python/rl/runtime/world_batch/adapter.py`, `python/rl/runtime/world_batch/__init__.py`, `tests/world_batch/test_world_batch_vec_env.py` | Callback refactors, training config changes, full adapter split, world-batch env base-class extraction | `pytest tests/world_batch/test_world_batch_vec_env.py -k "adapter_capability_snapshot or legacy_task_order_batch_writer_is_removed or task_order_reverse_projection_stays_removed or task_order_write_routes_through_maintained_helper or apply_launch_requests or step_worlds" -q` | Capability snapshot exists, refreshes on facade swap, and focused world-batch tests pass. | After P1-A/B; serial due runtime surface | 2 | pass |
| `P1-D1` | main thread | n/a | Extract policy-distribution diagnostics from `CMODiagnosticsCallback` into a focused helper while preserving the current callback method. | `python/training/diagnostics.py`, `python/training_callbacks.py` | Full callback class decomposition, RL algorithm changes, A5/A6 behavior tuning | `pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q` | Existing diagnostics tests pass and the public callback method remains available. | After P1-C; serial due callback touch | 1 | pass |
| `P1-D2` | main thread | n/a | Extract HMoE route/parameter diagnostics from `CMODiagnosticsCallback` into a focused helper while preserving parameter-stat throttling. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | Full callback class decomposition, RL algorithm changes, changing HMoE stat keys | `pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q` | Existing callback route/param stats still log; helper test proves parameter stats remain throttled. | After P1-D1; serial due callback touch | 1 | pass |
| `P1-D3` | main thread | n/a | Extract full/hybrid action diagnostics from `CMODiagnosticsCallback` into a focused helper while preserving logged scalar keys. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | Full callback class decomposition, RL algorithm changes, changing action schema semantics | `pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q` | Existing callback action stats still log; helper test proves full-action brake and combat switch semantics. | After P1-D2; serial due callback touch | 1 | pass |
| `P1-D4` | main thread | n/a | Extract leader observation/info/reward diagnostics from `CMODiagnosticsCallback` into a focused helper while preserving logged scalar keys. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | Full callback class decomposition, RL algorithm changes, changing leader stat keys | `pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q` | Existing callback leader stats still log; helper test proves observation, bucket, C2, and reward semantics. | After P1-D3; serial due callback touch | 1 | pass |
| `P1-D5` | main thread | n/a | Extract step reward-term diagnostics from `CMODiagnosticsCallback` into a focused helper while preserving logged scalar keys. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | Full callback class decomposition, RL algorithm changes, changing reward stat keys | `pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q` | Existing callback reward-term stats still log; helper test proves reward-term mean and missing-key behavior. | After P1-D4; serial due callback touch | 1 | pass |
| `P1-D6` | main thread | n/a | Extract A6 first-event info diagnostics from `CMODiagnosticsCallback` into a focused helper while preserving logged scalar keys. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_a6_event_value_diagnostics_callback.py` | Full callback class decomposition, RL algorithm changes, changing A6 stat keys or label semantics | `pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q` | Existing callback A6 info stats still log; helper test proves label-count and stable-zero behavior. | After P1-D5; serial due callback touch | 1 | pass |
| `P1-D7` | main thread | n/a | Extract A5 event info diagnostics from `CMODiagnosticsCallback` into a focused helper while preserving logged scalar keys. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | Full callback class decomposition, RL algorithm changes, changing A5 stat keys or release-discipline semantics | `pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q` | Existing callback A5 info stats still log; helper test proves event-rate, rejection, state, and component logging. | After P1-D6; serial due callback touch | 1 | pass |
| `P1-D8` | main thread | n/a | Extract runway/gear step info diagnostics from `CMODiagnosticsCallback` into a focused helper while preserving logged scalar keys. | `python/training/diagnostics.py`, `python/training_callbacks.py`, `tests/training/test_cooperative_diagnostics_callback.py` | Full callback class decomposition, RL algorithm changes, changing runway/gear stat keys | `pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q` | Existing callback runway/gear stats still log; helper test proves runway, cross-track tail, gear-collapse, and gear-stress logging. | After P1-D7; serial due callback touch | 1 | pass |
| `P1-D` | future worker | n/a | Split remaining basic reward/instrument scalar, terminal/preterm window, and cooperative/stateful event-window diagnostics callback responsibilities. | future callback/test files only after packet is written | RL algorithm changes, A5/A6 behavior tuning, reworking P1-D1/D2/D3/D4/D5/D6/D7/D8 helpers without need | future callback and training diagnostics tests | Separate packet exists and no overlapping callback edits are active. | Held until each responsibility has a bounded packet | 2 | held |
| `P1-E` | main thread | n/a | Record task status, evidence, and parent review index links. | `docs/task/review/engineering_governance_p1/**`, `docs/task/review/README*` | Claiming all P1 work complete | Markdown inspection; `git diff --check` | Docs distinguish local-pass P1-A/B/C/D1/D2/D3/D4/D5/D6/D7/D8 from held broader P1-D. | Last; serial | 1 | active |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not create a new conversation thread for this work.
- Do not allow two workers to edit the same task status table, scenario
  compiler validation module, runtime adapter, or callback file concurrently.
- P1-D requires a fresh packet before broader implementation because its write
  set is broader than the P1-D1/P1-D2/P1-D3/P1-D4/P1-D5/P1-D6/P1-D7/P1-D8 helper extractions in this run.
- A future full adapter split or `typing.Protocol` loader contract also requires
  a separate packet; P1-C only centralizes adapter-owned capability resolution.
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
./.venv/bin/python -m pytest tests/world_batch/test_world_batch_vec_env.py -k "adapter_capability_snapshot or legacy_task_order_batch_writer_is_removed or task_order_reverse_projection_stays_removed or task_order_write_routes_through_maintained_helper or apply_launch_requests or step_worlds" -q
./.venv/bin/python -m pytest tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py -q
./.venv/bin/python -m ruff check python/scenario/compiler/validation.py python/scenario/compiler/service.py python/scenario/compiler/merge.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch/__init__.py python/training/diagnostics.py python/training_callbacks.py tests/scenario/test_scenario_compiler.py tests/architecture/test_wp22_structural_guardrails.py tests/world_batch/test_world_batch_vec_env.py tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py
git diff --check -- tests/architecture/test_wp22_structural_guardrails.py python/scenario/compiler/validation.py python/scenario/compiler/service.py python/scenario/compiler/merge.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch/__init__.py python/training/diagnostics.py python/training_callbacks.py tests/scenario/test_scenario_compiler.py tests/world_batch/test_world_batch_vec_env.py tests/training/test_cooperative_diagnostics_callback.py tests/training/test_a6_event_value_diagnostics_callback.py docs/task/review/engineering_governance_p1 docs/task/review/README.md docs/task/review/README.zh.md docs/evaluation/architecture_review_20260603.md docs/evaluation/architecture_review_20260603.zh.md docs/evaluation/architecture_review_claim_verification_20260603.zh.md docs/evaluation/architecture_norms_correctness_review_20260603.zh.md docs/evaluation/architecture_structure_assessment_20260603.zh.md
```

## Acceptance Criteria

- P1-A architecture guard passes locally and asserts current ownership.
- P1-B scenario compiler tests pass locally and include negative shape cases.
- P1-C adapter-owned probing uses a named capability snapshot and focused tests
  prove it refreshes after facade swaps.
- P1-D1 policy-distribution diagnostics are extracted behind the existing
  callback method and focused diagnostics tests pass.
- P1-D2 HMoE diagnostics are extracted behind the existing callback method and
  focused diagnostics tests prove parameter-stat throttling.
- P1-D3 action diagnostics are extracted behind the existing callback method
  and focused diagnostics tests prove full-action brake/combat switch logging.
- P1-D4 leader diagnostics are extracted behind the existing callback method
  and focused diagnostics tests prove observation, bucket, C2, and reward
  logging.
- P1-D5 step reward-term diagnostics are extracted behind the existing callback
  method and focused diagnostics tests prove mean logging and missing-key
  behavior.
- P1-D6 A6 first-event info diagnostics are extracted behind the existing
  callback method and focused diagnostics tests prove label-count and
  stable-zero behavior.
- P1-D7 A5 event info diagnostics are extracted behind the existing callback
  method and focused diagnostics tests prove event-rate, rejection, state, and
  component logging.
- P1-D8 runway/gear step info diagnostics are extracted behind the existing
  callback method and focused diagnostics tests prove runway, cross-track tail,
  gear-collapse, and gear-stress logging.
- The task record does not mark broader P1-D or a broader adapter split
  complete.
- Residuals are explicit enough for later packets.

## Validation Evidence

```text
test_a2_structured_air_effects_do_not_write_rl_score_authority: pass
tests/architecture/test_wp22_structural_guardrails.py: pass, 17 passed
tests/scenario/test_scenario_compiler.py: pass, 23 passed
world-batch adapter focused tests: pass, 6 selected passed
training diagnostics focused tests: pass, 15 passed
ruff check for touched Python files: pass
git diff --check for touched P1 files: pass
scenario/prefab shape scan: pass, 50 JSON files
```

## Residual Map

Immediate:

- Re-run the focused validation before acceptance if later parallel edits touch
  architecture guardrails, scenario compiler files, or world-batch adapter files.

Follow-on:

- P1-D basic reward/instrument scalar, terminal/preterm window, and
  cooperative/stateful event-window diagnostics callback split;
  P1-D1/D2/D3/D4/D5/D6/D7/D8 extracted policy distribution, HMoE, action,
  leader, step reward, A6 event-window info, A5 event info, and runway/gear
  diagnostics.
- Full adapter split or `typing.Protocol` loader/runtime contract after the
  capability snapshot proves stable.
- Optional scenario JSON Schema publication if lightweight shape validation is
  later insufficient.

Deferred:

- Full scenario semantic validation.
- Broad runtime refactors.
