# Exact guidance mechanism ablation

- Runs: `320`.
- Scalars are frozen at `N=4`, `35 g`, and `APN gain=0.5`.
- Negative deltas mean the after-profile reduced miss distance.

| Matched effect | N30 | M45 | 60 stress | O near | O far |
|---|---:|---:|---:|---:|---:|
| `add_acceleration_lead_legacy` | -0.830 | -1.555 | -10.045 | -7.903 | -0.555 |
| `add_acceleration_lead_track_analytic` | -0.717 | -1.116 | -7.866 | -6.805 | -0.773 |
| `add_acceleration_lead_world_history` | -0.671 | -1.035 | -6.861 | -8.006 | -0.586 |
| `add_apn_to_current` | -0.259 | -0.622 | -68.883 | -54.780 | -0.532 |
| `lead_requires_capture_invariant` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `remove_capture_from_current` | -10.094 | 39.322 | 1607.274 | 1074.989 | -16.986 |
| `remove_lead_from_current` | 43.913 | 84.959 | 213.771 | 158.172 | 80.450 |
| `remove_pn_from_current` | 7.531 | 16.112 | 662.523 | 812.924 | 44.668 |
| `replace_legacy_pn_with_world_history_full` | -1.426 | -6.248 | -106.729 | -160.354 | -4.980 |
| `replace_legacy_pn_with_world_history_no_apn` | -1.497 | -6.794 | -135.537 | -153.955 | -5.291 |
| `replace_legacy_pn_with_world_history_velocity` | -1.656 | -7.314 | -138.721 | -153.852 | -5.260 |
| `replace_track_with_truth_cv_for_analytic_chain` | -3.121 | -3.835 | -221.091 | -257.446 | -4.380 |
| `replace_track_with_truth_cv_for_legacy_capture_lead` | -0.864 | -1.486 | -199.601 | -188.592 | -1.304 |
| `replace_world_history_with_track_analytic_pn` | 0.640 | 1.040 | 79.803 | 67.660 | 1.046 |
| `truth_cv_apn_invariant` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `truth_cv_quadratic_invariant` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Acceptance

- `baseline_profile_equivalent_within_1e_3_m`: `True`
- `component_vectors_close_within_1e_6_mps2`: `True`
- `disabled_components_zero_within_1e_12_g`: `True`
- `legacy_full_N30_all_enter_R_fuze`: `True`
- `legacy_full_O_controls_all_outside_R_fuze`: `True`
- `max_baseline_profile_delta_m`: `0.0`
- `max_component_sum_error_mps2`: `4.547473508864641e-12`
- `max_disabled_component_g`: `0.0`
- `max_invariant_abs_delta_m`: `0.0`
- `max_mirror_abs_difference_m`: `5.075043395397216e-05`
- `max_postclamp_g`: `35.00000000000001`
- `mirror_symmetric_within_1e_3_m`: `True`
- `postclamp_never_exceeds_35g`: `True`
- `truth_cv_and_capture_interaction_invariants_within_1e_6_m`: `True`

## Limits

- The truth-CV source is an oracle diagnostic and is not a production guidance input.
- Conditional deltas include nonlinear trajectory, saturation, and energy feedback.
- The constant-velocity matrix diagnoses implementation mechanisms, not real-weapon authority.
- M45 is a residual observation group; entering 15 m is not imposed as an acceptance gate.
