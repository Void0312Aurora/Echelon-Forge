# Lethality Hitbox Geometry Fidelity Gap

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/effects/work/issues/lethality_hitbox_geometry_fidelity_gap/README.md`
Owner: `systems/effects`
Last verified: `2026-08-08`

Status: `2026-06-14` retained / first mainline geometry subproject accepted; the current-hitbox geometry and proximity-projection gap exposed by the A2/MLF-5 expanded aspect/distance matrix has been closed for F-16C through the geometry-only fine-geometry engineering proxy subproject. Default runtime replacement, training benefit, and lethality conclusions are still not claimed by that geometry subproject.

First observed: `2026-06-11`, while reviewing the A2/MLF-5 heatmaps for continuous-rod nose 4 m / 6 m behavior and blast/fragmentation tail direct-hit behavior.

Issue class: modeling gap between target geometry, component exposure, proximity projection, and component failure probability.

Mainline execution entry:
[A2 Target Outer-Shape And Component Geometry](../../../reviews/f16c_target_geometry_20260614/README.md).

## Summary

The current lethality chain can turn post-detonation loads or cutting exposure into component failure probability and component damage facts. The target geometry, however, is still a small set of axis-aligned boxes with nested component boxes.

That creates two problems:

- a continuous-rod nose proximity point very close to the target boundary can produce no component damage;
- heatmap columns such as 4 m / 6 m can be misread as ordinary miss distance, while they are local-coordinate test points. In the observed case, 4 m is outside the nose box and 6 m is inside it.

These facts mean the current geometry is an engineering scaffold, not a real aircraft outer mold line or real component layout.

## Current Evidence

### Geometry Gate

Direct hit currently uses axis-aligned boxes:

- `check_hitbox(local_p, box)`: a point inside the box is a direct hit.
- `check_component(local_p, component)`: a point inside the component box is a direct component hit.
- proximity projection uses distance from the detonation point to hitbox or component-box surfaces, projected exposure, direction weighting, and warhead load estimates.

Related code:

- [default_effects_geometry_detail.inc](../../../../../../src/models/weapons/detail/default_effects_geometry_detail.inc)
- [default_effects_direct_hit_detail.inc](../../../../../../src/models/weapons/detail/default_effects_direct_hit_detail.inc)
- [default_effects_spatial_projection_detail.inc](../../../../../../src/models/weapons/detail/default_effects_spatial_projection_detail.inc)

### Current F-16 Boxes

The current F-16 geometry is in [f16c_block50.json](../../../../../../examples/config/database/aircraft/units/f16c_block50.json):

| Region | Center | Size | Extents |
| --- | --- | --- | --- |
| Nose | `[6.0, 0.0, 0.0]` | `[3.6, 1.0, 1.0]` | x: `4.2..7.8`, y: `-0.5..0.5`, z: `-0.5..0.5` |
| Fuselage | `[0.0, 0.0, 0.0]` | `[7.6, 1.4, 1.2]` | x: `-3.8..3.8`, y: `-0.7..0.7`, z: `-0.6..0.6` |
| Tail | `[-6.0, 0.0, 0.0]` | `[3.0, 1.1, 1.1]` | x: `-7.5..-4.5`, y: `-0.55..0.55`, z: `-0.55..0.55` |
| Wing | `[-0.8, 0.0, 0.0]` | `[3.0, 9.8, 0.35]` | x: `-2.3..0.7`, y: `-4.9..4.9`, z: `-0.175..0.175` |

The combined envelope is about `15.3 m x 9.8 m x 1.2 m`. Public F-16 length and wingspan are close to that length/width scale, but public aircraft height is about `4.8 m`; the current boxes are therefore a core fuselage/wing damage scaffold, not a full aircraft shape with vertical tail, canopy height, intake shape, pylons, or tail surfaces.

### Triggering Symptom

During MLF-5 heatmap review:

- continuous-rod nose `x=4.0` is about `0.2 m` ahead of the nose-box edge and is not a direct hit;
- the current statistics show `0.000000` any-component trigger rate for that point;
- from a lethality-model standpoint, a proximity event about 0.2 m from the outer boundary should not silently produce no component damage. The result cannot be treated as reasonable merely because the point is non-direct.

The same review also found an overly weak blast/fragmentation tail direct-hit path. That was repaired with a direct-hit load floor; the geometry-fidelity issue remains open.

## Impact

- Blocks higher-fidelity missile lethality claims: the current geometry cannot support strict claims about how a real AIM-120C hit would break up or crash a real MQ-9/F-16.
- Confuses heatmap interpretation: local coordinates, surface distance, miss distance, and direct-hit category are not separated enough.
- Affects continuous-rod and fragmentation proximity behavior: axial near passes, sweep area, masking, and grazing can be over-simplified, producing "near but no damage" or excessive direct/proximity jumps.
- Affects later structural-breakup work: later breakup, wreck, and debris stages would inherit wrong damaged regions if the geometry input stays too coarse.

## Non-Claims

- Do not treat the current axis-aligned boxes as real aircraft shape.
- Do not treat component-box dimensions as real component dimensions.
- Do not treat current 4 m / 6 m heatmap columns as an ordinary miss-distance curve.
- Do not claim real weapon/target fidelity for component failure probability before this geometry gap is addressed.
- Do not replace geometry improvement with simple probability inflation.

## Hypotheses

1. **Outer-shape and component boxes are mixed**: parent boxes act as both target shape and component-projection containers, with no separate skin/outer-hull geometry.
2. **Axis-aligned boxes are too coarse**: nose, wing, tail, intake, nozzle, and vertical-tail shapes are not rectangular boxes, so box edges create unnatural jumps.
3. **Distance convention is unclear**: heatmap columns are test coordinates or offsets, not always nearest distance to the aircraft surface.
4. **Continuous-rod axial projection is brittle**: when orientation is poor for cutting, the model may suppress close axial proximity to near zero.
5. **No explicit path/sweep intersection**: direct hit mostly checks whether the detonation point lies inside a box; missile path, rod sweep volume, and fragment-cloud shell crossing are not yet explicit.

## Related Domain Context

- A2 MLF-5 archive pointer:
  [docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/README.md](../../../reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/README.md)
- MLF-5 expanded aspect/distance matrix:
  [missile_lethality_component_failure_expanded_matrix_20260611.md](../../../reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/archive/mlf_5_component_failure_accepted_20260611/missile_lethality_component_failure_expanded_matrix_20260611.md)
- MLF-5 visual summary:
  [missile_lethality_component_failure_visual_summary_20260611.md](../../../reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/archive/mlf_5_component_failure_accepted_20260611/missile_lethality_component_failure_visual_summary_20260611.md)
- Current F-16 geometry data:
  [examples/config/database/aircraft/units/f16c_block50.json](../../../../../../examples/config/database/aircraft/units/f16c_block50.json)
- Current MQ-9 geometry data:
  [examples/config/database/aircraft/units/mq9_reaper.json](../../../../../../examples/config/database/aircraft/units/mq9_reaper.json)

## Next Gates

Follow-up geometry refinement should start with design, not parameter tuning. Recommended gates:

1. **Define distance conventions**: separate local coordinate, nearest outer-surface distance, missile-path closest distance, fuze detonation distance, and component-surface distance.
2. **Separate outer shape from components**: outer shape handles hit, masking, and path crossing; component boxes handle vulnerability zones and state writes.
3. **Add public-dimension audits**: compare each aircraft envelope against public length, wingspan, height, wing area, or three-view estimates.
4. **Add key geometry regions**: nose, cockpit, fuselage, wing, wing root, engine/intake, tail/vertical tail, and pylons should be expressible separately.
5. **Repair proximity projection**: a non-direct event close to the outer skin should not hard-drop to no component damage unless masking/orientation diagnostics explain why.
6. **Update visualization**: heatmaps should show coordinate point, surface distance, direct-hit state, candidate component count, and affected component count.

Tool design entry: [Hitbox Geometry Visual Review Tool Design](geometry_visual_review_design_20260611.md). The design proposes a GLB-based outer-shape review packet with three-view overlays before manual confirmation of regions, component boxes, and test points.

Sketchfab replacement entry: [Sketchfab F-16 Replacement Shortlist](sketchfab_f16_replacement_shortlist_20260611.md). Mainline geometry candidates should restart from CC BY 4.0 or broader Sketchfab assets, not FlightGear GPL v2-derived assets.

First mainline subproject: [A2 Target Outer-Shape And Component Geometry](../../../reviews/f16c_target_geometry_20260614/README.md). It is closed against the geometry-only acceptance gate; later default runtime replacement, training diagnostics, or other-airframe reuse require separate acceptance.

## GLB Source Status Addendum

The `2026-06-11` first pass found no source, author, license, or Sketchfab UID embedded in the repository F-16 GLB; `Temp/Model/resource.md` (local-only, untracked) also does not record an F-16 source.

The user later provided a download record for [FlightGear Aircraft-2018 f16.zip](https://mirrors.ibiblio.org/flightgear/ftp/Aircraft-2018/f16.zip). The zip server timestamp is `Fri, 29 May 2020 00:16:42 GMT`; archive entry `f16/Models/f16.ac` is timestamped `2020-05-09T04:15:22`; `LICENSE` is GNU GPL v2; `README.md` identifies the package as FlightGear F-16 Fighting Falcon; and `authors.txt` lists upstream contributors. Existing A2 source pins also record GitHub [NikolaiVChr/f16](https://github.com/NikolaiVChr/f16) commit `190a699c77bd3c2c7da1e3bb4bffc7a6013bc8f5`; GitHub `master` currently still points to the same commit.

Comparison found all `117` local GLB node/mesh names in FlightGear `f16.ac` named objects, including `AirIntake`, `RadarDomeTop`, `CanopyBackInside`, `LeftUpperAileron`, `RightUpperAileron`, `Rudder`, `Tail`, `VentralFins`, `LWStation1`, and `RWStation1`. Geometry counts are not identical, so the local GLB may have gone through Blender conversion, merging, pruning, or retriangulation. The object-name match is nevertheless strong enough to move the asset from plain unknown provenance to a strong FlightGear GPL v2 source candidate.

The user-provided `blob:https://github.com/70ccc3e5-b369-4d7d-b88d-0dce6c4ea77f` is a browser-local blob URL, not a fetchable GitHub file path. It only indicates that the object was created under the GitHub origin and cannot prove source by itself.

Current conclusion: the GLB remains only a historical provenance lead and local comparison asset; it should not enter the mainline geometry-derived path. Follow-up should prefer CC BY 4.0 or broader Sketchfab replacement assets for rebuilding the outer-shape review packet. Even with friendlier licensing, the replacement model can support only outer-shape review and coarse region design; it cannot prove real F-16C Block 50 internal structure, component boundaries, damage zones, or weapon effects by itself.

## Acceptance For Closure

- F-16 and MQ-9 have readable records for envelope dimensions, component zones, and public-dimension audit.
- Continuous-rod and fragmentation proximity tests cover close-to-skin but non-direct nose, tail, beam, top, and bottom cases.
- A roughly 0.2 m close-to-skin proximity case no longer silently produces zero component damage.
- Diagnostics explain nearest outer-surface distance, nearest component distance, candidate component count, masking, and direct-hit state.
- Any repair still avoids direct crash, structural-breakup, wreck/debris, or real weapon Pk claims.
