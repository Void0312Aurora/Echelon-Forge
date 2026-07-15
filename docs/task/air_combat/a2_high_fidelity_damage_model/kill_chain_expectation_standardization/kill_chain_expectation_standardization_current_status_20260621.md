# Kill-Chain Expectation Standardization Current Status

Status: `2026-07-15` accepted / retained expectation-standardization track plus
initial before-report harness implementation, a post-P5 component-response
threshold addendum, a standardized v0 expectation envelope, and a read-only
expectation-envelope audit. P0 subproject boundary is pass; P1 expectation
contract is pass with
`R_effect_policy=independent_review_variable`; P2 scenario matrix is pass; P3
metric mapping is pass; P4 harness plan is pass; P5 standard promotion decision
is pass. P6 admits engineering-proxy guarded single-layer dry-run plans, while
runtime parameter retuning and real-world authority remain held.

Chinese companion:
[kill_chain_expectation_standardization_current_status_20260621.zh.md](kill_chain_expectation_standardization_current_status_20260621.zh.md)

## Change Since Creation

- Created a dedicated A2 follow-on for idealized expectation standardization.
- Added the v0 expectation contract with normalized `rho_fuze` and `rho_effect`
  vocabulary.
- Added an AIM-120C-like engineering-proxy seed profile without real weapon or
  target authority.
- Linked the project from the parent A2 README files.
- Closed the P1 radius policy by keeping `R_effect` as an independent review
  variable.
- Added and closed the first P2 scenario expectation heatmap.
- Expanded the P2 acceptance object from a representative row list to a range x
  offset-angle matrix: the anchor grid covers
  `4/6/8/10/12/16 km` and `0/15/30/45/60/75/90 deg`, with a maneuver sparse
  grid for generality.
- Added a P2 sampling-density estimate: the coarse grid is only an anchor, the
  recommended P3/P4 main grid is about `572` signed cases per seed, and boundary
  cells receive local refinement.
- Selected the first `R_effect_variant` set for P3 / calibration-planning
  consumption: `REV-RUNTIME-PROJECTION`, `REV-EQ-FUZE`, and
  `REV-SMALLER-LOAD`.
- Added and closed P3 metric mapping, declaring stage-report fields, derived
  `rho_*` fields, `R_effect_variant` mapping, heatmap report row schema, and
  owner-guard fields.
- Added and closed the P4 harness plan, binding the P3 report row schema to
  case-grid batches, artifact family, a `32` worker pilot, P6 delta guard, and
  frozen-stage rules.
- Added and closed the original P5 standard promotion decision: at that time
  the P1-P4 content remained a task-local docs-only standard and did not write
  into `docs/standards`.
- Added the initial before-report harness:
  [kill_chain_harness_implementation_20260623.md](kill_chain_harness_implementation_20260623.md),
  with an `anchor-grid` case-grid generator, read-only decoupling-probe wrapper,
  and P3 heatmap-row projection.
- Added before-report visualization:
  [kces_anchor_cv_visualization_summary_20260623.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_visualization_summary_20260623.md),
  rendering the existing JSON into launch class, guidance status, `rho_fuze`,
  max failure probability, and effect band CSV/PNG/SVG matrices.
- Added first-review-stage attribution:
  [kces_anchor_cv_first_review_stage_summary_20260623.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_summary_20260623.md),
  splitting the current constant-velocity anchor rows into `4`
  `guidance_approach` review cells, `19` `no_review_pressure` cells, `21`
  `marginal_observation` cells, and `34` `negative_control_satisfied` cells.
- Added component-response local diagnosis:
  [kces_anchor_cv_response_diagnosis_summary_20260628.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_summary_20260628.md),
  now selecting zero `component_response` candidates for
  `REV-RUNTIME-PROJECTION` after the runtime spatial projection correction.
- Integrated before-report `component_detail`:
  `a2.kill_chain_expectation_component_detail.v1` is now a shared
  `component_detail_projection.py` read-only projection from the existing
  runtime facade. Response diagnosis consumes that projection and no longer
  reimplements lethality attribution inside KCES. The runtime variant now reads
  `missile_runtime_projection.resolved_projection_radius_m=9.0`, not the 15 m
  lethal radius.
- Added a post-P5 component-response quantization threshold addendum:
  [kill_chain_component_response_quantization_20260705.md](kill_chain_component_response_quantization_20260705.md),
  defining `trace_response`, `weak_response`, `nontrivial_response`,
  `material_response`, and `severe_response` from `p_max`, `delta_abs`, and an
  independent `sampled_failure_observed` flag. The current `4/6/8 km +/-30 deg`
  trace-response cells are `outside_effect` and satisfy the negative-control
  ceiling under the corrected runtime projection.
- Added a standardized v0 expectation envelope:
  [Air-To-Air Kill-Chain Expectation Envelope](../../../../standards/air/kill_chain_expectation_envelope.md),
  registering human-defined profile/grid/radius/band/tolerance inputs with
  derived report fields, launch/guidance envelope rules, effect-to-response
  floors and ceilings, distribution tolerances, continuity rules, cell status
  labels, and owner-stage attribution as an air-specialization planning
  supplement.
- Added a read-only expectation-envelope audit:
  [kces_anchor_cv_expectation_envelope_summary_20260706.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_summary_20260706.md),
  applying the standards-layer envelope to the existing `78` constant-velocity
  rows. After launch/guidance and marginal classifications were placed ahead of
  unrelated effect-metadata checks, the status counts are `4`
  `guidance_or_model_residual`, `21` `boundary_observation`, and `53`
  `satisfied`; this is a postprocessor result, not a simulation rerun,
  parameter edit, or calibration verdict.

## Maturity Matrix

| Item | State | Evidence | Boundary |
| --- | --- | --- | --- |
| Project boundary | pass | [README.md](README.md) | Docs-only; no runtime changes. |
| Expectation contract | pass | [kill_chain_idealized_expectation_contract_20260621.md](kill_chain_idealized_expectation_contract_20260621.md) | Ordinal bands only; no probability thresholds; `R_effect` remains independent. |
| Scenario matrix | pass | [kill_chain_scenario_expectation_matrix_20260622.md](kill_chain_scenario_expectation_matrix_20260622.md) | Heatmap cells classified, sampling-density estimate added, and first `R_effect_variant` set selected; metric mapping is now closed by P3. |
| Metric mapping | pass | [kill_chain_metric_mapping_20260623.md](kill_chain_metric_mapping_20260623.md) | Field contract exists; no runtime parameter value selected. |
| Calibration harness plan | pass | [kill_chain_calibration_harness_plan_20260623.md](kill_chain_calibration_harness_plan_20260623.md) | Plan exists; no batch simulation or runtime retuning performed. |
| Standard promotion decision | pass | [kill_chain_standard_promotion_decision_20260623.md](kill_chain_standard_promotion_decision_20260623.md) | Original P1-P4 decision retained the task-local workstream; the later v0 envelope is a planning supplement, not a runtime contract. |
| Harness initial implementation | partial | [kill_chain_harness_implementation_20260623.md](kill_chain_harness_implementation_20260623.md) | Full constant-velocity `78` case anchor before report, per-component `component_detail`, visualization heatmaps, first-review-stage attribution, and response local diagnosis exist; full `93` anchor/main grid, worker parallelism, and maneuver runtime support remain incomplete. |
| Component-response quantization thresholds | pass | [kill_chain_component_response_quantization_20260705.md](kill_chain_component_response_quantization_20260705.md) | Task-local docs-only diagnostic bands; grants no component-failure, Pk, or deterministic-fuze authority. |
| Standardized expectation envelope v0 | pass | [docs/standards/air/kill_chain_expectation_envelope.md](../../../../standards/air/kill_chain_expectation_envelope.md) | Air-specialization planning supplement; not a current runtime contract, no runtime parameter changes, and no calibration authority. |
| Expectation-envelope audit postprocessor | pass | [kces_anchor_cv_expectation_envelope_summary_20260706.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_summary_20260706.md) | Reads existing before report only; envelope fields are not yet emitted inline by the harness. |

## Residual Register

| Residual | Owner | Exit condition |
| --- | --- | --- |
| Probability / integrity thresholds now have a task-local v0 addendum but are not emitted by the harness yet | Future harness implementation | If machine consumption is needed, emit `component_response_quantized_band`, `component_response_sampled_failure_observed`, and `component_response_expectation_status` according to the addendum. |
| Standardized expectation envelope is available through a read-only postprocessor but not emitted inline by the harness yet | Future harness implementation | If machine consumption is needed inside the harness report, emit `a2.kill_chain_expectation_envelope.v0` fields such as `envelope_cell_status` and `envelope_owner_stage` from the before/after report. |
| Recommended main sampling grid not yet executed | Future harness implementation | The initial harness has generated the constant-velocity anchor before report and reviewable heatmaps; future execution produces the recommended-main before heatmap report. |
| Local `N` guidance residuals | Future guidance / launch-window review | Four `N` cells at `4/6 km` and `+/-45 deg` do not enter `R_fuze`; review P2 launch class or the guidance model. |
| Runtime projection source must remain explicit | Future harness maintenance | Keep `REV-RUNTIME-PROJECTION` bound to `missile_runtime_projection.resolved_projection_radius_m` and keep `REV-EQ-FUZE` separate as a declared sensitivity variant. |
| Worker parallelism and retry not implemented | Future harness implementation | Worker pool, failed-case retry, and batch summary writer exist. |
| Maneuvering-target runtime harness not implemented | Future harness implementation | `mild_maneuver` grid rows are no longer marked unsupported and have runtime facts. |
| Standards promotion held | Future standards promotion | Reopen under the standards maintenance policy only after accepted runtime/test/admission evidence exists. |
| Real authority unavailable | Future admission work | A future authority gate admits specific fields; until then all claims remain engineering proxy. |

## Recommended Next Steps

1. This P0-P5 workstream is closed; do not write runtime changes or treat the
   standards-layer envelope as a runtime contract in this batch.
2. Keep the four `guidance_approach` cells in the window / guidance review
   queue, and preserve the corrected 9 m runtime-projection source in all future
   before/after reports.
3. Preserve the P6 frozen-stage guard and authority boundary before any after
   report, parameter candidate, or standards promotion.

## Explicitly Refused Claims

- Real AIM-120C warhead, fuze, or fragment-pattern truth.
- Real F-16C vulnerability or component-failure truth.
- Deterministic fuze authority.
- Pk or stock weapon/target lethality authority.
- Runtime calibration authority from this docs-only seed.
