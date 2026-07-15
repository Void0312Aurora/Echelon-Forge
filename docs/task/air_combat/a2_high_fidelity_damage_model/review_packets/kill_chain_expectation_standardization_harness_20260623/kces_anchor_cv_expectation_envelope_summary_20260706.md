# KCES Expectation Envelope Audit

This report applies the standards-layer air-to-air kill-chain expectation
envelope to existing KCES before-report rows. It is a read-only review
artifact; it does not rerun simulation, edit parameters, or grant
calibration authority.

Boundary: standards planning supplement / engineering-proxy diagnostics only.

## Source

- Input: `docs/task/air_combat/a2_high_fidelity_damage_model/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json`
- Variant: `REV-RUNTIME-PROJECTION`
- Target motion layer: `nonmaneuvering_constant_velocity`
- Selected rows: `78`
- Envelope status counts: `{'boundary_observation': 21, 'guidance_or_model_residual': 4, 'satisfied': 53}`
- Owner-stage counts: `{'launch_window': 21, 'launch_window -> guidance_approach': 4, 'negative_control_satisfied': 34, 'no_review_pressure': 19}`

## Artifacts

- Manifest JSON: `kces_anchor_cv_expectation_envelope_manifest_20260706.json`
- Detail CSV: `kces_anchor_cv_expectation_envelope_detail_20260706.csv`
- Status matrix CSV: `kces_anchor_cv_expectation_envelope_matrix_20260706.csv`

## Review Rows

- `kces_anchor_grid_cv_4km_m45deg`: status=`guidance_or_model_residual`, owner=`launch_window -> guidance_approach`, launch=`N`, effect=`outside_effect`, response=`no_component_response`, p_max=`None`, delta_abs=`0.0`
- `kces_anchor_grid_cv_4km_p45deg`: status=`guidance_or_model_residual`, owner=`launch_window -> guidance_approach`, launch=`N`, effect=`outside_effect`, response=`no_component_response`, p_max=`None`, delta_abs=`0.0`
- `kces_anchor_grid_cv_6km_m45deg`: status=`guidance_or_model_residual`, owner=`launch_window -> guidance_approach`, launch=`N`, effect=`outside_effect`, response=`no_component_response`, p_max=`None`, delta_abs=`0.0`
- `kces_anchor_grid_cv_6km_p45deg`: status=`guidance_or_model_residual`, owner=`launch_window -> guidance_approach`, launch=`N`, effect=`outside_effect`, response=`no_component_response`, p_max=`None`, delta_abs=`0.0`

## Interpretation

- `guidance_or_model_residual` belongs to launch-window / guidance review.
- `below_outer_effective_floor` means the cell entered the effect envelope
  but only produced `trace_response`; it belongs to load / response factor
  decomposition rather than direct guidance or fuze retuning.
- `negative_control_pressure` means an outside or edge cell responded too
  strongly for the envelope.
