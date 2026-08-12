# Guidance mechanism ablation summary

- Runs: `200` across `20` cases and `10` mechanism variants.
- Full chain entered `R_fuze=15 m` in `6` cases and remained outside in `14` cases.
- Negative deltas below mean that adding the named mechanism reduced miss distance.

| Conditional effect | Mean delta (m) | 30 deg | 45 deg | 60 deg | Improved | Neutral | Worsened |
|---|---:|---:|---:|---:|---:|---:|---:|
| `apn_with_pn` | -18.162 | -0.327 | -2.351 | -85.453 | 10 | 10 | 0 |
| `apn_without_pn` | -31.329 | -0.585 | -14.977 | -125.520 | 16 | 4 | 0 |
| `lead_with_pn` | -100.418 | -54.255 | -109.588 | -174.404 | 20 | 0 | 0 |
| `lead_without_pn` | -146.714 | -116.812 | -164.029 | -171.886 | 20 | 0 | 0 |
| `near_instant_scalar_autopilot` | -12.553 | -0.613 | -2.187 | -57.168 | 20 | 0 | 0 |
| `pn_with_lead` | -253.564 | -17.073 | -163.919 | -905.834 | 20 | 0 | 0 |
| `pn_with_lead_apn` | -240.397 | -16.815 | -151.293 | -865.768 | 20 | 0 | 0 |
| `pn_without_lead_apn` | -299.859 | -79.630 | -218.360 | -903.316 | 20 | 0 | 0 |
| `remove_track_filter` | -22.137 | -2.826 | -6.678 | -91.677 | 20 | 0 | 0 |
| `second_order_autopilot` | 8.841 | 0.349 | 1.579 | 40.350 | 0 | 8 | 12 |
| `third_order_autopilot` | 23.693 | 1.607 | 5.846 | 103.562 | 0 | 0 | 20 |

## Structural controls

The 16 km / 30 deg row is an O-class negative control; values at or below 15 m breach it.

| Variant | 4 km / 45 deg | 6 km / 45 deg | 8 km / 45 deg | 16 km / 30 deg |
|---|---:|---:|---:|---:|
| `full` | 22.438 | 22.101 | 24.448 | 17.010 |
| `full_no_track_filter` | 19.120 | 18.206 | 19.400 | 12.703 |
| `full_fast_scalar_autopilot` | 20.078 | 21.520 | 23.735 | 16.148 |
| `full_autopilot_order2` | 25.279 | 22.843 | 25.024 | 17.331 |
| `full_autopilot_order3` | 35.878 | 24.537 | 25.767 | 18.690 |

## Interpretation limits

- epsilon gains are mechanism gates, not exact zero-valued C++ switches
- capture remains present in every variant and is not independently identified
- conditional deltas include nonlinear trajectory feedback, projection, saturation, and energy coupling
- constant-velocity cases diagnose the current engineering runtime and do not establish real-weapon authority
