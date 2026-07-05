# KCES First-Review-Stage Attribution Summary

This report consumes existing before-report rows and attributes each selected
heatmap cell to the first stage that should be reviewed. It is a diagnostic
triage artifact, not a calibration verdict or real-world authority claim.

Boundary: engineering-proxy diagnostics only.

## Source

- Input: `docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json`
- Variant: `REV-RUNTIME-PROJECTION`
- Target motion layer: `nonmaneuvering_constant_velocity`
- Selected rows: `78`
- Stage counts: `{'component_response': 6, 'guidance_approach': 4, 'marginal_observation': 21, 'negative_control_satisfied': 34, 'no_review_pressure': 13}`
- Priority counts: `{'high': 4, 'low': 21, 'medium': 6, 'none': 47}`

## Artifacts

- Manifest JSON: `kces_anchor_cv_first_review_stage_manifest_20260623.json`
- Stage matrix CSV: `kces_anchor_cv_first_review_stage_matrix_20260623.csv`
- Detail CSV: `kces_anchor_cv_first_review_stage_detail_20260623.csv`
- Stage heatmap PNG: `kces_anchor_cv_first_review_stage_heatmap_20260623.png`
- Stage heatmap SVG: `kces_anchor_cv_first_review_stage_heatmap_20260623.svg`

## Review Focus

- Guidance / launch-window residual cells:
  - `kces_anchor_grid_cv_4km_m45deg`: range_km=`4.0`, signed_bearing_deg=`-45.0`, rho_fuze=`1.4958821510618132`
  - `kces_anchor_grid_cv_4km_p45deg`: range_km=`4.0`, signed_bearing_deg=`45.0`, rho_fuze=`1.4958840663799733`
  - `kces_anchor_grid_cv_6km_m45deg`: range_km=`6.0`, signed_bearing_deg=`-45.0`, rho_fuze=`1.473400700835904`
  - `kces_anchor_grid_cv_6km_p45deg`: range_km=`6.0`, signed_bearing_deg=`45.0`, rho_fuze=`1.4734021545218676`
- Component-response review cells after guidance/fuze/load facts:
  - `kces_anchor_grid_cv_4km_m30deg`: range_km=`4.0`, signed_bearing_deg=`-30.0`, effect_band=`outer_effective`, max_failure_probability=`0.008649500378608573`
  - `kces_anchor_grid_cv_4km_p30deg`: range_km=`4.0`, signed_bearing_deg=`30.0`, effect_band=`outer_effective`, max_failure_probability=`0.008657485926310137`
  - `kces_anchor_grid_cv_6km_m30deg`: range_km=`6.0`, signed_bearing_deg=`-30.0`, effect_band=`outer_effective`, max_failure_probability=`0.00731975324788651`
  - `kces_anchor_grid_cv_6km_p30deg`: range_km=`6.0`, signed_bearing_deg=`30.0`, effect_band=`outer_effective`, max_failure_probability=`0.007325613998941034`
  - `kces_anchor_grid_cv_8km_m30deg`: range_km=`8.0`, signed_bearing_deg=`-30.0`, effect_band=`outer_effective`, max_failure_probability=`0.006350331908151525`
  - `kces_anchor_grid_cv_8km_p30deg`: range_km=`8.0`, signed_bearing_deg=`30.0`, effect_band=`outer_effective`, max_failure_probability=`0.0063555841366786684`

## Interpretation

- `guidance_approach` means a nominal cell did not enter the declared
  `R_fuze`; it should be reviewed before applying warhead or response
  pressure.
- `component_response` means guidance, fuze, and case-level load facts are
  present, but the response stage did not observe sampled component failure.
- `marginal_observation` and `negative_control_satisfied` are not failures;
  they preserve the heatmap topology for later comparison.
