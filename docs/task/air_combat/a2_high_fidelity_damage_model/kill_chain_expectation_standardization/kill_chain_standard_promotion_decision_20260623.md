# Kill-Chain Standard Promotion Decision

Status: `2026-06-23` P5 pass closeout / promotion decision for
[Kill-Chain Expectation Standardization](README.md).

Chinese companion:
[kill_chain_standard_promotion_decision_20260623.zh.md](kill_chain_standard_promotion_decision_20260623.zh.md)

## Inputs

- P1 expectation contract:
  [kill_chain_idealized_expectation_contract_20260621.md](kill_chain_idealized_expectation_contract_20260621.md)
- P2 scenario matrix:
  [kill_chain_scenario_expectation_matrix_20260622.md](kill_chain_scenario_expectation_matrix_20260622.md)
- P3 metric mapping:
  [kill_chain_metric_mapping_20260623.md](kill_chain_metric_mapping_20260623.md)
- P4 harness plan:
  [kill_chain_calibration_harness_plan_20260623.md](kill_chain_calibration_harness_plan_20260623.md)
- Standards maintenance policy:
  [../../../../standards/governance/standards_maintenance_policy.md](../../../../standards/governance/standards_maintenance_policy.md)
- Standards tree overview:
  [../../../../standards/README.md](../../../../standards/README.md)

## Decision Summary

| Field | Decision |
| --- | --- |
| `decision_id` | `KCES-P5-20260623` |
| `promotion_decision` | `retain_task_local_standard` |
| `standards_tree_write` | `none` |
| `runtime_calibration_authority` | `false` |
| `accepted_scope` | P1-P4 docs-only expectation contract, heatmap constraints, metric-field mapping, and harness plan. |
| `held_scope` | Runtime parameters, descriptors, batch simulation results, probability / integrity thresholds, real weapon / target authority, and global standards promotion. |

Conclusion: this subproject closes P5 as an
`accepted / retained task-local docs-only standard`. The P1-P4 content is strong
enough to constrain A2 calibration before runtime retuning, but it is not yet
strong enough to enter `docs/standards/` as a project-level maintained standard.

## Promotion Evaluation

| Content | Current maturity | P5 decision | Future promotion condition |
| --- | --- | --- | --- |
| Stage split and authority boundary | Stable task-local vocabulary. | Keep inside this subproject; do not add a standards page. | Reconsider if multiple air-combat follow-ons reuse the same vocabulary. |
| P2 range x offset-angle heatmap | Expectation matrix exists, but no runtime heatmap has been executed. | Retain as a task-local calibration oracle. | Consider an air-to-air calibration-report convention after accepted before/after heatmap evidence exists. |
| P3 report row schema | Field mapping exists, with some fields still planned-harness. | Retain as a task-local report schema. | CLI / artifact implementation exists and fields are stable test or diagnostic outputs. |
| P4 harness plan | Plan is complete, but no batch artifact exists. | Retain as the future implementation entry; do not promote. | Smoke / pilot / main-grid execution passes the delta guard, then evaluate a generic harness convention. |
| Real authority refusal | Already governed by foundation policy. | Do not duplicate into a new standard; keep referencing existing admission rules. | Update only after a future admission gate grants explicit fields. |

## Acceptance Boundary

Accepted:

- The P1-P4 documents, vocabulary, and report fields can constrain future A2
  kill-chain calibration work.
- `R_effect_policy=independent_review_variable` remains effective.
- The P2 main-grid recommendation, boundary-refinement budget, and first
  `R_effect_variant` set remain future harness inputs.
- The P3/P4 single-layer guard constraints remain entry conditions for future
  runtime calibration.

Held:

- No claim that the current 8 km / 30 deg runtime behavior has been calibrated.
- No claim that a 10 m-class proximity event is always lethal or always
  non-lethal.
- No probability thresholds, integrity thresholds, or real warhead parameters.
- No runtime, descriptor, test, or `docs/standards/` changes.

## Future Entries

After P5, this subproject has no remaining P0-P5 queue work. Follow-on work
must enter through a newly named workstream:

| Future entry | Trigger | Write scope |
| --- | --- | --- |
| `KCES-FUTURE-HARNESS-IMPLEMENTATION` | User asks to implement the P4 plan as CLI / artifacts. | tools/tests/docs evidence, still without default parameter retuning. |
| `KCES-FUTURE-BEFORE-HEATMAP` | Harness exists and a before report is needed. | evidence artifact + current status, no standards write. |
| `KCES-FUTURE-STANDARDS-PROMOTION` | Accepted runtime/test/admission evidence exists. | Open a review/task gap first, then update under the standards maintenance policy. |

## Closeout

P5 is pass. The recommended current state is:

```text
subproject_status = accepted_retained_task_local_docs_only_standard
standards_promotion = held_until_runtime_evidence
runtime_calibration = held
authority_claims = refused
```
