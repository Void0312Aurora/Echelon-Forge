# A9 Warhead Detonation Heatmap Validation - 2026-06-17

## Purpose

This validation sweep observes how the current proximity-detonation damage
chain responds to different target-local detonation points and generic warhead
families. It uses the existing debug entry point
`debug_apply_profiled_local_proximity_hit_with_velocity`, then records the
standard effects, warhead mechanism, component load, component damage, and
platform consequence events.

Scope boundary: all warhead profiles are generic synthetic research profiles
with `mass_kg=12`, `lethal_radius_m=35`, and `damage_scalar=90`. The result is
directional validation of the current model shape, not real-weapon calibration,
Pk evidence, entity-deletion evidence, or strict lethality authority.

## Sweep Setup

- Warhead families: `blast`, `blast_fragmentation`, `continuous_rod`
- Target: structured F-16 pair helper from the runtime test surface
- Missile relative velocity: `(900.0, -250.0, 0.0)` m/s
- Grid values: `[-24, -18, -12, -6, 0, 6, 12, 18, 24]` m
- Horizontal slice: target-local `forward/right`, with `up=0`
- Vertical slice: target-local `forward/up`, with `right=0`
- Total cases: `486`

## Artifacts

- CSV rows: `warhead_detonation_heatmap_20260617.csv`
- Sweep script: `warhead_detonation_heatmap_20260617.py`
- Damage heatmaps:
  - `warhead_detonation_heatmap_damage_horizontal_20260617.png`
  - `warhead_detonation_heatmap_damage_vertical_20260617.png`
- Mechanism heatmaps:
  - `warhead_detonation_heatmap_mechanism_horizontal_20260617.png`
  - `warhead_detonation_heatmap_mechanism_vertical_20260617.png`

## Observations

- The current chain is not a flat radius-only lookup. Detonation point changes
  alter primary component, component load count, platform damage channel, and
  mechanism-specific values.
- `blast` has the broadest nonzero system-damage footprint in this grid:
  `53/81` horizontal points and `51/81` vertical points produced nonzero system
  damage.
- `blast_fragmentation` carries both blast and fragment channels. In this run
  it produced nonzero system damage at `41/81` horizontal points and `35/81`
  vertical points, with fragment density concentrated near the target body.
- `continuous_rod` is the narrowest footprint but can produce high local damage
  when the rod-cut geometry aligns. It produced nonzero system damage at
  `23/81` horizontal points and `18/81` vertical points, with the maximum
  vertical-slice system damage reaching `1.000` at local `(-6, 0, -6)`.
- The component load count is also mechanism-dependent: maxima were `5` for
  `blast`, `4` for `blast_fragmentation`, and `2` for `continuous_rod` in this
  sweep.

## Current Interpretation

The heatmaps support the claim that the current warhead chain differentiates
warhead family and detonation geometry. It is useful for model-shape validation:
blast/fragment/rod channels activate in distinct areas and produce different
platform damage channels.

The same results also preserve the earlier fidelity boundary. They do not prove
realistic kill probability or calibrated weapon effects because the vulnerability
and warhead profile are still generic synthetic assumptions.
