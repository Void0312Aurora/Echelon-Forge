# Kill-Chain Expectation Standardization

Status: `2026-07-06` accepted / retained expectation-standardization track plus
post-P5 KCES harness diagnostics, component-response quantization, a
standards-layer v0 expectation envelope, and a read-only envelope audit over
the existing constant-velocity before report. This subproject defines
idealized kill-chain expectation contracts before runtime parameter retuning.
It does not claim real AIM-120C, F-16C, deterministic fuze, or Pk authority.

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
  [../../../../systems/standards/gradient_realism_principles.md](../../../../systems/standards/gradient_realism_principles.md)
- Public source admission rule:
  [../../../../research/standards/public_data_source_admission.md](../../../../research/standards/public_data_source_admission.md)
- Standards maintenance policy:
  [../../../../engineering/documentation/standards/standards_maintenance_policy.md](../../../../engineering/documentation/standards/standards_maintenance_policy.md)
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
| Expectation standardization | accepted / retained with standards planning supplement | This subproject, the P1-P5 closeout, post-P5 KCES harness diagnostics, and the standards-layer expectation envelope | Docs plus read-only diagnostics; no runtime parameter changes, no calibration authority, and no real-world authority. |

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
| `P5 Standard Promotion Decision` | Decide whether stable pieces move into `docs/standards`. | P1-P4 reviewed. | The original task-local workstream is retained; the later v0 expectation envelope is registered as an air-specialization planning supplement, not as a runtime contract. | pass |

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
- Component-response quantization threshold addendum:
  [kill_chain_component_response_quantization_20260705.md](kill_chain_component_response_quantization_20260705.md)
- Standardized expectation envelope:
  [Air-To-Air Kill-Chain Expectation Envelope](../../../../domains/air/work/issues/kill_chain_expectation_envelope.md)
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
- Constant-velocity anchor expectation-envelope audit:
  [kces_anchor_cv_expectation_envelope_summary_20260706.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_summary_20260706.md)
- P0-P5 themselves produce documentation and contract language only. The
  post-P5 initial harness implementation adds a read-only diagnostic wrapper,
  tests, heatmap visualization, first-review-stage attribution, and
  component-response report-level local diagnosis; the later envelope audit
  applies the standards-layer v0 expectation envelope to the existing before
  report as a read-only postprocessor. The before report now also preserves
  per-component `component_detail` load/response pairs through the shared
  `component_detail_projection.py` read-only projection from the existing
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
- P5 has recorded the standard-promotion decision: the original P1-P4
  workstream remains retained, while the later v0 expectation envelope is
  registered under `docs/domains/air` as a planning supplement and does not
  become a runtime contract.
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
- `P5` is closed as pass: this subproject remains accepted / retained; the
  later standards-layer envelope is an air-specialization planning supplement
  and future runtime-contract promotion still requires accepted
  runtime/test/admission evidence.
- Post-P5 initial harness implementation has started:
  `tools/diagnostics/kill_chain_expectation_harness.py` can generate the
  `anchor-grid` case grid and has generated the full constant-velocity `78`
  case before report. `tools/diagnostics/kill_chain_expectation_visualize.py`
  has rendered that before report into launch class, guidance status,
  `rho_fuze`, max failure probability, and effect band heatmaps.
  `tools/diagnostics/kill_chain_expectation_stage_attribution.py` has split the
  current `78` rows into `19` `no_review_pressure` cells, `25`
  `marginal_observation` cells, and `34`
  `negative_control_satisfied` cells. The runtime variant now reads the
  launch-time `missile_runtime_projection.resolved_projection_radius_m` value:
  `15 m * 0.60 = 9 m`. The `4/6/8 km +/-30 deg` rows are consequently
  `outside_effect`, and
  `tools/diagnostics/kill_chain_expectation_response_diagnosis.py` selects zero
  `component_response` candidates. The before report still preserves
  `a2.kill_chain_expectation_component_detail.v1` through the shared
  projection, but those details no longer create a current runtime-projection
  residual. On `2026-07-05`, the post-P5
  [component-response quantization addendum](kill_chain_component_response_quantization_20260705.md)
  added task-local diagnostic bands from `trace_response` through
  `severe_response` using `p_max`, `delta_abs`, and an independent
  `sampled_failure_observed` flag; it remains docs-only and grants no runtime
  calibration authority. On `2026-07-06`, the
  [standardized expectation envelope](../../../../domains/air/work/issues/kill_chain_expectation_envelope.md)
  registered the P1/P2/P3/addendum pieces as an air-specialization planning
  supplement covering
  human-defined inputs, derived report fields, response floors/ceilings,
  distribution tolerances, continuity rules, cell statuses, and owner-stage
  attribution. The read-only
  [expectation-envelope audit](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_summary_20260706.md)
  applied that envelope to the existing `78` constant-velocity rows after the
  audit priority correction and launch-window calibration: `25` cells are
  `boundary_observation`, and `53` cells are `satisfied`; no nominal guidance
  residual remains. Launch /
  guidance and marginal classifications are now evaluated before unrelated
  effect-metadata checks. It is a postprocessor result, not a simulation rerun,
  parameter edit, or real-world calibration verdict. The `4/6 km +/-45 deg`
  cells were reclassified from `N` to `M` after the measured `15 m` entry
  boundary remained near `36..38 deg` across `4..8 km`; forcing the earlier
  class required roughly `N=10..12` or `50 g`. The `18` runtime-projection
  `core/effective` rows all satisfy the response floor (`14` severe, `4`
  material), while the `10` outside-effect trace rows have no sampled failure.
  A separate `2026-07-15`
  [guidance mechanism ablation](../review_packets/kill_chain_guidance_mechanism_ablation_20260715/kill_chain_guidance_mechanism_ablation_conclusions_20260715.md)
  then ran `200` deterministic simulations across `20` mirrored CV cases and
  `10` mechanism variants. It shows that lead is the dominant necessary
  mechanism, PN is also necessary, and direct APN changes the `4/6/8 km x
  30/45 deg` core cells by only `0.01..1.53 m`. Removing track filtering
  improves `45 deg` misses but incorrectly moves the `16 km / 30 deg` O-class
  negative control inside `R_fuze`; a near-instant scalar autopilot is only a
  secondary improvement. Therefore “no nominal guidance residual” remains a
  classification result, not mechanism closure. A follow-on
  [exact mechanism ablation](../review_packets/kill_chain_guidance_exact_mechanism_ablation_20260715/kill_chain_guidance_exact_mechanism_ablation_conclusions_20260715.md)
  completed `320` exact-switch runs and vector-closure checks. World
  LOS-history PN improves the core `45 deg` cells by about `5.6..7.4 m`, but
  also moves `16 km / 30 deg` from `17.010 m` to `12.030 m`; truth-CV shows
  that the track velocity chain contributes about `3.1..4.4 m` of core
  residual. The current `45 deg -> M` boundary therefore describes the legacy
  runtime only: the N/M/O window also contains PN-frame, track-estimation, and
  capture-shaping effects, so the mechanism must be corrected before the
  window is recalibrated.
  The
  `15`
  mild-maneuver cases in the complete `93`
  anchor-grid, the `572` recommended-main-grid, worker parallelism, and
  maneuvering-target runtime support remain incomplete.
- P6 engineering-proxy guarded single-layer dry-run plans are admitted, while
  runtime parameter retuning, descriptor edits, after reports, and full batch
  execution remain held.

## Archive

Historical records move to [archive/README.md](archive/README.md) only after this
subproject has a replacement current-status or closeout surface.
