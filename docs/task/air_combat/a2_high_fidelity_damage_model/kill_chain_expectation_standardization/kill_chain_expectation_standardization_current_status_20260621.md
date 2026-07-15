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
The `2026-07-15` five-stage guidance mechanism/envelope/scalar sequence is now
complete: `nav_gain=4` is retained, while default promotion of the complete
candidate remains held for missing maneuver-target/APN evidence.

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
  splitting the current constant-velocity anchor rows into `19`
  `no_review_pressure` cells, `25`
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
  unrelated effect-metadata checks and the close-range `45 deg` cells were
  calibrated to `M`, the status counts are `25` `boundary_observation` and
  `53` `satisfied`; no nominal guidance residual remains. This is a
  postprocessor result, not a simulation rerun, parameter edit, or real-world
  calibration verdict.
- Calibrated the close-range launch-window oracle on `2026-07-15`: the runtime
  `4..16 km x 0..90 deg` diagnostic grid and `4..8 km x 35..45 deg`
  refinement place the `R_fuze=15 m` entry boundary near `36..38 deg` at close
  range. The `4/6 km x 45 deg` cells are now `M`; preserving the former `N`
  label required roughly `N=10..12` or `50 g`, so no runtime retune was taken.
- Added a `2026-07-15` guidance-mechanism ablation:
  [conclusions](../review_packets/kill_chain_guidance_mechanism_ablation_20260715/kill_chain_guidance_mechanism_ablation_conclusions_20260715.md).
  The `200` deterministic runs keep `N=4` and `35 g` frozen. Lead and PN are
  necessary; direct APN changes the `4/6/8 km x 30/45 deg` core cells by only
  `0.01..1.53 m`. Removing track filtering improves `45 deg` but breaches the
  `16 km / 30 deg` O-class negative control, while a near-instant scalar
  autopilot does not bring any `45 deg` cell inside `R_fuze`. The audit's zero
  nominal residual count is therefore classification closure, not guidance
  mechanism closure.
- Completed the same-day
  [exact mechanism ablation](../review_packets/kill_chain_guidance_exact_mechanism_ablation_20260715/kill_chain_guidance_exact_mechanism_ablation_conclusions_20260715.md):
  `20` mirrored cases and `16` discrete profiles produced `320` runs with
  `N=4`, `35 g`, and `APN=0.5` frozen and no epsilon gates. The all-enabled
  profile is casewise identical to baseline; disabled-component, vector-sum,
  total-clamp, and truth-CV invariants all pass. World LOS-history PN improves
  the `4/6/8 km / 45 deg` cells to `16.736/16.472/17.034 m`, but also moves
  `16 km / 30 deg` from `17.010 m` to `12.030 m`. Truth-CV moves the
  `6/8 km / 45 deg` cells inside `15 m` while pushing that O control to
  `9.503 m`. The current N/M/O window therefore incorporates legacy PN frame,
  track-estimation error, and capture window shaping; it is not purely a
  scalar-parameter result.
- Completed the subsequent five-stage mechanism-calibration sequence in order.
  Stages 1/2 made world LOS-history PN and the world-CV tracker
  production-selectable; stage 3 selected capture disabled. Stage 4 ran `1443`
  three-seed main-grid and `630` refined cases for the complete candidate,
  yielding `N/M/O=146/32/69`, maximum mirror drift `0.000114 m`, zero seed
  spread, zero capture, and a single connected hit region with no holes,
  angular reversals, or range islands. Stage 5 ran `13695` OFAT/half-step
  holdout cases over `nav_gain=3.5/3.75/4/4.25/4.5`. Lower gains reduced
  saturation P95 but moved the contour by `5 deg`; higher gains expanded the
  contour without reducing saturation. The result retains `N=4`. Scalar
  selection passes, while default promotion remains held because world-CV
  acceleration is fixed at zero and maneuver-target/APN authority is absent;
  the AIM-120 JSON was not changed.
- Rechecked the downstream runtime-projection response slice: all `18`
  `core/effective` rows satisfy their response floor (`14` severe, `4`
  material); the `10` outside-effect trace rows have no sampled failure and
  remain below `p_max=0.008658` and `delta_abs=0.006434`.

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
| Exact guidance mechanism ablation | pass | [kill_chain_guidance_exact_mechanism_ablation_conclusions_20260715.md](../review_packets/kill_chain_guidance_exact_mechanism_ablation_20260715/kill_chain_guidance_exact_mechanism_ablation_conclusions_20260715.md) | Exact controls, vector closure, world PN, track/truth-CV, and positive/negative controls are complete; this is diagnostic closure, not production mechanism admission. |
| Corrected-mechanism continuous envelope | pass | [stage-4 conclusions](../review_packets/kill_chain_guidance_envelope_rebuild_20260715/kill_chain_guidance_envelope_rebuild_20260715_conclusions.zh.md) | The three-seed CV engineering envelope passes; this is not maneuver-target, real-range, or Pk authority. |
| Constrained guidance-scalar calibration | pass / default promotion held | [stage-5 conclusions](../review_packets/kill_chain_guidance_scalar_calibration_20260715/kill_chain_guidance_scalar_calibration_20260715_conclusions.zh.md) | `nav_gain=4` retained; the complete candidate lacks maneuver/APN admission for default release. |

## Residual Register

| Residual | Owner | Exit condition |
| --- | --- | --- |
| Probability / integrity thresholds now have a task-local v0 addendum but are not emitted by the harness yet | Future harness implementation | If machine consumption is needed, emit `component_response_quantized_band`, `component_response_sampled_failure_observed`, and `component_response_expectation_status` according to the addendum. |
| Standardized expectation envelope is available through a read-only postprocessor but not emitted inline by the harness yet | Future harness implementation | If machine consumption is needed inside the harness report, emit `a2.kill_chain_expectation_envelope.v0` fields such as `envelope_cell_status` and `envelope_owner_stage` from the before/after report. |
| Recommended main sampling grid not yet executed | Future harness implementation | The initial harness has generated the constant-velocity anchor before report and reviewable heatmaps; future execution produces the recommended-main before heatmap report. |
| Runtime projection source must remain explicit | Future harness maintenance | Keep `REV-RUNTIME-PROJECTION` bound to `missile_runtime_projection.resolved_projection_radius_m` and keep `REV-EQ-FUZE` separate as a declared sensitivity variant. |
| Worker parallelism and retry not implemented | Future harness implementation | Worker pool, failed-case retry, and batch summary writer exist. |
| Maneuvering-target runtime harness not implemented | Future harness implementation | `mild_maneuver` grid rows are no longer marked unsupported and have runtime facts. |
| Complete-candidate default promotion remains held | Guidance runtime mechanism work | Establish nonzero acceleration-tracker authority and APN identifiability for maneuvering targets, then rerun the corrected envelope and scalar gates in config-backed no-override mode before atomically changing default selectors. |
| Standards promotion held | Future standards promotion | Reopen under the standards maintenance policy only after accepted runtime/test/admission evidence exists. |
| Real authority unavailable | Future admission work | A future authority gate admits specific fields; until then all claims remain engineering proxy. |

## Recommended Next Steps

1. Keep the closed P0-P5 standards workstream separate from the five-stage
   runtime-mechanism evidence; do not treat the standards-layer envelope as
   real-weapon or default-runtime authority.
2. Keep AIM-120 default selectors unchanged. The next work is not another `N`
   sweep: implement auditable nonzero acceleration estimation for maneuvering
   targets, or explicitly choose pure PN/APN=0 and rerun stages 4/5.
3. Only after the maneuver/APN gate passes, atomically write the complete
   candidate tuple and rerun the continuous envelope without overrides through
   the config-backed path. Do not combine world PN/capture-off with the legacy
   tracker as a partial release.

## Explicitly Refused Claims

- Real AIM-120C warhead, fuze, or fragment-pattern truth.
- Real F-16C vulnerability or component-failure truth.
- Deterministic fuze authority.
- Pk or stock weapon/target lethality authority.
- Runtime calibration authority from this docs-only seed.
