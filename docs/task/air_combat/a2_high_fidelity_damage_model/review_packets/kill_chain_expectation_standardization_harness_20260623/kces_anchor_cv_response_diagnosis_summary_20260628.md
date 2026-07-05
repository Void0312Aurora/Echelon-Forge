# KCES Component-Response Local Diagnosis

This report consumes existing before-report rows and inspects the cells
already attributed to `component_response`. It is a report-level local
diagnostic; it does not rerun simulation, edit parameters, or claim real
weapon / target / Pk authority.

Boundary: engineering-proxy diagnostics only.

## Source

- Input: `docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json`
- Variant: `REV-RUNTIME-PROJECTION`
- Target motion layer: `nonmaneuvering_constant_velocity`
- Candidate rows: `6`
- Baseline rows: `13`
- Diagnosis buckets: `{'outer_effect_low_component_load_probability_cliff': 6}`
- Detail projection signals: `{'all_component_rows_weak_load_low_response': 6}`

## Artifacts

- Manifest JSON: `kces_anchor_cv_response_diagnosis_manifest_20260628.json`
- Detail CSV: `kces_anchor_cv_response_diagnosis_detail_20260628.csv`
- Matrix CSV: `kces_anchor_cv_response_diagnosis_matrix_20260628.csv`
- Probability scatter PNG: `kces_anchor_cv_response_diagnosis_probability_scatter_20260628.png`
- Probability scatter SVG: `kces_anchor_cv_response_diagnosis_probability_scatter_20260628.svg`

## Candidate Rows

- `kces_anchor_grid_cv_4km_m30deg`: range_km=`4.0`, signed_bearing_deg=`-30.0`, rho_effect_case=`0.6307325565022268`, strongest_component_effect_scale=`0.16074519706261`, max_failure_probability=`0.008649500378608573`, detail_projection_signal=`all_component_rows_weak_load_low_response`, detail_top_component=`left_aileron_actuator`, baseline=`kces_anchor_grid_cv_4km_m15deg`, probability_ratio=`0.009764763898016605`
- `kces_anchor_grid_cv_4km_p30deg`: range_km=`4.0`, signed_bearing_deg=`30.0`, rho_effect_case=`0.6307359108463404`, strongest_component_effect_scale=`0.1613400679808985`, max_failure_probability=`0.008657485926310137`, detail_projection_signal=`all_component_rows_weak_load_low_response`, detail_top_component=`right_aileron_actuator`, baseline=`kces_anchor_grid_cv_4km_p15deg`, probability_ratio=`0.009775163620473206`
- `kces_anchor_grid_cv_6km_m30deg`: range_km=`6.0`, signed_bearing_deg=`-30.0`, rho_effect_case=`0.6844566899168928`, strongest_component_effect_scale=`0.13142752983439088`, max_failure_probability=`0.00731975324788651`, detail_projection_signal=`all_component_rows_weak_load_low_response`, detail_top_component=`left_aileron_actuator`, baseline=`kces_anchor_grid_cv_6km_m15deg`, probability_ratio=`0.008263540391359833`
- `kces_anchor_grid_cv_6km_p30deg`: range_km=`6.0`, signed_bearing_deg=`30.0`, rho_effect_case=`0.684459042391009`, strongest_component_effect_scale=`0.1318421682169499`, max_failure_probability=`0.007325613998941034`, detail_projection_signal=`all_component_rows_weak_load_low_response`, detail_top_component=`right_aileron_actuator`, baseline=`kces_anchor_grid_cv_6km_p15deg`, probability_ratio=`0.008271394180756763`
- `kces_anchor_grid_cv_8km_m30deg`: range_km=`8.0`, signed_bearing_deg=`-30.0`, rho_effect_case=`0.7308964200675603`, strongest_component_effect_scale=`0.11727138114478873`, max_failure_probability=`0.006350331908151525`, detail_projection_signal=`all_component_rows_weak_load_low_response`, detail_top_component=`left_aileron_actuator`, baseline=`kces_anchor_grid_cv_8km_m15deg`, probability_ratio=`0.007169110864687176`
- `kces_anchor_grid_cv_8km_p30deg`: range_km=`8.0`, signed_bearing_deg=`30.0`, rho_effect_case=`0.7308986250117762`, strongest_component_effect_scale=`0.11750353538707678`, max_failure_probability=`0.0063555841366786684`, detail_projection_signal=`all_component_rows_weak_load_low_response`, detail_top_component=`right_aileron_actuator`, baseline=`kces_anchor_grid_cv_8km_p15deg`, probability_ratio=`0.0071761661558646835`

## Interpretation

- All selected rows have guidance / fuze / case-level load facts, but no
  sampled component failure.
- The current six cells fall into a report-level probability cliff: the
  case-level `outer_effective` band maps to weak component load scale and
  very low max failure probability.
- When per-component details are present, `detail_projection_signal`
  separates a weak component-load projection from a response-curve-only
  explanation.
