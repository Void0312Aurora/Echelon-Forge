# Terrain Line Of Sight v1

Document kind: `task`
Lifecycle: `active`
Canonical: `docs/systems/environment/work/active/terrain_line_of_sight_v1/README.md`
Owner: `systems/environment` (query owner); `domains/ground` (direct-fire consumer)
Last verified: `2026-10-01`

## Authorized Outcome

Unblock item 5 of the Ground infantry
[Remaining unblock package](../../../../../domains/ground/work/active/eastern_plain_infantry_training_v1/native_runtime_blockers.md#remaining-unblock-package)
for its line-of-sight half: a reviewed, domain-neutral terrain line-of-sight
query, consumed by the bounded Ground rifle direct-fire gate before the hit
roll.

## Owner Decision

Terrain line of sight is a geometric question about the elevation surface; it
carries no Ground stance, cost, or fire semantics. It therefore belongs to the
shared `IEnvironmentModel` owner, beside the existing domain-neutral terrain,
slope, and transition queries. This is the first environment-runtime package
the [environment owner](../../../README.md) said must open here.

The Ground owner is the consumer. It owns which heights the query is asked
about (authored infantry posture heights, selected by the commanded stance) and
what a non-visible answer means for a shot (rejection before release).

## Scope

1. `IEnvironmentModel::get_terrain_line_of_sight_observation(from_x, from_y,
   from_height_above_terrain_m, to_x, to_y, to_height_above_terrain_m)`.
   Endpoints are anchored to the terrain surface plus an explicit height. The
   answer is `visible`, `blocked`, or `unknown`, with provenance: elevation
   source, sample spacing, sample count, distance, endpoint absolute heights,
   and the first blocking sample (position, terrain height, ray height).
2. Sample spacing is the loaded raster's metric cell size
   (`min(|step_x|, |step_y|)` from the Arnis bundle metadata). Interior samples
   are taken at `ceil(distance / spacing)` equal intervals; elevation uses the
   provider's existing nearest-cell lookup, so the query and
   `get_terrain_elevation` agree on the same surface. A sample blocks when
   terrain is strictly above the straight observer-target ray. No tolerance
   constant is introduced.
3. Fail closed: no metric elevation raster loaded (including the procedural
   and `flat` profiles, which are not measured terrain), a non-finite or
   negative input, or an endpoint outside the raster returns `unknown` with an
   explicit reason. `unknown` is never treated as visible.
4. Ground consumer: `fire_ground_weapon` evaluates the query between the
   shooter's eye height and the target's center-of-mass height (the current
   synthetic body-center hit point), each chosen by that entity's commanded
   `GroundStance`. `blocked`, `unknown`, or missing posture geometry rejects
   the shot before ammunition, cooldown, the launch record, or the hit roll
   are touched. Visible shots keep the existing `draw_seed` path unchanged.
5. Heights are authored unit content (`ground_infantry_posture`) carried on
   the existing `GroundInfantryCapability` component. No component or system
   is added to the default registry.

## Raster Edge

No terrain query reads elevation from outside a loaded measured raster.
Beyond the edge, `get_terrain_elevation` returns the procedural fallback
surface, which is not terrain, so a difference taken across the edge is
meaningless. Each query handles the edge explicitly:

| Query | Behaviour at and beyond the raster edge |
|---|---|
| `get_terrain_line_of_sight_observation` | Reads raster cells only. An endpoint or interior sample off the raster gives `unknown` (`EndpointOutsideRaster` / `SampleOutsideRaster`). |
| `get_ground_slope_deg` | Reads raster cells only. The documented 5 m half span (`IEnvironmentModel::kGroundSlopeSampleHalfSpanM`) becomes whole cells per axis, at least one. It is clamped to the raster, so an edge cell takes a one-sided difference over the cells that exist, divided by the metric distance between the sampled cell centres. Off the raster, or on an axis with a single cell, the result is NaN (unavailable). |
| `get_terrain_at`, `get_ground_transition_observation` | Off-raster cells are `Obstacle`, so a move off the raster blocks as before. |
| Ground movement cost | Consumes the slope query. NaN gives a zero multiplier, so movement is not admitted. |

The span is kept rather than replaced by the cell size. It is the documented
movement-sample contract of the
[Arnis native terrain](../../../../../domains/ground/reviews/ground_arnis_native_terrain_v1_20260924/README.md)
slice. On the 1 m Arnis grid it is the same +/-5 cell difference used inland
before this change, so only edge-adjacent cells change. Clamping, rather than
returning unavailable whenever the full window does not fit, keeps every cell
on the raster movable. It is the same edge treatment as the field-acceptance
estimator (`numpy.gradient`, one-sided at the boundary). Procedural and `flat`
profiles are defined everywhere and keep the interface's central difference.

Effect on the eastern-plain fixture (seed 42, HEI): the edge-parallel cases
leave the 0.20 slope floor. The native slope at the edge cells was about 88.7
degrees and is now the terrain's own value. The east, north, and south
parallel cases reach in 593 to 607 steps, matching inland cases (about 600).
The west parallel case takes 1264 steps, because that edge is genuinely steep:
22 to 24 degrees at the start, measured as 15 to 17 degrees east-west plus
about 20 degrees north-south directly from the raster. Step budgets are
derived by native preflight, so no test pins these counts.

Still open: off the raster, the point elevation (`get_terrain_elevation` and
`TerrainCell.elevation`) is still the procedural fallback. Air and physics
consumers use it, so making it unavailable would change their contract. This
package does not decide that.

Evidence: native doctest suite `environment_raster_boundary`
(`src/tests/test_environment_raster_boundary.cpp`). It covers the exact slope
on every cell of an inclined plane including edges and corners, a clamped
window beside a cliff, NaN slope off the raster and on a single-cell axis, and
off-raster moves still blocking. On the base the suite fails; edge cells read
about 86 degrees on a 15.6 degree plane.

## Height Provenance

The current values are `engineering_proxy`: round-number estimates of an
adult soldier's eye and center-of-mass heights for stand, crouch (kneel), and
prone, recorded in the unit JSON with that label. They are not calibrated.

Follow-up `TLOS-F1` (posture height calibration). Entry condition: before any
claim that depends on posture-height accuracy (a hit-probability or exposure
model, or LOS at the margin of a ridge). Derive the values from a cited
anthropometric source (for example ANSUR II, NATICK/TR-15/007) and a cited
firing-posture definition, and replace the `engineering_proxy` label.

## Held

- Cover and concealment, including tree-line and settlement masking. The Arnis
  DEM is a postprocessed ground surface; vegetation and buildings do not block.
- Earth curvature and atmospheric refraction. The raster is a local planar ENU
  grid; at the 300 m rifle range the curvature drop is below 1 cm, at the
  1.7 km fixture extent about 0.23 m. Entry condition: any consumer whose range
  makes that term comparable to the posture heights.
- Bilinear elevation interpolation (nearest-cell is the provider contract).
- Authored infantry hitboxes (the other half of item 5), suppression,
  ballistics, exposure, and sensor-model use of this query.

## Acceptance Evidence

- Native doctest: flat raster visible, ridge blocks with the first blocking
  sample reported, a ray above a lower ridge stays visible, no raster is
  `unknown`, endpoint on the raster edge is visible and one cell beyond is
  `unknown`.
- Native doctest and Python runtime test: the rifle gate rejects a
  terrain-blocked or unknown-terrain shot without consuming ammunition, and a
  visible shot keeps the existing reset-seed draw behavior.
- `ef_test`, `tests/runtime/ground`, `tests/training`,
  `tests/architecture/structural_boundaries`, and
  `tests/architecture/governance` on HEI, with no new reds against the stack
  baseline.

## Closure Condition

Accepted when the evidence above is green and recorded here; lasting facts are
then promoted to the environment README and the Ground specialization baseline,
and this package retires into `reviews/`.
