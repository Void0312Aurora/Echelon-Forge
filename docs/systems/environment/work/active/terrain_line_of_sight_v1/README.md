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
