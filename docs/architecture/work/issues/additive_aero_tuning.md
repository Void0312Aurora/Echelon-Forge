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
is repinned for this owned field extension. The transfer contract advances to
generation 4 and admits generation 3 through explicit migration that writes
the five constructor defaults into the staged bytes. The native registry test
imports the historical 45-field shape, commits durably, reopens the file journal,
and requires `Committed` recovery across all twelve owners. Direct current
payloads omitting any new field and unknown fields are rejected without mutation.
Generation 2 has expired from the N/N-1 window. Exact-byte recovery checks and
the existing candidate boundary are preserved.

## Review remediation validation (2026-10-08)

| Host / check | Result |
|---|---|
| Windows, fresh MSVC native build (`ef_py`, `ef_test`, host candidate) | Passed |
| Windows, complete host candidate suite | 74 cases, 2,045 assertions; no failures or skips |
| Windows, historical AeroTuning registry/commit/journal-reopen regression | 1 case, 54 assertions passed |
| Windows, composition and production rollout architecture gates | 162 passed, 1 skipped (g++ unavailable) |
| HEI via HEI-FRP, isolated Release build, GCC 15.2.0 | Passed |
| HEI, complete host candidate suite | 74 cases, 2,045 assertions; no failures or skips |
| HEI, state-transfer architecture contract | 11 passed |

HEI used Python 3.13.5 and CMake 4.2.3, the repository's pinned dependency
sources, and `CMAKE_POLICY_VERSION_MINIMUM=3.5` for the existing dependency
CMake declarations. The four modified C++ runtime/header/test source hashes
matched the Windows files. These results cover candidate transfer and durable
recovery; they do not grant production rollout authority.
