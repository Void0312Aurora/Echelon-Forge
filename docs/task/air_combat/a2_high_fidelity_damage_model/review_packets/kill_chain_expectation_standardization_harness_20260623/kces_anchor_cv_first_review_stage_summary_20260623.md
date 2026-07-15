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
- Stage counts: `{'marginal_observation': 25, 'negative_control_satisfied': 34, 'no_review_pressure': 19}`
- Priority counts: `{'low': 25, 'none': 53}`

## Artifacts

- Manifest JSON: `kces_anchor_cv_first_review_stage_manifest_20260623.json`
- Stage matrix CSV: `kces_anchor_cv_first_review_stage_matrix_20260623.csv`
- Detail CSV: `kces_anchor_cv_first_review_stage_detail_20260623.csv`
- Stage heatmap PNG: `kces_anchor_cv_first_review_stage_heatmap_20260623.png`
- Stage heatmap SVG: `kces_anchor_cv_first_review_stage_heatmap_20260623.svg`

## Review Focus

- No guidance / launch-window residual cells were selected.
- No component-response review cells were selected.

## Interpretation

- `guidance_approach` means a nominal cell did not enter the declared
  `R_fuze`; it should be reviewed before applying warhead or response
  pressure.
- `component_response` means guidance, fuze, and case-level load facts are
  present, but the response stage did not observe sampled component failure.
- `marginal_observation` and `negative_control_satisfied` are not failures;
  they preserve the heatmap topology for later comparison.
