# Kill-Chain Expectation Standardization

Status: `2026-06-28` accepted / retained task-local docs-only standard plus
post-P5 KCES harness diagnostics. This subproject defines idealized kill-chain
expectation contracts before runtime parameter retuning. It does not claim real
AIM-120C, F-16C, deterministic fuze, or Pk authority.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent A2 index: [../README.md](../README.md)
- Existing kill-chain calibration note:
  [../kill_chain_guidance_lethality_calibration_20260621.zh.md](../kill_chain_guidance_lethality_calibration_20260621.zh.md)
- Existing mechanism-decoupling record:
  [../kill_chain_mechanism_decoupling_analysis_20260621.zh.md](../kill_chain_mechanism_decoupling_analysis_20260621.zh.md)
- Calibration admission gate:
  [../kill_chain_calibration_admission_gate_20260621.zh.md](../kill_chain_calibration_admission_gate_20260621.zh.md)
- Foundation realism rule:
  [../../../../standards/foundation/gradient_realism_principles.md](../../../../standards/foundation/gradient_realism_principles.md)
- Public source admission rule:
  [../../../../standards/foundation/public_data_source_admission.md](../../../../standards/foundation/public_data_source_admission.md)
- Standards maintenance policy:
  [../../../../standards/governance/standards_maintenance_policy.md](../../../../standards/governance/standards_maintenance_policy.md)
- Repository AIM-120C-like proxy descriptor:
  [../../../../../examples/config/database/weapons/air_to_air/aim_120c.json](../../../../../examples/config/database/weapons/air_to_air/aim_120c.json)
- Repository F-16C-like synthetic target descriptor:
  [../../../../../examples/config/database/aircraft/units/f16c_block50.json](../../../../../examples/config/database/aircraft/units/f16c_block50.json)

## Purpose

This subproject creates the upstream expectation standard needed before kill-chain
calibration. The immediate problem is not "what number should be bigger"; it is
that the project needs a declared idealized oracle for launch-window behavior,
guidance miss distance, proximity-fuze trigger, warhead load field, component
response, and consequence projection.

The first reference case is an AIM-120C-like active-radar, blast-fragmentation
engineering proxy against a fighter-size synthetic target. The wording is
intentional: this is an engineering expectation envelope for the repository, not
a real AIM-120C performance claim.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Guidance/lethality symptom diagnosis | retained | Existing 8 km / 30 deg reports under the parent A2 directory | Describes current behavior; it is not the expectation standard. |
| Kill-chain stage decoupling | retained / implemented diagnostics | Existing facade, scalar ledger, named load factors, and response-owner records | Enables staged calibration checks; it does not choose idealized outcomes. |
| Calibration admission | engineering proxy guarded | P6 gate allows single-layer engineering-proxy planning | Does not grant real-world authority or cross-layer retuning. |
| Expectation standardization | accepted / retained task-local | This subproject, the P1-P5 closeout, and post-P5 KCES harness diagnostics | Docs-only standard plus read-only diagnostics; no runtime parameter changes and no global standards promotion. |

## Scope

In scope:

- Define idealized stage expectations before parameter calibration.
- Use normalized miss distance and declared radii instead of undeclared fixed
  meter claims.
- Separate launch-window, guidance, fuze, warhead, component-response, and
  consequence expectations.
- Provide an AIM-120C-like seed profile and a generic air-to-air template.
- Keep all claims inside repository engineering-proxy authority.

Out of scope:

- No real AIM-120C warhead, fuze, fragment-pattern, or Pk authority.
- No real F-16C vulnerability or component-failure authority.
- No runtime retuning, descriptor edits, or tests in the P0 docs seed.
- No use of current weak/strong runtime output as the expectation standard.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Create the subproject and freeze authority language. | User requests standardization subproject. | README, task clusters, status, queue, archive entry, and parent A2 links exist. | pass |
| `P1 Expectation Contract` | Draft the idealized stage contract and AIM-120C-like seed profile. | P0 boundary accepted. | Contract declares stages, normalized bands, profile fields, forbidden claims, and `R_effect_policy=independent_review_variable`. | pass |
| `P2 Scenario Matrix` | Convert the contract into a range x offset-angle heatmap constraint. | P1 contract reviewed. | Heatmap separates nominal, marginal, and outside-envelope cells, includes an anchor grid, recommended main sampling grid, maneuver sparse grid, boundary-refinement budget, and selects the first `R_effect_variant` evaluation set. | pass |
| `P3 Metric Mapping` | Map ordinal bands to measurable report fields. | P2 matrix exists. | Metrics identify stage report fields, `R_effect_variant` derivation rules, heatmap report row schema, and guard fields without selecting runtime parameter values. | pass |
| `P4 Calibration Harness Plan` | Bind single-layer calibration dry runs to expectation bands. | P3 metrics exist and P6 guard remains available. | Plan names layer-by-layer before/after checks, frozen-stage guards, artifact family, case-grid batches, and worker-pilot policy. | pass |
| `P5 Standard Promotion Decision` | Decide whether stable pieces move into `docs/standards`. | P1-P4 reviewed. | Retained task-local standard is recorded; this batch does not write into `docs/standards`. | pass |

## Task Clusters

- Task cluster plan:
  [kill_chain_expectation_standardization_task_clusters_20260621.md](kill_chain_expectation_standardization_task_clusters_20260621.md)
- Current dispatch queue:
  [kill_chain_expectation_standardization_dispatch_queue_20260621.md](kill_chain_expectation_standardization_dispatch_queue_20260621.md)
- Current status:
  [kill_chain_expectation_standardization_current_status_20260621.md](kill_chain_expectation_standardization_current_status_20260621.md)

## Outputs And Evidence

- Initial idealized expectation contract:
  [kill_chain_idealized_expectation_contract_20260621.md](kill_chain_idealized_expectation_contract_20260621.md)
- Initial scenario expectation matrix:
  [kill_chain_scenario_expectation_matrix_20260622.md](kill_chain_scenario_expectation_matrix_20260622.md)
- Metric mapping and heatmap report row schema:
  [kill_chain_metric_mapping_20260623.md](kill_chain_metric_mapping_20260623.md)
- Calibration harness plan:
  [kill_chain_calibration_harness_plan_20260623.md](kill_chain_calibration_harness_plan_20260623.md)
- Standard promotion decision:
  [kill_chain_standard_promotion_decision_20260623.md](kill_chain_standard_promotion_decision_20260623.md)
- Harness initial implementation:
  [kill_chain_harness_implementation_20260623.md](kill_chain_harness_implementation_20260623.md)
- Constant-velocity anchor before-report visualization:
  [kces_anchor_cv_visualization_summary_20260623.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_visualization_summary_20260623.md)
- Constant-velocity anchor first-review-stage attribution:
  [kces_anchor_cv_first_review_stage_summary_20260623.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_summary_20260623.md)
- Constant-velocity anchor component-response local diagnosis:
  [kces_anchor_cv_response_diagnosis_summary_20260628.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_summary_20260628.md)
- P0-P5 themselves produce documentation and contract language only. The
  post-P5 initial harness implementation adds a read-only diagnostic wrapper,
  tests, heatmap visualization, first-review-stage attribution, and
  component-response report-level local diagnosis; the before report now also
  preserves per-component `component_detail` load/response pairs through the
  shared `component_detail_projection.py` read-only projection from the existing
  runtime facade, and response diagnosis consumes that projection. It
  intentionally leaves runtime descriptors, default parameters, simulation
  behavior, and calibration data unchanged.

## Acceptance Gate

This subproject can be marked accepted only when:

- The idealized expectation contract distinguishes launch-window, guidance,
  fuze, warhead, component-response, and consequence expectations.
- The AIM-120C-like seed profile declares every proxy assumption it uses.
- The contract can express whether a 10 m-class miss is core, effective, edge,
  or out of envelope by reference to a declared radius, not by assertion.
- Follow-on calibration can map each expectation to exactly one kill-chain
  stage or explicitly mark it as cross-stage.
- P5 has recorded the standard-promotion decision: this remains a task-local
  docs-only standard and does not write into `docs/standards`.
- Real weapon, real target, deterministic fuze, and Pk authority remain refused
  unless a future admission gate explicitly grants them.

## Residuals And Next Steps

- `P1-A` is closed as pass with `R_effect` kept as an independent review
  variable.
- `P2` is closed as pass for a range x offset-angle heatmap:
  `4/6/8/10/12/16 km` and `0/15/30/45/60/75/90 deg` are anchor points; the
  recommended P3/P4 main sampling grid uses `4..16 km` at `1 km` steps and
  signed `0..90 deg` bearings at `5 deg` steps, about `572` cases per seed,
  plus local refinement along `N/M` and `M/O` boundaries. It
  selected `REV-RUNTIME-PROJECTION`, `REV-EQ-FUZE`, and `REV-SMALLER-LOAD` as
  the first evaluation variants while keeping `REV-DECLARED-EFFECT` held.
- `P3` is closed as pass: heatmap cells, sampling tiers, `R_effect_variant`
  values, and owner guards are mapped to stage-report / derived-report fields.
  `REV-SMALLER-LOAD` still requires a P4-declared `declared_effect_radius_m`;
  it has no default meter value.
- `P4` is closed as pass: the P3 report row schema is bound to a harness plan
  with a `32` worker pilot batch, `48-64` worker escalation criteria, P6 delta
  guard, and frozen-stage rules. `guidance_approach` remains read-only in this
  harness.
- `P5` is closed as pass: this subproject remains an accepted / retained
  task-local docs-only standard; this batch does not write into
  `docs/standards`, and future standards promotion reopens only after accepted
  runtime/test/admission evidence exists.
- Post-P5 initial harness implementation has started:
  `tools/diagnostics/kill_chain_expectation_harness.py` can generate the
  `anchor-grid` case grid and has generated the full constant-velocity `78`
  case before report. `tools/diagnostics/kill_chain_expectation_visualize.py`
  has rendered that before report into launch class, guidance status,
  `rho_fuze`, max failure probability, and effect band heatmaps.
  `tools/diagnostics/kill_chain_expectation_stage_attribution.py` has split the
  current `78` rows into `4` `guidance_approach` review cells, `6`
  `component_response` review cells, `13` `no_review_pressure` cells, `21`
  `marginal_observation` cells, and `34` `negative_control_satisfied` cells.
  `tools/diagnostics/kill_chain_expectation_response_diagnosis.py` classifies all
  six `component_response` cells as
  `outer_effect_low_component_load_probability_cliff`: the case-level
  `outer_effective` band maps to weak component load scale and very low
  response probability.
  The before report now preserves
  `a2.kill_chain_expectation_component_detail.v1` through the shared
  projection, and all six `component_response` cells have
  `detail_projection_signal=all_component_rows_weak_load_low_response`.
  The `8 km / 30 deg` case currently enters `R_fuze`, and its weak lethality
  routes through the `component_response` explanation chain; follow-on work is
  no longer detail retention or a new attribution layer, but factor
  decomposition across spatial projection, receiver exposure / armor /
  threshold, and response curve. The
  `15`
  mild-maneuver cases in the complete `93`
  anchor-grid, the `572` recommended-main-grid, worker parallelism, and
  maneuvering-target runtime support remain incomplete.
- Runtime calibration, descriptor edits, after reports, and full batch execution
  remain held.

## Archive

Historical records move to [archive/README.md](archive/README.md) only after this
subproject has a replacement current-status or closeout surface.
