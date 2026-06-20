# A9 Warhead Detonation Heatmap Validation - 2026-06-17

## Purpose

This validation sweep observes how the current proximity-detonation damage
chain responds to different target-local detonation points and generic
physics-profile warhead families. It uses the existing debug entry point
`debug_apply_profiled_local_proximity_hit_with_velocity`, then records the
standard effects, warhead mechanism, component load, component damage, and
platform consequence events.

Scope boundary: all warhead profiles are generic synthetic research profiles.
They use `mass_kg=12`, `lethal_radius_m=35`, `damage_scalar=90`,
`explosive_mass_kg=5.5`, `case_mass_kg=6.5`,
`gurney_constant_mps=2400`, `fragment_count=900`, and
`fragment_mass_kg=0.0026`. These values are generic order-of-magnitude inputs
for exercising the opt-in Gurney/fragment-decay/rod-cap path, not real-weapon
calibration, Pk evidence, entity-deletion evidence, or strict lethality
authority.

## Sweep Setup

- Warhead families: `blast`, `blast_fragmentation`, `continuous_rod`
- Target: structured F-16 pair helper from the runtime test surface
- Missile relative velocity: `(900.0, -250.0, 0.0)` m/s
- Grid values: `[-24, -18, -12, -6, 0, 6, 12, 18, 24]` m
- Horizontal slice: target-local `forward/right`, with `up=0`
- Vertical slice: target-local `forward/up`, with `right=0`
- Total cases: `486`
- Proximity interpretation excludes points where
  `direct_hitbox_intersection=True`; these points are direct-impact or
  interior-airframe proxies, not exterior proximity-fuze detonation points.

## Artifacts

- CSV rows: `warhead_detonation_heatmap_20260617.csv`
- Sweep script: `warhead_detonation_heatmap_20260617.py`
- Damage heatmaps:
  - `warhead_detonation_heatmap_damage_horizontal_20260617.png`
  - `warhead_detonation_heatmap_damage_vertical_20260617.png`
- Mechanism heatmaps:
  - `warhead_detonation_heatmap_mechanism_horizontal_20260617.png`
  - `warhead_detonation_heatmap_mechanism_vertical_20260617.png`

The heatmaps mask direct-hitbox/interior-proxy cells in gray. The CSV retains
those rows and marks them with `valid_proximity_point=False` for auditability.

## Observations

- The current chain is not a flat radius-only lookup. Detonation point changes
  alter primary component, component load count, platform damage channel, and
  mechanism-specific values.
- `blast` has the broadest nonzero system-damage footprint in this exterior-only
  grid: `50/78` horizontal points and `48/78` vertical points produced nonzero
  system damage.
- `blast_fragmentation` carries both blast and fragment channels. In this run
  it produced nonzero system damage at `38/78` horizontal points and `32/78`
  vertical points, with fragment density concentrated near the target body.
- `continuous_rod` is the narrowest footprint but can produce high local damage
  when the rod-cut geometry aligns. It produced nonzero system damage at
  `20/78` horizontal points and `15/78` vertical points, with the maximum
  exterior vertical-slice system damage reaching `1.000` at local `(-6, 0, -6)`.
- The component load count is also mechanism-dependent: maxima were `5` for
  `blast`, `4` for `blast_fragmentation`, and `2` for `continuous_rod` in this
  sweep.

## Current Interpretation

The heatmaps support the claim that the current warhead chain differentiates
warhead family and detonation geometry. It is useful for model-shape validation:
blast/fragment/rod channels activate in distinct areas and produce different
platform damage channels.

The exterior-only correction makes the proximity result more defensible: the
central forward-axis points `(-6, 0, 0)`, `(0, 0, 0)`, and `(6, 0, 0)` are no
longer used as proximity evidence because they intersect the target hitbox.
Remaining nonzero damage therefore comes from standoff/projection geometry, not
from sampling a missile detonation inside the aircraft body.

The same results also preserve the earlier fidelity boundary. They do not prove
realistic kill probability or calibrated weapon effects because the vulnerability
and warhead profile are still generic synthetic assumptions.

## Calibration Note

This update calibrates the validation artifact by exercising the opt-in
physics-profile path instead of relying only on legacy synthetic mass scaling:
fragment count, fragment mass, explosive mass, casing mass, and Gurney constant
are now present in the swept profile. The implementation also honors authored
`fragment_count` and `fragment_mass_kg` when estimating fragmentation loads and
sampling spatial effects.

The remaining `blast_fragmentation` cutoff near the outer standoff cells is not
evidence that the real effect radius should be that sharp. It comes from the
current spatial-projection gate, which projects only a bounded inner fraction of
the authored lethal radius. A simple projection-radius expansion was checked and
rejected because it weakened existing near-miss probability guardrails while
creating an overly strong far-tail system-damage artifact. The next calibration
step should therefore separate weak residual load, component-failure
probability, and platform-level system damage instead of only increasing the
projection radius.
