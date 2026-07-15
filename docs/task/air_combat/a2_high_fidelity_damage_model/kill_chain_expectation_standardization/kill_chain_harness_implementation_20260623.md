# Kill-Chain Expectation Harness Initial Implementation

Status: `2026-07-15` initial executable before-report harness plus read-only
diagnostic postprocessors for the future harness implementation entry under
[Kill-Chain Expectation Standardization](README.md).

Chinese companion:
[kill_chain_harness_implementation_20260623.zh.md](kill_chain_harness_implementation_20260623.zh.md)

## Implementation Entry

Tool:

```bash
python tools/diagnostics/kill_chain_expectation_harness.py --help
```

New test:

```bash
python -m pytest tests/tools/test_kill_chain_expectation_harness.py -q
python -m pytest tests/tools/test_kces_expectation_envelope_audit.py -q
```

Current schemas:

| Artifact | Schema |
| --- | --- |
| before report | `a2.kill_chain_expectation_before_report.v1` |
| case grid rows | `a2.kill_chain_expectation_case_grid.v1` |
| heatmap rows | `a2.kill_chain_expectation_heatmap_row.v1` |
| component detail | `a2.kill_chain_expectation_component_detail.v1` |
| visualization manifest | `a2.kill_chain_expectation_visualization_manifest.v1` |
| first-review-stage attribution | `a2.kill_chain_expectation_stage_attribution.v1` |
| response local diagnosis | `a2.kill_chain_expectation_response_diagnosis.v2` |
| expectation-envelope audit | `a2.kill_chain_expectation_envelope_audit.v1` |

## Implemented

- Generates the P2 `anchor-grid` case grid.
- Executes the `nonmaneuvering_constant_velocity` runtime slice, currently `78`
  signed anchor cases.
- Registers the `mild_maneuver` sparse grid as `15` signed case-grid rows, but
  marks them unsupported at runtime instead of pretending they ran.
- Calls the existing
  [kill_chain_decoupling_probe.py](../../../../../tools/diagnostics/kill_chain_decoupling_probe.py)
  for read-only runtime facts.
- Projects each runtime case into P3/P4 heatmap report field groups:
  `identity`, `launch_window`, `guidance_approach`, `fuze_decision`,
  `warhead_load_field`, `component_response`, `consequence_projection`, and
  `guards`.
- Preserves `component_detail` under each heatmap row through the shared
  `component_detail_projection.py` read-only projection from the existing
  runtime facade. The KCES harness no longer maintains its own component
  pairing, lethality attribution, or response rules.
- Expands `R_effect_variant` as an offline evaluation dimension, without
  multiplying simulation cases.
- Expands `REV-RUNTIME-PROJECTION`, `REV-EQ-FUZE`, and `REV-SMALLER-LOAD` by
  default. Without `--declared-effect-radius-m`, `REV-SMALLER-LOAD` emits
  `unclassified_missing_R_effect` instead of inventing a meter value.
- Keeps CLI stdout as JSON while native runtime logs go to stderr.
- Applies the standards-layer v0 expectation envelope through
  `tools.diagnostics.kces.envelope_audit` as a read-only postprocessor over an
  existing before report. This does not yet make the base harness emit envelope
  fields inline.

## Smoke Result

Command:

```bash
python tools/diagnostics/kill_chain_expectation_harness.py \
  --case-id kces_anchor_grid_cv_8km_p30deg \
  --effect-variants REV-RUNTIME-PROJECTION,REV-EQ-FUZE,REV-SMALLER-LOAD
```

Key result:

| Field | Value |
| --- | --- |
| `case_count` | `1` |
| `heatmap_row_count` | `3` |
| `launch_class` | `N` |
| `nearest_distance_m` | `10.963479375176643` |
| `R_fuze_m` | `15.0` |
| `rho_fuze` | `0.7308986250117762` |
| `entered_R_fuze` | `true` |
| `guidance_expectation_status` | `satisfied` |
| `REV-RUNTIME-PROJECTION.R_effect_m` | `9.0` |
| `REV-RUNTIME-PROJECTION.R_effect_source` | `missile_runtime_projection.resolved_projection_radius_m` |
| `REV-RUNTIME-PROJECTION.rho_effect_case` | `1.218164375019627` |
| `REV-RUNTIME-PROJECTION.effect_band` | `outside_effect` |
| `REV-EQ-FUZE.effect_band` | `outer_effective` |
| `REV-SMALLER-LOAD.effect_band` | `unclassified_missing_R_effect` |
| `max_failure_probability` | `0.0063555841366786684` |
| `component_response_band` | `observed_probability_only` |
| `authority_boundary_status` | `engineering_proxy_guarded` |

Interpretation:

- This smoke case enters `R_fuze`; it is not a total no-approach / no-fuze-fact
  failure.
- `REV-RUNTIME-PROJECTION` uses the launch-time runtime spatial projection
  radius: `15 m * 0.60 = 9 m`. The case is therefore `outside_effect`, while
  `REV-EQ-FUZE` remains an independent 15 m sensitivity row in
  `outer_effective`.
- The low-probability component response is permitted for the current
  `outside_effect` negative-control classification; it is not current
  component-response calibration pressure.

## Constant-Velocity Anchor Before Report

The full `nonmaneuvering_constant_velocity` anchor-grid before report has been
generated:

```text
docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json
```

Summary:

| Field | Value |
| --- | --- |
| `case_count` | `78` |
| `heatmap_row_count` | `234` |
| `launch_class_counts` | `N=23`, `M=21`, `O=34` |
| runtime-row `N` satisfied | `19` |
| runtime-row `N` guidance residual | `4` |
| runtime-row `M` observed marginal | `21` |
| runtime-row `O` negative-control satisfied | `34` |
| authority boundary | `engineering_proxy_guarded` for all rows |

`N` residual cases:

| case_id | range_km | signed_bearing_deg | nearest_distance_m | rho_fuze |
| --- | ---: | ---: | ---: | ---: |
| `kces_anchor_grid_cv_4km_m45deg` | `4` | `-45` | `22.438232265927198` | `1.4958821510618132` |
| `kces_anchor_grid_cv_4km_p45deg` | `4` | `45` | `22.4382609956996` | `1.4958840663799733` |
| `kces_anchor_grid_cv_6km_m45deg` | `6` | `-45` | `22.10101051253856` | `1.473400700835904` |
| `kces_anchor_grid_cv_6km_p45deg` | `6` | `45` | `22.101032317828015` | `1.4734021545218676` |

`8 km / 30 deg` anchor:

| case_id | nearest_distance_m | rho_fuze | `REV-RUNTIME-PROJECTION.effect_band` | max_failure_probability |
| --- | ---: | ---: | --- | ---: |
| `kces_anchor_grid_cv_8km_m30deg` | `10.963446301013404` | `0.7308964200675603` | `outside_effect` | `0.006350331908151525` |
| `kces_anchor_grid_cv_8km_p30deg` | `10.963479375176643` | `0.7308986250117762` | `outside_effect` | `0.0063555841366786684` |

Interpretation:

- The current constant-velocity anchor-grid `O` negative controls do not create
  unexpected downstream calibration pressure.
- The main guidance / launch-window mismatch is not at `8 km / 30 deg`; it is
  at the four `N` cells `4 km / +/-45 deg` and `6 km / +/-45 deg`.
- The `8 km / 30 deg` case enters `R_fuze`, but its nearest distance exceeds the
  corrected 9 m runtime projection radius. Its trace response therefore stays a
  satisfied outside-effect observation rather than a load / response residual.

## Constant-Velocity Anchor Visualization

The before report has been rendered into reviewable heatmap matrices. This step
only reads the JSON report; it does not rerun simulation, retune parameters, or
claim real weapon / target / Pk authority.

Generation command:

```bash
python tools/diagnostics/kill_chain_expectation_visualize.py \
  --input docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json \
  --output-dir docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623 \
  --prefix kces_anchor_cv \
  --variant REV-RUNTIME-PROJECTION \
  --target-motion-layer nonmaneuvering_constant_velocity \
  --date-stamp 20260623
```

Artifact entry points:

| Artifact | Path |
| --- | --- |
| manifest | [kces_anchor_cv_visualization_manifest_20260623.json](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_visualization_manifest_20260623.json) |
| summary | [kces_anchor_cv_visualization_summary_20260623.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_visualization_summary_20260623.md) |
| launch class heatmap | [kces_anchor_cv_launch_class_heatmap_20260623.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_launch_class_heatmap_20260623.png) / [csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_launch_class_heatmap_20260623.csv) |
| guidance status heatmap | [kces_anchor_cv_guidance_status_heatmap_20260623.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_guidance_status_heatmap_20260623.png) / [csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_guidance_status_heatmap_20260623.csv) |
| `rho_fuze` heatmap | [kces_anchor_cv_rho_fuze_heatmap_20260623.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_rho_fuze_heatmap_20260623.png) / [csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_rho_fuze_heatmap_20260623.csv) |
| max failure probability heatmap | [kces_anchor_cv_max_failure_probability_heatmap_20260623.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_max_failure_probability_heatmap_20260623.png) / [csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_max_failure_probability_heatmap_20260623.csv) |
| effect band heatmap | [kces_anchor_cv_effect_band_heatmap_20260623.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_effect_band_heatmap_20260623.png) / [csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_effect_band_heatmap_20260623.csv) |

The figures show:

- `8 km / +/-30 deg` is `sat` on the guidance-status heatmap, so it is not the
  current main guidance residual.
- `8 km / +/-30 deg` is a low-response point on the max-failure-probability
  heatmap, around `0.006`, but it is also outside the corrected 9 m runtime
  projection radius. It therefore remains a satisfied negative-control
  observation under `REV-RUNTIME-PROJECTION`.
- The four `N` residual cells are concentrated at `4/6 km` and `+/-45 deg`,
  which points to either P2 launch-window class review or current guidance
  model review.

## First-Review-Stage Attribution

The same before report has also been converted into a first-review-stage triage
artifact. This answers which layer each heatmap cell should review first; it is
not a calibration verdict and does not use real weapon / target authority.

Generation command:

```bash
python tools/diagnostics/kill_chain_expectation_stage_attribution.py \
  --input docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json \
  --output-dir docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623 \
  --prefix kces_anchor_cv \
  --variant REV-RUNTIME-PROJECTION \
  --target-motion-layer nonmaneuvering_constant_velocity \
  --date-stamp 20260623
```

Artifact entry points:

| Artifact | Path |
| --- | --- |
| summary | [kces_anchor_cv_first_review_stage_summary_20260623.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_summary_20260623.md) |
| manifest | [kces_anchor_cv_first_review_stage_manifest_20260623.json](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_manifest_20260623.json) |
| stage heatmap | [kces_anchor_cv_first_review_stage_heatmap_20260623.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_heatmap_20260623.png) / [csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_matrix_20260623.csv) |
| detail CSV | [kces_anchor_cv_first_review_stage_detail_20260623.csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_first_review_stage_detail_20260623.csv) |

Current attribution counts:

| First review stage | Count | Meaning |
| --- | ---: | --- |
| `guidance_approach` | `4` | `N` cells did not enter `R_fuze`; review launch-window class / guidance first. |
| `no_review_pressure` | `19` | `N` cells either reached an in-envelope response floor or remained trace-only outside the 9 m runtime projection radius. |
| `marginal_observation` | `21` | `M` cells are preserved as observations, not failures. |
| `negative_control_satisfied` | `34` | `O` cells stayed quiet. |

This clarifies the follow-on split:

- `4/6 km +/-45 deg` is a high-priority `guidance_approach` review.
- `4/6/8 km +/-30 deg` is outside the corrected 9 m runtime projection radius;
  its trace response creates no review pressure under `REV-RUNTIME-PROJECTION`.
- There is no `negative_control_alert`; the current outside-envelope cells do
  not create unexpected calibration pressure.

## Component-Response Local Diagnosis

The report-level local diagnosis is retained as a postprocessor. After the
runtime projection correction it selects no `component_response` candidates for
`REV-RUNTIME-PROJECTION`. This still only reads the before report; it does not
rerun simulation, edit parameters, or claim real weapon / target / Pk authority.

Generation command:

```bash
python tools/diagnostics/kill_chain_expectation_response_diagnosis.py \
  --input docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json \
  --output-dir docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623 \
  --prefix kces_anchor_cv \
  --variant REV-RUNTIME-PROJECTION \
  --target-motion-layer nonmaneuvering_constant_velocity \
  --date-stamp 20260628
```

Artifact entry points:

| Artifact | Path |
| --- | --- |
| summary | [kces_anchor_cv_response_diagnosis_summary_20260628.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_summary_20260628.md) |
| manifest | [kces_anchor_cv_response_diagnosis_manifest_20260628.json](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_manifest_20260628.json) |
| detail CSV | [kces_anchor_cv_response_diagnosis_detail_20260628.csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_detail_20260628.csv) |
| matrix CSV | [kces_anchor_cv_response_diagnosis_matrix_20260628.csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_matrix_20260628.csv) |
| probability scatter | [kces_anchor_cv_response_diagnosis_probability_scatter_20260628.png](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_probability_scatter_20260628.png) / [svg](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_response_diagnosis_probability_scatter_20260628.svg) |

Current diagnosis:

| Field | Value |
| --- | ---: |
| candidate rows | `0` |
| baseline rows | `13` |
| diagnosis buckets | `{}` |

Interpretation:

- No current row is attributed to `component_response` under
  `REV-RUNTIME-PROJECTION`, so this artifact asserts no local load / response
  residual.
- The same rows may still be inspected through `REV-EQ-FUZE` as an explicit
  radius-policy sensitivity, but that result must not be presented as the
  current runtime projection.

## Expectation-Envelope Audit

The same before report has also been evaluated against the standards-layer v0
expectation envelope. This is still a read-only postprocessor; it does not
rerun simulation, edit parameters, or grant calibration authority.

Generation command:

```bash
python -m tools.diagnostics.kces.envelope_audit \
  --input docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json \
  --output-dir docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623 \
  --prefix kces_anchor_cv \
  --variant REV-RUNTIME-PROJECTION \
  --target-motion-layer nonmaneuvering_constant_velocity \
  --date-stamp 20260706
```

Artifact entry points:

| Artifact | Path |
| --- | --- |
| summary | [kces_anchor_cv_expectation_envelope_summary_20260706.md](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_summary_20260706.md) |
| manifest | [kces_anchor_cv_expectation_envelope_manifest_20260706.json](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_manifest_20260706.json) |
| detail CSV | [kces_anchor_cv_expectation_envelope_detail_20260706.csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_detail_20260706.csv) |
| matrix CSV | [kces_anchor_cv_expectation_envelope_matrix_20260706.csv](../review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_expectation_envelope_matrix_20260706.csv) |

Current envelope status counts:

| Envelope cell status | Count | Reading |
| --- | ---: | --- |
| `guidance_or_model_residual` | `4` | Nominal `4/6 km +/-45 deg` cells miss `R_fuze`; review launch-window / guidance first. |
| `boundary_observation` | `21` | All marginal launch-window cells remain observations. |
| `satisfied` | `53` | Remaining nominal and negative-control cells create no envelope pressure. |

Owner-stage counts:

| Owner stage | Count |
| --- | ---: |
| `launch_window` | `21` |
| `launch_window -> guidance_approach` | `4` |
| `negative_control_satisfied` | `34` |
| `no_review_pressure` | `19` |

## Boundary

This slice does not perform:

- runtime parameter edits;
- descriptor edits;
- after reports;
- delta-guard comparison;
- full `93` anchor-grid or `572` recommended-main-grid execution;
- the `15` `mild_maneuver` anchor cases are not executed yet, so the complete
  `93` anchor-grid remains incomplete;
- parallel worker scheduling;
- maneuvering target runtime support;
- runtime-contract standards promotion;
- real AIM-120C / F-16C / deterministic-fuze / Pk authority.

## Follow-Up

Recommended next steps:

1. Review P2 launch-window class and the current guidance model for the four
   `guidance_approach` cells.
2. Keep `REV-EQ-FUZE` as an offline radius sensitivity and preserve the
   launch-time runtime projection snapshot as the sole source for
   `REV-RUNTIME-PROJECTION`.
3. Implement worker parallelism and failed-case retry.
4. Add `mild_maneuver` runtime support so the full `93` anchor-grid no longer
   contains unsupported rows.
5. Move to the `recommended-main-grid` pilot after the anchor-grid
   interpretation is stable.
