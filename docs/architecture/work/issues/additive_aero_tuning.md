# Additive aerodynamic effect tuning

Issue: #122

The air-domain `AeroTuning` component owns these provisional empirical effects.
They can be set in the existing per-platform `airframe.tuning` or top-level
`aero_tuning` content object. Missing fields retain the defaults below; setting a
coefficient to zero disables its additive effect. `enabled: false` selects the
global default preset, consistent with the existing tuning contract.

| Parameter | Default | Unit and applicability |
|---|---:|---|
| `flap_lift_coefficient_per_full_deflection` | 0.35 | Dimensionless lift increment at flaps=1, before the existing stall blend |
| `stores_drag_coefficient_per_drag_index` | 0.001 | Dimensionless drag increment per `MassProperties.current_drag_index` unit |
| `landing_gear_drag_coefficient_per_extension` | 0.04 | Dimensionless drag increment at gear extension=1 |
| `speedbrake_drag_coefficient_per_full_extension` | 0.08 | Dimensionless drag increment at speedbrake=1 |
| `flaps_drag_coefficient_per_full_deflection` | 0.02 | Dimensionless profile drag increment at flaps=1; induced drag remains in the polar |

These values preserve the original simplified C++ model. They are compatibility
defaults, not calibrated airframe measurements. The stores drag index is an
authored model index, not an SI area. Platform authors may override these fields
when they have calibration evidence; this migration performs no parameter fit.

Pilot flaps and speedbrake inputs only apply while `PilotAction.active` is true.
The existing input normalization, stall blend, ground effect, damage effects,
and induced drag polar remain in place. Content loading, state-transfer
reflection, and live coefficient tests cover the new fields.

The candidate ECS migration digest includes serialized component reflection and
is repinned for this owned field extension. A native state-transfer regression
checks current custom values, constructor defaults for older payloads omitting
the five fields, and rejection of unknown fields without mutating the target
(one case, 46 assertions). This preserves the existing candidate boundary.
