# Kill-Chain Expectation Standardization Current Status

Status: `2026-06-28` accepted / retained task-local standard plus initial
before-report harness implementation. P0 subproject boundary is pass; P1
expectation contract is pass with
`R_effect_policy=independent_review_variable`; P2 scenario matrix is pass; P3
metric mapping is pass; P4 harness plan is pass; P5 standard promotion decision
is pass; runtime calibration remains held.

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
- Added and closed the P5 standard promotion decision: the P1-P4 content remains
  a task-local docs-only standard, and this batch does not write into
  `docs/standards`.
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
  `guidance_approach` review cells, `6` `component_response` review cells,
  `13` `no_review_pressure` cells, `21` `marginal_observation` cells, and
  `34` `negative_control_satisfied` cells.
- Added component-response local diagnosis:
  [kces_anchor_cv_response_diagnosis_summary_20260628.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_summary_20260628.md),
  classifying all six `component_response` cells as
  `outer_effect_low_component_load_probability_cliff`, where the case-level
  `outer_effective` band maps to weak component load scale and very low
  response probability.
- Integrated before-report `component_detail`:
  `a2.kill_chain_expectation_component_detail.v1` is now a shared
  `component_detail_projection.py` read-only projection from the existing
  runtime facade. Response diagnosis consumes that projection and no longer
  reimplements lethality attribution inside KCES. All six `component_response`
  cells have
  `detail_projection_signal=all_component_rows_weak_load_low_response`.

## Maturity Matrix

| Item | State | Evidence | Boundary |
| --- | --- | --- | --- |
| Project boundary | pass | [README.md](README.md) | Docs-only; no runtime changes. |
| Expectation contract | pass | [kill_chain_idealized_expectation_contract_20260621.md](kill_chain_idealized_expectation_contract_20260621.md) | Ordinal bands only; no probability thresholds; `R_effect` remains independent. |
| Scenario matrix | pass | [kill_chain_scenario_expectation_matrix_20260622.md](kill_chain_scenario_expectation_matrix_20260622.md) | Heatmap cells classified, sampling-density estimate added, and first `R_effect_variant` set selected; metric mapping is now closed by P3. |
| Metric mapping | pass | [kill_chain_metric_mapping_20260623.md](kill_chain_metric_mapping_20260623.md) | Field contract exists; no runtime parameter value selected. |
| Calibration harness plan | pass | [kill_chain_calibration_harness_plan_20260623.md](kill_chain_calibration_harness_plan_20260623.md) | Plan exists; no batch simulation or runtime retuning performed. |
| Standard promotion decision | pass | [kill_chain_standard_promotion_decision_20260623.md](kill_chain_standard_promotion_decision_20260623.md) | Decision is retained task-local standard; this batch does not write into `docs/standards`. |
| Harness initial implementation | partial | [kill_chain_harness_implementation_20260623.md](kill_chain_harness_implementation_20260623.md) | Full constant-velocity `78` case anchor before report, per-component `component_detail`, visualization heatmaps, first-review-stage attribution, and response local diagnosis exist; full `93` anchor/main grid, worker parallelism, and maneuver runtime support remain incomplete. |

## Residual Register

| Residual | Owner | Exit condition |
| --- | --- | --- |
| Probability / integrity thresholds remain unquantified | KCES-P4/future evidence | P4 or follow-on admission work justifies thresholds; P3 only carries report fields. |
| Recommended main sampling grid not yet executed | Future harness implementation | The initial harness has generated the constant-velocity anchor before report and reviewable heatmaps; future execution produces the recommended-main before heatmap report. |
| `8 km / 30 deg` needs follow-on interpretation / calibration decision | Future factor decomposition | The before report shows `R_fuze` entry, first-review-stage attribution is `component_response`, and report-level diagnosis is `outer_effect_low_component_load_probability_cliff`; per-component load/response details are now preserved through the shared projection, so follow-on work should decompose the cliff cause into spatial projection, receiver exposure / armor / threshold, or response curve. |
| Local `N` guidance residuals | Future guidance / launch-window review | Four `N` cells at `4/6 km` and `+/-45 deg` do not enter `R_fuze`; review P2 launch class or the guidance model. |
| Local `N` low-response residuals | Future factor decomposition | Six `N` cells at `4/6/8 km` and `+/-30 deg` enter `R_fuze` and have outer-effective load bands, but no sampled response failure; same-range `15 deg` sampled-response baselines show max failure probability ratios of about `0.72%~0.98%`, and per-component `detail_projection_signal` is `all_component_rows_weak_load_low_response` for all six. |
| Worker parallelism and retry not implemented | Future harness implementation | Worker pool, failed-case retry, and batch summary writer exist. |
| Maneuvering-target runtime harness not implemented | Future harness implementation | `mild_maneuver` grid rows are no longer marked unsupported and have runtime facts. |
| Standards promotion held | Future standards promotion | Reopen under the standards maintenance policy only after accepted runtime/test/admission evidence exists. |
| Real authority unavailable | Future admission work | A future authority gate admits specific fields; until then all claims remain engineering proxy. |

## Recommended Next Steps

1. This P0-P5 docs-only workstream is closed; do not write runtime or
   `docs/standards` changes in this batch.
2. Use the shared projection output for per-component `component_loads[]` /
   `component_responses[]` details to decompose the response-cliff cause while
   keeping the four `guidance_approach` cells in the window / guidance review
   queue.
3. Preserve the P6 frozen-stage guard and authority boundary before any after
   report, parameter candidate, or standards promotion.

## Explicitly Refused Claims

- Real AIM-120C warhead, fuze, or fragment-pattern truth.
- Real F-16C vulnerability or component-failure truth.
- Deterministic fuze authority.
- Pk or stock weapon/target lethality authority.
- Runtime calibration authority from this docs-only seed.
