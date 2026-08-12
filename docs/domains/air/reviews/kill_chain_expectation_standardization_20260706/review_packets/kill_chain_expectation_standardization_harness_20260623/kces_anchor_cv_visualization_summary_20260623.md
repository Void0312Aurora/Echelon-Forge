# KCES Anchor CV Visualization Summary

This artifact renders the existing before-report JSON as reviewable heatmap
matrices. It does not rerun simulation, retune runtime parameters, or claim
real weapon / target / Pk authority.

Boundary: engineering-proxy diagnostics only.

## Source

- Input: `docs/domains/air/reviews/kill_chain_expectation_standardization_20260706/review_packets/kill_chain_expectation_standardization_harness_20260623/kces_anchor_cv_before_report_20260623.json`
- Variant: `REV-RUNTIME-PROJECTION`
- Target motion layer: `nonmaneuvering_constant_velocity`
- Selected rows: `78`
- Launch classes: `{'M': 25, 'N': 19, 'O': 34}`
- Guidance statuses: `{'negative_control_satisfied': 34, 'observed_marginal': 25, 'satisfied': 19}`

## Artifacts

| Metric | CSV | PNG | SVG |
| --- | --- | --- | --- |
| `effect_band` | `kces_anchor_cv_effect_band_heatmap_20260623.csv` | `kces_anchor_cv_effect_band_heatmap_20260623.png` | `kces_anchor_cv_effect_band_heatmap_20260623.svg` |
| `guidance_status` | `kces_anchor_cv_guidance_status_heatmap_20260623.csv` | `kces_anchor_cv_guidance_status_heatmap_20260623.png` | `kces_anchor_cv_guidance_status_heatmap_20260623.svg` |
| `launch_class` | `kces_anchor_cv_launch_class_heatmap_20260623.csv` | `kces_anchor_cv_launch_class_heatmap_20260623.png` | `kces_anchor_cv_launch_class_heatmap_20260623.svg` |
| `max_failure_probability` | `kces_anchor_cv_max_failure_probability_heatmap_20260623.csv` | `kces_anchor_cv_max_failure_probability_heatmap_20260623.png` | `kces_anchor_cv_max_failure_probability_heatmap_20260623.svg` |
| `rho_fuze` | `kces_anchor_cv_rho_fuze_heatmap_20260623.csv` | `kces_anchor_cv_rho_fuze_heatmap_20260623.png` | `kces_anchor_cv_rho_fuze_heatmap_20260623.svg` |

## Review Notes

- No nominal guidance residual cells were selected.
- `8 km / +/-30 deg` selected rows:
  - `kces_anchor_grid_cv_8km_m30deg`: nearest_distance_m=`10.963446301013404`, rho_fuze=`0.7308964200675603`, effect_band=`outside_effect`, max_failure_probability=`0.006350331908151525`
  - `kces_anchor_grid_cv_8km_p30deg`: nearest_distance_m=`10.963479375176643`, rho_fuze=`0.7308986250117762`, effect_band=`outside_effect`, max_failure_probability=`0.0063555841366786684`
