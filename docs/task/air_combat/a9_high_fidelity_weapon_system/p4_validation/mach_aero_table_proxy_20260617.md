# A9 Mach Aero Table Proxy Validation - 2026-06-17

## Purpose

This note closes residual R4 by replacing the single transonic Cd0 interpolation
with optional Mach-indexed lookup tables for base drag and induced-drag factor.
The table values are engineering proxies for generic missile-body behavior, not
real-weapon calibration.

## Public Data Availability

Relevant public data exists, but it is not sufficient to claim stock-weapon
truth. The A9 source ledger records three G5 sources: MIL-HDBK-1211 for generic
missile flight simulation conventions and power-on/off base drag, NACA/NASA
fineness-ratio-10 zero-lift drag data for the Mach-dependent Cd0 shape, and
Fleeman for generic induced-drag-factor ranges.

The useful public shape is:

- subsonic Cd0 roughly `0.30-0.45`
- transonic Cd0 peak roughly `0.45-0.70`
- supersonic Cd0 roughly `0.28-0.40`
- induced-drag factor k for tail-controlled missiles roughly `0.6-1.2` in
  classical drag-polar notation, represented here by the existing model's
  normalized `induced_drag_k` scale rather than a direct CL coefficient.

## Proxy Table

The temporary table follows the public shape above:

| Mach | Cd0 proxy | induced_drag_k proxy |
|------|-----------|----------------------|
| 0.0 | 0.30 | 6.0 |
| 0.8 | 0.34 | 7.5 |
| 1.0 | 0.58 | 9.5 |
| 1.2 | 0.52 | 10.5 |
| 2.0 | 0.38 | 9.0 |
| 3.0 | 0.33 | 8.0 |
| 4.0 | 0.31 | 7.0 |

These are deliberately generic. They encode a transonic drag rise and a mild
supersonic decline while preserving the existing model's scalar fallback when no
table is configured.

## Implementation

- New tuning fields:
  - `cd0_mach_breakpoints`
  - `cd0_mach_values`
  - `induced_drag_k_mach_breakpoints`
  - `induced_drag_k_mach_values`
- Tables are exposed through Python bindings, JSON parsing, launch-time tuning
  overlay, runtime missile state, and `debug_get_missile_runtime_state`.
- Invalid tables (wrong size, non-finite values, non-positive values, or
  non-increasing Mach breakpoints) fall back to the existing scalar model.

## Validation

Commands:

- `cmake --build build --target ef_py -j2`
- `PYTHONPATH=build pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py -k 'mach_table or cd0_supersonic or induced_drag'`
- `PYTHONPATH=build pytest -q tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py`
- `PYTHONPATH=build python docs/task/air_combat/a9_high_fidelity_weapon_system/p3_integration/p3c_a9_tuning_example.py`

Outcomes:

- Mach-table focused selector: `4 passed`
- Full launch/guidance/dynamics collector: `40 passed`
- P3-C tuning example: `11/11 A9 fields round-trip PASS`

The table tests prove that configured Cd0(M) and k(M) arrays reach runtime
missile state and alter high-speed/turn-energy behavior. They do not prove a
real weapon drag polar.
