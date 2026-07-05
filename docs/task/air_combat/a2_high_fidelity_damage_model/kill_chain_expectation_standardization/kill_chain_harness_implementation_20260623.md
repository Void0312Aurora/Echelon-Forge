# Kill-Chain Expectation Harness Initial Implementation

Status: `2026-06-23` initial executable before-report harness for the future
harness implementation entry under
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
| `REV-RUNTIME-PROJECTION.effect_band` | `outer_effective` |
| `REV-EQ-FUZE.effect_band` | `outer_effective` |
| `REV-SMALLER-LOAD.effect_band` | `unclassified_missing_R_effect` |
| `max_failure_probability` | `0.0063555841366786684` |
| `component_response_band` | `observed_probability_only` |
| `authority_boundary_status` | `engineering_proxy_guarded` |

Interpretation:

- This smoke case enters `R_fuze`; it is not a total no-approach / no-fuze-fact
  failure.
- Under `REV-RUNTIME-PROJECTION` and `REV-EQ-FUZE`, the case-level
  `rho_effect_case` lands in `outer_effective`; this is a report band, not a
  probability threshold or real-warhead claim.
- Component response remains a low-probability observation. That supports a
  future before-heatmap first-failed-stage analysis, but it is not a calibration
  conclusion.

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
| `kces_anchor_grid_cv_8km_m30deg` | `10.963446301013404` | `0.7308964200675603` | `outer_effective` | `0.006350331908151525` |
| `kces_anchor_grid_cv_8km_p30deg` | `10.963479375176643` | `0.7308986250117762` | `outer_effective` | `0.0063555841366786684` |

Interpretation:

- The current constant-velocity anchor-grid `O` negative controls do not create
  unexpected downstream calibration pressure.
- The main guidance / launch-window mismatch is not at `8 km / 30 deg`; it is
  at the four `N` cells `4 km / +/-45 deg` and `6 km / +/-45 deg`.
- The `8 km / 30 deg` case enters `R_fuze`, but response remains low; follow-on
  work should route it through the `warhead_load_field -> component_response`
  explanation chain instead of treating it as a no-approach fact.

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
  heatmap, around `0.006`; follow-on analysis should therefore route through
  `warhead_load_field -> component_response`.
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
| `component_response` | `6` | `N` cells have guidance / fuze / load facts but no sampled response failure. |
| `no_review_pressure` | `13` | `N` cells entered fuze, detonated, had load, and sampled response. |
| `marginal_observation` | `21` | `M` cells are preserved as observations, not failures. |
| `negative_control_satisfied` | `34` | `O` cells stayed quiet. |

This clarifies the follow-on split:

- `4/6 km +/-45 deg` is a high-priority `guidance_approach` review.
- `4/6/8 km +/-30 deg` is a medium-priority `component_response` review,
  including the originally raised `8 km / 30 deg` cell.
- There is no `negative_control_alert`; the current outside-envelope cells do
  not create unexpected calibration pressure.

## Component-Response Local Diagnosis

The six cells attributed to `component_response` now have a report-level local
diagnosis. This still only reads the before report; it does not rerun
simulation, edit parameters, or claim real weapon / target / Pk authority.

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

| Diagnosis bucket | Count | Reading |
| --- | ---: | --- |
| `outer_effect_low_component_load_probability_cliff` | `6` | Case-level `outer_effective` band maps to weak component load scale and very low response probability. |

Per-component projection signal:

| Detail projection signal | Count | Reading |
| --- | ---: | --- |
| `all_component_rows_weak_load_low_response` | `6` | All preserved per-component rows combine weak load scale with low response probability. |

Preserved detail for `8 km / +30 deg`:

| Detail | Value |
| --- | --- |
| component detail rows | `4` |
| strongest load component | `right_horizontal_tail_actuator_or_surface_component` / `flight_control` |
| strongest load `effect_scale` | `0.11750353538707678` |
| strongest load `rho_effect_component` | `0.40311860731986976` |
| max-probability component | `right_aileron_actuator` / `flight_control` |
| max component `failure_probability` | `0.0063555841366786684` |
| max component `effect_scale` | `0.06955096109949216` |
| sampled failure | `false` |

Against same-range, same-side `15 deg` sampled-response baselines:

- `4 km +/-30 deg` max failure probability is about `0.98%` of the `15 deg`
  baseline, and strongest component load scale is about `17.6%`.
- `6 km +/-30 deg` max failure probability is about `0.83%` of the `15 deg`
  baseline, and strongest component load scale is about `14.4%`.
- `8 km +/-30 deg` max failure probability is about `0.72%` of the `15 deg`
  baseline, and strongest component load scale is about `12.8%`.

Interpretation:

- All six cells have guidance / fuze / case-level load facts, so they should
  not be relabeled as guidance failures.
- The low response looks more like a probability cliff from case-level
  `outer_effective` into component-level load / response than simple random
  sampling miss.
- The before report now preserves per-component `component_loads[]` and
  `component_responses[]` details through the shared projection helper. The
  next slice should explain the low-response cause inside those existing
  fields: warhead spatial projection, target receiver exposure / armor /
  threshold, or response curve.

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
- standards promotion;
- real AIM-120C / F-16C / deterministic-fuze / Pk authority.

## Follow-Up

Recommended next steps:

1. Use the shared projection output for per-component `component_loads[]` and
   `component_responses[]` details to decompose the response-cliff cause:
   warhead spatial projection, receiver exposure / armor / threshold, or
   response curve.
2. Review P2 launch-window class and the current guidance model for the four
   `guidance_approach` cells.
3. Implement worker parallelism and failed-case retry.
4. Add `mild_maneuver` runtime support so the full `93` anchor-grid no longer
   contains unsupported rows.
5. Move to the `recommended-main-grid` pilot after the anchor-grid
   interpretation is stable.
