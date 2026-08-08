# Kill-Chain Expectation Standardization Task Clusters

Status: `2026-06-23` finite task-cluster plan for
[Kill-Chain Expectation Standardization](README.md). P0-P5 are pass.

Chinese companion:
[kill_chain_expectation_standardization_task_clusters_20260621.zh.md](kill_chain_expectation_standardization_task_clusters_20260621.zh.md)

## Boundary Decision

This subproject may define expectation contracts, scenario matrices, metric
mappings, and calibration-harness plans. It must not retune runtime parameters,
edit weapon/target descriptors, or claim real AIM-120C/F-16C/Pk authority.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `KCES-P0 Project Boundary` | main thread | n/a | Create the subproject, status, queue, archive entry, and parent A2 links. | `docs/domains/air/reviews/kill_chain_expectation_standardization_20260706/**`; parent A2 README files | Runtime/code/test changes; standards promotion | `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model` | Required files exist, parent README links this project, and forbidden claims are explicit. | first, serial | 1 | pass |
| `KCES-P1 Expectation Contract` | main thread | n/a | Define stage contract, normalized bands, AIM-120C-like seed profile, and generic row template. | Contract docs inside this subproject | Numeric probability calibration; real weapon authority | Markdown/link review and `git diff --check` | Contract explains 10 m-class ambiguity only through declared profile fields and closes `R_effect_policy=independent_review_variable`. | after P0 | 2 | pass |
| `KCES-P2 Scenario Matrix` | main thread | n/a | Add range x offset-angle heatmap covering nominal, marginal, and outside-envelope cells, plus a follow-on sampling-density estimate. | Scenario matrix docs inside this subproject | Runtime simulation changes; learned-policy evidence | Matrix review plus `git diff --check` | Heatmap declares range axis, offset-angle axis, target-motion layer, launch-window class, expected stage bands, recommended main-grid / seed budget, and first `R_effect_variant` handoff. | after P1 | 2 | pass |
| `KCES-P3 Metric Mapping` | main thread | n/a | Map ordinal expectation bands to existing or planned stage-report fields. | Metric mapping doc; optional diagnostics-readiness checklist | Parameter values; descriptor edits | Docs check and field-reference review | Each metric is owned by one stage or marked cross-stage; heatmap report row schema exists. | after P2 | 2 | pass |
| `KCES-P4 Calibration Harness Plan` | main thread | n/a | Bind expectation rows to P6 single-layer before/after and delta-guard requirements. | Harness plan doc; optional dry-run artifact path proposal | Running full calibration or changing runtime parameters | Docs check; optional CLI dry-run if artifacts already exist | Plan rejects cross-layer changes and names frozen stage ids. | after P3 | 2 | pass |
| `KCES-P5 Closure / Promotion Decision` | main thread | n/a | Record accepted/held residuals and decide whether any stable contract belongs in `docs/standards`. | [kill_chain_standard_promotion_decision_20260623.md](kill_chain_standard_promotion_decision_20260623.md) and README/status/task-cluster updates | Silent standards promotion; overclaiming accepted runtime behavior | Docs diff check and parent index sync | Status, residuals, and parent README agree; decision is retained task-local standard. | last, serial | 1 | pass |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not let two workers edit the contract, status line, or parent README links
  concurrently.
- Runtime descriptors, C++/Python code, tests, and scenario configs remain out
  of scope until P4 explicitly opens a docs-only harness plan.
- Keep closure and standards-promotion decisions serial.
- Do not create a new Codex session thread; any delegated worker must remain in
  the current session and within the cluster write set.

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
git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model
```

Future clusters may add link checks, schema checks, or diagnostics dry runs, but
P0/P1 are documentation-only.

## Acceptance Criteria

- The contract distinguishes expectation stages and forbidden authority claims.
- Scenario rows cannot be interpreted without declared `R_fuze`, `R_effect`,
  target proxy, and geometry class.
- Calibration follow-on work can target one layer at a time.
- Real weapon, real target, deterministic-fuze, and Pk authority remain refused.

## Residual Map

Immediate:

- None. This P0-P5 docs-only workstream is closed.

Follow-on:

- Future harness implementation: implement the P4 CLI / artifact path and
  generate a before heatmap report.
- Future standards promotion: reopen only after accepted runtime/test/admission
  evidence exists.

Deferred:

- Runtime parameter changes.
- Descriptor edits.
- Real-world authority admission.
